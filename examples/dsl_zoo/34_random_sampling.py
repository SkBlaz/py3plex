# Random sampling of results
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(50)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%50}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(50)
] + [
    {'source': f'N{i}', 'target': f'N{(i+5)%50}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 50, 5)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree")
    .sample(n=10, seed=42)
    .execute(net)
)

print(result.to_pandas().head())
