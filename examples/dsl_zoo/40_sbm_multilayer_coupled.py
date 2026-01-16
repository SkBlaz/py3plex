"""Coupled Multilayer SBM: Encouraging consistency across layers.

This example demonstrates the "coupled" mode which applies a coupling
penalty to encourage similar block affinity matrices across layers.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import sbm_fit
import numpy as np

# Create multilayer network with highly similar structure across layers
np.random.seed(46)
net = multinet.multi_layer_network(directed=False)

nodes = [f'N{i}' for i in range(30)]
n_nodes = 30
layers = ['layer1', 'layer2', 'layer3']

# Shared block assignments
block_assignments = np.array([i // 15 for i in range(n_nodes)])  # 2 blocks of 15

# Very similar B matrices (with small noise)
base_B = np.array([
    [0.5, 0.1],
    [0.1, 0.5]
])

# Generate edges for each layer
for layer in layers:
    for node in nodes:
        net.add_node(node, layer=layer)
    
    # Add small layer-specific noise
    noise = np.random.randn(2, 2) * 0.05
    B = np.clip(base_B + noise, 0.01, 0.99)
    B = (B + B.T) / 2  # Symmetrize
    
    for i in range(n_nodes):
        for j in range(i+1, n_nodes):
            p = B[block_assignments[i], block_assignments[j]]
            
            if np.random.rand() < p:
                net.add_edge(nodes[i], nodes[j], layer_src=layer, layer_dst=layer)

# Fit with independent mode (baseline)
print("Fitting independent SBM (no coupling)...")
partition_ind, model_ind = sbm_fit(
    net,
    n_blocks=2,
    mode="independent",  # No coupling
    algorithm="dc_sbm",
    return_model=True,
    seed=46,
    verbose=False
)

# Fit with coupled mode
print("Fitting coupled SBM (with coupling penalty)...")
partition_coupled, model_coupled = sbm_fit(
    net,
    n_blocks=2,
    mode="coupled",  # Coupling penalty encourages similar B matrices
    algorithm="dc_sbm",
    return_model=True,
    seed=46,
    verbose=False
)

# Compare similarity of B matrices
def frobenius_similarity(B_list):
    """Compute average pairwise Frobenius distance."""
    distances = []
    for i in range(len(B_list)):
        for j in range(i+1, len(B_list)):
            dist = np.linalg.norm(B_list[i] - B_list[j], 'fro')
            distances.append(dist)
    return np.mean(distances) if distances else 0.0

B_ind = model_ind.block_affinity_
B_coupled = model_coupled.block_affinity_

print(f"\nIndependent mode:")
print(f"  Average B matrix distance: {frobenius_similarity(B_ind):.4f}")

print(f"\nCoupled mode:")
print(f"  Average B matrix distance: {frobenius_similarity(B_coupled):.4f}")

print("\nCoupled mode should have smaller distance (more similar B matrices)")

# Show actual B matrices
print("\nBlock affinity matrices (coupled mode):")
for i, layer in enumerate(layers):
    B = B_coupled[i]
    print(f"\n{layer}:")
    print(f"  [[{B[0,0]:.3f}, {B[0,1]:.3f}]")
    print(f"   [{B[1,0]:.3f}, {B[1,1]:.3f}]]")
