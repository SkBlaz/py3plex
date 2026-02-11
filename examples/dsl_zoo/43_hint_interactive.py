"""Example 43: Interactive query building with .hint()

Demonstrates the .hint() ergonomics feature (NEW in v1.1+) that provides
context-aware suggestions for next query-building steps.

Runtime: FAST (~0.1s)
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create sample network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
])

print("=" * 60)
print("Example 1: Getting hints at query start")
print("=" * 60)

# Start building query and get hints
q = Q.nodes()
print("\nQuery state: Q.nodes()")
print("Calling .hint()...\n")
q.hint()  # Shows suggested next steps

print("\n" + "=" * 60)
print("Example 2: Getting hints after layer selection")
print("=" * 60)

# Add layer filter and get new hints
q = Q.nodes().from_layers(L["social"])
print("\nQuery state: Q.nodes().from_layers(L['social'])")
print("Calling .hint()...\n")
q.hint()  # Context-aware suggestions

print("\n" + "=" * 60)
print("Example 3: Chaining .hint() during query building")
print("=" * 60)

# Demonstrate chaining (hint returns self)
result = (
    Q.nodes()
     .from_layers(L["social"])
     .hint()  # Non-invasive - just displays info
     .compute("degree")
     .hint()  # Get new suggestions after compute
     .execute(net)
)

print("\nFinal result:")
print(result.to_pandas().head())

print("\n[HINT] Interactive query building reduces cognitive load")
print("[HINT] Use .hint() when learning DSL or building complex queries")
