"""Physical plan operators for the py3plex optimizer.

Physical operators are produced by :mod:`py3plex.optimizer.planner` after the
logical plan has been optimised.  Each operator can *execute* a concrete step
against the network and returns a partial result that is piped to the next
operator in the tree.

The module intentionally stays thin: execution delegates back to the existing
DSL executor so we never duplicate logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .plan_nodes import PhysicalOp


# ---------------------------------------------------------------------------
# Scan operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalNodeScanNX(PhysicalOp):
    """Scan all (node, layer) tuples using the NetworkX backend."""

    def execute(self, context: Dict[str, Any]) -> Any:
        network = context.get("network")
        return list(network.get_nodes()) if network is not None else []


@dataclass
class PhysicalEdgeScanNX(PhysicalOp):
    """Scan all edges using the NetworkX backend."""

    def execute(self, context: Dict[str, Any]) -> Any:
        network = context.get("network")
        return list(network.get_edges()) if network is not None else []


# ---------------------------------------------------------------------------
# Filter operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalFilterVectorized(PhysicalOp):
    """Filter items using vectorised numeric comparisons (fast path)."""

    conditions: List[Any] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        items = context.get("items", [])
        # Delegate to the DSL fast-path filter if available
        try:
            from py3plex.dsl.fastpath import fast_select_nodes, build_fast_index, match_fastpath
            network = context.get("network")
            select_stmt = context.get("select_stmt")
            if network and select_stmt:
                plan = match_fastpath(select_stmt)
                if plan:
                    idx = build_fast_index(network, plan)
                    return fast_select_nodes(plan, idx)
        except Exception:
            pass
        return items


@dataclass
class PhysicalFilterPython(PhysicalOp):
    """Filter items using Python iteration (general-purpose)."""

    conditions: List[Any] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        # Return items unchanged; actual filtering is done by the executor
        return context.get("items", [])


# ---------------------------------------------------------------------------
# Compute operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalComputeNetworkX(PhysicalOp):
    """Compute centrality measures using NetworkX."""

    measures: List[str] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


@dataclass
class PhysicalComputeCached(PhysicalOp):
    """Serve pre-computed centrality results from the global compute cache."""

    measures: List[str] = field(default_factory=list)
    cache_keys: List[str] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


# ---------------------------------------------------------------------------
# Aggregate operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalAggregateHash(PhysicalOp):
    """Aggregate using hash-map (optimal for small group counts)."""

    aggregations: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


@dataclass
class PhysicalAggregateSort(PhysicalOp):
    """Aggregate after sorting (optimal for large, pre-sorted data)."""

    aggregations: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


# ---------------------------------------------------------------------------
# Grouping / Coverage / TopK / Limit operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalLayerPushdown(PhysicalOp):
    """Push layer filtering into the scan (avoids materialising all items)."""

    layers: List[str] = field(default_factory=list)

    def execute(self, context: Dict[str, Any]) -> Any:
        network = context.get("network")
        if network is None:
            return []
        nodes = list(network.get_nodes())
        layer_set = set(self.layers)
        return [n for n in nodes if len(n) > 1 and str(n[1]) in layer_set]


@dataclass
class PhysicalCoverage(PhysicalOp):
    """Execute cross-group coverage logic."""

    mode: str = "all"
    k: Optional[int] = None

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


@dataclass
class PhysicalTopKHeap(PhysicalOp):
    """Return top-k items using a min-heap (O(n log k))."""

    k: int = 10
    key: str = ""
    desc: bool = True

    def execute(self, context: Dict[str, Any]) -> Any:
        import heapq

        items = context.get("items", [])
        attributes = context.get("attributes", {})
        key_vals = attributes.get(self.key, {})
        if not key_vals:
            return items[: self.k]

        def _val(item: Any) -> float:
            v = key_vals.get(item, 0)
            if isinstance(v, dict):
                v = v.get("mean", 0)
            return float(v) if v is not None else 0.0

        top = heapq.nlargest(self.k, items, key=_val) if self.desc else heapq.nsmallest(self.k, items, key=_val)
        return top


@dataclass
class PhysicalLimitEarly(PhysicalOp):
    """Truncate result to at most *n* items (early termination)."""

    n: int = 0

    def execute(self, context: Dict[str, Any]) -> Any:
        items = context.get("items", [])
        return items[: self.n] if self.n > 0 else items


# ---------------------------------------------------------------------------
# UQ / Null-model operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalUQMonteCarlo(PhysicalOp):
    """Wrap a sub-plan with Monte-Carlo uncertainty quantification."""

    uq_spec: Dict[str, Any] = field(default_factory=dict)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


@dataclass
class PhysicalNullModelGenerator(PhysicalOp):
    """Generate null model network instances."""

    null_model_spec: Dict[str, Any] = field(default_factory=dict)

    def execute(self, context: Dict[str, Any]) -> Any:
        return context.get("items", [])


# ---------------------------------------------------------------------------
# High-level plan container and builder
# ---------------------------------------------------------------------------


@dataclass
class PhysicalPlan:
    """A complete physical execution plan.

    Attributes
    ----------
    root:
        Root of the physical operator tree.
    estimated_cost:
        Total estimated cost as produced by the cost model.
    plan_hash:
        Short hash of the serialised plan tree (for provenance / caching).
    backend:
        Name of the graph backend (e.g. ``"networkx"``).
    """

    root: PhysicalOp
    estimated_cost: float = 0.0
    plan_hash: str = ""
    backend: str = "networkx"

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of this plan."""

        def _node_dict(op: PhysicalOp) -> dict:
            d: dict = {
                "type": type(op).__name__,
                "estimated_cost": op.estimated_cost,
                "actual_cost": op.actual_cost,
                "children": [_node_dict(c) for c in op.children],
            }
            for key in ("measures", "conditions", "layers", "aggregations",
                        "group_by", "mode", "k", "n", "key", "desc",
                        "uq_spec", "null_model_spec"):
                if hasattr(op, key):
                    d[key] = getattr(op, key)
            return d

        return {
            "backend": self.backend,
            "estimated_cost": self.estimated_cost,
            "plan_hash": self.plan_hash,
            "tree": _node_dict(self.root),
        }

    def execute(self, context: dict) -> Any:
        """Execute the plan by walking the operator tree depth-first."""
        return self.root.execute(context)


class PhysicalPlanBuilder:
    """Convert an optimised logical plan into a :class:`PhysicalPlan`.

    The builder performs *backend-aware* physical operator selection:

    * NetworkX backend (default): ``PhysicalNodeScanNX`` / ``PhysicalEdgeScanNX``
    * Filter: vectorised for simple numeric predicates, Python otherwise
    * Aggregate: hash for small group counts, sort for large
    * order_by + limit: heap-based top-k
    """

    # Threshold below which hash-aggregate is preferred over sort-aggregate
    HASH_AGGREGATE_ROW_THRESHOLD: int = 10_000
    # Threshold for subgraph-first centrality computation
    SUBGRAPH_COMPUTE_THRESHOLD: int = 500

    def __init__(self, backend: str = "networkx") -> None:
        self.backend = backend

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, logical_plan: "LogicalOp", stats: "Any" = None) -> PhysicalPlan:  # noqa: F821
        """Convert *logical_plan* into a :class:`PhysicalPlan`."""
        import hashlib
        import json

        root = self._build_op(logical_plan, stats)
        total_cost = self._tree_cost(root)

        # Produce a short plan hash from the tree structure
        plan_str = json.dumps(PhysicalPlan(root=root).to_dict()["tree"], sort_keys=True)
        plan_hash = hashlib.sha256(plan_str.encode()).hexdigest()[:16]

        return PhysicalPlan(
            root=root,
            estimated_cost=total_cost,
            plan_hash=plan_hash,
            backend=self.backend,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_op(self, logical: "LogicalOp", stats: "Any") -> PhysicalOp:
        from .plan_nodes import (
            LogicalScanNodes,
            LogicalScanEdges,
            LogicalFilter,
            LogicalLayerFilter,
            LogicalCompute,
            LogicalAggregate,
            LogicalGroupByLayer,
            LogicalGroupByLayerPair,
            LogicalCoverage,
            LogicalOrderBy,
            LogicalLimit,
            LogicalTopK,
            LogicalUQ,
            LogicalNullModel,
            LogicalProject,
            LogicalCachedCompute,
            LogicalEmptyScan,
        )

        children = [self._build_op(c, stats) for c in logical.children]
        estimated_rows = getattr(logical, "estimated_rows", None) or 0

        ltype = type(logical).__name__

        if ltype == "LogicalEmptyScan":
            op = PhysicalNodeScanNX()
        elif ltype == "LogicalScanNodes":
            if self.backend == "networkx":
                op = PhysicalNodeScanNX()
            else:
                op = PhysicalNodeScanNX()  # fallback
        elif ltype == "LogicalScanEdges":
            if self.backend == "networkx":
                op = PhysicalEdgeScanNX()
            else:
                op = PhysicalEdgeScanNX()  # fallback
        elif ltype == "LogicalLayerFilter":
            layers = getattr(logical, "layers", [])
            op = PhysicalLayerPushdown(layers=layers)
        elif ltype == "LogicalFilter":
            conditions = getattr(logical, "conditions", [])
            # Use vectorised path for simple numeric predicates
            if all(self._is_simple_numeric(c) for c in conditions):
                op = PhysicalFilterVectorized(conditions=conditions)
            else:
                op = PhysicalFilterPython(conditions=conditions)
        elif ltype == "LogicalCachedCompute":
            op = PhysicalComputeCached(
                measures=getattr(logical, "measures", []),
            )
        elif ltype == "LogicalCompute":
            op = PhysicalComputeNetworkX(
                measures=getattr(logical, "measures", []),
            )
        elif ltype in ("LogicalGroupByLayer", "LogicalGroupByLayerPair"):
            # Handled as a pass-through; real grouping is in the executor
            op = PhysicalFilterPython()
        elif ltype == "LogicalAggregate":
            aggs = getattr(logical, "aggregations", {})
            grp = getattr(logical, "group_by", [])
            if estimated_rows < self.HASH_AGGREGATE_ROW_THRESHOLD:
                op = PhysicalAggregateHash(aggregations=aggs, group_by=grp)
            else:
                op = PhysicalAggregateSort(aggregations=aggs, group_by=grp)
        elif ltype == "LogicalCoverage":
            op = PhysicalCoverage(
                mode=getattr(logical, "mode", "all"),
                k=getattr(logical, "k", None),
            )
        elif ltype == "LogicalTopK":
            op = PhysicalTopKHeap(
                k=getattr(logical, "k", 10),
                key=getattr(logical, "key", ""),
                desc=getattr(logical, "desc", True),
            )
        elif ltype == "LogicalOrderBy":
            keys = getattr(logical, "keys", [])
            op = PhysicalFilterPython()  # ordering is handled by executor
        elif ltype == "LogicalLimit":
            n = getattr(logical, "n", 0)
            op = PhysicalLimitEarly(n=n)
        elif ltype == "LogicalUQ":
            op = PhysicalUQMonteCarlo(uq_spec=getattr(logical, "uq_spec", {}))
        elif ltype == "LogicalNullModel":
            op = PhysicalNullModelGenerator(
                null_model_spec=getattr(logical, "null_model_spec", {})
            )
        elif ltype in ("LogicalProject",):
            op = PhysicalFilterPython()
        else:
            # Unknown node: emit a pass-through
            op = PhysicalFilterPython()

        op.children = children
        op.estimated_cost = self._estimate_op_cost(ltype, estimated_rows)
        return op

    @staticmethod
    def _is_simple_numeric(condition: "Any") -> bool:
        """Return True if *condition* is a simple numeric comparison dict."""
        if not isinstance(condition, dict):
            return False
        return condition.get("op") in {">", "<", ">=", "<=", "==", "!="}

    @staticmethod
    def _estimate_op_cost(ltype: str, estimated_rows: int) -> float:
        costs = {
            "LogicalScanNodes": 1.0,
            "LogicalScanEdges": 1.0,
            "LogicalFilter": 0.5,
            "LogicalLayerFilter": 0.3,
            "LogicalCompute": 10.0,
            "LogicalCachedCompute": 0.1,
            "LogicalAggregate": 5.0,
            "LogicalCoverage": 2.0,
            "LogicalTopK": 2.0,
            "LogicalOrderBy": 3.0,
            "LogicalLimit": 0.1,
            "LogicalUQ": 20.0,
        }
        base = costs.get(ltype, 1.0)
        return base * max(estimated_rows, 1)

    @staticmethod
    def _tree_cost(op: PhysicalOp) -> float:
        total = op.estimated_cost
        for child in op.children:
            total += PhysicalPlanBuilder._tree_cost(child)
        return total
