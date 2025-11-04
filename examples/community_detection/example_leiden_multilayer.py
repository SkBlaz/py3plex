#!/usr/bin/env python3
"""
Example: Leiden community detection for multilayer networks.

This example demonstrates how to use the Leiden algorithm for detecting
communities in multilayer networks using py3plex.

SKIP_CI: external_deps - Requires leidenalg package
"""

import sys
sys.path.insert(0, '../../')

from py3plex.core import multinet, random_generators
from py3plex.algorithms.community_detection import leiden_multilayer

print("=" * 70)
print("Leiden Multilayer Community Detection Example")
print("=" * 70)

# Example 1: Simple multilayer network
print("\n### Example 1: Simple 2-layer network ###\n")

network1 = multinet.multi_layer_network(directed=False)

# Layer 1: Triangle
network1.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['C', 'L1', 'A', 'L1', 1]
], input_type='list')

# Layer 2: Line
network1.add_edges([
    ['A', 'L2', 'B', 'L2', 1],
    ['B', 'L2', 'C', 'L2', 1]
], input_type='list')

print("Running Leiden algorithm...")
result1 = leiden_multilayer(
    network1,
    interlayer_coupling=0.5,
    resolution=1.0,
    seed=42,
    max_iter=100
)

print(result1.summary())
print("\nCommunity assignments:")
for (node, layer), community in sorted(result1.communities.items()):
    print(f"  Node {node} in layer {layer}: Community {community}")


# Example 2: Random multilayer ER network
print("\n\n### Example 2: Random multilayer Erdős-Rényi network ###\n")

# Generate a random multilayer network
network2 = random_generators.random_multilayer_ER(
    n=20,
    l=3,
    p=0.15,
    directed=False
)

print(f"Network has {len(list(network2.get_nodes()))} node-layer pairs")

print("\nRunning Leiden with default parameters...")
result2 = leiden_multilayer(
    network2,
    interlayer_coupling=1.0,
    resolution=1.0,
    seed=42
)

print(result2.summary())

# Show community distribution
community_sizes = {}
for com in result2.communities.values():
    community_sizes[com] = community_sizes.get(com, 0) + 1

print("\nCommunity size distribution:")
for com, size in sorted(community_sizes.items()):
    print(f"  Community {com}: {size} node-layer pairs")


# Example 3: Different resolution parameters per layer
print("\n\n### Example 3: Layer-specific resolution parameters ###\n")

network3 = multinet.multi_layer_network(directed=False)

# Create two communities in layer 1
for i in range(4):
    for j in range(i + 1, 4):
        network3.add_edge(i, 'L1', j, 'L1', 1)

for i in range(4, 8):
    for j in range(i + 1, 8):
        network3.add_edge(i, 'L1', j, 'L1', 1)

# Sparse layer 2
for i in range(0, 7, 2):
    network3.add_edge(i, 'L2', i + 1, 'L2', 1)

print("Testing different resolution settings...")

# High resolution in L1, low in L2
result3a = leiden_multilayer(
    network3,
    interlayer_coupling=0.5,
    resolution={'L1': 1.5, 'L2': 0.5},
    seed=42
)

print("\nWith γ_L1=1.5, γ_L2=0.5:")
print(f"  Modularity: {result3a.modularity:.4f}")
print(f"  Communities: {len(set(result3a.communities.values()))}")

# Equal resolution
result3b = leiden_multilayer(
    network3,
    interlayer_coupling=0.5,
    resolution=1.0,
    seed=42
)

print("\nWith γ=1.0 (all layers):")
print(f"  Modularity: {result3b.modularity:.4f}")
print(f"  Communities: {len(set(result3b.communities.values()))}")


# Example 4: Different coupling strengths
print("\n\n### Example 4: Effect of interlayer coupling ###\n")

network4 = multinet.multi_layer_network(directed=False)

# Create similar structure in both layers
for layer in ['L1', 'L2']:
    for i in range(3):
        for j in range(i + 1, 3):
            network4.add_edge(i, layer, j, layer, 1)
    
    for i in range(3, 6):
        for j in range(i + 1, 6):
            network4.add_edge(i, layer, j, layer, 1)

print("Testing different coupling strengths...")

# No coupling
result4a = leiden_multilayer(
    network4,
    interlayer_coupling=0.0,
    resolution=1.0,
    seed=42
)

print("\nWith ω=0.0 (no coupling):")
print(f"  Modularity: {result4a.modularity:.4f}")
print(f"  Communities: {len(set(result4a.communities.values()))}")

# Strong coupling
result4b = leiden_multilayer(
    network4,
    interlayer_coupling=2.0,
    resolution=1.0,
    seed=42
)

print("\nWith ω=2.0 (strong coupling):")
print(f"  Modularity: {result4b.modularity:.4f}")
print(f"  Communities: {len(set(result4b.communities.values()))}")

# Check community alignment across layers
aligned_count = 0
total_count = 0
for node in range(6):
    if (node, 'L1') in result4b.communities and (node, 'L2') in result4b.communities:
        if result4b.communities[(node, 'L1')] == result4b.communities[(node, 'L2')]:
            aligned_count += 1
        total_count += 1

print(f"  Cross-layer alignment: {aligned_count}/{total_count} nodes in same community")


print("\n" + "=" * 70)
print("Examples completed!")
print("=" * 70)
