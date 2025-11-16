"""
Example: Ego-Centric Multilayer Visualization

This example demonstrates the ego-centric visualization mode, which focuses on
a single node (the "ego") and shows its neighborhood across different layers.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving

from py3plex.core import multinet
from py3plex.visualization.multilayer import visualize_multilayer_network
import os


def create_sample_multilayer_network():
    """Create a small synthetic multilayer network for demonstration."""
    # Create multilayer network with node '3' as the ego
    network = multinet.multi_layer_network(directed=False)
    
    # Layer A: star with node 3 at center
    for i in range(1, 7):
        network.add_nodes([{'source': str(i), 'type': 'A'}], input_type='dict')
    
    network.add_edges([
        {'source': '3', 'target': '1', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '4', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '5', 'source_type': 'A', 'target_type': 'A'},
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Layer B: path with node 3 in the middle
    for i in range(1, 6):
        network.add_nodes([{'source': str(i), 'type': 'B'}], input_type='dict')
    
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
        {'source': '2', 'target': '3', 'source_type': 'B', 'target_type': 'B'},
        {'source': '3', 'target': '4', 'source_type': 'B', 'target_type': 'B'},
        {'source': '4', 'target': '5', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    # Layer C: triangle with node 3
    for i in [3, 6, 7]:
        network.add_nodes([{'source': str(i), 'type': 'C'}], input_type='dict')
    
    network.add_edges([
        {'source': '3', 'target': '6', 'source_type': 'C', 'target_type': 'C'},
        {'source': '6', 'target': '7', 'source_type': 'C', 'target_type': 'C'},
        {'source': '7', 'target': '3', 'source_type': 'C', 'target_type': 'C'},
    ], input_type='dict')
    
    return network


def main():
    print("=" * 70)
    print("EGO-CENTRIC MULTILAYER VISUALIZATION EXAMPLE")
    print("=" * 70)
    
    # Create sample network
    print("\nCreating sample multilayer network...")
    network = create_sample_multilayer_network()
    network.basic_stats()
    
    # Example 1: Ego-centric view for node '3' (1-hop neighborhood)
    print("\n" + "-" * 70)
    print("Example 1: Ego-centric view for node '3' (1-hop)")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='3',
        max_depth=1,
        layout="spring",
        node_size=100,
        ego_node_size=400,
        with_labels=True
    )
    
    output_dir = "/home/runner/work/py3plex/py3plex/example_images"

    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_ego_node3_1hop.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    print("  Red node = ego (node '3')")
    print("  Blue nodes = 1-hop neighbors")
    
    # Example 2: Ego-centric view with 2-hop neighborhood
    print("\n" + "-" * 70)
    print("Example 2: Ego-centric view for node '3' (2-hop)")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='3',
        max_depth=2,
        layout="spring",
        node_size=100,
        ego_node_size=400,
        with_labels=True
    )
    
    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_ego_node3_2hop.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    print("  Shows extended 2-hop neighborhood")
    
    # Example 3: Ego-centric with circular layout
    print("\n" + "-" * 70)
    print("Example 3: Ego-centric with circular layout")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='3',
        max_depth=1,
        layout="circular",
        node_size=100,
        ego_node_size=400,
        with_labels=True,
        max_cols=2
    )
    
    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_ego_circular.png")
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # Example 4: Ego-centric for specific layers only
    print("\n" + "-" * 70)
    print("Example 4: Ego-centric for specific layers (A and B only)")
    print("-" * 70)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='3',
        layers=['A', 'B'],
        max_depth=1,
        layout="spring",
        node_size=100,
        ego_node_size=400,
        with_labels=True
    )
    
    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_ego_subset.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    print("  Shows only layers A and B")
    
    print("\n" + "=" * 70)
    print("EGO-CENTRIC EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  • Focus on single node (ego) neighborhood")
    print("  • Side-by-side comparison across layers")
    print("  • Highlighted ego node (red, larger)")
    print("  • Adjustable neighborhood depth (1-hop, 2-hop)")
    print("  • Layer-specific filtering")
    print("\nInterpretation:")
    print("  • Red node = the ego (focal node)")
    print("  • Blue nodes = neighbors of the ego")
    print("  • Each subplot = ego's neighborhood in one layer")
    print("\nUse cases:")
    print("  • Analyze how a specific node connects in different contexts")
    print("  • Compare local structure across layers")
    print("  • Identify layer-specific influential neighbors")


if __name__ == "__main__":
    main()
