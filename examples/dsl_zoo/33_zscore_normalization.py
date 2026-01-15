# Z-score normalization per layer
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(15)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(12)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%12}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(12)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree", "pagerank")
    .per_layer()
    .zscore("degree", "pagerank")
    .end_grouping()
    .execute(net)
)

print(result.to_pandas().head())
