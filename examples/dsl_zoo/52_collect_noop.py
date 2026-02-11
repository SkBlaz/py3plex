"""
52. Collect: No-op for API compatibility

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .collect() - a no-op method for API compatibility with other frameworks.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: .collect() is a no-op, included for compatibility with dplyr/Spark APIs
result = (
    Q.nodes()
     .compute("degree")
     .collect()  # No-op, returns self
     .execute(net)
)

print("Nodes (collect is a no-op):")
print(result.to_pandas())
