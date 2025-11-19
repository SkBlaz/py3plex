"""
Interactive Diagonal Multilayer Visualization Example

This example demonstrates the interactive diagonal multilayer network visualization
using Plotly. This visualization extends the traditional diagonal layout by making
it interactive and 3D, allowing users to explore multilayer networks dynamically.

Features:
1. Interactive 3D diagonal layout for multilayer networks
2. Layers positioned diagonally in 3D space
3. Hover to see node and layer information
4. Rotate, zoom, and pan the visualization
5. Inter-layer edges shown as dashed lines
6. Node sizes scaled by degree

Requirements:
- plotly package (install with: pip install plotly)

Runtime: FAST (< 10 seconds)
"""

import os
import networkx as nx
from py3plex.core import multinet
from py3plex.visualization.multilayer import interactive_diagonal_plot

print("=" * 70)
print("Interactive Diagonal Multilayer Network Visualization")
print("=" * 70)

# Check if plotly is available
try:
    import plotly.graph_objects as go
    print("✓ Plotly is available")
except ImportError:
    print("✗ Plotly not found. Install with: pip install plotly")
    exit(1)

# Create a multilayer network
print("\nStep 1: Creating multilayer network...")
network = multinet.multi_layer_network()

# Define layers
layers = ['social', 'professional', 'hobby']
nodes_per_layer = {
    'social': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank'],
    'professional': ['Alice', 'Bob', 'Grace', 'Henry', 'Ivan', 'Frank'],
    'hobby': ['Bob', 'Charlie', 'David', 'Grace', 'Jane', 'Eve']
}

print(f"  Layers: {layers}")
print(f"  Creating {sum(len(nodes) for nodes in nodes_per_layer.values())} node-layer pairs")

# Add nodes to layers
for layer in layers:
    for node in nodes_per_layer[layer]:
        network.add_nodes([{'source': node, 'type': layer}])

# Add edges within layers
edges_by_layer = {
    'social': [
        ('Alice', 'Bob'), ('Bob', 'Charlie'), ('Charlie', 'David'),
        ('David', 'Eve'), ('Eve', 'Frank'), ('Frank', 'Alice'),
        ('Alice', 'Charlie'), ('Bob', 'David')
    ],
    'professional': [
        ('Alice', 'Bob'), ('Bob', 'Grace'), ('Grace', 'Henry'),
        ('Henry', 'Ivan'), ('Ivan', 'Frank'), ('Frank', 'Alice'),
        ('Grace', 'Frank')
    ],
    'hobby': [
        ('Bob', 'Charlie'), ('Charlie', 'David'), ('David', 'Grace'),
        ('Grace', 'Jane'), ('Jane', 'Eve'), ('Eve', 'Bob'),
        ('Charlie', 'Eve')
    ]
}

print("\nStep 2: Adding intra-layer edges...")
total_edges = 0
for layer in layers:
    for src, tgt in edges_by_layer[layer]:
        network.add_edges([{
            'source': src,
            'target': tgt,
            'source_type': layer,
            'target_type': layer
        }])
        total_edges += 1

print(f"  Added {total_edges} intra-layer edges")

# Add inter-layer edges (same person across layers)
print("\nStep 3: Adding inter-layer connections...")
inter_layer_connections = [
    ('Alice', 'Alice', 'social', 'professional'),
    ('Bob', 'Bob', 'social', 'professional'),
    ('Bob', 'Bob', 'social', 'hobby'),
    ('Bob', 'Bob', 'professional', 'hobby'),
    ('Charlie', 'Charlie', 'social', 'hobby'),
    ('David', 'David', 'social', 'hobby'),
    ('Eve', 'Eve', 'social', 'hobby'),
    ('Frank', 'Frank', 'social', 'professional'),
    ('Grace', 'Grace', 'professional', 'hobby'),
]

inter_layer_edges_list = []
for src, tgt, layer1, layer2 in inter_layer_connections:
    network.add_edges([{
        'source': src,
        'target': tgt,
        'source_type': layer1,
        'target_type': layer2
    }])
    inter_layer_edges_list.append((src, tgt))

print(f"  Added {len(inter_layer_connections)} inter-layer edges")

# Display network statistics
print("\n✓ Network created")
network.basic_stats()

# Get layers for visualization
print("\nStep 4: Preparing layers for visualization...")
labels_list, graphs, multilinks = network.get_layers("diagonal")

print(f"  Extracted {len(graphs)} layers:")
for label, graph in zip(labels_list, graphs):
    print(f"    - {label}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

# Create interactive diagonal visualization
print("\nStep 5: Creating interactive 3D diagonal visualization...")
print("  This may take a moment...")

fig = interactive_diagonal_plot(
    graphs,
    layer_labels=labels_list,
    layout_algorithm="spring",
    layer_gap=3.0,
    node_size_base=8,
    colorscale="Viridis",
    show_interlayer_edges=True,
    interlayer_edges=inter_layer_edges_list
)

if fig:
    print("\n✓ Interactive visualization created!")
    print("\nVisualization Features:")
    print("  • Layers arranged diagonally in 3D space")
    print("  • Node size represents degree centrality")
    print("  • Node color represents degree (darker = higher degree)")
    print("  • Intra-layer edges: solid gray lines")
    print("  • Inter-layer edges: dashed red lines")
    print("  • Hover over nodes for details")
    print("  • Click and drag to rotate")
    print("  • Scroll to zoom")
    print("  • Use legend to toggle layer visibility")
    
    # Save to HTML
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "interactive_diagonal_multilayer.html")
    
    try:
        fig.write_html(output_file)
        print(f"\n✓ Saved to: {output_file}")
        print("  Open in your browser to explore interactively!")
    except Exception as e:
        print(f"\nNote: Could not save file: {e}")
    
    print("\n" + "=" * 70)
    print("Layer Information:")
    print("  • Social layer: Personal relationships")
    print("  • Professional layer: Work connections")
    print("  • Hobby layer: Shared interests")
    print("\nCross-layer nodes (appear in multiple layers):")
    cross_layer_nodes = set()
    for layer_nodes in nodes_per_layer.values():
        for node in layer_nodes:
            appearances = sum(1 for nodes in nodes_per_layer.values() if node in nodes)
            if appearances > 1:
                cross_layer_nodes.add(node)
    
    for node in sorted(cross_layer_nodes):
        node_layers = [layer for layer, nodes in nodes_per_layer.items() if node in nodes]
        print(f"  • {node}: {', '.join(node_layers)}")
    
    print("=" * 70)
    print("\nTip: Try these interactions:")
    print("  1. Hover over nodes to see their names and degrees")
    print("  2. Click and drag to rotate the 3D view")
    print("  3. Click legend items to show/hide specific layers")
    print("  4. Look for red dashed lines connecting the same person across layers")
    print("=" * 70)
else:
    print("\n✗ Failed to create visualization")
    print("  Make sure plotly is installed: pip install plotly")
