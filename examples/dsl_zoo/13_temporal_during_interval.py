# Temporal: filter edges during interval (edges carry a time attribute)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 't': 50.0},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 't': 120.0},
    {'source': 'Carol', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social', 't': 180.0},
    {'source': 'Dave', 'target': 'Alice', 'source_type': 'social', 'target_type': 'social', 't': 250.0},
])

result = (
    Q.edges()
    .during(100.0, 200.0)
    .from_layers(L["social"])
    .execute(net)
)

print(result.to_pandas().head())
