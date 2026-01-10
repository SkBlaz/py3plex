"""Tropical lexicographic semiring example with layer-switch counting.

This example demonstrates:
- Using tropical_lex semiring for multiobjective optimization
- Minimizing both path cost and number of layer switches
- Lexicographic ordering (cost first, then switches)
"""

from py3plex.core import multinet
from py3plex.dsl import S


def main():
    """Run tropical lexicographic example."""
    print("=" * 60)
    print("Tropical Lexicographic (cost + layer switches)")
    print("=" * 60)

    # Create a two-layer network
    network = multinet.multi_layer_network(directed=False)

    # Add nodes in two layers
    nodes = [
        {'source': 'A', 'type': 'road'},
        {'source': 'B', 'type': 'road'},
        {'source': 'C', 'type': 'road'},
        {'source': 'A', 'type': 'rail'},
        {'source': 'B', 'type': 'rail'},
        {'source': 'C', 'type': 'rail'},
    ]
    network.add_nodes(nodes)

    # Add intra-layer edges (within same transport mode)
    # Road: A-B-C
    # Rail: A-B-C (faster but requires mode switch)
    edges = [
        # Road network
        {'source': 'A', 'target': 'B', 'source_type': 'road', 'target_type': 'road', 'weight': 5.0},
        {'source': 'B', 'target': 'C', 'source_type': 'road', 'target_type': 'road', 'weight': 5.0},
        # Rail network (faster)
        {'source': 'A', 'target': 'B', 'source_type': 'rail', 'target_type': 'rail', 'weight': 2.0},
        {'source': 'B', 'target': 'C', 'source_type': 'rail', 'target_type': 'rail', 'weight': 2.0},
        # Inter-layer connections (mode switches at A, B, C)
        {'source': 'A', 'target': 'A', 'source_type': 'road', 'target_type': 'rail', 'weight': 0.5},
        {'source': 'B', 'target': 'B', 'source_type': 'road', 'target_type': 'rail', 'weight': 0.5},
        {'source': 'C', 'target': 'C', 'source_type': 'road', 'target_type': 'rail', 'weight': 0.5},
    ]
    network.add_edges(edges)

    print("\nNetwork structure:")
    print("  Road layer: A --(5)-- B --(5)-- C  (total: 10)")
    print("  Rail layer: A --(2)-- B --(2)-- C  (total: 4)")
    print("  Mode switches available at: A, B, C (cost: 0.5 each)")

    # Use tropical_lex with custom lift to count layer switches
    print("\nFinding optimal path from A@road to C@road...")
    print("Objectives: (1) minimize cost, (2) minimize layer switches")

    def lift_with_switch_count(edge):
        """Lift function that returns (cost, layer_switch_count)."""
        weight = edge.get('weight', 1.0)
        # Count as layer switch if source_type != target_type
        is_switch = 1 if edge.get('source_type') != edge.get('target_type') else 0
        return (weight, is_switch)

    # Note: This requires custom integration; for now show concept
    print("\n[Conceptual example - full integration pending]")
    print("Path options:")
    print("  1. Stay on road: A@road -> B@road -> C@road")
    print("     Cost: 10.0, Switches: 0")
    print("  2. Switch to rail: A@road -> A@rail -> B@rail -> C@rail -> C@road")
    print("     Cost: 5.0, Switches: 2")
    print("  3. Switch mid-route: A@road -> B@road -> B@rail -> C@rail -> C@road")
    print("     Cost: 8.0, Switches: 2")

    print("\nLexicographic ordering:")
    print("  (5.0, 2) < (8.0, 2) < (10.0, 0)")
    print("  Best path: Option 2 (lowest cost despite switches)")

    print("\n" + "=" * 60)
    print(" Example completed (conceptual demonstration)")
    print("=" * 60)


if __name__ == "__main__":
    main()
