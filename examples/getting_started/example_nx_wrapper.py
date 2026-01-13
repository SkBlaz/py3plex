"""
Betweenness centrality on a multilayer network.

Generates a random multilayer Erdős-Rényi graph, aggregates it, and runs
NetworkX betweenness centrality through `monoplex_nx_wrapper`. Prerequisites:
py3plex installed; no optional extras needed.

SKIP_CI: slow - Betweenness centrality on 300-node network may take more than 10 seconds
"""

from __future__ import annotations

import random
import numpy as np
from py3plex.core import random_generators

DEFAULT_SEED = 42


def main() -> int:
    """Compute betweenness centrality on a random multilayer network."""
    np.random.seed(DEFAULT_SEED)
    random.seed(DEFAULT_SEED)

    print("Generating random multilayer Erdős-Rényi network...")
    print("Parameters: 300 nodes, 6 layers, edge probability 0.05")

    multilayer_network = random_generators.random_multilayer_ER(
        300,
        6,
        0.05,
        directed=False,
    )

    print("Network generated successfully!")
    print("\nComputing betweenness centrality...")
    print("(This measures how often nodes act as bridges between other nodes)\n")

    centralities = multilayer_network.monoplex_nx_wrapper("betweenness_centrality")

    print(f"Total nodes analyzed: {len(centralities)}")
    print("\nTop 10 nodes by betweenness centrality:")
    print("-" * 70)

    top_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:10]
    for rank, (node, centrality) in enumerate(top_nodes, 1):
        print(f"{rank:2d}. Node {node}: {centrality:.6f}")

    print("\n" + "=" * 70)
    print("Interpretation:")
    print("  - Higher values indicate nodes that bridge different network regions")
    print("  - These nodes are critical for network connectivity")
    print("  - Removing high-betweenness nodes can fragment the network")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
