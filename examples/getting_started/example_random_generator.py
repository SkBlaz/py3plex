"""
Generate and (optionally) visualize a random multilayer network.

Creates a multilayer Erdos-Renyi network and explains key parameters.
Prerequisites: py3plex installed; matplotlib is optional for visualization
and skipped by default (backend set to Agg).
"""

from __future__ import annotations

import os
import random
from typing import Any

import numpy as np
from py3plex.core import random_generators

DEFAULT_SEED = 42


def generate_random_multilayer_network(
    num_nodes: int = 200,
    num_layers: int = 6,
    edge_prob: float = 0.09,
    directed: bool = True,
) -> Any:
    """Generate a random multilayer Erdos-Renyi network."""
    np.random.seed(DEFAULT_SEED)
    random.seed(DEFAULT_SEED)

    print("Generating random multilayer Erdos-Renyi network...")
    print("Parameters:")
    print(f"  - Number of nodes: {num_nodes}")
    print(f"  - Number of layers: {num_layers}")
    print(f"  - Edge probability: {edge_prob}")
    print(f"  - Directed: {directed}")

    network = random_generators.random_multilayer_ER(
        num_nodes,
        num_layers,
        edge_prob,
        directed=directed,
    )

    print("\nNetwork generated successfully!")
    return network


def visualize_network_if_interactive(network) -> None:
    """Visualize the network if a GUI backend is available."""
    if os.environ.get("MPLBACKEND") == "Agg":
        print("Running in non-interactive mode - skipping visualization")
        return

    print("Visualizing the network (close the window to exit)...")
    network.visualize_network(show=True, no_labels=True)


def main() -> int:
    """Generate a network; visualization is skipped unless backend allows GUI."""
    os.environ.setdefault("MPLBACKEND", "Agg")

    network = generate_random_multilayer_network(
        num_nodes=200,
        num_layers=6,
        edge_prob=0.09,
        directed=True,
    )
    visualize_network_if_interactive(network)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
