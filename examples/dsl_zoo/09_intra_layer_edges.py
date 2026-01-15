# Intra-layer edges only (special predicate)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(8)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(8)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%8}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(8)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%8}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(8)
] + [
    {'source': f'N{i}', 'target': f'N{i}', 'source_type': 'social', 'target_type': 'work'}
    for i in range(4)
])

result = (
    Q.edges()
    .from_layers(L["*"])
    .where(intralayer=True)
    .execute(net)
)

print(result.to_pandas().head())
