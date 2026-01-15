# Temporal: query at specific time point
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q, L

tnet = TemporalMultiLayerNetwork(directed=False)
edges = [
    ('Alice', 'social', 'Bob', 'social', 50.0, 1.0),
    ('Bob', 'social', 'Carol', 'social', 100.0, 1.0),
    ('Carol', 'social', 'Dave', 'social', 150.0, 1.0),
    ('Dave', 'social', 'Alice', 'social', 200.0, 1.0),
]
tnet.add_edges(edges, input_type="tuple")

result = (
    Q.edges()
    .at(150.0)
    .from_layers(L["social"])
    .execute(tnet)
)

print(result.to_pandas().head())
