"""Multilayer SBM: Shared memberships across layers.

This example shows how to fit SBM to multilayer networks with
shared block memberships but different connection patterns per layer.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import sbm_fit
import numpy as np

# Create multilayer network with shared community structure
np.random.seed(45)
net = multinet.multi_layer_network(directed=False)

nodes = [f'N{i}' for i in range(30)]
n_nodes = 30
n_layers = 3
layers = ['social', 'professional', 'hobby']

# Shared block assignments (same across layers)
block_assignments = np.array([i // 10 for i in range(n_nodes)])  # 3 blocks of 10

# Different connection patterns per layer
B_matrices = {
    'social': np.array([
        [0.5, 0.1, 0.05],
        [0.1, 0.4, 0.1],
        [0.05, 0.1, 0.5]
    ]),
    'professional': np.array([
        [0.4, 0.2, 0.1],
        [0.2, 0.5, 0.15],
        [0.1, 0.15, 0.4]
    ]),
    'hobby': np.array([
        [0.6, 0.05, 0.2],
        [0.05, 0.5, 0.05],
        [0.2, 0.05, 0.6]
    ])
}

# Generate edges for each layer
edges = []
for layer in layers:
    B = B_matrices[layer]
    for i in range(n_nodes):
        for j in range(i+1, n_nodes):
            p = B[block_assignments[i], block_assignments[j]]
            
            if np.random.rand() < p:
                edges.append({
                    'source': nodes[i],
                    'target': nodes[j],
                    'source_type': layer,
                    'target_type': layer
                })

if edges:
    net.add_edges(edges)

# Fit multilayer SBM with shared memberships
print("Fitting multilayer SBM with shared memberships...")
partition, model = sbm_fit(
    net,
    n_blocks=3,
    mode="shared_blocks",  # Shared memberships, separate B per layer
    algorithm="dc_sbm",
    return_model=True,
    seed=45
)

# Check that memberships are shared across layers
print(f"\nModel layer mode: {model.layer_mode_}")
print(f"Number of B matrices: {len(model.block_affinity_)}")
print(f"Communities found: {len(set(partition.values()))}")

# Check recovery for each layer
from collections import Counter
for layer in layers:
    layer_partition = {k[0]: v for k, v in partition.items() if k[1] == layer}
    comm_sizes = Counter(layer_partition.values())
    print(f"\n{layer} layer:")
    print(f"  Community sizes: {dict(sorted(comm_sizes.items()))}")

# Show B matrices vary by layer
print("\nBlock affinity matrices (first 2x2 submatrix):")
for i, layer in enumerate(layers):
    if i < len(model.block_affinity_):
        B = model.block_affinity_[i]
        print(f"\n{layer}:")
        print(f"  [[{B[0,0]:.3f}, {B[0,1]:.3f}]")
        print(f"   [{B[1,0]:.3f}, {B[1,1]:.3f}]]")
