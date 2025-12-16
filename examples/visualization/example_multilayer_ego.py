"""
Example: Ego-Centric Multilayer Visualization

Demonstrates the ego-centric visualization mode, focusing on a single node
across multiple layers. Saves static images using a non-interactive backend.
"""

from __future__ import annotations

import os
from typing import Iterable

import matplotlib

matplotlib.use('Agg')  # Use non-interactive backend for saving
import numpy as np
from py3plex.core import multinet
from py3plex.utils import get_example_image_path
from py3plex.visualization.multilayer import visualize_multilayer_network


def create_sample_multilayer_network() -> multinet.multi_layer_network:
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


def save_figure(fig, filename: str) -> str:
    """Save a matplotlib figure to the example images directory."""
    output_path = get_example_image_path(filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    return output_path


def render_example(network: multinet.multi_layer_network, ego: str, max_depth: int, layout: str, filename: str, layers: Iterable[str] | None = None, dpi: int = 150) -> None:
    """Render and persist a single ego visualization."""
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego=ego,
        layers=list(layers) if layers is not None else None,
        max_depth=max_depth,
        layout=layout,
        node_size=100,
        ego_node_size=400,
        with_labels=True,
    )
    path = save_figure(fig, filename)
    print(f"✓ Saved: {path}")


def main() -> int:
    np.random.seed(42)
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
    
    render_example(network, ego='3', max_depth=1, layout="spring", filename="multilayer_ego_node3_1hop.png")
    print("  Red node = ego (node '3')")
    print("  Blue nodes = 1-hop neighbors")
    
    # Example 2: Ego-centric view with 2-hop neighborhood
    print("\n" + "-" * 70)
    print("Example 2: Ego-centric view for node '3' (2-hop)")
    print("-" * 70)
    
    render_example(network, ego='3', max_depth=2, layout="spring", filename="multilayer_ego_node3_2hop.png")
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
    path = save_figure(fig, "multilayer_ego_circular.png")
    print(f"✓ Saved: {path}")
    
    # Example 4: Ego-centric for specific layers only
    print("\n" + "-" * 70)
    print("Example 4: Ego-centric for specific layers (A and B only)")
    print("-" * 70)
    
    render_example(
        network,
        ego='3',
        layers=['A', 'B'],
        max_depth=1,
        layout="spring",
        filename="multilayer_ego_subset.png",
    )
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
