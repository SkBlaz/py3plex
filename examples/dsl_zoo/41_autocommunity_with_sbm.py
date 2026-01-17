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

# Generate with clear SBM structure
block_assignments = np.array([i // 10 for i in range(40)])  # 4 blocks

B = np.array([
    [0.6, 0.1, 0.05, 0.05],
    [0.1, 0.6, 0.05, 0.05],
    [0.05, 0.05, 0.6, 0.1],
    [0.05, 0.05, 0.1, 0.6]
])

edges = []
for i in range(40):
    for j in range(i+1, 40):
        p = B[block_assignments[i], block_assignments[j]]
        
        if np.random.rand() < p:
            edges.append({
                'source': nodes[i],
                'target': nodes[j],
                'source_type': 'network',
                'target_type': 'network'
            })

if edges:
    net.add_edges(edges)

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
if hasattr(result, 'leaderboard') and result.leaderboard is not None:
    print("\nLeaderboard (top 5):")
    leaderboard_df = result.leaderboard.head()
    # Print all available columns
    print(leaderboard_df.to_string(index=False))
    
    # Check if SBM variants were included
    if 'contestant_id' in leaderboard_df.columns:
        sbm_rows = leaderboard_df[leaderboard_df['contestant_id'].str.contains('sbm', case=False)]
        if len(sbm_rows) > 0:
            print(f"\nSBM variants evaluated: {len(sbm_rows)}")
        else:
            print("\n(SBM may not have been included due to fast=True limiting candidates)")
else:
    print("\nNote: Leaderboard not available in this mode")

# Show community statistics
from collections import Counter
comm_sizes = Counter(result.partition.values())
print(f"\nCommunity sizes: {dict(sorted(comm_sizes.items()))}")

# If winner is SBM, show additional info
if 'sbm' in result.algorithm['name'].lower():
    print("\nSBM was selected as the best algorithm.")
    if 'mode' in result.algorithm.get('params', {}):
        print(f"   Mode: {result.algorithm['params']['mode']}")
    if 'n_blocks' in result.algorithm.get('params', {}):
        print(f"   Blocks: {result.algorithm['params']['n_blocks']}")
