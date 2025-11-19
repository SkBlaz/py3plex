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

# Define layers with more nodes
layers = ['social', 'professional', 'hobby']
nodes_per_layer = {
    'social': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 
               'George', 'Hannah', 'Ian', 'Julia', 'Kevin', 'Laura',
               'Mike', 'Nancy', 'Oscar', 'Paula'],
    'professional': ['Alice', 'Bob', 'Frank', 'Grace', 'Henry', 'Ivan',
                     'Julia', 'Kevin', 'Mike', 'Nancy', 'Quinn', 'Rachel',
                     'Steve', 'Tina', 'Uma', 'Victor'],
    'hobby': ['Bob', 'Charlie', 'David', 'Eve', 'Grace', 'Hannah',
              'Ian', 'Jane', 'Laura', 'Oscar', 'Paula', 'Quinn',
              'Rachel', 'Sam', 'Tina', 'Wendy']
}

print(f"  Layers: {layers}")
print(f"  Creating {sum(len(nodes) for nodes in nodes_per_layer.values())} node-layer pairs")

# Add nodes to layers
for layer in layers:
    for node in nodes_per_layer[layer]:
        network.add_nodes([{'source': node, 'type': layer}])

# Add edges within layers - creating denser networks
edges_by_layer = {
    'social': [
        # Core group connections
        ('Alice', 'Bob'), ('Bob', 'Charlie'), ('Charlie', 'David'),
        ('David', 'Eve'), ('Eve', 'Frank'), ('Frank', 'Alice'),
        ('Alice', 'Charlie'), ('Bob', 'David'), ('Charlie', 'Eve'),
        ('David', 'Frank'), ('Eve', 'Alice'), ('Frank', 'Bob'),
        # Extended network connections
        ('George', 'Hannah'), ('Hannah', 'Ian'), ('Ian', 'Julia'),
        ('Julia', 'Kevin'), ('Kevin', 'Laura'), ('Laura', 'George'),
        ('Mike', 'Nancy'), ('Nancy', 'Oscar'), ('Oscar', 'Paula'),
        ('Paula', 'Mike'),
        # Cross-group connections
        ('Alice', 'George'), ('Bob', 'Hannah'), ('Charlie', 'Ian'),
        ('David', 'Julia'), ('Eve', 'Kevin'), ('Frank', 'Laura'),
        ('George', 'Mike'), ('Hannah', 'Nancy'), ('Ian', 'Oscar'),
        ('Julia', 'Paula'), ('Kevin', 'Mike'), ('Laura', 'Nancy')
    ],
    'professional': [
        # Work team 1
        ('Alice', 'Bob'), ('Bob', 'Frank'), ('Frank', 'Grace'),
        ('Grace', 'Henry'), ('Henry', 'Ivan'), ('Ivan', 'Alice'),
        ('Alice', 'Grace'), ('Bob', 'Henry'), ('Frank', 'Ivan'),
        # Work team 2
        ('Julia', 'Kevin'), ('Kevin', 'Mike'), ('Mike', 'Nancy'),
        ('Nancy', 'Quinn'), ('Quinn', 'Rachel'), ('Rachel', 'Julia'),
        ('Julia', 'Mike'), ('Kevin', 'Nancy'), ('Mike', 'Quinn'),
        # Work team 3
        ('Steve', 'Tina'), ('Tina', 'Uma'), ('Uma', 'Victor'),
        ('Victor', 'Steve'),
        # Cross-team connections
        ('Alice', 'Julia'), ('Bob', 'Kevin'), ('Frank', 'Mike'),
        ('Grace', 'Nancy'), ('Henry', 'Quinn'), ('Ivan', 'Rachel'),
        ('Julia', 'Steve'), ('Kevin', 'Tina'), ('Mike', 'Uma'),
        ('Nancy', 'Victor')
    ],
    'hobby': [
        # Interest group 1
        ('Bob', 'Charlie'), ('Charlie', 'David'), ('David', 'Eve'),
        ('Eve', 'Grace'), ('Grace', 'Hannah'), ('Hannah', 'Bob'),
        ('Bob', 'David'), ('Charlie', 'Eve'), ('David', 'Grace'),
        # Interest group 2
        ('Ian', 'Jane'), ('Jane', 'Laura'), ('Laura', 'Oscar'),
        ('Oscar', 'Paula'), ('Paula', 'Quinn'), ('Quinn', 'Ian'),
        ('Ian', 'Laura'), ('Jane', 'Oscar'), ('Laura', 'Paula'),
        # Interest group 3
        ('Rachel', 'Sam'), ('Sam', 'Tina'), ('Tina', 'Wendy'),
        ('Wendy', 'Rachel'),
        # Cross-interest connections
        ('Bob', 'Ian'), ('Charlie', 'Jane'), ('David', 'Laura'),
        ('Eve', 'Oscar'), ('Grace', 'Paula'), ('Hannah', 'Quinn'),
        ('Ian', 'Rachel'), ('Jane', 'Sam'), ('Oscar', 'Tina'),
        ('Paula', 'Wendy')
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

# Add many more inter-layer edges (representing people active across multiple contexts)
print("\nStep 3: Adding inter-layer connections...")
inter_layer_connections = [
    # Social <-> Professional connections
    ('Alice', 'Alice', 'social', 'professional'),
    ('Bob', 'Bob', 'social', 'professional'),
    ('Frank', 'Frank', 'social', 'professional'),
    ('Julia', 'Julia', 'social', 'professional'),
    ('Kevin', 'Kevin', 'social', 'professional'),
    ('Mike', 'Mike', 'social', 'professional'),
    ('Nancy', 'Nancy', 'social', 'professional'),
    # Social <-> Hobby connections
    ('Bob', 'Bob', 'social', 'hobby'),
    ('Charlie', 'Charlie', 'social', 'hobby'),
    ('David', 'David', 'social', 'hobby'),
    ('Eve', 'Eve', 'social', 'hobby'),
    ('Hannah', 'Hannah', 'social', 'hobby'),
    ('Ian', 'Ian', 'social', 'hobby'),
    ('Laura', 'Laura', 'social', 'hobby'),
    ('Oscar', 'Oscar', 'social', 'hobby'),
    ('Paula', 'Paula', 'social', 'hobby'),
    # Professional <-> Hobby connections
    ('Bob', 'Bob', 'professional', 'hobby'),
    ('Grace', 'Grace', 'professional', 'hobby'),
    ('Julia', 'Julia', 'professional', 'hobby'),
    ('Kevin', 'Kevin', 'professional', 'hobby'),
    ('Mike', 'Mike', 'professional', 'hobby'),
    ('Nancy', 'Nancy', 'professional', 'hobby'),
    ('Quinn', 'Quinn', 'professional', 'hobby'),
    ('Rachel', 'Rachel', 'professional', 'hobby'),
    ('Tina', 'Tina', 'professional', 'hobby'),
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
    layout_algorithm="force",
    layer_gap=2.5,
    node_size_base=10,
    show_interlayer_edges=True,
    interlayer_edges=inter_layer_edges_list
)

if fig:
    # Enhance the figure with better styling
    fig.update_layout(
        title={
            'text': 'Interactive Multilayer Network<br><sub>Hover over nodes for details, drag to rotate</sub>',
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        hovermode='closest',
        plot_bgcolor='rgba(240, 240, 240, 0.9)'
    )
    
    print("✓ Interactive visualization created!")
    print("\nVisualization Features:")
    print("  • Layers arranged diagonally in 3D space")
    print("  • Layer-specific colors for easy identification")
    print("  • Node size represents degree centrality")
    print("  • Intra-layer edges: solid colored lines")
    print("  • Inter-layer edges: dashed gray lines")
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
    print("Network Statistics:")
    print(f"  • Total unique individuals: {len(set([n for nodes in nodes_per_layer.values() for n in nodes]))}")
    print(f"  • Total nodes (across all layers): {sum(len(nodes) for nodes in nodes_per_layer.values())}")
    print(f"  • Total intra-layer edges: {sum(len(edges) for edges in edges_by_layer.values())}")
    print(f"  • Total inter-layer edges: {len(inter_layer_connections)}")
    print("\nLayer Information:")
    print("  • Social layer: Personal relationships and friendships")
    print("  • Professional layer: Work and business connections")
    print("  • Hobby layer: Shared interests and activities")
    print("\nCross-layer nodes (active in multiple contexts):")
    cross_layer_nodes = {}
    for node in set([n for nodes in nodes_per_layer.values() for n in nodes]):
        appearances = [layer for layer, nodes in nodes_per_layer.items() if node in nodes]
        if len(appearances) > 1:
            cross_layer_nodes[node] = appearances
    
    # Show a sample of cross-layer nodes
    sample_size = min(10, len(cross_layer_nodes))
    for i, (node, node_layers) in enumerate(sorted(cross_layer_nodes.items())[:sample_size]):
        print(f"  • {node}: {', '.join(node_layers)}")
    if len(cross_layer_nodes) > sample_size:
        print(f"  ... and {len(cross_layer_nodes) - sample_size} more individuals active across layers")
    
    print("=" * 70)
    print("\nTip: Try these interactions:")
    print("  1. Hover over nodes to see their names and degrees")
    print("  2. Click and drag to rotate the 3D view")
    print("  3. Click legend items to show/hide specific layers")
    print("  4. Look for gray dashed lines connecting people across layers")
    print("  5. Notice the distinct colors: red (social), turquoise (prof), yellow (hobby)")
    print("=" * 70)
else:
    print("\n✗ Failed to create visualization")
    print("  Make sure plotly is installed: pip install plotly")
