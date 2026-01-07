"""Boolean reachability example using boolean semiring.

This example demonstrates:
- Using boolean semiring for reachability queries
- S.paths() with boolean algebra
- Checking connectivity in multilayer networks
"""

from py3plex.core import multinet
from py3plex.dsl import S, L


def main():
    """Run boolean reachability example."""
    print("=" * 60)
    print("Boolean Reachability (boolean semiring)")
    print("=" * 60)
    
    # Create a network with disconnected components
    network = multinet.multi_layer_network(directed=True)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'social'},
        {'source': 'E', 'type': 'social'},
    ]
    network.add_nodes(nodes)
    
    # Add edges (A->B->C, D->E are separate components)
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'social', 'target_type': 'social'},
    ]
    network.add_edges(edges)
    
    print("\nNetwork structure:")
    print("  Component 1: A -> B -> C")
    print("  Component 2: D -> E")
    
    # Compute reachability from A using boolean semiring
    print("\nComputing reachability from A using boolean semiring...")
    
    result = (
        S.paths()
         .from_node('A')
         .semiring('boolean')
         .lift(attr=None, default=True)  # All edges contribute True
         .from_layers(L['social'])
         .execute(network)
    )
    
    # Display results
    print("\nReachability from A:")
    print("-" * 40)
    
    for item in result.items:
        node = item['node']
        reachable = item['value']
        status = "✓ reachable" if reachable else "✗ unreachable"
        print(f"  {node}: {status}")
    
    # Verify expected results
    expected = {
        'A': True,   # Source
        'B': True,   # A -> B
        'C': True,   # A -> B -> C
        'D': False,  # Disconnected
        'E': False,  # Disconnected
    }
    
    print("\nVerification:")
    actual = {item['node']: item['value'] for item in result.items}
    for node, expected_val in expected.items():
        actual_val = actual.get(node, False)
        match = "✓" if actual_val == expected_val else "✗"
        print(f"  {node}: expected={expected_val}, actual={actual_val} {match}")
    
    print("\n" + "=" * 60)
    print("✓ Example completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
