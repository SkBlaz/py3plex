"""
Network construction: Using fluent chaining.

Demonstrates:
- Method chaining for network construction
- Adding nodes and edges in sequence
"""

from py3plex.core.multinet import multi_layer_network

# 1. Create and build network using chaining
network = multi_layer_network(directed=False)

# 2. Add nodes
network.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'work'},
])

# 3. Add edges
network.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'work'},
])

# 4. Print result
print(f"Built network with {len(list(network.get_nodes()))} nodes")
