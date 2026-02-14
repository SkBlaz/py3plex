"""
44. Arrange: Sort results by columns

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .arrange() for sorting results (alias for .order_by()).
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

# DSL: Compute degree and arrange by descending order
result = (
    Q.nodes()
     .compute("degree")
     .arrange("degree", desc=True)  # Sort by degree descending
     .execute(net)
)

print("Nodes sorted by degree (descending):")
print(result.to_pandas())
