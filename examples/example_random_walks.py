"""
Random Walk Examples for Py3plex

This example demonstrates the comprehensive random walk capabilities:
1. Basic random walks with weighted edges
2. Node2Vec biased random walks with p/q parameters
3. Multiple walk generation
4. Multilayer network walks
5. Statistical validation of walk properties
"""

import networkx as nx
import numpy as np
from collections import Counter

from py3plex.algorithms.general.walkers import (
    basic_random_walk,
    node2vec_walk,
    generate_walks,
    layer_specific_random_walk,
)


def example_basic_random_walk():
    """Demonstrate basic random walk functionality."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Random Walk")
    print("=" * 70)
    
    # Create Karate Club graph
    G = nx.karate_club_graph()
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Perform a random walk
    walk = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    print(f"\nRandom walk from node 0:")
    print(f"  Path: {' -> '.join(map(str, walk))}")
    print(f"  Length: {len(walk)} nodes")
    
    # Verify reproducibility
    walk2 = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    print(f"\nReproducibility check:")
    print(f"  Walk 1 == Walk 2: {walk == walk2}")


def example_weighted_random_walk():
    """Demonstrate weighted edge handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Weighted Random Walk")
    print("=" * 70)
    
    # Create weighted graph
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 10.0),  # high weight
        (0, 2, 1.0),   # low weight
        (1, 2, 5.0),
    ])
    
    print(f"Graph edges with weights:")
    for u, v, w in G.edges(data='weight'):
        print(f"  {u} -- {v}: weight={w}")
    
    # Count visits to neighbors of node 0
    visits_weighted = Counter()
    visits_unweighted = Counter()
    
    num_trials = 1000
    for i in range(num_trials):
        # Weighted walk
        walk_w = basic_random_walk(G, 0, 1, weighted=True, seed=i)
        if len(walk_w) > 1:
            visits_weighted[walk_w[1]] += 1
        
        # Unweighted walk
        walk_u = basic_random_walk(G, 0, 1, weighted=False, seed=i)
        if len(walk_u) > 1:
            visits_unweighted[walk_u[1]] += 1
    
    print(f"\nVisit frequency over {num_trials} walks from node 0:")
    print(f"  Weighted:   Node 1: {visits_weighted[1]}, Node 2: {visits_weighted[2]}")
    print(f"  Unweighted: Node 1: {visits_unweighted[1]}, Node 2: {visits_unweighted[2]}")
    print(f"  Weight ratio (10:1) vs visit ratio: {visits_weighted[1] / max(visits_weighted[2], 1):.1f}:1")


def example_node2vec_biased_walk():
    """Demonstrate Node2Vec biased random walks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Node2Vec Biased Random Walk")
    print("=" * 70)
    
    # Create triangle graph for demonstrating bias
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
    
    G = nx.karate_club_graph()
    
    # Generate walks from all nodes
    all_walks = generate_walks(G, num_walks=10, walk_length=5, seed=42)
    print(f"\nGenerated {len(all_walks)} walks from all {G.number_of_nodes()} nodes")
    print(f"Expected: {G.number_of_nodes() * 10} walks")
    
    # Generate walks from specific nodes
    subset_walks = generate_walks(
        G, 
        num_walks=5, 
        walk_length=10, 
        start_nodes=[0, 1, 2],
        seed=42
    )
    print(f"\nGenerated {len(subset_walks)} walks from nodes [0, 1, 2]")
    print(f"First walk: {' -> '.join(map(str, subset_walks[0]))}")
    
    # Generate edge sequences
    edge_walks = generate_walks(
        G,
        num_walks=3,
        walk_length=5,
        start_nodes=[0],
        return_edges=True,
        seed=42
    )
    print(f"\nEdge sequences (first walk):")
    for edge in edge_walks[0]:
        print(f"  {edge[0]} -> {edge[1]}")


def example_multilayer_walks():
    """Demonstrate multilayer network walks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Multilayer Network Walks")
    print("=" * 70)
    
    # Create a simple graph with layer information in node names
    # This demonstrates the concept without requiring full multilayer setup
    G = nx.Graph()
    
    # Add nodes with layer information (py3plex format: "nodeID---layerID")
    nodes_social = ["A---social", "B---social", "C---social"]
    nodes_biological = ["A---biological", "B---biological", "C---biological"]
    
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
    
    print(f"Multilayer graph:")
    print(f"  Layers: 2 (social, biological)")
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
    print(f"\nLayer-constrained walk (social only):")
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
    print(f"\nWalk with 30% cross-layer probability:")
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
    print(f"\nExpected probabilities:")
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
