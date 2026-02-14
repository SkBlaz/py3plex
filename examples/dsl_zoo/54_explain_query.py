"""
54. Explain: Human-readable query explanation

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .explain() for getting a human-readable explanation of query execution.
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

# DSL: Execute query and explain results
result = (
    Q.nodes()
     .from_layers(L["social"])
     .compute("degree", "betweenness_centrality")
     .where(degree__gt=0)
     .execute(net)
)

# Get human-readable explanation
print("Query Explanation:")
print("=" * 60)
print(result.explain())
