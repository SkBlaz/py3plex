"""
Basic Example: Generating and Visualizing Random Multilayer Networks

This example demonstrates how to:
1. Generate a random multilayer Erdős-Rényi (ER) network
2. Visualize the network structure

The random_multilayer_ER function creates a multilayer network where each layer
is an Erdős-Rényi random graph with the specified parameters.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

import os

from py3plex.core import random_generators


def generate_random_multilayer_network(
    num_nodes: int = 200,
    num_layers: int = 6,
    edge_prob: float = 0.09,
    directed: bool = True,
):
    """
    Generate a random multilayer Erdős-Rényi network.

    Args:
        num_nodes: Number of nodes in the network
        num_layers: Number of layers
        edge_prob: Probability of edge creation between any two nodes
        directed: Whether the network is directed

    Returns:
        Generated multilayer network
    """
    print("Generating random multilayer Erdős-Rényi network...")
    print("Parameters:")
    print(f"  - Number of nodes: {num_nodes}")
    print(f"  - Number of layers: {num_layers}")
    print(f"  - Edge probability: {edge_prob}")
    print(f"  - Directed: {directed}")

    # Generate the multilayer network
    network = random_generators.random_multilayer_ER(
        num_nodes, num_layers, edge_prob, directed=directed
    )

    print("\nNetwork generated successfully!")
    return network


def visualize_network_if_interactive(network) -> None:
    """
    Visualize the network if not in CI mode.

    Args:
        network: The multilayer network to visualize
    """
    # In CI mode, skip interactive visualization
    if os.environ.get("MPLBACKEND") == "Agg":
        print("Running in CI mode - skipping interactive visualization")
    else:
        print("Visualizing the network (close the window to exit)...")
        # Visualize the network without node labels for clarity
        network.visualize_network(show=True, no_labels=True)


def main() -> None:
    """Generate and visualize a random multilayer network."""
    network = generate_random_multilayer_network(
        num_nodes=200, num_layers=6, edge_prob=0.09, directed=True
    )
    visualize_network_if_interactive(network)


if __name__ == "__main__":
    main()
