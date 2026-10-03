"""Build a logical plan tree from a DSL AST (SelectStmt).

The :class:`LogicalPlanBuilder` walks the ``SelectStmt`` dataclass produced
by the DSL builder and converts each field into a tree of :class:`LogicalOp`
nodes.  The tree preserves the *semantic order* defined by the AST so that
the optimizer rules can reason about it without re-inspecting the raw AST.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

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
from py3plex.dsl.ast import ParamRef
from py3plex.dsl.errors import DslExecutionError, ParameterMissingError


def _get_condition_list(select: Any) -> List[Any]:
    """Return a flat list of where-clause conditions from a SelectStmt."""
    conditions = []
    where = getattr(select, "where_clause", None)
    if where is None:
        where = getattr(select, "where", None)
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
        names = list(layer_expr.names)
        return names if "*" not in names else []
    # LayerSet stores layer names in ._names
    if hasattr(layer_expr, "_names"):
        names = list(layer_expr._names)
        return names if "*" not in names else []
    # The DSL v2 AST stores simple layer expressions as LayerExpr terms.
    terms = getattr(layer_expr, "terms", None)
    ops = getattr(layer_expr, "ops", None)
    if terms is not None and ops is not None:
        if len(ops) != max(0, len(terms) - 1) or any(op != "+" for op in ops):
            return []
        names = [getattr(term, "name", None) for term in terms]
        if all(isinstance(name, str) and name != "*" for name in names):
            return names
    return []


class LogicalPlanBuilder:
    """Convert a ``SelectStmt`` AST node into a logical plan tree.

    Parameters
    ----------
    ast_query:
        The top-level ``Query`` dataclass (from ``py3plex.dsl.ast``).
    """

    def __init__(
        self, ast_query: Any, params: Optional[Dict[str, Any]] = None
    ) -> None:
        self._query = ast_query
        self._params = params or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> LogicalOp:
        """Build and return the root of the logical plan tree."""
        select = getattr(self._query, "select", None)
        if select is None and hasattr(self._query, "target"):
            select = self._query
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
        computation_signatures: List[str] = []
        if compute_spec:
            if isinstance(compute_spec, list):
                for item in compute_spec:
                    if isinstance(item, str):
                        name = item
                        signature_data = {"name": item}
                    else:
                        name = getattr(item, "name", getattr(item, "measure", str(item)))
                        signature_data = asdict(item) if is_dataclass(item) else vars(item)
                    measures.append(name)
                    computation_signatures.append(
                        json.dumps(signature_data, sort_keys=True, default=str)
                    )
            elif isinstance(compute_spec, dict):
                measures = list(compute_spec.keys())
                computation_signatures = [
                    json.dumps({"name": name, "spec": spec}, sort_keys=True, default=str)
                    for name, spec in compute_spec.items()
                ]
        if measures:
            comp = LogicalCompute(
                children=[node],
                measures=measures,
                computation_signatures=computation_signatures,
            )
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
            if isinstance(limit, ParamRef):
                if limit.name not in self._params:
                    raise ParameterMissingError(
                        limit.name, provided_params=list(self._params)
                    )
                limit = self._params[limit.name]
            try:
                limit_value = int(limit)
            except (TypeError, ValueError) as exc:
                raise DslExecutionError(
                    f"Query limit must be an integer, got {limit!r}."
                ) from exc
            lim = LogicalLimit(children=[node], n=limit_value)
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
