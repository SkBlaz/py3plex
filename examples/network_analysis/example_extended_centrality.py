#!/usr/bin/env python3
"""
Example: Extended Centrality Metrics for Multilayer Networks

This example demonstrates the usage of extended centrality metrics (18-30)
implemented in py3plex for multilayer network analysis.

Author: py3plex contributors
Date: 2025

SKIP_CI: slow - Computing multiple centrality metrics takes more than 10 seconds
"""

from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.centrality import (
    MultilayerCentrality,
    compute_all_centralities,
)


def create_example_network():
    """Create a simple multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)

    # Layer 1: Social network (star topology)
    network.add_edges(
        [
            ["Alice", "L1", "Bob", "L1", 1],
            ["Alice", "L1", "Charlie", "L1", 1],
            ["Alice", "L1", "David", "L1", 1],
            ["Alice", "L1", "Eve", "L1", 1],
        ],
        input_type="list",
    )

    # Layer 2: Collaboration network (mesh topology)
    network.add_edges(
        [
            ["Alice", "L2", "Bob", "L2", 1],
            ["Bob", "L2", "Charlie", "L2", 1],
            ["Charlie", "L2", "David", "L2", 1],
            ["David", "L2", "Eve", "L2", 1],
            ["Eve", "L2", "Alice", "L2", 1],
        ],
        input_type="list",
    )

    return network


def example_information_centrality(calc):
    """Example: Information Centrality (Stephenson-Zelen style)."""
    print("\n" + "=" * 70)
    print("18. Information Centrality")
    print("=" * 70)

    info_cent = calc.information_centrality()

    print("\nInformation centrality measures node importance based on")
    print("information flow through the network using Laplacian inverse.\n")

    # Show top 3 nodes
    sorted_nodes = sorted(info_cent.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 node-layer pairs:")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_accessibility(calc):
    """Example: Accessibility (entropy-based reach)."""
    print("\n" + "=" * 70)
    print("21. Accessibility Centrality")
    print("=" * 70)

    accessibility = calc.accessibility_centrality(h=2)

    print("\nAccessibility measures the diversity of nodes reachable within h steps")
    print("using entropy of the probability distribution.\n")

    # Show values for all nodes
    sorted_nodes = sorted(accessibility.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 most accessible node-layer pairs (h=2):")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_percolation(calc):
    """Example: Percolation Centrality."""
    print("\n" + "=" * 70)
    print("22. Percolation Centrality")
    print("=" * 70)

    percolation = calc.percolation_centrality(edge_activation_prob=0.5, trials=50)

    print("\nPercolation centrality measures node importance based on")
    print("maintaining network connectivity under random edge failures.\n")

    sorted_nodes = sorted(percolation.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 most robust node-layer pairs:")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_spreading(calc):
    """Example: Spreading (Epidemic) Centrality."""
    print("\n" + "=" * 70)
    print("23. Spreading (Epidemic) Centrality")
    print("=" * 70)

    spreading = calc.spreading_centrality(beta=0.2, mu=0.1, trials=20, steps=50)

    print("\nSpreading centrality measures how influential a node is in spreading")
    print("information or disease through the network (SIR model).\n")

    sorted_nodes = sorted(spreading.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 most influential spreaders:")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_collective_influence(calc):
    """Example: Collective Influence."""
    print("\n" + "=" * 70)
    print("24. Collective Influence")
    print("=" * 70)

    ci = calc.collective_influence(radius=2)

    print("\nCollective influence identifies influential spreaders by considering")
    print("not just immediate neighbors but also nodes at distance l.\n")

    sorted_nodes = sorted(ci.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 most influential nodes (radius=2):")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_harmonic_closeness(calc):
    """Example: Harmonic Closeness."""
    print("\n" + "=" * 70)
    print("27. Harmonic Closeness Centrality")
    print("=" * 70)

    harmonic = calc.harmonic_closeness_centrality()

    print("\nHarmonic closeness handles disconnected graphs better than")
    print("standard closeness by summing reciprocals of distances.\n")

    sorted_nodes = sorted(harmonic.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 most central nodes:")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_bridging(calc):
    """Example: Bridging Centrality."""
    print("\n" + "=" * 70)
    print("28. Bridging Centrality")
    print("=" * 70)

    bridging = calc.bridging_centrality()

    print("\nBridging centrality combines betweenness with the bridging coefficient,")
    print("identifying nodes that connect sparse regions of the network.\n")

    sorted_nodes = sorted(bridging.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top 3 bridge nodes:")
    for (node, layer), value in sorted_nodes:
        print(f"  {node} (Layer {layer}): {value:.4f}")


def example_lp_aggregation(calc):
    """Example: Lp-Aggregated Centrality."""
    print("\n" + "=" * 70)
    print("30. Lp-Aggregated Centrality")
    print("=" * 70)

    # Get layer degrees
    layer_degrees = calc.layer_degree_centrality(weighted=False)

    # L2 norm aggregation
    l2_agg = calc.lp_aggregated_centrality(layer_degrees, p=2)

    # L-infinity norm aggregation
    linf_agg = calc.lp_aggregated_centrality(layer_degrees, p=float("inf"))

    print("\nLp-aggregated centrality provides a framework for combining")
    print("per-layer centrality measures using different Lp norms.\n")

    print("L2 norm aggregation (Euclidean):")
    sorted_nodes = sorted(l2_agg.items(), key=lambda x: x[1], reverse=True)
    for node, value in sorted_nodes:
        print(f"  {node}: {value:.4f}")

    print("\nL-infinity norm aggregation (Maximum):")
    sorted_nodes = sorted(linf_agg.items(), key=lambda x: x[1], reverse=True)
    for node, value in sorted_nodes:
        print(f"  {node}: {value:.4f}")


def example_compute_all(network):
    """Example: Computing all extended centrality metrics at once."""
    print("\n" + "=" * 70)
    print("Computing All Extended Centrality Metrics")
    print("=" * 70)

    results = compute_all_centralities(network, include_extended=True)

    print(f"\nComputed {len(results)} centrality measures:")
    for key in sorted(results.keys()):
        if isinstance(results[key], dict):
            print(f"  - {key}: {len(results[key])} values")
        else:
            # For measures that return nested dicts (like HITS)
            print(f"  - {key}: nested structure")


def main():
    """Run all examples."""
    print("=" * 70)
    print("Extended Centrality Metrics Examples")
    print("py3plex - Multilayer Network Analysis")
    print("=" * 70)

    # Create example network
    network = create_example_network()
    calc = MultilayerCentrality(network)

    # Run examples
    example_information_centrality(calc)
    example_accessibility(calc)
    example_percolation(calc)
    example_spreading(calc)
    example_collective_influence(calc)
    example_harmonic_closeness(calc)
    example_bridging(calc)
    example_lp_aggregation(calc)

    # Compute all at once
    example_compute_all(network)

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
