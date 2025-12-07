#!/usr/bin/env python
"""Example demonstrating DSL linting functionality.

This example shows how to use the DSL linting API to validate
queries and detect potential issues.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, lint, explain


def create_sample_network():
    """Create a sample multilayer network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in multiple layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Carol', 'type': 'social'},
        {'source': 'Dave', 'type': 'work'},
        {'source': 'Eve', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Dave', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


def example_1_valid_query():
    """Example 1: Linting a valid query."""
    print("=" * 60)
    print("Example 1: Linting a Valid Query")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Build a valid query
    query = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=1)
         .compute("degree")
         .to_ast()
    )
    
    # Run linting
    diagnostics = lint(query, graph=network)
    
    if diagnostics:
        print("Issues found:")
        for d in diagnostics:
            print(f"  [{d.severity.upper()}] {d.code}: {d.message}")
    else:
        print("✓ No issues found - query is valid!")
    
    print()


def example_2_unknown_layer():
    """Example 2: Detecting unknown layer."""
    print("=" * 60)
    print("Example 2: Detecting Unknown Layer")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Build a query with unknown layer
    query = (
        Q.nodes()
         .from_layers(L["unknown_layer"])
         .to_ast()
    )
    
    # Run linting
    diagnostics = lint(query, graph=network)
    
    if diagnostics:
        print("Issues found:")
        for d in diagnostics:
            print(f"  [{d.severity.upper()}] {d.code}: {d.message}")
            if d.suggested_fix:
                print(f"    → Suggestion: {d.suggested_fix.replacement}")
    
    print()


def example_3_type_mismatch():
    """Example 3: Detecting type mismatch."""
    print("=" * 60)
    print("Example 3: Detecting Type Mismatch")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Build a query with type mismatch
    query = (
        Q.nodes()
         .where(degree__gt="not_a_number")  # Comparing numeric to string
         .to_ast()
    )
    
    # Run linting
    diagnostics = lint(query, graph=network)
    
    if diagnostics:
        print("Issues found:")
        for d in diagnostics:
            print(f"  [{d.severity.upper()}] {d.code}: {d.message}")
    
    print()


def example_4_explain():
    """Example 4: Using explain for detailed analysis."""
    print("=" * 60)
    print("Example 4: Detailed Query Explanation")
    print("=" * 60)
    
    network = create_sample_network()
    
    # Build a query
    query = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=1)
         .compute("betweenness_centrality", alias="bc")
         .order_by("bc", desc=True)
         .limit(10)
         .to_ast()
    )
    
    # Get explanation
    result = explain(query, graph=network)
    
    print("\nAST Summary:")
    print(result.ast_summary)
    
    print(f"\nEstimated Cost: {result.cost_estimate}")
    
    print("\nType Information:")
    for key, type_val in result.type_info.items():
        print(f"  {key}: {type_val}")
    
    print("\nExecution Plan:")
    for step in result.plan_steps:
        print(f"  {step}")
    
    if result.diagnostics:
        print("\nDiagnostics:")
        for d in result.diagnostics:
            print(f"  [{d.severity.upper()}] {d.code}: {d.message}")
    else:
        print("\n✓ No issues detected")
    
    print()


def main():
    """Run all examples."""
    print("\nDSL Linting Examples\n")
    
    example_1_valid_query()
    example_2_unknown_layer()
    example_3_type_mismatch()
    example_4_explain()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
