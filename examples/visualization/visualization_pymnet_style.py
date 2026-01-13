"""
Pymnet Style Multilayer Visualization Example

This example demonstrates the pymnet style multilayer network visualization,
inspired by the pymnet library's visualization approach. The implementation
is native to py3plex.

Reference:
    Pymnet library: https://github.com/bolozna/Multilayer-networks-library
    Kivelä, M., et al. (2014). Multilayer networks. Journal of complex networks, 2(3), 203-271.

Features demonstrated:
- Creating a 3-layer multiplex network
- Adding inter-layer coupling edges
- Pymnet style visualization with deterministic layout
- Saving outputs in PNG and SVG formats
- Different styling options

The pymnet style visualization displays multilayer networks with:
- Layers stacked along a vertical axis
- Shared node positions across layers (deterministic layout)
- Clear distinction between intra-layer and inter-layer edges
- Configurable node and edge styling
"""

import os
import networkx as nx
import matplotlib.pyplot as plt
from py3plex.core import multinet
from py3plex.visualization.pymnet_style import draw_multilayer_pymnet

print("=" * 70)
print("PYMNET STYLE MULTILAYER VISUALIZATION EXAMPLE")
print("=" * 70)

# ============================================================================
# Example 1: Simple 3-Layer Multiplex Network
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 1: Simple 3-Layer Multiplex with Inter-layer Coupling")
print("=" * 70)

# Create a py3plex multilayer network
network = multinet.multi_layer_network(directed=False)

# Define nodes (same nodes across all layers - multiplex structure)
nodes = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']

# Layer 1: Social Network
print("\nBuilding Layer 1: Social Network...")
for node in nodes:
    network.add_nodes([{'source': node, 'type': 'social'}], input_type='dict')

social_edges = [
    ('Alice', 'Bob'),
    ('Bob', 'Charlie'),
    ('Charlie', 'Diana'),
    ('Diana', 'Eve'),
    ('Eve', 'Alice'),
]

for u, v in social_edges:
    network.add_edges([{
        'source': u,
        'target': v,
        'source_type': 'social',
        'target_type': 'social'
    }], input_type='dict')

# Layer 2: Work Collaboration Network
print("Building Layer 2: Work Collaboration Network...")
for node in nodes:
    network.add_nodes([{'source': node, 'type': 'work'}], input_type='dict')

work_edges = [
    ('Alice', 'Charlie'),
    ('Bob', 'Diana'),
    ('Charlie', 'Eve'),
]

for u, v in work_edges:
    network.add_edges([{
        'source': u,
        'target': v,
        'source_type': 'work',
        'target_type': 'work'
    }], input_type='dict')

# Layer 3: Online Gaming Network
print("Building Layer 3: Online Gaming Network...")
for node in nodes:
    network.add_nodes([{'source': node, 'type': 'gaming'}], input_type='dict')

gaming_edges = [
    ('Alice', 'Diana'),
    ('Bob', 'Eve'),
    ('Charlie', 'Alice'),
]

for u, v in gaming_edges:
    network.add_edges([{
        'source': u,
        'target': v,
        'source_type': 'gaming',
        'target_type': 'gaming'
    }], input_type='dict')

# Add inter-layer coupling (same nodes across layers)
print("Adding inter-layer coupling edges...")
# Note: py3plex doesn't directly support inter-layer edges in this format,
# so we'll demonstrate using the dict format instead in Example 2

print(f"\nNetwork created with {len(nodes)} nodes per layer and 3 layers")
print(f" Social layer: {len(social_edges)} edges")
print(f" Work layer: {len(work_edges)} edges")
print(f" Gaming layer: {len(gaming_edges)} edges")

# Draw pymnet style visualization
print("\nGenerating pymnet style visualization...")
fig, ax, handles, positions = draw_multilayer_pymnet(
    network,
    layout="spring",
    seed=42,
    layer_gap=2.5,
    node_size=150,
    node_alpha=0.9,
    intra_edge_alpha=0.3,
    inter_edge_alpha=0.15,
    intra_edge_width=1.0,
    inter_edge_width=0.8,
    show_node_labels=True,
    show_layer_labels=True,
    node_color_by="layer",
    figsize=(12, 8)
)

# Save outputs
output_dir = "/tmp/pymnet_style_outputs"
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, "pymnet_example1.png")
svg_path = os.path.join(output_dir, "pymnet_example1.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight')
fig.savefig(svg_path, bbox_inches='tight')

print(f"\n Visualization saved:")
print(f" PNG: {png_path}")
print(f" SVG: {svg_path}")

plt.close(fig)

# ============================================================================
# Example 2: Using NetworkX Graphs Dictionary Format
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 2: NetworkX Graphs with Inter-layer Edges")
print("=" * 70)

# Create layers as separate NetworkX graphs
layer_social = nx.Graph()
layer_social.add_edges_from([
    ('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E'), ('E', 'A')
])

layer_work = nx.Graph()
layer_work.add_edges_from([
    ('A', 'C'), ('B', 'D'), ('C', 'E')
])

layer_family = nx.Graph()
layer_family.add_edges_from([
    ('A', 'D'), ('B', 'E')
])

layers_dict = {
    'Social': layer_social,
    'Work': layer_work,
    'Family': layer_family
}

print(f"\nCreated 3 layers:")
print(f" Social: {layer_social.number_of_nodes()} nodes, {layer_social.number_of_edges()} edges")
print(f" Work: {layer_work.number_of_nodes()} nodes, {layer_work.number_of_edges()} edges")
print(f" Family: {layer_family.number_of_nodes()} nodes, {layer_family.number_of_edges()} edges")

# Draw with different styling
print("\nGenerating pymnet style visualization with degree-based coloring...")
fig, ax, handles, positions = draw_multilayer_pymnet(
    layers_dict,
    layout="spring",
    seed=123,
    layer_gap=3.0,
    node_size=200,
    node_color_by="degree",  # Color by degree
    show_node_labels=True,
    show_layer_labels=True,
    figsize=(12, 9)
)

png_path = os.path.join(output_dir, "pymnet_example2_degree.png")
svg_path = os.path.join(output_dir, "pymnet_example2_degree.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight')
fig.savefig(svg_path, bbox_inches='tight')

print(f"\n Visualization saved:")
print(f" PNG: {png_path}")
print(f" SVG: {svg_path}")

plt.close(fig)

# ============================================================================
# Example 3: Edge List Format with Inter-layer Connections
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 3: Edge List Format with Inter-layer Edges")
print("=" * 70)

# Create edge list including inter-layer edges
edge_list = [
    # Layer 1 edges
    ('node1', 'L1', 'node2', 'L1'),
    ('node2', 'L1', 'node3', 'L1'),
    ('node3', 'L1', 'node4', 'L1'),
    # Layer 2 edges
    ('node1', 'L2', 'node3', 'L2'),
    ('node2', 'L2', 'node4', 'L2'),
    # Layer 3 edges
    ('node1', 'L3', 'node4', 'L3'),
    ('node3', 'L3', 'node4', 'L3'),
    # Inter-layer connections (couplings)
    ('node1', 'L1', 'node1', 'L2'),
    ('node1', 'L2', 'node1', 'L3'),
    ('node3', 'L1', 'node3', 'L2'),
    ('node3', 'L2', 'node3', 'L3'),
    ('node4', 'L1', 'node4', 'L2'),
]

print(f"\nCreated edge list with {len(edge_list)} edges")
intra_count = sum(1 for u, lu, v, lv in edge_list if lu == lv)
inter_count = sum(1 for u, lu, v, lv in edge_list if lu != lv)
print(f" Intra-layer edges: {intra_count}")
print(f" Inter-layer edges: {inter_count}")

# Draw with circular layout
print("\nGenerating pymnet style visualization with circular layout...")
fig, ax, handles, positions = draw_multilayer_pymnet(
    edge_list,
    layout="circular",
    seed=42,
    layer_gap=2.0,
    node_size=180,
    show_node_labels=True,
    show_layer_labels=True,
    intra_edge_alpha=0.4,
    inter_edge_alpha=0.2,
    figsize=(10, 8)
)

png_path = os.path.join(output_dir, "pymnet_example3_edgelist.png")
svg_path = os.path.join(output_dir, "pymnet_example3_edgelist.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight')
fig.savefig(svg_path, bbox_inches='tight')

print(f"\n Visualization saved:")
print(f" PNG: {png_path}")
print(f" SVG: {svg_path}")

plt.close(fig)

# ============================================================================
# Example 4: Custom Node Coloring
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 4: Custom Node Coloring Function")
print("=" * 70)

# Create simple multilayer network
layers = {
    'Layer A': nx.path_graph(5),
    'Layer B': nx.cycle_graph(5),
    'Layer C': nx.star_graph(4)
}

print(f"\nCreated 3 layers with different structures:")
print(f" Layer A: Path graph (5 nodes)")
print(f" Layer B: Cycle graph (5 nodes)")
print(f" Layer C: Star graph (5 nodes)")

# Custom coloring function
def custom_color_function(node, layer):
    """Color nodes based on layer and node ID."""
    colors = {
        'Layer A': '#e74c3c',  # Red
        'Layer B': '#3498db',  # Blue
        'Layer C': '#2ecc71'   # Green
    }
    return colors.get(layer, '#95a5a6')

print("\nGenerating pymnet style visualization with custom coloring...")
fig, ax, handles, positions = draw_multilayer_pymnet(
    layers,
    layout="kamada_kawai",
    seed=42,
    layer_gap=2.8,
    node_size=160,
    node_color_by=custom_color_function,  # Custom coloring
    show_node_labels=True,
    show_layer_labels=True,
    figsize=(10, 8)
)

png_path = os.path.join(output_dir, "pymnet_example4_custom.png")
svg_path = os.path.join(output_dir, "pymnet_example4_custom.svg")

fig.savefig(png_path, dpi=150, bbox_inches='tight')
fig.savefig(svg_path, bbox_inches='tight')

print(f"\n Visualization saved:")
print(f" PNG: {png_path}")
print(f" SVG: {svg_path}")

plt.close(fig)

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 70)
print("PYMNET STYLE VISUALIZATION EXAMPLES COMPLETE")
print("=" * 70)

print(f"""
Summary of outputs saved to: {output_dir}

Examples created:
1. Simple 3-layer multiplex (social, work, gaming networks)
2. NetworkX graphs with degree-based coloring
3. Edge list format with inter-layer connections
4. Custom node coloring function

Key features of pymnet style visualization:
- Deterministic layouts (controlled by seed parameter)
- Shared node positions across layers
- Clear visual separation between layers
- Configurable node and edge styling
- Support for multiple input formats
- Export to PNG and SVG formats

For more information:
- See py3plex documentation on visualization
- Reference: pymnet library (https://github.com/bolozna/Multilayer-networks-library)
- Kivelä et al. (2014). Multilayer networks. Journal of complex networks.
""")

print("=" * 70)
print("Example complete! Check the output directory for visualizations.")
print("=" * 70)
