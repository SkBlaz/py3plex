# Null-model statistical testing
from py3plex.core import multinet
from py3plex.dsl import N, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(15)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
] + [
    {'source': f'N{i}', 'target': f'N{(i+2)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(0, 15, 3)
])

# Generate null models using configuration model
result = (
    N.configuration()
    .samples(30)
    .seed(42)
    .execute(net)
)

print("Generated", result.n_samples if hasattr(result, 'n_samples') else len(result) if hasattr(result, '__len__') else "N/A", "null model samples")
print(type(result).__name__)
