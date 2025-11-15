#!/usr/bin/env python
"""
Create a high-quality, publication-ready flow visualization for the README showcase.
This addresses aesthetic concerns: clear layer separation, larger nodes, prominent flows.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from py3plex.core import multinet
from py3plex.visualization.multilayer import draw_multilayer_flow


def create_showcase_network():
    """Create a richer, more visually interesting multilayer network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Social network (8 nodes, denser connections)
    nodes_l1 = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry']
    for node in nodes_l1:
        network.add_nodes([{'source': node, 'type': 'Social'}], input_type='dict')
    
    edges_l1 = [
        ('Alice', 'Bob'), ('Alice', 'Charlie'), ('Alice', 'Diana'),
        ('Bob', 'Charlie'), ('Bob', 'Eve'), ('Charlie', 'Diana'),
        ('Diana', 'Eve'), ('Diana', 'Frank'), ('Eve', 'Frank'),
        ('Frank', 'Grace'), ('Grace', 'Henry'), ('Eve', 'Henry'),
    ]
    for u, v in edges_l1:
        network.add_edges([{
            'source': u, 'target': v, 
            'source_type': 'Social', 'target_type': 'Social'
        }], input_type='dict')
    
    # Layer 2: Work network (7 nodes, hub structure)
    nodes_l2 = ['Alice', 'Bob', 'Charlie', 'Diana', 'Frank', 'Grace', 'Ivan']
    for node in nodes_l2:
        network.add_nodes([{'source': node, 'type': 'Work'}], input_type='dict')
    
    edges_l2 = [
        ('Alice', 'Diana'), ('Alice', 'Frank'), ('Alice', 'Grace'),
        ('Bob', 'Diana'), ('Charlie', 'Diana'), ('Diana', 'Frank'),
        ('Diana', 'Grace'), ('Diana', 'Ivan'), ('Frank', 'Ivan'),
    ]
    for u, v in edges_l2:
        network.add_edges([{
            'source': u, 'target': v,
            'source_type': 'Work', 'target_type': 'Work'
        }], input_type='dict')
    
    # Layer 3: Hobby network (6 nodes)
    nodes_l3 = ['Bob', 'Charlie', 'Diana', 'Eve', 'Grace', 'Henry']
    for node in nodes_l3:
        network.add_nodes([{'source': node, 'type': 'Hobby'}], input_type='dict')
    
    edges_l3 = [
        ('Bob', 'Charlie'), ('Charlie', 'Diana'), ('Diana', 'Eve'),
        ('Diana', 'Grace'), ('Grace', 'Henry'), ('Eve', 'Henry'),
        ('Bob', 'Henry'),
    ]
    for u, v in edges_l3:
        network.add_edges([{
            'source': u, 'target': v,
            'source_type': 'Hobby', 'target_type': 'Hobby'
        }], input_type='dict')
    
    # Add substantial inter-layer connections
    inter_edges = [
        # Social to Work
        ('Alice', 'Alice', 'Social', 'Work'),
        ('Bob', 'Bob', 'Social', 'Work'),
        ('Charlie', 'Charlie', 'Social', 'Work'),
        ('Diana', 'Diana', 'Social', 'Work'),
        ('Frank', 'Frank', 'Social', 'Work'),
        ('Grace', 'Grace', 'Social', 'Work'),
        
        # Work to Hobby
        ('Bob', 'Bob', 'Work', 'Hobby'),
        ('Charlie', 'Charlie', 'Work', 'Hobby'),
        ('Diana', 'Diana', 'Work', 'Hobby'),
        ('Grace', 'Grace', 'Work', 'Hobby'),
    ]
    
    for u, v, layer_u, layer_v in inter_edges:
        network.add_edges([{
            'source': u, 'target': v,
            'source_type': layer_u, 'target_type': layer_v
        }], input_type='dict')
    
    return network


def create_publication_quality_visualization():
    """Create a publication-quality flow visualization with excellent aesthetics."""
    print("Creating publication-quality flow visualization...")
    
    network = create_showcase_network()
    labels, graphs, multilinks = network.get_layers("diagonal")
    
    # Create figure with optimal size for showcase
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='white')
    fig.patch.set_facecolor('white')
    
    # Draw with optimized parameters for maximum visual impact
    draw_multilayer_flow(
        graphs,
        multilinks,
        labels=labels,
        ax=ax,
        display=False,
        layer_gap=2.2,          # Tighter spacing to reduce whitespace
        node_size=200,          # Much larger nodes (was 80)
        node_cmap="coolwarm",   # Better contrast colormap
        flow_alpha=0.6,         # More visible flows (was 0.4)
        flow_min_width=1.5,     # Thicker minimum (was 0.5)
        flow_max_width=12.0     # Much thicker maximum (was 6.0)
    )
    
    # Add visual enhancements
    # Draw clear rectangular boxes around each layer
    layer_colors = ['#FFE6E6', '#E6F3FF', '#E6FFE6']  # Soft red, blue, green
    y_positions = [0, 2.2, 4.4]  # Match layer_gap
    
    for idx, (y_pos, color) in enumerate(zip(y_positions, layer_colors)):
        # Get x extent for this layer
        layer_nodes = len(graphs[idx].nodes())
        x_min = -0.5
        x_max = layer_nodes - 0.5
        
        # Draw filled rectangle with border
        rect = mpatches.Rectangle(
            (x_min, y_pos - 0.8), 
            x_max - x_min, 
            1.6,
            facecolor=color,
            edgecolor='#666666',
            linewidth=2,
            alpha=0.2,
            zorder=0
        )
        ax.add_patch(rect)
    
    # Add title with better styling
    ax.text(0.5, 1.02, 'Multilayer Flow Visualization', 
           transform=ax.transAxes,
           fontsize=16, fontweight='bold', 
           ha='center', va='bottom',
           color='#2c3e50')
    
    # Add subtle subtitle
    ax.text(0.5, 0.98, 'Nodes sized and colored by network activity | Flow width shows connection strength', 
           transform=ax.transAxes,
           fontsize=9, style='italic',
           ha='center', va='top',
           color='#7f8c8d')
    
    # Adjust layout to minimize whitespace
    ax.set_xlim(-1, max(len(g.nodes()) for g in graphs) + 0.5)
    ax.set_ylim(-1, 5.5)
    
    # Save with high quality
    plt.tight_layout()
    plt.savefig('/tmp/multilayer_flow_showcase.png', 
               dpi=200, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    print("✓ Saved to: /tmp/multilayer_flow_showcase.png")
    plt.close()
    
    return '/tmp/multilayer_flow_showcase.png'


if __name__ == '__main__':
    print("="*70)
    print("CREATING SHOWCASE-QUALITY FLOW VISUALIZATION")
    print("="*70)
    print("\nAddressing aesthetic concerns:")
    print("  • Larger nodes (200 vs 80)")
    print("  • Thicker flows (1.5-12.0 vs 0.5-6.0)")
    print("  • Tighter layer spacing to reduce whitespace")
    print("  • Clear layer separation with background bands")
    print("  • Better color scheme (coolwarm)")
    print("  • Higher alpha for more visible flows")
    
    output_path = create_publication_quality_visualization()
    
    print("\n" + "="*70)
    print("✓ SHOWCASE VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\nGenerated: {output_path}")
    print("\nThis visualization features:")
    print("  - Clear visual distinction between layers")
    print("  - Large, prominent nodes")
    print("  - Thick, highly visible flow ribbons")
    print("  - Minimal whitespace")
    print("  - Publication-ready quality")
