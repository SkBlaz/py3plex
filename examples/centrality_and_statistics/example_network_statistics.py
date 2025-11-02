"""
Statistics Example: Computing Network Statistics and Identifying Hubs

This example demonstrates how to:
1. Load a network
2. Generate a quick network summary
3. Compute comprehensive network statistics
4. Identify hub nodes (highly connected nodes)

Network statistics help understand:
- Overall network structure and connectivity
- Scale and density of the network
- Important nodes (hubs) that connect many others
- Topological properties for comparison with other networks
"""

import os
from py3plex.core import multinet
from py3plex.utils import get_dataset_path
from py3plex.algorithms.statistics.basic_statistics import (
    core_network_statistics,
    identify_n_hubs
)

print("=" * 70)
print("NETWORK STATISTICS AND HUB IDENTIFICATION")
print("=" * 70)

# Define dataset path
dataset_path = get_dataset_path("imdb_gml.gml")

# Check if file exists
if not os.path.exists(dataset_path):
    print(f"Error: Dataset file '{dataset_path}' not found.")
    print("This example requires the IMDB network dataset.")
    exit(1)

print(f"\nLoading network from: {dataset_path}")

# Load the network
multilayer_network = multinet.multi_layer_network().load_network(
    dataset_path,
    directed=True,
    input_type="gml"
)

print("✓ Network loaded successfully!")

print("\n" + "=" * 70)
print("QUICK NETWORK SUMMARY")
print("=" * 70)

# Get a quick text summary of the network
# This provides a high-level overview of the network structure
summary = multilayer_network.summary()
print(summary)

print("\n" + "=" * 70)
print("DETAILED NETWORK STATISTICS")
print("=" * 70)

# Compute comprehensive network statistics
# This includes:
# - Number of nodes and edges
# - Network density (how connected it is)
# - Average degree (average connections per node)
# - Clustering coefficient (tendency to form triangles)
# - Connected components
# - Diameter and radius
# - And more...

print("\nComputing core network statistics...")
stats_frame = core_network_statistics(multilayer_network.core_network)

print("\nStatistics:")
print("-" * 70)

# Display statistics in a readable format
if isinstance(stats_frame, dict):
    for key, value in stats_frame.items():
        # Format numeric values for readability
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
else:
    print(stats_frame)

print("\n" + "=" * 70)
print("HUB IDENTIFICATION")
print("=" * 70)

# Identify top N nodes by degree (number of connections)
# Hub nodes are highly connected and often play important roles:
# - Information brokers
# - Critical connectors
# - Influential nodes
# - Potential points of failure

n_hubs = 20
print(f"\nIdentifying top {n_hubs} hub nodes by degree...")

top_hubs = identify_n_hubs(multilayer_network.core_network, n_hubs)

print(f"\nTop {n_hubs} hubs (node, degree):")
print("-" * 70)

# Display hub nodes with their degrees
if isinstance(top_hubs, list):
    for rank, (node, degree) in enumerate(top_hubs, 1):
        print(f"  {rank:2d}. Node {node}: {degree} connections")
elif isinstance(top_hubs, dict):
    sorted_hubs = sorted(top_hubs.items(), key=lambda x: x[1], reverse=True)
    for rank, (node, degree) in enumerate(sorted_hubs[:n_hubs], 1):
        print(f"  {rank:2d}. Node {node}: {degree} connections")
else:
    print(top_hubs)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print("\nKey Insights:")
print("  - Network statistics reveal overall structure and connectivity patterns")
print("  - Hub nodes are critical for network function and resilience")
print("  - High degree nodes often bridge different communities")
print("  - Statistics enable comparison with random or theoretical models")

print("\nNext Steps:")
print("  - Compare with random networks of similar size")
print("  - Analyze hub node roles in the network context")
print("  - Investigate communities around hub nodes")
print("  - Study resilience by simulating hub removal")
