"""Example: Advanced DSL Queries for Multilayer Networks

This example demonstrates advanced usage of the DSL including:
- Working with real-world-like network structures
- Filtering based on computed centrality measures
- Combining multiple analysis operators
- Using DSL for network comparison across layers
"""

from py3plex.core import multinet
from py3plex.dsl import execute_query, format_result

print("=" * 80)
print("ADVANCED DSL QUERIES FOR MULTILAYER NETWORKS")
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

# Example 1: Find hub stations (high degree) in each layer
print("\n" + "=" * 80)
print("[2] Example 1: Identify hub stations in each transport layer")
print("-" * 80)

for layer in layers:
    print(f"\nLayer: {layer.upper()}")
    print(f"Query: SELECT nodes WHERE layer=\"{layer}\" AND degree > 1")
    result = execute_query(network, f'SELECT nodes WHERE layer="{layer}" AND degree > 1')
    print(f"Hub stations (degree > 1): {len(result['nodes'])}")
    for node in result['nodes']:
        degree = network.core_network.degree(node)
        print(f"  {node}: degree={degree}")

# Example 2: Compare betweenness centrality across layers
print("\n" + "=" * 80)
print("[3] Example 2: Compare betweenness centrality across layers")
print("-" * 80)

layer_centralities = {}
for layer in layers:
    print(f"\nAnalyzing {layer.upper()} layer...")
    result = execute_query(
        network,
        f'SELECT nodes WHERE layer="{layer}" COMPUTE betweenness_centrality'
    )
    layer_centralities[layer] = result['computed']['betweenness_centrality']

    # Show top 3 nodes
    sorted_nodes = sorted(
        layer_centralities[layer].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    print("Top 3 by betweenness centrality:")
    for node, centrality in sorted_nodes:
        print(f"  {node}: {centrality:.4f}")

# Example 3: Find well-connected stations across all layers
print("\n" + "=" * 80)
print("[4] Example 3: Find well-connected stations (degree > 2 in any layer)")
print("-" * 80)
print("Query: SELECT nodes WHERE degree > 2")
print()

result = execute_query(network, 'SELECT nodes WHERE degree > 2')
print(format_result(result, limit=20))

# Example 4: Analysis of specific stations
print("\n" + "=" * 80)
print("[5] Example 4: Analyze specific hub stations (D, E, F, H)")
print("-" * 80)

hub_stations = ['D', 'E', 'F', 'H']
for station in hub_stations:
    print(f"\nStation {station} analysis:")
    for layer in layers:
        # Find this specific node-layer pair
        node = (station, layer)
        if node in list(network.get_nodes()):
            degree = network.core_network.degree(node)
            print(f"  {layer}: degree={degree}")

# Example 5: Layer comparison - which layer is most connected?
print("\n" + "=" * 80)
print("[6] Example 5: Layer connectivity comparison")
print("-" * 80)

print("\nAverage degree per layer:")
for layer in layers:
    result = execute_query(network, f'SELECT nodes WHERE layer="{layer}" COMPUTE degree')
    degrees = result['computed']['degree']
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
    print(f"  {layer}: {avg_degree:.2f}")

# Example 6: Find isolated or low-connectivity nodes
print("\n" + "=" * 80)
print("[7] Example 6: Find low-connectivity nodes (degree <= 1)")
print("-" * 80)
print("Query: SELECT nodes WHERE degree <= 1")
print()

result = execute_query(network, 'SELECT nodes WHERE degree <= 1')
print(format_result(result, limit=20))

# Example 7: Multiple centrality measures for major hubs
print("\n" + "=" * 80)
print("[8] Example 7: Comprehensive analysis of metro hubs")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"metro\" AND degree >= 2")
print("       COMPUTE degree betweenness_centrality closeness_centrality")
print()

result = execute_query(
    network,
    'SELECT nodes WHERE layer="metro" AND degree >= 2 COMPUTE degree betweenness_centrality closeness_centrality'
)

print(f"Metro hubs found: {result['count']}")
print("\nDetailed analysis:")
for node in result['nodes']:
    print(f"\n  {node}:")
    for measure, values in result['computed'].items():
        if node in values:
            print(f"    {measure}: {values[node]:.4f}")

# Example 8: Cross-layer analysis
print("\n" + "=" * 80)
print("[9] Example 8: Cross-layer station importance")
print("-" * 80)

print("\nStations appearing in all layers with high connectivity:")
station_scores = {}

for station in stations:
    total_degree = 0
    present_in_layers = 0

    for layer in layers:
        node = (station, layer)
        if node in list(network.get_nodes()):
            degree = network.core_network.degree(node)
            total_degree += degree
            present_in_layers += 1

    if present_in_layers == len(layers):  # Present in all layers
        station_scores[station] = total_degree

# Show top stations
sorted_stations = sorted(station_scores.items(), key=lambda x: x[1], reverse=True)
print("\nTop stations by total degree across all layers:")
for station, score in sorted_stations[:5]:
    print(f"  Station {station}: total degree = {score}")

# Example 9: Using NOT operator to exclude layers
print("\n" + "=" * 80)
print("[9] Example 9: Find stations NOT in bus layer")
print("-" * 80)
print("Query: SELECT nodes WHERE NOT layer=\"bus\" AND degree > 1")
print()

result = execute_query(network, 'SELECT nodes WHERE NOT layer="bus" AND degree > 1')
print(format_result(result, limit=15))

# Example 10: Complex conditional query with multiple conditions
print("\n" + "=" * 80)
print("[10] Example 10: Complex query - metro or train with high degree")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"metro\" OR layer=\"train\" COMPUTE degree_centrality")
print()

result = execute_query(
    network,
    'SELECT nodes WHERE layer="metro" OR layer="train" COMPUTE degree_centrality'
)
print(format_result(result, limit=15))

# Summary
print("\n" + "=" * 80)
print("ADVANCED DSL ANALYSIS COMPLETE")
print("=" * 80)
print("\nKey insights demonstrated:")
print("  ✓ Layer-specific hub identification")
print("  ✓ Cross-layer centrality comparison")
print("  ✓ Multi-measure node analysis")
print("  ✓ Network connectivity patterns")
print("  ✓ Comprehensive station importance ranking")
print("  ✓ Using NOT operator for layer exclusion")
print("  ✓ Complex conditional queries with OR")
print("\nThe DSL enables complex multilayer network analysis with simple queries!")
