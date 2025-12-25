#!/usr/bin/env python3
"""Simple test script to validate mutate() functionality."""

import sys
from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("Testing Builder DSL Key Operations")
print("=" * 80)

# Create a sample network
network = multinet.multi_layer_network(directed=False)

# Add nodes
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'David', 'type': 'work'},
    {'source': 'Eve', 'type': 'work'},
]
network.add_nodes(nodes)

# Add edges
edges = [
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
]
network.add_edges(edges)

print(f"\nNetwork created with {len(nodes)} nodes and {len(edges)} edges")

# Test 1: Node Selection
print("\n" + "=" * 80)
print("Test 1: Node Selection (Q.nodes())")
print("-" * 80)
result = Q.nodes().execute(network)
print(f"✓ Selected {result.count} nodes")
assert result.count > 0, "Should have nodes"

# Test 2: Edge Selection
print("\n" + "=" * 80)
print("Test 2: Edge Selection (Q.edges())")
print("-" * 80)
result = Q.edges().execute(network)
print(f"✓ Selected {result.count} edges")
assert result.count > 0, "Should have edges"

# Test 3: Filtering
print("\n" + "=" * 80)
print("Test 3: Filtering (.where())")
print("-" * 80)
result = Q.nodes().where(layer="social").execute(network)
print(f"✓ Filtered to {result.count} social nodes")
assert result.count == 3, "Should have 3 social nodes"

# Test 4: Mutations
print("\n" + "=" * 80)
print("Test 4: Mutations (.mutate())")
print("-" * 80)

# Test 4a: Simple constant mutation
result = Q.nodes().compute("degree").mutate(
    category="hub"
).execute(network)
print(f"✓ Added constant 'category' column")
assert 'category' in result.attributes, "Should have 'category' attribute"
# Note: Constant values work in the implementation

# Test 4b: Lambda-based mutation
result = Q.nodes().compute("degree").mutate(
    doubled_degree=lambda row: row.get("degree", 0) * 2,
    plus_one=lambda row: row.get("degree", 0) + 1
).execute(network)
print(f"✓ Created 'doubled_degree' and 'plus_one' columns using lambdas")
assert 'doubled_degree' in result.attributes, "Should have 'doubled_degree' attribute"
assert 'plus_one' in result.attributes, "Should have 'plus_one' attribute"

# Verify the transformations
for node in result.items[:3]:
    degree = result.attributes.get('degree', {}).get(node, 0)
    doubled = result.attributes.get('doubled_degree', {}).get(node, 0)
    plus_one = result.attributes.get('plus_one', {}).get(node, 0)
    print(f"  {node}: degree={degree}, doubled={doubled}, plus_one={plus_one}")
    assert doubled == degree * 2, f"Doubled degree should be {degree * 2}, got {doubled}"
    assert plus_one == degree + 1, f"Plus one should be {degree + 1}, got {plus_one}"

# Test 4c: Complex mutation with multiple attributes
result = Q.nodes().compute("degree", "clustering").mutate(
    score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
    is_hub=lambda row: row.get("degree", 0) > 1
).execute(network)
print(f"✓ Created 'score' and 'is_hub' columns using multiple attributes")
assert 'score' in result.attributes, "Should have 'score' attribute"
assert 'is_hub' in result.attributes, "Should have 'is_hub' attribute"

# Test 5: Summary
print("\n" + "=" * 80)
print("Test 5: Summary (.summarize())")
print("-" * 80)
result = Q.nodes().compute("degree").summarize(
    avg_degree="mean(degree)",
    max_degree="max(degree)",
    n="n()"
).execute(network)
print(f"✓ Created summary with avg_degree, max_degree, and count")
assert 'avg_degree' in result.attributes, "Should have 'avg_degree' attribute"
assert 'max_degree' in result.attributes, "Should have 'max_degree' attribute"
assert 'n' in result.attributes, "Should have 'n' attribute"

# Print summary results
if result.items:
    item = result.items[0]
    avg_deg = result.attributes.get('avg_degree', {}).get(item, 0)
    max_deg = result.attributes.get('max_degree', {}).get(item, 0)
    count = result.attributes.get('n', {}).get(item, 0)
    print(f"  avg_degree={avg_deg:.2f}, max_degree={max_deg}, n={count}")

# Final test: Complex query combining everything
print("\n" + "=" * 80)
print("Test 6: Complex Query - All Operations Together")
print("-" * 80)
result = (
    Q.nodes()                                      # 1. Node selection
    .where(layer="social")                         # 2. Filtering
    .compute("degree", "clustering")                # Compute attributes
    .mutate(                                        # 3. Mutations
        score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
        normalized_degree=lambda row: row.get("degree", 0) / 3.0
    )
    .execute(network)
)
print(f"✓ Complex query executed successfully with {result.count} nodes")
assert result.count == 3, "Should have 3 social nodes"
assert 'score' in result.attributes, "Should have 'score' attribute"
assert 'normalized_degree' in result.attributes, "Should have 'normalized_degree' attribute"

# Test to_pandas export
print("\n" + "=" * 80)
print("Test 7: Export to Pandas DataFrame")
print("-" * 80)
df = result.to_pandas()
print(f"✓ Exported to DataFrame with shape {df.shape}")
print("\nFirst few rows:")
print(df.head())

print("\n" + "=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print("\nBuilder DSL supports all 5 key operations:")
print("  1. ✓ Node selection (Q.nodes())")
print("  2. ✓ Edge selection (Q.edges())")
print("  3. ✓ Filtering (.where())")
print("  4. ✓ Mutations (.mutate())")
print("  5. ✓ Summary (.summarize())")
print("=" * 80)
