"""
Example: Edge-Colored Projection Multilayer Visualization

This example demonstrates the edge-colored projection visualization mode, which
projects all layers onto a single 2D graph and uses edge colors to indicate
which layer each edge belongs to.
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

    # Layer A: cycle
    network.add_nodes([
        {'source': str(i), 'type': 'A'} for i in range(1, 6)
    ], input_type='dict')

    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '2', 'target': '3', 'source_type': 'A', 'target_type': 'A'},
        {'source': '3', 'target': '4', 'source_type': 'A', 'target_type': 'A'},
        {'source': '4', 'target': '5', 'source_type': 'A', 'target_type': 'A'},
        {'source': '5', 'target': '1', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')

    # Layer B: star
    network.add_nodes([
        {'source': str(i), 'type': 'B'} for i in range(1, 6)
    ], input_type='dict')

    network.add_edges([
        {'source': '3', 'target': '1', 'source_type': 'B', 'target_type': 'B'},
        {'source': '3', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
        {'source': '3', 'target': '4', 'source_type': 'B', 'target_type': 'B'},
        {'source': '3', 'target': '5', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')

    # Layer C: path
    network.add_nodes([
        {'source': str(i), 'type': 'C'} for i in range(1, 6)
    ], input_type='dict')

    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'C', 'target_type': 'C'},
        {'source': '2', 'target': '3', 'source_type': 'C', 'target_type': 'C'},
        {'source': '3', 'target': '4', 'source_type': 'C', 'target_type': 'C'},
        {'source': '4', 'target': '5', 'source_type': 'C', 'target_type': 'C'},
    ], input_type='dict')

    return network


def main():
    print("=" * 70)
    print("EDGE-COLORED PROJECTION VISUALIZATION EXAMPLE")
    print("=" * 70)

    # Create sample network
    print("\nCreating sample multilayer network...")
    network = create_sample_multilayer_network()
    network.basic_stats()

    # Example 1: Basic edge-colored projection
    print("\n" + "-" * 70)
    print("Example 1: Edge-colored projection with spring layout")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="spring",
        node_size=500,
        edge_alpha=0.7,
        with_labels=True
    )

    # Use repo-local output directory
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(repo_root, "example_images")


    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_edge_projection_spring.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")

    # Example 2: Circular layout
    print("\n" + "-" * 70)
    print("Example 2: Edge-colored projection with circular layout")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="circular",
        node_size=500,
        edge_alpha=0.6,
        with_labels=True
    )

    # output_dir already defined above
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_edge_projection_circular.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")

    # Example 3: With custom layer colors
    print("\n" + "-" * 70)
    print("Example 3: Edge-colored projection with custom colors")
    print("-" * 70)

    custom_colors = {
        'A': 'red',
        'B': 'blue',
        'C': 'green'
    }

    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="spring",
        node_size=500,
        layer_colors=custom_colors,
        edge_alpha=0.7,
        with_labels=True
    )

    # output_dir already defined above
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_edge_projection_custom.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")

    print("\n" + "=" * 70)
    print("EDGE-COLORED PROJECTION EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  • Aggregated view of all layers in one plot")
    print("  • Color-coded edges showing layer membership")
    print("  • Legend distinguishing different layers")
    print("  • Support for different layout algorithms")
    print("  • Custom color schemes for layers")


if __name__ == "__main__":
    main()
