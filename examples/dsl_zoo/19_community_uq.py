# Community detection with UQ (partition uncertainty)
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
    Q.nodes()
    .from_layers(L["*"])
    .community(method="leiden", gamma=1.0, omega=1.0, random_state=42, partition_name="uq")
    .compute("degree")
    .uq(method="seed", n_samples=20, ci=0.95, seed=42)
    .execute(net)
)

print(result.to_pandas().head())
