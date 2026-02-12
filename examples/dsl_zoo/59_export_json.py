"""
59. Export to JSON

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates JSON export pattern: QueryResult -> pandas -> JSON.
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
# Pattern: QueryResult -> pandas DataFrame -> JSON
# (pandas properly handles tuple keys and provides clean JSON structure)
df = result.to_pandas()
json_str = df.to_json(orient='records', indent=2)
print("JSON export:")
print("=" * 60)
print(json_str)
