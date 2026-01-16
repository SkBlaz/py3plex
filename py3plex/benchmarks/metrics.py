"""Metric registry for community detection benchmarking.

This module provides a registry of metrics for evaluating community detection
algorithms, including modularity, conductance, coverage, and stability.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import warnings

import networkx as nx
import numpy as np


@dataclass
class CommunityMetric:
    """Community detection metric specification.

    Attributes:
        name: Metric name (e.g., "modularity")
        func: Callable that computes the metric
        description: Human-readable description
        requires_network: Whether the metric needs the network
        requires_uq: Whether the metric requires UQ results
    """

    name: str
    func: Callable
    description: str
    requires_network: bool = True
    requires_uq: bool = False


# Global metric registry
metric_registry: Dict[str, CommunityMetric] = {}


def register_metric(
    name: str,
    func: Callable,
    description: str = "",
    requires_network: bool = True,
    requires_uq: bool = False,
) -> None:
    """Register a community detection metric.

    Args:
        name: Metric name
        func: Callable with signature fn(network, partition, layers, **ctx) -> float
        description: Human-readable description
        requires_network: Whether metric needs the network
        requires_uq: Whether metric requires UQ results
    """
    metric_registry[name] = CommunityMetric(
        name=name,
        func=func,
        description=description,
        requires_network=requires_network,
        requires_uq=requires_uq,
    )


def get_metric(name: str) -> Optional[CommunityMetric]:
    """Get a metric from the registry.

    Args:
        name: Metric name

    Returns:
        CommunityMetric if found, None otherwise
    """
    return metric_registry.get(name)


def compute_metric(
    name: str,
    network: Any,
    partition: Dict[Any, int],
    layers: Optional[List[str]] = None,
    **ctx
) -> float:
    """Compute a metric for a partition.

    Args:
        name: Metric name
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Additional context (e.g., uq_results)

    Returns:
        Metric value

    Raises:
        ValueError: If metric not found
    """
    metric = get_metric(name)
    if metric is None:
        raise ValueError(f"Unknown metric: {name}")

    try:
        return metric.func(network, partition, layers, **ctx)
    except Exception as e:
        warnings.warn(f"Failed to compute {name}: {e}")
        return float("nan")


# ============================================================================
# Built-in Metrics
# ============================================================================


def _compute_modularity(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Compute multilayer modularity.

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Unused

    Returns:
        Modularity score
    """
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        compute_multilayer_modularity,
    )

    try:
        # Try multilayer-aware modularity first
        if hasattr(network, "get_layers") and layers:
            return compute_multilayer_modularity(network, partition, layers)
    except Exception:
        pass

    # Fallback: convert to NetworkX and compute single-layer modularity
    try:
        # Get flattened graph
        if hasattr(network, "get_layers"):
            # Aggregate across layers
            G = nx.Graph()
            for layer in layers or network.get_layers():
                layer_g = network.get_layer_graph(layer)
                G.add_edges_from(layer_g.edges())
        else:
            G = network

        # Convert partition to communities list
        communities = {}
        for node, comm in partition.items():
            communities.setdefault(comm, []).append(node)

        return nx.algorithms.community.modularity(G, communities.values())
    except Exception as e:
        warnings.warn(f"Modularity computation failed: {e}")
        return 0.0


def _compute_conductance(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Compute average conductance across communities.

    Lower conductance indicates better community separation.

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Unused

    Returns:
        Average conductance
    """
    try:
        # Get flattened graph
        if hasattr(network, "get_layers"):
            G = nx.Graph()
            for layer in layers or network.get_layers():
                layer_g = network.get_layer_graph(layer)
                G.add_edges_from(layer_g.edges())
        else:
            G = network

        # Group nodes by community
        communities = {}
        for node, comm in partition.items():
            communities.setdefault(comm, set()).add(node)

        # Compute conductance for each community
        conductances = []
        for nodes in communities.values():
            if len(nodes) < 2:
                continue
            cond = nx.algorithms.cuts.conductance(G, nodes)
            conductances.append(cond)

        return np.mean(conductances) if conductances else 0.0
    except Exception as e:
        warnings.warn(f"Conductance computation failed: {e}")
        return float("nan")


def _compute_coverage(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Compute coverage (fraction of nodes in non-singleton communities).

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Unused

    Returns:
        Coverage fraction
    """
    try:
        # Count community sizes
        comm_sizes = {}
        for node, comm in partition.items():
            comm_sizes[comm] = comm_sizes.get(comm, 0) + 1

        # Count nodes in non-singleton communities
        non_singleton = sum(
            1 for node, comm in partition.items() if comm_sizes[comm] > 1
        )

        total = len(partition)
        return non_singleton / total if total > 0 else 0.0
    except Exception as e:
        warnings.warn(f"Coverage computation failed: {e}")
        return 0.0


def _compute_n_communities(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Count number of communities.

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Unused

    Returns:
        Number of communities
    """
    return float(len(set(partition.values())))


def _compute_stability(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Compute partition stability from UQ results.

    Args:
        network: Multilayer network
        partition: Node -> community mapping (reference)
        layers: Optional layer list
        **ctx: Must contain 'uq_partitions' key

    Returns:
        Stability score (mean NMI across UQ replicates)
    """
    from sklearn.metrics import normalized_mutual_info_score

    uq_partitions = ctx.get("uq_partitions", [])
    if not uq_partitions:
        warnings.warn("Stability metric requires UQ partitions")
        return float("nan")

    # Compute NMI between reference and each UQ replicate
    nmis = []
    ref_labels = [partition.get(node, -1) for node in sorted(partition.keys())]

    for uq_partition in uq_partitions:
        uq_labels = [uq_partition.get(node, -1) for node in sorted(partition.keys())]
        nmi = normalized_mutual_info_score(ref_labels, uq_labels)
        nmis.append(nmi)

    return float(np.mean(nmis))


def _compute_runtime_ms(
    network: Any, partition: Dict[Any, int], layers: Optional[List[str]], **ctx
) -> float:
    """Extract runtime from context.

    Args:
        network: Multilayer network
        partition: Node -> community mapping
        layers: Optional layer list
        **ctx: Must contain 'runtime_ms' key

    Returns:
        Runtime in milliseconds
    """
    return float(ctx.get("runtime_ms", 0.0))


# Register built-in metrics
register_metric(
    "modularity",
    _compute_modularity,
    "Multilayer modularity (quality of community structure)",
    requires_network=True,
)

register_metric(
    "conductance",
    _compute_conductance,
    "Average conductance (lower is better separation)",
    requires_network=True,
)

register_metric(
    "coverage",
    _compute_coverage,
    "Fraction of nodes in non-singleton communities",
    requires_network=False,
)

register_metric(
    "n_communities",
    _compute_n_communities,
    "Number of detected communities",
    requires_network=False,
)

register_metric(
    "stability",
    _compute_stability,
    "Partition stability under uncertainty (requires UQ)",
    requires_network=False,
    requires_uq=True,
)

register_metric(
    "runtime_ms",
    _compute_runtime_ms,
    "Algorithm runtime in milliseconds",
    requires_network=False,
)
