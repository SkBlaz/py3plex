"""
Example: Small Multiples Multilayer Visualization

This example demonstrates the small multiples visualization mode, which displays
each layer as a separate subplot in a grid layout. This makes it easy to compare
the structure of different layers side-by-side.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving

import networkx as nx
from py3plex.core import multinet
from py3plex.visualization.multilayer import visualize_multilayer_network
from py3plex.utils import get_example_image_path


def create_sample_multilayer_network():
    """Create a small synthetic multilayer network for demonstration."""
    # Create multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to layer 'A'
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
        {'source': '3', 'type': 'A'},
        {'source': '4', 'type': 'A'},
    ], input_type='dict')
    
    # Add edges to layer 'A'
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '2', 'target': '3', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '4', 'source_type': 'A', 'target_type': 'A'},
        {'source': '4', 'target': '1', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Add nodes to layer 'B'
    network.add_nodes([
        {'source': '1', 'type': 'B'},
        {'source': '2', 'type': 'B'},
        {'source': '3', 'type': 'B'},
        {'source': '5', 'type': 'B'},
    ], input_type='dict')
    
    # Add edges to layer 'B' (different structure)
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
        {'source': '2', 'target': '5', 'source_type': 'B', 'target_type': 'B'},
        {'source': '5', 'target': '3', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    # Add nodes to layer 'C'
    network.add_nodes([
        {'source': '1', 'type': 'C'},
        {'source': '2', 'type': 'C'},
        {'source': '3', 'type': 'C'},
        {'source': '4', 'type': 'C'},
        {'source': '5', 'type': 'C'},
    ], input_type='dict')
    
    # Add edges to layer 'C' (star topology)
    network.add_edges([
        {'source': '1', 'target': '3', 'source_type': 'C', 'target_type': 'C'},
        {'source': '2', 'target': '3', 'source_type': 'C', 'target_type': 'C'},
        {'source': '3', 'target': '4', 'source_type': 'C', 'target_type': 'C'},
        {'source': '3', 'target': '5', 'source_type': 'C', 'target_type': 'C'},
    ], input_type='dict')
    
    return network


def main():
    print("=" * 70)
    print("SMALL MULTIPLES VISUALIZATION EXAMPLE")
    print("=" * 70)
    
    # Create sample network
    print("\nCreating sample multilayer network...")
    network = create_sample_multilayer_network()
    network.basic_stats()
    
    # Ensure output directory exists
    import os
    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Example 1: Small multiples with shared layout
    print("\n" + "-" * 70)
    print("Example 1: Small multiples with shared layout")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=True,
        layout="spring",
        node_size=300,
        show_layer_titles=True,
        with_labels=True
    )
    
    output_path = os.path.join(output_dir, "multilayer_small_multiples_shared.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # Example 2: Small multiples with independent layouts
    print("\n" + "-" * 70)
    print("Example 2: Small multiples with independent layouts per layer")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=False,
        layout="spring",
        node_size=300,
        show_layer_titles=True,
        with_labels=True
    )
    
    output_path = os.path.join(output_dir, "multilayer_small_multiples_independent.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # Example 3: Circular layout
    print("\n" + "-" * 70)
    print("Example 3: Small multiples with circular layout")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=True,
        layout="circular",
        node_size=300,
        max_cols=2,
        show_layer_titles=True,
        with_labels=True
    )
    
    output_path = os.path.join(output_dir, "multilayer_small_multiples_circular.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    print("\n" + "=" * 70)
    print("SMALL MULTIPLES EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  • Side-by-side comparison of layer structures")
    print("  • Shared layout for consistent node positioning")
    print("  • Independent layouts for layer-specific optimization")
    print("  • Multiple layout algorithms (spring, circular)")


if __name__ == "__main__":
    main()
