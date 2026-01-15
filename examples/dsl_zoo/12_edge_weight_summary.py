# Edge-weight summary per layer
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'social'} for i in range(10)
] + [
    {'source': f'N{i}', 'type': 'work'} for i in range(10)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0 + i * 0.1}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'work', 'target_type': 'work', 'weight': 2.0 + i * 0.2}
    for i in range(10)
])

result = (
    Q.edges()
    .from_layers(L["*"])
    .per_layer_pair()
    .summarise(mean_w="mean(weight)", sum_w="sum(weight)", count="n()")
    .end_grouping()
    .execute(net)
)

print(result.to_pandas().head())
