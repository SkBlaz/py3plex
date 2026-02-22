"""Cost model for the py3plex query optimizer.

The :class:`CostModel` produces a :class:`CostEstimate` for a given
:class:`~py3plex.optimizer.plan_nodes.LogicalOp` node.  Estimates are *rough*
but directionally correct so that the optimizer can compare two equivalent
plans.

NetworkStats
~~~~~~~~~~~~
The model accepts a :class:`NetworkStats` snapshot that can be cheaply
extracted from a multilayer network object.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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
    LogicalScanEdges,
    LogicalScanNodes,
    LogicalUQ,
)


@dataclass
class NetworkStats:
    """Lightweight statistics snapshot extracted from a network."""

    node_count: int = 0
    edge_count: int = 0
    layer_count: int = 1
    avg_degree: float = 0.0
    # Maps layer_name -> node count in that layer
    layer_sizes: Dict[str, int] = field(default_factory=dict)
    density: float = 0.0

    @classmethod
    def from_network(cls, network: Any) -> "NetworkStats":
        """Extract statistics from a ``multi_layer_network`` instance."""
        try:
            nodes = list(network.get_nodes())
            edges = list(network.get_edges())
            layers = list(network.get_layers())
            node_count = len(nodes)
            edge_count = len(edges)
            layer_count = max(len(layers), 1)
            avg_degree = (2 * edge_count / node_count) if node_count > 0 else 0.0

            layer_sizes: Dict[str, int] = {}
            for layer in layers:
                layer_nodes = [n for n in nodes if len(n) > 1 and n[1] == layer]
                layer_sizes[str(layer)] = len(layer_nodes)

            density = (
                edge_count / (node_count * (node_count - 1) / 2)
                if node_count > 1
                else 0.0
            )
            return cls(
                node_count=node_count,
                edge_count=edge_count,
                layer_count=layer_count,
                avg_degree=avg_degree,
                layer_sizes=layer_sizes,
                density=min(density, 1.0),
            )
        except Exception:
            return cls()


@dataclass
class CostEstimate:
    """Cost estimate for a logical operation."""

    cpu_cost: float = 0.0
    memory_cost: float = 0.0
    io_cost: float = 0.0
    total_cost: float = 0.0
    estimated_rows: int = 0

    def __add__(self, other: "CostEstimate") -> "CostEstimate":
        return CostEstimate(
            cpu_cost=self.cpu_cost + other.cpu_cost,
            memory_cost=self.memory_cost + other.memory_cost,
            io_cost=self.io_cost + other.io_cost,
            total_cost=self.total_cost + other.total_cost,
            estimated_rows=max(self.estimated_rows, other.estimated_rows),
        )


class CostModel:
    """Estimate the cost of logical plan nodes.

    Parameters
    ----------
    stats:
        Pre-computed :class:`NetworkStats`.  If *None*, a zero-stats object
        is used and all estimates will be very rough.
    """

    # Calibration constants
    _SCAN_COST_PER_ROW = 0.01
    _FILTER_COST_PER_ROW = 0.05
    _COMPUTE_COST_CENTRALITY = 50.0   # per measure, per 1000 nodes
    _AGG_COST_PER_ROW = 0.1
    _ORDER_COST_PER_ROW = 0.2         # O(n log n) approximated as linear here
    _UQ_MULTIPLIER = 20               # 20 bootstrap samples by default
    _NULL_MODEL_MULTIPLIER = 10

    def __init__(self, stats: Optional[NetworkStats] = None) -> None:
        self._stats = stats or NetworkStats()

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def estimate(self, op: LogicalOp) -> CostEstimate:
        """Return a :class:`CostEstimate` for *op* (not recursive)."""
        s = self._stats
        # Delegate to per-type helpers
        if isinstance(op, LogicalScanNodes):
            rows = s.node_count or 100
            return CostEstimate(
                cpu_cost=rows * self._SCAN_COST_PER_ROW,
                estimated_rows=rows,
                total_cost=rows * self._SCAN_COST_PER_ROW,
            )

        if isinstance(op, LogicalScanEdges):
            rows = s.edge_count or 200
            return CostEstimate(
                cpu_cost=rows * self._SCAN_COST_PER_ROW,
                estimated_rows=rows,
                total_cost=rows * self._SCAN_COST_PER_ROW,
            )

        if isinstance(op, LogicalLayerFilter):
            parent_rows = _child_rows(op, s.node_count)
            selectivity = self._layer_selectivity(op, s)
            rows = max(1, int(parent_rows * selectivity))
            cost = parent_rows * self._FILTER_COST_PER_ROW
            return CostEstimate(cpu_cost=cost, estimated_rows=rows, total_cost=cost)

        if isinstance(op, LogicalFilter):
            parent_rows = _child_rows(op, s.node_count)
            sel = self._predicate_selectivity(op, s)
            rows = max(1, int(parent_rows * sel))
            cost = parent_rows * self._FILTER_COST_PER_ROW
            return CostEstimate(cpu_cost=cost, estimated_rows=rows, total_cost=cost)

        if isinstance(op, LogicalCompute):
            parent_rows = _child_rows(op, s.node_count)
            n_measures = max(1, len(op.measures))
            # Betweenness / closeness are expensive; pagerank is medium
            heavy = sum(
                1
                for m in op.measures
                if any(
                    kw in m
                    for kw in ("betweenness", "closeness")
                )
            )
            light = n_measures - heavy
            cost = (
                heavy * self._COMPUTE_COST_CENTRALITY * max(1, s.node_count / 1000)
                + light * self._COMPUTE_COST_CENTRALITY * 0.2 * max(1, s.node_count / 1000)
            )
            return CostEstimate(
                cpu_cost=cost,
                memory_cost=parent_rows * 0.001,
                estimated_rows=parent_rows,
                total_cost=cost,
            )

        if isinstance(op, (LogicalGroupByLayer, LogicalGroupByLayerPair)):
            parent_rows = _child_rows(op, s.node_count)
            cost = parent_rows * self._AGG_COST_PER_ROW
            return CostEstimate(cpu_cost=cost, estimated_rows=parent_rows, total_cost=cost)

        if isinstance(op, LogicalAggregate):
            parent_rows = _child_rows(op, s.node_count)
            group_count = max(1, s.layer_count)
            cost = parent_rows * self._AGG_COST_PER_ROW
            return CostEstimate(cpu_cost=cost, estimated_rows=group_count, total_cost=cost)

        if isinstance(op, LogicalCoverage):
            parent_rows = _child_rows(op, s.node_count)
            cost = parent_rows * 0.05
            return CostEstimate(cpu_cost=cost, estimated_rows=parent_rows, total_cost=cost)

        if isinstance(op, LogicalOrderBy):
            parent_rows = _child_rows(op, s.node_count)
            cost = parent_rows * self._ORDER_COST_PER_ROW * math.log2(max(2, parent_rows))
            return CostEstimate(cpu_cost=cost, estimated_rows=parent_rows, total_cost=cost)

        if isinstance(op, LogicalLimit):
            parent_rows = _child_rows(op, s.node_count)
            rows = min(op.n, parent_rows)
            return CostEstimate(cpu_cost=0.0, estimated_rows=rows, total_cost=0.0)

        if isinstance(op, LogicalUQ):
            parent_rows = _child_rows(op, s.node_count)
            n_samples = op.uq_spec.get("n_samples", self._UQ_MULTIPLIER)
            cost = parent_rows * self._FILTER_COST_PER_ROW * n_samples
            return CostEstimate(cpu_cost=cost, estimated_rows=parent_rows, total_cost=cost)

        if isinstance(op, LogicalNullModel):
            parent_rows = _child_rows(op, s.node_count)
            cost = s.edge_count * self._NULL_MODEL_MULTIPLIER
            return CostEstimate(cpu_cost=cost, estimated_rows=parent_rows, total_cost=cost)

        # Default / unknown
        parent_rows = _child_rows(op, 100)
        return CostEstimate(cpu_cost=1.0, estimated_rows=parent_rows, total_cost=1.0)

    # ------------------------------------------------------------------
    # Selectivity helpers
    # ------------------------------------------------------------------

    def _layer_selectivity(self, op: "LogicalLayerFilter", stats: NetworkStats) -> float:
        if not op.layers or stats.layer_count == 0:
            return 1.0
        return min(1.0, len(op.layers) / stats.layer_count)

    def _predicate_selectivity(self, op: "LogicalFilter", stats: NetworkStats) -> float:
        """Rough selectivity: 0.3 for degree filters, 0.5 otherwise."""
        for cond in op.conditions:
            attr = getattr(cond, "field", None) or (
                cond.get("field") if isinstance(cond, dict) else None
            )
            if attr and "degree" in str(attr):
                return 0.3
        return 0.5

    # ------------------------------------------------------------------
    # Whole-tree cost
    # ------------------------------------------------------------------

    def total_tree_cost(self, root: LogicalOp) -> float:
        """Recursively sum cost estimates for all nodes in the plan tree."""
        estimate = self.estimate(root)
        total = estimate.total_cost
        for child in root.children:
            total += self.total_tree_cost(child)
        return total


def _child_rows(op: LogicalOp, default: int) -> int:
    """Return estimated_rows of the first child, or *default*."""
    if op.children and op.children[0].estimated_rows is not None:
        return op.children[0].estimated_rows
    return default
