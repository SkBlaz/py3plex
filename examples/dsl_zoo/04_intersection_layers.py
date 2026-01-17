# Intersection of layer sets (overlapping layer name)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
# Nodes across gene, drug, and shared layers
net.add_nodes([
    {'source': f'N{i}', 'type': 'gene'} for i in range(15)
] + [
    {'source': f'N{i}', 'type': 'drug'} for i in range(10)
] + [
    {'source': f'N{i}', 'type': 'shared'} for i in range(8)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'gene', 'target_type': 'gene'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'drug', 'target_type': 'drug'}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'N{(i+1)%8}', 'source_type': 'shared', 'target_type': 'shared'}
    for i in range(8)
])

result = (
    Q.nodes()
    .from_layers(L["(gene | shared) & (shared | drug)"])
    .compute("degree")
    .execute(net)
)

print(result.to_pandas().head())
