"""
Example: Pattern Matching API for Finding Graph Motifs
=======================================================

This example demonstrates the Pattern Matching Builder API for finding
graph motifs, paths, and subgraph patterns in multilayer networks.

The pattern matching API enables declarative specification of structural
patterns that should be found in the network.
"""

from py3plex.core import multinet
from py3plex.dsl import Q


def create_sample_network():
    """Create a sample multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes across social and work layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'David', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer - triangle Alice-Bob-Charlie + David-Bob
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
        {'source': 'David', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 0.5},
        # Work layer - simple path
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
        {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work', 'weight': 1.2},
    ]
    network.add_edges(edges)
    
    return network


def example_basic_edge_pattern():
    """Example 1: Find all edges in the network."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Edge Pattern")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Define a simple edge pattern: two nodes connected by an edge
    pattern = (
        Q.pattern()
         .node("a")
         .node("b")
         .edge("a", "b", directed=False)
         .limit(5)  # Limit results for display
    )
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} edges (showing first 5)")
    print(result.to_pandas())


def example_layer_constrained_pattern():
    """Example 2: Find edges within a specific layer."""
    print("\n" + "=" * 60)
    print("Example 2: Layer-Constrained Pattern")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Find edges only within the social layer
    pattern = (
        Q.pattern()
         .node("a").where(layer="social")
         .node("b").where(layer="social")
         .edge("a", "b", directed=False)
    )
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} edges in social layer")
    print(result.to_pandas())


def example_weighted_edges():
    """Example 3: Find edges with weight constraints."""
    print("\n" + "=" * 60)
    print("Example 3: Weighted Edge Pattern")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Find edges with weight > 1.0
    pattern = (
        Q.pattern()
         .node("a")
         .node("b")
         .edge("a", "b", directed=False)
         .where(weight__gt=1.0)
    )
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} edges with weight > 1.0")
    print(result.to_pandas())


def example_triangle_motif():
    """Example 4: Find triangle motifs."""
    print("\n" + "=" * 60)
    print("Example 4: Triangle Motif")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Find triangles
    pattern = Q.pattern().triangle("a", "b", "c").limit(1)
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} triangle(s)")
    print(result.to_pandas())
    
    # Get unique nodes in the triangle
    nodes = result.to_nodes(unique=True)
    print(f"\nNodes in triangle: {[node[0] for node in nodes]}")


def example_path_pattern():
    """Example 5: Find 2-hop paths."""
    print("\n" + "=" * 60)
    print("Example 5: 2-Hop Path Pattern")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Find 2-hop paths
    pattern = (
        Q.pattern()
         .path(["a", "b", "c"])
         .node("a").where(layer="social")
         .node("b").where(layer="social")
         .node("c").where(layer="social")
         .limit(3)
    )
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} 2-hop paths (showing 3)")
    print(result.to_pandas())


def example_high_degree_nodes():
    """Example 6: Find connections between high-degree nodes."""
    print("\n" + "=" * 60)
    print("Example 6: High-Degree Node Connections")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Find pairs of high-degree nodes connected by edges
    pattern = (
        Q.pattern()
         .node("a").where(layer="social", degree__gt=2)
         .node("b").where(layer="social", degree__gt=2)
         .edge("a", "b", directed=False)
         .constraint("a != b")  # Ensure different nodes
         .returning("a", "b")
    )
    
    result = pattern.execute(network)
    print(f"\nFound {result.count} high-degree pairs")
    print(result.to_pandas())


def example_execution_plan():
    """Example 7: View query execution plan."""
    print("\n" + "=" * 60)
    print("Example 7: Query Execution Plan")
    print("=" * 60)
    
    # Create a pattern with selective predicates
    pattern = (
        Q.pattern()
         .node("a").where(degree__gt=3)
         .node("b")
         .edge("a", "b")
    )
    
    plan = pattern.explain()
    print("\nExecution Plan:")
    print(f"  Root variable: {plan['root_var']}")
    print(f"  Join order: {[step['var'] for step in plan['join_order']]}")
    print(f"  Estimated complexity: {plan['estimated_complexity']}")
    
    print("\nVariable Plans:")
    for var, var_plan in plan['variable_plans'].items():
        print(f"  {var}: {var_plan['num_predicates']} predicates, "
              f"~{var_plan['estimated_candidates']} candidates")


def example_result_projections():
    """Example 8: Different result projections."""
    print("\n" + "=" * 60)
    print("Example 8: Result Projections")
    print("=" * 60)
    
    network = create_sample_network()
    
    pattern = (
        Q.pattern()
         .node("a").where(layer="social")
         .node("b").where(layer="social")
         .edge("a", "b", directed=False)
         .limit(3)
    )
    
    result = pattern.execute(network)
    
    # Projection 1: Pandas DataFrame
    print("\n1. As Pandas DataFrame:")
    print(result.to_pandas())
    
    # Projection 2: Unique nodes
    print("\n2. Unique nodes:")
    nodes = result.to_nodes(unique=True)
    print(f"   {[node[0] for node in nodes]}")
    
    # Projection 3: Edge tuples
    print("\n3. Edge tuples:")
    edges = result.to_edges()
    for src, dst in edges[:3]:
        print(f"   {src[0]} -> {dst[0]}")
    
    # Projection 4: Induced subgraph
    print("\n4. Induced subgraph:")
    subgraph = result.to_subgraph(network)
    print(f"   Nodes: {subgraph.number_of_nodes()}")
    print(f"   Edges: {subgraph.number_of_edges()}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Pattern Matching API Examples")
    print("=" * 60)
    
    # Run all examples
    example_basic_edge_pattern()
    example_layer_constrained_pattern()
    example_weighted_edges()
    example_triangle_motif()
    example_path_pattern()
    example_high_degree_nodes()
    example_execution_plan()
    example_result_projections()
    
    print("\n" + "=" * 60)
    print("All Examples Completed!")
    print("=" * 60)
