"""
Network construction: From edge list.

Demonstrates:
- Creating network from dictionary-based edge list
- Different layer assignments
- Edge attributes
"""

from py3plex.core.multinet import multi_layer_network

# 1. Create network
network = multi_layer_network(directed=False)

# 2. Define edges with layers
edges = [
    {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    {'source': 'A', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
    {'source': 'C', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'},
]

# 3. Add edges
network.add_edges(edges)

# 4. Print result
print(f"Network: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")
print(f"Layers: {network.layers}")
