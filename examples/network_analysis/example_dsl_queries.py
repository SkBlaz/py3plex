"""Example: DSL v2 Query Builder for Multilayer Network Analysis

This example demonstrates the preferred DSL v2 Query Builder API for querying
and analyzing multilayer networks using the modern Q builder pattern.

DSL v2 Features:
- Chainable builder API: Q.nodes().where(...).compute(...).execute()
- Type-safe with IDE autocomplete support
- Django-style lookups (degree__gt, layer__in, etc.)
- Layer algebra: L["social"] + L["work"]
- Native UQ integration with .uq()
- Better error messages and provenance tracking

This example aligns with AGENTS.md Golden Paths and shows the preferred patterns
for network analysis in py3plex. For legacy string DSL, see documentation.

Examples cover:
1. Basic node selection by layer
2. Filtering by degree with comparison operators
3. Complex queries with layer algebra
4. Computing centrality measures
5. Chaining operations for advanced analysis
6. Using pandas export for data analysis
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("DSL V2 QUERY BUILDER FOR MULTILAYER NETWORK ANALYSIS")
print("=" * 80)

# Create a sample multilayer network
print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes to multiple layers
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'David', 'type': 'social'},
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
    {'source': 'Charlie', 'type': 'work'},
    {'source': 'Alice', 'type': 'transport'},
    {'source': 'Bob', 'type': 'transport'},
    {'source': 'David', 'type': 'transport'},
    {'source': 'Eve', 'type': 'transport'},
]

network.add_nodes(nodes)

# Add edges within and across layers
edges = [
    # Social layer connections
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},

    # Work layer connections
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},

    # Transport layer connections
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
    {'source': 'Bob', 'target': 'David', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Eve', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
    {'source': 'David', 'target': 'Eve', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
]

network.add_edges(edges)

print(f"Network created: {network}")
print(f"Total nodes: {len(list(network.get_nodes()))}")
print(f"Total edges: {len(list(network.get_edges()))}")

# Example 1: Select all nodes in a specific layer
print("\n" + "=" * 80)
print("[2] Example 1: Select all nodes in 'social' layer")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['social']).execute(network)")
print()

result = Q.nodes().from_layers(L['social']).execute(network)
print(f"Found {result.count} nodes in 'social' layer:")
for node in result.items[:5]:  # Show first 5
    print(f"  - {node}")
if result.count > 5:
    print(f"  ... and {result.count - 5} more")

# Example 2: Select nodes with high degree
print("\n" + "=" * 80)
print("[3] Example 2: Select nodes with degree > 2")
print("-" * 80)
print("Query: Q.nodes().where(degree__gt=2).execute(network)")
print()

result = Q.nodes().where(degree__gt=2).execute(network)
print(f"Found {result.count} nodes with degree > 2:")
for node in result.items[:5]:
    print(f"  - {node}")
if result.count > 5:
    print(f"  ... and {result.count - 5} more")

# Example 3: Combine layer and degree filters
print("\n" + "=" * 80)
print("[4] Example 3: Select high-degree nodes in 'transport' layer")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['transport']).where(degree__gt=1).execute(network)")
print()

result = Q.nodes().from_layers(L['transport']).where(degree__gt=1).execute(network)
print(f"Found {result.count} nodes:")
for node in result.items:
    print(f"  - {node}")

# Example 4: Use layer algebra for multiple layers
print("\n" + "=" * 80)
print("[5] Example 4: Select nodes in 'social' OR 'work' layer (Layer Algebra)")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['social'] + L['work']).execute(network)")
print()

result = Q.nodes().from_layers(L['social'] + L['work']).execute(network)
print(f"Found {result.count} nodes in social or work layers")
# Group by layer for clarity
df = result.to_pandas()
print(f"\nBreakdown by layer:")
print(df['layer'].value_counts())

# Example 5: Compute centrality for filtered nodes
print("\n" + "=" * 80)
print("[6] Example 5: Compute betweenness centrality for 'social' layer")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['social']).compute('betweenness_centrality').execute(network)")
print()

result = Q.nodes().from_layers(L['social']).compute('betweenness_centrality').execute(network)
df = result.to_pandas()
print(f"Computed betweenness for {len(df)} nodes:")
print(df[['id', 'layer', 'betweenness_centrality']].sort_values('betweenness_centrality', ascending=False).head())

# Example 6: Multiple measures with chaining
print("\n" + "=" * 80)
print("[7] Example 6: Compute multiple measures and sort")
print("-" * 80)
print("Query: Q.nodes().where(degree__gt=2).compute('degree_centrality', 'closeness_centrality')")
print("           .order_by('degree_centrality', desc=True).limit(5).execute(network)")
print()

result = (
    Q.nodes()
    .where(degree__gt=2)
    .compute('degree_centrality', 'closeness_centrality')
    .order_by('degree_centrality', desc=True)
    .limit(5)
    .execute(network)
)
df = result.to_pandas()
print(f"Top 5 nodes by degree centrality:")
print(df[['id', 'layer', 'degree_centrality', 'closeness_centrality']])

# Example 7: Per-layer analysis with grouping
print("\n" + "=" * 80)
print("[8] Example 7: Per-layer top nodes (Advanced Pattern)")
print("-" * 80)
print("Query: Q.nodes().per_layer().compute('degree')")
print("           .order_by('degree', desc=True).execute(network)")
print()

result = (
    Q.nodes()
    .per_layer()
    .compute('degree')
    .execute(network)
)
df = result.to_pandas()
print(f"Nodes grouped by layer:")
# Show top 3 per layer
for layer in df['layer'].unique():
    layer_df = df[df['layer'] == layer].nlargest(3, 'degree')
    print(f"\nTop 3 in layer '{layer}':")
    print(layer_df[['id', 'degree']].to_string(index=False))

# Example 8: Complex query with degree range
print("\n" + "=" * 80)
print("[9] Example 8: Nodes with degree between 2 and 4")
print("-" * 80)
print("Query: Q.nodes().where(degree__gte=2, degree__lte=4).execute(network)")
print()

result = Q.nodes().where(degree__gte=2, degree__lte=4).execute(network)
print(f"Found {result.count} nodes with 2 <= degree <= 4:")
for node in result.items[:10]:
    print(f"  - {node}")
if result.count > 10:
    print(f"  ... and {result.count - 10} more")

# Example 9: All nodes with pandas export
print("\n" + "=" * 80)
print("[10] Example 9: Export all nodes to pandas DataFrame")
print("-" * 80)
print("Query: Q.nodes().execute(network).to_pandas()")
print()

result = Q.nodes().execute(network)
df = result.to_pandas()
print(f"Total nodes: {len(df)}")
print(f"\nDataFrame preview:")
print(df.head(10))

# Example 10: Compute degree for all nodes
print("\n" + "=" * 80)
print("[11] Example 10: Compute degree for all nodes")
print("-" * 80)
print("Query: Q.nodes().compute('degree').execute(network)")
print()

result = Q.nodes().compute('degree').execute(network)
df = result.to_pandas()
print(f"Degree statistics:")
print(df['degree'].describe())

# Example 11: Layer difference (exclusion pattern)
print("\n" + "=" * 80)
print("[12] Example 11: Exclude a layer using Layer Algebra")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['*'] - L['social']).execute(network)")
print()

result = Q.nodes().from_layers(L['*'] - L['social']).execute(network)
print(f"Found {result.count} nodes NOT in 'social' layer:")
df = result.to_pandas()
print(f"Layers present: {df['layer'].unique()}")

# Example 12: Clustering coefficient
print("\n" + "=" * 80)
print("[13] Example 12: Compute clustering coefficient for social layer")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['social']).compute('clustering').execute(network)")
print()

result = Q.nodes().from_layers(L['social']).compute('clustering').execute(network)
df = result.to_pandas()
print(f"Clustering coefficient for social layer:")
print(df[['id', 'clustering']].sort_values('clustering', ascending=False).head())

# Example 13: PageRank computation
print("\n" + "=" * 80)
print("[14] Example 13: Compute PageRank for all nodes")
print("-" * 80)
print("Query: Q.nodes().compute('pagerank').order_by('pagerank', desc=True).limit(5).execute(network)")
print()

result = (
    Q.nodes()
    .compute('pagerank')
    .order_by('pagerank', desc=True)
    .limit(5)
    .execute(network)
)
df = result.to_pandas()
print(f"Top 5 nodes by PageRank:")
print(df[['id', 'layer', 'pagerank']])

# Summary
print("\n" + "=" * 80)
print("DSL V2 QUERY EXAMPLES COMPLETE")
print("=" * 80)
print("\nKey DSL v2 Patterns Demonstrated:")
print("  OK Q.nodes() - Node query builder")
print("  OK .from_layers(L[...]) - Layer filtering with algebra")
print("  OK .where(attr__op=value) - Django-style filtering")
print("  OK .compute('metric') - Centrality computation")
print("  OK .order_by('attr', desc=True) - Sorting")
print("  OK .limit(n) - Result limiting")
print("  OK .per_layer() - Grouped analysis")
print("  OK .to_pandas() - Export to DataFrame")
print("\nComparison operators in .where():")
print("  __gt (>), __gte (>=), __lt (<), __lte (<=), __eq (=), __ne (!=)")
print("\nAvailable measures for .compute():")
print("  degree, degree_centrality, betweenness_centrality")
print("  closeness_centrality, eigenvector_centrality, pagerank, clustering")
print("\nFor more patterns, see AGENTS.md Golden Paths")

