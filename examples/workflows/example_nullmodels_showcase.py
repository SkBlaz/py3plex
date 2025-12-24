#!/usr/bin/env python
"""
Null Models Showcase: All Available Models
===========================================

This example demonstrates all null model types available in py3plex:

1. Configuration model - Preserves degree sequence
2. Erdős-Rényi model - Random graph with fixed edge probability
3. Layer shuffle model - Randomizes layer assignments
4. Edge swap model - Rewires edges while preserving degree

Each model is useful for testing different null hypotheses about
network structure.

Runtime: FAST (<10 seconds) - suitable for CI
Dependencies: py3plex only
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from py3plex.core import multinet
from py3plex.nullmodels import (
    configuration_model,
    erdos_renyi_model,
    layer_shuffle_model,
    edge_swap_model,
    generate_null_model,
)


def create_test_network() -> multinet.multi_layer_network:
    """Create a simple multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    edges = [
        # Layer A: Triangle
        ["n1", "A", "n2", "A", 1.0],
        ["n2", "A", "n3", "A", 1.0],
        ["n3", "A", "n1", "A", 1.0],
        
        # Layer B: Star
        ["n1", "B", "n2", "B", 1.0],
        ["n1", "B", "n3", "B", 1.0],
        ["n1", "B", "n4", "B", 1.0],
        
        # Inter-layer
        ["n1", "A", "n1", "B", 1.0],
        ["n2", "A", "n2", "B", 1.0],
        ["n3", "A", "n3", "B", 1.0],
    ]
    
    net.add_edges(edges, input_type="list")
    return net


def demonstrate_configuration_model(net: multinet.multi_layer_network) -> None:
    """Demo: Configuration model preserves degree distribution."""
    print("\n" + "=" * 70)
    print("1. Configuration Model")
    print("=" * 70)
    print("\nPreserves: Degree sequence of each node")
    print("Randomizes: Which nodes connect to each other")
    print("Use case: Test if observed patterns arise from degree distribution alone")
    
    # Generate null model
    null_net = configuration_model(net, preserve_layers=True)
    
    # Compare degrees
    orig_degrees = dict(net.core_network.degree())
    null_degrees = dict(null_net.core_network.degree())
    
    print("\nDegree comparison (original vs null):")
    print(f"{'Node':<8} {'Original':<10} {'Null':<10} {'Match':<8}")
    print("-" * 40)
    
    for node in sorted(orig_degrees.keys(), key=str)[:5]:
        orig = orig_degrees[node]
        null = null_degrees.get(node, 0)
        match = "✓" if orig == null else "✗"
        print(f"{str(node):<8} {orig:<10} {null:<10} {match:<8}")
    
    print(f"\nEdge count: {net.core_network.number_of_edges()} → "
          f"{null_net.core_network.number_of_edges()}")


def demonstrate_erdos_renyi_model(net: multinet.multi_layer_network) -> None:
    """Demo: Erdős-Rényi model with fixed edge probability."""
    print("\n" + "=" * 70)
    print("2. Erdős-Rényi Model")
    print("=" * 70)
    print("\nPreserves: Number of nodes")
    print("Randomizes: All connections (uniform probability)")
    print("Use case: Compare against completely random network baseline")
    
    # Calculate edge probability from original network
    n = net.core_network.number_of_nodes()
    m = net.core_network.number_of_edges()
    p = 2 * m / (n * (n - 1)) if n > 1 else 0
    
    print(f"\nOriginal network:")
    print(f"  Nodes: {n}")
    print(f"  Edges: {m}")
    print(f"  Implied probability: {p:.3f}")
    
    # Generate null model
    null_net = erdos_renyi_model(net, p=p, preserve_layers=False)
    
    print(f"\nGenerated Erdős-Rényi network:")
    print(f"  Nodes: {null_net.core_network.number_of_nodes()}")
    print(f"  Edges: {null_net.core_network.number_of_edges()}")
    print(f"  Density: {2 * null_net.core_network.number_of_edges() / (n * (n - 1)) if n > 1 else 0:.3f}")


def demonstrate_layer_shuffle_model(net: multinet.multi_layer_network) -> None:
    """Demo: Layer shuffle randomizes layer assignments."""
    print("\n" + "=" * 70)
    print("3. Layer Shuffle Model")
    print("=" * 70)
    print("\nPreserves: Node connections")
    print("Randomizes: Which layer each edge belongs to")
    print("Use case: Test if layer structure matters or is arbitrary")
    
    # Get layer distribution before
    from collections import Counter
    orig_layers = []
    for u, v, data in net.core_network.edges(data=True):
        layer = data.get('type', 'unknown')
        orig_layers.append(layer)
    
    orig_dist = Counter(orig_layers)
    
    print(f"\nOriginal layer distribution:")
    for layer, count in sorted(orig_dist.items()):
        print(f"  {layer}: {count} edges")
    
    # Generate null model
    null_net = layer_shuffle_model(net)
    
    # Get layer distribution after
    null_layers = []
    for u, v, data in null_net.core_network.edges(data=True):
        layer = data.get('type', 'unknown')
        null_layers.append(layer)
    
    null_dist = Counter(null_layers)
    
    print(f"\nShuffled layer distribution:")
    for layer, count in sorted(null_dist.items()):
        print(f"  {layer}: {count} edges")
    
    print(f"\nNote: Edge count preserved, layer assignments randomized")


def demonstrate_edge_swap_model(net: multinet.multi_layer_network) -> None:
    """Demo: Edge swap model preserves degrees through edge rewiring."""
    print("\n" + "=" * 70)
    print("4. Edge Swap Model")
    print("=" * 70)
    print("\nPreserves: Degree sequence (via edge swaps)")
    print("Randomizes: Network structure through rewiring")
    print("Use case: Similar to configuration model, but via edge swapping")
    
    # Get original properties
    orig_degrees = dict(net.core_network.degree())
    orig_n_edges = net.core_network.number_of_edges()
    
    # Generate null model
    null_net = edge_swap_model(net, n_swaps=20, preserve_layers=True)
    
    # Get null properties
    null_degrees = dict(null_net.core_network.degree())
    null_n_edges = null_net.core_network.number_of_edges()
    
    print(f"\nNetwork properties comparison:")
    print(f"  Edges: {orig_n_edges} → {null_n_edges}")
    print(f"  Degree preserved: ", end="")
    
    degrees_match = all(orig_degrees.get(n) == null_degrees.get(n) 
                       for n in orig_degrees)
    print("✓" if degrees_match else "✗")
    
    # Check if structure changed
    orig_edges = set(net.core_network.edges())
    null_edges = set(null_net.core_network.edges())
    
    same_edges = len(orig_edges & null_edges)
    total_edges = len(orig_edges)
    
    print(f"\nEdges changed: {total_edges - same_edges}/{total_edges} "
          f"({100 * (total_edges - same_edges) / total_edges:.1f}%)")


def demonstrate_batch_generation() -> None:
    """Demo: Generate multiple null model samples efficiently."""
    print("\n" + "=" * 70)
    print("5. Batch Generation")
    print("=" * 70)
    print("\nFor statistical tests, you typically need many null samples.")
    print("The generate_null_model() function handles this efficiently.\n")
    
    net = create_test_network()
    
    print("Generating 50 null model samples...")
    result = generate_null_model(
        net,
        model="configuration",
        num_samples=50,
        preserve_layers=True
    )
    
    print(f"\nGenerated {len(result.samples)} samples")
    print(f"Model: {result.model_type}")
    print(f"Meta: {result.meta}")
    
    # Compute statistics across samples
    edge_counts = [sample.core_network.number_of_edges() 
                   for sample in result.samples]
    
    print(f"\nEdge count distribution across samples:")
    print(f"  Mean: {np.mean(edge_counts):.1f}")
    print(f"  Std: {np.std(edge_counts):.2f}")
    print(f"  Range: [{min(edge_counts)}, {max(edge_counts)}]")
    print(f"\nOriginal network: {net.core_network.number_of_edges()} edges")


def main() -> int:
    """Run all null model demonstrations."""
    np.random.seed(42)
    
    print("\n" + "#" * 70)
    print("# Null Models Showcase: Complete Guide")
    print("#" * 70)
    print("\npy3plex provides 4 null model types for hypothesis testing:")
    print("  1. Configuration model - Preserves degree distribution")
    print("  2. Erdős-Rényi model - Uniform random connections")
    print("  3. Layer shuffle model - Randomizes layer assignments")
    print("  4. Edge swap model - Degree-preserving rewiring")
    
    net = create_test_network()
    
    print(f"\nTest network: {net.core_network.number_of_nodes()} nodes, "
          f"{net.core_network.number_of_edges()} edges")
    
    # Demonstrate each model
    demonstrate_configuration_model(net)
    demonstrate_erdos_renyi_model(net)
    demonstrate_layer_shuffle_model(net)
    demonstrate_edge_swap_model(net)
    demonstrate_batch_generation()
    
    print("\n" + "#" * 70)
    print("# All null models demonstrated successfully!")
    print("#" * 70)
    print("\nWhen to use each model:")
    print("  • Configuration: Test if patterns arise from degree alone")
    print("  • Erdős-Rényi: Compare against uniform random baseline")
    print("  • Layer shuffle: Test if layer structure is meaningful")
    print("  • Edge swap: Alternative degree-preserving randomization")
    print("\nFor more details, see: py3plex.nullmodels documentation")
    print()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
