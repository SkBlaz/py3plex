"""
53. Hint: Interactive query building suggestions

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .hint() for getting context-aware suggestions during query building.
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

# DSL: Use .hint() to get suggestions during query building
print("Building query with hints:\n")

q = Q.nodes().from_layers(L["social"])
print("After .from_layers():")
q.hint()  # Shows suggestions for next steps

q = q.compute("degree")
print("\nAfter .compute('degree'):")
q.hint()  # Shows new suggestions

# Complete the query
result = q.execute(net)
print("\nFinal result:")
print(result.to_pandas())
