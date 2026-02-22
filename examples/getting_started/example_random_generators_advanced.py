"""
Advanced random multilayer graph generators.

Demonstrates the multilayer Erdos-Renyi generator and highlights other
available generators (Barabasi-Albert, SBM variants). Prerequisites:
py3plex installed; no optional dependencies required.
"""

from __future__ import annotations

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.advanced_random_generators import multilayer_erdos_renyi

DEFAULT_SEED = 42


def main() -> int:
    """Generate a multilayer ER graph and convert it to py3plex."""
    print("=== Random Graph Generators Demo ===\n")

    print("Generating multilayer Erdos-Renyi network...")
    graph = multilayer_erdos_renyi(
        n=20,
        p=0.2,
        num_layers=3,
        interlayer_prob=0.1,
        seed=DEFAULT_SEED,
    )

    print(f"\nGenerated multilayer ER network:")
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")

    net = multi_layer_network(network_type="multilayer", directed=False)
    net.load_network(graph, input_type="nx")

    print(f"\nConverted to py3plex network:")
    print(f"  {net}")

    print("\nAvailable generators:")
    print("  - multilayer_erdos_renyi: Random edges")
    print("  - multilayer_barabasi_albert: Scale-free networks")
    print("  - multilayer_stochastic_block_model: Community structure")
    print("  - multilayer_sbm_with_dependencies: Layer-dependent communities\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
