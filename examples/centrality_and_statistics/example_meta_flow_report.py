#!/usr/bin/env python3
"""
Example: Meta Flow Report - Comprehensive Multilayer Network Analysis

This example demonstrates how to use the MetaFlowReport class to conduct
multiple analyses at once, including centralities, communities, and statistics.
This is a convenient way to get a comprehensive view of your multilayer network.
"""

from py3plex.core import multinet
from py3plex.algorithms.meta_flow_report import MetaFlowReport, run_meta_analysis


def create_example_network():
    """Create a sample multilayer social network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Facebook network
    network.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'David', 'facebook', 1],
        ['Carol', 'facebook', 'David', 'facebook', 1],
        ['David', 'facebook', 'Eve', 'facebook', 1],
    ], input_type='list')
    
    # Layer 2: Twitter network
    network.add_edges([
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Alice', 'twitter', 'Eve', 'twitter', 1],
        ['Bob', 'twitter', 'David', 'twitter', 1],
        ['Carol', 'twitter', 'David', 'twitter', 1],
        ['David', 'twitter', 'Eve', 'twitter', 1],
    ], input_type='list')
    
    # Layer 3: LinkedIn network
    network.add_edges([
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Bob', 'linkedin', 'David', 'linkedin', 1],
        ['Carol', 'linkedin', 'David', 'linkedin', 1],
        ['Carol', 'linkedin', 'Eve', 'linkedin', 1],
    ], input_type='list')
    
    # Inter-layer connections (same person across platforms)
    network.add_edges([
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Alice', 'twitter', 'Alice', 'linkedin', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Bob', 'twitter', 'Bob', 'linkedin', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
        ['Carol', 'twitter', 'Carol', 'linkedin', 1],
        ['David', 'facebook', 'David', 'twitter', 1],
        ['David', 'twitter', 'David', 'linkedin', 1],
        ['Eve', 'facebook', 'Eve', 'twitter', 1],
        ['Eve', 'twitter', 'Eve', 'linkedin', 1],
    ], input_type='list')
    
    return network


def example_basic_usage():
    """Example 1: Basic usage with default options."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Meta Flow Report")
    print("=" * 80)
    
    network = create_example_network()
    
    # Quick analysis with convenience function
    results = run_meta_analysis(
        network,
        include_centralities=True,
        include_communities=True,
        include_statistics=True,
        print_summary=True  # This will print a nice summary
    )
    
    print("\nAnalysis complete! Results stored in 'results' dictionary.")


def example_selective_analysis():
    """Example 2: Selective analysis - only centralities and statistics."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Selective Analysis (Centralities + Statistics only)")
    print("=" * 80)
    
    network = create_example_network()
    
    report = MetaFlowReport(network)
    
    # Run only specific analyses
    results = report.run_all_analyses(
        include_centralities=True,
        include_communities=False,  # Skip community detection
        include_statistics=True,
        include_path_based=False,   # Skip expensive path-based measures
        include_advanced=False       # Skip expensive advanced measures
    )
    
    # Print custom summary
    report.print_summary(results, top_n=3)


def example_advanced_analysis():
    """Example 3: Advanced analysis with all measures."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Advanced Analysis (All Measures)")
    print("=" * 80)
    print("Note: This may take longer due to expensive computations\n")
    
    network = create_example_network()
    
    report = MetaFlowReport(network)
    
    # Run comprehensive analysis with advanced measures
    results = report.run_all_analyses(
        include_centralities=True,
        include_communities=True,
        include_statistics=True,
        include_path_based=True,    # Include closeness, betweenness
        include_advanced=True,       # Include HITS, k-core, etc.
        community_methods=['louvain', 'leiden'],  # Specify methods
        gamma=1.0,                   # Resolution parameter
        omega=1.0                    # Inter-layer coupling
    )
    
    report.print_summary(results, top_n=5)


def example_custom_analysis():
    """Example 4: Custom analysis with individual component access."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: Custom Analysis (Individual Components)")
    print("=" * 80)
    
    network = create_example_network()
    
    report = MetaFlowReport(network)
    
    # Run analyses separately for fine-grained control
    print("\n1. Computing centralities...")
    centralities = report.compute_centralities(
        include_path_based=False,
        include_advanced=False
    )
    
    print("\n2. Running community detection...")
    communities = report.detect_communities(
        methods=['louvain'],
        gamma=1.0,
        omega=1.0
    )
    
    print("\n3. Computing statistics...")
    statistics = report.compute_statistics(
        include_advanced=False
    )
    
    # Manually inspect results
    print("\n" + "-" * 80)
    print("CUSTOM ANALYSIS RESULTS")
    print("-" * 80)
    
    # Show top nodes by overlapping degree
    if 'overlapping_degree' in centralities:
        print("\nTop 3 nodes by Overlapping Degree:")
        top_nodes = sorted(
            centralities['overlapping_degree'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for node, degree in top_nodes:
            print(f"  {node}: {degree}")
    
    # Show community structure
    if 'louvain' in communities:
        print("\nCommunity Structure (Louvain):")
        comm_counts = {}
        for comm_id in communities['louvain'].values():
            comm_counts[comm_id] = comm_counts.get(comm_id, 0) + 1
        print(f"  Number of communities: {len(comm_counts)}")
        print(f"  Sizes: {dict(sorted(comm_counts.items()))}")
    
    # Show layer densities
    if 'layer_densities' in statistics:
        print("\nLayer Densities:")
        for layer, density in statistics['layer_densities'].items():
            print(f"  {layer}: {density:.4f}")


def example_get_top_nodes():
    """Example 5: Extracting top nodes by specific measures."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 5: Extracting Top Nodes")
    print("=" * 80)
    
    network = create_example_network()
    
    report = MetaFlowReport(network)
    
    # Run basic analysis
    report.run_all_analyses(
        include_centralities=True,
        include_communities=False,
        include_statistics=True,
        include_path_based=False,
        include_advanced=False
    )
    
    print("\nTop 3 Nodes by Different Measures:")
    print("-" * 80)
    
    # Get top nodes by different centrality measures
    measures = [
        'overlapping_degree',
        'participation_coefficient',
        'multiplex_eigenvector'
    ]
    
    for measure in measures:
        top_nodes = report.get_top_nodes(
            measure=measure,
            n=3,
            category='centralities'
        )
        
        if top_nodes:
            print(f"\n{measure.replace('_', ' ').title()}:")
            for node, value in top_nodes:
                print(f"  {str(node):30} {value:.6f}")
    
    # Export results for further processing
    results_dict = report.export_to_dict()
    print(f"\n\nResults exported: {list(results_dict.keys())}")


def example_comparison():
    """Example 6: Comparing two different networks."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 6: Comparing Networks")
    print("=" * 80)
    
    # Create two different networks
    network1 = create_example_network()
    
    # Create a sparser network for comparison
    network2 = multinet.multi_layer_network(directed=False)
    network2.add_edges([
        ['Alice', 'L1', 'Bob', 'L1', 1],
        ['Carol', 'L1', 'David', 'L1', 1],
        ['Alice', 'L2', 'Carol', 'L2', 1],
        ['Bob', 'L2', 'David', 'L2', 1],
        ['Alice', 'L1', 'Alice', 'L2', 1],
        ['Bob', 'L1', 'Bob', 'L2', 1],
        ['Carol', 'L1', 'Carol', 'L2', 1],
        ['David', 'L1', 'David', 'L2', 1],
    ], input_type='list')
    
    # Analyze both networks
    print("\nNetwork 1 (Dense social network):")
    print("-" * 40)
    report1 = MetaFlowReport(network1)
    results1 = report1.run_all_analyses(
        include_centralities=True,
        include_communities=False,
        include_statistics=True,
        include_path_based=False,
        include_advanced=False
    )
    
    print("\nNetwork 2 (Sparse network):")
    print("-" * 40)
    report2 = MetaFlowReport(network2)
    results2 = report2.run_all_analyses(
        include_centralities=True,
        include_communities=False,
        include_statistics=True,
        include_path_based=False,
        include_advanced=False
    )
    
    # Compare layer densities
    print("\n" + "=" * 80)
    print("COMPARISON: Layer Densities")
    print("=" * 80)
    
    if ('statistics' in results1 and 'layer_densities' in results1['statistics'] and
        'statistics' in results2 and 'layer_densities' in results2['statistics']):
        
        print(f"\n{'Layer':<15} {'Network 1':<15} {'Network 2':<15} {'Difference':<15}")
        print("-" * 60)
        
        all_layers = set(results1['statistics']['layer_densities'].keys()) | \
                    set(results2['statistics']['layer_densities'].keys())
        
        for layer in sorted(all_layers):
            d1 = results1['statistics']['layer_densities'].get(layer, 0)
            d2 = results2['statistics']['layer_densities'].get(layer, 0)
            diff = d1 - d2
            print(f"{layer:<15} {d1:<15.4f} {d2:<15.4f} {diff:+.4f}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("META FLOW REPORT EXAMPLES")
    print("Comprehensive Multilayer Network Analysis")
    print("=" * 80)
    
    try:
        # Run examples
        example_basic_usage()
        example_selective_analysis()
        example_advanced_analysis()
        example_custom_analysis()
        example_get_top_nodes()
        example_comparison()
        
        print("\n\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("1. Use run_meta_analysis() for quick comprehensive analysis")
        print("2. Use MetaFlowReport class for fine-grained control")
        print("3. Disable expensive options (path_based, advanced) for large networks")
        print("4. Use get_top_nodes() to extract important nodes")
        print("5. Export results with export_to_dict() for further processing")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
