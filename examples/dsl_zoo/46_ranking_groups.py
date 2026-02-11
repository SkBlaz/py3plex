"""Example 46: Ranking within groups

Demonstrates .rank_by() for computing ranks within per-layer groups
or globally across the network.

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
    {'source': 'Eve', 'type': 'work'},
])
net.add_edges([
    # Social layer - Alice is hub
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    # Work layer - Bob is hub
    {'source': 'Bob', 'target': 'Alice', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
])

print("=" * 60)
print("Example 1: Global ranking by degree")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .rank_by("degree", method="dense")
     .order_by("degree", desc=True)
     .execute(net)
)
print(result.to_pandas())

print("\n" + "=" * 60)
print("Example 2: Per-layer ranking")
print("=" * 60)

result = (
    Q.nodes()
     .per_layer()
     .compute("degree")
     .rank_by("degree", method="dense")
     .end_grouping()
     .order_by("degree", desc=True)
     .execute(net)
)
df = result.to_pandas()
print(df)

print("\n[NOTE] Per-layer ranking: same node can have different ranks in different layers")
print(f"[NOTE] Alice degree_rank in social: {df[(df['id']=='Alice') & (df['layer']=='social')]['degree_rank'].values}")
print(f"[NOTE] Alice degree_rank in work: {df[(df['id']=='Alice') & (df['layer']=='work')]['degree_rank'].values}")

print("\n" + "=" * 60)
print("Example 3: Ranking with ties handling")
print("=" * 60)

result = (
    Q.nodes()
     .compute("degree")
     .rank_by("degree", method="min")  # min, max, average, dense
     .order_by("degree", desc=True)
     .execute(net)
)
print(result.to_pandas())

print("\n[TIP] Use rank_by() to create rank columns without changing order")
print("[TIP] method='dense' gives consecutive ranks (1, 2, 3...)")
print("[TIP] method='min' gives minimum rank for ties (1, 2, 2, 4...)")
print("[TIP] Combine with .per_layer() for within-layer ranking")
