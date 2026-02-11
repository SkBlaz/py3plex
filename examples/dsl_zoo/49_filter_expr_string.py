"""Example 49: String expression filtering

Demonstrates .filter_expr() for filtering using string expressions,
useful for dynamic or programmatic query construction.

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
    {'source': 'Dave', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Carol', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
])

print("=" * 60)
print("Example 1: Simple string expression")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .filter_expr("degree > 1")
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 2: Complex AND expression")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree", "clustering")
     .filter_expr("degree > 1 and clustering < 1.0")
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 3: OR expression with parentheses")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .filter_expr("(degree == 1) or (degree == 3)")
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 4: Layer filtering via expression")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .filter_expr("layer == 'social' and degree > 1")
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 5: Dynamic expression from user input")
print("=" * 60)

# Simulate user-provided filter criteria
user_threshold = 2
user_layer = "social"
expr = f"degree >= {user_threshold} and layer == '{user_layer}'"

print(f"User expression: {expr}")

result = (
    Q.nodes()
     .compute("degree")
     .filter_expr(expr)
     .execute(net)
)
print(result.to_pandas())

print("\n[TIP] Use .filter_expr() for dynamic/programmatic filtering")
print("[TIP] String expressions support: >, <, >=, <=, ==, !=, and, or, ()")
print("[TIP] Equivalent to .where() but accepts string expressions")
print("[TIP] Useful for user-provided filters or templated queries")
