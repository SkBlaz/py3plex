#!/usr/bin/env python3
"""
Example: Automatic community detection algorithm selection.

Teaches:
- How to use auto_select_community for automatic algorithm selection
- Understanding the multi-metric evaluation and "most wins" decision engine
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
except ImportError as exc:  # pragma: no cover - surfaced to user
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


def example_simple_network() -> None:
    """Example 1: Auto-select on a simple karate-club-like network."""
    _print_header("Example 1: Simple network with clear community structure")
    
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
          f"{network.number_of_edges()} edges")
    
    # Run auto-select in fast mode
    print("\nRunning auto-select (fast mode)...")
    result = auto_select_community(network, fast=True, max_candidates=3, seed=DEFAULT_SEED)
    
    # Show explanation
    print("\n" + result.explain())
    
    # Show leaderboard
    print("\n--- Leaderboard (Top 3) ---")
    print(result.leaderboard.head(3).to_string(index=False))
    
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
          f"{network.number_of_edges()} edges")
    
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
    print(f"Candidates evaluated: {result.provenance['selection_config']['n_candidates_evaluated']}")
    print(f"Metrics used: {result.provenance['selection_config']['n_metrics_used']}")
    
    # Show wins by bucket
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
    print("\nThis demonstrates automatic selection of the best community")
    print("detection algorithm using multi-metric evaluation.")
    
    try:
        example_simple_network()
        example_multilayer_network()
        example_random_network()
        
        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
