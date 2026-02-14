"""
46. Filter Expression: String-based filtering

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .filter_expr() for string-based boolean expressions.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
])

# DSL: Use string expression for complex filtering
result = (
    Q.nodes()
     .compute("degree")
     .filter_expr("degree > 1 and layer == 'social'")  # String-based filter
     .execute(net)
)

print("Nodes with degree > 1 in social layer:")
print(result.to_pandas())
