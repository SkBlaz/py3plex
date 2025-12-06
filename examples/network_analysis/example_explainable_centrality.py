#!/usr/bin/env python3
"""
Example: Explainable Centrality in Multilayer Networks

Demonstrates how to use the explainable centrality module to get
human-readable explanations for why certain nodes are central.

This example shows:
1. Creating a multilayer network with a clear bridge node
2. Computing various centrality measures
3. Getting detailed explanations for individual nodes
4. Getting explanations for top-k central nodes
"""

from py3plex.core import multinet
from py3plex.algorithms.centrality.explain import (
    explain_node_centrality,
    explain_top_k_central_nodes,
)
from py3plex.algorithms.centrality_toolkit import (
    multiplex_degree_centrality,
)


def create_bridge_network():
    """
    Create a network where one node bridges two layers.

    Structure:
        Layer 1: A-B-C (chain)
        Layer 2: B-D-E (chain)

    Node B is the bridge connecting both layers.
    """
    net = multinet.multi_layer_network(directed=False)

    # Layer 1: Social network
    net.add_edges(
        [
            ["A", "social", "B", "social", 1],
            ["B", "social", "C", "social", 1],
        ],
        input_type="list",
    )

    # Layer 2: Collaboration network
    net.add_edges(
        [
            ["B", "collaboration", "D", "collaboration", 1],
            ["D", "collaboration", "E", "collaboration", 1],
        ],
        input_type="list",
    )

    return net


def main():
    """Demonstrate explainable centrality features."""
    print("=" * 70)
    print("Explainable Centrality Demo")
    print("=" * 70)
    print()

    # Create network
    print("Creating a multilayer network with a bridge node...")
    net = create_bridge_network()
    print(f"Network has {len(list(net.get_nodes()))} nodes")
    print()

    # Compute centrality
    print("Computing degree centrality...")
    centrality_scores = multiplex_degree_centrality(net, normalized=False)
    print(f"Centrality scores: {centrality_scores}")
    print()

    # Explain individual node
    print("-" * 70)
    print("Explaining node B (the bridge node):")
    print("-" * 70)

    bridge_node = ("B", "social")
    if bridge_node in centrality_scores:
        explanation = explain_node_centrality(
            net, bridge_node, centrality_scores, method="degree"
        )

        print(f"\nNode: {bridge_node}")
        print(f"Centrality Score: {explanation['score']}")
        print(f"Rank: {explanation['rank']} out of {len(centrality_scores)} nodes")
        print(f"Percentile: {explanation['percentile']}%")
        print()
        print("Per-Layer Degree:")
        for layer, degree in explanation["degree_per_layer"].items():
            print(f"  {layer}: {degree}")
        print()
        print("Layer Contributions:")
        for layer, contrib in explanation["layer_breakdown"].items():
            print(f"  {layer}: {contrib}")
        print()
        print(f"Inter-layer edges: {explanation['num_interlayer_edges']}")
        print(f"Local triangles: {explanation['local_motifs'].get('triangles', 0)}")
    print()

    # Explain a peripheral node
    print("-" * 70)
    print("Explaining node A (peripheral node):")
    print("-" * 70)

    peripheral_node = ("A", "social")
    if peripheral_node in centrality_scores:
        explanation = explain_node_centrality(
            net, peripheral_node, centrality_scores, method="degree"
        )

        print(f"\nNode: {peripheral_node}")
        print(f"Centrality Score: {explanation['score']}")
        print(f"Rank: {explanation['rank']} out of {len(centrality_scores)} nodes")
        print(f"Percentile: {explanation['percentile']}%")
        print()
        print("Per-Layer Degree:")
        for layer, degree in explanation["degree_per_layer"].items():
            print(f"  {layer}: {degree}")
        print()
        print(f"Inter-layer edges: {explanation['num_interlayer_edges']}")
    print()

    # Explain top-k nodes
    print("=" * 70)
    print("Top-3 Most Central Nodes:")
    print("=" * 70)

    top_k_explanations = explain_top_k_central_nodes(
        net, centrality_scores, method="degree", k=3
    )

    for i, (node, explanation) in enumerate(top_k_explanations.items(), 1):
        print(f"\n{i}. Node: {node}")
        print(f"   Score: {explanation['score']}")
        print(f"   Layers: {list(explanation['degree_per_layer'].keys())}")
        print(f"   Total degree: {sum(explanation['degree_per_layer'].values())}")
        if explanation["num_interlayer_edges"] > 0:
            print(
                f"   ** Bridge node: {explanation['num_interlayer_edges']} inter-layer edges"
            )

    print()
    print("=" * 70)
    print("Key Insights:")
    print("=" * 70)
    print("- Node B has the highest centrality because it bridges two layers")
    print("- Peripheral nodes (A, C, E) have lower centrality")
    print("- Inter-layer edges identify bridge nodes automatically")
    print()


if __name__ == "__main__":
    main()
