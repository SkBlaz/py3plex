# Per-layer top hubs (Golden Path)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(15)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(10)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+2)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 15, 3)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(10)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree", "betweenness_centrality")
    .per_layer()
    .top_k(10, "degree")
    .end_grouping()
    .execute(net)
)

print(result.to_pandas().head())
