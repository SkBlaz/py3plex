"""
Example: Supra-Adjacency Heatmap Multilayer Visualization

This example demonstrates the supra-adjacency matrix heatmap visualization,
which shows the multilayer network as a block matrix where each block represents
the adjacency matrix of one layer.
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

    # Layer 1: Complete graph on nodes 1-4
    for i in range(1, 5):
        network.add_nodes([{'source': str(i), 'type': '1'}], input_type='dict')

    for i in range(1, 5):
        for j in range(i + 1, 5):
            network.add_edges([{
                'source': str(i),
                'target': str(j),
                'source_type': '1',
                'target_type': '1'
            }], input_type='dict')

    # Layer 2: Path on nodes 1-4
    for i in range(1, 5):
        network.add_nodes([{'source': str(i), 'type': '2'}], input_type='dict')

    for i in range(1, 4):
        network.add_edges([{
            'source': str(i),
            'target': str(i + 1),
            'source_type': '2',
            'target_type': '2'
        }], input_type='dict')

    # Layer 3: Star on nodes 1-5 (node 3 is center)
    for i in range(1, 6):
        network.add_nodes([{'source': str(i), 'type': '3'}], input_type='dict')

    for i in [1, 2, 4, 5]:
        network.add_edges([{
            'source': '3',
            'target': str(i),
            'source_type': '3',
            'target_type': '3'
        }], input_type='dict')

    return network


def main():
    print("=" * 70)
    print("SUPRA-ADJACENCY HEATMAP VISUALIZATION EXAMPLE")
    print("=" * 70)

    # Create sample network
    print("\nCreating sample multilayer network...")
    network = create_sample_multilayer_network()
    network.basic_stats()

    # Example 1: Basic supra-adjacency heatmap (intra-layer only)
    print("\n" + "-" * 70)
    print("Example 1: Supra-adjacency heatmap (intra-layer only)")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=False,
        cmap="Blues"
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"


    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_supra_heatmap_intra.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")
    print("  Block-diagonal structure shows intra-layer connections only")

    # Example 2: Supra-adjacency with inter-layer connections
    print("\n" + "-" * 70)
    print("Example 2: Supra-adjacency heatmap (with inter-layer coupling)")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=True,
        inter_layer_weight=0.5,
        cmap="viridis"
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_supra_heatmap_inter.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")
    print("  Off-diagonal blocks show inter-layer coupling for shared nodes")

    # Example 3: Different colormap
    print("\n" + "-" * 70)
    print("Example 3: Supra-adjacency with RdYlBu colormap")
    print("-" * 70)

    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=True,
        inter_layer_weight=1.0,
        cmap="RdYlBu_r"
    )

    output_dir = "/home/runner/work/py3plex/py3plex/example_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multilayer_supra_heatmap_rdylbu.png")
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f" Saved: {output_path}")

    print("\n" + "=" * 70)
    print("SUPRA-ADJACENCY HEATMAP EXAMPLE COMPLETE")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  • Matrix representation of multilayer structure")
    print("  • Block-diagonal showing layer-specific connections")
    print("  • Optional inter-layer coupling visualization")
    print("  • Grid lines delineating layer boundaries")
    print("  • Multiple colormap options")
    print("\nInterpretation:")
    print("  • Each block along diagonal = adjacency matrix of one layer")
    print("  • Off-diagonal blocks = inter-layer connections (when enabled)")
    print("  • White grid lines separate layers")


if __name__ == "__main__":
    main()
