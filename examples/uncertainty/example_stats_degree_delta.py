"""Example: Computing degree with Delta (deterministic) uncertainty.

This example demonstrates the simplest case of the uncertainty-first
statistics system: computing a deterministic statistic (node degree)
where the uncertainty is Delta(0).

The key point is that even deterministic stats are StatValue objects,
maintaining consistency across the system.
"""

import sys
sys.path.insert(0, '/home/runner/work/py3plex/py3plex')

from py3plex.core import multinet
from py3plex.stats import StatValue, Delta, Provenance


def compute_degree_stat(network, node_id):
    """Compute degree as a StatValue with Delta(0) uncertainty.
    
    Args:
        network: Multilayer network
        node_id: Node to compute degree for
        
    Returns:
        StatValue with degree and deterministic uncertainty
    """
    # Compute the degree
    degree = network.core_network.degree(node_id)
    
    # Wrap in StatValue with Delta(0) uncertainty
    return StatValue(
        value=degree,
        uncertainty=Delta(0.0),  # Deterministic - no uncertainty
        provenance=Provenance(
            algorithm="degree",
            uncertainty_method="delta",
            parameters={"node": node_id}
        )
    )


def main():
    """Demonstrate degree computation with Delta uncertainty."""
    print("=" * 60)
    print("Uncertainty-First Statistics: Degree with Delta")
    print("=" * 60)
    print()
    
    # Create a simple multilayer network
    print("1. Creating multilayer network...")
    net = multinet.multi_layer_network(directed=False)
    
    # Add edges
    edges = [
        ["A", "L1", "B", "L1", 1.0],
        ["B", "L1", "C", "L1", 1.0],
        ["A", "L1", "C", "L1", 1.0],
        ["A", "L2", "B", "L2", 1.0],
        ["B", "L2", "D", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    print(f"   Added {len(edges)} edges across 2 layers")
    print()
    
    # Compute degree for each node
    print("2. Computing degrees with Delta(0) uncertainty...")
    nodes = ["A", "B", "C", "D"]
    degree_stats = {}
    
    for node in nodes:
        if (node, "L1") in net.core_network or (node, "L2") in net.core_network:
            # Compute overall degree (both layers)
            degree_l1 = net.core_network.degree((node, "L1")) if (node, "L1") in net.core_network else 0
            degree_l2 = net.core_network.degree((node, "L2")) if (node, "L2") in net.core_network else 0
            total_degree = degree_l1 + degree_l2
            
            degree_stats[node] = StatValue(
                value=total_degree,
                uncertainty=Delta(0.0),
                provenance=Provenance("degree", "delta", {"layers": ["L1", "L2"]})
            )
    
    print(f"   Computed degrees for {len(degree_stats)} nodes")
    print()
    
    # Display results
    print("3. Results:")
    print("-" * 60)
    print(f"{'Node':<10} {'Degree':<10} {'Std':<10} {'Robustness':<15}")
    print("-" * 60)
    
    for node, stat in sorted(degree_stats.items()):
        print(f"{node:<10} {float(stat):<10.1f} {stat.std():<10.3f} {stat.robustness():<15.3f}")
    
    print("-" * 60)
    print()
    
    # Demonstrate arithmetic with uncertainty propagation
    print("4. Demonstrating arithmetic with uncertainty propagation...")
    
    if "A" in degree_stats and "B" in degree_stats:
        stat_a = degree_stats["A"]
        stat_b = degree_stats["B"]
        
        # Addition
        stat_sum = stat_a + stat_b
        print(f"   A + B = {float(stat_sum):.1f} (std: {stat_sum.std():.3f})")
        
        # Multiplication
        stat_product = stat_a * stat_b
        print(f"   A * B = {float(stat_product):.1f} (std: {stat_product.std():.3f})")
        
        # Division
        if float(stat_b) > 0:
            stat_ratio = stat_a / stat_b
            print(f"   A / B = {float(stat_ratio):.3f} (std: {stat_ratio.std():.3f})")
    
    print()
    
    # Demonstrate backward compatibility
    print("5. Backward compatibility with float()...")
    if "A" in degree_stats:
        stat = degree_stats["A"]
        # Old code expecting float still works
        degree_value = float(stat)
        print(f"   float(stat_A) = {degree_value} (type: {type(degree_value).__name__})")
    print()
    
    # Demonstrate serialization
    print("6. JSON serialization...")
    if "A" in degree_stats:
        stat = degree_stats["A"]
        json_dict = stat.to_json_dict()
        print(f"   StatValue for A:")
        print(f"     value: {json_dict['value']}")
        print(f"     uncertainty: {json_dict['uncertainty']}")
        print(f"     provenance: {json_dict['provenance']}")
    print()
    
    print("=" * 60)
    print("Key Takeaways:")
    print("- Even deterministic stats are StatValue objects")
    print("- Delta(0) represents zero uncertainty (perfect certainty)")
    print("- Robustness = 1.0 for deterministic values")
    print("- Arithmetic operations preserve deterministic uncertainty")
    print("- Backward compatible via float() conversion")
    print("=" * 60)


if __name__ == "__main__":
    main()
