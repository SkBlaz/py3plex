"""Example: Using .explain() to add explanations to DSL query results.

This example demonstrates the .explain() DSL predicate that enriches query results
with additional context about nodes:
- Community membership and size
- Top neighbors by weight or degree
- Layer footprint (which layers the node appears in)

Explanations are computed efficiently on the final result set (after filters/limits).
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create a sample multilayer network
network = multinet.multi_layer_network(directed=False)

# Add nodes across multiple layers
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
    {'source': 'Dave', 'type': 'social'},
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},  # Alice appears in both layers
    {'source': 'Bob', 'type': 'work'},
    {'source': 'Frank', 'type': 'work'},
]
network.add_nodes(nodes)

# Add edges with weights
edges = [
    # Social layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
    {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Carol', 'target': 'Dave', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Dave', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social', 'weight': 0.5},
    # Work layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 3.0},
    {'source': 'Bob', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work', 'weight': 2.5},
    {'source': 'Alice', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work', 'weight': 1.5},
]
network.add_edges(edges)

print("=" * 80)
print("Example 1: Basic explain() usage with default explanations")
print("=" * 80)

# Query nodes with explanations
result = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("degree")
    .order_by("degree", desc=True)
    .limit(5)
    .explain(neighbors_top=3)  # Add explanations with top 3 neighbors
    .execute(network)
)

# Export to pandas with expanded explanations
df = result.to_pandas(expand_explanations=True)

print("\nNodes with explanations:")
print(df[['id', 'layer', 'degree', 'top_neighbors', 'layers_present', 'n_layers_present']])
print()

print("=" * 80)
print("Example 2: Custom explanation blocks")
print("=" * 80)

# Query with only specific explanation blocks
result = (
    Q.nodes()
    .from_layers(L["social"] + L["work"])
    .compute("degree")
    .per_layer()
    .explain(
        include=["top_neighbors", "layer_footprint"],  # Only these blocks
        neighbors_top=2,  # Top 2 neighbors
        neighbors={"metric": "weight", "scope": "layer"}  # Rank by weight, per-layer
    )
    .execute(network)
)

df = result.to_pandas(expand_explanations=True)

print("\nPer-layer results with custom explanations:")
print(df[['id', 'layer', 'degree', 'top_neighbors', 'n_layers_present']])
print()

print("=" * 80)
print("Example 3: Flagship usage pattern from the issue")
print("=" * 80)

# The flagship usage: explanations with all blocks
result = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("degree", "betweenness_centrality")
    .limit(20)
    .explain(
        neighbors_top=10,
        include=["community", "top_neighbors", "layer_footprint"]
    )
    .execute(network)
)

df = result.to_pandas(expand_explanations=True)

print("\nFlagship pattern results:")
# Show selected columns (community columns may be None if no partition exists)
available_cols = ['id', 'layer', 'degree']
if 'betweenness_centrality' in df.columns:
    available_cols.append('betweenness_centrality')
if 'top_neighbors' in df.columns:
    available_cols.append('top_neighbors')
if 'n_layers_present' in df.columns:
    available_cols.append('n_layers_present')

print(df[available_cols])
print()

print("=" * 80)
print("Example 4: Explanations with neighbors ranked by degree")
print("=" * 80)

result = (
    Q.nodes()
    .from_layers(L["social"])
    .limit(3)
    .explain(
        include=["top_neighbors"],
        neighbors_top=5,
        neighbors={"metric": "degree"}  # Rank by neighbor degree instead of weight
    )
    .execute(network)
)

df = result.to_pandas(expand_explanations=True)

print("\nNeighbors ranked by degree:")
print(df[['id', 'layer', 'top_neighbors']])
print()

print("=" * 80)
print("Example 5: Excluding specific explanation blocks")
print("=" * 80)

result = (
    Q.nodes()
    .from_layers(L["social"])
    .limit(3)
    .explain(
        exclude=["community"],  # Exclude community block
        neighbors_top=2
    )
    .execute(network)
)

df = result.to_pandas(expand_explanations=True)

print("\nWith community excluded (only top_neighbors and layer_footprint):")
print(df[['id', 'layer', 'top_neighbors', 'layers_present']])
print()

print("✅ All examples completed successfully!")
print()
print("Note: Explanation columns may be None if:")
print("  - No community partition is assigned to the network (community_id, community_size)")
print("  - A node has no neighbors (top_neighbors)")
print("  - A node only appears in one layer (n_layers_present=1)")
