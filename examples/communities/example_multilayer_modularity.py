#!/usr/bin/env python3
"""
Example: Multilayer Modularity and Community Detection

This script demonstrates the multilayer modularity maximization capabilities
in py3plex, including:
- Calculating multilayer modularity
- Detecting communities with the generalized Louvain algorithm
- Generating synthetic multilayer networks with ground-truth communities

Prerequisites:
- numpy, scipy, and networkx must be installed (pulled in by py3plex)

SKIP_CI: slow - Runs Louvain algorithm multiple times with synthetic network generation, takes more than 10 seconds
"""

import sys
import os

# Add parent directory to path to import py3plex
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        multilayer_modularity,
        louvain_multilayer,
    )
    from py3plex.algorithms.community_detection.multilayer_benchmark import (
        generate_multilayer_lfr,
        generate_coupled_er_multilayer,
        generate_sbm_multilayer,
    )
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install required packages: numpy, scipy, networkx")
    sys.exit(1)

DEFAULT_SEED = 42


def example_basic_modularity():
    """Example 1: Basic multilayer modularity calculation."""
    print("=" * 70)
    print("Example 1: Basic Multilayer Modularity")
    print("=" * 70)

    # Create a simple 2-layer network
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: Triangle (A-B-C all connected)
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1]
    ], input_type='list')

    # Layer 2: Line (A-B-C)
    network.add_edges([
        ['A', 'L2', 'B', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1]
    ], input_type='list')

    print("\nNetwork structure:")
    print(f"  Nodes: {len(list(network.get_nodes()))}")
    print(f"  Edges: {len(list(network.get_edges()))}")

    # Test different community assignments
    print("\nTesting community assignments:")

    # All nodes in same community
    communities1 = {
        ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 0,
        ('A', 'L2'): 0, ('B', 'L2'): 0, ('C', 'L2'): 0
    }
    Q1 = multilayer_modularity(network, communities1, gamma=1.0, omega=1.0)
    print(f"  All in same community: Q = {Q1:.4f}")

    # Split into two communities
    communities2 = {
        ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
        ('A', 'L2'): 0, ('B', 'L2'): 0, ('C', 'L2'): 1
    }
    Q2 = multilayer_modularity(network, communities2, gamma=1.0, omega=1.0)
    print(f"  Split communities: Q = {Q2:.4f}")

    # Test effect of coupling
    print("\nEffect of inter-layer coupling (omega):")
    for omega in [0.0, 0.5, 1.0, 2.0]:
        Q = multilayer_modularity(network, communities2, gamma=1.0, omega=omega)
        print(f"  ω = {omega:.1f}: Q = {Q:.4f}")

    print()


def example_louvain_detection():
    """Example 2: Community detection with Louvain algorithm."""
    print("=" * 70)
    print("Example 2: Community Detection with Louvain")
    print("=" * 70)

    # Create a network with clear community structure
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: Two cliques
    edges_l1 = [
        # Clique 1
        ['A', 'L1', 'B', 'L1', 1],
        ['A', 'L1', 'C', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        # Clique 2
        ['D', 'L1', 'E', 'L1', 1],
        ['D', 'L1', 'F', 'L1', 1],
        ['E', 'L1', 'F', 'L1', 1],
        # Bridge
        ['C', 'L1', 'D', 'L1', 1],
    ]

    # Layer 2: Similar structure
    edges_l2 = [
        ['A', 'L2', 'B', 'L2', 1],
        ['A', 'L2', 'C', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1],
        ['D', 'L2', 'E', 'L2', 1],
        ['D', 'L2', 'F', 'L2', 1],
        ['E', 'L2', 'F', 'L2', 1],
        ['C', 'L2', 'D', 'L2', 1],
    ]

    network.add_edges(edges_l1 + edges_l2, input_type='list')

    print("\nNetwork structure:")
    print(f"  Nodes: {len({n for n, l in network.get_nodes()})}")
    print("  Layers: 2")
    print(f"  Total edges: {len(list(network.get_edges()))}")

    # Detect communities with different coupling strengths
    print("\nDetecting communities with different coupling strengths:")

    for omega in [0.0, 1.0, 5.0]:
        communities = louvain_multilayer(
            network, gamma=1.0, omega=omega, random_state=DEFAULT_SEED, max_iter=20
        )
        Q = multilayer_modularity(network, communities, gamma=1.0, omega=omega)
        n_communities = len(set(communities.values()))

        print(f"\n  ω = {omega:.1f}:")
        print(f"    Modularity: Q = {Q:.4f}")
        print(f"    Number of communities: {n_communities}")

        # Show assignment for a few nodes
        print("    Sample assignments:")
        for node in ['A', 'B', 'D', 'E']:
            coms = [communities.get((node, layer), -1) for layer in ['L1', 'L2']]
            print(f"      Node {node}: L1→{coms[0]}, L2→{coms[1]}")

    print()


def example_synthetic_networks():
    """Example 3: Generating synthetic multilayer networks."""
    print("=" * 70)
    print("Example 3: Synthetic Multilayer Networks")
    print("=" * 70)

    # Example 3a: Multilayer LFR
    print("\n3a. Multilayer LFR Benchmark:")
    print("    Generating network with ground-truth communities...")

    try:
        network, ground_truth = generate_multilayer_lfr(
            n=50,
            layers=['L1', 'L2'],
            mu=0.15,
            avg_degree=8,
            min_community=10,
            community_persistence=0.8,
            seed=DEFAULT_SEED
        )

        print(f"    Generated network with {len(list(network.get_nodes()))} node-layer pairs")
        print(f"    Ground truth: {len(set().union(*ground_truth.values()))} communities")

        # Detect communities
        detected = louvain_multilayer(
            network, gamma=1.0, omega=1.0, random_state=DEFAULT_SEED, max_iter=20
        )
        Q = multilayer_modularity(network, detected, gamma=1.0, omega=1.0)

        print(f"    Detected: {len(set(detected.values()))} communities")
        print(f"    Modularity: Q = {Q:.4f}")

    except Exception as e:
        print(f"    Error generating LFR: {e}")

    # Example 3b: Coupled ER
    print("\n3b. Coupled Erdős-Rényi:")
    print("    Generating random multilayer network...")

    try:
        network = generate_coupled_er_multilayer(
            n=50,
            layers=['L1', 'L2', 'L3'],
            p=0.1,
            omega=1.0,
            coupling_probability=1.0,
            seed=DEFAULT_SEED
        )

        print(f"    Generated network with {len(list(network.get_nodes()))} node-layer pairs")
        print(f"    Total edges: {len(list(network.get_edges()))}")

        # Detect communities (should be few or none in random graph)
        communities = louvain_multilayer(
            network, gamma=1.0, omega=1.0, random_state=DEFAULT_SEED, max_iter=20
        )
        Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)

        print(f"    Detected: {len(set(communities.values()))} communities")
        print(f"    Modularity: Q = {Q:.4f} (expected near 0 for random graph)")

    except Exception as e:
        print(f"    Error generating coupled ER: {e}")

    # Example 3c: Stochastic Block Model
    print("\n3c. Multilayer Stochastic Block Model:")
    print("    Generating network with block structure...")

    try:
        communities_gt = [
            {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},      # Block 0
            {10, 11, 12, 13, 14, 15, 16, 17, 18, 19}  # Block 1
        ]

        network, ground_truth = generate_sbm_multilayer(
            n=20,
            layers=['L1', 'L2'],
            communities=communities_gt,
            p_in=0.6,
            p_out=0.05,
            community_persistence=0.9,
            seed=DEFAULT_SEED
        )

        print(f"    Generated network with {len(list(network.get_nodes()))} node-layer pairs")
        print(f"    Ground truth: {len(set(ground_truth.values()))} blocks")

        # Detect communities
        detected = louvain_multilayer(
            network, gamma=1.0, omega=1.0, random_state=DEFAULT_SEED, max_iter=20
        )
        Q = multilayer_modularity(network, detected, gamma=1.0, omega=1.0)

        print(f"    Detected: {len(set(detected.values()))} communities")
        print(f"    Modularity: Q = {Q:.4f}")

    except Exception as e:
        print(f"    Error generating SBM: {e}")

    print()


def example_parameter_tuning():
    """Example 4: Parameter tuning for resolution and coupling."""
    print("=" * 70)
    print("Example 4: Parameter Tuning")
    print("=" * 70)

    # Create test network
    network = multinet.multi_layer_network(directed=False)

    # Two communities in each layer
    edges = [
        # Layer 1
        ['A', 'L1', 'B', 'L1', 1], ['A', 'L1', 'C', 'L1', 1], ['B', 'L1', 'C', 'L1', 1],
        ['D', 'L1', 'E', 'L1', 1], ['D', 'L1', 'F', 'L1', 1], ['E', 'L1', 'F', 'L1', 1],
        # Layer 2
        ['A', 'L2', 'B', 'L2', 1], ['A', 'L2', 'C', 'L2', 1], ['B', 'L2', 'C', 'L2', 1],
        ['D', 'L2', 'E', 'L2', 1], ['D', 'L2', 'F', 'L2', 1], ['E', 'L2', 'F', 'L2', 1],
    ]
    network.add_edges(edges, input_type='list')

    print("\nTesting different parameter combinations:")
    print(f"{'γ':>6} {'ω':>6} {'Q':>8} {'#Com':>6}")
    print("-" * 30)

    best_Q = -float('inf')
    best_params = None

    for gamma in [0.5, 1.0, 1.5]:
        for omega in [0.1, 1.0, 5.0]:
            try:
                communities = louvain_multilayer(
                    network, gamma=gamma, omega=omega, random_state=DEFAULT_SEED, max_iter=20
                )
                Q = multilayer_modularity(network, communities, gamma=gamma, omega=omega)
                n_com = len(set(communities.values()))

                print(f"{gamma:>6.1f} {omega:>6.1f} {Q:>8.4f} {n_com:>6}")

                if Q > best_Q:
                    best_Q = Q
                    best_params = (gamma, omega, n_com)
            except Exception as e:
                print(f"{gamma:>6.1f} {omega:>6.1f}   Error: {e}")

    if best_params:
        print(f"\nBest parameters: γ={best_params[0]:.1f}, ω={best_params[1]:.1f}")
        print(f"  Modularity: Q = {best_Q:.4f}")
        print(f"  Communities: {best_params[2]}")

    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MULTILAYER MODULARITY AND COMMUNITY DETECTION EXAMPLES")
    print("=" * 70 + "\n")

    try:
        example_basic_modularity()
        example_louvain_detection()
        example_synthetic_networks()
        example_parameter_tuning()

        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
