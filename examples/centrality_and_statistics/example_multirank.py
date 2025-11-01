#!/usr/bin/env python3
"""
Example: MultiRank and Multiplex PageRank Variants

This example demonstrates the use of MultiRank and Multiplex PageRank variants
for multilayer network analysis.

These algorithms are particularly useful for:
1. Co-ranking nodes and layers simultaneously (MultiRank)
2. Modeling cross-layer influence in social and information networks (Multiplex PageRank)
"""

import numpy as np

from py3plex.algorithms.multilayer_algorithms.multirank import (
    multirank,
    multiplex_pagerank,
)


def example_multirank():
    """Demonstrate MultiRank co-ranking algorithm."""
    print("=" * 70)
    print("Example 1: MultiRank Co-Ranking")
    print("=" * 70)

    # Create a simple 3-node, 2-layer network
    # Layer 1: Well-connected triangle
    L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)

    # Layer 2: Linear chain
    L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

    print("\nLayer 1 (triangle):")
    print(L1)
    print("\nLayer 2 (chain):")
    print(L2)

    # Compute MultiRank
    node_scores, layer_scores = multirank([L1, L2], alpha=0.85)

    print("\nNode scores (importance across all layers):")
    for i, score in enumerate(node_scores):
        print(f"  Node {i}: {score:.4f}")

    print("\nLayer scores (importance of each layer):")
    for i, score in enumerate(layer_scores):
        print(f"  Layer {i+1}: {score:.4f}")

    print(
        "\nInterpretation: Layer 1 has higher score (more connections), "
        "node 1 is most central."
    )


def example_multiplex_pagerank_variants():
    """Demonstrate Multiplex PageRank variants."""
    print("\n" + "=" * 70)
    print("Example 2: Multiplex PageRank Variants")
    print("=" * 70)

    # Create a simple 3-node, 2-layer network
    L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

    # Neutral variant (baseline, no cross-layer influence)
    print("\nNeutral variant (no cross-layer influence):")
    result_neutral = multiplex_pagerank([L1, L2], variant="neutral", alpha=0.85)
    print("  Node scores:", result_neutral["node_scores"])

    # Additive variant (cross-layer influence via sum)
    print("\nAdditive variant (cross-layer sum, c=0.5):")
    result_additive = multiplex_pagerank(
        [L1, L2], variant="additive", c=0.5, alpha=0.85
    )
    print("  Node scores:", result_additive["node_scores"])

    # Multiplicative variant (cross-layer influence via product)
    print("\nMultiplicative variant (cross-layer product, c=0.5):")
    result_multiplicative = multiplex_pagerank(
        [L1, L2], variant="multiplicative", c=0.5, alpha=0.85
    )
    print("  Node scores:", result_multiplicative["node_scores"])

    # Combined variant (additive + multiplicative)
    print("\nCombined variant (c1=0.5, c2=0.3):")
    result_combined = multiplex_pagerank(
        [L1, L2], variant="combined", c1=0.5, c2=0.3, alpha=0.85
    )
    print("  Node scores:", result_combined["node_scores"])

    print(
        "\nInterpretation: Different coupling functions produce different rankings."
    )


def example_comparison():
    """Compare different variants on a larger network."""
    print("\n" + "=" * 70)
    print("Example 3: Comparison on Larger Network")
    print("=" * 70)

    # Create a 5-node, 3-layer network
    np.random.seed(42)
    N = 5
    L = 3

    layers = []
    for ell in range(L):
        # Random adjacency matrix
        layer = np.random.rand(N, N)
        layer = (layer + layer.T) / 2  # Make symmetric
        layer = (layer > 0.5).astype(float)  # Binarize
        np.fill_diagonal(layer, 0)  # Remove self-loops
        layers.append(layer)

    print(f"\nNetwork: {N} nodes, {L} layers")

    # Compare variants
    variants = ["neutral", "additive", "multiplicative", "combined"]
    results = {}

    for variant in variants:
        if variant == "combined":
            result = multiplex_pagerank(
                layers, variant=variant, c1=0.5, c2=0.3
            )
        elif variant == "neutral":
            result = multiplex_pagerank(layers, variant=variant)
        else:
            result = multiplex_pagerank(layers, variant=variant, c=0.5)
        results[variant] = result["node_scores"]

    print("\nNode rankings by variant:")
    print("Node  | Neutral | Additive | Multiplicative | Combined")
    print("-" * 60)
    for i in range(N):
        print(
            f"  {i}   |  {results['neutral'][i]:.3f}  |  {results['additive'][i]:.3f}   "
            f"|     {results['multiplicative'][i]:.3f}      |  {results['combined'][i]:.3f}"
        )


def example_coupling_strength():
    """Demonstrate effect of coupling strength."""
    print("\n" + "=" * 70)
    print("Example 4: Effect of Coupling Strength")
    print("=" * 70)

    # Create a simple network
    L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

    # Test different coupling strengths
    coupling_strengths = [0.1, 0.5, 1.0, 2.0]

    print("\nAdditive variant with different coupling strengths:")
    print("Node  | c=0.1  | c=0.5  | c=1.0  | c=2.0")
    print("-" * 50)

    results_by_c = {}
    for c in coupling_strengths:
        result = multiplex_pagerank([L1, L2], variant="additive", c=c)
        results_by_c[c] = result["node_scores"]

    for i in range(3):
        print(
            f"  {i}   | {results_by_c[0.1][i]:.3f}  | {results_by_c[0.5][i]:.3f}  "
            f"| {results_by_c[1.0][i]:.3f}  | {results_by_c[2.0][i]:.3f}"
        )

    print("\nInterpretation: Higher coupling = stronger cross-layer influence.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MultiRank and Multiplex PageRank Examples")
    print("=" * 70)

    example_multirank()
    example_multiplex_pagerank_variants()
    example_comparison()
    example_coupling_strength()

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
