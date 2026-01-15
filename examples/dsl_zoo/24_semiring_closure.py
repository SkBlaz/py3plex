# Semiring algebra / paths / closure
from py3plex.core import multinet
from py3plex.dsl import S, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(10)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0}
    for i in range(10)
])

# Semiring closure using min-plus semiring
result = (
    S.closure()
    .semiring("min_plus")
    .from_layers(L["*"])
    .k(5)
    .execute(net)
)

print("Closure result type:", type(result).__name__)
if hasattr(result, 'to_pandas'):
    print(result.to_pandas().head())
else:
    print("Result:", result)
