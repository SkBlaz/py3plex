"""
59. Export to JSON

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .to_json() for exporting results to JSON format.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L
import json

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Query and export to JSON
result = (
    Q.nodes()
     .compute("degree")
     .execute(net)
)

# Export to JSON string
json_str = result.to_json()
print("JSON export:")
print("=" * 60)
# Pretty-print the JSON
parsed = json.loads(json_str)
print(json.dumps(parsed, indent=2))
