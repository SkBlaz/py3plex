"""Example 45: Dplyr-style slicing operations

Demonstrates slice(), first(), last(), and pluck() for extracting
specific rows or columns from query results.

Runtime: FAST (~0.1s)
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create sample network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'Node_{i}', 'type': 'social'} for i in range(1, 11)
] + [
    {'source': f'Node_{i}', 'type': 'work'} for i in range(1, 11)
])
net.add_edges([
    {'source': f'Node_{i}', 'target': f'Node_{i+1}',
     'source_type': 'social', 'target_type': 'social'}
    for i in range(1, 10)
] + [
    {'source': f'Node_{i}', 'target': f'Node_{i+1}',
     'source_type': 'work', 'target_type': 'work'}
    for i in range(1, 10)
])

print("=" * 60)
print("Example 1: Get first N items with .head()")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree", desc=True)
     .head(3)  # Top 3 items
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 2: Get last N items with .tail()")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree", desc=True)
     .tail(3)  # Bottom 3 items
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 3: Slice with start and end indices")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree", desc=True)
     .slice(2, 5)  # Items 2-5 (0-indexed)
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 4: Get single item with .first()")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree", desc=True)
     .first()  # Top item only
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 5: Extract column with .pluck()")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .order_by("degree", desc=True)
     .head(5)
     .pluck("degree")  # Extract just degree column
     .execute(net)
)
df = result.to_pandas()
print("Extracted degree column:")
print(df)

print("\n[TIP] Use .head() / .tail() / .slice() for sampling results")
print("[TIP] Use .first() / .last() for single-item queries")
print("[TIP] Use .pluck() to extract specific columns only")
