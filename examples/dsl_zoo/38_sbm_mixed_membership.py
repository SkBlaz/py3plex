"""MMSBM: Mixed-membership SBM with soft assignments.

This example demonstrates mixed-membership SBM where nodes can
belong to multiple communities with different probabilities.
"""

from py3plex.core import multinet
from py3plex.algorithms.sbm import mmsbm_fit
import numpy as np

# Create network with overlapping communities
np.random.seed(44)
net = multinet.multi_layer_network(directed=False)

nodes = [f'N{i}' for i in range(30)]
for node in nodes:
    net.add_node(node, layer='social')

# Create soft membership ground truth
# Most nodes belong primarily to one community
# But some nodes (10-14) belong to both communities 0 and 1
n_nodes = 30
K = 3
true_soft_membership = np.zeros((n_nodes, K))

for i in range(10):
    true_soft_membership[i, 0] = 0.9
    true_soft_membership[i, 1] = 0.05
    true_soft_membership[i, 2] = 0.05

for i in range(10, 15):
    # Overlapping nodes
    true_soft_membership[i, 0] = 0.45
    true_soft_membership[i, 1] = 0.45
    true_soft_membership[i, 2] = 0.10

for i in range(15, 25):
    true_soft_membership[i, 1] = 0.9
    true_soft_membership[i, 0] = 0.05
    true_soft_membership[i, 2] = 0.05

for i in range(25, 30):
    true_soft_membership[i, 2] = 0.9
    true_soft_membership[i, 0] = 0.05
    true_soft_membership[i, 1] = 0.05

# Generate edges based on soft memberships
B = np.array([
    [0.5, 0.1, 0.05],
    [0.1, 0.5, 0.05],
    [0.05, 0.05, 0.5]
])

for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        # Probability of edge based on soft memberships and B
        p = np.dot(true_soft_membership[i], np.dot(B, true_soft_membership[j]))
        
        if np.random.rand() < p:
            net.add_edge(nodes[i], nodes[j], layer_src='social', layer_dst='social')

# Fit MMSBM
print("Fitting mixed-membership SBM...")
model = mmsbm_fit(net, n_blocks=3, model="dc_sbm", seed=44, n_init=3)

# Access soft memberships
soft_memberships = model.memberships_
print(f"\nSoft membership matrix shape: {soft_memberships.shape}")

# Show membership probabilities for overlapping nodes (10-14)
print("\nMembership probabilities for overlapping nodes (10-14):")
for i in range(10, 15):
    probs = soft_memberships[i]
    print(f"  Node N{i}: [{probs[0]:.3f}, {probs[1]:.3f}, {probs[2]:.3f}]")

# Compare with hard partition
partition = model.to_partition_vector()
print(f"\nHard partition (argmax):")
for i in range(10, 15):
    print(f"  Node N{i}: Community {partition[f'N{i}']}")

# Show entropy (uncertainty) for each node
if hasattr(model, 'uncertainty_'):
    entropy = model.uncertainty_['node_entropy']
    print(f"\nNode entropy (uncertainty):")
    print(f"  Mean entropy: {entropy.mean():.3f}")
    print(f"  Max entropy: {entropy.max():.3f} (node {np.argmax(entropy)})")
    print(f"  Min entropy: {entropy.min():.3f} (node {np.argmin(entropy)})")
