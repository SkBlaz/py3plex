"""
Random Walk Examples for Py3plex

This example demonstrates the comprehensive random walk capabilities:
1. Basic random walks with weighted edges
2. Node2Vec biased random walks with p/q parameters
3. Multiple walk generation
4. Multilayer network walks
5. Statistical validation of walk properties
"""

import numpy as np
from collections import Counter

from py3plex.core import multinet
from py3plex.algorithms.general.walkers import (
    basic_random_walk,
    node2vec_walk,
    generate_walks,
    layer_specific_random_walk,
)
from py3plex.utils import get_dataset_path


def example_basic_random_walk():
    """Demonstrate basic random walk functionality."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Random Walk")
    print("=" * 70)

    # Load py3plex example network
    network = multinet.multi_layer_network().load_network(
        get_dataset_path("test.edgelist"),
        directed=False,
        input_type="edgelist"
    )
    G = network.core_network
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Get a starting node from the loaded network
    start_node = list(G.nodes())[0]

    # Perform a random walk
    walk = basic_random_walk(G, start_node=start_node, walk_length=10, seed=42)
    print(f"\nRandom walk from node {start_node}:")
    print(f"  Path: {' -> '.join(str(n) for n in walk[:5])}...{' -> '.join(str(n) for n in walk[-3:])}")
    print(f"  Length: {len(walk)} nodes")

    # Verify reproducibility
    walk2 = basic_random_walk(G, start_node=start_node, walk_length=10, seed=42)
    print("\nReproducibility check:")
    print(f"  Walk 1 == Walk 2: {walk == walk2}")


def example_weighted_random_walk():
    """Demonstrate weighted edge handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Weighted Random Walk")
    print("=" * 70)

    # Load py3plex network and add weights
    network = multinet.multi_layer_network().load_network(
        get_dataset_path("test.edgelist"),
        directed=False,
        input_type="edgelist"
    )
    G = network.core_network

    # Add weights to a subset of edges for demonstration
    # Get first node with at least 2 neighbors
    start_node = None
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        if len(neighbors) >= 2:
            start_node = node
            neighbor1, neighbor2 = neighbors[0], neighbors[1]
            break

    if start_node is None:
        print("Could not find suitable node for weighted walk demo")
        return

    # Set weights
    G[start_node][neighbor1]['weight'] = 10.0
    G[start_node][neighbor2]['weight'] = 1.0

    print(f"Testing weighted walks from node {start_node}:")
    print(f"  Edge to {neighbor1}: weight=10.0 (high)")
    print(f"  Edge to {neighbor2}: weight=1.0 (low)")

    # Count visits to neighbors
    visits_weighted = Counter()
    visits_unweighted = Counter()

    num_trials = 1000
    for i in range(num_trials):
        # Weighted walk
        walk_w = basic_random_walk(G, start_node, 1, weighted=True, seed=i)
        if len(walk_w) > 1:
            visits_weighted[walk_w[1]] += 1

        # Unweighted walk
        walk_u = basic_random_walk(G, start_node, 1, weighted=False, seed=i)
        if len(walk_u) > 1:
            visits_unweighted[walk_u[1]] += 1

    print(f"\nVisit frequency over {num_trials} walks from node {start_node}:")
    print(f"  Weighted:   {neighbor1}: {visits_weighted[neighbor1]}, {neighbor2}: {visits_weighted[neighbor2]}")
    print(f"  Unweighted: {neighbor1}: {visits_unweighted[neighbor1]}, {neighbor2}: {visits_unweighted[neighbor2]}")
    if visits_weighted[neighbor2] > 0:
        ratio = visits_weighted[neighbor1] / visits_weighted[neighbor2]
        print(f"  Weight ratio (10:1) vs visit ratio: {ratio:.1f}:1")


def example_node2vec_biased_walk():
    """Demonstrate Node2Vec biased random walks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Node2Vec Biased Random Walk")
    print("=" * 70)

    # Create triangle graph for demonstrating bias
    import networkx as nx
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    print("Triangle graph: 0 -- 1 -- 2 -- 0")

    # Test different p/q parameters
    configs = [
        (1.0, 1.0, "Balanced (p=1, q=1)"),
        (0.1, 1.0, "Low p (return bias)"),
        (10.0, 1.0, "High p (forward bias)"),
        (1.0, 0.1, "Low q (exploration bias)"),
        (1.0, 10.0, "High q (local bias)"),
    ]

    num_trials = 1000
    for p, q, desc in configs:
        backtracks = 0

        for i in range(num_trials):
            walk = node2vec_walk(G, 0, 10, p=p, q=q, seed=i)
            # Count backtracking (returning to node 2 steps back)
            for j in range(2, len(walk)):
                if walk[j] == walk[j-2]:
                    backtracks += 1

        backtrack_rate = backtracks / (num_trials * 9)  # 9 possible backtracks per walk
        print(f"\n{desc}:")
        print(f"  Backtrack rate: {backtrack_rate:.3f}")


def example_generate_multiple_walks():
    """Demonstrate multiple walk generation."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Generate Multiple Walks")
    print("=" * 70)

    # Load py3plex network
    network = multinet.multi_layer_network().load_network(
        get_dataset_path("test.edgelist"),
        directed=False,
        input_type="edgelist"
    )
    G = network.core_network

    # Get first 10 nodes for demonstration (network is large)
    demo_nodes = list(G.nodes())[:10]

    # Generate walks from subset of nodes
    all_walks = generate_walks(G, num_walks=5, walk_length=5, start_nodes=demo_nodes, seed=42)
    print(f"\nGenerated {len(all_walks)} walks from {len(demo_nodes)} nodes")
    print(f"Expected: {len(demo_nodes) * 5} walks")

    # Generate walks from specific nodes
    subset_walks = generate_walks(
        G,
        num_walks=3,
        walk_length=10,
        start_nodes=demo_nodes[:3],
        seed=42
    )
    print(f"\nGenerated {len(subset_walks)} walks from first 3 nodes")
    print(f"First walk (first 5 nodes): {' -> '.join(str(n) for n in subset_walks[0][:5])}...")

    # Generate edge sequences
    edge_walks = generate_walks(
        G,
        num_walks=2,
        walk_length=5,
        start_nodes=[demo_nodes[0]],
        return_edges=True,
        seed=42
    )
    print("\nEdge sequences (first walk, first 3 edges):")
    for edge in edge_walks[0][:3]:
        print(f"  {edge[0]} -> {edge[1]}")


def example_multilayer_walks():
    """Demonstrate multilayer network walks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Multilayer Network Walks")
    print("=" * 70)

    # Create a simple graph with layer information in node names
    # This demonstrates the concept without requiring full multilayer setup
    import networkx as nx
    G = nx.Graph()

    # Add nodes with layer information (py3plex format: "nodeID---layerID")

    # Add intra-layer edges
    G.add_edges_from([
        ("A---social", "B---social"),
        ("B---social", "C---social"),
        ("C---social", "A---social"),
        ("A---biological", "B---biological"),
        ("B---biological", "C---biological"),
    ])

    # Add inter-layer edges (connecting same node across layers)
    G.add_edges_from([
        ("A---social", "A---biological"),
        ("B---social", "B---biological"),
    ])

    print("Multilayer graph:")
    print("  Layers: 2 (social, biological)")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    # Layer-constrained walk
    walk_constrained = layer_specific_random_walk(
        G,
        start_node="A---social",
        walk_length=10,
        layer="social",
        cross_layer_prob=0.0,
        seed=42
    )
    print("\nLayer-constrained walk (social only):")
    print(f"  {' -> '.join(walk_constrained)}")
    print(f"  All nodes in social layer: {all('social' in node for node in walk_constrained)}")

    # Walk with cross-layer transitions
    walk_cross = layer_specific_random_walk(
        G,
        start_node="A---social",
        walk_length=10,
        layer="social",
        cross_layer_prob=0.3,
        seed=42
    )
    print("\nWalk with 30% cross-layer probability:")
    print(f"  {' -> '.join(walk_cross)}")

    # Count layer transitions
    social_count = sum(1 for node in walk_cross if 'social' in node)
    bio_count = sum(1 for node in walk_cross if 'biological' in node)
    print(f"  Nodes in social layer: {social_count}")
    print(f"  Nodes in biological layer: {bio_count}")


def example_statistical_validation():
    """Demonstrate statistical properties of walks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Statistical Validation")
    print("=" * 70)

    # For statistical validation, we use simple constructed graphs
    # to verify mathematical properties
    import networkx as nx

    # Test edge weight frequency
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 1.0),
        (0, 2, 2.0),
        (0, 3, 3.0),
    ])

    print("Graph with weighted edges from node 0:")
    print("  0 -- 1: weight=1.0")
    print("  0 -- 2: weight=2.0")
    print("  0 -- 3: weight=3.0")
    print("  Expected visit ratio: 1:2:3")

    visits = Counter()
    num_trials = 10000

    for i in range(num_trials):
        walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
        if len(walk) > 1:
            visits[walk[1]] += 1

    total = sum(visits.values())
    print(f"\nObserved visits over {num_trials} walks:")
    print(f"  Node 1: {visits[1]} ({visits[1]/total:.3f})")
    print(f"  Node 2: {visits[2]} ({visits[2]/total:.3f})")
    print(f"  Node 3: {visits[3]} ({visits[3]/total:.3f})")
    print("\nExpected probabilities:")
    print(f"  Node 1: {1/6:.3f}")
    print(f"  Node 2: {2/6:.3f}")
    print(f"  Node 3: {3/6:.3f}")

    # Test uniformity on complete graph
    print("\n" + "-" * 70)
    print("Uniformity test on complete graph")
    print("-" * 70)

    n = 10
    G_complete = nx.complete_graph(n)
    visits_uniform = Counter()

    for i in range(num_trials):
        walk = basic_random_walk(G_complete, 0, 1, weighted=False, seed=i)
        if len(walk) > 1:
            visits_uniform[walk[1]] += 1

    expected_per_node = num_trials / (n - 1)
    print(f"Complete graph with {n} nodes")
    print(f"Expected visits per neighbor: {expected_per_node:.1f}")

    deviations = []
    for node in range(1, n):
        deviation = abs(visits_uniform[node] - expected_per_node) / expected_per_node
        deviations.append(deviation)
        print(f"  Node {node}: {visits_uniform[node]} visits (deviation: {deviation:.3f})")

    avg_deviation = np.mean(deviations)
    print(f"Average deviation: {avg_deviation:.3f} (should be < 0.1)")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("RANDOM WALK EXAMPLES FOR PY3PLEX")
    print("=" * 70)

    example_basic_random_walk()
    example_weighted_random_walk()
    example_node2vec_biased_walk()
    example_generate_multiple_walks()
    example_multilayer_walks()
    example_statistical_validation()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
