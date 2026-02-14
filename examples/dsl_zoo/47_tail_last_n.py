"""
47. Tail: Get last n items

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .tail() for selecting the last n items.
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
    {'source': 'Eve', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Carol', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Dave', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Get last 2 nodes after sorting
result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree")  # Sort ascending
     .tail(2)  # Get last 2 items
     .execute(net)
)

print("Last 2 nodes (highest degree):")
print(result.to_pandas())
