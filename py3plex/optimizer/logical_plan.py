"""Build a logical plan tree from a DSL AST (SelectStmt).

The :class:`LogicalPlanBuilder` walks the ``SelectStmt`` dataclass produced
by the DSL builder and converts each field into a tree of :class:`LogicalOp`
nodes.  The tree preserves the *semantic order* defined by the AST so that
the optimizer rules can reason about it without re-inspecting the raw AST.
"""

from __future__ import annotations

from typing import Any, List

from .plan_nodes import (
    LogicalAggregate,
    LogicalCompute,
    LogicalCoverage,
    LogicalFilter,
    LogicalGroupByLayer,
    LogicalGroupByLayerPair,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalNullModel,
    LogicalOp,
    LogicalOrderBy,
    LogicalProject,
    LogicalScanEdges,
    LogicalScanNodes,
    LogicalUQ,
)


def _get_condition_list(select: Any) -> List[Any]:
    """Return a flat list of where-clause conditions from a SelectStmt."""
    conditions = []
    where = getattr(select, "where_clause", None)
    if where is None:
        return conditions
    if isinstance(where, list):
        conditions.extend(where)
    else:
        conditions.append(where)
    return conditions


def _get_layer_list(select: Any) -> List[str]:
    """Return layer names from a SelectStmt's layer_expr."""
    layer_expr = getattr(select, "layer_expr", None)
    if layer_expr is None:
        return []
    # LayerExprBuilder stores layer names in .names
    if hasattr(layer_expr, "names"):
        return list(layer_expr.names)
    # LayerSet stores layer names in ._names
    if hasattr(layer_expr, "_names"):
        return list(layer_expr._names)
    return []


class LogicalPlanBuilder:
    """Convert a ``SelectStmt`` AST node into a logical plan tree.

    Parameters
    ----------
    ast_query:
        The top-level ``Query`` dataclass (from ``py3plex.dsl.ast``).
    """

    def __init__(self, ast_query: Any) -> None:
        self._query = ast_query

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> LogicalOp:
        """Build and return the root of the logical plan tree."""
        select = getattr(self._query, "select", None)
        if select is None:
            # Fallback: return an empty node-scan so the optimizer never crashes
            return LogicalScanNodes()

        return self._build_select(select)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_select(self, select: Any) -> LogicalOp:
        target = getattr(select, "target", "nodes")
        # -- 1. Scan ---------------------------------------------------
        if str(target) in ("nodes", "Target.NODES"):
            node: LogicalOp = LogicalScanNodes()
        else:
            node = LogicalScanEdges()

        # -- 2. Layer filter -------------------------------------------
        layers = _get_layer_list(select)
        if layers:
            lf = LogicalLayerFilter(children=[node], layers=layers)
            node = lf

        # -- 3. WHERE filter -------------------------------------------
        conditions = _get_condition_list(select)
        if conditions:
            filt = LogicalFilter(children=[node], conditions=conditions)
            node = filt

        # -- 4. Compute ------------------------------------------------
        compute_spec = getattr(select, "compute_spec", None) or getattr(select, "compute", None)
        measures: List[str] = []
        if compute_spec:
            if isinstance(compute_spec, list):
                for item in compute_spec:
                    name = item if isinstance(item, str) else getattr(item, "measure", str(item))
                    measures.append(name)
            elif isinstance(compute_spec, dict):
                measures = list(compute_spec.keys())
        if measures:
            comp = LogicalCompute(children=[node], measures=measures)
            node = comp

        # -- 5. Grouping -----------------------------------------------
        group_mode = getattr(select, "group_mode", None)
        if group_mode == "per_layer":
            grp: LogicalOp = LogicalGroupByLayer(children=[node])
            node = grp
        elif group_mode == "per_layer_pair":
            grp = LogicalGroupByLayerPair(children=[node])
            node = grp

        # -- 6. Aggregation --------------------------------------------
        agg_spec = getattr(select, "aggregate_spec", None)
        if agg_spec:
            aggregations = agg_spec if isinstance(agg_spec, dict) else {}
            agg = LogicalAggregate(children=[node], aggregations=aggregations)
            node = agg

        # -- 7. Coverage -----------------------------------------------
        coverage_spec = getattr(select, "coverage_spec", None)
        if coverage_spec:
            mode = coverage_spec.get("mode", "all") if isinstance(coverage_spec, dict) else "all"
            k_val = coverage_spec.get("k") if isinstance(coverage_spec, dict) else None
            cov = LogicalCoverage(children=[node], mode=mode, k=k_val)
            node = cov

        # -- 8. ORDER BY -----------------------------------------------
        order_spec = getattr(select, "order_spec", None)
        if order_spec:
            keys = order_spec if isinstance(order_spec, list) else [order_spec]
            desc = getattr(select, "order_desc", False)
            ord_node = LogicalOrderBy(children=[node], keys=keys, desc=desc)
            node = ord_node

        # -- 9. LIMIT --------------------------------------------------
        limit = getattr(select, "limit", None)
        if limit is not None:
            lim = LogicalLimit(children=[node], n=int(limit))
            node = lim

        # -- 10. UQ ----------------------------------------------------
        uq_spec = getattr(select, "uq_spec", None)
        if uq_spec:
            uq_node = LogicalUQ(children=[node], uq_spec=uq_spec if isinstance(uq_spec, dict) else {})
            node = uq_node

        # -- 11. NULL MODEL --------------------------------------------
        null_model_spec = getattr(select, "null_model_spec", None)
        if null_model_spec:
            nm_node = LogicalNullModel(
                children=[node],
                null_model_spec=null_model_spec if isinstance(null_model_spec, dict) else {},
            )
            node = nm_node

        # -- 12. Project (column subset) --------------------------------
        select_cols = getattr(select, "select_columns", None)
        if select_cols:
            proj = LogicalProject(children=[node], columns=list(select_cols))
            node = proj

        return node

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"LogicalPlanBuilder(query={self._query!r})"
