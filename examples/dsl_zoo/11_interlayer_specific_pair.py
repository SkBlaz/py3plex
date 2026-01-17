# Interlayer edges between specific layer pair
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'N{i}', 'type': 'gene'} for i in range(10)
] + [
    {'source': f'D{i}', 'type': 'disease'} for i in range(8)
] + [
    {'source': f'P{i}', 'type': 'protein'} for i in range(6)
])
net.add_edges([
    {'source': f'N{i}', 'target': f'D{i%8}', 'source_type': 'gene', 'target_type': 'disease'}
    for i in range(10)
] + [
    {'source': f'N{i}', 'target': f'P{i%6}', 'source_type': 'gene', 'target_type': 'protein'}
    for i in range(10)
])

result = (
    Q.edges()
    .from_layers(L["*"])
    .where(interlayer=("gene", "disease"))
    .summarise(count="n()")
    .execute(net)
)

count = result.attributes.get("count", {}).get("__global__", 0)
print("Edge count between gene and disease layers:", count)
