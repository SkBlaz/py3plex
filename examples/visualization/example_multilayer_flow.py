#!/usr/bin/env python
"""
Example demonstrating the new flow/alluvial visualization for multilayer networks.

This example shows how to use the draw_multilayer_flow function and the 
visualize_network method with style='flow' or style='alluvial'.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for CI
import matplotlib.pyplot as plt

from py3plex.core import multinet

def create_example_network():
    """Create a sample multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Social network
    for node in ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']:
        network.add_nodes([{'source': node, 'type': 'social'}], input_type='dict')
    
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Diana', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    ], input_type='dict')
    
    # Layer 2: Work network
    for node in ['Alice', 'Bob', 'Charlie', 'Diana', 'Frank']:
        network.add_nodes([{'source': node, 'type': 'work'}], input_type='dict')
    
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'Diana', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'Diana', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Diana', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
    ], input_type='dict')
    
    # Layer 3: Hobby network
    for node in ['Bob', 'Charlie', 'Diana', 'Eve', 'Frank']:
        network.add_nodes([{'source': node, 'type': 'hobby'}], input_type='dict')
    
    network.add_edges([
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Charlie', 'target': 'Diana', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Diana', 'target': 'Frank', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'hobby', 'target_type': 'hobby'},
    ], input_type='dict')
    
    # Add inter-layer connections (same person across layers)
    inter_layer_edges = [
        # Social to Work
        {'source': 'Alice', 'target': 'Alice', 'source_type': 'social', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Bob', 'source_type': 'social', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'work'},
        {'source': 'Diana', 'target': 'Diana', 'source_type': 'social', 'target_type': 'work'},
        
        # Work to Hobby
        {'source': 'Bob', 'target': 'Bob', 'source_type': 'work', 'target_type': 'hobby'},
        {'source': 'Charlie', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'hobby'},
        {'source': 'Diana', 'target': 'Diana', 'source_type': 'work', 'target_type': 'hobby'},
        {'source': 'Frank', 'target': 'Frank', 'source_type': 'work', 'target_type': 'hobby'},
    ]
    
    for edge in inter_layer_edges:
        network.add_edges([edge], input_type='dict')
    
    return network


def example_basic_flow():
    """Example 1: Basic flow visualization using visualize_network."""
    print("\n" + "="*70)
    print("Example 1: Basic Flow Visualization")
    print("="*70)
    
    network = create_example_network()
    
    print("\nNetwork statistics:")
    network.basic_stats()
    
    print("\nCreating flow visualization using visualize_network(style='flow')...")
    ax = network.visualize_network(style='flow', show=False)
    
    plt.savefig('/tmp/example_flow_basic.png', dpi=150, bbox_inches='tight')
    print("✓ Saved to: /tmp/example_flow_basic.png")
    plt.close()


def example_custom_flow():
    """Example 2: Custom flow visualization with parameters."""
    print("\n" + "="*70)
    print("Example 2: Custom Flow Visualization with Parameters")
    print("="*70)
    
    network = create_example_network()
    
    # Get layers data for custom visualization
    from py3plex.visualization.multilayer import draw_multilayer_flow
    
    labels, graphs, multilinks = network.get_layers("diagonal")
    
    print(f"\nLayers: {labels}")
    print(f"Number of multilink types: {len(multilinks)}")
    
    print("\nCreating custom flow visualization...")
    fig, ax = plt.subplots(figsize=(14, 8))
    
    draw_multilayer_flow(
        graphs,
        multilinks,
        labels=labels,
        ax=ax,
        display=False,
        layer_gap=3.5,
        node_size=80,
        node_cmap="RdYlBu",
        flow_alpha=0.4,
        flow_min_width=0.5,
        flow_max_width=6.0
    )
    
    plt.title("Multilayer Network Flow Visualization\n(Social, Work, and Hobby Networks)", 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.savefig('/tmp/example_flow_custom.png', dpi=150, bbox_inches='tight')
    print("✓ Saved to: /tmp/example_flow_custom.png")
    plt.close()


def example_comparison():
    """Example 3: Compare flow visualization with diagonal visualization."""
    print("\n" + "="*70)
    print("Example 3: Comparing Flow vs Diagonal Visualization")
    print("="*70)
    
    network = create_example_network()
    
    # Create comparison figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    print("\nCreating diagonal visualization (left)...")
    network.visualize_network(style='diagonal', show=False, axis=axes[0])
    axes[0].set_title("Diagonal Layout", fontsize=12, fontweight='bold')
    
    print("Creating flow visualization (right)...")
    network.visualize_network(style='flow', show=False, axis=axes[1])
    axes[1].set_title("Flow/Alluvial Layout", fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/tmp/example_flow_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved to: /tmp/example_flow_comparison.png")
    plt.close()


if __name__ == '__main__':
    print("="*70)
    print("MULTILAYER FLOW VISUALIZATION EXAMPLES")
    print("="*70)
    print("\nThis example demonstrates the new flow/alluvial visualization style")
    print("for multilayer networks. The visualization shows:")
    print("  • Each layer as a horizontal band")
    print("  • Nodes positioned along the x-axis within each layer")
    print("  • Node colors indicating activity (degree centrality)")
    print("  • Inter-layer connections as flowing ribbons")
    
    try:
        example_basic_flow()
        example_custom_flow()
        example_comparison()
        
        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70)
        print("\nGenerated visualizations:")
        print("  1. /tmp/example_flow_basic.png")
        print("  2. /tmp/example_flow_custom.png")
        print("  3. /tmp/example_flow_comparison.png")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
