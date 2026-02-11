"""
56. Provenance: Access execution metadata

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates accessing .provenance metadata for reproducibility.
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

# DSL: Execute query and access provenance
result = (
    Q.nodes()
     .compute("degree")
     .execute(net)
)

# Access provenance metadata
prov = result.provenance
print("Provenance Metadata:")
print("=" * 60)
print(json.dumps(prov, indent=2))

print("\nKey provenance fields:")
print(f"  Engine: {prov.get('engine')}")
print(f"  Version: {prov.get('py3plex_version')}")
print(f"  Timestamp: {prov.get('timestamp_utc')}")
print(f"  Is replayable: {result.is_replayable}")
