#!/usr/bin/env python
"""
Example: dplyr-style DSL operations for multilayer networks

This script demonstrates the new dplyr-inspired operations in py3plex DSL,
making multilayer network analysis more ergonomic and expressive.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

# Create a sample multilayer social-professional network
print("Creating multilayer network...")
net = multinet.multi_layer_network(directed=False)

# Add nodes across 3 layers
nodes = []
for layer in ["social", "work", "hobby"]:
    for person in ["Alice", "Bob", "Charlie", "Diana", "Eve"]:
        nodes.append({'source': person, 'type': layer})
net.add_nodes(nodes)

# Add edges with different patterns per layer
edges = [
    # Social layer: Alice and Bob are connectors
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    
    # Work layer: Alice is the hub
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Alice', 'target': 'Diana', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Alice', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    
    # Hobby layer: More distributed
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby'},
    {'source': 'Charlie', 'target': 'Diana', 'source_type': 'hobby', 'target_type': 'hobby'},
    {'source': 'Diana', 'target': 'Eve', 'source_type': 'hobby', 'target_type': 'hobby'},
]
net.add_edges(edges)

print("\n" + "="*70)
print("Example 1: Per-layer statistics with summarize()")
print("="*70)

stats = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
     .summarize(
         mean_degree="mean(degree)",
         max_degree="max(degree)",
         num_nodes="n()"
     )
     .arrange("-mean_degree")  # Sort by mean degree descending
     .rename(layer_name="id", avg_deg="mean_degree", max_deg="max_degree", n="num_nodes")
     .execute(net)
)

print("\nLayer statistics:")
print(stats.to_pandas())

print("\n" + "="*70)
print("Example 2: Find influential nodes with centrality() and rank_by()")
print("="*70)

influential = (
    Q.nodes()
     .from_layers(L["*"])
     .centrality("degree", bc="betweenness_centrality")
     .per_layer()
     .rank_by("bc", method="dense")  # Add rank column
     .zscore("degree")  # Add z-score for degree
     .end_grouping()
     .arrange("-bc")
     .limit(10)
     .execute(net)
)

print("\nTop influential nodes:")
print(influential.to_pandas())

print("\n" + "="*70)
print("Example 3: Cross-layer hub detection with coverage()")
print("="*70)

# Find nodes that are top-2 in at least 2 layers
multi_layer_hubs = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
     .top_k(2, "degree")
     .coverage(mode="at_least", k=2)
     .execute(net)
)

print("\nNodes that are hubs in at least 2 layers:")
print(multi_layer_hubs.to_pandas())

print("\n" + "="*70)
print("Example 4: Fraction-based coverage (new feature!)")
print("="*70)

# Find nodes appearing in top-3 of at least 67% of layers
frequent_leaders = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
     .top_k(3, "degree")
     .coverage(mode="fraction", p=0.67)  # At least 67% of layers
     .execute(net)
)

print("\nNodes in top-3 of at least 67% of layers:")
print(frequent_leaders.to_pandas())

print("\n" + "="*70)
print("Example 5: Column operations - select, drop, rename")
print("="*70)

clean_view = (
    Q.nodes()
     .from_layers(L["social"])
     .compute("degree", "betweenness_centrality")
     .rename(person="id", connections="degree", influence="betweenness_centrality")
     .select("person", "connections", "influence")  # Only keep these columns
     .arrange("-influence")
     .execute(net)
)

print("\nCleaned social network view:")
print(clean_view.to_pandas())

print("\n" + "="*70)
print("Example 6: Distinct values")
print("="*70)

# Get unique degree values across all layers
unique_degrees = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .distinct("degree")  # Deduplicate by degree
     .arrange("degree")
     .execute(net)
)

print("\nUnique degree values in the network:")
print(unique_degrees.to_pandas())

print("\n" + "="*70)
print("✓ All examples completed successfully!")
print("="*70)
print("\nKey Takeaways:")
print("  • summarize() enables group-wise aggregations (mean, max, min, etc.)")
print("  • centrality() is a convenient shorthand for common metrics")
print("  • rank_by() and zscore() add statistical context to your analysis")
print("  • coverage(mode='fraction', p=...) finds cross-layer patterns")
print("  • select(), drop(), rename() clean and shape your results")
print("  • arrange() and distinct() provide familiar data manipulation")
print("\nThe DSL now feels like dplyr but is multilayer-aware! 🎉")
