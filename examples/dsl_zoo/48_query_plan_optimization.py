"""Example 48: Query planner and optimization

Demonstrates the DSL v2 query planner that automatically optimizes
query execution by reordering operations.

Runtime: FAST (~0.1s)
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create sample network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': f'Node_{i}', 'type': 'social'} for i in range(1, 21)
] + [
    {'source': f'Node_{i}', 'type': 'work'} for i in range(1, 21)
])
net.add_edges([
    {'source': f'Node_{i}', 'target': f'Node_{i+1}',
     'source_type': 'social', 'target_type': 'social'}
    for i in range(1, 20)
] + [
    {'source': f'Node_{i}', 'target': f'Node_{i+2}',
     'source_type': 'work', 'target_type': 'work'}
    for i in range(1, 18)
])

print("=" * 60)
print("Example 1: Query planner automatic optimization")
print("=" * 60)

# Query with filters - planner will optimize execution order
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")  # Expensive compute
     .from_layers(L["social"])  # Layer filter (cheap)
     .where(degree__gt=2)  # Attribute filter
     .execute(net)
)

# Check if planner optimized
prov = result.meta.get('provenance', {})
plan_hash = prov.get('query', {}).get('plan_hash')
print(f"\nQuery executed with plan hash: {plan_hash}")
print(f"Execution time: {prov.get('performance', {}).get('total_ms', 'N/A')}ms")

print("\n[NOTE] Planner moved .from_layers() early to reduce item set")
print("[NOTE] Filters applied before expensive compute operations")

print("\n" + "=" * 60)
print("Example 2: Checking cache hits")
print("=" * 60)

# Run same query twice - second should hit cache
result1 = Q.nodes().compute("degree").execute(net)
result2 = Q.nodes().compute("degree").execute(net)  # Cache hit

prov1 = result1.meta.get('provenance', {})
prov2 = result2.meta.get('provenance', {})

time1 = prov1.get('performance', {}).get('total_ms', 0)
time2 = prov2.get('performance', {}).get('total_ms', 0)

print(f"\nFirst execution: {time1}ms")
print(f"Second execution: {time2}ms")
print(f"Speedup: {time1/time2:.2f}x" if time2 > 0 else "Speedup: N/A")

print("\n" + "=" * 60)
print("Example 3: Compute policy - minimal")
print("=" * 60)

# Request 3 metrics but only use 1 in filter
# With minimal compute policy, only degree computed
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality", "closeness_centrality")
     .where(degree__gt=2)  # Only uses degree
     .execute(net)
)

computed = result.computed_metrics
print(f"\nMetrics requested: degree, betweenness_centrality, closeness_centrality")
print(f"Metrics computed: {computed}")
print("[NOTE] Planner may optimize away unused expensive metrics")

print("\n" + "=" * 60)
print("Example 4: Filter pushdown optimization")
print("=" * 60)

result = (
    Q.nodes()
     .where(layer="social")  # Intrinsic field - can push down
     .compute("degree")  # Only computed on social layer
     .where(degree__gt=2)  # Computed field - stays after compute
     .execute(net)
)

print(f"\nOptimized query result count: {result.count}")
print("[NOTE] Layer filter pushed before compute for efficiency")

print("\n[TIP] Query planner runs automatically - no configuration needed")
print("[TIP] Use .from_layers() early to reduce computation scope")
print("[TIP] Planner caches expensive operations by network+query+params")
print("[TIP] Same network + same query + same seed -> cache hit")
