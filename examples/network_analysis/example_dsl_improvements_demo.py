#!/usr/bin/env python3
"""Demonstration of py3plex DSL improvements.

This script demonstrates the new edge query and aggregation capabilities
that have been added to py3plex DSL v2.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_demo_network():
    """Create a demonstration multilayer network."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes across multiple layers
    nodes = []
    for person in ['Alice', 'Bob', 'Charlie', 'David', 'Eve']:
        for layer in ['social', 'work', 'hobby']:
            nodes.append({'source': person, 'type': layer})
    net.add_nodes(nodes)
    
    # Add edges with varying weights
    edges = [
        # Social layer - dense connections
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 3.0},
        {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social', 'weight': 2.5},
        
        # Work layer - sparser
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 4.0},
        {'source': 'Alice', 'target': 'David', 'source_type': 'work', 'target_type': 'work', 'weight': 5.0},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work', 'weight': 3.5},
        
        # Hobby layer - chain
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby', 'weight': 1.0},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'hobby', 'target_type': 'hobby', 'weight': 2.0},
        {'source': 'David', 'target': 'Eve', 'source_type': 'hobby', 'target_type': 'hobby', 'weight': 1.5},
    ]
    net.add_edges(edges)
    
    return net


def demo_endpoint_properties():
    """Demonstrate filtering edges by endpoint properties."""
    print("=" * 70)
    print("DEMO 1: Edge Filtering with Endpoint Properties")
    print("=" * 70)
    
    net = create_demo_network()
    
    # Filter edges where source has high degree
    result = (
        Q.edges()
         .where(src_degree__gt=2)
         .execute(net)
    )
    
    print(f"\n✓ Edges where source has degree > 2: {result.count} edges")
    df = result.to_pandas()
    print(df[['source', 'target', 'source_layer', 'target_layer']].head())
    
    # Filter by both endpoint degrees
    result = (
        Q.edges()
         .where(src_degree__ge=2, dst_degree__ge=2)
         .execute(net)
    )
    
    print(f"\n✓ Edges where both endpoints have degree >= 2: {result.count} edges")
    

def demo_aggregations():
    """Demonstrate new aggregation operators."""
    print("\n" + "=" * 70)
    print("DEMO 2: Advanced Aggregation Operators")
    print("=" * 70)
    
    net = create_demo_network()
    
    # Global aggregations on edges
    result = (
        Q.edges()
         .summarize(
             total_edges="count()",
             avg_weight="mean(weight)",
             median_weight="median(weight)",
             q95_weight="quantile(weight, 0.95)",
             max_weight="max(weight)",
             std_weight="std(weight)"
         )
         .execute(net)
    )
    
    print("\n✓ Global edge statistics:")
    df = result.to_pandas()
    print(df.T)  # Transpose for better readability
    
    # Per-layer-pair aggregations
    result = (
        Q.edges()
         .per_layer_pair()
         .aggregate(
             edge_count="count()",
             avg_weight="mean(weight)",
             median_weight="median(weight)",
             total_weight="sum(weight)"
         )
         .execute(net)
    )
    
    print("\n✓ Per-layer-pair statistics:")
    df = result.to_pandas()
    print(df)


def demo_endpoint_aggregations():
    """Demonstrate aggregating endpoint properties."""
    print("\n" + "=" * 70)
    print("DEMO 3: Aggregating Endpoint Properties")
    print("=" * 70)
    
    net = create_demo_network()
    
    # Aggregate endpoint degrees per layer pair
    result = (
        Q.edges()
         .per_layer_pair()
         .aggregate(
             edge_count="count()",
             avg_src_degree="mean(src_degree)",
             avg_dst_degree="mean(dst_degree)",
             max_src_degree="max(src_degree)",
             avg_weight="mean(weight)"
         )
         .execute(net)
    )
    
    print("\n✓ Endpoint degree statistics per layer pair:")
    df = result.to_pandas()
    print(df)


def demo_node_aggregations():
    """Demonstrate node aggregations for comparison."""
    print("\n" + "=" * 70)
    print("DEMO 4: Node Aggregations (for comparison)")
    print("=" * 70)
    
    net = create_demo_network()
    
    # Per-layer node statistics
    result = (
        Q.nodes()
         .compute("degree")
         .per_layer()
         .aggregate(
             node_count="count()",
             avg_degree="mean(degree)",
             median_degree="median(degree)",
             q25_degree="quantile(degree, 0.25)",
             q75_degree="quantile(degree, 0.75)"
         )
         .execute(net)
    )
    
    print("\n✓ Per-layer node statistics:")
    df = result.to_pandas()
    print(df)


def main():
    """Run all demonstrations."""
    print("\n" + "#" * 70)
    print("# py3plex DSL Improvements Demonstration")
    print("#" * 70)
    print("\nShowcasing new edge query and aggregation capabilities")
    print("added to py3plex DSL v2.\n")
    
    demo_endpoint_properties()
    demo_aggregations()
    demo_endpoint_aggregations()
    demo_node_aggregations()
    
    print("\n" + "=" * 70)
    print("All demonstrations completed successfully!")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  ✓ Edge filtering by endpoint properties (src_degree, dst_degree)")
    print("  ✓ Advanced aggregations (median, quantile)")
    print("  ✓ Per-layer-pair grouping and aggregation")
    print("  ✓ Endpoint property aggregation")
    print("  ✓ Full parity between node and edge queries")
    print()


if __name__ == "__main__":
    main()
