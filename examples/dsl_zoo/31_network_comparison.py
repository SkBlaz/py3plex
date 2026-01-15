# Network comparison using C.compare()
from py3plex.core import multinet
from py3plex.dsl import C

# Create two networks to compare
net1 = multinet.multi_layer_network(directed=False)
net1.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(10)])
net1.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(10)
])

net2 = multinet.multi_layer_network(directed=False)
net2.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(10)])
net2.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+2)%10}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(10)
])

result = (
    C.compare("network1", "network2")
    .using("multiplex_jaccard")
    .execute({"network1": net1, "network2": net2})
)

print(f"Comparison result: {type(result).__name__}")
print(result)
