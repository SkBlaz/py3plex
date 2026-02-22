#!/usr/bin/env python3
"""
Example: Versatility (Multilayer Eigenvector Centrality)

This example demonstrates how to compute versatility, a multilayer centrality
that ranks nodes by aggregating their eigenvector-based importance across layers
of an interconnected (multiplex) network.

Versatility is based on the multilayer eigenvector centrality formulation from:
- De Domenico et al. (2013) "Mathematical Formulation of Multilayer Networks"
- De Domenico et al. (2015) "Ranking in interconnected multilayer networks reveals versatile nodes"

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

import numpy as np
import scipy.sparse as sp
from py3plex.algorithms.multilayer_algorithms.versatility import (
    build_supra_adjacency,
    versatility,
    versatility_katz,
)


def example_1_basic_usage():
    """Example 1: Basic versatility computation on a 2-layer network."""
    print("\n" + "="*70)
    print("Example 1: Basic Versatility Computation")
    print("="*70)

    # Create Layer 1: Triangle (social network)
    # All nodes equally connected
    L1 = sp.csr_matrix([
        [0, 1, 1, 0],
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0]
    ])

    # Create Layer 2: Star (collaboration network)
    # Node 0 is the hub
    L2 = sp.csr_matrix([
        [0, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 0]
    ])

    # Compute versatility with interlayer coupling omega=0.1
    v = versatility([L1, L2], interlayer=0.1, normalize="l1", seed=42)

    print("\nLayer 1 (Social): Triangle among nodes 0,1,2; node 3 isolated")
    print("Layer 2 (Collab): Star with node 0 as hub")
    print("\nVersatility scores (omega=0.1):")
    for i, score in enumerate(v):
        print(f"  Node {i}: {score:.4f}")

    print("\nInterpretation:")
    print("  - Node 0 has highest versatility (central in Layer 2, connected in Layer 1)")
    print("  - Node 3 has lowest versatility (isolated in Layer 1)")


def example_2_omega_effect():
    """Example 2: Effect of interlayer coupling strength (omega)."""
    print("\n" + "="*70)
    print("Example 2: Effect of Interlayer Coupling (omega)")
    print("="*70)

    # Layer 1: Node 0 is central
    L1 = sp.csr_matrix([
        [0, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 0]
    ])

    # Layer 2: Node 1 is central
    L2 = sp.csr_matrix([
        [0, 1, 0, 0],
        [1, 0, 1, 1],
        [0, 1, 0, 0],
        [0, 1, 0, 0]
    ])

    print("\nLayer 1: Node 0 is hub")
    print("Layer 2: Node 1 is hub")

    omegas = [0.01, 0.1, 0.5, 1.0]

    print("\nVersatility scores for different omega values:")
    print(f"{'Omega':<10} {'Node 0':<12} {'Node 1':<12} {'Node 2':<12} {'Node 3':<12}")
    print("-" * 58)

    for omega in omegas:
        v = versatility([L1, L2], interlayer=omega, normalize="l1", seed=42)
        print(f"{omega:<10.2f} {v[0]:<12.4f} {v[1]:<12.4f} {v[2]:<12.4f} {v[3]:<12.4f}")

    print("\nInterpretation:")
    print("  - Low omega: Layers are weakly coupled, rankings dominated by individual layers")
    print("  - High omega: Layers are strongly coupled, rankings blend across layers")
    print("  - As omega increases, versatility becomes more balanced across nodes")


def example_3_layer_scores():
    """Example 3: Examining per-layer contributions to versatility."""
    print("\n" + "="*70)
    print("Example 3: Per-Layer Versatility Scores")
    print("="*70)

    # Create 3 layers with different structures
    # Layer 1: Triangle
    L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])

    # Layer 2: Path
    L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

    # Layer 3: Star
    L3 = sp.csr_matrix([[0, 1, 1], [1, 0, 0], [1, 0, 0]])

    # Compute versatility with layer scores
    v, X = versatility(
        [L1, L2, L3],
        interlayer=0.2,
        normalize="l1",
        return_layer_scores=True,
        seed=42
    )

    print("\nLayer structures:")
    print("  Layer 1: Triangle (all nodes equal)")
    print("  Layer 2: Path (node 1 central)")
    print("  Layer 3: Star (node 0 central)")

    print("\nPer-layer scores (X[i, alpha]):")
    print(f"{'Node':<8} {'Layer 1':<12} {'Layer 2':<12} {'Layer 3':<12} {'Total':<12}")
    print("-" * 56)

    for i in range(3):
        print(f"{i:<8} {X[i,0]:<12.4f} {X[i,1]:<12.4f} {X[i,2]:<12.4f} {v[i]:<12.4f}")

    print("\nInterpretation:")
    print("  - Each column shows node importance within that layer")
    print("  - Total versatility = sum across layers")
    print("  - Versatile nodes contribute significantly across multiple layers")


def example_4_directed_weighted():
    """Example 4: Directed and weighted networks."""
    print("\n" + "="*70)
    print("Example 4: Directed and Weighted Networks")
    print("="*70)

    # Layer 1: Directed citation network
    L1 = sp.csr_matrix([
        [0, 2, 0],  # Paper 0 cites Paper 1 (weight=2)
        [0, 0, 3],  # Paper 1 cites Paper 2 (weight=3)
        [1, 1, 0]   # Paper 2 cites both (weight=1 each)
    ])

    # Layer 2: Directed collaboration network
    L2 = sp.csr_matrix([
        [0, 1, 2],  # Collaborations from 0
        [0, 0, 1],  # Collaborations from 1
        [0, 0, 0]   # No collaborations from 2
    ])

    v = versatility([L1, L2], interlayer=0.3, normalize="l1", seed=42)

    print("\nLayer 1: Citation network (directed, weighted)")
    print("Layer 2: Collaboration network (directed, weighted)")

    print("\nVersatility scores:")
    for i, score in enumerate(v):
        print(f"  Node {i}: {score:.4f}")

    print("\nInterpretation:")
    print("  - Node 1 has high versatility (receives citations, central in both layers)")
    print("  - Weights affect the strength of connections")
    print("  - Direction matters: incoming vs outgoing edges contribute differently")


def example_5_missing_nodes():
    """Example 5: Handling nodes absent from some layers."""
    print("\n" + "="*70)
    print("Example 5: Nodes Absent from Some Layers")
    print("="*70)

    # Layer 1: All 4 nodes present
    L1 = sp.csr_matrix([
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 1, 1, 0]
    ])

    # Layer 2: Node 3 is absent (zero row/column)
    L2 = sp.csr_matrix([
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0]
    ])

    # Layer 3: Node 2 is absent
    L3 = sp.csr_matrix([
        [0, 1, 0, 1],
        [1, 0, 0, 1],
        [0, 0, 0, 0],
        [1, 1, 0, 0]
    ])

    v = versatility([L1, L2, L3], interlayer=0.15, normalize="l1", seed=42)

    print("\nLayer presence:")
    print("  Node 0: present in all layers")
    print("  Node 1: present in all layers")
    print("  Node 2: absent from Layer 3")
    print("  Node 3: absent from Layer 2")

    print("\nVersatility scores:")
    for i, score in enumerate(v):
        print(f"  Node {i}: {score:.4f}")

    print("\nInterpretation:")
    print("  - Nodes absent from some layers have lower versatility")
    print("  - Interlayer coupling helps: absent nodes still get some score from other layers")
    print("  - No NaNs or infinities - robust handling of missing data")


def example_6_katz_fallback():
    """Example 6: Using Katz-based versatility for difficult graphs."""
    print("\n" + "="*70)
    print("Example 6: Katz Versatility for Reducible Graphs")
    print("="*70)

    # Create a graph with weak connectivity
    # Layer 1: Two disconnected components
    L1 = sp.csr_matrix([
        [0, 1, 0, 0],
        [1, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0]
    ])

    # Layer 2: Different structure
    L2 = sp.csr_matrix([
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [1, 0, 0, 0],
        [0, 1, 0, 0]
    ])

    print("\nLayer 1: Two disconnected components {0,1} and {2,3}")
    print("Layer 2: Two cycles")

    # Standard versatility
    v_standard = versatility([L1, L2], interlayer=0.05, normalize="l1", seed=42)

    # Katz versatility with automatic alpha
    v_katz = versatility_katz([L1, L2], interlayer=0.05, alpha=None, normalize="l1")

    print("\nStandard versatility:")
    for i, score in enumerate(v_standard):
        print(f"  Node {i}: {score:.4f}")

    print("\nKatz versatility (damping-based):")
    for i, score in enumerate(v_katz):
        print(f"  Node {i}: {score:.4f}")

    print("\nInterpretation:")
    print("  - Katz versatility is more robust for reducible graphs")
    print("  - Damping prevents concentration on single component")
    print("  - Use Katz when standard method has convergence issues")


def example_7_supra_adjacency():
    """Example 7: Understanding the supra-adjacency matrix."""
    print("\n" + "="*70)
    print("Example 7: Supra-Adjacency Matrix Structure")
    print("="*70)

    # Small 2-node, 2-layer example
    L1 = sp.csr_matrix([[0, 1], [1, 0]])
    L2 = sp.csr_matrix([[0, 1], [1, 0]])

    S = build_supra_adjacency([L1, L2], interlayer=0.5)

    print("\nLayer adjacencies:")
    print("L1 =")
    print(L1.toarray())
    print("\nL2 =")
    print(L2.toarray())

    print(f"\nSupra-adjacency matrix (4x4 for 2 nodes x 2 layers):")
    print("     [L1 block | coupling ]")
    print("S =  [---------|----------]")
    print("     [coupling | L2 block ]")
    print()
    print(S.toarray())

    print("\nInterpretation:")
    print("  - Block (0:2, 0:2): Layer 1 adjacency")
    print("  - Block (2:4, 2:4): Layer 2 adjacency")
    print("  - Off-diagonal: Interlayer coupling (omega=0.5)")
    print("  - Total size: (NxL) x (NxL) = 4 x 4")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("VERSATILITY: MULTILAYER EIGENVECTOR CENTRALITY")
    print("="*70)
    print("\nThis script demonstrates versatility computation on multilayer networks.")
    print("\nReferences:")
    print("  - De Domenico et al. (2013) Phys. Rev. X 3, 041022")
    print("  - De Domenico et al. (2015) Nat. Comm. 6, 6868")

    try:
        example_1_basic_usage()
        example_2_omega_effect()
        example_3_layer_scores()
        example_4_directed_weighted()
        example_5_missing_nodes()
        example_6_katz_fallback()
        example_7_supra_adjacency()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
