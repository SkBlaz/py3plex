# Coverage: cross-layer node filtering
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(15)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(12)
] + [
    {'source': f'N{i}', 'type': 'hobby'} for i in range(10)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%12}', 'source_type': 'work', 'target_type': 'work'}
    for i in range(12)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'hobby', 'target_type': 'hobby'}
    for i in range(10)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree")
    .per_layer()
    .top_k(5, "degree")
    .end_grouping()
    .coverage(mode="all")
    .execute(net)
)

print(result.to_pandas().head())
