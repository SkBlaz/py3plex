# Parameterized queries with Param placeholders
from py3plex.core import multinet
from py3plex.dsl import Q, L, Param

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(15)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+2)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 15, 3)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("degree")
    .where(degree__gt=Param.int("threshold"))
    .order_by("degree", desc=True)
    .execute(net, threshold=2)
)

print(result.to_pandas().head())
