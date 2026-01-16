# Compositional UQ: uncertainty propagation through aggregate/ranking
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(10)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(8)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%8}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(8)
])

# Compositional UQ: Per-layer aggregation with uncertainty
result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree", "clustering")
    .per_layer()
    .aggregate(
        avg_degree="mean(degree)",
        max_cluster="max(clustering)",
        node_count="count()"
    )
    .uq(method="bootstrap", n_samples=20, ci=0.95, seed=42)
    .execute(net)
)

print(result.to_pandas().head())
