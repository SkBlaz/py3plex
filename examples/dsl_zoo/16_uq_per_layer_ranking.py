# UQ per-layer: stable per-layer ranking
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(12)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(10)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%12}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(12)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(10)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("pagerank")
    .per_layer()
    .uq(method="seed", n_samples=30, ci=0.95, seed=42)
    .top_k(10, "pagerank")
    .end_grouping()
    .execute(net)
)

print(result.to_pandas(expand_uncertainty=True).head())
