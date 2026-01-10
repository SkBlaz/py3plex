"""
Network construction: From NetworkX graph.

Demonstrates:
- Converting NetworkX graph to multilayer network
- Simple edge transfer
"""

import networkx as nx
from py3plex.core.multinet import multi_layer_network

# 1. Create small NetworkX graph
G = nx.Graph()
G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])

# 2. Convert to multilayer (single layer)
network = multi_layer_network(directed=False)
for u, v in G.edges():
    network.add_edges([{
        'source': str(u),
        'target': str(v),
        'source_type': 'simple',
        'target_type': 'simple'
    }])

# 3. Print result
print(f"Converted {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
print(f"Multilayer network created successfully")
