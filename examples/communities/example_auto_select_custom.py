#!/usr/bin/env python3
"""
Example: Auto-select with custom metrics and candidates.

Teaches:
- How to define custom evaluation metrics
- How to specify custom algorithm candidates
- Understanding MetricSpec and CandidateSpec
- Tailoring auto-select to specific use cases

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Auto-selection with custom configuration
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

try:
    from py3plex.algorithms.community_detection import auto_select_community
    from py3plex.core import multinet, random_generators
    from py3plex.selection.metric_registry import MetricSpec, get_metric_registry
    from py3plex.selection.community_registry import CandidateSpec
    import numpy as np
    import networkx as nx
except ImportError as exc:  # pragma: no cover - surfaced to user
    auto_select_community = None
    multinet = None
    random_generators = None
    MetricSpec = None
    CandidateSpec = None
    get_metric_registry = None
    np = None
    nx = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for individual sections."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def custom_metric_coverage(
    partition: Dict,
    network: Any,
    contestant_metadata: Optional[Dict] = None
) -> float:
    """Custom metric: fraction of nodes assigned to communities.
    
    Args:
        partition: Community assignments {(node, layer): comm_id}
        network: Network object
        contestant_metadata: Optional metadata from contestant
    
    Returns:
        Coverage ratio (0.0 to 1.0)
    """
    total_nodes = len(list(network.get_nodes()))
    assigned_nodes = len(partition)
    
    if total_nodes == 0:
        return 0.0
    
    return assigned_nodes / total_nodes


def custom_metric_balance(
    partition: Dict,
    network: Any,
    contestant_metadata: Optional[Dict] = None
) -> float:
    """Custom metric: balance of community sizes (Gini coefficient).
    
    Lower values indicate more balanced communities.
    
    Args:
        partition: Community assignments
        network: Network object
        contestant_metadata: Optional metadata
    
    Returns:
        Gini coefficient (0.0 = perfect balance, 1.0 = maximum imbalance)
    """
    if not partition:
        return 1.0
    
    # Count community sizes
    sizes: Dict[int, int] = {}
    for comm_id in partition.values():
        sizes[comm_id] = sizes.get(comm_id, 0) + 1
    
    size_list = sorted(sizes.values())
    n = len(size_list)
    
    if n == 0:
        return 1.0
    
    # Gini coefficient
    cumsum = 0
    for i, size in enumerate(size_list):
        cumsum += (2 * (i + 1) - n - 1) * size
    
    total = sum(size_list)
    if total == 0:
        return 1.0
    
    gini = cumsum / (n * total)
    return abs(gini)


def custom_metric_avg_community_size(
    partition: Dict,
    network: Any,
    contestant_metadata: Optional[Dict] = None
) -> float:
    """Custom metric: average community size.
    
    Args:
        partition: Community assignments
        network: Network object
        contestant_metadata: Optional metadata
    
    Returns:
        Average community size
    """
    if not partition:
        return 0.0
    
    sizes: Dict[int, int] = {}
    for comm_id in partition.values():
        sizes[comm_id] = sizes.get(comm_id, 0) + 1
    
    if not sizes:
        return 0.0
    
    return sum(sizes.values()) / len(sizes)


def example_custom_metrics() -> None:
    """Example 1: Using custom metrics for evaluation."""
    _print_header("Example 1: Auto-select with custom metrics")
    
    # Create a network
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(20)]
    network.add_nodes(nodes)
    
    # Create communities with different sizes
    # Community 1: 10 nodes (large)
    edges_c1 = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(10) for j in range(i+1, 10)
        if (i + j) % 2 == 0
    ]
    
    # Community 2: 5 nodes (medium)
    edges_c2 = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(10, 15) for j in range(i+1, 15)
    ]
    
    # Community 3: 5 nodes (medium)
    edges_c3 = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(15, 20) for j in range(i+1, 20)
    ]
    
    network.add_edges(edges_c1 + edges_c2 + edges_c3)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes")
    
    # Define custom metrics
    custom_metrics = [
        MetricSpec(
            name="coverage",
            callable=custom_metric_coverage,
            direction="max",  # Higher coverage is better
            bucket="sanity",  # Sanity check bucket
            requires_uq=False,
        ),
        MetricSpec(
            name="balance",
            callable=custom_metric_balance,
            direction="min",  # Lower Gini = more balanced
            bucket="structure",  # Structure bucket
            requires_uq=False,
        ),
        MetricSpec(
            name="avg_size",
            callable=custom_metric_avg_community_size,
            direction="max",  # Prefer larger communities (configurable)
            bucket="structure",
            requires_uq=False,
        ),
    ]
    
    print(f"\nUsing {len(custom_metrics)} custom metrics:")
    for metric in custom_metrics:
        print(f"  - {metric.name} ({metric.bucket}, {metric.direction})")
    
    # Run auto-select with custom metrics
    print("\nRunning auto-select with custom metrics...")
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=2,
        custom_metrics=custom_metrics,
        seed=DEFAULT_SEED
    )
    
    # Show results
    print("\n" + result.explain())
    
    print("\n--- Leaderboard with Custom Metrics ---")
    print(result.leaderboard.to_string(index=False))
    
    # Show custom metric values for winner
    print("\n--- Winner's Custom Metric Values ---")
    winner = result.chosen
    for metric in custom_metrics:
        if metric.name in winner.metrics:
            print(f"  {metric.name}: {winner.metrics[metric.name]:.4f}")


def example_mixed_metrics() -> None:
    """Example 2: Mixing custom metrics with default metrics."""
    _print_header("Example 2: Combining custom and default metrics")
    
    # Create network
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=25,
        l=2,
        p=0.15,
        directed=False,
    )
    
    print(f"Network: {len(list(network.get_nodes()))} node-layer pairs")
    
    # Get default metrics and add custom ones
    registry = get_metric_registry()
    default_metrics = registry.get_default_metrics(uq_enabled=False)
    
    # Add custom metric
    custom_balance = MetricSpec(
        name="custom_balance",
        callable=custom_metric_balance,
        direction="min",
        bucket="structure",
        requires_uq=False,
    )
    
    mixed_metrics = default_metrics + [custom_balance]
    
    print(f"\nUsing {len(mixed_metrics)} metrics total:")
    print(f"  - {len(default_metrics)} default metrics")
    print(f"  - 1 custom metric (custom_balance)")
    
    # Run auto-select
    print("\nRunning auto-select...")
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=2,
        custom_metrics=mixed_metrics,
        seed=DEFAULT_SEED
    )
    
    print("\n" + result.explain())
    
    # Show metrics by bucket
    print("\n--- Metrics by Bucket ---")
    for bucket, metrics in result.report['metrics_by_bucket'].items():
        if metrics:
            print(f"\n{bucket}:")
            for metric_name in metrics[:3]:  # Show first 3
                print(f"  - {metric_name}")


def example_custom_candidates() -> None:
    """Example 3: Specifying custom algorithm candidates."""
    _print_header("Example 3: Custom algorithm candidates")
    
    # Create simple network
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
    network.add_nodes(nodes)
    
    edges = [
        {"source": f"N{i}", "target": f"N{(i+1) % 15}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(15)
    ]
    network.add_edges(edges)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes (ring structure)")
    
    # Define custom candidates with specific parameters
    # Note: This requires knowledge of available algorithms
    print("\nNote: Custom candidates require algorithm-specific knowledge")
    print("This example shows the structure, but may need adjustment")
    print("based on available algorithms in your installation.")
    
    # For demonstration, we'll use the default auto-select
    # which automatically builds candidates
    print("\nRunning auto-select with default candidate building...")
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=3,
        seed=DEFAULT_SEED
    )
    
    print("\n" + result.explain())
    
    print("\n--- Candidate Information ---")
    print(f"Algorithms detected: {len(result.provenance['algorithms_detected'])}")
    print("Detected algorithms:")
    for algo in result.provenance['algorithms_detected'][:5]:
        print(f"  - {algo}")


def main() -> int:
    """Run all custom metric examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex is properly installed.", file=sys.stderr)
        return 1
    
    print("=" * 70)
    print("Auto-Select with Custom Metrics and Candidates")
    print("=" * 70)
    print("\nCustom metrics allow you to tailor algorithm selection")
    print("to your specific community detection requirements.")
    
    try:
        example_custom_metrics()
        example_mixed_metrics()
        example_custom_candidates()
        
        print("\n" + "=" * 70)
        print("✓ All custom metric examples completed!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("- MetricSpec defines custom evaluation metrics")
        print("- Metrics have direction (max/min) and bucket")
        print("- Can mix custom and default metrics")
        print("- Buckets prevent single-metric domination")
        print("- CandidateSpec allows algorithm customization")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
