#!/usr/bin/env python
"""
Simple test script for the new draw_multilayer_flow visualization.
This creates a small test multilayer network and visualizes it.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from py3plex.core import multinet
from py3plex.visualization.multilayer import draw_multilayer_flow

def test_basic_flow_visualization():
    """Test basic flow visualization with a simple multilayer network."""
    print("Creating test multilayer network...")
    
    # Create a simple multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to layer 1
    network.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ], input_type='dict')
    
    # Add edges in layer 1
    network.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ], input_type='dict')
    
    # Add nodes to layer 2
    network.add_nodes([
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'D', 'type': 'layer2'},
    ], input_type='dict')
    
    # Add edges in layer 2
    network.add_edges([
        {'source': 'A', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'},
        {'source': 'B', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'},
    ], input_type='dict')
    
    # Add inter-layer edges
    network.add_edges([
        {'source': 'A', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer2'},
        {'source': 'B', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer2'},
    ], input_type='dict')
    
    print("Network created. Basic stats:")
    network.basic_stats()
    
    print("\nGetting layers...")
    labels, graphs, multilinks = network.get_layers("diagonal")
    
    print(f"Number of layers: {len(graphs)}")
    print(f"Layer labels: {labels}")
    print(f"Number of multilink types: {len(multilinks)}")
    
    print("\nTesting draw_multilayer_flow...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        result_ax = draw_multilayer_flow(
            graphs,
            multilinks,
            labels=labels,
            ax=ax,
            display=False,
            layer_gap=2.0,
            node_size=100,
            flow_alpha=0.5
        )
        
        plt.savefig('/tmp/test_flow_viz.png', dpi=100, bbox_inches='tight')
        print("✓ Flow visualization created successfully!")
        print("  Saved to: /tmp/test_flow_viz.png")
        plt.close()
        
    except Exception as e:
        print(f"✗ Error creating flow visualization: {e}")
        import traceback
        traceback.print_exc()
        plt.close()
        return False
    
    return True


def test_visualize_network_flow_style():
    """Test the flow style through visualize_network method."""
    print("\n" + "="*60)
    print("Testing visualize_network with style='flow'...")
    print("="*60)
    
    # Create a simple multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to layer 1
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
        {'source': '3', 'type': 'A'},
    ], input_type='dict')
    
    # Add edges in layer 1
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Add nodes to layer 2
    network.add_nodes([
        {'source': '1', 'type': 'B'},
        {'source': '2', 'type': 'B'},
    ], input_type='dict')
    
    # Add edges in layer 2
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    # Add inter-layer edges
    network.add_edges([
        {'source': '1', 'target': '1', 'source_type': 'A', 'target_type': 'B'},
        {'source': '2', 'target': '2', 'source_type': 'A', 'target_type': 'B'},
    ], input_type='dict')
    
    try:
        ax = network.visualize_network(style='flow', show=False)
        plt.savefig('/tmp/test_visualize_network_flow.png', dpi=100, bbox_inches='tight')
        print("✓ visualize_network with style='flow' works!")
        print("  Saved to: /tmp/test_visualize_network_flow.png")
        plt.close()
        return True
    except Exception as e:
        print(f"✗ Error with visualize_network flow style: {e}")
        import traceback
        traceback.print_exc()
        plt.close()
        return False


if __name__ == '__main__':
    print("="*60)
    print("Testing draw_multilayer_flow implementation")
    print("="*60)
    
    success1 = test_basic_flow_visualization()
    success2 = test_visualize_network_flow_style()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*60)
