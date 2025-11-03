"""
Basic Example: Saving and Loading Networks in gpickle Format

This example demonstrates how to:
1. Load a network from a GML file
2. Save it in gpickle format (Python's pickle format for NetworkX graphs)
3. Load the saved gpickle file
4. Display basic network statistics

gpickle format is useful for:
- Fast serialization/deserialization
- Preserving all network attributes
- Efficient storage of complex network structures
"""

import os
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

# Path to the input dataset
dataset = get_dataset_path("imdb_gml.gml")

# Check if the dataset exists
if not os.path.exists(dataset):
    print(f"Warning: Dataset file '{dataset}' not found.")
    print("This example requires the IMDB dataset in the datasets folder.")
    print("Please ensure the file exists before running this example.")
    exit(1)

print("Loading network from GML format...")
# Load network from GML file
# GML (Graph Modeling Language) is a standard format for graphs
multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, 
    directed=True, 
    input_type=dataset.split(".")[-1]  # Automatically detect 'gml' format
)

print(f"Network loaded successfully from {dataset}")

# Define output path for gpickle file
output_path = get_dataset_path("imdb.gpickle")

print(f"\nSaving network to gpickle format: {output_path}")
# Save the network in gpickle format
# gpickle is NetworkX's native serialization format
multilayer_network.save_network(output_path, output_type="gpickle")

print("Network saved successfully!")

print("\nReloading network from gpickle format...")
# Create a new network object and load from the gpickle file
multilayer_network_new = multinet.multi_layer_network()
multilayer_network_new.load_network(output_path, input_type="gpickle")

print("Network reloaded successfully!")

print("\nDisplaying basic network statistics:")
print("-" * 50)
# Display basic statistics about the loaded network
multilayer_network_new.basic_stats()
