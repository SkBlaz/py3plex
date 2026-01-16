"""SBM: Basic stochastic block model with fixed K.

This example demonstrates the simplest usage of the native SBM
implementation: fitting a model with a fixed number of blocks.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import sbm_fit
import numpy as np

# Create a synthetic network with block structure
np.random.seed(42)
net = multinet.multi_layer_network(directed=False)

# Add nodes (3 blocks, 10 nodes each)
nodes = [f'N{i}' for i in range(30)]
for node in nodes:
    net.add_node(node, layer='social')

# Generate edges with block structure
# Block 0: nodes 0-9, Block 1: nodes 10-19, Block 2: nodes 20-29
for i in range(30):
    for j in range(i+1, 30):
        # Within-block: high probability
        same_block = (i // 10) == (j // 10)
        p = 0.4 if same_block else 0.05
        
        if np.random.rand() < p:
            net.add_edge(nodes[i], nodes[j], layer_src='social', layer_dst='social')

# Fit SBM with K=3
print("Fitting SBM with K=3 blocks...")
partition = sbm_fit(
    net,
    n_blocks=3,
    algorithm="dc_sbm",  # Degree-corrected SBM
    seed=42
)

# Analyze results
communities = set(partition.values())
print(f"Number of communities found: {len(communities)}")

# Count members per community
from collections import Counter
comm_sizes = Counter(partition.values())
print(f"Community sizes: {dict(sorted(comm_sizes.items()))}")

# Check block recovery (nodes 0-9 should be in same community, etc.)
first_block_communities = {partition[(f'N{i}', 'social')] for i in range(10)}
second_block_communities = {partition[(f'N{i}', 'social')] for i in range(10, 20)}
third_block_communities = {partition[(f'N{i}', 'social')] for i in range(20, 30)}

print(f"First block purity: {1 if len(first_block_communities) == 1 else 'Mixed'}")
print(f"Second block purity: {1 if len(second_block_communities) == 1 else 'Mixed'}")
print(f"Third block purity: {1 if len(third_block_communities) == 1 else 'Mixed'}")
