# AutoCommunity DSL shortcut
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(20)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%20}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(20)
] + [
    {'source': f'N{i}', 'target': f'N{(i+2)%20}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 20, 2)
])

result = (
    Q.communities()
    .auto_select(fast=True, seed=42)
    .execute(net)
)

print("Communities detected:", len(result.communities) if hasattr(result, 'communities') else "N/A")
print(result.to_pandas().head() if hasattr(result, 'to_pandas') else result)
