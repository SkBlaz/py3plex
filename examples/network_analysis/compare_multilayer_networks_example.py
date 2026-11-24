#!/usr/bin/env python3
"""
Example: Statistical Comparison of Multilayer Networks

This script demonstrates how to use py3plex's statistical comparison framework
to describe individual networks and test differences between independent cohorts.
"""

from py3plex.core import multinet
from py3plex.datasets import make_random_multiplex
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

    print("\n3. Descriptive comparison of the two networks")
    descriptive = compare_multilayer_networks(
        [net1, net2], metrics=["density", "average_degree", "node_activity"]
    )
    summaries = ["metric", "layer", "mean_group_0", "mean_group_1"]
    print(descriptive[summaries].to_string(index=False))

    print("\n4. Permutation test on two cohorts of independent graphs")
    cohorts = [
        [
            make_random_multiplex(
                n_nodes=20, n_layers=2, p=probability,
                random_state=100 * group + replicate,
            )
            for replicate in range(8)
        ]
        for group, probability in enumerate((0.15, 0.35))
    ]
    results = compare_multilayer_networks(
        cohorts, metrics=["density", "average_degree"],
        n_permutations=999, correction="fdr_bh", seed=42,
    )
    columns = summaries + ["p_value", "adjusted_p_value", "significant"]
    print(results[columns].to_string(index=False))


if __name__ == "__main__":
    main()
