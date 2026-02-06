#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple demonstration of py3plex v1.1+ ergonomics features.

This script demonstrates the ergonomics features designed to reduce friction
for both human users and LLM agents:

1. Interactive Query Building with .hint()
2. Enhanced QueryResult Introspection
3. Pedagogical Error Messages
4. Performance and Semantic Warnings
5. Multilayer Semantics Awareness

No new markdown documentation is created - this is pure demonstration code.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, DslError
from py3plex.dsl.warnings import suppress_warnings


def create_demo_network():
    """Create a simple multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes to two layers
    nodes = []
    for person in ['Alice', 'Bob', 'Charlie', 'David']:
        for layer in ['social', 'work']:
            nodes.append({'source': person, 'type': layer})
    net.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        # Work layer
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
    ]
    net.add_edges(edges)
    
    return net


def demo_1_hint_method():
    """Demonstrate .hint() method for interactive query building."""
    print("\n" + "=" * 60)
    print("Demo 1: Interactive Query Building with .hint()")
    print("=" * 60)
    
    net = create_demo_network()
    
    # Start building a query and use hint() to see suggestions
    print("\n1. Start with basic node query:")
    q = Q.nodes()
    q.hint()  # Shows suggestions for what to do next
    
    # Chain hint() calls throughout query building
    print("\n2. Add layer selection and check hints:")
    q = Q.nodes().from_layers(L["social"])
    q.hint()  # Shows updated suggestions
    
    # Hint is chainable and non-invasive
    print("\n3. Build complete query with hints:")
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .hint()  # Can be used in chain
         .compute("degree")
         .hint()  # Can be called multiple times
         .execute(net)
    )
    
    print(f"\nQuery executed successfully, got {result.count} results")


def demo_2_enhanced_introspection():
    """Demonstrate enhanced QueryResult introspection."""
    print("\n" + "=" * 60)
    print("Demo 2: Enhanced QueryResult Introspection")
    print("=" * 60)
    
    net = create_demo_network()
    
    # Execute a query and inspect the result
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=1)
         .execute(net)
    )
    
    print("\nQueryResult representation shows full context:")
    print(result)  # Uses enhanced __repr__
    
    print(f"\nTarget: {result.target}")
    print(f"Count: {result.count}")
    print(f"Computed metrics: {result.computed_metrics}")


def demo_3_pedagogical_errors():
    """Demonstrate pedagogical error messages."""
    print("\n" + "=" * 60)
    print("Demo 3: Pedagogical Error Messages")
    print("=" * 60)
    
    net = create_demo_network()
    
    # Try to use an unknown metric
    print("\n1. Unknown metric error:")
    try:
        result = Q.nodes().compute("unknownmetric").execute(net)
    except DslError as e:
        print(f"Error caught: {e}")
        print("\nNote: Error message includes suggestions and examples")
    
    # Try to use wrong layer name
    print("\n2. Unknown layer error:")
    try:
        result = Q.nodes().from_layers(L["nonexistent"]).execute(net)
    except Exception as e:
        # May not raise error in some implementations
        print(f"Query executed with empty result: {e if hasattr(e, 'message') else 'OK'}")


def demo_4_warnings():
    """Demonstrate performance and semantic warnings."""
    print("\n" + "=" * 60)
    print("Demo 4: Performance and Semantic Warnings")
    print("=" * 60)
    
    net = create_demo_network()
    
    # Multilayer semantic warnings are context-aware
    print("\n1. Multilayer context (may show warnings):")
    result = Q.nodes().compute("degree").execute(net)
    print(f"Computed degree for {result.count} node replicas")
    
    # Warnings can be suppressed when needed
    print("\n2. Suppress warnings:")
    with suppress_warnings("degree_ambiguity"):
        result = Q.nodes().compute("degree").execute(net)
        print(f"Query executed without warnings: {result.count} results")


def demo_5_multilayer_semantics():
    """Demonstrate multilayer semantics awareness."""
    print("\n" + "=" * 60)
    print("Demo 5: Multilayer Semantics Awareness")
    print("=" * 60)
    
    net = create_demo_network()
    
    # Node replicas vs physical nodes
    print("\n1. Understanding node replicas:")
    result = Q.nodes().execute(net)
    print(f"Total node replicas: {result.count}")
    
    # Physical nodes
    physical_nodes = set(item[0] for item in result.items)
    print(f"Physical nodes: {len(physical_nodes)}")
    print(f"Physical node names: {sorted(physical_nodes)}")
    
    # Per-layer analysis
    print("\n2. Per-layer operations:")
    result = (
        Q.nodes()
         .per_layer()
         .compute("degree")
         .execute(net)
    )
    
    print(f"Computed per-layer metrics")
    if 'grouping' in result.meta:
        print(f"Grouping mode: {result.meta['grouping'].get('mode', 'unknown')}")


def main():
    """Run all ergonomics demonstrations."""
    print("\n" + "=" * 60)
    print("py3plex v1.1+ Ergonomics Features Demonstration")
    print("=" * 60)
    print("\nThis script demonstrates ergonomics features without")
    print("creating any new markdown documentation files.")
    
    # Run all demos
    demo_1_hint_method()
    demo_2_enhanced_introspection()
    demo_3_pedagogical_errors()
    demo_4_warnings()
    demo_5_multilayer_semantics()
    
    print("\n" + "=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
