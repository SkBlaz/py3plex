"""
Basic Example: Generating and Visualizing Random Multilayer Networks

This example demonstrates how to:
1. Generate a random multilayer Erdős-Rényi (ER) network
2. Visualize the network structure

The random_multilayer_ER function creates a multilayer network where each layer
is an Erdős-Rényi random graph with the specified parameters.
"""

from py3plex.core import random_generators

print("Generating random multilayer Erdős-Rényi network...")
print("Parameters:")
print("  - Number of nodes: 200")
print("  - Number of layers: 6")
print("  - Edge probability: 0.09")
print("  - Directed: True")

# Generate the multilayer network
# Parameters: (num_nodes, num_layers, edge_probability, directed)
ER_multilayer = random_generators.random_multilayer_ER(
    200,    # Number of nodes in the network
    6,      # Number of layers
    0.09,   # Probability of edge creation between any two nodes
    directed=True
)

print("\nNetwork generated successfully!")

# In CI mode, skip interactive visualization
import os
if os.environ.get('MPLBACKEND') == 'Agg':
    print("Running in CI mode - skipping interactive visualization")
else:
    print("Visualizing the network (close the window to exit)...")
    # Visualize the network without node labels for clarity
    ER_multilayer.visualize_network(show=True, no_labels=True)
