# Pattern matching (Cypher-like)
from py3plex.core import multinet
from py3plex.dsl import Q

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(10)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%10}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(10)
])

# Pattern matching for edges in social layer
result = (
    Q.pattern()
    .node("a").where(layer="social")
    .node("b").where(layer="social")
    .edge("a", "b", directed=False)
    .returning("a", "b")
    .limit(25)
    .execute(net)
)

print(result.to_pandas().head() if hasattr(result, 'to_pandas') else result)
