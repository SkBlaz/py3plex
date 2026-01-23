"""
Query Algebra: Verification and Assertions

This example demonstrates using query algebra for scientific validation,
including subset checks, non-empty assertions, and disjoint verification.

Topics covered:
- Q.assert_subset(): Verify subset relationships
- Q.assert_nonempty(): Ensure queries return results
- Q.assert_disjoint(): Check for exclusive sets
- Use cases for regression testing and monotonicity checks
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 70)
print("Query Algebra: Verification and Assertions")
print("=" * 70)
print()

# Create a simple multilayer network
print("1. Creating a multilayer network...")
net = multinet.multi_layer_network(directed=False)

# Add nodes with varying degrees
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'David', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
])

# Add edges to create different degrees
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
])

print(f"   Network: {len(net.get_nodes())} nodes (replicas), {len(net.get_layers())} layers")
print()

# Example 1: Monotonicity verification - Filtering reduces results
print("2. MONOTONICITY CHECK: Filtering should reduce results")
print("-" * 70)

all_nodes = Q.nodes()
filtered = Q.nodes().where(degree__gt=1)

print("   Verifying that filtered ⊆ all_nodes...")
try:
    Q.assert_subset(filtered, all_nodes, net)
    print("   ✓ Monotonicity verified: filtered is subset of all_nodes")
except AssertionError as e:
    print(f"   ✗ Monotonicity violation: {e}")
print()

# Example 2: Non-empty intersection validation
print("3. NON-EMPTY CHECK: Ensuring meaningful intersections")
print("-" * 70)

social = Q.nodes().from_layers(L["social"])
high_degree = Q.nodes().where(degree__gt=1)

intersection = social & high_degree

print("   Checking if intersection is meaningful...")
try:
    Q.assert_nonempty(intersection, net, 
                      message="No high-degree nodes in social layer")
    print("   ✓ Intersection is non-empty")
    
    # Execute and show results
    result = intersection.execute(net)
    print(f"   Result: {len(result.items)} nodes")
except AssertionError as e:
    print(f"   ✗ Intersection is empty: {e}")
print()

# Example 3: Disjoint verification - Exclusive partitions
print("4. DISJOINT CHECK: Verifying exclusive layer membership")
print("-" * 70)

social_only = Q.nodes().from_layers(L["social"])
work_only = Q.nodes().from_layers(L["work"])

print("   Checking if layers are disjoint (by replica)...")
try:
    Q.assert_disjoint(social_only, work_only, net, identity="by_replica")
    print("   ✓ Layers are disjoint (by replica)")
except AssertionError as e:
    print(f"   ✗ Layers overlap: {e}")
print()

# Example 4: Scientific claim validation
print("5. SCIENTIFIC CLAIM: High degree implies high betweenness?")
print("-" * 70)

print("   Claim: 'High-degree nodes always have high betweenness'")
print("   (This is often FALSE, so we expect a counterexample)")

high_degree = Q.nodes().where(degree__gt=2)
# Note: Would need betweenness computed for real test
# high_betweenness = Q.nodes().where(betweenness_centrality__gt=0.2)

print("   Testing subset relationship...")
try:
    # This would test: high_degree ⊆ high_betweenness
    # Q.assert_subset(high_degree, high_betweenness, net)
    print("   (Skipped - requires betweenness computation)")
    print("   In practice: Often finds counterexamples!")
except AssertionError as e:
    print(f"   ✗ Claim falsified: {e}")
print()

# Example 5: Regression testing
print("6. REGRESSION TEST: Query behavior consistency")
print("-" * 70)

print("   Regression test: Ensure filtering still works as expected")

# Define expected behavior
all_count_before = len(Q.nodes().execute(net).items)
filtered_count_before = len(Q.nodes().where(degree__gt=1).execute(net).items)

print(f"   All nodes: {all_count_before}")
print(f"   Filtered (degree > 1): {filtered_count_before}")

# Verify subset relationship
Q.assert_subset(
    Q.nodes().where(degree__gt=1),
    Q.nodes(),
    net
)
print("   ✓ Regression test passed: Filtering behavior consistent")
print()

# Example 6: Coverage analysis with assertions
print("7. COVERAGE ANALYSIS: Measuring layer overlap")
print("-" * 70)

social_result = Q.nodes().from_layers(L["social"]).execute(net)
work_result = Q.nodes().from_layers(L["work"]).execute(net)

# Set identity for by_id comparison
from py3plex.dsl.algebra import IdentityStrategy
social_result.meta['identity_strategy'] = IdentityStrategy.BY_ID
work_result.meta['identity_strategy'] = IdentityStrategy.BY_ID

overlap = social_result & work_result
print(f"   Social layer: {len(social_result.items)} nodes")
print(f"   Work layer: {len(work_result.items)} nodes")
print(f"   Overlap (by node ID): {len(overlap.items)} nodes")

# Verify overlap is non-empty
try:
    Q.assert_nonempty(overlap, message="No nodes appear in both layers")
    print("   ✓ Layers share common nodes")
except AssertionError:
    print("   ✗ Layers are completely disjoint")
print()

print("=" * 70)
print("Query algebra assertions enable scientific validation!")
print("=" * 70)
