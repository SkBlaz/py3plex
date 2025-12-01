"""Example: SQL-like DSL for Multilayer Network Queries

This example demonstrates the Domain-Specific Language (DSL) for querying
and analyzing multilayer networks using SQL-like syntax.

The DSL supports:
- SELECT nodes/edges with filtering conditions
- WHERE clauses with logical operators (AND, OR, NOT)
- Comparison operators (>, <, =, >=, <=, !=)
- COMPUTE clauses for analytical measures
- Layer-based filtering
- Degree and centrality-based filtering

Examples cover:
1. Basic node selection by layer
2. Filtering by degree
3. Complex queries with multiple conditions
4. Computing centrality measures
5. Using convenience functions
"""

from py3plex.core import multinet
from py3plex.dsl import (
    execute_query,
    format_result,
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer,
)

print("=" * 80)
print("SQL-LIKE DSL FOR MULTILAYER NETWORK QUERIES")
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
print("Query: SELECT nodes WHERE layer=\"social\"")
print()

result = execute_query(network, 'SELECT nodes WHERE layer="social"')
print(format_result(result))

# Example 2: Select nodes with high degree
print("\n" + "=" * 80)
print("[3] Example 2: Select nodes with degree > 2")
print("-" * 80)
print("Query: SELECT nodes WHERE degree > 2")
print()

result = execute_query(network, 'SELECT nodes WHERE degree > 2')
print(format_result(result))

# Example 3: Combine layer and degree filters with AND
print("\n" + "=" * 80)
print("[4] Example 3: Select high-degree nodes in 'transport' layer")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"transport\" AND degree > 1")
print()

result = execute_query(network, 'SELECT nodes WHERE layer="transport" AND degree > 1')
print(format_result(result))

# Example 4: Use OR operator
print("\n" + "=" * 80)
print("[5] Example 4: Select nodes in 'social' OR 'work' layer")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"social\" OR layer=\"work\"")
print()

result = execute_query(network, 'SELECT nodes WHERE layer="social" OR layer="work"')
print(format_result(result, limit=15))

# Example 5: Compute centrality for filtered nodes
print("\n" + "=" * 80)
print("[6] Example 5: Compute betweenness centrality for 'social' layer")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"social\" COMPUTE betweenness_centrality")
print()

result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality')
print(format_result(result))

# Example 6: Multiple measures
print("\n" + "=" * 80)
print("[7] Example 6: Compute multiple measures for high-degree nodes")
print("-" * 80)
print("Query: SELECT nodes WHERE degree > 2 COMPUTE degree_centrality closeness_centrality")
print()

result = execute_query(network, 'SELECT nodes WHERE degree > 2 COMPUTE degree_centrality closeness_centrality')
print(format_result(result))

# Example 7: Using convenience functions
print("\n" + "=" * 80)
print("[8] Example 7: Using convenience functions")
print("-" * 80)

print("\na) Select nodes by layer:")
social_nodes = select_nodes_by_layer(network, 'social')
print(f"   Nodes in 'social' layer: {len(social_nodes)}")
print(f"   {social_nodes}")

print("\nb) Select high-degree nodes:")
high_degree_nodes = select_high_degree_nodes(network, min_degree=3)
print(f"   Nodes with degree > 3: {len(high_degree_nodes)}")
print(f"   {high_degree_nodes}")

print("\nc) Compute centrality for layer:")
centrality = compute_centrality_for_layer(network, 'transport', 'degree_centrality')
print(f"   Degree centrality for 'transport' layer:")
for node, value in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
    print(f"     {node}: {value:.4f}")

# Example 8: Complex query with degree range
print("\n" + "=" * 80)
print("[9] Example 8: Complex query - nodes with degree between 2 and 4")
print("-" * 80)
print("Query: SELECT nodes WHERE degree >= 2 AND degree <= 4")
print()

result = execute_query(network, 'SELECT nodes WHERE degree >= 2 AND degree <= 4')
print(format_result(result, limit=20))

# Example 9: All nodes (no filter)
print("\n" + "=" * 80)
print("[10] Example 9: Select all nodes (no WHERE clause)")
print("-" * 80)
print("Query: SELECT nodes")
print()

result = execute_query(network, 'SELECT nodes')
print(format_result(result, limit=15))

# Example 10: Compute degree for all nodes
print("\n" + "=" * 80)
print("[11] Example 10: Compute degree for all nodes")
print("-" * 80)
print("Query: SELECT nodes COMPUTE degree")
print()

result = execute_query(network, 'SELECT nodes COMPUTE degree')
print(format_result(result, limit=15))

# Example 11: Using NOT operator
print("\n" + "=" * 80)
print("[12] Example 11: Using NOT operator to exclude a layer")
print("-" * 80)
print("Query: SELECT nodes WHERE NOT layer=\"social\"")
print()

result = execute_query(network, 'SELECT nodes WHERE NOT layer="social"')
print(format_result(result, limit=15))

# Example 12: Filtering by centrality measures
print("\n" + "=" * 80)
print("[13] Example 12: Filter nodes by betweenness centrality")
print("-" * 80)
print("Query: SELECT nodes WHERE betweenness >= 0 COMPUTE betweenness_centrality")
print()

result = execute_query(network, 'SELECT nodes WHERE betweenness >= 0 COMPUTE betweenness_centrality')
print(format_result(result, limit=10))

# Example 13: Clustering coefficient
print("\n" + "=" * 80)
print("[14] Example 13: Compute clustering coefficient for nodes")
print("-" * 80)
print("Query: SELECT nodes WHERE layer=\"social\" COMPUTE clustering")
print()

result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE clustering')
print(format_result(result, limit=10))

# Example 14: PageRank computation
print("\n" + "=" * 80)
print("[15] Example 14: Compute PageRank for all nodes")
print("-" * 80)
print("Query: SELECT nodes COMPUTE pagerank")
print()

result = execute_query(network, 'SELECT nodes COMPUTE pagerank')
print(format_result(result, limit=10))

# Summary
print("\n" + "=" * 80)
print("DSL QUERY EXAMPLES COMPLETE")
print("=" * 80)
print("\nSupported DSL syntax:")
print("  SELECT nodes|edges [WHERE conditions] [COMPUTE measures]")
print("\nWHERE conditions:")
print("  - layer = \"value\"")
print("  - degree >/</>=/<=/=/!= value")
print("  - betweenness/closeness/eigenvector >= value")
print("  - Logical: AND, OR, NOT")
print("\nCOMPUTE measures:")
print("  - degree, degree_centrality")
print("  - betweenness_centrality, closeness_centrality")
print("  - eigenvector_centrality, pagerank")
print("  - clustering")
print("\nFor more information, see: py3plex.dsl module documentation")
