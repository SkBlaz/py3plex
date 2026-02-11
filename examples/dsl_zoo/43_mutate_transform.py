"""
43. Mutate: Transform and add computed columns

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .mutate() for adding/transforming columns with lambda functions.
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

# DSL: Compute degree and add normalized/scaled columns using mutate
result = (
    Q.nodes()
     .compute("degree")
     .mutate(
         norm_degree=lambda r: r["degree"] / 3.0,  # Normalize by max degree
         degree_squared=lambda r: r["degree"] ** 2,  # Square the degree
         high_degree=lambda r: r["degree"] > 1,  # Boolean flag
     )
     .execute(net)
)

print("Nodes with mutated columns:")
print(result.to_pandas().head())
