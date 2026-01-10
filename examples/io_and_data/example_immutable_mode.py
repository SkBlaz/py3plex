"""
Protect a network with an immutable, copy-on-write view.

Shows how to wrap a `multi_layer_network` with `make_immutable` so read
operations work as usual while writes produce safe copies. Prerequisite:
py3plex installed; no optional extras.
"""

from __future__ import annotations

from py3plex.core.immutable import make_immutable
from py3plex.core.multinet import multi_layer_network


def build_network() -> multi_layer_network:
    """Create a tiny two-node multilayer network."""
    net = multi_layer_network(network_type="multilayer", directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "layer1"},
            {"source": "B", "type": "layer1"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "layer1",
                "target_type": "layer1",
            },
        ]
    )
    return net


def main() -> int:
    """Demonstrate immutable network mode."""
    print("=== Immutable Mode Demo ===\n")

    net = build_network()
    print(f"Original network: {net.core_network.number_of_nodes()} nodes")

    immutable = make_immutable(net, copy_on_write=True)

    print(f"Immutable view created: {immutable.number_of_nodes()} nodes")
    print("Network is now immutable - modifications create new copies\n")

    nodes = list(immutable.get_nodes())
    print(f" Can read nodes: {len(nodes)} nodes")

    edges = immutable.number_of_edges()
    print(f" Can read edges: {edges} edges")

    print("\nBenefits:")
    print("  - Prevents accidental mutations during analysis")
    print("  - Safe for concurrent read operations")
    print("  - Copy-on-write for efficient memory usage\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
