"""
Interactive Multilayer Visualization Example

This example demonstrates advanced interactive visualization techniques for
multilayer networks using Plotly.

Features:
1. Multiple layers with different node sets
2. Inter-layer connections
3. Interactive 3D visualization
4. Custom color schemes per layer
5. Node hover information

Requirements:
- plotly package (install with: pip install plotly)

Runtime: FAST (< 10 seconds)
"""

import os
import networkx as nx
from py3plex.core import multinet
from py3plex.visualization.multilayer import interactive_hairball_plot
from py3plex.visualization.colors import colors_default

print("=" * 70)
print("Interactive Multilayer Network Visualization")
print("=" * 70)

# Check if plotly is available
try:
    import plotly.graph_objects as go
    print(" Plotly is available")
except ImportError:
    print(" Plotly not found. Install with: pip install plotly")
    print(" Skipping interactive visualization example")
    exit(0)

# Create a multilayer network
print("\nStep 1: Creating multilayer network...")
network = multinet.multi_layer_network()

# Add nodes to different layers
layers = ['social', 'professional', 'family']
nodes_per_layer = {
    'social': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'professional': ['Alice', 'Bob', 'Frank', 'Grace', 'Henry'],
    'family': ['Alice', 'Charlie', 'David', 'Ivan', 'Jane']
}

print(f" Layers: {layers}")

for layer in layers:
    for node in nodes_per_layer[layer]:
        network.add_nodes([{'source': node, 'type': layer}])

# Add edges within layers
edges_by_layer = {
    'social': [('Alice', 'Bob'), ('Bob', 'Charlie'), ('Charlie', 'David'),
               ('David', 'Eve'), ('Eve', 'Alice')],
    'professional': [('Alice', 'Bob'), ('Bob', 'Frank'), ('Frank', 'Grace'),
                     ('Grace', 'Henry'), ('Henry', 'Alice')],
    'family': [('Alice', 'Charlie'), ('Charlie', 'David'), ('David', 'Ivan'),
               ('Ivan', 'Jane'), ('Jane', 'Alice')]
}

for layer in layers:
    for src, tgt in edges_by_layer[layer]:
        network.add_edges([{
            'source': src,
            'target': tgt,
            'source_type': layer,
            'target_type': layer
        }])

# Add inter-layer edges (same person across layers)
print("\nStep 2: Adding inter-layer connections...")
inter_layer_edges = [
    ('Alice', 'Alice', 'social', 'professional'),
    ('Alice', 'Alice', 'professional', 'family'),
    ('Bob', 'Bob', 'social', 'professional'),
    ('Charlie', 'Charlie', 'social', 'family'),
    ('David', 'David', 'social', 'family'),
]

for src, tgt, layer1, layer2 in inter_layer_edges:
    network.add_edges([{
        'source': src,
        'target': tgt,
        'source_type': layer1,
        'target_type': layer2
    }])

print(" Network created")
network.basic_stats()

# Convert to aggregate NetworkX graph for visualization
print("\nStep 3: Creating aggregate visualization...")
# Get the core network as a graph
G = nx.Graph()

# Add all nodes
all_nodes = set()
for layer in layers:
    for node in nodes_per_layer[layer]:
        all_nodes.add(node)

for node in all_nodes:
    G.add_node(node)

# Add all edges (aggregate across layers)
for layer in layers:
    for src, tgt in edges_by_layer[layer]:
        if G.has_edge(src, tgt):
            G[src][tgt]['weight'] = G[src][tgt].get('weight', 0) + 1
        else:
            G.add_edge(src, tgt, weight=1)

print(f" Aggregate graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Compute layout
print("\nStep 4: Computing 3D spring layout...")
pos = nx.spring_layout(G, dim=2, iterations=100, seed=42)

# Compute node attributes
degrees = dict(G.degree())
max_degree = max(degrees.values())

# Node sizes based on degree
node_sizes = [20 + 80 * (degrees[node] / max_degree) for node in G.nodes()]

# Color nodes by their primary layer presence
print("\nStep 5: Assigning colors by layer membership...")
node_layer_counts = {node: {layer: 0 for layer in layers} for node in all_nodes}
for layer in layers:
    for node in nodes_per_layer[layer]:
        node_layer_counts[node][layer] = 1

# Determine primary layer for each node
node_primary_layer = {}
for node in all_nodes:
    # Count which layers this node belongs to
    layer_count = sum(node_layer_counts[node].values())
    if layer_count > 0:
        for layer in layers:
            if node_layer_counts[node][layer] == 1:
                node_primary_layer[node] = layer
                break

# Create color mapping
layer_colors = {
    'social': 0,
    'professional': 50,
    'family': 100
}

color_mapping = {}
for node in G.nodes():
    primary_layer = node_primary_layer.get(node, layers[0])
    color_mapping[node] = layer_colors.get(primary_layer, 0)

# Create interactive visualization
print("\nStep 6: Generating interactive Plotly visualization...")

fig = interactive_hairball_plot(
    G,
    nsizes=node_sizes,
    final_color_mapping=color_mapping,
    pos=pos,
    colorscale="Viridis"
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

    print(" Interactive visualization created!")
    print("\nFeatures:")
    print("  - Node size = degree centrality")
    print("  - Node color = primary layer membership")
    print("  - Hover for node details")
    print("  - Click and drag to explore")
    print("  - Zoom with mouse wheel")

    # Save to HTML
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "interactive_multilayer.html")

    try:
        fig.write_html(output_file)
        print(f"\n Saved to: {output_file}")
        print("  Open in your browser to explore!")
    except Exception as e:
        print(f"\nNote: Could not save file: {e}")

    print("\n" + "=" * 70)
    print("Layer Legend:")
    print("  - Social layer: Dark blue nodes")
    print("  - Professional layer: Green nodes")
    print("  - Family layer: Yellow nodes")
    print("  - Cross-layer nodes: Mixed colors")
    print("=" * 70)
else:
    print(" Failed to create visualization")
