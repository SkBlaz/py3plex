"""
Example: Multiplex Routing with Layer-Switching Costs

This example demonstrates the native multiplex routing capabilities in py3plex,
which preserves layer semantics and supports configurable layer-switching costs.

Key Features Demonstrated:
1. Single-objective shortest path with switch costs
2. Zero vs. high switch cost behavior
3. Asymmetric switch cost matrices
4. Multi-objective Pareto-optimal routing
5. Layer-constrained routing

The implementation is sparse-first and never flattens the network.
"""

from py3plex.core import multinet
from py3plex.algorithms.routing import multiplex_shortest_path


def example_basic_routing():
    """Example 1: Basic routing with different switch costs."""
    print("=" * 70)
    print("Example 1: Basic Multiplex Routing")
    print("=" * 70)

    # Create a simple multiplex network with two layers
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Add edges
    edges = [
        # Social layer: A -- B -- C (longer path)
        ['A', 'social', 'B', 'social', 1.0],
        ['B', 'social', 'C', 'social', 1.0],
        # Work layer: A -- C (shorter direct path)
        ['A', 'work', 'C', 'work', 0.5],
    ]
    net.add_edges(edges, input_type='list')

    print("\nNetwork structure:")
    print("  Social layer: A -- B -- C (cost: 1.0 + 1.0 = 2.0)")
    print("  Work layer:   A -- C     (cost: 0.5)")

    # Test with zero switch cost (equivalent to flattened network)
    print("\n1a) With zero switch cost:")
    result = multiplex_shortest_path(net, 'A', 'C', switch_cost=0.0)
    print(f"  Path: {' -> '.join([f'{n}@{l}' for n, l in result['path']])}")
    print(f"  Total distance: {result['total_distance']}")
    print(f"  Layer switches: {result['num_switches']}")

    # Test with high switch cost (bias against layer switching)
    print("\n1b) With high switch cost (100.0):")
    result = multiplex_shortest_path(net, 'A', 'C', switch_cost=100.0)
    print(f"  Path: {' -> '.join([f'{n}@{l}' for n, l in result['path']])}")
    print(f"  Total distance: {result['total_distance']}")
    print(f"  Layer switches: {result['num_switches']}")
    print()


def example_asymmetric_switch_costs():
    """Example 2: Asymmetric switch cost matrix."""
    print("=" * 70)
    print("Example 2: Asymmetric Layer-Switching Costs")
    print("=" * 70)

    # Create network requiring layer switches
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'social', 'B', 'social', 1.0],
        ['B', 'work', 'C', 'work', 1.0],
    ]
    net.add_edges(edges, input_type='list')

    print("\nNetwork structure:")
    print("  Node A only in 'social' layer")
    print("  Node C only in 'work' layer")
    print("  Node B exists in both layers")

    # Define asymmetric switch costs
    switch_matrix = {
        ('social', 'work'): 0.1,   # Cheap: social -> work
        ('work', 'social'): 10.0,  # Expensive: work -> social
    }

    print("\nSwitch cost matrix:")
    print("  social -> work: 0.1")
    print("  work -> social: 10.0")

    result = multiplex_shortest_path(
        net, 'A', 'C',
        switch_cost=1.0,  # Default (unused due to matrix)
        switch_cost_matrix=switch_matrix
    )

    print("\nOptimal route A -> C:")
    print(f"  Path: {' -> '.join([f'{n}@{l}' for n, l in result['path']])}")
    print(f"  Total cost: {result['total_distance']}")
    print(f"    Edge A->B: 1.0")
    print(f"    Switch social->work at B: 0.1")
    print(f"    Edge B->C: 1.0")
    print()


def example_pareto_optimal():
    """Example 3: Multi-objective Pareto-optimal routing."""
    print("=" * 70)
    print("Example 3: Multi-Objective Pareto-Optimal Routing")
    print("=" * 70)

    # Create network with trade-off between distance and switches
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Longer path with no switches (stay in L1)
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['C', 'L1', 'D', 'L1', 1.0],
        # Shorter path requiring switches
        ['A', 'L2', 'B', 'L2', 0.5],
        ['B', 'L3', 'D', 'L3', 0.5],
    ]
    net.add_edges(edges, input_type='list')

    print("\nNetwork structure:")
    print("  L1: A -- B -- C -- D (total: 3.0, no switches)")
    print("  L2: A -- B           (0.5)")
    print("  L3: B -- D           (0.5)")

    result = multiplex_shortest_path(
        net, 'A', 'D',
        switch_cost=0.5,
        objective='pareto'
    )

    print(f"\nFound {len(result['paths'])} Pareto-optimal solution(s):")
    for i, (path, obj) in enumerate(zip(result['paths'], result['objectives'])):
        print(f"\n  Solution {i+1}:")
        print(f"    Path: {' -> '.join([f'{n}@{l}' for n, l in path])}")
        print(f"    Distance: {obj[0]:.2f}")
        print(f"    Switches: {obj[1]}")

    print("\n  Trade-off: Solution 1 minimizes distance (with 1 switch)")
    print("             Solution 2 minimizes switches (longer distance)")
    print()


def example_layer_constraints():
    """Example 4: Layer-constrained routing."""
    print("=" * 70)
    print("Example 4: Layer-Constrained Routing")
    print("=" * 70)

    # Create network with multiple layers
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ['A', 'L1', 'B', 'L1', 1.0],
        ['B', 'L1', 'C', 'L1', 1.0],
        ['A', 'L2', 'C', 'L2', 0.5],  # Shorter path in L2
        ['A', 'L3', 'B', 'L3', 0.3],
        ['B', 'L3', 'C', 'L3', 0.3],  # Even shorter in L3
    ]
    net.add_edges(edges, input_type='list')

    print("\nNetwork structure:")
    print("  L1: A -- B -- C (cost: 2.0)")
    print("  L2: A -- C     (cost: 0.5)")
    print("  L3: A -- B -- C (cost: 0.6)")

    # Without constraints: should use L3
    print("\nWithout layer constraints:")
    result1 = multiplex_shortest_path(net, 'A', 'C', switch_cost=0.0)
    print(f"  Path: {' -> '.join([f'{n}@{l}' for n, l in result1['path']])}")
    print(f"  Distance: {result1['total_distance']}")

    # With constraint: force to use only L1
    print("\nWith allowed_layers=['L1']:")
    result2 = multiplex_shortest_path(
        net, 'A', 'C',
        switch_cost=0.0,
        allowed_layers=['L1']
    )
    print(f"  Path: {' -> '.join([f'{n}@{l}' for n, l in result2['path']])}")
    print(f"  Distance: {result2['total_distance']}")
    print()


def example_practical_scenario():
    """Example 5: Practical multi-modal transportation network."""
    print("=" * 70)
    print("Example 5: Multi-Modal Transportation Network")
    print("=" * 70)

    # Model a transportation network with different modes
    net = multinet.multi_layer_network(directed=False, verbose=False)

    edges = [
        # Walking layer (slow but always available)
        ['Home', 'walk', 'BusStop', 'walk', 10.0],
        ['BusStop', 'walk', 'MetroStation', 'walk', 5.0],
        ['MetroStation', 'walk', 'Work', 'walk', 8.0],

        # Bus layer (medium speed)
        ['BusStop', 'bus', 'MetroStation', 'bus', 3.0],

        # Metro layer (fast but limited connections)
        ['MetroStation', 'metro', 'Work', 'metro', 2.0],
    ]
    net.add_edges(edges, input_type='list')

    print("\nMulti-modal transportation network:")
    print("  Walk:  Home -- BusStop -- MetroStation -- Work")
    print("         (10.0)    (5.0)       (8.0)")
    print("  Bus:   BusStop -- MetroStation (3.0)")
    print("  Metro: MetroStation -- Work (2.0)")

    # Define realistic mode-switching costs
    switch_costs = {
        ('walk', 'bus'): 2.0,    # Wait for bus
        ('walk', 'metro'): 3.0,  # Buy ticket, enter station
        ('bus', 'walk'): 0.5,    # Just get off
        ('bus', 'metro'): 2.0,   # Transfer
        ('metro', 'walk'): 0.5,  # Exit station
    }

    result = multiplex_shortest_path(
        net, 'Home', 'Work',
        switch_cost=1.0,
        switch_cost_matrix=switch_costs
    )

    print("\nOptimal route Home -> Work:")
    route_str = []
    for i, (node, layer) in enumerate(result['path']):
        if i > 0 and result['path'][i][1] != result['path'][i-1][1]:
            route_str.append(f"[switch to {layer}]")
        route_str.append(f"{node}@{layer}")
    print(f"  Route: {' -> '.join(route_str)}")
    print(f"  Total time: {result['total_distance']:.1f} units")
    print(f"  Mode switches: {result['num_switches']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MULTIPLEX ROUTING EXAMPLES")
    print("Demonstrates native multiplex shortest-path routing")
    print("with explicit layer-switching costs")
    print("=" * 70 + "\n")

    example_basic_routing()
    example_asymmetric_switch_costs()
    example_pareto_optimal()
    example_layer_constraints()
    example_practical_scenario()

    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
