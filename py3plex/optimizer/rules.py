"""Rule-based and cost-based rewrite rules for the py3plex query optimizer.

Each rule is a stand-alone callable that accepts a :class:`LogicalOp` tree,
decides whether it matches a specific pattern, and returns a (potentially
rewritten) tree.  The :class:`RuleEngine` iterates all registered rules to
fixpoint (up to ``OPTIMIZER_MAX_ITER`` rounds).
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .plan_nodes import (
    LogicalCompute,
    LogicalFilter,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalOp,
)
from py3plex.dsl.errors import DslExecutionError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class OptimizationRule:
    """Base class for deterministic, semantics-preserving plan rewrites."""

    id: str = ""
    name: str = "BaseRule"
    description: str = ""

    def match(self, plan: LogicalOp) -> bool:  # noqa: ARG002
        """Return ``True`` if this rule can be applied to *plan*."""
        return False

    def matches(self, plan: LogicalOp, context: Any = None) -> bool:  # noqa: ARG002
        """Return whether this rule applies to *plan* in *context*."""
        return self.match(plan)

    def apply(self, plan: LogicalOp) -> LogicalOp:
        """Return a rewritten logical plan (or the same node if unchanged)."""
        return plan

    def rewrite(self, plan: LogicalOp, context: Any = None) -> LogicalOp:  # noqa: ARG002
        """Return a rewritten plan without modifying the input plan."""
        return self.apply(plan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _type_name(op: LogicalOp) -> str:
    return type(op).__name__


def _stable_value(value: Any) -> Any:
    """Convert plan attributes to a deterministic JSON-compatible value."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            item.name: _stable_value(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, dict):
        entries = [
            (_stable_value(key), _stable_value(item))
            for key, item in value.items()
        ]
        return sorted(entries, key=lambda pair: json.dumps(pair[0], sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_stable_value(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    if callable(value):
        raise TypeError("callables cannot be included in optimizer plan fingerprints")
    if hasattr(value, "__dict__"):
        return {
            "__type__": type(value).__qualname__,
            "attributes": {
                key: _stable_value(item)
                for key, item in sorted(vars(value).items())
                if not key.startswith("_")
            },
        }
    raise TypeError(
        f"unsupported optimizer plan value: {type(value).__qualname__}"
    )


def plan_fingerprint(plan: LogicalOp) -> str:
    """Return a stable SHA-256 fingerprint of a logical plan tree."""
    def _node_payload(node: LogicalOp) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": type(node).__qualname__}
        for item in fields(node):
            value = getattr(node, item.name)
            if item.name == "children":
                payload[item.name] = [_node_payload(child) for child in value]
            else:
                payload[item.name] = _stable_value(value)
        return payload

    try:
        serialized = json.dumps(
            _node_payload(plan), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        raise DslExecutionError(f"Unable to fingerprint optimizer plan: {exc}") from exc
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def render_logical_plan(plan: LogicalOp) -> str:
    """Render a logical plan as a stable, indented tree."""
    labels = {
        "LogicalScanNodes": "Scan[nodes]",
        "LogicalScanEdges": "Scan[edges]",
        "LogicalFilter": "Filter",
        "LogicalLayerFilter": "LayerFilter",
        "LogicalCompute": "Compute",
        "LogicalAggregate": "Aggregate",
        "LogicalGroupByLayer": "GroupByLayer",
        "LogicalGroupByLayerPair": "GroupByLayerPair",
        "LogicalCoverage": "Coverage",
        "LogicalOrderBy": "Sort",
        "LogicalLimit": "Limit",
        "LogicalUQ": "UQ",
        "LogicalNullModel": "NullModel",
        "LogicalProject": "Project",
        "LogicalEmptyScan": "EmptyScan",
    }
    lines: List[str] = []
    stack: List[Tuple[LogicalOp, str, bool]] = [(plan, "", True)]
    while stack:
        node, prefix, is_last = stack.pop()
        name = type(node).__name__
        details: List[str] = []
        for attr in ("conditions", "layers", "measures", "keys", "n", "columns"):
            value = getattr(node, attr, None)
            if value not in (None, [], ""):
                details.append(f"{attr}={_stable_value(value)}")
        label = labels.get(name, name)
        if details:
            label += "[" + ", ".join(details) + "]"
        if lines:
            lines.append(prefix + ("└── " if is_last else "├── ") + label)
            child_prefix = prefix + ("    " if is_last else "│   ")
        else:
            lines.append(label)
            child_prefix = ""
        children = list(getattr(node, "children", []))
        for index in range(len(children) - 1, -1, -1):
            stack.append((children[index], child_prefix, index == len(children) - 1))
    return "\n".join(lines)


@dataclass(frozen=True)
class RewriteEvent:
    """One deterministic rewrite application."""

    rule_id: str
    rule_name: str
    pass_number: int
    before_fingerprint: str
    after_fingerprint: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-compatible event."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "pass_number": self.pass_number,
            "before_fingerprint": self.before_fingerprint,
            "after_fingerprint": self.after_fingerprint,
            "details": _stable_value(self.details),
        }


@dataclass(frozen=True)
class OptimizationTrace:
    """Structured summary of a bounded optimizer run."""

    rules_considered: Tuple[str, ...]
    events: Tuple[RewriteEvent, ...]
    passes: int
    original_fingerprint: str
    optimized_fingerprint: str

    @property
    def rules_applied(self) -> List[str]:
        """Return unique applied rule IDs in first-application order."""
        return list(dict.fromkeys(event.rule_id for event in self.events))

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-compatible trace."""
        return {
            "rules_considered": list(self.rules_considered),
            "rules_applied": self.rules_applied,
            "passes": self.passes,
            "original_fingerprint": self.original_fingerprint,
            "optimized_fingerprint": self.optimized_fingerprint,
            "events": [event.to_dict() for event in self.events],
        }


@dataclass(frozen=True)
class RewriteResult:
    """Original and optimized plans together with their rewrite trace."""

    original_plan: LogicalOp
    optimized_plan: LogicalOp
    trace: OptimizationTrace


def _rule_details(before: LogicalOp, after: LogicalOp) -> Dict[str, Any]:
    details: Dict[str, Any] = {"node_type": type(before).__name__}
    if isinstance(before, LogicalFilter) and isinstance(after, LogicalFilter):
        details.update(
            filters_before=len(before.conditions),
            filters_after=len(after.conditions),
        )
    elif isinstance(before, LogicalLayerFilter) and isinstance(after, LogicalLayerFilter):
        details.update(layers_before=list(before.layers), layers_after=list(after.layers))
    elif isinstance(before, LogicalCompute) and isinstance(after, LogicalCompute):
        details.update(
            computations_before=list(before.measures),
            computations_after=list(after.measures),
        )
    return details


# ---------------------------------------------------------------------------
# Rule 1: Push layer filter below compute
# ---------------------------------------------------------------------------


class PushLayerFilterBelowCompute(OptimizationRule):
    """Move ``LogicalLayerFilter`` before ``LogicalCompute``."""

    id = "X001"
    name = "PushLayerFilterBelowCompute"
    description = "Experimental output-layer filter movement across computation."

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

    id = "R003"
    name = "PushFilterBelowCompute"
    description = "Push intrinsic-field filters beneath computation."

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
        conditions = getattr(child, "conditions", [])
        for pred in conditions:
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

    id = "X002"
    name = "PushFilterBelowAggregate"
    description = "Experimental filter movement across aggregation."

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

    id = "R001"
    name = "CombineAdjacentFilters"
    description = "Fuse adjacent filters while preserving predicate order."

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalFilter":
            return False
        if not plan.children:
            return False
        return _type_name(plan.children[0]) == "LogicalFilter"

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner_filt = plan.children[0]
        combined_conditions = list(getattr(inner_filt, "conditions", [])) + list(
            getattr(plan, "conditions", [])
        )
        merged = copy.copy(plan)
        merged.conditions = combined_conditions  # type: ignore[attr-defined]
        merged.children = list(inner_filt.children)
        return merged


class ConstantPredicateSimplification(OptimizationRule):
    """Remove identity ``True`` predicates from an AND condition list."""

    id = "R002"
    name = "ConstantPredicateSimplification"
    description = "Remove literal True conditions from conjunctive filter lists."

    def match(self, plan: LogicalOp) -> bool:
        return isinstance(plan, LogicalFilter) and any(
            condition is True for condition in plan.conditions
        )

    def apply(self, plan: LogicalOp) -> LogicalOp:
        simplified = copy.copy(plan)
        simplified.conditions = [
            condition for condition in plan.conditions if condition is not True
        ]
        return simplified


class PruneNestedLayerFilters(OptimizationRule):
    """Intersect adjacent concrete layer filters without changing results."""

    id = "R004"
    name = "PruneNestedLayerFilters"
    description = "Intersect adjacent concrete layer filters."

    def match(self, plan: LogicalOp) -> bool:
        return (
            isinstance(plan, LogicalLayerFilter)
            and len(plan.children) == 1
            and isinstance(plan.children[0], LogicalLayerFilter)
            and all(isinstance(layer, str) for layer in plan.layers)
            and all(isinstance(layer, str) for layer in plan.children[0].layers)
        )

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner = plan.children[0]
        allowed = set(plan.layers)
        merged = copy.copy(plan)
        merged.layers = list(dict.fromkeys(
            layer for layer in inner.layers if layer in allowed
        ))
        merged.children = list(inner.children)
        return merged


class DeduplicateComputations(OptimizationRule):
    """Remove exact duplicate deterministic computations in one compute stage."""

    id = "R006"
    name = "DeduplicateComputations"
    description = "Deduplicate identical deterministic computations in a stage."

    @staticmethod
    def _is_deterministic(measure: str) -> bool:
        try:
            from py3plex.dsl.metrics import find_metric
            spec = find_metric(measure)
            return bool(spec and spec.deterministic)
        except (ImportError, AttributeError):
            return False

    @staticmethod
    def _is_plain_signature(signature: str) -> bool:
        try:
            details = json.loads(signature)
        except (TypeError, ValueError):
            return False
        return not any(
            details.get(key)
            for key in ("uncertainty", "approx")
        ) and not any(
            details.get(key) is not None
            for key in (
                "method", "n_samples", "ci", "bootstrap_unit",
                "bootstrap_mode", "n_null", "null_model", "random_state", "kind",
            )
        )

    def match(self, plan: LogicalOp) -> bool:
        if not isinstance(plan, LogicalCompute):
            return False
        signatures = plan.computation_signatures
        if len(signatures) != len(plan.measures):
            signatures = [json.dumps({"name": name}, sort_keys=True) for name in plan.measures]
        seen = set()
        for name, signature in zip(plan.measures, signatures):
            if (
                self._is_deterministic(name)
                and self._is_plain_signature(signature)
                and signature in seen
            ):
                return True
            seen.add(signature)
        return False

    def apply(self, plan: LogicalOp) -> LogicalOp:
        signatures = plan.computation_signatures
        if len(signatures) != len(plan.measures):
            signatures = [json.dumps({"name": name}, sort_keys=True) for name in plan.measures]
        seen = set()
        measures: List[str] = []
        retained_signatures: List[str] = []
        for name, signature in zip(plan.measures, signatures):
            duplicate_is_safe = (
                self._is_deterministic(name)
                and self._is_plain_signature(signature)
            )
            if duplicate_is_safe and signature in seen:
                continue
            seen.add(signature)
            measures.append(name)
            retained_signatures.append(signature)
        rewritten = copy.copy(plan)
        rewritten.measures = measures
        rewritten.computation_signatures = retained_signatures
        return rewritten


class CollapseNestedLimits(OptimizationRule):
    """Collapse adjacent non-negative limits to their minimum."""

    id = "R007"
    name = "CollapseNestedLimits"
    description = "Collapse adjacent non-negative limits to the stricter bound."

    def match(self, plan: LogicalOp) -> bool:
        return (
            isinstance(plan, LogicalLimit)
            and plan.n >= 0
            and len(plan.children) == 1
            and isinstance(plan.children[0], LogicalLimit)
            and plan.children[0].n >= 0
        )

    def apply(self, plan: LogicalOp) -> LogicalOp:
        inner = plan.children[0]
        collapsed = copy.copy(plan)
        collapsed.n = min(plan.n, inner.n)
        collapsed.children = list(inner.children)
        return collapsed


# ---------------------------------------------------------------------------
# Rule 5: Reorder filters by selectivity
# ---------------------------------------------------------------------------


class ReorderFiltersBySelectivity(OptimizationRule):
    """Put cheaper / more-selective predicates first."""

    id = "X003"
    name = "ReorderFiltersBySelectivity"
    description = "Experimental predicate reordering heuristic."

    def match(self, plan: LogicalOp) -> bool:
        if _type_name(plan) != "LogicalFilter":
            return False
        conditions = list(getattr(plan, "conditions", []))
        return len(conditions) > 1

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
        new_plan.conditions = sorted(  # type: ignore[attr-defined]
            getattr(plan, "conditions", []), key=_priority
        )
        return new_plan


# ---------------------------------------------------------------------------
# Rule 6: Convert OrderBy+Limit to TopK
# ---------------------------------------------------------------------------


class ConvertOrderByLimitToTopK(OptimizationRule):
    """Replace ``LogicalOrderBy`` + ``LogicalLimit`` with ``LogicalTopK``."""

    id = "X004"
    name = "ConvertOrderByLimitToTopK"
    description = "Experimental sort-and-limit physical strategy rewrite."

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

    id = "R005"
    name = "RemoveRedundantProject"
    description = "Remove an empty project that denotes selection of all columns."

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

    id = "X005"
    name = "EarlyLimitPushdown"
    description = "Experimental early-limit movement."

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

    id = "X006"
    name = "ConvertAggregateToHashIfSmallGroups"
    description = "Experimental aggregate strategy selection."

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

    id = "X007"
    name = "UseCachedCentralityIfAvailable"
    description = "Experimental cache lookup rewrite."

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

    id = "X008"
    name = "CollapsePerLayerIntoScanPartition"
    description = "Experimental grouping/scan fusion."

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

    id = "X009"
    name = "ConvertCoverageToBitmaskAggregation"
    description = "Experimental coverage implementation selection."

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

    id = "X010"
    name = "ShortCircuitEmptyLayer"
    description = "Experimental empty-layer scan short-circuit."

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

    id = "X011"
    name = "ConvertUQComputeToSharedBaseCompute"
    description = "Experimental shared base computation for UQ."

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

    id = "X012"
    name = "MergeMultipleComputesIntoSinglePass"
    description = "Experimental adjacent compute-stage fusion."

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

DEFAULT_REWRITE_RULES: Tuple[OptimizationRule, ...] = (
    CombineAdjacentFilters(),
    ConstantPredicateSimplification(),
    PruneNestedLayerFilters(),
    DeduplicateComputations(),
    CollapseNestedLimits(),
)

# Kept as a compatibility alias; unsafe experimental rules remain available
# by explicit construction, but are not part of the default rule set.
ALL_RULES: List[OptimizationRule] = list(DEFAULT_REWRITE_RULES)

LEGACY_EXPERIMENTAL_RULES: Tuple[OptimizationRule, ...] = (
    PushLayerFilterBelowCompute(),
    PushFilterBelowCompute(),
    PushFilterBelowAggregate(),
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
)


def validate_plan(plan: LogicalOp) -> None:
    """Validate the structural invariants required by logical rewrites."""
    stack = [plan]
    while stack:
        node = stack.pop()
        if not isinstance(node, LogicalOp):
            raise DslExecutionError(
                f"Invalid optimizer plan child: expected LogicalOp, got {type(node).__name__}."
            )
        if not isinstance(node.children, list) or any(
            not isinstance(child, LogicalOp) for child in node.children
        ):
            raise DslExecutionError(
                f"Invalid children on optimizer node {type(node).__name__}."
            )
        if isinstance(node, LogicalLimit) and not isinstance(node.n, int):
            raise DslExecutionError("LogicalLimit requires an integer limit.")
        stack.extend(node.children)


class RuleEngine:
    """Apply an explicit, ordered set of rules with bounded convergence."""

    def __init__(
        self,
        rules: Optional[Sequence[OptimizationRule]] = None,
        max_iter: int = 10,
    ) -> None:
        if max_iter < 1:
            raise DslExecutionError("Optimizer max_iter must be at least 1.")
        self.rules = tuple(rules if rules is not None else DEFAULT_REWRITE_RULES)
        self.max_iter = max_iter
        identifiers = [rule.id for rule in self.rules]
        if any(not identifier for identifier in identifiers):
            raise DslExecutionError("Every optimizer rule must define a stable rule ID.")
        if len(set(identifiers)) != len(identifiers):
            duplicate = next(
                identifier for identifier in identifiers if identifiers.count(identifier) > 1
            )
            raise DslExecutionError(f"Duplicate optimizer rule ID: {duplicate}.")

    def describe_rules(self) -> List[Dict[str, str]]:
        """Return deterministic metadata for the configured rule order."""
        return [
            {"id": rule.id, "name": rule.name, "description": rule.description}
            for rule in self.rules
        ]

    def _apply_once(
        self, plan: LogicalOp, pass_number: int, context: Any
    ) -> Tuple[LogicalOp, List[RewriteEvent]]:
        """Apply one bottom-up pass without mutating the source plan."""
        events: List[RewriteEvent] = []
        rewritten: Dict[int, LogicalOp] = {}
        stack: List[Tuple[LogicalOp, bool]] = [(plan, False)]
        while stack:
            node, visited = stack.pop()
            if not visited:
                stack.append((node, True))
                for child in reversed(node.children):
                    stack.append((child, False))
                continue

            current = copy.copy(node)
            current.children = [rewritten[id(child)] for child in node.children]
            for rule in self.rules:
                try:
                    if not rule.matches(current, context):
                        continue
                    before_fingerprint = plan_fingerprint(current)
                    candidate = rule.rewrite(copy.deepcopy(current), context)
                    if not isinstance(candidate, LogicalOp):
                        raise DslExecutionError(
                            f"Optimizer rule {rule.id} returned {type(candidate).__name__}, "
                            "expected LogicalOp."
                        )
                    after_fingerprint = plan_fingerprint(candidate)
                    if before_fingerprint != after_fingerprint:
                        events.append(
                            RewriteEvent(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                pass_number=pass_number,
                                before_fingerprint=before_fingerprint,
                                after_fingerprint=after_fingerprint,
                                details=_rule_details(current, candidate),
                            )
                        )
                        current = candidate
                except DslExecutionError:
                    raise
                except Exception as exc:
                    raise DslExecutionError(
                        f"Optimizer rule {rule.id} ({rule.name}) failed: {exc}"
                    ) from exc
            rewritten[id(node)] = current
        result = rewritten[id(plan)]
        validate_plan(result)
        return result, events

    def rewrite(self, plan: LogicalOp) -> tuple[LogicalOp, List[str]]:
        """Compatibility wrapper returning the plan and applied rule names."""
        result = self.optimize(plan)
        return result.optimized_plan, [event.rule_name for event in result.trace.events]

    def optimize(self, plan: LogicalOp, context: Any = None) -> RewriteResult:
        """Optimize *plan*, returning immutable trace and original/optimized trees."""
        validate_plan(plan)
        original = copy.deepcopy(plan)
        original_fingerprint = plan_fingerprint(original)
        current = copy.deepcopy(plan)
        seen = {original_fingerprint}
        events: List[RewriteEvent] = []
        passes = 0

        for pass_number in range(1, self.max_iter + 1):
            rewritten, pass_events = self._apply_once(current, pass_number, context)
            passes = pass_number
            after_fingerprint = plan_fingerprint(rewritten)
            logger.debug("Optimizer pass %d considered %d rule(s).", pass_number, len(self.rules))
            for event in pass_events:
                logger.debug(
                    "%s %s: applied",
                    event.rule_id,
                    event.rule_name,
                )
            if after_fingerprint == plan_fingerprint(current):
                current = rewritten
                break
            if after_fingerprint in seen:
                raise DslExecutionError(
                    f"Optimizer rewrite cycle detected after pass {pass_number}."
                )
            seen.add(after_fingerprint)
            events.extend(pass_events)
            current = rewritten
            if pass_number == self.max_iter:
                probe, _ = self._apply_once(current, pass_number + 1, context)
                if plan_fingerprint(probe) != after_fingerprint:
                    raise DslExecutionError(
                        f"Optimizer failed to converge after {self.max_iter} passes."
                    )

        optimized_fingerprint = plan_fingerprint(current)
        trace = OptimizationTrace(
            rules_considered=tuple(rule.id for rule in self.rules),
            events=tuple(events),
            passes=passes,
            original_fingerprint=original_fingerprint,
            optimized_fingerprint=optimized_fingerprint,
        )
        return RewriteResult(original, current, trace)


BUILTIN_RULES: List[OptimizationRule] = list(DEFAULT_REWRITE_RULES)
