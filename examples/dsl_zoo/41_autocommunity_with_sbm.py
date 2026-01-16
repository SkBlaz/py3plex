"""AutoCommunity with SBM: Algorithm selection including SBM variants.

This example shows how SBM integrates with AutoCommunity to be
automatically selected alongside other algorithms like Leiden and Louvain.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import auto_select_community
import numpy as np

# Create network with clear block structure (SBM-friendly)
np.random.seed(47)
net = multinet.multi_layer_network(directed=False)

nodes = [f'N{i}' for i in range(40)]
for node in nodes:
    net.add_node(node, layer='network')

# Generate with clear SBM structure
block_assignments = np.array([i // 10 for i in range(40)])  # 4 blocks

B = np.array([
    [0.6, 0.1, 0.05, 0.05],
    [0.1, 0.6, 0.05, 0.05],
    [0.05, 0.05, 0.6, 0.1],
    [0.05, 0.05, 0.1, 0.6]
])

for i in range(40):
    for j in range(i+1, 40):
        p = B[block_assignments[i], block_assignments[j]]
        
        if np.random.rand() < p:
            net.add_edge(nodes[i], nodes[j], layer_src='network', layer_dst='network')

# Run AutoCommunity - will evaluate SBM alongside other algorithms
print("Running AutoCommunity with SBM as candidate...")
print("(This may take a moment as multiple algorithms are evaluated)\n")

result = auto_select_community(
    net,
    mode="wins",  # Use legacy wins mode for simpler demonstration
    fast=True,  # Use fast mode with smaller parameter grids
    seed=47,
    max_candidates=5  # Limit candidates for speed
)

# Show results
print(f"\nWinning algorithm: {result.algorithm['name']}")
print(f"Parameters: {result.algorithm.get('params', {})}")
print(f"Number of communities: {len(set(result.partition.values()))}")

# Check if SBM was evaluated
if hasattr(result, 'leaderboard'):
    print("\nLeaderboard (top 5):")
    leaderboard_df = result.leaderboard.head()
    print(leaderboard_df[['contestant_id', 'wins', 'avg_score']].to_string(index=False))
    
    # Check if SBM variants were included
    sbm_rows = leaderboard_df[leaderboard_df['contestant_id'].str.contains('sbm', case=False)]
    if len(sbm_rows) > 0:
        print(f"\nSBM variants evaluated: {len(sbm_rows)}")
        print(sbm_rows[['contestant_id', 'wins']].to_string(index=False))
    else:
        print("\n(SBM may not have been included due to fast=True limiting candidates)")

# Show community statistics
from collections import Counter
comm_sizes = Counter(result.partition.values())
print(f"\nCommunity sizes: {dict(sorted(comm_sizes.items()))}")

# If winner is SBM, show additional info
if 'sbm' in result.algorithm['name'].lower():
    print("\n🎉 SBM was selected as the best algorithm!")
    if 'mode' in result.algorithm.get('params', {}):
        print(f"   Mode: {result.algorithm['params']['mode']}")
    if 'n_blocks' in result.algorithm.get('params', {}):
        print(f"   Blocks: {result.algorithm['params']['n_blocks']}")
