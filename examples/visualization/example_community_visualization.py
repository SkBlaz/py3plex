"""
Visualization Example: Community Structure Visualization

This example demonstrates how to:
1. Load a network with ground truth community labels
2. Color nodes by their community membership
3. Visualize the network to show community structure

This is useful for:
- Validating community detection algorithms
- Understanding network modularity
- Presenting community structure in publications
"""

import os
from py3plex.core import multinet
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from collections import Counter
from py3plex.utils import get_dataset_path

print("=" * 70)
print("COMMUNITY STRUCTURE VISUALIZATION")
print("=" * 70)

# Define file paths
network_file = get_dataset_path("network.dat")
community_file = get_dataset_path("community.dat")

# Check if files exist
if not os.path.exists(network_file):
    print(f"Error: Network file '{network_file}' not found.")
    print("This example requires the network dataset.")
    exit(1)

if not os.path.exists(community_file):
    print(f"Error: Community file '{community_file}' not found.")
    print("This example requires ground truth community labels.")
    exit(1)

print(f"\nLoading network from: {network_file}")
# Load the network from edgelist format
network = multinet.multi_layer_network().load_network(
    input_file=network_file,
    directed=False,
    input_type="edgelist"
)

print("Network loaded successfully!")
print("\nBasic network statistics:")
print("-" * 70)
network.basic_stats()

print(f"\nLoading ground truth communities from: {community_file}")
# Load pre-defined community assignments
# File format: typically node_id community_id per line
network.read_ground_truth_communities(community_file)

print("Communities loaded successfully!")

# Get the community partition
partition = network.ground_truth_communities

# Analyze community distribution
community_sizes = Counter(partition.values())
print(f"\nCommunity statistics:")
print(f"  Total communities: {len(community_sizes)}")
print(f"  Largest community: {max(community_sizes.values())} nodes")
print(f"  Smallest community: {min(community_sizes.values())} nodes")
print(f"  Average community size: {sum(community_sizes.values()) / len(community_sizes):.1f} nodes")

# Select top N communities to visualize
# (Too many colors can be hard to distinguish)
top_n = 100
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

print(f"\nVisualizing top {min(top_n, len(partition_counts))} communities by size")

# Create color mapping for communities
# Each community gets a unique color from the default palette
color_mappings = dict(
    zip(top_n_communities,
        [x for x in colors_default if x != "black"][0:top_n])
)

# Assign colors to nodes based on their community
# Nodes in smaller communities are colored black
network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

print("\nGenerating visualization...")
print("(Close the window to exit)")
print("-" * 70)

# Visualize the network with community colors
hairball_plot(
    network.core_network,
    color_list=network_colors,
    layout_parameters={"iterations": 100},  # Force-directed layout iterations
    scale_by_size=True,    # Scale node size by degree
    layout_algorithm="force",  # Use force-directed layout
    legend=False           # Don't show legend (too many communities)
)

print("\nVisualization parameters:")
print("  Layout: Force-directed (100 iterations)")
print("  Node size: Scaled by degree")
print("  Node color: Community membership")
print("  Black nodes: Small communities (not in top N)")

plt.show()

print("\n" + "=" * 70)
print("Visualization complete!")
print("=" * 70)
