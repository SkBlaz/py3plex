"""
Quickstart: Create a simple network and analyze it.

Demonstrates:
- Creating a network from scratch
- Adding nodes and edges
- Computing basic statistics
"""

from py3plex.core.multinet import multi_layer_network

# 1. Create network
network = multi_layer_network(directed=False)

# 2. Add edges (nodes created automatically)
network.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
])

# 3. Print statistics
print(f"Nodes: {len(list(network.get_nodes()))}")
print(f"Edges: {len(list(network.get_edges()))}")
print(f"Layers: {len(network.get_layers()[0])}")
