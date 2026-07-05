"""Logical and physical plan objects for the DSL compiler pipeline.

These are lightweight frozen dataclasses that represent the output of the
planner / rewrite pass.  They are **inspectable** — user code can examine
``plan.ops`` and ``plan.metadata`` — but they carry no executable state
themselves.

Usage::

    from py3plex.dsl.plan import LogicalPlan, PhysicalPlan
    from py3plex.dsl.plan import (
        OP_SCAN_NODES, OP_LAYER_FILTER, OP_COMPUTE_METRIC,
    )

    program = q.compile()
    plan = program.plan(net)   # returns PlannedQuery from planner.py
    # or build a LogicalPlan manually:
    lp = LogicalPlan(ops=(OP_SCAN_NODES, OP_LAYER_FILTER))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

__all__ = [
    # Constants for logical op names
    "OP_SCAN_NODES",
    "OP_SCAN_EDGES",
    "OP_RESOLVE_LAYERS",
    "OP_LAYER_FILTER",
    "OP_PREDICATE_FILTER",
    "OP_COMPUTE_METRIC",
    "OP_GROUP_BY_LAYER",
    "OP_GROUP_BY_LAYER_PAIR",
    "OP_TOP_K",
    "OP_COVERAGE_FILTER",
    "OP_AGGREGATE",
    "OP_ORDER_BY",
    "OP_LIMIT",
    "OP_PROJECT",
    # Plan dataclasses
    "LogicalPlan",
    "PhysicalPlan",
]

# ---------------------------------------------------------------------------
# Logical operator name constants
# ---------------------------------------------------------------------------

OP_SCAN_NODES: str = "ScanNodes"
OP_SCAN_EDGES: str = "ScanEdges"
OP_RESOLVE_LAYERS: str = "ResolveLayers"
OP_LAYER_FILTER: str = "LayerFilter"
OP_PREDICATE_FILTER: str = "PredicateFilter"
OP_COMPUTE_METRIC: str = "ComputeMetric"
OP_GROUP_BY_LAYER: str = "GroupByLayer"
OP_GROUP_BY_LAYER_PAIR: str = "GroupByLayerPair"
OP_TOP_K: str = "TopK"
OP_COVERAGE_FILTER: str = "CoverageFilter"
OP_AGGREGATE: str = "Aggregate"
OP_ORDER_BY: str = "OrderBy"
OP_LIMIT: str = "Limit"
OP_PROJECT: str = "Project"


# ---------------------------------------------------------------------------
# Plan dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LogicalPlan:
    """An ordered sequence of logical operators.

    Attributes:
        ops: Tuple of logical operator name strings, in execution order.
        metadata: Arbitrary key/value metadata about the plan (e.g.
            ``{"required_measures": [...], "cost_hint": "expensive"}``).
    """

    ops: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure ops is always a tuple even if a list was passed
        object.__setattr__(self, "ops", tuple(self.ops))

    def __str__(self) -> str:
        lines = [f"LogicalPlan ({len(self.ops)} ops):"]
        for i, op in enumerate(self.ops, start=1):
            lines.append(f"  {i}. {op}")
        return "\n".join(lines)


@dataclass(frozen=True)
class PhysicalPlan:
    """An ordered sequence of physical operators.

    Attributes:
        ops: Tuple of physical operator name strings, in execution order.
        metadata: Arbitrary key/value metadata (planner config, timings, …).
    """

    ops: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "ops", tuple(self.ops))

    def __str__(self) -> str:
        lines = [f"PhysicalPlan ({len(self.ops)} ops):"]
        for i, op in enumerate(self.ops, start=1):
            lines.append(f"  {i}. {op}")
        return "\n".join(lines)
