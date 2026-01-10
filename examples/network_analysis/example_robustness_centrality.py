"""Example: Robustness Centrality Analysis

This example demonstrates how to use robustness centrality to identify
critical nodes and layers in multilayer networks.

Robustness centrality measures how much a node or layer's removal impacts
the network, based on metrics like:
- Giant component size
- Average shortest path length
- Epidemic dynamics (SIS/SIR)
"""

import numpy as np
from py3plex.core import multinet
from py3plex.centrality import robustness_centrality


def build_example_network():
    """Build a small multilayer network for demonstration.

    Structure:
    - Layer L0: a--b--c--d (chain)
    - Layer L1: a--b, c--d (two pairs)
    - Layer L2: b--c (bridge)
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)

    edges = [
        # Layer 0: chain
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "d", "L0", 1.0],
        # Layer 1: two pairs
        ["a", "L1", "b", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        # Layer 2: bridge layer
        ["b", "L2", "c", "L2", 1.0],
    ]

    net.add_edges(edges, input_type="list")
    return net


def example_node_robustness_giant_component():
    """Example 1: Node robustness based on giant component."""
    print("\n" + "="*70)
    print("Example 1: Node Robustness - Giant Component")
    print("="*70)

    net = build_example_network()

    # Compute robustness scores
    scores = robustness_centrality(
        net,
        target="node",
        metric="giant_component",
        seed=42
    )

    # Sort by robustness (highest first)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("\nNode Robustness Scores (impact on giant component):")
    print("-" * 70)
    for node, score in sorted_scores:
        print(f"  {node}: {score:.4f}")

    print("\nInterpretation:")
    print("- Higher score = more critical for network connectivity")
    print("- Nodes b and c are bridges between layers, so they have high impact")


def example_node_robustness_shortest_path():
    """Example 2: Node robustness based on average shortest path."""
    print("\n" + "="*70)
    print("Example 2: Node Robustness - Average Shortest Path")
    print("="*70)

    net = build_example_network()

    scores = robustness_centrality(
        net,
        target="node",
        metric="avg_shortest_path",
        seed=42
    )

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("\nNode Robustness Scores (impact on path length):")
    print("-" * 70)
    for node, score in sorted_scores:
        print(f"  {node}: {score:.4f}")

    print("\nInterpretation:")
    print("- Higher score = removing this node increases path lengths more")
    print("- Bridge nodes cause the most disruption to shortest paths")


def example_layer_robustness():
    """Example 3: Layer robustness."""
    print("\n" + "="*70)
    print("Example 3: Layer Robustness - Giant Component")
    print("="*70)

    net = build_example_network()

    scores = robustness_centrality(
        net,
        target="layer",
        metric="giant_component",
        seed=42
    )

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("\nLayer Robustness Scores (impact on giant component):")
    print("-" * 70)
    for layer, score in sorted_scores:
        print(f"  {layer}: {score:.4f}")

    print("\nInterpretation:")
    print("- Higher score = layer is more important for connectivity")
    print("- L0 has the most edges, so removing it has highest impact")


def example_sis_dynamics():
    """Example 4: Node robustness based on SIS epidemic dynamics."""
    print("\n" + "="*70)
    print("Example 4: Node Robustness - SIS Epidemic Dynamics")
    print("="*70)

    net = build_example_network()

    scores = robustness_centrality(
        net,
        target="node",
        metric="sis_final_prevalence",
        dynamics_params={
            "beta": 0.4,     # Infection rate
            "mu": 0.1,       # Recovery rate
            "steps": 100,    # Simulation steps
        },
        seed=42
    )

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("\nNode Robustness Scores (impact on epidemic prevalence):")
    print("-" * 70)
    for node, score in sorted_scores:
        print(f"  {node}: {score:.4f}")

    print("\nInterpretation:")
    print("- Higher score = removing this node reduces epidemic prevalence more")
    print("- Note: Can be negative if removal increases prevalence (stochastic)")
    print("- Central nodes typically have higher impact on disease spread")


def example_sir_dynamics():
    """Example 5: Node robustness based on SIR epidemic dynamics."""
    print("\n" + "="*70)
    print("Example 5: Node Robustness - SIR Epidemic Dynamics")
    print("="*70)

    net = build_example_network()

    scores = robustness_centrality(
        net,
        target="node",
        metric="sir_final_size",
        dynamics_params={
            "beta": 0.3,     # Infection rate
            "gamma": 0.1,    # Recovery rate
            "steps": 150,    # Simulation steps
        },
        seed=42
    )

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("\nNode Robustness Scores (impact on epidemic final size):")
    print("-" * 70)
    for node, score in sorted_scores:
        print(f"  {node}: {score:.4f}")

    print("\nInterpretation:")
    print("- Higher score = removing this node reduces final epidemic size more")
    print("- Shows which nodes are most critical for disease propagation")


def example_sampling():
    """Example 6: Using sampling for large networks."""
    print("\n" + "="*70)
    print("Example 6: Sampling for Large Networks")
    print("="*70)

    net = build_example_network()

    # Only measure a subset of nodes
    sample_nodes = [("a", "L0"), ("b", "L0"), ("c", "L0")]

    scores = robustness_centrality(
        net,
        target="node",
        metric="giant_component",
        sample_nodes=sample_nodes,
        seed=42
    )

    print(f"\nMeasured {len(scores)} nodes (sampled from network):")
    print("-" * 70)
    for node, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {node}: {score:.4f}")

    print("\nUse case:")
    print("- For large networks, measure only a subset of nodes")
    print("- Speeds up computation while still identifying critical nodes")


def compare_metrics():
    """Example 7: Compare different metrics on the same network."""
    print("\n" + "="*70)
    print("Example 7: Comparing Multiple Metrics")
    print("="*70)

    net = build_example_network()

    # Target node to analyze
    target_node = ("b", "L0")

    metrics = {
        "giant_component": {},
        "avg_shortest_path": {},
        "sis_final_prevalence": {"beta": 0.4, "mu": 0.1, "steps": 50},
        "sir_final_size": {"beta": 0.3, "gamma": 0.1, "steps": 50},
    }

    print(f"\nRobustness scores for node {target_node}:")
    print("-" * 70)

    for metric_name, params in metrics.items():
        scores = robustness_centrality(
            net,
            target="node",
            metric=metric_name,
            dynamics_params=params if params else None,
            seed=42
        )
        score = scores.get(target_node, 0.0)
        print(f"  {metric_name:25s}: {score:8.4f}")

    print("\nInterpretation:")
    print("- Different metrics reveal different aspects of node importance")
    print("- Structural metrics (giant_component, path length) show connectivity role")
    print("- Dynamic metrics (SIS/SIR) show importance for spreading processes")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ROBUSTNESS CENTRALITY EXAMPLES")
    print("="*70)
    print("\nThis script demonstrates various ways to measure node and layer")
    print("importance in multilayer networks using robustness centrality.")

    # Run all examples
    example_node_robustness_giant_component()
    example_node_robustness_shortest_path()
    example_layer_robustness()
    example_sis_dynamics()
    example_sir_dynamics()
    example_sampling()
    compare_metrics()

    print("\n" + "="*70)
    print("For more information, see the documentation:")
    print("  help(robustness_centrality)")
    print("="*70 + "\n")
