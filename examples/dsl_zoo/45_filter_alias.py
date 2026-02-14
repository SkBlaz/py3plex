"""
45. Filter: Alternative syntax for .where()

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .filter() as an alias for .where() (dplyr-style).
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Dave', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Use .filter() instead of .where() (same behavior)
result = (
    Q.nodes()
     .compute("degree")
     .filter(degree__gt=1)  # Filter for nodes with degree > 1
     .execute(net)
)

print("Nodes with degree > 1:")
print(result.to_pandas())
