"""
Basic Example: Layer Extraction and Analysis

This example demonstrates how to:
1. Load a multilayer network
2. Extract individual layers from the network
3. Compute and display statistics for each layer

Layer extraction is useful for:
- Analyzing individual network aspects separately
- Comparing properties across layers
- Understanding layer-specific characteristics

SKIP_CI: external_deps - Requires specific dataset files
"""

import os
from py3plex.core import multinet
from py3plex.algorithms.statistics.basic_statistics import core_network_statistics
from py3plex.utils import get_dataset_path

# Path to the dataset
dataset_path = get_dataset_path("epigenetics.gpickle")

# Check if the dataset exists
if not os.path.exists(dataset_path):
    print(f"Warning: Dataset file '{dataset_path}' not found.")
    print("This example requires the epigenetics dataset.")
    print("Please ensure the file exists before running this example.")
    exit(1)

print("Loading multilayer network...")
# Load the network from gpickle_biomine format
# This format is specific to biological/biomine networks
multilayer_network = multinet.multi_layer_network().load_network(
    dataset_path,
    directed=False,
    input_type="gpickle_biomine"
)

print("Network loaded successfully!")
print("\nExtracting individual layers...")

# Extract layers from the multilayer network
# Returns: layer names, network objects, and multiedge lists
names, networks, multiedges = multilayer_network.get_layers()

print(f"Extracted {len(names)} layers from the network")
print("\nAnalyzing statistics for each layer:")
print("=" * 70)

# Compute and display statistics for each extracted layer
for name, network, multiedgelist in zip(names, networks, multiedges):
    print(f"\nLayer: {name}")
    print("-" * 70)

    # Calculate core network statistics
    # This includes metrics like number of nodes, edges, density, etc.
    stats = core_network_statistics(network)

    # Display the statistics
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"  Number of multiedges: {len(multiedgelist)}")

print("\n" + "=" * 70)
print("Layer analysis complete!")
