#!/usr/bin/env python3
"""
Example: Leiden community detection for multilayer networks.

Teaches:
- How to run Leiden on simple and randomly generated multilayer graphs
- How coupling (omega) and resolution (gamma) affect multilayer community structure

Prerequisites:
- `leidenalg` dependency of py3plex must be installed.

SKIP_CI: external_deps - Requires leidenalg package
"""

from __future__ import annotations

import sys
from typing import Dict

import numpy as np

try:
    from py3plex.algorithms.community_detection import leiden_multilayer
    from py3plex.core import multinet, random_generators
except ImportError as exc:  # pragma: no cover - surfaced to user
    leiden_multilayer = None
    multinet = None
    random_generators = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for individual sections."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def example_simple_network() -> None:
    """Example 1: Two-layer toy graph (triangle + line)."""
    _print_header("Example 1: Simple 2-layer network")
    network = multinet.multi_layer_network(directed=False)

    network.add_edges(
        [
            ["A", "L1", "B", "L1", 1],
            ["B", "L1", "C", "L1", 1],
            ["C", "L1", "A", "L1", 1],
        ],
        input_type="list",
    )
    network.add_edges(
        [
            ["A", "L2", "B", "L2", 1],
            ["B", "L2", "C", "L2", 1],
        ],
        input_type="list",
    )

    result = leiden_multilayer(
        network,
        interlayer_coupling=0.5,
        resolution=1.0,
        seed=DEFAULT_SEED,
        max_iter=100,
    )

    print(result.summary())
    print("\nCommunity assignments:")
    for (node, layer), community in sorted(result.communities.items()):
        print(f"  Node {node} in layer {layer}: Community {community}")


def example_random_er() -> None:
    """Example 2: Random multilayer Erdos-Renyi graph."""
    _print_header("Example 2: Random multilayer Erdos-Renyi network")
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=20,
        l=3,
        p=0.15,
        directed=False,
    )
    print(f"Network has {len(list(network.get_nodes()))} node-layer pairs")

    result = leiden_multilayer(
        network,
        interlayer_coupling=1.0,
        resolution=1.0,
        seed=DEFAULT_SEED,
    )

    print(result.summary())

    community_sizes: Dict[int, int] = {}
    for com in result.communities.values():
        community_sizes[com] = community_sizes.get(com, 0) + 1

    print("\nCommunity size distribution:")
    for com, size in sorted(community_sizes.items()):
        print(f"  Community {com}: {size} node-layer pairs")


def example_resolution_per_layer() -> None:
    """Example 3: Different resolution parameters per layer."""
    _print_header("Example 3: Layer-specific resolution parameters")
    network = multinet.multi_layer_network(directed=False)

    edges_l1 = []
    for i in range(4):
        for j in range(i + 1, 4):
            edges_l1.append([i, "L1", j, "L1", 1])
    for i in range(4, 8):
        for j in range(i + 1, 8):
            edges_l1.append([i, "L1", j, "L1", 1])
    network.add_edges(edges_l1, input_type="list")

    edges_l2 = []
    for i in range(0, 7, 2):
        edges_l2.append([i, "L2", i + 1, "L2", 1])
    network.add_edges(edges_l2, input_type="list")

    print("Testing different resolution settings...")
    result_high = leiden_multilayer(
        network,
        interlayer_coupling=0.5,
        resolution={"L1": 1.5, "L2": 0.5},
        seed=DEFAULT_SEED,
    )

    print("\nWith gamma_L1=1.5, gamma_L2=0.5:")
    print(f"  Modularity: {result_high.modularity:.4f}")
    print(f"  Communities: {len(set(result_high.communities.values()))}")

    result_equal = leiden_multilayer(
        network,
        interlayer_coupling=0.5,
        resolution=1.0,
        seed=DEFAULT_SEED,
    )

    print("\nWith gamma=1.0 (all layers):")
    print(f"  Modularity: {result_equal.modularity:.4f}")
    print(f"  Communities: {len(set(result_equal.communities.values()))}")


def example_coupling_strengths() -> None:
    """Example 4: Effect of interlayer coupling strengths."""
    _print_header("Example 4: Effect of interlayer coupling")
    network = multinet.multi_layer_network(directed=False)

    edges_both = []
    for layer in ["L1", "L2"]:
        for i in range(3):
            for j in range(i + 1, 3):
                edges_both.append([i, layer, j, layer, 1])

        for i in range(3, 6):
            for j in range(i + 1, 6):
                edges_both.append([i, layer, j, layer, 1])

    network.add_edges(edges_both, input_type="list")
    print("Testing different coupling strengths...")

    result_none = leiden_multilayer(
        network,
        interlayer_coupling=0.0,
        resolution=1.0,
        seed=DEFAULT_SEED,
    )

    print("\nWith omega=0.0 (no coupling):")
    print(f"  Modularity: {result_none.modularity:.4f}")
    print(f"  Communities: {len(set(result_none.communities.values()))}")

    result_strong = leiden_multilayer(
        network,
        interlayer_coupling=2.0,
        resolution=1.0,
        seed=DEFAULT_SEED,
    )

    print("\nWith omega=2.0 (strong coupling):")
    print(f"  Modularity: {result_strong.modularity:.4f}")
    print(f"  Communities: {len(set(result_strong.communities.values()))}")

    aligned_count = 0
    total_count = 0
    for node in range(6):
        l1 = result_strong.communities.get((node, "L1"))
        l2 = result_strong.communities.get((node, "L2"))
        if l1 is not None and l2 is not None:
            if l1 == l2:
                aligned_count += 1
            total_count += 1

    print(f"  Cross-layer alignment: {aligned_count}/{total_count} nodes in same community")


def main() -> int:
    """Run all Leiden multilayer examples."""
    if IMPORT_ERROR:
        print(f"Error importing dependencies: {IMPORT_ERROR}")
        print("Install py3plex with leidenalg support to run this example.")
        return 1

    np.random.seed(DEFAULT_SEED)
    print("=" * 70)
    print("Leiden Multilayer Community Detection Example")
    print("=" * 70)

    try:
        example_simple_network()
        example_random_er()
        example_resolution_per_layer()
        example_coupling_strengths()
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"\nError while running Leiden examples: {exc}")
        return 1

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
