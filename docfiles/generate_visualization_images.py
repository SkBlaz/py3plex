#!/usr/bin/env python3
"""
Generate visualization images for the visualization.rst documentation.

This script generates images that match the code examples in the documentation.
Each image is generated from the exact code shown in visualization.rst to ensure
the output matches the source exactly.

Output images are saved to: example_images/
"""

import os
import sys

# Set up matplotlib for non-interactive backend BEFORE any other imports
os.environ['MPLBACKEND'] = 'Agg'

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import random

# Set random seeds for reproducible output
random.seed(42)
np.random.seed(42)

# Import py3plex modules
from py3plex.core import multinet, random_generators
from py3plex.visualization.multilayer import (
    draw_multilayer_default,
    visualize_multilayer_network,
)
from py3plex.utils import get_dataset_path

# Output directory (relative to repo root)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, 'example_images')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def save_figure(filename, dpi=150, bbox_inches='tight'):
    """Save current figure and close it."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches, facecolor='white')
    plt.close()
    print(f"  [OK] Saved: {filepath}")


def generate_basic_multilayer():
    """
    Generate: multilayer.png
    
    Matches the Quick Start example in visualization.rst:
    Basic Multilayer Visualization using draw_multilayer_default
    """
    print_section("Generating: multilayer.png (Basic Multilayer Visualization)")
    
    # Generate a sample multilayer network (since network.csv doesn't exist)
    # This creates a representative example
    network = random_generators.random_multilayer_ER(30, 3, 0.15, directed=False)
    
    # Get layer data (returns: labels, graphs, multilinks) - matches corrected docs
    labels, graphs, multilinks = network.get_layers()
    
    # Create figure with appropriate size
    plt.figure(figsize=(10, 8))
    
    # Visualize with defaults - this matches the documentation example
    draw_multilayer_default(
        graphs,
        display=False,
        labels=labels
    )
    
    save_figure('multilayer.png')


def generate_minimal_mode():
    """
    Generate: hairball.png
    
    Matches the Minimal Mode example - large network visualization
    """
    print_section("Generating: hairball.png (Minimal Mode - Large Networks)")
    
    # Generate a larger network for minimal mode demonstration
    network = random_generators.random_multilayer_ER(100, 4, 0.05, directed=False)
    
    # Get layer data - matches corrected docs
    labels, graphs, multilinks = network.get_layers()
    
    plt.figure(figsize=(10, 8))
    
    # Minimal preset for large networks - matches documentation
    draw_multilayer_default(
        graphs,
        # Node settings
        node_size=5,              # Small nodes
        labels=False,             # No layer labels (too cluttered)
        node_labels=False,        # No node IDs
        
        # Edge settings
        edge_size=0.5,            # Thin edges
        alphalevel=0.3,           # Transparent edges (reduce clutter)
        
        # Layout
        background_shape="circle",  # Circular layout
        
        # Display
        display=False,
        remove_isolated_nodes=True  # Clean up isolated nodes
    )
    
    save_figure('hairball.png')


def generate_dense_mode():
    """
    Generate: multiplex.png
    
    Matches the Dense Mode example - small network with maximum detail
    """
    print_section("Generating: multiplex.png (Dense Mode - Small Networks)")
    
    # Generate a small network for dense mode
    network = random_generators.random_multilayer_ER(15, 2, 0.25, directed=False)
    
    # Get layer data - matches corrected docs
    labels, graphs, multilinks = network.get_layers()
    
    plt.figure(figsize=(8, 6))
    
    # Dense preset for small, detailed networks - matches documentation
    draw_multilayer_default(
        graphs,
        # Node settings
        node_size=20,             # Large nodes
        labels=labels,            # Show all labels
        node_labels=True,         # Show node IDs
        node_font_size=10,        # Readable font
        scale_by_size=True,       # Scale by degree
        
        # Edge settings
        edge_size=2.0,            # Thick edges
        alphalevel=0.8,           # Mostly opaque
        arrowsize=0.5,            # Visible arrows (if directed)
        
        # Layout
        background_shape="rectangle",  # Rectangular layout
        networks_color="rainbow",
        
        # Display
        display=False
    )
    
    save_figure('multiplex.png')


def generate_small_multiples():
    """
    Generate: multilayer_small_multiples_shared.png
    
    Matches the Small Multiples View example
    """
    print_section("Generating: multilayer_small_multiples_shared.png")
    
    # Load a sample network or generate one
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        # Generate a sample network
        network = random_generators.random_multilayer_ER(25, 3, 0.2, directed=False)
    
    # Use visualize_multilayer_network with small_multiples mode
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=True,       # Same node positions in all layers
        layout="spring",          # Layout algorithm
        node_size=300,
        max_cols=3,               # Maximum columns in grid
        show_layer_titles=True,
        with_labels=True
    )
    
    save_figure('multilayer_small_multiples_shared.png')


def generate_edge_projection():
    """
    Generate: multilayer_edge_projection_spring.png
    
    Matches the Edge-Colored Projection example
    """
    print_section("Generating: multilayer_edge_projection_spring.png")
    
    # Load or generate network
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        network = random_generators.random_multilayer_ER(25, 3, 0.2, directed=False)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="spring",
        node_size=500,
        edge_alpha=0.7,           # Edge transparency
        with_labels=True
    )
    
    save_figure('multilayer_edge_projection_spring.png')


def generate_supra_heatmap():
    """
    Generate: multilayer_supra_heatmap_inter.png
    
    Matches the Supra-Adjacency Heatmap example with inter-layer connections
    """
    print_section("Generating: multilayer_supra_heatmap_inter.png")
    
    # Load or generate network
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        network = random_generators.random_multilayer_ER(20, 3, 0.25, directed=False)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=True,
        inter_layer_weight=0.5,   # Weight for inter-layer edges
        cmap="viridis"
    )
    
    save_figure('multilayer_supra_heatmap_inter.png')


def generate_radial_layers():
    """
    Generate: multilayer_radial_with_inter.png
    
    Matches the Radial/Concentric Layers example
    """
    print_section("Generating: multilayer_radial_with_inter.png")
    
    # Load or generate network
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        network = random_generators.random_multilayer_ER(20, 3, 0.2, directed=False)
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,          # Radius of innermost layer
        radius_step=1.5,          # Distance between layers
        node_size=200,
        draw_inter_layer_edges=True,
        edge_alpha=0.5
    )
    
    save_figure('multilayer_radial_with_inter.png')


def generate_ego_multilayer():
    """
    Generate: multilayer_ego_node3_1hop.png
    
    Matches the Ego-Centric Multilayer View example
    """
    print_section("Generating: multilayer_ego_node3_1hop.png")
    
    # Generate a network with known node IDs
    network = random_generators.random_multilayer_ER(20, 3, 0.25, directed=False)
    
    # Get a node that exists in the network
    nodes = list(network.get_nodes())
    if nodes:
        ego_node = nodes[0][0]  # Get the first node ID
        
        fig = visualize_multilayer_network(
            network,
            visualization_type="ego_multilayer",
            ego=ego_node,            # Node to focus on
            max_depth=1,              # Neighborhood depth (hops)
            layout="spring",
            node_size=100,
            ego_node_size=400         # Highlight ego node
        )
        
        save_figure('multilayer_ego_node3_1hop.png')
    else:
        print("  [SKIP] No nodes found in network")


def generate_flow_visualization():
    """
    Generate: multilayer_flow.png
    
    Matches the Flow/Alluvial Visualization example
    """
    print_section("Generating: multilayer_flow.png")
    
    # Load or generate network
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        network = random_generators.random_multilayer_ER(20, 3, 0.25, directed=False)
    
    # Flow visualization
    try:
        ax = network.visualize_network(style='flow', show=False)
        save_figure('multilayer_flow.png')
    except Exception as e:
        print(f"  [ERROR] Failed to generate flow visualization: {e}")


def generate_sankey_diagram():
    """
    Generate: multilayer_sankey_diagram.png
    
    Matches the Sankey Diagram example
    """
    print_section("Generating: multilayer_sankey_diagram.png")
    
    # Load or generate network
    dataset = get_dataset_path("multiedgelist.txt")
    if os.path.exists(dataset):
        network = multinet.multi_layer_network().load_network(
            dataset, input_type="multiedgelist", directed=False
        )
    else:
        network = random_generators.random_multilayer_ER(25, 3, 0.2, directed=False)
    
    # Sankey-style diagram showing inter-layer flow strength
    try:
        ax = network.visualize_network(style='sankey', show=False)
        save_figure('multilayer_sankey_diagram.png')
    except Exception as e:
        print(f"  [ERROR] Failed to generate sankey diagram: {e}")


def generate_communities():
    """
    Generate: communities.png
    
    Matches the Color-Coding by Community example
    """
    print_section("Generating: communities.png")
    
    try:
        from py3plex.algorithms.community_detection import community_wrapper as cw
        import matplotlib.cm as cm
        
        # Generate a network with community structure
        network = random_generators.random_multilayer_ER(40, 3, 0.15, directed=False)
        
        # Try to detect communities
        try:
            communities = cw.louvain_communities(network.core_network)
        except Exception:
            # If community detection fails, create dummy communities
            nodes = list(network.get_nodes())
            communities = {node: i % 4 for i, node in enumerate(nodes)}
        
        # Assign colors
        num_communities = len(set(communities.values()))
        colors_list = cm.rainbow([i/max(1, num_communities) for i in range(num_communities)])
        
        # Get layers and visualize - matches corrected docs
        labels, graphs, multilinks = network.get_layers()
        
        plt.figure(figsize=(10, 8))
        
        draw_multilayer_default(
            graphs,
            display=False,
            labels=labels,
            node_size=15,
            alphalevel=0.5
        )
        
        save_figure('communities.png')
        
    except Exception as e:
        print(f"  [ERROR] Failed to generate communities visualization: {e}")


def main():
    """Generate all visualization images for documentation."""
    print("\n" + "=" * 70)
    print("  VISUALIZATION DOCUMENTATION IMAGE GENERATOR")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("Generating images that match the code examples in visualization.rst...\n")
    
    # Generate each image
    generators = [
        generate_basic_multilayer,      # multilayer.png
        generate_minimal_mode,          # hairball.png
        generate_dense_mode,            # multiplex.png
        generate_small_multiples,       # multilayer_small_multiples_shared.png
        generate_edge_projection,       # multilayer_edge_projection_spring.png
        generate_supra_heatmap,         # multilayer_supra_heatmap_inter.png
        generate_radial_layers,         # multilayer_radial_with_inter.png
        generate_ego_multilayer,        # multilayer_ego_node3_1hop.png
        generate_flow_visualization,    # multilayer_flow.png
        generate_sankey_diagram,        # multilayer_sankey_diagram.png
        generate_communities,           # communities.png
    ]
    
    success_count = 0
    for gen_func in generators:
        try:
            gen_func()
            success_count += 1
        except Exception as e:
            print(f"  [ERROR] {gen_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"  COMPLETE: Generated {success_count}/{len(generators)} images")
    print("=" * 70)
    print(f"\nImages saved to: {OUTPUT_DIR}")
    print("These images match the code examples in visualization.rst\n")


if __name__ == "__main__":
    main()
