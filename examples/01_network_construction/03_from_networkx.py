"""
Network construction: From NetworkX graph.

Demonstrates:
- Converting NetworkX graph to multilayer network
- Preserving attributes
"""

import networkx as nx
from py3plex.core.multinet import multi_layer_network

# 1. Create NetworkX graph
G = nx.karate_club_graph()

# 2. Convert to multilayer (single layer)
network = multi_layer_network(directed=False)
for u, v in G.edges():
    network.add_edges([{
        'source': str(u),
        'target': str(v),
        'source_type': 'karate',
        'target_type': 'karate'
    }])

# 3. Print result
print(f"Converted {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
print(f"Layers: {network.get_layers()[0]}")
