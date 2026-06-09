"""Logical and physical plan node types for the py3plex optimizer.

This module defines the tree-node primitives shared by both the logical
and physical plan representations.  Nodes are intentionally *simple*
data-classes so that the optimizer rules can pattern-match on ``type(node)``
without any heavyweight class hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------


@dataclass
class LogicalOp:
    """Base class for all logical operator nodes."""

    children: List["LogicalOp"] = field(default_factory=list)
    schema: Dict[str, Any] = field(default_factory=dict)
    estimated_rows: Optional[int] = None


@dataclass
class PhysicalOp:
    """Base class for all physical operator nodes."""

    children: List["PhysicalOp"] = field(default_factory=list)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0

    def execute(self, context: Dict[str, Any]) -> Any:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Logical operators
# ---------------------------------------------------------------------------


@dataclass
class LogicalScanNodes(LogicalOp):
    """Scan all nodes from the network."""


@dataclass
class LogicalScanEdges(LogicalOp):
    """Scan all edges from the network."""


@dataclass
class LogicalFilter(LogicalOp):
    """Apply a predicate filter to items."""

    conditions: List[Any] = field(default_factory=list)
    selectivity: float = 1.0  # fraction of rows expected to pass


@dataclass
class LogicalLayerFilter(LogicalOp):
    """Filter items to a specific set of layers."""

    layers: List[str] = field(default_factory=list)
    selectivity: float = 1.0


@dataclass
class LogicalCompute(LogicalOp):
    """Compute one or more metrics on items."""

    measures: List[str] = field(default_factory=list)


@dataclass
class LogicalAggregate(LogicalOp):
    """Aggregate items using grouping functions."""

    aggregations: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)


@dataclass
class LogicalGroupByLayer(LogicalOp):
    """Group nodes by their layer."""


@dataclass
class LogicalGroupByLayerPair(LogicalOp):
    """Group edges by their (source_layer, target_layer) pair."""


@dataclass
class LogicalCoverage(LogicalOp):
    """Apply cross-group coverage filtering."""

    mode: str = "all"
    k: Optional[int] = None
    fraction: Optional[float] = None


@dataclass
class LogicalOrderBy(LogicalOp):
    """Order items by one or more keys."""

    keys: List[str] = field(default_factory=list)
    desc: bool = False


@dataclass
class LogicalLimit(LogicalOp):
    """Limit result count."""

    n: int = 0


@dataclass
class LogicalUQ(LogicalOp):
    """Wrap child with uncertainty quantification."""

    uq_spec: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogicalNullModel(LogicalOp):
    """Generate null model networks."""

    null_model_spec: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogicalProject(LogicalOp):
    """Project (select) a subset of attributes."""

    columns: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Physical operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalNodeScanNX(PhysicalOp):
    """Scan nodes using the NetworkX backend."""


@dataclass
class PhysicalEdgeScanNX(PhysicalOp):
    """Scan edges using the NetworkX backend."""


@dataclass
class PhysicalFilterVectorized(PhysicalOp):
    """Apply a numeric predicate filter using vectorised operations."""

    conditions: List[Any] = field(default_factory=list)


@dataclass
class PhysicalFilterPython(PhysicalOp):
    """Apply a predicate filter using Python iteration."""

    conditions: List[Any] = field(default_factory=list)


@dataclass
class PhysicalComputeNetworkX(PhysicalOp):
    """Compute centrality measures via NetworkX."""

    measures: List[str] = field(default_factory=list)


@dataclass
class PhysicalComputeCached(PhysicalOp):
    """Serve pre-computed centrality from the global cache."""

    measures: List[str] = field(default_factory=list)
    cache_keys: List[str] = field(default_factory=list)


@dataclass
class PhysicalAggregateHash(PhysicalOp):
    """Aggregate using a hash-map approach (good for small group counts)."""

    aggregations: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)


@dataclass
class PhysicalAggregateSort(PhysicalOp):
    """Aggregate after sorting (good for large sorted datasets)."""

    aggregations: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)


@dataclass
class PhysicalLayerPushdown(PhysicalOp):
    """Push layer filtering into the scan stage."""

    layers: List[str] = field(default_factory=list)


@dataclass
class PhysicalCoverage(PhysicalOp):
    """Execute cross-group coverage logic."""

    mode: str = "all"
    k: Optional[int] = None


@dataclass
class PhysicalTopKHeap(PhysicalOp):
    """Return top-k items using a heap."""

    k: int = 10
    key: str = ""
    desc: bool = True


@dataclass
class PhysicalLimitEarly(PhysicalOp):
    """Cut output to at most *n* items early in the pipeline."""

    n: int = 0


@dataclass
class PhysicalUQMonteCarlo(PhysicalOp):
    """Wrap child with Monte-Carlo UQ sampling."""

    uq_spec: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhysicalNullModelGenerator(PhysicalOp):
    """Generate null model instances."""

    null_model_spec: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Extra logical operators used by optimisation rules
# ---------------------------------------------------------------------------


@dataclass
class LogicalTopK(LogicalOp):
    """Return top-k items by a given key (replaces OrderBy + Limit)."""

    k: int = 10
    key: str = ""
    desc: bool = True


@dataclass
class LogicalCachedCompute(LogicalOp):
    """Compute node that can be satisfied from the global centrality cache."""

    measures: List[str] = field(default_factory=list)


@dataclass
class LogicalEmptyScan(LogicalOp):
    """Placeholder for a known-empty result (e.g. empty layer set)."""
