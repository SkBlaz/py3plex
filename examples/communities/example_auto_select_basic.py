#!/usr/bin/env python3
"""
Example: Automatic community detection algorithm selection with mode comparison.

Teaches:
- How to use auto_select_community with different modes (Pareto vs wins)
- Understanding Pareto-optimal multi-objective selection
- Understanding legacy "most wins" pairwise comparison
- Comparing results between the two modes
- Accessing results: partition, leaderboard, and explanations
- Using fast mode for quick exploration

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Auto-selection evaluates multiple algorithms
"""

from __future__ import annotations

import sys
from typing import Dict

try:
    from py3plex.algorithms.community_detection import auto_select_community
    from py3plex.core import multinet, random_generators
    import numpy as np
except ImportError as exc: # pragma: no cover - surfaced to user
    auto_select_community = None
    multinet = None
    random_generators = None
    np = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for individual sections."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def example_mode_comparison() -> None:
    """Example 1: Compare Pareto vs wins mode on the same network."""
    _print_header("Example 1: Pareto mode vs Wins mode comparison")

    # Create a simple network with two clear communities
    network = multinet.multi_layer_network(directed=False)

    # Community 1: nodes 0-4
    nodes_c1 = [{"source": f"N{i}", "type": "layer1"} for i in range(5)]
    network.add_nodes(nodes_c1)

    edges_c1 = [
        {"source": f"N{i}", "target": f"N{j}",
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5) for j in range(i+1, 5)
    ]

    # Community 2: nodes 5-9
    nodes_c2 = [{"source": f"N{i}", "type": "layer1"} for i in range(5, 10)]
    network.add_nodes(nodes_c2)

    edges_c2 = [
        {"source": f"N{i}", "target": f"N{j}",
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5, 10) for j in range(i+1, 10)
    ]

    # Bridge between communities
    bridge = [
        {"source": "N4", "target": "N5",
         "source_type": "layer1", "target_type": "layer1"}
    ]

    network.add_edges(edges_c1 + edges_c2 + bridge)

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run with Pareto mode (default, multi-objective)
    print("\n--- Pareto Mode (Multi-Objective) ---")
    print("Using Pareto dominance for selection...")
    result_pareto = auto_select_community(
        network, mode="pareto", fast=True, seed=DEFAULT_SEED
    )
    
    print("\n" + result_pareto.explain())
    
    if hasattr(result_pareto, 'pareto_front'):
        print(f"\nPareto front size: {len(result_pareto.pareto_front)}")
        print(f"Algorithms: {result_pareto.pareto_front}")

    # Run with wins mode (legacy, backward compatible)
    print("\n\n--- Wins Mode (Legacy, Backward Compatible) ---")
    print("Using pairwise wins for selection...")
    result_wins = auto_select_community(
        network, mode="wins", fast=True, seed=DEFAULT_SEED
    )
    
    print("\n" + result_wins.explain())
    
    if hasattr(result_wins, 'leaderboard'):
        print("\n--- Leaderboard (Top 3) ---")
        print(result_wins.leaderboard.head(3).to_string(index=False))

    # Compare results
    print("\n\n--- Comparison ---")
    print(f"Pareto winner: {result_pareto.algorithm['name']}")
    print(f"Wins winner: {result_wins.algorithm['name']}")
    
    pareto_comms = len(set(result_pareto.partition.values()))
    wins_comms = len(set(result_wins.partition.values()))
    
    print(f"Pareto communities: {pareto_comms}")
    print(f"Wins communities: {wins_comms}")


def example_simple_network() -> None:
    """Example 2: Simple network with Pareto mode (recommended)."""
    _print_header("Example 2: Simple network with Pareto mode")

    # Create a simple network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
    network.add_nodes(nodes)
    
    # Add edges forming two communities
    edges = [
        # Community 1
        {"source": "N0", "target": "N1", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N1", "target": "N2", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N2", "target": "N3", "source_type": "layer1", "target_type": "layer1"},
        # Community 2
        {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N5", "target": "N6", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N6", "target": "N7", "source_type": "layer1", "target_type": "layer1"},
        # Bridge
        {"source": "N3", "target": "N4", "source_type": "layer1", "target_type": "layer1"},
    ]
    network.add_edges(edges)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes, {network.edge_count} edges")
    
    # Run auto-select with Pareto mode
    print("\nRunning auto-select...")
    result = auto_select_community(network, mode="pareto", fast=True, seed=DEFAULT_SEED)
    
    # Show results
    print("\n" + result.explain())

    # Show partition summary
    print("\n--- Partition Summary ---")
    communities: Dict[int, int] = {}
    for node_layer, comm_id in result.partition.items():
        communities[comm_id] = communities.get(comm_id, 0) + 1

    print(f"Number of communities found: {len(communities)}")
    for comm_id, size in sorted(communities.items()):
        print(f"  Community {comm_id}: {size} nodes")


def example_multilayer_network() -> None:
    """Example 2: Auto-select on a multilayer network."""
    _print_header("Example 2: Multilayer network")

    # Create a simple 2-layer network
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: Social network
    nodes_social = [{"source": f"Person{i}", "type": "social"} for i in range(6)]
    network.add_nodes(nodes_social)

    edges_social = [
        {"source": "Person0", "target": "Person1", "source_type": "social", "target_type": "social"},
        {"source": "Person1", "target": "Person2", "source_type": "social", "target_type": "social"},
        {"source": "Person3", "target": "Person4", "source_type": "social", "target_type": "social"},
        {"source": "Person4", "target": "Person5", "source_type": "social", "target_type": "social"},
    ]
    network.add_edges(edges_social)

    # Layer 2: Work network
    nodes_work = [{"source": f"Person{i}", "type": "work"} for i in range(6)]
    network.add_nodes(nodes_work)

    edges_work = [
        {"source": "Person0", "target": "Person3", "source_type": "work", "target_type": "work"},
        {"source": "Person1", "target": "Person4", "source_type": "work", "target_type": "work"},
        {"source": "Person2", "target": "Person5", "source_type": "work", "target_type": "work"},
    ]
    network.add_edges(edges_work)

    print(f"Network: {len(network.get_layers())} layers, "
          f"{len(list(network.get_nodes()))} node-layer pairs")

    # Run auto-select
    print("\nRunning auto-select on multilayer network...")
    result = auto_select_community(network, fast=True, max_candidates=2, seed=DEFAULT_SEED)

    # Show results
    print("\n" + result.explain())

    print("\n--- Community assignments by layer ---")
    by_layer: Dict[str, Dict] = {}
    for (node, layer), comm_id in result.partition.items():
        if layer not in by_layer:
            by_layer[layer] = {}
        by_layer[layer][node] = comm_id

    for layer, assignments in sorted(by_layer.items()):
        print(f"\nLayer: {layer}")
        for node, comm_id in sorted(assignments.items())[:5]:  # Show first 5
            print(f"  {node}: Community {comm_id}")
        if len(assignments) > 5:
            print(f"  ... and {len(assignments) - 5} more nodes")


def example_random_network() -> None:
    """Example 3: Auto-select on a random network."""
    _print_header("Example 3: Random Erdős-Rényi network")

    # Create a random network
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=30,
        l=2,
        p=0.2,
        directed=False,
    )

    print(f"Network: {len(list(network.get_nodes()))} node-layer pairs, "
          f"{network.edge_count} edges")

    # Run auto-select with more candidates
    print("\nRunning auto-select with max_candidates=5...")
    result = auto_select_community(network, fast=True, max_candidates=5, seed=DEFAULT_SEED)

    # Show results
    print("\n" + result.explain())

    # Show full leaderboard
    print("\n--- Full Leaderboard ---")
    print(result.leaderboard.to_string(index=False))

    # Show provenance information
    print("\n--- Selection Provenance ---")
    print(f"Algorithms detected: {len(result.provenance['algorithms_detected'])}")
    
    # Handle different provenance structures between modes
    selection_config = result.provenance.get('selection_config', {})
    if 'n_candidates_evaluated' in selection_config:
        print(f"Candidates evaluated: {selection_config['n_candidates_evaluated']}")
    if 'n_metrics_used' in selection_config:
        print(f"Metrics used: {selection_config['n_metrics_used']}")

    # Show wins by bucket (only available in wins mode)
    if 'wins_by_bucket' in result.provenance:
        print("\n--- Winner's wins by metric bucket ---")
        for bucket, wins in result.provenance['wins_by_bucket'].items():
            if wins > 0:
                print(f"  {bucket}: {wins}")


def main() -> int:
    """Run all examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex is properly installed.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("Auto-Select Community Detection Examples")
    print("=" * 70)
    print("\nThis demonstrates automatic selection with Pareto-optimal")
    print("multi-objective evaluation (default) vs legacy wins mode.")

    try:
        example_mode_comparison()
        example_simple_network()
        example_multilayer_network()
        example_random_network()

        print("\n" + "=" * 70)
        print(" All examples completed successfully!")
        print("=" * 70)
        print("\nKey takeaways:")
        print("1. Pareto mode (default) uses multi-objective selection")
        print("2. Wins mode (legacy) uses pairwise comparison")
        print("3. Pareto mode may produce consensus from multiple algorithms")
        print("4. Both modes are deterministic with the same seed")

    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
