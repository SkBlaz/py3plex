"""Example: Builder DSL Mutate Operations

This example demonstrates the .mutate() method in the DSL v2 builder API.
The mutate operation creates new columns or transforms existing ones using
lambda functions or simple expressions, similar to dplyr::mutate in R.

Key Features:
- Row-by-row transformations (not aggregations)
- Support for lambda functions
- Access to all existing attributes in transformations
- Chainable with other DSL operations
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("BUILDER DSL: MUTATE OPERATIONS")
print("=" * 80)

# Create a sample multilayer network
print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes across multiple layers
people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']
layers = ['social', 'work']

nodes = []
for person in people:
    for layer in layers:
        nodes.append({'source': person, 'type': layer})

network.add_nodes(nodes)

# Add edges
edges = [
    # Social network (highly connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},

    # Work network (moderately connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Charlie', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
]

network.add_edges(edges)

print(f"Network created with {len(people)} people across {len(layers)} layers")
print(f"Total node-layer pairs: {len(nodes)}")
print(f"Total edges: {len(edges)}")

# Example 1: Simple transformations
print("\n" + "=" * 80)
print("[2] Example 1: Simple Column Transformations")
print("-" * 80)
print("Code:")
print(" Q.nodes().compute('degree').mutate(")
print(" doubled_degree=lambda row: row.get('degree', 0) * 2,")
print(" degree_plus_ten=lambda row: row.get('degree', 0) + 10")
print(" ).execute(network)")
print()

result = Q.nodes().compute("degree").mutate(
    doubled_degree=lambda row: row.get("degree", 0) * 2,
    degree_plus_ten=lambda row: row.get("degree", 0) + 10
).execute(network)

df = result.to_pandas()
print("First 10 rows:")
print(df.head(10))

# Example 2: Computed scores from multiple attributes
print("\n" + "=" * 80)
print("[3] Example 2: Computing Derived Metrics")
print("-" * 80)
print("Code:")
print(" Q.nodes().compute('degree', 'clustering').mutate(")
print(" hub_score=lambda row: row.get('degree', 0) * row.get('clustering', 0),")
print(" is_hub=lambda row: row.get('degree', 0) > 2,")
print(" normalized_degree=lambda row: row.get('degree', 0) / 5.0")
print(" ).execute(network)")
print()

result = Q.nodes().compute("degree", "clustering").mutate(
    hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
    is_hub=lambda row: row.get("degree", 0) > 2,
    normalized_degree=lambda row: row.get("degree", 0) / 5.0
).execute(network)

df = result.to_pandas()
print("Top 10 nodes by hub_score:")
print(df.nlargest(10, 'hub_score')[['id', 'layer', 'degree', 'clustering', 'hub_score', 'is_hub']])

# Example 3: Filtering on mutated columns
print("\n" + "=" * 80)
print("[4] Example 3: Mutate + Filter Pipeline")
print("-" * 80)
print("Code:")
print(" Q.nodes().compute('degree').mutate(")
print(" score=lambda row: row.get('degree', 0) * 2")
print(" ).execute(network)")
print(" # Then filter the DataFrame")
print()

result = Q.nodes().compute("degree").mutate(
    score=lambda row: row.get("degree", 0) * 2
).execute(network)

df = result.to_pandas()
high_score = df[df['score'] > 4]
print(f"Nodes with score > 4: {len(high_score)}")
print(high_score[['id', 'layer', 'degree', 'score']].head(10))

# Example 4: Per-layer analysis with mutate
print("\n" + "=" * 80)
print("[5] Example 4: Per-Layer Analysis with Mutate")
print("-" * 80)
print("Code:")
print(" Q.nodes().where(layer='social').compute('degree').mutate(")
print(" category=lambda row: 'hub' if row.get('degree', 0) > 2 else 'peripheral'")
print(" ).execute(network)")
print()

result = Q.nodes().where(layer="social").compute("degree").mutate(
    category=lambda row: "hub" if row.get("degree", 0) > 2 else "peripheral"
).execute(network)

df = result.to_pandas()
print("Social layer categorization:")
print(df[['id', 'degree', 'category']].sort_values('degree', ascending=False))

# Example 5: Complex transformations
print("\n" + "=" * 80)
print("[6] Example 5: Complex Multi-Column Transformations")
print("-" * 80)
print("Code:")
print(" Q.nodes().compute('degree', 'betweenness_centrality', 'clustering').mutate(")
print(" influence=lambda row: (")
print(" row.get('degree', 0) * 0.4 + ")
print(" row.get('betweenness_centrality', 0) * 0.4 + ")
print(" row.get('clustering', 0) * 0.2")
print(" ),")
print(" rank=lambda row: 'high' if row.get('degree', 0) > 3 else 'medium' if row.get('degree', 0) > 1 else 'low'")
print(" ).execute(network)")
print()

result = Q.nodes().compute("degree", "betweenness_centrality", "clustering").mutate(
    influence=lambda row: (
        row.get("degree", 0) * 0.4 +
        row.get("betweenness_centrality", 0) * 0.4 +
        row.get("clustering", 0) * 0.2
    ),
    rank=lambda row: "high" if row.get("degree", 0) > 3 else "medium" if row.get("degree", 0) > 1 else "low"
).execute(network)

df = result.to_pandas()
print("Top 10 most influential nodes:")
print(df.nlargest(10, 'influence')[['id', 'layer', 'degree', 'betweenness_centrality', 'influence', 'rank']])

# Summary
print("\n" + "=" * 80)
print("SUMMARY: MUTATE OPERATIONS")
print("=" * 80)
print("\nKey Capabilities Demonstrated:")
print(" Simple arithmetic transformations")
print(" Multi-attribute calculations")
print(" Conditional expressions")
print(" Boolean flags")
print(" Normalization and scaling")
print(" Complex scoring functions")
print("\nBest Practices:")
print(" • Use mutate() for row-by-row transformations")
print(" • Use summarize()/aggregate() for group-level aggregations")
print(" • Chain mutate() with other DSL operations (where, compute, etc.)")
print(" • Export to pandas for advanced filtering on mutated columns")
print("\nFor more information:")
print(" • Documentation: docfiles/user_guide/dsl.rst")
print(" • Builder API examples: example_dsl_builder_api.py")
print(" • dplyr-style operations: example_dsl_dplyr_operations.py")
print("=" * 80)
