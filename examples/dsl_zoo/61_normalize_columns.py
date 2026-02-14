"""
61. Normalize: Column normalization

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .normalize() for normalizing column values.
Note: This uses .mutate() for normalization as .normalize() may not be a standard method.
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

# DSL: Compute metrics and normalize using mutate
result = (
    Q.nodes()
     .compute("degree")
     .execute(net)
)

# Get min/max for normalization
df = result.to_pandas()
min_degree = df['degree'].min()
max_degree = df['degree'].max()

# Apply min-max normalization
result_normalized = (
    Q.nodes()
     .compute("degree")
     .mutate(
         degree_normalized=lambda r: (r["degree"] - min_degree) / (max_degree - min_degree) 
         if max_degree > min_degree else 0.0
     )
     .execute(net)
)

print("Nodes with normalized degree:")
print(result_normalized.to_pandas())
