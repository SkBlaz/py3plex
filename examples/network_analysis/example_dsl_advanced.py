"""Example: Advanced DSL v2 Queries for Multilayer Networks

This example demonstrates advanced usage of DSL v2 Query Builder including:
- Working with real-world-like network structures
- Filtering based on computed centrality measures
- Combining multiple analysis operators
- Using DSL v2 for network comparison across layers
- Per-layer analysis and aggregations

DSL v2 patterns used:
- Q.nodes() query builder
- Layer algebra with L["layer"]
- Django-style lookups (degree__gt, layer__in)
- Per-layer grouping with .per_layer()
- Chained operations for complex analysis

This example aligns with AGENTS.md Golden Paths showing advanced multilayer
network analysis patterns. For basic DSL v2 examples, see example_dsl_queries.py.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("ADVANCED DSL V2 QUERIES FOR MULTILAYER NETWORKS")
print("=" * 80)

# Create a more complex multilayer network representing a transportation system
print("\n[1] Creating multi-modal transportation network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Define stations/stops
stations = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
layers = ['bus', 'metro', 'train']

# Add nodes for each station in each layer
nodes = []
for station in stations:
    for layer in layers:
        nodes.append({'source': station, 'type': layer})

network.add_nodes(nodes)

# Add edges representing connections
edges = [
    # Bus network (dense, connects many stations)
    {'source': 'A', 'target': 'B', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'B', 'target': 'C', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'C', 'target': 'D', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'D', 'target': 'E', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'A', 'target': 'C', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'B', 'target': 'D', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'E', 'target': 'F', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'F', 'target': 'G', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'G', 'target': 'H', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'H', 'target': 'I', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},
    {'source': 'I', 'target': 'J', 'source_type': 'bus', 'target_type': 'bus', 'weight': 1.0},

    # Metro network (fewer connections, major hubs)
    {'source': 'A', 'target': 'D', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},
    {'source': 'D', 'target': 'F', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},
    {'source': 'F', 'target': 'H', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},
    {'source': 'H', 'target': 'J', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},
    {'source': 'B', 'target': 'E', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},
    {'source': 'E', 'target': 'I', 'source_type': 'metro', 'target_type': 'metro', 'weight': 1.0},

    # Train network (long-distance, sparse)
    {'source': 'A', 'target': 'E', 'source_type': 'train', 'target_type': 'train', 'weight': 1.0},
    {'source': 'E', 'target': 'H', 'source_type': 'train', 'target_type': 'train', 'weight': 1.0},
    {'source': 'C', 'target': 'G', 'source_type': 'train', 'target_type': 'train', 'weight': 1.0},
    {'source': 'D', 'target': 'J', 'source_type': 'train', 'target_type': 'train', 'weight': 1.0},
]

network.add_edges(edges)

print(f"Network created: {network}")
print(f"Layers: {layers}")
print(f"Stations: {len(stations)}")
print(f"Total node-layer pairs: {len(list(network.get_nodes()))}")
print(f"Total connections: {len(list(network.get_edges()))}")

# Example 1: Find hub stations (high degree) in each layer using DSL v2
print("\n" + "=" * 80)
print("[2] Example 1: Identify hub stations in each transport layer")
print("-" * 80)

for layer in layers:
    print(f"\nLayer: {layer.upper()}")
    print(f"Query: Q.nodes().from_layers(L['{layer}']).where(degree__gt=1).compute('degree').execute(network)")
    
    result = Q.nodes().from_layers(L[layer]).where(degree__gt=1).compute('degree').execute(network)
    df = result.to_pandas()
    
    print(f"Hub stations (degree > 1): {len(df)}")
    for _, row in df.iterrows():
        print(f"  {row['id']}: degree={row['degree']}")

# Example 2: Compare betweenness centrality across layers
print("\n" + "=" * 80)
print("[3] Example 2: Compare betweenness centrality across layers")
print("-" * 80)

layer_centralities = {}
for layer in layers:
    print(f"\nAnalyzing {layer.upper()} layer...")
    print(f"Query: Q.nodes().from_layers(L['{layer}']).compute('betweenness_centrality').execute(network)")
    
    result = Q.nodes().from_layers(L[layer]).compute('betweenness_centrality').execute(network)
    df = result.to_pandas()
    
    # Show top 3 nodes
    top_3 = df.nlargest(3, 'betweenness_centrality')
    print("Top 3 by betweenness centrality:")
    for _, row in top_3.iterrows():
        print(f"  {row['id']}: {row['betweenness_centrality']:.4f}")

# Example 3: Find well-connected stations across all layers
print("\n" + "=" * 80)
print("[4] Example 3: Find well-connected stations (degree > 2 in any layer)")
print("-" * 80)
print("Query: Q.nodes().where(degree__gt=2).compute('degree').execute(network)")
print()

result = Q.nodes().where(degree__gt=2).compute('degree').execute(network)
df = result.to_pandas()
print(f"Found {len(df)} well-connected nodes:")
print(df[['id', 'layer', 'degree']].head(20).to_string(index=False))

# Example 4: Analysis of specific stations using grouping
print("\n" + "=" * 80)
print("[5] Example 4: Analyze specific hub stations (D, E, F, H)")
print("-" * 80)

hub_stations = ['D', 'E', 'F', 'H']
print("Query: Q.nodes().where(id__in=['D', 'E', 'F', 'H']).compute('degree').execute(network)")
print()

# Note: DSL v2 doesn't have id__in, so we'll query and filter
result = Q.nodes().compute('degree').execute(network)
df = result.to_pandas()
df_hubs = df[df['id'].isin(hub_stations)]

for station in hub_stations:
    print(f"\nStation {station} analysis:")
    station_df = df_hubs[df_hubs['id'] == station]
    for _, row in station_df.iterrows():
        print(f"  {row['layer']}: degree={row['degree']}")

# Example 5: Layer comparison using per-layer aggregation
print("\n" + "=" * 80)
print("[6] Example 5: Layer connectivity comparison (Advanced Pattern)")
print("-" * 80)
print("Query: Q.nodes().per_layer().compute('degree').execute(network)")
print()

result = Q.nodes().per_layer().compute('degree').execute(network)
df = result.to_pandas()

print("\nAverage degree per layer:")
for layer in layers:
    layer_df = df[df['layer'] == layer]
    avg_degree = layer_df['degree'].mean()
    print(f"  {layer}: {avg_degree:.2f}")

# Example 6: Find isolated or low-connectivity nodes
print("\n" + "=" * 80)
print("[7] Example 6: Find low-connectivity nodes (degree <= 1)")
print("-" * 80)
print("Query: Q.nodes().where(degree__lte=1).compute('degree').execute(network)")
print()

result = Q.nodes().where(degree__lte=1).compute('degree').execute(network)
df = result.to_pandas()
print(f"Found {len(df)} low-connectivity nodes:")
print(df[['id', 'layer', 'degree']].head(20).to_string(index=False))

# Example 7: Multiple centrality measures for major hubs
print("\n" + "=" * 80)
print("[8] Example 7: Comprehensive analysis of metro hubs")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['metro']).where(degree__gte=2)")
print("           .compute('degree', 'betweenness_centrality', 'closeness_centrality')")
print("           .execute(network)")
print()

result = (
    Q.nodes()
    .from_layers(L['metro'])
    .where(degree__gte=2)
    .compute('degree', 'betweenness_centrality', 'closeness_centrality')
    .execute(network)
)
df = result.to_pandas()

print(f"Metro hubs found: {len(df)}")
print("\nDetailed analysis:")
print(df[['id', 'degree', 'betweenness_centrality', 'closeness_centrality']].to_string(index=False))

# Example 8: Cross-layer analysis using Layer Algebra
print("\n" + "=" * 80)
print("[9] Example 8: Multi-layer analysis with Layer Algebra")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['*']).compute('degree').execute(network)")
print()

result = Q.nodes().from_layers(L['*']).compute('degree').execute(network)
df = result.to_pandas()

print("\nStations with high total degree across all layers:")
# Group by station and sum degrees
station_totals = df.groupby('id')['degree'].sum().sort_values(ascending=False)
print("\nTop stations by total degree across all layers:")
for station, total_degree in station_totals.head(5).items():
    print(f"  Station {station}: total degree = {total_degree}")

# Example 9: Using Layer Difference (exclusion pattern)
print("\n" + "=" * 80)
print("[10] Example 9: Find stations NOT in bus layer (Layer Algebra)")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['*'] - L['bus']).where(degree__gt=1).compute('degree').execute(network)")
print()

result = Q.nodes().from_layers(L['*'] - L['bus']).where(degree__gt=1).compute('degree').execute(network)
df = result.to_pandas()
print(f"Found {len(df)} high-degree nodes not in bus layer:")
print(df[['id', 'layer', 'degree']].head(15).to_string(index=False))

# Example 10: Complex query with Layer Union and chaining
print("\n" + "=" * 80)
print("[11] Example 10: Complex query - metro or train with sorted results")
print("-" * 80)
print("Query: Q.nodes().from_layers(L['metro'] + L['train'])")
print("           .compute('degree_centrality')")
print("           .order_by('degree_centrality', desc=True)")
print("           .limit(10)")
print("           .execute(network)")
print()

result = (
    Q.nodes()
    .from_layers(L['metro'] + L['train'])
    .compute('degree_centrality')
    .order_by('degree_centrality', desc=True)
    .limit(10)
    .execute(network)
)
df = result.to_pandas()
print(f"Top 10 nodes by degree centrality in metro/train:")
print(df[['id', 'layer', 'degree_centrality']].to_string(index=False))

# Summary
print("\n" + "=" * 80)
print("ADVANCED DSL V2 ANALYSIS COMPLETE")
print("=" * 80)
print("\nKey DSL v2 patterns demonstrated:")
print("  OK Q.nodes() - Query builder")
print("  OK .from_layers(L['layer']) - Single layer selection")
print("  OK .from_layers(L['a'] + L['b']) - Layer union")
print("  OK .from_layers(L['*'] - L['a']) - Layer exclusion")
print("  OK .where(attr__op=value) - Django-style filtering")
print("  OK .compute('metric1', 'metric2') - Multiple measures")
print("  OK .order_by('attr', desc=True) - Sorting")
print("  OK .limit(n) - Result limiting")
print("  OK .per_layer() - Grouped analysis")
print("  OK .to_pandas() - DataFrame export")
print("\nComparison operators:")
print("  __gt (>), __gte (>=), __lt (<), __lte (<=), __eq (=), __ne (!=)")
print("\nDSL v2 enables complex multilayer network analysis with chainable operations!")
print("\nFor more patterns, see AGENTS.md Golden Paths")

