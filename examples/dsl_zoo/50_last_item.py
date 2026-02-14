"""
50. Last: Get last item only

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .last() for selecting only the last item.
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
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Get node with lowest degree
result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree")  # Ascending
     .last()  # Get only the last item
     .execute(net)
)

print("Node with lowest degree:")
print(result.to_pandas())
