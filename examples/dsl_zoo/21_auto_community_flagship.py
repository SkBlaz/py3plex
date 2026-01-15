# AutoCommunity full "flagship" (Pareto + UQ + null calibration)
from py3plex.core import multinet
from py3plex.algorithms.community_detection import AutoCommunity

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
    AutoCommunity()
    .candidates("louvain", "leiden")
    .metrics("modularity", "coverage")
    .uq(method="perturbation", n_samples=20, seed=42)
    .null_model(type="configuration", samples=20)
    .pareto()
    .seed(42)
    .execute(net)
)

print("Selected algorithm:", result.algorithm.get('name', 'N/A') if hasattr(result, 'algorithm') else "N/A")
print("Communities:", result.community_stats.n_communities if hasattr(result, 'community_stats') else "N/A")
