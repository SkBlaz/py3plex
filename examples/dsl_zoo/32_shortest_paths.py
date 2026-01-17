# Path queries: shortest paths
from py3plex.core import multinet
from py3plex.dsl import P, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(10)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{(i+3)%10}', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0}
    for i in range(0, 10, 2)
])

result = (
    P.shortest("N0", "N5")
    .on_layers(L["social"])
    .execute(net)
)

print(f"Path result: {type(result).__name__}")
print(result)
