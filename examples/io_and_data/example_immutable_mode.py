"""
Example demonstrating immutable network mode with copy-on-write.

This example shows how to create immutable views of networks to prevent
accidental modifications during analysis pipelines.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.core.immutable import make_immutable


def main():
    """Demonstrate immutable network mode."""
    print("=== Immutable Mode Demo ===\n")
    
    # Create a mutable network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])
    
    print(f"Original network: {net.core_network.number_of_nodes()} nodes")
    
    # Make immutable with copy-on-write semantics
    immutable = make_immutable(net, copy_on_write=True)
    
    print(f"Immutable view created: {immutable.number_of_nodes()} nodes")
    print("Network is now immutable - modifications create new copies\n")
    
    # Read operations work fine
    nodes = list(immutable.get_nodes())
    print(f"✓ Can read nodes: {len(nodes)} nodes")
    
    edges = immutable.number_of_edges()
    print(f"✓ Can read edges: {edges} edges")
    
    # The original network is protected from accidental modification
    print("\nBenefits:")
    print("  - Prevents accidental mutations during analysis")
    print("  - Safe for concurrent read operations")
    print("  - Copy-on-write for efficient memory usage\n")


if __name__ == "__main__":
    main()
