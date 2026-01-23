"""
Query Algebra: Basic Operations

This example demonstrates the basic algebraic operators for composing queries
and combining results in py3plex's DSL.

Topics covered:
- Union (|): Combine items from two queries
- Intersection (&): Keep only items in both queries
- Difference (-): Remove items from one query
- Symmetric difference (^): Items in exactly one query
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.algebra import IdentityStrategy

print("=" * 70)
print("Query Algebra: Basic Operations")
print("=" * 70)
print()

# Create a simple multilayer network
print("1. Creating a multilayer network...")
net = multinet.multi_layer_network(directed=False)

# Add nodes to multiple layers
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
    {'source': 'David', 'type': 'work'},
])

# Add edges
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
])

print(f"   Network: {len(list(net.get_nodes()))} nodes (replicas), {len(list(net.get_layers()))} layers")
print()

# Example 1: Union - Combine results from different layers
print("2. UNION: Combining nodes from different layers")
print("-" * 70)

social_nodes = Q.nodes().from_layers(L["social"]).execute(net)
work_nodes = Q.nodes().from_layers(L["work"]).execute(net)

print(f"   Social layer: {len(social_nodes.items)} nodes")
print(f"   Work layer: {len(work_nodes.items)} nodes")

# Set identity strategy to avoid ambiguity
social_nodes.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
work_nodes.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA

union = social_nodes | work_nodes
print(f"   Union (social | work): {len(union.items)} nodes")
print(f"   Nodes: {[item[0] for item in union.items]}")
print()

# Example 2: Intersection - Find nodes in both queries
print("3. INTERSECTION: Finding nodes in both results")
print("-" * 70)

all_nodes = Q.nodes().execute(net)
social_only = Q.nodes().from_layers(L["social"]).execute(net)

# Set identity
all_nodes.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
social_only.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA

intersection = all_nodes & social_only
print(f"   All nodes: {len(all_nodes.items)}")
print(f"   Social nodes: {len(social_only.items)}")
print(f"   Intersection: {len(intersection.items)} nodes")
print()

# Example 3: Difference - Remove nodes
print("4. DIFFERENCE: Removing nodes from a set")
print("-" * 70)

all_nodes = Q.nodes().execute(net)
work_only = Q.nodes().from_layers(L["work"]).execute(net)

# Set identity
all_nodes.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
work_only.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA

difference = all_nodes - work_only
print(f"   All nodes: {len(all_nodes.items)}")
print(f"   Work nodes: {len(work_only.items)}")
print(f"   Difference (all - work): {len(difference.items)} nodes (social only)")
print(f"   Nodes: {[item[0] for item in difference.items]}")
print()

# Example 4: Symmetric difference - Exclusive membership
print("5. SYMMETRIC DIFFERENCE: Nodes in exactly one set")
print("-" * 70)

social = Q.nodes().from_layers(L["social"]).execute(net)
work = Q.nodes().from_layers(L["work"]).execute(net)

# Set identity
social.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
work.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA

sym_diff = social ^ work
print(f"   Social nodes: {len(social.items)}")
print(f"   Work nodes: {len(work.items)}")
print(f"   Symmetric difference: {len(sym_diff.items)} nodes")
print(f"   (Nodes exclusive to one layer or the other)")
print()

# Example 5: Provenance tracking
print("6. PROVENANCE: Tracking algebraic operations")
print("-" * 70)

result = social | work
print(f"   Operation: {result.meta.get('algebra_operation')}")
print(f"   Operand counts: {result.meta.get('operand_counts')}")
print(f"   Result count: {result.meta.get('result_count')}")
print(f"   Identity strategy: {result.meta.get('identity_strategy')}")
print()

print("=" * 70)
print("Query algebra enables compositional reasoning over network queries!")
print("=" * 70)
