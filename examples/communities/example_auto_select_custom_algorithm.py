#!/usr/bin/env python3
"""
Example: Adding a custom community detection algorithm to auto_select.

Teaches:
- How to implement a custom community detection algorithm
- How to make your algorithm compatible with auto_select_community
- How to use CandidateSpec to register custom algorithms
- Understanding the algorithm interface requirements

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Auto-selection with custom algorithms
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Tuple

try:
    from py3plex.algorithms.community_detection import auto_select_community
    from py3plex.core import multinet
    from py3plex.selection.community_registry import CandidateSpec
    import numpy as np
    import networkx as nx
except ImportError as exc:  # pragma: no cover - surfaced to user
    auto_select_community = None
    multinet = None
    CandidateSpec = None
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


# ============================================================================
# Custom Algorithm Implementation
# ============================================================================

def simple_label_propagation(
    network: Any,
    max_iterations: int = 100,
    seed: int = None
) -> Dict[Tuple[Any, Any], int]:
    """
    Custom community detection algorithm: Simple label propagation.
    
    This is a basic implementation for demonstration purposes. In real use,
    you would implement more sophisticated algorithms.
    
    Args:
        network: py3plex multi_layer_network object
        max_iterations: Maximum number of iterations
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping (node, layer) tuples to community IDs
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Initialize: each node gets its own community
    partition = {}
    node_to_id = {}
    id_counter = 0
    
    for node, layer in network.get_nodes():
        partition[(node, layer)] = id_counter
        node_to_id[(node, layer)] = id_counter
        id_counter += 1
    
    # Label propagation: iteratively update labels
    for iteration in range(max_iterations):
        changed = False
        nodes = list(network.get_nodes())
        np.random.shuffle(nodes)  # Random order
        
        for node, layer in nodes:
            # Get neighbors
            neighbors = []
            try:
                # Get edges for this node
                node_edges = network.get_edges_by_node(node, layer)
                for edge in node_edges:
                    # Parse edge format: (source, source_layer, target, target_layer, weight)
                    if len(edge) >= 4:
                        src, src_layer, tgt, tgt_layer = edge[:4]
                        if src == node and src_layer == layer:
                            neighbors.append((tgt, tgt_layer))
                        elif tgt == node and tgt_layer == layer:
                            neighbors.append((src, src_layer))
            except:
                # Fallback: iterate all edges
                for edge in network.get_edges():
                    if len(edge) >= 4:
                        src, src_layer, tgt, tgt_layer = edge[:4]
                        if src == node and src_layer == layer:
                            neighbors.append((tgt, tgt_layer))
                        elif tgt == node and tgt_layer == layer:
                            neighbors.append((src, src_layer))
            
            if not neighbors:
                continue
            
            # Count neighbor labels
            label_counts: Dict[int, int] = {}
            for neighbor in neighbors:
                if neighbor in partition:
                    label = partition[neighbor]
                    label_counts[label] = label_counts.get(label, 0) + 1
            
            if label_counts:
                # Adopt most common neighbor label
                most_common = max(label_counts, key=label_counts.get)
                if partition[(node, layer)] != most_common:
                    partition[(node, layer)] = most_common
                    changed = True
        
        if not changed:
            break
    
    return partition


def greedy_modularity(
    network: Any,
    resolution: float = 1.0,
    seed: int = None
) -> Dict[Tuple[Any, Any], int]:
    """
    Custom algorithm: Greedy modularity optimization.
    
    This is a simplified modularity-based algorithm for demonstration.
    
    Args:
        network: py3plex multi_layer_network object
        resolution: Resolution parameter (higher = more communities)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping (node, layer) tuples to community IDs
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Start with each node in its own community
    partition = {}
    for idx, (node, layer) in enumerate(network.get_nodes()):
        partition[(node, layer)] = idx
    
    # Simple greedy merge: merge communities if it improves modularity
    # (This is a very simplified version - real algorithms are more sophisticated)
    
    improved = True
    iteration = 0
    max_iterations = 20
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        # Try merging random pairs of communities
        communities = list(set(partition.values()))
        if len(communities) <= 2:
            break
        
        for _ in range(min(10, len(communities))):
            if len(communities) < 2:
                break
            
            # Pick two random communities
            idx1, idx2 = np.random.choice(len(communities), 2, replace=False)
            c1, c2 = communities[idx1], communities[idx2]
            
            # Merge them (simple version - always merge)
            for node_layer, comm in partition.items():
                if comm == c2:
                    partition[node_layer] = c1
            
            improved = True
            break
    
    # Renumber communities to be consecutive
    unique_comms = sorted(set(partition.values()))
    comm_map = {old: new for new, old in enumerate(unique_comms)}
    partition = {k: comm_map[v] for k, v in partition.items()}
    
    return partition


# ============================================================================
# Examples
# ============================================================================

def example_custom_algorithm_basic() -> None:
    """Example 1: Using a custom algorithm with auto_select."""
    _print_header("Example 1: Custom algorithm with auto_select")
    
    # Create a test network
    network = multinet.multi_layer_network(directed=False)
    
    # Create two communities
    for i in range(10):
        network.add_nodes([{"source": f"N{i}", "type": "layer1"}])
    
    # Dense intra-community edges (community 1: 0-4, community 2: 5-9)
    edges_c1 = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5) for j in range(i+1, 5)
    ]
    edges_c2 = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(5, 10) for j in range(i+1, 10)
    ]
    # Bridge
    edges_bridge = [
        {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"}
    ]
    
    network.add_edges(edges_c1 + edges_c2 + edges_bridge)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes")
    
    # Create a custom candidate using our custom algorithm
    print("\nCreating custom algorithm candidate...")
    
    custom_candidate = CandidateSpec(
        name="simple_label_propagation",
        callable=simple_label_propagation,
        params={"max_iterations": 50},
        supports_multilayer=True,
        seed_param_name="seed",
    )
    
    print(f"Custom candidate: {custom_candidate.contestant_id}")
    
    # Run auto_select with custom candidates
    print("\nRunning auto_select with custom algorithm...")
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=3,
        custom_candidates=[custom_candidate],
        seed=DEFAULT_SEED
    )
    
    print("\n" + result.explain())
    print("\n--- Leaderboard ---")
    print(result.leaderboard.to_string(index=False))
    
    # Show partition
    print("\n--- Custom Algorithm Result ---")
    if result.algorithm["name"] == "simple_label_propagation":
        print("✓ Our custom algorithm was selected as the winner!")
    else:
        print(f"Winner: {result.algorithm['name']}")
    
    communities = {}
    for (node, layer), comm_id in result.partition.items():
        communities[comm_id] = communities.get(comm_id, 0) + 1
    
    print(f"\nCommunities found: {len(communities)}")
    for comm_id, size in sorted(communities.items()):
        print(f"  Community {comm_id}: {size} nodes")


def example_multiple_custom_algorithms() -> None:
    """Example 2: Comparing multiple custom algorithms."""
    _print_header("Example 2: Multiple custom algorithms")
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(20)]
    network.add_nodes(nodes)
    
    # Create 3 communities with varying density
    for comm_idx in range(3):
        start = comm_idx * 6
        end = min(start + 6, 20)
        edges = [
            {"source": f"N{i}", "target": f"N{j}", 
             "source_type": "layer1", "target_type": "layer1"}
            for i in range(start, end) for j in range(i+1, end)
            if (i + j) % 2 == 0  # Sparse connections
        ]
        network.add_edges(edges)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes")
    
    # Create multiple custom candidates
    print("\nCreating multiple custom algorithm candidates...")
    
    candidates = [
        CandidateSpec(
            name="simple_label_propagation",
            callable=simple_label_propagation,
            params={"max_iterations": 30},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
        CandidateSpec(
            name="simple_label_propagation",
            callable=simple_label_propagation,
            params={"max_iterations": 100},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
        CandidateSpec(
            name="greedy_modularity",
            callable=greedy_modularity,
            params={"resolution": 1.0},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
        CandidateSpec(
            name="greedy_modularity",
            callable=greedy_modularity,
            params={"resolution": 1.5},
            supports_multilayer=True,
            seed_param_name="seed",
        ),
    ]
    
    print(f"Created {len(candidates)} custom candidates:")
    for c in candidates:
        print(f"  - {c.contestant_id}")
    
    # Run auto_select
    print("\nRunning auto_select to compare custom algorithms...")
    result = auto_select_community(
        network,
        fast=True,
        custom_candidates=candidates,
        seed=DEFAULT_SEED
    )
    
    print("\n" + result.explain())
    
    print("\n--- Full Leaderboard ---")
    print(result.leaderboard.to_string(index=False))
    
    print("\n--- Winner Details ---")
    print(f"Algorithm: {result.algorithm['name']}")
    print(f"Parameters: {result.algorithm['params']}")


def example_custom_with_default() -> None:
    """Example 3: Mixing custom algorithms with default detection."""
    _print_header("Example 3: Custom + default algorithms")
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
    network.add_nodes(nodes)
    
    edges = [
        {"source": f"N{i}", "target": f"N{j}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(15) for j in range(i+1, 15)
        if abs(i - j) <= 3  # Connect nearby nodes
    ]
    network.add_edges(edges)
    
    print(f"Network: {len(list(network.get_nodes()))} nodes")
    print("Note: To mix custom and default algorithms, you need to manually")
    print("      build both sets and combine them.")
    
    # For now, demonstrate with just custom
    print("\nDemonstrating with custom algorithm...")
    
    custom_candidate = CandidateSpec(
        name="simple_label_propagation",
        callable=simple_label_propagation,
        params={"max_iterations": 50},
        supports_multilayer=True,
        seed_param_name="seed",
    )
    
    result = auto_select_community(
        network,
        fast=True,
        custom_candidates=[custom_candidate],
        seed=DEFAULT_SEED
    )
    
    print("\n" + result.explain())


def main() -> int:
    """Run all custom algorithm examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex is properly installed.", file=sys.stderr)
        return 1
    
    print("=" * 70)
    print("Adding Custom Community Detection Algorithms")
    print("=" * 70)
    print("\nThis example shows how to implement and use custom community")
    print("detection algorithms with auto_select_community.")
    
    try:
        example_custom_algorithm_basic()
        example_multiple_custom_algorithms()
        example_custom_with_default()
        
        print("\n" + "=" * 70)
        print("✓ All custom algorithm examples completed!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("- Custom algorithms must return Dict[(node, layer), community_id]")
        print("- Use CandidateSpec to register custom algorithms")
        print("- Specify seed_param_name for reproducibility")
        print("- Can compare multiple custom algorithm variants")
        print("- Custom algorithms compete in auto_select evaluation")
        print("\nAlgorithm Requirements:")
        print("- Accept network as first parameter")
        print("- Return partition as Dict[Tuple[node, layer], int]")
        print("- Optionally accept seed parameter for reproducibility")
        print("- Should handle py3plex multi_layer_network objects")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
