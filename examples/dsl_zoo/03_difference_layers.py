# Difference of layers (exclude coupling/noise layer)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(10)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(10)
] + [
    {'source': f'N{i}', 'type': 'coupling'} for i in range(10)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{i}', 'source_type': 'social', 'target_type': 'coupling'}
    for i in range(10)
])

result = (
    Q.nodes()
    .from_layers(L["*"] - L["coupling"])
    .compute("degree")
    .execute(net)
)

print(result.to_pandas().head())
