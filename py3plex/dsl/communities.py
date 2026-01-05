"""Community data structures and utilities for DSL v2.

This module provides the data model for communities as a first-class DSL target.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CommunityRecord:
    """Canonical representation of a community in the network.

    Attributes:
        community_id: Stable identifier for this community (int or str)
        layer_scope: Single layer, multi-layer, or aggregated scope
        members: List of (node_id, layer) tuples that are members
        size: Number of nodes in the community
        intra_edges: Number of edges within the community
        inter_edges: Number of edges crossing community boundary
        density_intra: Density of connections within community
        cut_size: Number of boundary edges (same as inter_edges)
        modularity_contribution: Contribution to overall modularity (if available)
        metadata: Algorithm-specific fields (resolution, seed, etc.)
    """
    community_id: Any
    layer_scope: str  # "single_layer", "multi_layer", "aggregated"
    members: List[Tuple[Any, Any]]
    size: int
    intra_edges: int = 0
    inter_edges: int = 0
    density_intra: float = 0.0
    cut_size: int = 0
    boundary_edges: int = 0  # Alias for cut_size
    modularity_contribution: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure boundary_edges is in sync with inter_edges/cut_size."""
        # Make boundary_edges and cut_size consistent
        if self.cut_size == 0 and self.inter_edges > 0:
            self.cut_size = self.inter_edges
        if self.boundary_edges == 0 and self.inter_edges > 0:
            self.boundary_edges = self.inter_edges
        elif self.boundary_edges == 0 and self.cut_size > 0:
            self.boundary_edges = self.cut_size


def build_community_records(
    network: Any,
    partition: Dict[Tuple[Any, Any], Any],
    name: str = "default",
    metadata: Optional[Dict[str, Any]] = None
) -> List[CommunityRecord]:
    """Build CommunityRecord objects from a partition.

    Args:
        network: Multilayer network object
        partition: Dict mapping (node, layer) tuples to community IDs
        name: Name of the partition (e.g., "louvain", "infomap")
        metadata: Algorithm-specific metadata

    Returns:
        List of CommunityRecord objects
    """
    from collections import defaultdict

    metadata = metadata or {}

    # Group nodes by community
    communities_members: Dict[Any, List[Tuple[Any, Any]]] = defaultdict(list)
    for node_layer, comm_id in partition.items():
        communities_members[comm_id].append(node_layer)

    # Build records
    records = []
    for comm_id, members in communities_members.items():
        # Count edges
        intra_edges = 0
        inter_edges = 0

        # Get member set for fast lookup
        member_set = set(members)

        # Count edges within/across community
        for node, layer in members:
            # Get neighbors in the network
            if hasattr(network, 'core_network'):
                if (node, layer) in network.core_network:
                    for neighbor in network.core_network.neighbors((node, layer)):
                        if neighbor in member_set:
                            intra_edges += 1
                        else:
                            inter_edges += 1

        # Each edge counted twice (once from each endpoint)
        intra_edges = intra_edges // 2

        # Calculate density
        size = len(members)
        max_edges = (size * (size - 1)) // 2 if size > 1 else 0
        density_intra = intra_edges / max_edges if max_edges > 0 else 0.0

        # Determine layer scope
        layers_in_community = {layer for _, layer in members}
        if len(layers_in_community) == 1:
            layer_scope = "single_layer"
        else:
            layer_scope = "multi_layer"

        record = CommunityRecord(
            community_id=comm_id,
            layer_scope=layer_scope,
            members=members,
            size=size,
            intra_edges=intra_edges,
            inter_edges=inter_edges,
            density_intra=density_intra,
            cut_size=inter_edges,
            boundary_edges=inter_edges,
            metadata={"name": name, **metadata}
        )
        records.append(record)

    return records


def filter_communities(
    records: List[CommunityRecord],
    **filters
) -> List[CommunityRecord]:
    """Filter community records based on predicates.

    Args:
        records: List of CommunityRecord objects
        **filters: Filter predicates (e.g., size__gt=10, density_intra__lt=0.5)

    Returns:
        Filtered list of CommunityRecord objects
    """
    result = records[:]

    for key, value in filters.items():
        if "__" in key:
            attr, op = key.rsplit("__", 1)

            if op == "gt":
                result = [r for r in result if getattr(r, attr, 0) > value]
            elif op == "gte":
                result = [r for r in result if getattr(r, attr, 0) >= value]
            elif op == "lt":
                result = [r for r in result if getattr(r, attr, 0) < value]
            elif op == "lte":
                result = [r for r in result if getattr(r, attr, 0) <= value]
            elif op == "eq":
                result = [r for r in result if getattr(r, attr, None) == value]
            elif op == "ne":
                result = [r for r in result if getattr(r, attr, None) != value]
            elif op == "between":
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    low, high = value
                    result = [r for r in result if low <= getattr(r, attr, 0) <= high]
        elif key == "layer":
            # Filter by layer scope
            result = [r for r in result if r.layer_scope == value]
        else:
            # Direct equality
            result = [r for r in result if getattr(r, key, None) == value]

    return result


def compute_community_metric(
    record: CommunityRecord,
    metric: str,
    network: Any = None
) -> Any:
    """Compute a metric for a single community.

    Args:
        record: CommunityRecord object
        metric: Metric name (e.g., "size", "conductance", "hub_nodes_top_k")
        network: Network object (needed for some metrics)

    Returns:
        Computed metric value
    """
    # Simple metrics
    if metric == "size":
        return record.size
    elif metric == "intra_edges":
        return record.intra_edges
    elif metric == "inter_edges":
        return record.inter_edges
    elif metric == "cut_size":
        return record.cut_size
    elif metric == "boundary_edges":
        return record.boundary_edges
    elif metric == "density_intra":
        return record.density_intra
    elif metric == "modularity_contribution":
        return record.modularity_contribution or 0.0

    # Complex metrics requiring network
    elif metric == "conductance":
        # Conductance = cut_size / (2 * intra_edges + cut_size)
        denom = 2 * record.intra_edges + record.cut_size
        return record.cut_size / denom if denom > 0 else 0.0

    elif metric == "normalized_cut":
        # Similar to conductance
        return compute_community_metric(record, "conductance", network)

    elif metric.startswith("hub_nodes_top_"):
        # Extract k from "hub_nodes_top_k"
        try:
            k = int(metric.split("_")[-1])
        except (ValueError, IndexError):
            k = 5

        # Would need network to compute centrality
        # For now, return member nodes (requires network implementation)
        if network is None:
            return []

        # Return top k nodes by degree within community
        member_degrees = []
        for node, layer in record.members:
            if hasattr(network, 'core_network'):
                if (node, layer) in network.core_network:
                    degree = network.core_network.degree((node, layer))
                    member_degrees.append(((node, layer), degree))

        member_degrees.sort(key=lambda x: x[1], reverse=True)
        return [node for node, degree in member_degrees[:k]]

    else:
        # Unknown metric
        return None
