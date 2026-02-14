"""
58. Export to NetworkX

FAST: <1s runtime
Dependencies: py3plex (core), networkx

Demonstrates .to_networkx() for exporting results to NetworkX graph.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Query and export to NetworkX
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .execute(net)
)

# Export to NetworkX graph
nx_graph = result.to_networkx()
print(f"NetworkX graph type: {type(nx_graph)}")
print(f"Nodes: {nx_graph.number_of_nodes()}")
print(f"Edges: {nx_graph.number_of_edges()}")
print(f"\nNode attributes (sample):")
for node, attrs in list(nx_graph.nodes(data=True))[:2]:
    print(f"  {node}: {attrs}")
