"""
51. Pluck: Extract single column

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .pluck() for extracting a single column as a list.
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

# DSL: Extract just the degree values
result = (
    Q.nodes()
     .compute("degree")
     .pluck("degree")  # Extract single column
     .execute(net)
)

print("Degree values only:")
df = result.to_pandas()
print(df)
print(f"\nPlucked column: {df['degree'].tolist()}")
