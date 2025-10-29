#!/usr/bin/env python3
"""
Example: Statistical Comparison of Multilayer Networks

This script demonstrates how to use py3plex's statistical comparison framework
to compare multilayer networks and detect statistically significant differences.
"""

from py3plex.core import multinet
from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks


def main():
    """Main demonstration function."""
    
    print("=" * 70)
    print("Statistical Comparison of Multilayer Networks - Example")
    print("=" * 70)
    
    # Create Network 1: Dense social network
    print("\n1. Creating first network (dense)...")
    net1 = multinet.multi_layer_network(directed=False)
    net1.add_edges([
        # Facebook layer - dense connections
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'David', 'facebook', 1],
        # Twitter layer
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Bob', 'twitter', 'Carol', 'twitter', 1],
        # Inter-layer connections
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
    ], input_type='list')
    
    print(f"   Network 1: {len(list(net1.get_nodes()))} nodes, {len(list(net1.get_edges()))} edges")
    
    # Create Network 2: Sparse social network
    print("\n2. Creating second network (sparse)...")
    net2 = multinet.multi_layer_network(directed=False)
    net2.add_edges([
        # Facebook layer - sparse
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Carol', 'facebook', 'David', 'facebook', 1],
        # Twitter layer
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        # Inter-layer connections
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
    ], input_type='list')
    
    print(f"   Network 2: {len(list(net2.get_nodes()))} nodes, {len(list(net2.get_edges()))} edges")
    
    # Perform statistical comparison
    print("\n3. Comparing networks using permutation test...")
    results = compare_multilayer_networks(
        [net1, net2],
        metrics=['density', 'average_degree', 'node_activity'],
        test='permutation',
        n_permutations=1000,
        correction='fdr_bh',
        alpha=0.05
    )
    
    print("\n4. Results:")
    print("-" * 70)
    print(results.to_string(index=False))
    
    # Show significant differences
    print("\n5. Statistically Significant Differences (α = 0.05):")
    print("-" * 70)
    significant = results[results['significant']]
    if len(significant) > 0:
        for _, row in significant.iterrows():
            print(f"   Metric: {row['metric']}")
            print(f"   Layer: {row['layer']}")
            print(f"   P-value: {row['p_value']:.4f}")
            print(f"   Adjusted P-value: {row['adjusted_p_value']:.4f}")
            print(f"   Effect size: {row['effect_size']:.4f}")
            print(f"   Mean Group 0: {row['mean_group_0']:.4f}")
            print(f"   Mean Group 1: {row['mean_group_1']:.4f}")
            print()
    else:
        print("   No statistically significant differences found.")
    
    # Example with multiple networks
    print("\n6. Comparing three networks using Kruskal-Wallis test...")
    
    # Create third network
    net3 = multinet.multi_layer_network(directed=False)
    net3.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
    ], input_type='list')
    
    results_multi = compare_multilayer_networks(
        [net1, net2, net3],
        metrics=['density'],
        test='kruskal',
        correction='bonferroni',
        alpha=0.05
    )
    
    print("\n   Multi-network comparison results:")
    print("-" * 70)
    print(results_multi[['metric', 'layer', 'p_value', 'adjusted_p_value', 'significant']].to_string(index=False))
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
