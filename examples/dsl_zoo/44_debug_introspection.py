"""Example 44: Debug and result introspection

Demonstrates QueryResult introspection with enhanced __repr__ and .debug()
for understanding query execution details.

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
print("Example 1: Enhanced QueryResult __repr__")
print("=" * 60)

# Execute query and inspect result object
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .per_layer()
     .execute(net)
)

print("\nResult representation:")
print(result)  # Shows: target, count, attributes, computed, grouping, etc.

print("\n" + "=" * 60)
print("Example 2: Inspecting metadata")
print("=" * 60)

print(f"\nTarget: {result.target}")
print(f"Count: {result.count}")
print(f"Attributes: {list(result.attributes.keys())}")
print(f"Computed metrics: {result.computed_metrics}")
if result.meta.get("grouping"):
    print(f"Grouping: {result.meta['grouping']}")

print("\n" + "=" * 60)
print("Example 3: Checking provenance")
print("=" * 60)

if "provenance" in result.meta:
    prov = result.meta["provenance"]
    print(f"\nEngine: {prov.get('engine', 'N/A')}")
    print(f"Query AST hash: {prov.get('query', {}).get('ast_hash', 'N/A')}")
    print(f"Execution time: {prov.get('performance', {}).get('total_ms', 'N/A')}ms")

print("\n" + "=" * 60)
print("Example 4: Result with UQ")
print("=" * 60)

# Query with uncertainty
result_uq = (
    Q.nodes()
     .compute("degree")
     .uq(method="seed", n_samples=5, seed=42)
     .execute(net)
)

print("\nUQ Result representation:")
print(result_uq)
print(f"Has uncertainty: {result_uq.meta.get('has_uncertainty', False)}")

print("\n[TIP] Always inspect QueryResult before calling .to_pandas()")
print("[TIP] Use result.meta for execution details and diagnostics")
