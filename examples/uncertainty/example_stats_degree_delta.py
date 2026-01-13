"""Degree with deterministic (Delta) uncertainty.

Demonstrates how deterministic statistics are still StatValue objects,
preserving uncertainty metadata and arithmetic support. Dependencies:
py3plex (editable install or sys.path tweak below).
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.core import multinet
from py3plex.stats import Delta, Provenance, StatValue

LAYERS = ("L1", "L2")


def create_example_network() -> multinet.multi_layer_network:
    """Create a simple two-layer network."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["A", "L1", "B", "L1", 1.0],
        ["B", "L1", "C", "L1", 1.0],
        ["A", "L1", "C", "L1", 1.0],
        ["A", "L2", "B", "L2", 1.0],
        ["B", "L2", "D", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


def compute_degree_stat(network: multinet.multi_layer_network, node_id: Tuple[str, str]) -> StatValue:
    """Compute degree as a StatValue with Delta(0) uncertainty."""
    degree = network.core_network.degree(node_id)
    return StatValue(
        value=degree,
        uncertainty=Delta(0.0),
        provenance=Provenance(
            algorithm="degree",
            uncertainty_method="delta",
            parameters={"node": node_id},
        ),
    )


def compute_total_degrees(network: multinet.multi_layer_network, nodes) -> Dict[str, StatValue]:
    """Aggregate degrees across layers while preserving deterministic uncertainty."""
    degree_stats: Dict[str, StatValue] = {}

    for node in nodes:
        layer_stats = [
            compute_degree_stat(network, (node, layer))
            for layer in LAYERS
            if (node, layer) in network.core_network
        ]

        if not layer_stats:
            continue

        total_stat = layer_stats[0]
        for extra_stat in layer_stats[1:]:
            total_stat = total_stat + extra_stat

        degree_stats[node] = StatValue(
            value=float(total_stat),
            uncertainty=Delta(0.0),
            provenance=Provenance("degree", "delta", {"layers": list(LAYERS)}),
        )

    return degree_stats


def display_degree_table(degree_stats: Dict[str, StatValue]) -> None:
    """Print a small table of deterministic degree stats."""
    print("3. Results:")
    print("-" * 60)
    print(f"{'Node':<10} {'Degree':<10} {'Std':<10} {'Robustness':<15}")
    print("-" * 60)

    for node, stat in sorted(degree_stats.items()):
        print(f"{node:<10} {float(stat):<10.1f} {stat.std():<10.3f} {stat.robustness():<15.3f}")

    print("-" * 60)
    print()


def demonstrate_arithmetic(degree_stats: Dict[str, StatValue]) -> None:
    """Show that arithmetic keeps Delta(0) uncertainty intact."""
    print("4. Demonstrating arithmetic with uncertainty propagation...")

    if "A" in degree_stats and "B" in degree_stats:
        stat_a = degree_stats["A"]
        stat_b = degree_stats["B"]

        stat_sum = stat_a + stat_b
        print(f"   A + B = {float(stat_sum):.1f} (std: {stat_sum.std():.3f})")

        stat_product = stat_a * stat_b
        print(f"   A * B = {float(stat_product):.1f} (std: {stat_product.std():.3f})")

        if float(stat_b) > 0:
            stat_ratio = stat_a / stat_b
            print(f"   A / B = {float(stat_ratio):.3f} (std: {stat_ratio.std():.3f})")

    print()


def demonstrate_backward_compatibility(degree_stats: Dict[str, StatValue]) -> None:
    """Confirm StatValue behaves like a float where needed."""
    print("5. Backward compatibility with float()...")
    if "A" in degree_stats:
        stat = degree_stats["A"]
        degree_value = float(stat)
        print(f"   float(stat_A) = {degree_value} (type: {type(degree_value).__name__})")
    print()


def demonstrate_serialization(degree_stats: Dict[str, StatValue]) -> None:
    """Show JSON serialization of deterministic StatValue."""
    print("6. JSON serialization...")
    if "A" in degree_stats:
        stat = degree_stats["A"]
        json_dict = stat.to_json_dict()
        print(f"   StatValue for A:")
        print(f"     value: {json_dict['value']}")
        print(f"     uncertainty: {json_dict['uncertainty']}")
        print(f"     provenance: {json_dict['provenance']}")
    print()


def main() -> int:
    """Demonstrate degree computation with Delta uncertainty."""
    print("=" * 60)
    print("Uncertainty-First Statistics: Degree with Delta")
    print("=" * 60)
    print()

    print("1. Creating multilayer network...")
    net = create_example_network()
    print(f"   Added {net.core_network.number_of_edges()} edges across {len(LAYERS)} layers")
    print()

    print("2. Computing degrees with Delta(0) uncertainty...")
    nodes = ["A", "B", "C", "D"]
    degree_stats = compute_total_degrees(net, nodes)
    print(f"   Computed degrees for {len(degree_stats)} nodes")
    print()

    display_degree_table(degree_stats)
    demonstrate_arithmetic(degree_stats)
    demonstrate_backward_compatibility(degree_stats)
    demonstrate_serialization(degree_stats)

    print("=" * 60)
    print("Key Takeaways:")
    print("- Even deterministic stats are StatValue objects")
    print("- Delta(0) represents zero uncertainty (perfect certainty)")
    print("- Robustness = 1.0 for deterministic values")
    print("- Arithmetic operations preserve deterministic uncertainty")
    print("- Backward compatible via float() conversion")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
