"""Selection fast path for DSL v2.

This module implements a **selection-only** fast path that accelerates common
WHERE filters (layer membership and degree thresholds) by pre-building a
compact index over the network and applying filters via simple integer
comparisons rather than the full condition-evaluation pipeline.

Important distinctions
----------------------
* This fast path accelerates **item selection** (nodes / edges), NOT metric
  computation.  It is completely separate from the approximate-centrality
  compute fast path controlled by :class:`~py3plex.dsl.ast.ApproximationSpec`.
* Eligibility is **strict**: if the query contains any pattern not listed below
  the fast path returns ``None`` and the baseline executor runs instead.
* The caller records ``provenance["backend"]["fast_path"] = True/False``.

Supported predicate shapes
--------------------------
Node queries
    * Layer filter: ``from_layers(L["X"])`` or ``WHERE layer="X"``
    * Degree thresholds: ``degree__gt``, ``degree__ge``, ``degree__lt``,
      ``degree__le``, ``degree__eq``
    * Only AND combinations of the above.  No NOT, no OR, no function calls.

Edge queries
    * ``src_degree__gt/ge/lt/le/eq``
    * ``dst_degree__gt/ge/lt/le/eq``
    * Optional ``source_layer == X AND target_layer == Y``
    * Only AND combinations.  No NOT, no OR.

Fallback
--------
Any exception raised inside the fast path is caught by the caller, which then
runs the baseline executor and appends ``"fast_path_failed_fallback"`` to the
provenance warnings list.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastPlan
# ---------------------------------------------------------------------------

@dataclass
class FastPlan:
    """Compressed description of a fast-path eligible query.

    Attributes
    ----------
    target:
        ``"nodes"`` or ``"edges"``.
    allowed_layers:
        Set of layer names the node must belong to, or ``None`` for all layers.
    allowed_layer_pairs:
        Set of ``(src_layer, dst_layer)`` pairs for edge queries, or ``None``.
    node_degree_min:
        Minimum node degree (inclusive), or ``None``.
    node_degree_max:
        Maximum node degree (inclusive), or ``None``.
    src_degree_min / src_degree_max:
        Degree bounds for the source node of an edge.
    dst_degree_min / dst_degree_max:
        Degree bounds for the destination node of an edge.
    """

    target: str  # "nodes" | "edges"
    allowed_layers: Optional[Set[str]] = None
    allowed_layer_pairs: Optional[Set[Tuple[str, str]]] = None
    node_degree_min: Optional[int] = None
    node_degree_max: Optional[int] = None
    src_degree_min: Optional[int] = None
    src_degree_max: Optional[int] = None
    dst_degree_min: Optional[int] = None
    dst_degree_max: Optional[int] = None

    def summary(self) -> str:
        """Return a short human-readable description of the plan."""
        parts = [f"target={self.target}"]
        if self.allowed_layers is not None:
            parts.append(f"layers={sorted(self.allowed_layers)}")
        if self.allowed_layer_pairs is not None:
            parts.append(f"layer_pairs={sorted(self.allowed_layer_pairs)}")
        if self.node_degree_min is not None:
            parts.append(f"deg>={self.node_degree_min}")
        if self.node_degree_max is not None:
            parts.append(f"deg<={self.node_degree_max}")
        if self.src_degree_min is not None:
            parts.append(f"src_deg>={self.src_degree_min}")
        if self.src_degree_max is not None:
            parts.append(f"src_deg<={self.src_degree_max}")
        if self.dst_degree_min is not None:
            parts.append(f"dst_deg>={self.dst_degree_min}")
        if self.dst_degree_max is not None:
            parts.append(f"dst_deg<={self.dst_degree_max}")
        return "FastPlan(" + ", ".join(parts) + ")"


# ---------------------------------------------------------------------------
# FastIndex
# ---------------------------------------------------------------------------

@dataclass
class FastIndex:
    """Pre-built index for fast selection.

    Node fields (populated when target == "nodes"):
    -------------------------------------------------
    nodes_list:
        All ``(node_id, layer)`` tuples in stable insertion order.
    node_layers:
        Parallel list of layer names.
    node_degree:
        Parallel list of aggregate degrees.
    nodes_by_layer:
        Mapping from layer name to list of indices into ``nodes_list``.

    Edge fields (populated when target == "edges"):
    -------------------------------------------------
    edges_list:
        All ``(src, dst, src_layer, dst_layer)`` tuples in stable order.
    edge_src_degree:
        Parallel list of source-node degrees.
    edge_dst_degree:
        Parallel list of destination-node degrees.
    edges_by_layerpair:
        Mapping from ``(src_layer, dst_layer)`` to list of indices.
    """

    # Nodes
    nodes_list: List[Tuple] = field(default_factory=list)
    node_layers: List[str] = field(default_factory=list)
    node_degree: List[int] = field(default_factory=list)
    nodes_by_layer: Dict[str, List[int]] = field(default_factory=dict)

    # Edges
    edges_list: List[Tuple] = field(default_factory=list)
    edge_src_degree: List[int] = field(default_factory=list)
    edge_dst_degree: List[int] = field(default_factory=list)
    edges_by_layerpair: Dict[Tuple[str, str], List[int]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# match_fastpath
# ---------------------------------------------------------------------------

# Operators that map to lower bound (degree >= threshold)
_LOWER_OPS: Set[str] = {">", ">=", "gt", "ge", "gte"}
# Operators that map to upper bound (degree <= threshold)
_UPPER_OPS: Set[str] = {"<", "<=", "lt", "le", "lte"}
# Equality operators
_EQ_OPS: Set[str] = {"=", "==", "eq"}

# Friendly names -> canonical field names for node degree predicates
_NODE_DEGREE_FIELDS: Set[str] = {"degree"}
# Friendly names for edge degree predicates
_SRC_DEGREE_FIELDS: Set[str] = {"src_degree"}
_DST_DEGREE_FIELDS: Set[str] = {"dst_degree"}
# Layer-equality fields
_LAYER_FIELDS: Set[str] = {"layer"}
_SRC_LAYER_FIELDS: Set[str] = {"source_layer", "src_layer"}
_DST_LAYER_FIELDS: Set[str] = {"target_layer", "dst_layer"}


def _coerce_to_int_or_num(val: Any) -> float:
    """Return a numeric value; raise ValueError if not numeric."""
    if isinstance(val, (int, float)):
        return val
    raise ValueError(f"Expected numeric bound, got {type(val).__name__}: {val!r}")


def match_fastpath(select_stmt: Any) -> Optional[FastPlan]:
    """Analyse a :class:`~py3plex.dsl.ast.SelectStmt` and return a
    :class:`FastPlan` when the query is strictly eligible, or ``None``
    otherwise.

    Parameters
    ----------
    select_stmt:
        A ``SelectStmt`` AST node.

    Returns
    -------
    FastPlan or None
        ``None`` means the query is not eligible and the baseline executor
        must be used.
    """
    # Avoid circular import; import locally.
    from .ast import Target, ConditionExpr, ConditionAtom, Comparison

    # ---- gate on features that are incompatible with fast path ---------------

    # Grouping, aggregation, compute, uq, ordering, limits, community detection,
    # temporal contexts, or post_filters are all passed through to the baseline.
    # The fast path only handles pure selection (no downstream transforms).
    if getattr(select_stmt, "group_by", None):
        return None
    if getattr(select_stmt, "compute", None):
        return None
    if getattr(select_stmt, "order_by", None):
        return None
    if getattr(select_stmt, "limit", None) is not None:
        return None
    if getattr(select_stmt, "uq_config", None):
        return None
    if getattr(select_stmt, "community_config", None):
        return None
    if getattr(select_stmt, "temporal_context", None):
        return None
    if getattr(select_stmt, "window_spec", None):
        return None
    if getattr(select_stmt, "post_filters", None):
        return None
    if getattr(select_stmt, "sensitivity_config", None):
        return None
    if getattr(select_stmt, "explain_spec", None):
        return None

    # ---- determine target ----------------------------------------------------
    target_enum = getattr(select_stmt, "target", None)
    if target_enum is None:
        return None
    if target_enum == Target.NODES:
        target = "nodes"
    elif target_enum == Target.EDGES:
        target = "edges"
    else:
        return None  # COMMUNITIES etc. not handled

    # ---- layer filter --------------------------------------------------------
    # We support layer_set and legacy layer_expr.  The fast path resolves these
    # *lazily* at execution time (see build_fast_index), so here we just note
    # their presence.  We'll store the raw layer_set / layer_expr on the plan
    # as helper attributes so build_fast_index can resolve them.
    #
    # We do NOT support mixed layer_set + layer_expr (shouldn't happen).
    has_layer_filter = bool(
        getattr(select_stmt, "layer_set", None)
        or getattr(select_stmt, "layer_expr", None)
    )
    # Store references so build_fast_index can resolve later
    _layer_set = getattr(select_stmt, "layer_set", None)
    _layer_expr = getattr(select_stmt, "layer_expr", None)

    # ---- parse WHERE conditions -----------------------------------------------
    where: Optional[ConditionExpr] = getattr(select_stmt, "where", None)

    # Collect parsed bounds
    allowed_layers: Optional[Set[str]] = None
    allowed_layer_pairs_src: Optional[str] = None  # for edge source layer
    allowed_layer_pairs_dst: Optional[str] = None  # for edge target layer

    node_degree_min: Optional[float] = None
    node_degree_max: Optional[float] = None
    src_degree_min: Optional[float] = None
    src_degree_max: Optional[float] = None
    dst_degree_min: Optional[float] = None
    dst_degree_max: Optional[float] = None

    if where is not None:
        # Reject if there are any OR operators
        ops = getattr(where, "ops", [])
        for op in ops:
            if str(op).upper() == "OR":
                return None

        atoms = getattr(where, "atoms", [])
        for atom in atoms:
            # We only accept simple Comparison atoms; reject function calls and
            # special predicates.
            if not getattr(atom, "is_comparison", False):
                return None
            comp: Comparison = atom.comparison

            # Reject NOT (represented as negated comparisons)
            if getattr(comp, "negated", False):
                return None

            left: str = str(comp.left).strip()
            op: str = str(comp.op).strip()
            right = comp.right

            # Resolve ParamRef — fast path cannot handle unbound params
            from .ast import ParamRef
            if isinstance(right, ParamRef):
                return None

            # -- layer equality for nodes ---
            if target == "nodes" and left in _LAYER_FIELDS:
                if op not in _EQ_OPS:
                    return None  # Non-equality layer filter not supported
                if allowed_layers is None:
                    allowed_layers = set()
                allowed_layers.add(str(right))
                continue

            # -- source_layer / target_layer for edges ---
            if target == "edges" and left in _SRC_LAYER_FIELDS:
                if op not in _EQ_OPS:
                    return None
                allowed_layer_pairs_src = str(right)
                continue
            if target == "edges" and left in _DST_LAYER_FIELDS:
                if op not in _EQ_OPS:
                    return None
                allowed_layer_pairs_dst = str(right)
                continue

            # -- node degree ---
            if target == "nodes" and left in _NODE_DEGREE_FIELDS:
                try:
                    val = _coerce_to_int_or_num(right)
                except ValueError:
                    return None
                if op in _LOWER_OPS:
                    effective_min = val if op in {">=", "ge", "gte"} else val + 1
                    node_degree_min = (
                        max(node_degree_min, effective_min)
                        if node_degree_min is not None
                        else effective_min
                    )
                elif op in _UPPER_OPS:
                    effective_max = val if op in {"<=", "le", "lte"} else val - 1
                    node_degree_max = (
                        min(node_degree_max, effective_max)
                        if node_degree_max is not None
                        else effective_max
                    )
                elif op in _EQ_OPS:
                    node_degree_min = val
                    node_degree_max = val
                else:
                    return None
                continue

            # -- src_degree / dst_degree ---
            if target == "edges" and left in _SRC_DEGREE_FIELDS:
                try:
                    val = _coerce_to_int_or_num(right)
                except ValueError:
                    return None
                if op in _LOWER_OPS:
                    eff = val if op in {">=", "ge", "gte"} else val + 1
                    src_degree_min = max(src_degree_min, eff) if src_degree_min is not None else eff
                elif op in _UPPER_OPS:
                    eff = val if op in {"<=", "le", "lte"} else val - 1
                    src_degree_max = min(src_degree_max, eff) if src_degree_max is not None else eff
                elif op in _EQ_OPS:
                    src_degree_min = val
                    src_degree_max = val
                else:
                    return None
                continue

            if target == "edges" and left in _DST_DEGREE_FIELDS:
                try:
                    val = _coerce_to_int_or_num(right)
                except ValueError:
                    return None
                if op in _LOWER_OPS:
                    eff = val if op in {">=", "ge", "gte"} else val + 1
                    dst_degree_min = max(dst_degree_min, eff) if dst_degree_min is not None else eff
                elif op in _UPPER_OPS:
                    eff = val if op in {"<=", "le", "lte"} else val - 1
                    dst_degree_max = min(dst_degree_max, eff) if dst_degree_max is not None else eff
                elif op in _EQ_OPS:
                    dst_degree_min = val
                    dst_degree_max = val
                else:
                    return None
                continue

            # Any other predicate → not eligible
            return None

    # ---- build allowed_layer_pairs -------------------------------------------
    allowed_layer_pairs: Optional[Set[Tuple[str, str]]] = None
    if allowed_layer_pairs_src is not None or allowed_layer_pairs_dst is not None:
        # Both must be specified for a pair constraint
        if allowed_layer_pairs_src is not None and allowed_layer_pairs_dst is not None:
            allowed_layer_pairs = {(allowed_layer_pairs_src, allowed_layer_pairs_dst)}
        else:
            # Only one side specified → not strictly a pair filter → bail out
            return None

    # ---- convert float bounds to int (they represent degree counts) ----------
    def _to_int_bound(v: Optional[float]) -> Optional[int]:
        if v is None:
            return None
        return int(v)

    plan = FastPlan(
        target=target,
        allowed_layers=allowed_layers,
        allowed_layer_pairs=allowed_layer_pairs,
        node_degree_min=_to_int_bound(node_degree_min),
        node_degree_max=_to_int_bound(node_degree_max),
        src_degree_min=_to_int_bound(src_degree_min),
        src_degree_max=_to_int_bound(src_degree_max),
        dst_degree_min=_to_int_bound(dst_degree_min),
        dst_degree_max=_to_int_bound(dst_degree_max),
    )

    # Attach raw references so build_fast_index can resolve the layer filter
    # coming from from_layers() / layer_set.  These are NOT part of the public
    # dataclass interface but are set dynamically.
    plan._layer_set = _layer_set  # type: ignore[attr-defined]
    plan._layer_expr = _layer_expr  # type: ignore[attr-defined]

    return plan


# ---------------------------------------------------------------------------
# build_fast_index
# ---------------------------------------------------------------------------

def build_fast_index(network: Any, plan: FastPlan) -> FastIndex:
    """Build a :class:`FastIndex` over *network* for the given *plan*.

    Parameters
    ----------
    network:
        A ``multi_layer_network`` instance.
    plan:
        A :class:`FastPlan` from :func:`match_fastpath`.

    Returns
    -------
    FastIndex
        A pre-built index ready for use by :func:`fast_select_nodes` or
        :func:`fast_select_edges`.
    """
    idx = FastIndex()

    # ---- resolve active layers from plan's stored references -----------------
    active_layers: Optional[Set[str]] = None
    if getattr(plan, "_layer_set", None) is not None:
        active_layers = plan._layer_set.resolve(network, strict=False, warn_empty=False)  # type: ignore[attr-defined]
    elif getattr(plan, "_layer_expr", None) is not None:
        # Lazy import to avoid circular dependency
        from .executor import _evaluate_layer_expr
        active_layers = _evaluate_layer_expr(plan._layer_expr, network)  # type: ignore[attr-defined]

    # Merge WHERE layer filters with from_layers filter (intersection)
    if plan.allowed_layers is not None:
        if active_layers is not None:
            active_layers = active_layers & plan.allowed_layers
        else:
            active_layers = plan.allowed_layers

    if plan.target == "nodes":
        _build_node_index(network, idx, active_layers)
    else:
        _build_edge_index(network, idx, plan)

    return idx


def _build_node_index(
    network: Any, idx: FastIndex, active_layers: Optional[Set[str]]
) -> None:
    """Populate node fields of *idx*."""
    # Build a degree table once from the underlying NetworkX graph
    G = network.core_network  # type: ignore[attr-defined]
    degree_map: Dict[Any, int] = dict(G.degree())

    all_nodes = list(network.get_nodes())

    for i, node_tuple in enumerate(all_nodes):
        # node_tuple is (node_id, layer)
        if not isinstance(node_tuple, tuple) or len(node_tuple) < 2:
            continue
        node_id, layer = node_tuple[0], node_tuple[1]
        if active_layers is not None and layer not in active_layers:
            continue

        # degree_map keys are (node_id, layer) tuples — must look up with full tuple
        deg = degree_map.get(node_tuple, degree_map.get(node_id, 0))
        pos = len(idx.nodes_list)
        idx.nodes_list.append(node_tuple)
        idx.node_layers.append(str(layer))
        idx.node_degree.append(deg)
        if str(layer) not in idx.nodes_by_layer:
            idx.nodes_by_layer[str(layer)] = []
        idx.nodes_by_layer[str(layer)].append(pos)


def _build_edge_index(network: Any, idx: FastIndex, plan: FastPlan) -> None:
    """Populate edge fields of *idx*."""
    G = network.core_network  # type: ignore[attr-defined]
    degree_map: Dict[Any, int] = dict(G.degree())

    # Resolve allowed layer pairs from from_layers / layer_expr
    active_layers: Optional[Set[str]] = None
    if getattr(plan, "_layer_set", None) is not None:
        active_layers = plan._layer_set.resolve(network, strict=False, warn_empty=False)  # type: ignore[attr-defined]
    elif getattr(plan, "_layer_expr", None) is not None:
        from .executor import _evaluate_layer_expr
        active_layers = _evaluate_layer_expr(plan._layer_expr, network)  # type: ignore[attr-defined]

    all_edges = list(network.get_edges(data=True))

    for edge in all_edges:
        # Edge tuples: (src, dst, data_dict) or (src, dst, src_layer, dst_layer, ...)
        if len(edge) == 3 and isinstance(edge[2], dict):
            src, dst, data = edge
            src_layer = str(data.get("source_type", data.get("src_layer", data.get("layer", ""))))
            dst_layer = str(data.get("target_type", data.get("dst_layer", data.get("layer", ""))))
        elif len(edge) >= 4:
            src, dst, src_layer, dst_layer = edge[0], edge[1], str(edge[2]), str(edge[3])
            data = {}
        else:
            continue

        # Layer pair filter from plan
        if plan.allowed_layer_pairs is not None:
            if (src_layer, dst_layer) not in plan.allowed_layer_pairs:
                continue
        # Active layer filter from from_layers
        if active_layers is not None:
            if src_layer not in active_layers or dst_layer not in active_layers:
                continue

        src_deg = degree_map.get(src, 0)
        dst_deg = degree_map.get(dst, 0)

        pos = len(idx.edges_list)
        # Store in baseline-compatible format: (src, dst, data_dict)
        idx.edges_list.append((src, dst, data))
        idx.edge_src_degree.append(src_deg)
        idx.edge_dst_degree.append(dst_deg)

        pair_key = (src_layer, dst_layer)
        if pair_key not in idx.edges_by_layerpair:
            idx.edges_by_layerpair[pair_key] = []
        idx.edges_by_layerpair[pair_key].append(pos)


# ---------------------------------------------------------------------------
# fast_select_nodes
# ---------------------------------------------------------------------------

def fast_select_nodes(plan: FastPlan, idx: FastIndex) -> List[Tuple]:
    """Select nodes using the pre-built index.

    Parameters
    ----------
    plan:
        A :class:`FastPlan` with degree bounds.
    idx:
        A :class:`FastIndex` populated by :func:`build_fast_index`.

    Returns
    -------
    list
        ``(node_id, layer)`` tuples in stable order.
    """
    # Candidate indices
    if plan.allowed_layers is not None:
        candidates: List[int] = []
        for layer in plan.allowed_layers:
            candidates.extend(idx.nodes_by_layer.get(layer, []))
        # Sort to restore stable order
        candidates.sort()
    else:
        candidates = list(range(len(idx.nodes_list)))

    # Apply degree bounds
    d_min = plan.node_degree_min
    d_max = plan.node_degree_max

    result = []
    for i in candidates:
        deg = idx.node_degree[i]
        if d_min is not None and deg < d_min:
            continue
        if d_max is not None and deg > d_max:
            continue
        result.append(idx.nodes_list[i])

    return result


# ---------------------------------------------------------------------------
# fast_select_edges
# ---------------------------------------------------------------------------

def fast_select_edges(plan: FastPlan, idx: FastIndex) -> List[Tuple]:
    """Select edges using the pre-built index.

    Parameters
    ----------
    plan:
        A :class:`FastPlan` with src/dst degree bounds.
    idx:
        A :class:`FastIndex` populated by :func:`build_fast_index`.

    Returns
    -------
    list
        ``(src, dst, {data})`` tuples in stable order (same format as
        ``network.get_edges(data=True)``).
    """
    if plan.allowed_layer_pairs is not None:
        candidates: List[int] = []
        for pair in plan.allowed_layer_pairs:
            candidates.extend(idx.edges_by_layerpair.get(pair, []))
        candidates.sort()
    else:
        candidates = list(range(len(idx.edges_list)))

    sd_min = plan.src_degree_min
    sd_max = plan.src_degree_max
    dd_min = plan.dst_degree_min
    dd_max = plan.dst_degree_max

    result = []
    for i in candidates:
        s_deg = idx.edge_src_degree[i]
        d_deg = idx.edge_dst_degree[i]
        if sd_min is not None and s_deg < sd_min:
            continue
        if sd_max is not None and s_deg > sd_max:
            continue
        if dd_min is not None and d_deg < dd_min:
            continue
        if dd_max is not None and d_deg > dd_max:
            continue
        result.append(idx.edges_list[i])

    return result
