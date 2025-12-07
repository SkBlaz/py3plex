"""
Basic Example: Saving Networks in Different Edgelist Formats

This example demonstrates how to:
1. Load a multilayer network
2. Save it in various edgelist formats
3. Understand the differences between format types

Supported edgelist formats:
- multiedgelist: Human-readable format with node/layer names (node1 layer1 node2 layer2 weight)
- edgelist: Simple numeric format with encoded node-layer pairs (id1 id2 weight)
- multiedgelist_encoded: Numeric format maintaining layer information (node_id1 layer_id1 node_id2 layer_id2 weight)

SKIP_CI: external_deps - Requires specific dataset files
"""

import os
from py3plex.core import multinet
from py3plex.utils import get_dataset_path, get_data_path

# Path to the dataset
dataset_path = get_dataset_path("goslim_mirna.gpickle")

# Check if the dataset exists
if not os.path.exists(dataset_path):
    print(f"Warning: Dataset file '{dataset_path}' not found.")
    print("This example requires the goslim_mirna dataset.")
    print("Please ensure the file exists before running this example.")
    exit(1)

print("Loading multilayer network...")
# Load the network from gpickle_biomine format
multilayer_network = multinet.multi_layer_network().load_network(
    dataset_path,
    directed=False,
    input_type="gpickle_biomine"
)

print("Network loaded successfully!")
print("\nSaving network in different edgelist formats...\n")

# Get the datasets directory for output files
datasets_dir = get_data_path("datasets")

# 1. Save as multiedgelist (string-based, human-readable)
print("1. Saving as multiedgelist (human-readable format)...")
output_path1 = os.path.join(datasets_dir, "mirna_multiedgelist.list")
multilayer_network.save_network(output_path1, output_type="multiedgelist")
print(f"   Saved to: {output_path1}")
print("   Format: node1 layer1 node2 layer2 weight")

# 2. Save as simple edgelist (encoded node-layer pairs as integers)
print("\n2. Saving as edgelist (compact numeric format)...")
output_path2 = os.path.join(datasets_dir, "mirna_edgelist.list")
multilayer_network.save_network(output_path2, output_type="edgelist")
print(f"   Saved to: {output_path2}")
print("   Format: encoded_node_layer_id1 encoded_node_layer_id2 weight")

# 3. Save as encoded multiedgelist (numeric with layer information)
print("\n3. Saving as encoded multiedgelist (numeric with layer info)...")
output_path3 = os.path.join(datasets_dir, "mirna_multiedgelist_encoded.list")
multilayer_network.save_network(output_path3, output_type="multiedgelist_encoded")
print(f"   Saved to: {output_path3}")
print("   Format: node_id1 layer_id1 node_id2 layer_id2 weight")

print("\nAll formats saved successfully!")
print("\nNote: Node and layer mappings are stored in the network object:")
print(f"  - Node mapping: multilayer_network.node_map")
print(f"  - Layer mapping: multilayer_network.layer_map")
print("\nThese mappings allow you to convert between numeric IDs and original names.")

# Optionally display mappings (uncomment to see)
# print("\nNode mapping sample:")
# print(dict(list(multilayer_network.node_map.items())[:5]))
# print("\nLayer mapping:")
# print(multilayer_network.layer_map)
