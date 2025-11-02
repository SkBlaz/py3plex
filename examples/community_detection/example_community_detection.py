"""
Community Detection Example: Louvain and Infomap Algorithms

This example demonstrates how to:
1. Load a network from a sparse matrix format
2. Apply the Louvain community detection algorithm
3. Visualize communities with distinct colors
4. (Optional) Apply the Infomap algorithm for comparison

Community detection identifies groups of densely connected nodes,
revealing the modular structure of networks.

Algorithms:
- Louvain: Fast, hierarchical, optimizes modularity (BSD-3 license)
- Infomap: Flow-based, optimizes information flow (requires binary)
"""

import os
import random
import numpy as np
from collections import Counter
import argparse

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.utils import get_dataset_path

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Community detection and visualization example"
)
parser.add_argument(
    "--input_network",
    default=get_dataset_path("cora.mat"),
    help="Path to input network file (default: datasets/cora.mat)"
)
parser.add_argument(
    "--input_type",
    default="sparse",
    help="Input format type (default: sparse)"
)
parser.add_argument(
    "--iterations",
    default=200,
    type=int,
    help="Number of layout iterations for visualization (default: 200)"
)
parser.add_argument(
    "--seed",
    default=42,
    type=int,
    help="Random seed for reproducibility (default: 42)"
)
args = parser.parse_args()

# Set random seeds for reproducible results
random.seed(args.seed)
np.random.seed(args.seed)

print("=" * 70)
print("COMMUNITY DETECTION AND VISUALIZATION")
print("=" * 70)

# Check if input file exists
if not os.path.exists(args.input_network):
    print(f"Error: Input file '{args.input_network}' not found.")
    print("Please specify a valid network file using --input_network")
    exit(1)

print(f"\nConfiguration:")
print(f"  Input file: {args.input_network}")
print(f"  Input type: {args.input_type}")
print(f"  Layout iterations: {args.iterations}")
print(f"  Random seed: {args.seed}")

print(f"\nLoading network from {args.input_network}...")
# Load the network
# The .mat file should contain network and group objects
network = multinet.multi_layer_network().load_network(
    input_file=args.input_network,
    directed=False,
    input_type=args.input_type
)

# Convert sparse matrix to py3plex format if needed
if args.input_type == 'sparse':
    print("Converting sparse matrix to px format...")
    # Adds dummy layers for single-layer networks
    network.sparse_to_px()

print("\nNetwork statistics:")
print("-" * 70)
network.basic_stats()

##############################################################################
# LOUVAIN ALGORITHM - Fast modularity optimization
##############################################################################

print("\n" + "=" * 70)
print("LOUVAIN COMMUNITY DETECTION")
print("=" * 70)
print("Running Louvain algorithm (optimizes network modularity)...")

# Apply Louvain community detection
# This is a fast, hierarchical algorithm that maximizes modularity
partition = cw.louvain_communities(network)

# Analyze detected communities
community_sizes = Counter(partition.values())
print(f"\nCommunity detection complete!")
print(f"  Total communities found: {len(community_sizes)}")
print(f"  Largest community: {max(community_sizes.values())} nodes")
print(f"  Smallest community: {min(community_sizes.values())} nodes")
print(f"  Average community size: {sum(community_sizes.values()) / len(community_sizes):.1f} nodes")

# Select top N communities by size for visualization
top_n = 10
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

print(f"\nVisualizing top {top_n} communities by size...")

# Create color mapping for communities
color_mappings = dict(
    zip(top_n_communities,
        [x for x in colors_default if x != "black"][0:top_n])
)

# Assign colors: top communities get distinct colors, others are black
network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

print("Generating Louvain visualization...")
print("(Close the window to continue)")

# Visualize the network with community colors
hairball_plot(
    network.core_network,
    color_list=network_colors,
    layout_parameters={"iterations": args.iterations},
    scale_by_size=True,      # Node size proportional to degree
    layout_algorithm="force",  # Force-directed layout
    legend=False              # Too many communities for legend
)
plt.show()

##############################################################################
# INFOMAP ALGORITHM (OPTIONAL) - Flow-based community detection
##############################################################################

print("\n" + "=" * 70)
print("INFOMAP COMMUNITY DETECTION (OPTIONAL)")
print("=" * 70)

print("""
Note: Infomap requires an external binary that is no longer bundled.

Options:
  1. Download from: https://www.mapequation.org/infomap/
  2. Install via: pip install infomap
  3. Use Louvain (above) as a Python-only alternative

Attempting to run Infomap...
""")

try:
    print("Running Infomap algorithm...")
    # Apply Infomap community detection
    # multiplex=False treats the network as a single layer
    partition = cw.infomap_communities(
        network,
        binary="./infomap",  # Assumes infomap is in PATH or current directory
        multiplex=False,
        verbose=True,
        seed=args.seed
    )
    
    # Analyze Infomap communities
    community_sizes = Counter(partition.values())
    print(f"\nInfomap detection complete!")
    print(f"  Total communities found: {len(community_sizes)}")
    
    # Select top N communities
    top_n = 5
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]
    
    # Create color mapping
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n])
    )
    
    # Assign colors
    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in network.get_nodes()
    ]
    
    print("Generating Infomap visualization...")
    print("(Close the window to exit)")
    
    # Visualize Infomap results
    hairball_plot(
        network.core_network,
        color_list=network_colors,
        layout_parameters={"iterations": args.iterations},
        scale_by_size=True,
        layout_algorithm="force",
        legend=False
    )
    plt.show()
    
except FileNotFoundError as e:
    print(f"✗ Infomap binary not found: {e}")
    print("  Using Louvain results from above instead.")
except Exception as e:
    print(f"✗ Error running Infomap: {e}")
    print("  Using Louvain results from above instead.")

##############################################################################
# OPTIONAL: SAVE NETWORK AS EDGELIST
##############################################################################

print("\n" + "=" * 70)
print("OPTIONAL: SAVING NETWORK AS EDGELIST")
print("=" * 70)

# Uncomment to save the network in edgelist format
# This is useful for importing into other tools
save_edgelist = False  # Set to True to enable

if save_edgelist:
    output_file = "tmp_network.txt"
    print(f"Saving network to: {output_file}")
    
    # Serialize to edgelist format
    # Returns inverse node mapping (numeric ID -> original name)
    inverse_node_map = network.serialize_to_edgelist(
        edgelist_file=output_file
    )
    
    print(f"✓ Network saved successfully!")
    print(f"  Node mapping saved in: network.node_map")
else:
    print("Edgelist export disabled (set save_edgelist=True to enable)")

print("\n" + "=" * 70)
print("COMMUNITY DETECTION COMPLETE")
print("=" * 70)

print("\nKey takeaways:")
print("  ✓ Louvain: Fast, Python-only, optimizes modularity")
print("  ✓ Infomap: Flow-based, requires binary, very accurate")
print("  ✓ Both reveal hierarchical community structure")
print("  ✓ Visualizations help validate detected communities")
