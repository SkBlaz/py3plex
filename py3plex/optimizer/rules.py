"""Rule-based and cost-based rewrite rules for the py3plex query optimizer.

Each rule is a stand-alone callable that accepts a :class:`LogicalOp` tree,
decides whether it matches a specific pattern, and returns a (potentially
rewritten) tree.  The :class:`RuleEngine` iterates all registered rules to
fixpoint (up to ``OPTIMIZER_MAX_ITER`` rounds).
"""

from __future__ import annotations

import copy
import logging
from typing import List, Optional, Type

from .plan_nodes import LogicalOp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class OptimizationRule:
    """Base class for all rewrite rules."""

    name: str = "BaseRule"

    def match(self, plan: LogicalOp) -> bool:  # noqa: ARG002
        """Return ``True`` if this rule can be applied to *plan*."""
        return False

    def apply(self, plan: LogicalOp) -> LogicalOp:
        """Return a rewritten logical plan (or the same node if unchanged)."""
        return plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _type_name(op: LogicalOp) -> str:
    return type(op).__name__


# ---------------------------------------------------------------------------
# Rule 1: Push layer filter below compute
# ---------------------------------------------------------------------------


class PushLayerFilterBelowCompute(OptimizationRule):
    """Move ``LogicalLayerFilter`` before ``LogicalCompute``."""

    name = "PushLayerFilterBelowCompute"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalCompute":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalLayerFilter"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        # Compute(LayerFilter(child)) -> LayerFilter(Compute(child))
        layer_filter = plan.children[0]
        inner_child = layer_filter.children[0] if layer_filter.children else layer_filter
        new_compute = copy.copy(plan)
        new_compute.children = [inner_child] + list(plan.children[1:])
        new_filter = copy.copy(layer_filter)
        new_filter.children = [new_compute] + list(layer_filter.children[1:])
        return new_filter


# ---------------------------------------------------------------------------
# Rule 2: Push filter below compute
# ---------------------------------------------------------------------------


class PushFilterBelowCompute(OptimizationRule):
    """Move ``LogicalFilter`` before ``LogicalCompute`` when safe."""

    name = "PushFilterBelowCompute"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalCompute":
            return False
        if not plan.children:
            return False
        child = plan.children[0]
        if _type_name(child) != "LogicalFilter":
            return False
        # Only push down if the filter predicate does not reference computed cols
        measures = getattr(plan, "measures", [])
        predicates = getattr(child, "predicates", [])
        for pred in predicates:
            for m in measures:
                if m in str(pred):
                    return False
        return True

    def apply(self, plan: LogicalOp) -> LogicalOp:
        filt = plan.children[0]
        inner = filt.children[0] if filt.children else filt
        new_compute = copy.copy(plan)
        new_compute.children = [inner] + list(plan.children[1:])
        new_filt = copy.copy(filt)
        new_filt.children = [new_compute] + list(filt.children[1:])
        return new_filt


# ---------------------------------------------------------------------------
# Rule 3: Push filter below aggregate when safe
# ---------------------------------------------------------------------------


class PushFilterBelowAggregate(OptimizationRule):
    """Move ``LogicalFilter`` before ``LogicalAggregate`` when safe."""

    name = "PushFilterBelowAggregate"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalAggregate":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalFilter"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        filt = plan.children[0]
        inner = filt.children[0] if filt.children else filt
        new_agg = copy.copy(plan)
        new_agg.children = [inner] + list(plan.children[1:])
        new_filt = copy.copy(filt)
        new_filt.children = [new_agg] + list(filt.children[1:])
        return new_filt


# ---------------------------------------------------------------------------
# Rule 4: Combine adjacent filters
# ---------------------------------------------------------------------------


class CombineAdjacentFilters(OptimizationRule):
    """Merge two consecutive ``LogicalFilter`` nodes into one."""

    name = "CombineAdjacentFilters"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalFilter":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalFilter"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner_filt = plan.children[0]
        combined_predicates = list(getattr(plan, "predicates", [])) + list(
            getattr(inner_filt, "predicates", [])
        )
        merged = copy.copy(plan)
        merged.predicates = combined_predicates  # type: ignore[attr-defined]
        merged.children = list(inner_filt.children)
        return merged


# ---------------------------------------------------------------------------
# Rule 5: Reorder filters by selectivity
# ---------------------------------------------------------------------------


class ReorderFiltersBySelectivity(OptimizationRule):
    """Put cheaper / more-selective predicates first."""

    name = "ReorderFiltersBySelectivity"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalFilter":
            return False
        predicates = list(getattr(plan, "predicates", []))
        return len(predicates) > 1

    def apply(self, plan: LogicalOp) -> LogicalOp:
        # Simple heuristic: layer predicates first, then equality, then range
        def _priority(pred: object) -> int:
            s = str(pred)
            if "layer" in s:
                return 0
            if "__eq" in s or "=" in s:
                return 1
            return 2

        new_plan = copy.copy(plan)
        new_plan.predicates = sorted(  # type: ignore[attr-defined]
            getattr(plan, "predicates", []), key=_priority
        )
        return new_plan


# ---------------------------------------------------------------------------
# Rule 6: Convert OrderBy+Limit to TopK
# ---------------------------------------------------------------------------


class ConvertOrderByLimitToTopK(OptimizationRule):
    """Replace ``LogicalOrderBy`` + ``LogicalLimit`` with ``LogicalTopK``."""

    name = "ConvertOrderByLimitToTopK"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalOrderBy":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalLimit"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        from .plan_nodes import LogicalTopK

        limit_op = plan.children[0]
        topk = LogicalTopK(
            k=getattr(limit_op, "n", 10),
            key=getattr(plan, "key", ""),
            desc=getattr(plan, "desc", True),
            children=list(limit_op.children),
        )
        return topk


# ---------------------------------------------------------------------------
# Rule 7: Remove redundant project
# ---------------------------------------------------------------------------


class RemoveRedundantProject(OptimizationRule):
    """Remove a ``LogicalProject`` that selects all columns."""

    name = "RemoveRedundantProject"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalProject":
            return False
        cols = getattr(plan, "columns", None)
        return not cols  # empty columns list means "select all"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        return plan.children[0] if plan.children else plan


# ---------------------------------------------------------------------------
# Rule 8: Early limit pushdown
# ---------------------------------------------------------------------------


class EarlyLimitPushdown(OptimizationRule):
    """Push ``LogicalLimit`` below ``LogicalOrderBy`` when safe."""

    name = "EarlyLimitPushdown"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalLimit":
            return False
        if not plan.children:
            return False
        child_type = _type_name(plan.children[0])
        return child_type not in {"LogicalOrderBy", "LogicalAggregate"}

    def apply(self, plan: LogicalOp) -> LogicalOp:
        # Inject an early limit below current child where safe
        child = plan.children[0]
        from .plan_nodes import LogicalLimit

        early = LogicalLimit(n=getattr(plan, "n", 0), children=list(child.children))
        new_child = copy.copy(child)
        new_child.children = [early] + list(child.children[1:])
        new_plan = copy.copy(plan)
        new_plan.children = [new_child] + list(plan.children[1:])
        return new_plan


# ---------------------------------------------------------------------------
# Rule 9: Choose hash or sort aggregate
# ---------------------------------------------------------------------------


class ConvertAggregateToHashIfSmallGroups(OptimizationRule):
    """Tag ``LogicalAggregate`` with ``use_hash=True`` for small group counts."""

    name = "ConvertAggregateToHashIfSmallGroups"

    SMALL_THRESHOLD = 128

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalAggregate":
            return False
        return not getattr(plan, "use_hash", False)

    def apply(self, plan: LogicalOp) -> LogicalOp:
        estimated = getattr(plan, "estimated_rows", None)
        if estimated is None or estimated <= self.SMALL_THRESHOLD:
            new_plan = copy.copy(plan)
            new_plan.use_hash = True  # type: ignore[attr-defined]
            return new_plan
        return plan


# ---------------------------------------------------------------------------
# Rule 10: Use cached centrality
# ---------------------------------------------------------------------------


class UseCachedCentralityIfAvailable(OptimizationRule):
    """Replace ``LogicalCompute`` with a cache-read node when available."""

    name = "UseCachedCentralityIfAvailable"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalCompute":
            return False
        measures = getattr(plan, "measures", [])
        if not measures:
            return False
        try:
            from py3plex.dsl.cache import _GLOBAL_CACHE  # type: ignore[import]

            cache_key = tuple(sorted(measures))
            return cache_key in _GLOBAL_CACHE
        except Exception:
            return False

    def apply(self, plan: LogicalOp) -> LogicalOp:
        from .plan_nodes import LogicalCachedCompute

        return LogicalCachedCompute(
            measures=list(getattr(plan, "measures", [])),
            children=list(plan.children),
        )


# ---------------------------------------------------------------------------
# Rule 11: Collapse per-layer into scan partition
# ---------------------------------------------------------------------------


class CollapsePerLayerIntoScanPartition(OptimizationRule):
    """Fold ``LogicalGroupByLayer`` directly into the scan operator."""

    name = "CollapsePerLayerIntoScanPartition"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalGroupByLayer":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) in {"LogicalScanNodes", "LogicalScanEdges"}

    def apply(self, plan: LogicalOp) -> LogicalOp:
        scan = plan.children[0]
        new_scan = copy.copy(scan)
        new_scan.partition_by_layer = True  # type: ignore[attr-defined]
        new_plan = copy.copy(plan)
        new_plan.children = [new_scan] + list(plan.children[1:])
        return new_plan


# ---------------------------------------------------------------------------
# Rule 12: Convert coverage to bitmask
# ---------------------------------------------------------------------------


class ConvertCoverageToBitmaskAggregation(OptimizationRule):
    """Tag ``LogicalCoverage`` to use a bitmask-based aggregation."""

    name = "ConvertCoverageToBitmaskAggregation"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalCoverage":
            return False
        return not getattr(plan, "use_bitmask", False)

    def apply(self, plan: LogicalOp) -> LogicalOp:
        new_plan = copy.copy(plan)
        new_plan.use_bitmask = True  # type: ignore[attr-defined]
        return new_plan


# ---------------------------------------------------------------------------
# Rule 13: Short-circuit empty layer
# ---------------------------------------------------------------------------


class ShortCircuitEmptyLayer(OptimizationRule):
    """Replace a scan on a known-empty layer with an empty-scan node."""

    name = "ShortCircuitEmptyLayer"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalLayerFilter":
            return False
        layers = getattr(plan, "layers", None)
        return isinstance(layers, (list, set)) and len(layers) == 0

    def apply(self, plan: LogicalOp) -> LogicalOp:
        from .plan_nodes import LogicalEmptyScan

        return LogicalEmptyScan(children=[])


# ---------------------------------------------------------------------------
# Rule 14: Shared base compute for UQ
# ---------------------------------------------------------------------------


class ConvertUQComputeToSharedBaseCompute(OptimizationRule):
    """Share the base-network compute result across UQ replicates."""

    name = "ConvertUQComputeToSharedBaseCompute"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalUQ":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalCompute"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner = plan.children[0]
        new_inner = copy.copy(inner)
        new_inner.shared_base = True  # type: ignore[attr-defined]
        new_plan = copy.copy(plan)
        new_plan.children = [new_inner] + list(plan.children[1:])
        return new_plan


# ---------------------------------------------------------------------------
# Rule 15: Merge multiple computes into single pass
# ---------------------------------------------------------------------------


class MergeMultipleComputesIntoSinglePass(OptimizationRule):
    """Merge two adjacent ``LogicalCompute`` nodes into one multi-measure pass."""

    name = "MergeMultipleComputesIntoSinglePass"

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalCompute":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalCompute"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner = plan.children[0]
        combined = list(getattr(plan, "measures", [])) + list(getattr(inner, "measures", []))
        merged = copy.copy(plan)
        merged.measures = combined  # type: ignore[attr-defined]
        merged.children = list(inner.children)
        return merged


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

ALL_RULES: List[OptimizationRule] = [
    PushLayerFilterBelowCompute(),
    PushFilterBelowCompute(),
    PushFilterBelowAggregate(),
    CombineAdjacentFilters(),
    ReorderFiltersBySelectivity(),
    ConvertOrderByLimitToTopK(),
    RemoveRedundantProject(),
    EarlyLimitPushdown(),
    ConvertAggregateToHashIfSmallGroups(),
    UseCachedCentralityIfAvailable(),
    CollapsePerLayerIntoScanPartition(),
    ConvertCoverageToBitmaskAggregation(),
    ShortCircuitEmptyLayer(),
    ConvertUQComputeToSharedBaseCompute(),
    MergeMultipleComputesIntoSinglePass(),
]


class RuleEngine:
    """Iteratively applies all registered rules until fixpoint."""

    def __init__(
        self,
        rules: Optional[List[OptimizationRule]] = None,
        max_iter: int = 10,
    ) -> None:
        self.rules = rules if rules is not None else list(ALL_RULES)
        self.max_iter = max_iter

    def _apply_once(self, plan: LogicalOp) -> tuple[LogicalOp, List[str]]:
        """Apply each rule once to *plan* tree (top-down DFS).

        Returns the rewritten plan and the list of rule names that fired.
        """
        applied: List[str] = []
        for rule in self.rules:
            try:
                if rule.match(plan):
                    plan = rule.apply(plan)
                    applied.append(rule.name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Rule %s failed: %s", rule.name, exc)

        # Recurse into children
        new_children: List[LogicalOp] = []
        for child in plan.children:
            new_child, child_applied = self._apply_once(child)
            new_children.append(new_child)
            applied.extend(child_applied)

        if new_children != list(plan.children):
            plan = copy.copy(plan)
            plan.children = new_children

        return plan, applied

    def rewrite(self, plan: LogicalOp) -> tuple[LogicalOp, List[str]]:
        """Iteratively rewrite *plan* until fixpoint or *max_iter* rounds."""
        all_applied: List[str] = []
        for _ in range(self.max_iter):
            new_plan, applied = self._apply_once(plan)
            all_applied.extend(applied)
            if not applied:
                break
            plan = new_plan
        return plan, all_applied


# Public alias for ALL_RULES expected by the package __init__
BUILTIN_RULES: List[OptimizationRule] = ALL_RULES
