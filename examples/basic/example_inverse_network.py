"""
Basic Example: Creating an Inverse (Transposed) Network

This example demonstrates how to:
1. Load a directed multilayer network
2. Invert/transpose the network (reverse all edge directions)
3. Compare statistics before and after inversion

Network inversion is useful for:
- Analyzing information flow in the opposite direction
- Finding incoming vs outgoing connectivity patterns
- Studying reversed causality relationships
"""

import os
from py3plex.core import multinet

# Path to the dataset
dataset_path = "../datasets/epigenetics.gpickle"

# Check if the dataset exists
if not os.path.exists(dataset_path):
    print(f"Warning: Dataset file '{dataset_path}' not found.")
    print("This example requires the epigenetics dataset.")
    print("Please ensure the file exists before running this example.")
    exit(1)

print("Loading directed multilayer network...")
# Load a directed network (edge directions matter)
multilayer_network = multinet.multi_layer_network().load_network(
    dataset_path,
    directed=True,  # Network has directed edges
    input_type="gpickle_biomine"
)

print("Network loaded successfully!")
print("\n" + "=" * 70)
print("ORIGINAL NETWORK STATISTICS")
print("=" * 70)
# Display statistics of the original network
multilayer_network.basic_stats()

print("\n" + "=" * 70)
print("INVERTING NETWORK (reversing all edge directions)...")
print("=" * 70)

# Invert the network (reverse all edge directions)
# If override_core=True, replaces the original network
# If override_core=False, stores as obj.core_network_inverse
multilayer_network.invert(override_core=True)

print("\nInversion complete!")
print("\n" + "=" * 70)
print("INVERTED NETWORK STATISTICS")
print("=" * 70)
# Display statistics of the inverted network
multilayer_network.basic_stats()

print("\n" + "=" * 70)
print("\nNote: In the inverted network:")
print("  - All edge directions are reversed")
print("  - In-degree becomes out-degree and vice versa")
print("  - Useful for analyzing opposite information flow patterns")
