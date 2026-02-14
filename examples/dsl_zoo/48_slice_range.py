"""
48. Slice: Array-style slicing of results

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .slice() for array-style indexing (start, end).
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'Node_{i}', 'type': 'social'} 
    for i in range(10)
])
net.add_edges([
    {'source': f'Node_{i}', 'target': f'Node_{i+1}', 
     'source_type': 'social', 'target_type': 'social'}
    for i in range(9)
])

# DSL: Get items 2-5 (Python-style slicing)
result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree")
     .slice(2, 5)  # Get items at indices 2, 3, 4
     .execute(net)
)

print("Nodes at indices 2-5:")
print(result.to_pandas())
