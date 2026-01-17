# Temporal: query at specific time point (edges carry a time attribute)
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 't': 50.0},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 't': 100.0},
    {'source': 'Carol', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social', 't': 150.0},
    {'source': 'Dave', 'target': 'Alice', 'source_type': 'social', 'target_type': 'social', 't': 200.0},
])

result = (
    Q.edges()
    .at(150.0)
    .from_layers(L["social"])
    .execute(net)
)

print(result.to_pandas().head())
