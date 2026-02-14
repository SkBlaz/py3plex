"""
57. Replay: Reproduce query from provenance

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .replay() for reproducing queries from provenance.
Note: Full replay requires provenance mode to be enabled.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Execute query (provenance is captured by default)
result = (
    Q.nodes()
     .compute("degree")
     .execute(net)
)

print("Original result:")
print(result.to_pandas())

# Check if result is replayable
print(f"\nIs replayable: {result.is_replayable}")
print(f"Provenance keys: {list(result.provenance.keys())}")

# Note: Full replay requires replayable provenance mode
# For demonstration, we show the provenance structure
if result.is_replayable:
    print("\nThis result can be replayed using .replay()")
else:
    print("\nNote: Enable provenance mode for full replay capability")
    print("See AGENTS.md for provenance configuration")
