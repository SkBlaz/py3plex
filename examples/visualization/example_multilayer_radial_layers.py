"""
Example: Radial Layers Multilayer Visualization

This example demonstrates the radial/concentric visualization mode, which arranges
layers as concentric circles with nodes positioned on rings and inter-layer edges
shown as radial connections.
"""

import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for saving

from py3plex.core import multinet
from py3plex.visualization.multilayer import visualize_multilayer_network
import os


def create_sample_multilayer_network():
    """Create a small synthetic multilayer network for demonstration."""
    # Create multilayer network
    network = multinet.multi_layer_network(directed=False)

    # Layer A: triangle
    for i in [1, 2, 3]:
        network.add_nodes([{'source': str(i), 'type': 'A'}], input_type='dict')

    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '2', 'target': '3', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '1', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')

    # Layer B: square
    for i in [1, 2, 3, 4]:
        network.add_nodes([{'source': str(i), 'type': 'B'}], input_type='dict')

    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
        {'source': '2', 'target': '3', 'source_type': 'B', 'target_type': 'B'},
        {'source': '3', 'target': '4', 'source_type': 'B', 'target_type': 'B'},
        {'source': '4', 'target': '1', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')

    # Layer C: pentagon
    for i in [1, 2, 3, 4, 5]:
        network.add_nodes([{'source': str(i), 'type': 'C'}], input_type='dict')

    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'C', 'target_type': 'C'},
        {'source': '2', 'target': '3', 'source_type': 'C', 'target_type': 'C'},
        {'source': '3', 'target': '4', 'source_type': 'C', 'target_type': 'C'},
        {'source': '4', 'target': '5', 'source_type': 'C', 'target_type': 'C'},
        {'source': '5', 'target': '1', 'source_type': 'C', 'target_type': 'C'},
    ], input_type='dict')

    # Add inter-layer edges
    network.add_edges([
        {'source': '1', 'target': '1', 'source_type': 'A', 'target_type': 'B'},
        {'source': '2', 'target': '2', 'source_type': 'B', 'target_type': 'C'},
        {'source': '3', 'target': '3', 'source_type': 'A', 'target_type': 'C'},
    ], input_type='dict')

    return network


def main():
    print("=" * 70)
    print("RADIAL LAYERS VISUALIZATION EXAMPLE")
    print("=" * 70)

    # Create sample network
    print("\nCreating sample multilayer network...")
    network = create_sample_multilayer_network()
    network.basic_stats()

    # Example 1: Basic radial visualization
    print("\n" + "-" * 70)
    print("Example 1: Radial layers with inter-layer edges")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,
        radius_step=1.5,
        node_size=200,
        draw_inter_layer_edges=True,
        edge_alpha=0.5
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"


    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_radial_with_inter.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")
    print("  Concentric rings show different layers")
    print("  Radial lines connect nodes across layers")

    # Example 2: Radial without inter-layer edges
    print("\n" + "-" * 70)
    print("Example 2: Radial layers (intra-layer only)")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,
        radius_step=1.5,
        node_size=200,
        draw_inter_layer_edges=False,
        edge_alpha=0.6
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_radial_intra_only.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")
    print("  Shows only intra-layer connections")

    # Example 3: Compact radial with smaller spacing
    print("\n" + "-" * 70)
    print("Example 3: Compact radial layout")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,
        radius_step=0.8,
        node_size=150,
        draw_inter_layer_edges=True,
        edge_alpha=0.4
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_radial_compact.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")
    print("  Tighter spacing between layers")

    print("\n" + "=" * 70)
    print("RADIAL LAYERS EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  • Concentric circle layout for layers")
    print("  • Aligned node positions across layers")
    print("  • Color-coded layers for distinction")
    print("  • Inter-layer edges as radial connections")
    print("  • Adjustable ring spacing")
    print("\nInterpretation:")
    print("  • Each ring = one layer")
    print("  • Same node appears at same angle on all rings")
    print("  • Dashed lines = inter-layer connections")


if __name__ == "__main__":
    main()
