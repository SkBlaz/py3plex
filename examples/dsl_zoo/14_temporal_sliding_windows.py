# Temporal: sliding windows
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q, L

tnet = TemporalMultiLayerNetwork(directed=False)
edges = [
    (f'N{i}', 'social', f'N{(i+1)%10}', 'social', float(i * 20), 1.0)
    for i in range(20)
]
tnet.add_edges(edges, input_type="tuple")

result = (
    Q.edges()
    .from_layers(L["social"])
    .window(window_size=100.0, step=50.0, aggregation="list")
    .summarise(count="n()")
    .execute(tnet)
)

print(result.to_pandas().head())
