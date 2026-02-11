"""
55. Debug: Technical debugging information

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .debug() for getting technical details about query execution.
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

# DSL: Execute query and get debugging info
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .order_by("betweenness_centrality", desc=True)
     .limit(10)
     .execute(net)
)

# Get technical debugging information
print("Debug Information:")
print("=" * 60)
print(result.debug())
