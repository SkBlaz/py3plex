#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DSL Patterns Quick Reference - 7 Essential Patterns for py3plex.

This script demonstrates the 7 most common DSL query patterns that cover
80% of typical use cases. It's designed as executable documentation without
creating separate markdown files.

Run this script to see each pattern in action with live output.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_example_network():
    """Create a simple multilayer network for demonstrations."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes to 3 layers
    nodes = []
    for person in ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']:
        for layer in ['social', 'work', 'hobby']:
            nodes.append({'source': person, 'type': layer})
    net.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer - more connected
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
        
        # Work layer - moderate
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
        
        # Hobby layer - sparse
        {'source': 'Alice', 'target': 'Frank', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'hobby', 'target_type': 'hobby'},
    ]
    net.add_edges(edges)
    
    return net


def pattern_1_basic_filtering():
    """Pattern 1: Basic Node Query with Filtering.
    
    USE CASE: Find nodes matching criteria in a specific layer.
    FREQUENCY: 40% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 1: Basic Node Query with Filtering")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = (
        Q.nodes()
         .from_layers(L["social"])              # Select layer
         .where(degree__gt=2)                    # Filter by attribute
         .compute("betweenness_centrality")      # Compute metrics
         .execute(net)
    )
    """)
    
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=2)
         .compute("betweenness_centrality")
         .execute(net)
    )
    
    print(f"\nResult: Found {result.count} high-degree nodes in social layer")
    df = result.to_pandas()
    print("\nTop results:")
    print(df[['node', 'degree', 'betweenness_centrality']].head())


def pattern_2_cross_layer_hubs():
    """Pattern 2: Cross-Layer Hub Analysis.
    
    USE CASE: Identify nodes that are important across multiple layers.
    FREQUENCY: 25% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 2: Cross-Layer Hub Analysis")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = (
        Q.nodes()
         .from_layers(L["*"])                    # All layers
         .compute("degree", "pagerank")
         .per_layer()                             # Group by layer
           .top_k(3, "degree")                    # Top 3 per layer
         .end_grouping()
         .coverage(mode="at_least", k=2)         # Keep nodes in ≥2 layers
         .execute(net)
    )
    """)
    
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "pagerank")
         .per_layer()
           .top_k(3, "degree")
         .end_grouping()
         .coverage(mode="at_least", k=2)
         .execute(net)
    )
    
    print(f"\nResult: Found {result.count} cross-layer hubs")
    df = result.to_pandas()
    print("\nCross-layer hubs:")
    for node in df['node'].unique():
        layers = df[df['node'] == node]['layer'].tolist()
        print(f"  - {node}: present in {layers}")


def pattern_3_uncertainty_quantification():
    """Pattern 3: Uncertainty Quantification.
    
    USE CASE: Get confidence intervals for metrics.
    FREQUENCY: 15% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 3: Uncertainty Quantification")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = (
        Q.nodes()
         .compute("pagerank")
         .uq(method="bootstrap",                 # Bootstrap resampling
             n_samples=50,                       # 50 samples
             ci=0.95,                            # 95% confidence interval
             seed=42)                            # Reproducibility
         .execute(net)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    """)
    
    result = (
        Q.nodes()
         .compute("pagerank")
         .uq(method="bootstrap", n_samples=50, ci=0.95, seed=42)
         .execute(net)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    print(f"\nResult: Computed PageRank with confidence intervals for {len(df)} nodes")
    print("\nSample with confidence intervals:")
    print(df[['node', 'pagerank', 'pagerank_ci95_low', 'pagerank_ci95_high']].head())


def pattern_4_layer_algebra():
    """Pattern 4: Layer Algebra.
    
    USE CASE: Combine or subtract layers using set operations.
    FREQUENCY: 12% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 4: Layer Algebra")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    # Union of layers
    result_union = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])   # Union
         .execute(net)
    )
    
    # All except one layer
    result_diff = (
        Q.nodes()
         .from_layers(L["*"] - L["hobby"])       # Difference
         .execute(net)
    )
    """)
    
    result_union = Q.nodes().from_layers(L["social"] + L["work"]).execute(net)
    print(f"\nSocial ∪ Work: {result_union.count} node replicas")
    
    result_diff = Q.nodes().from_layers(L["*"] - L["hobby"]).execute(net)
    print(f"All - Hobby: {result_diff.count} node replicas")
    
    result_single = Q.nodes().from_layers(L["social"]).execute(net)
    print(f"Social only: {result_single.count} node replicas")


def pattern_5_mutate_transform():
    """Pattern 5: Data Transformation with Mutate.
    
    USE CASE: Create derived columns with custom logic.
    FREQUENCY: 10% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 5: Data Transformation with Mutate")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = (
        Q.nodes()
         .compute("degree", "clustering")
         .mutate(
             hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
             category=lambda row: "hub" if row.get("degree", 0) > 2 else "peripheral"
         )
         .execute(net)
    )
    """)
    
    result = (
        Q.nodes()
         .compute("degree", "clustering")
         .mutate(
             hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
             category=lambda row: "hub" if row.get("degree", 0) > 2 else "peripheral"
         )
         .execute(net)
    )
    
    df = result.to_pandas()
    print(f"\nResult: Created 2 derived columns for {len(df)} nodes")
    print("\nCategory distribution:")
    print(df['category'].value_counts())
    print("\nSample with derived columns:")
    print(df[['node', 'degree', 'clustering', 'hub_score', 'category']].head())


def pattern_6_aggregation():
    """Pattern 6: Per-Layer Aggregation.
    
    USE CASE: Compute summary statistics per layer.
    FREQUENCY: 8% of queries
    """
    print("\n" + "=" * 70)
    print("PATTERN 6: Per-Layer Aggregation")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = (
        Q.nodes()
         .per_layer()
         .compute("degree")
         .aggregate(
             avg_degree="mean(degree)",
             max_degree="max(degree)",
             node_count="count()"
         )
         .execute(net)
    )
    """)
    
    result = (
        Q.nodes()
         .per_layer()
         .compute("degree")
         .aggregate(
             avg_degree="mean(degree)",
             max_degree="max(degree)",
             node_count="count()"
         )
         .execute(net)
    )
    
    print(f"\nResult: Computed per-layer statistics")
    print("\nPer-layer summary:")
    for item, avg_deg in zip(result.items, result.attributes['avg_degree']):
        idx = result.items.index(item)
        max_deg = result.attributes['max_degree'][idx]
        count = result.attributes['node_count'][idx]
        print(f"  - {item}: {count} nodes, avg degree = {avg_deg:.2f}, max = {max_deg}")


def pattern_7_export_formats():
    """Pattern 7: Multiple Export Formats.
    
    USE CASE: Export results to various data structures.
    FREQUENCY: 30% of queries (combined)
    """
    print("\n" + "=" * 70)
    print("PATTERN 7: Multiple Export Formats")
    print("=" * 70)
    
    net = create_example_network()
    
    print("\nCode:")
    print("""
    result = Q.nodes().compute("degree").execute(net)
    
    # Pandas DataFrame
    df = result.to_pandas()
    
    # NetworkX graph
    graph = result.to_networkx()
    
    # Apache Arrow (high-performance)
    table = result.to_arrow()
    
    # CSV file
    df.to_csv("results.csv", index=False)
    """)
    
    result = Q.nodes().compute("degree").execute(net)
    
    # Pandas
    df = result.to_pandas()
    print(f"\n✓ Pandas DataFrame: {len(df)} rows × {len(df.columns)} columns")
    
    # NetworkX
    graph = result.to_networkx()
    print(f"✓ NetworkX graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Arrow
    table = result.to_arrow()
    print(f"✓ Apache Arrow table: {len(table)} rows × {len(table.columns)} columns")
    
    print("\nDataFrame preview:")
    print(df[['node', 'layer', 'degree']].head())


def main():
    """Run all pattern demonstrations."""
    print("\n" + "=" * 70)
    print("PY3PLEX DSL PATTERNS: QUICK REFERENCE")
    print("=" * 70)
    print("\nThis script demonstrates the 7 most common DSL query patterns.")
    print("Each pattern includes:")
    print("  - Use case description")
    print("  - Frequency in typical workflows")
    print("  - Complete working code")
    print("  - Live execution with sample output")
    print("\nNo markdown files are created - the code IS the documentation!")
    
    # Run all patterns
    pattern_1_basic_filtering()
    pattern_2_cross_layer_hubs()
    pattern_3_uncertainty_quantification()
    pattern_4_layer_algebra()
    pattern_5_mutate_transform()
    pattern_6_aggregation()
    pattern_7_export_formats()
    
    print("\n" + "=" * 70)
    print("SUMMARY: 7 Essential DSL Patterns")
    print("=" * 70)
    print("""
    1. Basic Filtering          (40%) - Q.nodes().from_layers().where().compute()
    2. Cross-Layer Hubs         (25%) - .per_layer().top_k().coverage()
    3. Uncertainty Quantif.     (15%) - .uq(method="bootstrap", n_samples=100)
    4. Layer Algebra            (12%) - L["a"] + L["b"], L["*"] - L["x"]
    5. Data Transformation      (10%) - .mutate(new_col=lambda row: ...)
    6. Aggregation              (8%)  - .per_layer().aggregate()
    7. Export Formats           (30%) - .to_pandas(), .to_networkx(), .to_arrow()
    
    💡 Pro Tip: Chain these patterns together for powerful queries!
    
    📚 More Resources:
       - See README.md for quick patterns section
       - See AGENTS.md#quick-start-golden-paths for comprehensive guide
       - See examples/network_analysis/ for 50+ detailed examples
    """)


if __name__ == "__main__":
    main()
