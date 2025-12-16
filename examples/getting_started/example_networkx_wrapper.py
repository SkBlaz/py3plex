"""
NetworkX wrapper for multilayer networks.

Builds a random multilayer Erdős-Rényi network, aggregates it, and runs a
NetworkX centrality algorithm through `monoplex_nx_wrapper`. Prerequisites:
py3plex installed; NetworkX is already bundled as a dependency.
"""

from __future__ import annotations

import random
import numpy as np
from py3plex.core import random_generators

DEFAULT_SEED = 42


def main() -> int:
    """Generate a network and compute centrality."""
    np.random.seed(DEFAULT_SEED)
    random.seed(DEFAULT_SEED)

    print("Generating random multilayer Erdős-Rényi network...")
    print("Parameters: 300 nodes, 6 layers, edge probability 0.05")

    er_net = random_generators.random_multilayer_ER(
        300,
        6,
        0.05,
        directed=False,
    )

    print("Network generated successfully!")
    print("\nComputing degree centrality for all nodes...")
    print("(This aggregates the network across all layers)")

    centralities = er_net.monoplex_nx_wrapper("degree_centrality")

    print(f"\nTotal nodes analyzed: {len(centralities)}")
    print("\nTop 5 nodes by degree centrality:")
    print("-" * 50)

    top_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (node, centrality) in enumerate(top_nodes, 1):
        print(f"{rank}. Node {node}: {centrality:.4f}")

    print("\nNote: Centrality values range from 0 to 1, where 1 means")
    print("the node is connected to all other nodes in the network.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
