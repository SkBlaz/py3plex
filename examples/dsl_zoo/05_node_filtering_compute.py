# Node attribute filtering with compute
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(20)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%20}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(20)
] + [
    {'source': f'N{i}', 'target': f'N{(i+2)%20}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 20, 2)
] + [
    {'source': f'N{i}', 'target': f'N{(i+3)%20}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 20, 3)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .where(degree__gt=5)
    .compute("pagerank")
    .execute(net)
)

print(result.to_pandas().head())
