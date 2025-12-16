"""Temporal multilayer network walkthrough.

Shows how to:
1. Build a temporal multilayer network and add time-stamped edges.
2. Slice by time ranges and take snapshots.
3. Iterate over sliding windows.
4. Run streaming PageRank and community-change detection.

Dependencies: py3plex, networkx (installed with py3plex extras).
"""

from __future__ import annotations

from pathlib import Path
import random
import sys
from typing import Dict

import networkx as nx
import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.algorithms.temporal import streaming_community_change, streaming_pagerank
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

DEFAULT_SEED = 42


def create_sample_temporal_network() -> TemporalMultiLayerNetwork:
    """Create a small deterministic temporal multilayer network."""
    print("Creating temporal multilayer network...")

    tnet = TemporalMultiLayerNetwork(directed=True)

    # Add time-stamped edges representing network evolution
    # Time 0-100: Initial network structure
    edges_t1 = [
        ('Alice', 'social', 'Bob', 'social', 50.0, 1.0),
        ('Bob', 'social', 'Charlie', 'social', 50.0, 1.0),
        ('Charlie', 'social', 'Alice', 'social', 50.0, 1.0),
    ]

    # Time 100-200: Network grows
    edges_t2 = [
        ('Alice', 'social', 'David', 'social', 150.0, 1.0),
        ('David', 'social', 'Eve', 'social', 150.0, 1.0),
        ('Eve', 'social', 'Bob', 'social', 150.0, 1.0),
    ]

    # Time 200-300: More connections
    edges_t3 = [
        ('David', 'social', 'Charlie', 'social', 250.0, 1.0),
        ('Eve', 'social', 'Alice', 'social', 250.0, 1.0),
    ]

    # Add all edges
    all_edges = edges_t1 + edges_t2 + edges_t3
    tnet.add_edges(all_edges, input_type="tuple")

    print(f"Created network with {tnet.number_of_edges()} temporal edges")
    print(f"Time range: {tnet.time_range()}")

    return tnet


def demonstrate_time_slicing(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate time-based slicing."""
    print("\n=== Time-Based Slicing ===")

    # Get edges in a specific time range
    print("\nEdges between t=100 and t=200:")
    edges = list(tnet.edges_between(100.0, 200.0))
    for edge in edges:
        print(f"  {edge['source']} -> {edge['target']} at t={edge['t']}")

    # Create a time-sliced subnetwork
    sliced = tnet.slice_time_window(100.0, 200.0)
    print(f"\nSliced network has {sliced.number_of_edges()} edges")


def demonstrate_snapshots(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate snapshot creation."""
    print("\n=== Network Snapshots ===")

    # Cumulative snapshot at t=150
    snapshot_cumulative = tnet.snapshot_at(150.0, mode="up_to")
    print(f"\nCumulative snapshot at t=150:")
    print(f"  Nodes: {snapshot_cumulative.core_network.number_of_nodes()}")
    print(f"  Edges: {snapshot_cumulative.core_network.number_of_edges()}")

    # Exact snapshot at t=150
    snapshot_exact = tnet.snapshot_at(150.0, mode="exact")
    print(f"\nExact snapshot at t=150:")
    print(f"  Edges: {snapshot_exact.core_network.number_of_edges()}")


def demonstrate_sliding_windows(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate sliding window iteration."""
    print("\n=== Sliding Windows ===")

    # Non-overlapping windows
    print("\nNon-overlapping windows (size=100):")
    for t_start, t_end, window_net in tnet.window_iter(window_size=100.0):
        print(f"  Window [{t_start:.0f}, {t_end:.0f}]: {window_net.number_of_edges()} edges")

    # Overlapping windows
    print("\nOverlapping windows (size=100, step=50):")
    for t_start, t_end, window_net in tnet.window_iter(window_size=100.0, step=50.0):
        print(f"  Window [{t_start:.0f}, {t_end:.0f}]: {window_net.number_of_edges()} edges")


def demonstrate_streaming_pagerank(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate streaming PageRank."""
    print("\n=== Streaming PageRank ===")

    print("\nComputing PageRank over time windows:")
    for t_start, t_end, scores in streaming_pagerank(
        tnet,
        window_size=100.0,
        max_iter_per_window=10,
        normalize=True,
    ):
        print(f"\nWindow [{t_start:.0f}, {t_end:.0f}]:")
        # Show top 3 nodes
        top_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for node, score in top_nodes:
            print(f"  {node}: {score:.4f}")


def _detect_components(network: nx.DiGraph) -> Dict[tuple, int]:
    """Group nodes into weakly connected components."""
    graph = network.core_network if hasattr(network, "core_network") else network
    communities: Dict[tuple, int] = {}
    for idx, component in enumerate(nx.weakly_connected_components(graph)):
        for node in component:
            communities[node] = idx
    return communities


def demonstrate_streaming_community(tnet: TemporalMultiLayerNetwork) -> None:
    """Demonstrate streaming community detection."""
    print("\n=== Streaming Community Detection ===")

    print("\nDetecting community changes over time:")
    for t_start, t_end, communities, change_score in streaming_community_change(
        tnet,
        _detect_components,
        window_size=100.0,
    ):
        num_communities = len(set(communities.values()))
        print(f"\nWindow [{t_start:.0f}, {t_end:.0f}]:")
        print(f"  Number of communities: {num_communities}")
        print(f"  Change score: {change_score:.4f}")

        # Show community membership
        if communities:
            comm_members = {}
            for node, comm_id in communities.items():
                comm_members.setdefault(comm_id, []).append(node)

            for comm_id, members in sorted(comm_members.items()):
                # Convert node tuples to strings if needed
                member_strs = [str(m) if isinstance(m, tuple) else m for m in members]
                print(f"  Community {comm_id}: {', '.join(member_strs)}")


def main() -> int:
    """Run all demonstrations."""
    random.seed(DEFAULT_SEED)
    np.random.seed(DEFAULT_SEED)

    print("=" * 60)
    print("Temporal Multilayer Network Example")
    print("=" * 60)

    # Create temporal network
    tnet = create_sample_temporal_network()

    # Demonstrate features
    demonstrate_time_slicing(tnet)
    demonstrate_snapshots(tnet)
    demonstrate_sliding_windows(tnet)
    demonstrate_streaming_pagerank(tnet)
    demonstrate_streaming_community(tnet)

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
