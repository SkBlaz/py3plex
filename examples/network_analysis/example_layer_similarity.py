"""
Example demonstrating layer similarity metrics.

This example shows how to compute similarity between layers using
Jaccard similarity, spectral similarity, and correlation matrices.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.layer_similarity import (
    jaccard_layer_similarity,
    layer_correlation_matrix,
)


def main():
    """Demonstrate layer similarity metrics."""
    print("=== Layer Similarity Demo ===\n")

    # Create network with multiple layers
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'L1'},
        {'source': 'B', 'type': 'L1'},
        {'source': 'C', 'type': 'L1'},
        {'source': 'A', 'type': 'L2'},
        {'source': 'B', 'type': 'L2'},
        {'source': 'C', 'type': 'L2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
    ])

    print(f"Network: 2 layers (L1, L2) with shared nodes\n")

    # Compute Jaccard similarity
    try:
        # Node overlap similarity
        sim_nodes = jaccard_layer_similarity(net, 'L1', 'L2', element='nodes')
        print(f"Jaccard node similarity (L1, L2): {sim_nodes:.4f}")

        # Edge overlap similarity
        sim_edges = jaccard_layer_similarity(net, 'L1', 'L2', element='edges')
        print(f"Jaccard edge similarity (L1, L2): {sim_edges:.4f}")

        # Compute full correlation matrix
        print("\nComputing layer correlation matrix...")
        sim_matrix, layers = layer_correlation_matrix(net, method='jaccard')
        print(f"Matrix shape: {sim_matrix.shape}")
        print(f"Layers: {layers}")
        print("\nCorrelation matrix:")
        print(sim_matrix)

        print("\nUse cases:")
        print("  - Identify redundant layers")
        print("  - Detect layer communities")
        print("  - Guide layer compression strategies\n")

    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
