#!/usr/bin/env python3
"""
Example: Multilayer Network Centrality Measures

This example demonstrates how to compute various centrality measures
for multilayer/multiplex networks using py3plex.

SKIP_CI: slow - Computing centrality measures takes more than 10 seconds
"""

from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality, compute_all_centralities
import numpy as np


def create_example_network():
    """Create a sample multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: A small social network (triangle + extra node)
    network.add_edges([
        ['Alice', 'Social', 'Bob', 'Social', 1],
        ['Bob', 'Social', 'Charlie', 'Social', 1],
        ['Charlie', 'Social', 'Alice', 'Social', 1],
        ['Alice', 'Social', 'David', 'Social', 1]
    ], input_type='list')

    # Layer 2: A collaboration network (different structure)
    network.add_edges([
        ['Alice', 'Collab', 'Bob', 'Collab', 2],
        ['Alice', 'Collab', 'Charlie', 'Collab', 2],
        ['Bob', 'Collab', 'David', 'Collab', 2],
        ['Charlie', 'Collab', 'David', 'Collab', 2]
    ], input_type='list')

    # Layer 3: A communication network (star topology)
    network.add_edges([
        ['Alice', 'Comm', 'Bob', 'Comm', 1],
        ['Alice', 'Comm', 'Charlie', 'Comm', 1],
        ['Alice', 'Comm', 'David', 'Comm', 1]
    ], input_type='list')

    return network


def print_centrality_results(centralities, title):
    """Pretty print centrality results."""
    print(f"\n{title}")
    print("=" * len(title))

    # Sort by centrality value (descending)
    sorted_results = sorted(centralities.items(), key=lambda x: x[1], reverse=True)

    for node, centrality in sorted_results:
        print(f"{str(node):25} {centrality:.4f}")


def main():
    """Main demonstration function."""
    print("Multilayer Network Centrality Measures Demo")
    print("=" * 45)

    # Create example network
    network = create_example_network()
    print(f"\nCreated multilayer network with {len(list(network.get_nodes()))} node-layer pairs")
    print(f"Network has {len(list(network.get_edges()))} edges")

    # Initialize centrality calculator
    calc = MultilayerCentrality(network)

    # ==================== DEGREE-BASED MEASURES ====================
    print("\n\n1. DEGREE-BASED MEASURES")
    print("-" * 30)

    # Layer-specific degree centrality
    layer_degrees = calc.layer_degree_centrality(weighted=False)
    print_centrality_results(layer_degrees, "Layer-Specific Degree Centrality")

    # Layer-specific strength (weighted degree)
    layer_strengths = calc.layer_degree_centrality(weighted=True)
    print_centrality_results(layer_strengths, "Layer-Specific Strength Centrality")

    # Overlapping degree (node-level)
    overlapping_degrees = calc.overlapping_degree_centrality(weighted=False)
    print_centrality_results(overlapping_degrees, "Overlapping Degree Centrality")

    # Participation coefficient
    participation = calc.participation_coefficient(weighted=False)
    print_centrality_results(participation, "Participation Coefficient")

    # ==================== EIGENVECTOR-BASED MEASURES ====================
    print("\n\n2. EIGENVECTOR-BASED MEASURES")
    print("-" * 35)

    # Multiplex eigenvector centrality
    eigenvector_centrality = calc.multiplex_eigenvector_centrality()
    print_centrality_results(eigenvector_centrality, "Multiplex Eigenvector Centrality")

    # Eigenvector versatility (node-level)
    versatility = calc.multiplex_eigenvector_versatility()
    print_centrality_results(versatility, "Eigenvector Versatility")

    # Katz-Bonacich centrality
    katz_centrality = calc.katz_bonacich_centrality(alpha=0.1)
    print_centrality_results(katz_centrality, "Katz-Bonacich Centrality")

    # PageRank centrality
    pagerank_centrality = calc.pagerank_centrality(damping=0.85)
    print_centrality_results(pagerank_centrality, "PageRank Centrality")

    # ==================== PATH-BASED MEASURES ====================
    print("\n\n3. PATH-BASED MEASURES")
    print("-" * 25)

    # Closeness centrality
    closeness_centrality = calc.multilayer_closeness_centrality()
    print_centrality_results(closeness_centrality, "Multilayer Closeness Centrality")

    # Betweenness centrality
    betweenness_centrality = calc.multilayer_betweenness_centrality()
    print_centrality_results(betweenness_centrality, "Multilayer Betweenness Centrality")

    # ==================== ADVANCED MEASURES ====================
    print("\n\n4. ADVANCED MEASURES")
    print("-" * 20)

    # HITS centrality
    hits_centrality = calc.hits_centrality()
    print_centrality_results(hits_centrality, "HITS Centrality")

    # Current-flow centrality measures
    current_flow_closeness = calc.current_flow_closeness_centrality()
    print_centrality_results(current_flow_closeness, "Current-Flow Closeness Centrality")

    current_flow_betweenness = calc.current_flow_betweenness_centrality()
    print_centrality_results(current_flow_betweenness, "Current-Flow Betweenness Centrality")

    # Communicability-based measures
    subgraph_centrality = calc.subgraph_centrality()
    print_centrality_results(subgraph_centrality, "Subgraph Centrality")

    total_communicability = calc.total_communicability()
    print_centrality_results(total_communicability, "Total Communicability")

    # K-core decomposition
    k_core = calc.multiplex_k_core()
    print_centrality_results(k_core, "Multiplex K-Core")

    # ==================== AGGREGATION EXAMPLES ====================
    print("\n\n5. AGGREGATION EXAMPLES")
    print("-" * 25)

    # Different ways to aggregate node-layer centralities to node level
    print("\nAggregating Eigenvector Centrality:")

    sum_agg = calc.aggregate_to_node_level(eigenvector_centrality, method='sum')
    print_centrality_results(sum_agg, "Sum Aggregation")

    max_agg = calc.aggregate_to_node_level(eigenvector_centrality, method='max')
    print_centrality_results(max_agg, "Max Aggregation")

    # Weighted aggregation (giving more weight to social layer)
    layer_weights = {'Social': 2.0, 'Collab': 1.5, 'Comm': 1.0}
    weighted_agg = calc.aggregate_to_node_level(eigenvector_centrality,
                                               method='weighted_sum',
                                               weights=layer_weights)
    print_centrality_results(weighted_agg, "Weighted Sum Aggregation")

    # ==================== COMPUTE ALL CENTRALITIES ====================
    print("\n\n6. COMPREHENSIVE ANALYSIS")
    print("-" * 28)

    # Compute all available centralities at once (including advanced measures)
    all_centralities = compute_all_centralities(network,
                                               include_path_based=True,
                                               include_advanced=True)

    print("\nAvailable centrality measures:")
    for measure_name in sorted(all_centralities.keys()):
        if isinstance(all_centralities[measure_name], dict):
            num_values = len(all_centralities[measure_name])
            print(f"  - {measure_name:35} ({num_values} values)")
        else:
            # Handle HITS which might return nested dict for directed networks
            print(f"  - {measure_name:35} (complex structure)")

    # ==================== INSIGHTS ====================
    print("\n\n7. NETWORK INSIGHTS")
    print("-" * 20)

    # Find most central nodes by different measures
    print("\nMost central nodes by different measures:")

    measures_to_check = {
        'Overlapping Degree': overlapping_degrees,
        'Participation Coeff': participation,
        'Eigenvector Versatility': versatility,
        'PageRank (aggregated)': calc.aggregate_to_node_level(pagerank_centrality, method='sum'),
        'Closeness (aggregated)': calc.aggregate_to_node_level(closeness_centrality, method='sum'),
        'Betweenness (aggregated)': calc.aggregate_to_node_level(betweenness_centrality, method='sum'),
        'Subgraph (aggregated)': calc.aggregate_to_node_level(subgraph_centrality, method='sum'),
        'K-Core (aggregated)': calc.aggregate_to_node_level(k_core, method='max')
    }

    for measure_name, centralities in measures_to_check.items():
        top_node = max(centralities.items(), key=lambda x: x[1])
        print(f"  {measure_name:20}: {top_node[0]} ({top_node[1]:.4f})")

    # Analyze layer-specific importance
    print("\nLayer-specific analysis:")
    layers = ['Social', 'Collab', 'Comm']

    for layer in layers:
        layer_centralities = calc.layer_degree_centrality(layer=layer, weighted=False)
        avg_degree = np.mean(list(layer_centralities.values()))
        max_degree = max(layer_centralities.values())
        print(f"  {layer} layer: avg_degree={avg_degree:.2f}, max_degree={max_degree}")

    print("\nDemo completed!")


if __name__ == "__main__":
    main()
