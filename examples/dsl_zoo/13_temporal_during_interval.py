# Temporal: filter edges during interval
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q, L

tnet = TemporalMultiLayerNetwork(directed=False)
edges = [
    ('Alice', 'social', 'Bob', 'social', 50.0, 1.0),
    ('Bob', 'social', 'Carol', 'social', 120.0, 1.0),
    ('Carol', 'social', 'Dave', 'social', 180.0, 1.0),
    ('Dave', 'social', 'Alice', 'social', 250.0, 1.0),
]
tnet.add_edges(edges, input_type="tuple")

result = (
    Q.edges()
    .during(100.0, 200.0)
    .from_layers(L["social"])
    .execute(tnet)
)

print(result.to_pandas().head())
