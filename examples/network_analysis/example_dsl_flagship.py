#!/usr/bin/env python3
"""
Flagship Example: DSL-Powered Multilayer Network Analysis
==========================================================

This flagship example demonstrates the full power of py3plex's Domain-Specific
Language (DSL) for analyzing multilayer networks. It showcases a complete
workflow combining:

1. **Network Creation**: Building a realistic multilayer social network
2. **DSL Queries**: SQL-like queries for node/edge selection and filtering
3. **Centrality Analysis**: Computing and comparing multiple centrality measures
4. **Statistical Reports**: Generating comprehensive network statistics
5. **Community Detection**: Identifying and analyzing network communities

This example serves as a comprehensive introduction to py3plex's DSL capabilities
and is designed to be both educational and practically useful.

Usage:
    python example_dsl_flagship.py

For more information on the DSL syntax, see the documentation:
    - docs/user_guide/dsl.rst
    - py3plex.dsl module docstrings

Authors: py3plex contributors
Date: 2025
"""

from collections import Counter
from typing import Dict, List, Any

from py3plex.core import multinet
from py3plex.dsl import (
    execute_query,
    format_result,
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer,
)
from py3plex.algorithms.statistical_report import generate_statistical_report
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.algorithms.centrality_toolkit import (
    multilayer_betweenness_centrality,
    versatility_score,
    aggregate_centrality_across_layers,
)


def create_sample_network() -> multinet.multi_layer_network:
    """Create a sample multilayer social network for demonstration.
    
    Creates a network with three layers:
    - social: Friend relationships
    - work: Professional collaborations  
    - family: Family connections
    
    Returns:
        multi_layer_network: A sample multilayer network
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Define people in our network
    people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 
              'Frank', 'Grace', 'Henry', 'Ivy', 'Jack']
    
    # Add nodes to each layer
    nodes = []
    for person in people:
        for layer in ['social', 'work', 'family']:
            nodes.append({'source': person, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges - creating different network structures per layer
    edges = [
        # Social layer: Dense friend network with central hub (Bob)
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Frank', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Grace', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Henry', 'target': 'Ivy', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Ivy', 'target': 'Jack', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
        
        # Work layer: Professional collaborations with different structure
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'Grace', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Frank', 'target': 'Henry', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Grace', 'target': 'Jack', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'David', 'target': 'Ivy', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Henry', 'source_type': 'work', 'target_type': 'work'},
        
        # Family layer: Sparse family connections
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Grace', 'target': 'Henry', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Ivy', 'target': 'Jack', 'source_type': 'family', 'target_type': 'family'},
    ]
    network.add_edges(edges)
    
    return network


def demonstrate_dsl_queries(network: multinet.multi_layer_network) -> None:
    """Demonstrate basic and advanced DSL queries.
    
    Args:
        network: The multilayer network to query
    """
    print("\n" + "=" * 80)
    print("PART 1: DSL QUERY DEMONSTRATIONS")
    print("=" * 80)
    
    # Query 1: Select all nodes in a specific layer
    print("\n[1.1] Basic Layer Selection")
    print("-" * 80)
    print("Query: SELECT nodes WHERE layer=\"social\"")
    result = execute_query(network, 'SELECT nodes WHERE layer="social"')
    print(f"Found {result['count']} nodes in social layer")
    print(f"Sample nodes: {result['nodes'][:3]}...")
    
    # Query 2: Filter by degree
    print("\n[1.2] Degree-Based Filtering")
    print("-" * 80)
    print("Query: SELECT nodes WHERE degree > 2")
    result = execute_query(network, 'SELECT nodes WHERE degree > 2')
    print(f"Found {result['count']} high-degree nodes (degree > 2)")
    for node in result['nodes'][:5]:
        degree = network.core_network.degree(node)
        print(f"  {node}: degree = {degree}")
    
    # Query 3: Complex conditions with AND
    print("\n[1.3] Complex Query with AND")
    print("-" * 80)
    print("Query: SELECT nodes WHERE layer=\"social\" AND degree >= 3")
    result = execute_query(network, 'SELECT nodes WHERE layer="social" AND degree >= 3')
    print(f"Found {result['count']} social layer hubs (degree >= 3)")
    for node in result['nodes']:
        degree = network.core_network.degree(node)
        print(f"  {node}: degree = {degree}")
    
    # Query 4: OR operator for multiple layers
    print("\n[1.4] Multi-Layer Query with OR")
    print("-" * 80)
    print("Query: SELECT nodes WHERE layer=\"work\" OR layer=\"family\"")
    result = execute_query(network, 'SELECT nodes WHERE layer="work" OR layer="family"')
    print(f"Found {result['count']} nodes in work or family layers")
    
    # Query 5: NOT operator
    print("\n[1.5] Exclusion Query with NOT")
    print("-" * 80)
    print("Query: SELECT nodes WHERE NOT layer=\"social\"")
    result = execute_query(network, 'SELECT nodes WHERE NOT layer="social"')
    print(f"Found {result['count']} nodes NOT in social layer")


def demonstrate_centrality_analysis(network: multinet.multi_layer_network) -> Dict[str, Any]:
    """Demonstrate centrality computation using DSL.
    
    Args:
        network: The multilayer network to analyze
        
    Returns:
        Dictionary containing centrality results for further analysis
    """
    print("\n" + "=" * 80)
    print("PART 2: CENTRALITY ANALYSIS")
    print("=" * 80)
    
    centrality_results = {}
    
    # Compute multiple centrality measures for social layer
    print("\n[2.1] Compute Betweenness Centrality for Social Layer")
    print("-" * 80)
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality'
    )
    
    if 'computed' in result and 'betweenness_centrality' in result['computed']:
        centralities = result['computed']['betweenness_centrality']
        centrality_results['social_betweenness'] = centralities
        
        # Show top 5 nodes
        sorted_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 nodes by betweenness centrality (social layer):")
        for node, centrality in sorted_nodes:
            print(f"  {node}: {centrality:.4f}")
    
    # Multi-measure computation
    print("\n[2.2] Multi-Measure Centrality Analysis")
    print("-" * 80)
    print("Query: SELECT nodes WHERE layer=\"social\" COMPUTE degree_centrality closeness_centrality")
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" COMPUTE degree_centrality closeness_centrality'
    )
    
    if 'computed' in result:
        print("\nCentrality comparison for social layer hubs:")
        print(f"{'Node':<25} {'Degree Cent.':<15} {'Closeness Cent.':<15}")
        print("-" * 55)
        
        # Get nodes with high degree centrality
        if 'degree_centrality' in result['computed']:
            deg_cent = result['computed']['degree_centrality']
            close_cent = result['computed'].get('closeness_centrality', {})
            
            top_nodes = sorted(deg_cent.items(), key=lambda x: x[1], reverse=True)[:5]
            for node, dc in top_nodes:
                cc = close_cent.get(node, 0)
                print(f"{str(node):<25} {dc:<15.4f} {cc:<15.4f}")
    
    # Cross-layer centrality comparison
    print("\n[2.3] Cross-Layer Centrality Comparison")
    print("-" * 80)
    
    layers = ['social', 'work', 'family']
    layer_avg_centrality = {}
    
    for layer in layers:
        result = execute_query(
            network,
            f'SELECT nodes WHERE layer="{layer}" COMPUTE betweenness_centrality'
        )
        if 'computed' in result and 'betweenness_centrality' in result['computed']:
            centralities = result['computed']['betweenness_centrality']
            if centralities:
                avg = sum(centralities.values()) / len(centralities)
                max_cent = max(centralities.values())
                layer_avg_centrality[layer] = {'avg': avg, 'max': max_cent}
    
    print(f"{'Layer':<12} {'Avg Betweenness':<18} {'Max Betweenness':<18}")
    print("-" * 48)
    for layer, stats in layer_avg_centrality.items():
        print(f"{layer:<12} {stats['avg']:<18.4f} {stats['max']:<18.4f}")
    
    centrality_results['layer_comparison'] = layer_avg_centrality
    
    # Multilayer centrality using toolkit
    print("\n[2.4] Multilayer Betweenness Centrality")
    print("-" * 80)
    try:
        ml_betweenness = multilayer_betweenness_centrality(network)
        centrality_results['multilayer_betweenness'] = ml_betweenness
        
        # Aggregate across layers
        aggregated = aggregate_centrality_across_layers(ml_betweenness, aggregation='sum')
        
        print("Top 5 nodes by aggregated multilayer betweenness:")
        sorted_agg = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:5]
        for node_id, total in sorted_agg:
            print(f"  {node_id}: {total:.4f}")
        
        # Compute versatility
        print("\n[2.5] Versatility Scores")
        print("-" * 80)
        versatility = versatility_score(ml_betweenness)
        centrality_results['versatility'] = versatility
        
        print("Versatility measures how evenly a node's importance is distributed across layers.")
        print("Top 5 most versatile nodes:")
        sorted_vers = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
        for node_id, vers in sorted_vers:
            print(f"  {node_id}: {vers:.4f}")
            
    except Exception as e:
        print(f"Note: Multilayer centrality computation skipped: {e}")
    
    return centrality_results


def demonstrate_statistics(network: multinet.multi_layer_network) -> None:
    """Demonstrate statistical report generation.
    
    Args:
        network: The multilayer network to analyze
    """
    print("\n" + "=" * 80)
    print("PART 3: STATISTICAL ANALYSIS")
    print("=" * 80)
    
    print("\n[3.1] Generating Comprehensive Statistical Report")
    print("-" * 80)
    
    report = generate_statistical_report(
        network,
        output_format='text',
        include_sections=['basic', 'degree', 'layers', 'clustering']
    )
    
    print(report)


def demonstrate_community_detection(network: multinet.multi_layer_network) -> Dict[str, int]:
    """Demonstrate community detection and integration with DSL.
    
    Args:
        network: The multilayer network to analyze
        
    Returns:
        Community partition dictionary
    """
    print("\n" + "=" * 80)
    print("PART 4: COMMUNITY DETECTION")
    print("=" * 80)
    
    print("\n[4.1] Running Louvain Community Detection")
    print("-" * 80)
    
    try:
        # Detect communities using Louvain algorithm
        partition = cw.louvain_communities(network)
        
        # Analyze detected communities
        community_sizes = Counter(partition.values())
        num_communities = len(community_sizes)
        
        print(f"Detected {num_communities} communities")
        print(f"Largest community: {max(community_sizes.values())} nodes")
        print(f"Smallest community: {min(community_sizes.values())} nodes")
        
        # Show community distribution
        print("\nCommunity size distribution:")
        for comm_id, size in sorted(community_sizes.items(), key=lambda x: x[1], reverse=True):
            print(f"  Community {comm_id}: {size} nodes")
        
        # Integrate with DSL: Find hubs in each community
        print("\n[4.2] Hub Identification per Community")
        print("-" * 80)
        
        # Group nodes by community
        community_nodes = {}
        for node, comm in partition.items():
            if comm not in community_nodes:
                community_nodes[comm] = []
            community_nodes[comm].append(node)
        
        # For top 3 communities, find the highest degree node
        for comm_id in list(sorted(community_sizes.keys(), 
                                    key=lambda x: community_sizes[x], 
                                    reverse=True))[:3]:
            nodes_in_comm = community_nodes[comm_id]
            
            # Find highest degree node in this community
            node_degrees = [(node, network.core_network.degree(node)) 
                           for node in nodes_in_comm]
            hub = max(node_degrees, key=lambda x: x[1])
            
            print(f"Community {comm_id} ({len(nodes_in_comm)} nodes):")
            print(f"  Hub node: {hub[0]} (degree: {hub[1]})")
        
        return partition
        
    except Exception as e:
        print(f"Community detection failed: {e}")
        print("Note: Louvain requires python-louvain package.")
        return {}


def demonstrate_convenience_functions(network: multinet.multi_layer_network) -> None:
    """Demonstrate convenience functions for common operations.
    
    Args:
        network: The multilayer network to analyze
    """
    print("\n" + "=" * 80)
    print("PART 5: CONVENIENCE FUNCTIONS")
    print("=" * 80)
    
    print("\n[5.1] select_nodes_by_layer()")
    print("-" * 80)
    social_nodes = select_nodes_by_layer(network, 'social')
    print(f"Nodes in social layer: {len(social_nodes)}")
    
    print("\n[5.2] select_high_degree_nodes()")
    print("-" * 80)
    high_deg_nodes = select_high_degree_nodes(network, min_degree=2)
    print(f"Nodes with degree > 2: {len(high_deg_nodes)}")
    
    high_deg_social = select_high_degree_nodes(network, min_degree=2, layer='social')
    print(f"Social layer nodes with degree > 2: {len(high_deg_social)}")
    
    print("\n[5.3] compute_centrality_for_layer()")
    print("-" * 80)
    centrality = compute_centrality_for_layer(network, 'work', 'degree_centrality')
    print(f"Work layer degree centrality (top 5):")
    for node, cent in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {node}: {cent:.4f}")


def demonstrate_first_class_method(network: multinet.multi_layer_network) -> None:
    """Demonstrate using execute_query as a first-class method.
    
    Args:
        network: The multilayer network to analyze
    """
    print("\n" + "=" * 80)
    print("PART 6: FIRST-CLASS METHOD USAGE")
    print("=" * 80)
    
    print("\n[6.1] Using network.execute_query() directly")
    print("-" * 80)
    print("The execute_query function is available directly on the network object!")
    
    # Use the method directly
    result = network.execute_query('SELECT nodes WHERE layer="work" AND degree >= 2')
    print(f"Query: SELECT nodes WHERE layer=\"work\" AND degree >= 2")
    print(f"Found {result['count']} work layer nodes with degree >= 2")
    
    for node in result['nodes']:
        print(f"  {node}")


def main():
    """Main function demonstrating the complete DSL-powered analysis workflow."""
    print("=" * 80)
    print("PY3PLEX DSL FLAGSHIP EXAMPLE")
    print("Complete Multilayer Network Analysis Workflow")
    print("=" * 80)
    
    # Step 1: Create sample network
    print("\n[SETUP] Creating sample multilayer network...")
    network = create_sample_network()
    print(f"Created network: {network}")
    print(f"  - Nodes: {len(list(network.get_nodes()))}")
    print(f"  - Edges: {len(list(network.get_edges()))}")
    
    # Step 2: Demonstrate DSL queries
    demonstrate_dsl_queries(network)
    
    # Step 3: Demonstrate centrality analysis
    centrality_results = demonstrate_centrality_analysis(network)
    
    # Step 4: Generate statistics
    demonstrate_statistics(network)
    
    # Step 5: Community detection
    partition = demonstrate_community_detection(network)
    
    # Step 6: Convenience functions
    demonstrate_convenience_functions(network)
    
    # Step 7: First-class method
    demonstrate_first_class_method(network)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
This flagship example demonstrated:

✓ DSL Query Syntax:
  - SELECT nodes/edges with WHERE conditions
  - Logical operators: AND, OR, NOT
  - Comparison operators: >, <, >=, <=, =, !=
  - COMPUTE clause for centrality measures

✓ Centrality Analysis:
  - Betweenness, closeness, degree centrality
  - Cross-layer comparison
  - Multilayer centrality with versatility scores

✓ Statistical Reports:
  - Basic network statistics
  - Degree distribution
  - Layer-specific analysis
  - Clustering coefficients

✓ Community Detection:
  - Louvain algorithm integration
  - Community size analysis
  - Hub identification per community

✓ Convenience Functions:
  - select_nodes_by_layer()
  - select_high_degree_nodes()
  - compute_centrality_for_layer()
  - network.execute_query() first-class method

For more details, see:
  - Documentation: docs/user_guide/dsl.rst
  - API Reference: py3plex.dsl module
  - Examples: examples/network_analysis/
""")


if __name__ == "__main__":
    main()
