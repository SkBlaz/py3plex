#!/usr/bin/env python3
"""
Example: New Multiplex Network Metrics

This example demonstrates the newly implemented metrics for multiplex networks,
including betweenness, closeness, participation, redundancy, rich-club,
percolation, and modularity measures.

Runtime: FAST (< 5 seconds)
"""

from py3plex.core import multinet
from py3plex.algorithms.statistics import multilayer_statistics
import numpy as np


def create_example_network():
    """Create a sample multiplex network with interesting structure."""
    network = multinet.multi_layer_network(directed=False)

    # Social layer: Triangle plus bridge
    network.add_edges([
        ['Alice', 'Social', 'Bob', 'Social', 1],
        ['Bob', 'Social', 'Charlie', 'Social', 1],
        ['Charlie', 'Social', 'Alice', 'Social', 1],
        ['Charlie', 'Social', 'David', 'Social', 1],  # Bridge
    ], input_type='list')

    # Work layer: Star topology
    network.add_edges([
        ['Alice', 'Work', 'Bob', 'Work', 1],
        ['Alice', 'Work', 'Charlie', 'Work', 1],
        ['Alice', 'Work', 'David', 'Work', 1],
        ['Alice', 'Work', 'Eve', 'Work', 1],
    ], input_type='list')

    # Family layer: Different structure with some overlap
    network.add_edges([
        ['Bob', 'Family', 'Charlie', 'Family', 1],
        ['Bob', 'Family', 'David', 'Family', 1],
        ['David', 'Family', 'Eve', 'Family', 1],
    ], input_type='list')

    return network


def demonstrate_centrality_metrics():
    """Demonstrate multiplex betweenness and closeness."""
    print("\n" + "="*70)
    print("1. MULTIPLEX CENTRALITY METRICS")
    print("="*70)

    network = create_example_network()

    # Multiplex betweenness
    betweenness = multilayer_statistics.multiplex_betweenness_centrality(network)
    print("\nMultiplex Betweenness Centrality (top 5):")
    sorted_between = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
    for node_layer, value in sorted_between:
        print(f"  {str(node_layer):30} {value:.4f}")

    # Multiplex closeness
    closeness = multilayer_statistics.multiplex_closeness_centrality(network)
    print("\nMultiplex Closeness Centrality (top 5):")
    sorted_close = sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:5]
    for node_layer, value in sorted_close:
        print(f"  {str(node_layer):30} {value:.4f}")


def demonstrate_participation_metrics():
    """Demonstrate community participation measures."""
    print("\n" + "="*70)
    print("2. COMMUNITY PARTICIPATION METRICS")
    print("="*70)

    network = create_example_network()

    # Define simple community structure
    communities = {
        ('Alice', 'Social'): 0,
        ('Bob', 'Social'): 0,
        ('Charlie', 'Social'): 0,
        ('David', 'Social'): 1,
        ('Alice', 'Work'): 0,
        ('Bob', 'Work'): 0,
        ('Charlie', 'Work'): 0,
        ('David', 'Work'): 1,
        ('Eve', 'Work'): 1,
        ('Bob', 'Family'): 0,
        ('Charlie', 'Family'): 0,
        ('David', 'Family'): 1,
        ('Eve', 'Family'): 1,
    }

    nodes = ['Alice', 'Bob', 'Charlie', 'David', 'Eve']

    print("\nParticipation Coefficient:")
    for node in nodes:
        pc = multilayer_statistics.community_participation_coefficient(
            network, communities, node
        )
        print(f"  {node:10} {pc:.4f}")

    print("\nParticipation Entropy:")
    for node in nodes:
        entropy = multilayer_statistics.community_participation_entropy(
            network, communities, node
        )
        print(f"  {node:10} {entropy:.4f}")


def demonstrate_redundancy_metrics():
    """Demonstrate layer redundancy analysis."""
    print("\n" + "="*70)
    print("3. LAYER REDUNDANCY METRICS")
    print("="*70)

    network = create_example_network()
    layers = ['Social', 'Work', 'Family']

    print("\nLayer Redundancy Coefficients:")
    for i, layer_i in enumerate(layers):
        for layer_j in layers[i+1:]:
            redundancy = multilayer_statistics.layer_redundancy_coefficient(
                network, layer_i, layer_j
            )
            unique, redundant = multilayer_statistics.unique_redundant_edges(
                network, layer_i, layer_j
            )
            print(f"  {layer_i:10} vs {layer_j:10}: redundancy={redundancy:.3f}, "
                  f"unique={unique}, redundant={redundant}")


def demonstrate_rich_club():
    """Demonstrate rich-club analysis."""
    print("\n" + "="*70)
    print("4. RICH-CLUB ANALYSIS")
    print("="*70)

    network = create_example_network()

    print("\nRich-Club Coefficient by Degree Threshold:")
    for k in [1, 2, 3]:
        phi = multilayer_statistics.multiplex_rich_club_coefficient(network, k=k)
        print(f"  k={k}: φ(k) = {phi:.4f}")


def demonstrate_percolation():
    """Demonstrate percolation and robustness analysis."""
    print("\n" + "="*70)
    print("5. PERCOLATION AND ROBUSTNESS")
    print("="*70)

    network = create_example_network()

    # Percolation threshold
    print("\nPercolation Thresholds (estimated):")
    for strategy in ['random', 'degree']:
        threshold = multilayer_statistics.percolation_threshold(
            network, removal_strategy=strategy, trials=5
        )
        print(f"  {strategy:10} removal: {threshold:.3f}")

    # Targeted layer removal
    print("\nResilience After Layer Removal:")
    for layer in ['Social', 'Work', 'Family']:
        resilience = multilayer_statistics.targeted_layer_removal(
            network, layer, return_resilience=True
        )
        print(f"  Remove {layer:10} layer: resilience = {resilience:.3f}")


def demonstrate_modularity():
    """Demonstrate modularity computation."""
    print("\n" + "="*70)
    print("6. MODULARITY COMPUTATION")
    print("="*70)

    network = create_example_network()

    # Define two different community structures
    communities_1 = {
        ('Alice', 'Social'): 0,
        ('Bob', 'Social'): 0,
        ('Charlie', 'Social'): 0,
        ('David', 'Social'): 1,
        ('Alice', 'Work'): 0,
        ('Bob', 'Work'): 0,
        ('Charlie', 'Work'): 0,
        ('David', 'Work'): 1,
        ('Eve', 'Work'): 1,
        ('Bob', 'Family'): 0,
        ('Charlie', 'Family'): 0,
        ('David', 'Family'): 1,
        ('Eve', 'Family'): 1,
    }

    communities_2 = {
        ('Alice', 'Social'): 0,
        ('Bob', 'Social'): 1,
        ('Charlie', 'Social'): 1,
        ('David', 'Social'): 1,
        ('Alice', 'Work'): 0,
        ('Bob', 'Work'): 1,
        ('Charlie', 'Work'): 1,
        ('David', 'Work'): 1,
        ('Eve', 'Work'): 1,
        ('Bob', 'Family'): 1,
        ('Charlie', 'Family'): 1,
        ('David', 'Family'): 1,
        ('Eve', 'Family'): 1,
    }

    print("\nModularity Scores:")
    Q1 = multilayer_statistics.compute_modularity_score(network, communities_1)
    Q2 = multilayer_statistics.compute_modularity_score(network, communities_2)
    print(f"  Partition 1: Q = {Q1:.4f}")
    print(f"  Partition 2: Q = {Q2:.4f}")
    print(f"\n  Better partition: {'Partition 1' if Q1 > Q2 else 'Partition 2'}")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("DEMONSTRATION: NEW MULTIPLEX NETWORK METRICS")
    print("="*70)
    print("\nThis script demonstrates the newly implemented metrics for")
    print("multiplex network analysis in py3plex.")

    try:
        demonstrate_centrality_metrics()
        demonstrate_participation_metrics()
        demonstrate_redundancy_metrics()
        demonstrate_rich_club()
        demonstrate_percolation()
        demonstrate_modularity()

        print("\n" + "="*70)
        print("All demonstrations completed successfully!")
        print("="*70)
        print("\nThese metrics extend py3plex's capabilities for analyzing")
        print("complex multilayer network structures.")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
