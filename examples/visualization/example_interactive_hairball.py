"""
Interactive Visualization Example: Hairball Plot with Plotly

This example demonstrates how to:
1. Create a multilayer network
2. Generate an interactive 3D hairball visualization using Plotly
3. Explore the network interactively in a web browser

Requirements:
- plotly package (install with: pip install plotly)

Runtime: FAST (< 5 seconds) - Generates interactive HTML visualization
Note: This example creates an HTML file that can be opened in any web browser.
"""

import os
import networkx as nx
from py3plex.core import multinet, random_generators
from py3plex.visualization.multilayer import interactive_hairball_plot
from py3plex.visualization.colors import colors_default

print("=" * 60)
print("Interactive Hairball Visualization Example")
print("=" * 60)

# Check if plotly is available
try:
    import plotly
    print(f"✓ Plotly version {plotly.__version__} detected")
except ImportError:
    print("✗ Plotly not found. Install with: pip install plotly")
    print("  Or install py3plex with viz extras: pip install py3plex[viz]")
    exit(1)

# Generate a random multilayer network for demonstration
print("\nStep 1: Generating random multilayer network...")
print("  - Nodes: 50")
print("  - Layers: 3")
print("  - Edge probability: 0.15")

multilayer_net = random_generators.random_multilayer_ER(
    50,     # Number of nodes
    3,      # Number of layers
    0.15,   # Edge probability
    directed=False
)

print("✓ Network generated successfully")
multilayer_net.basic_stats()

# Convert to NetworkX graph for visualization
print("\nStep 2: Converting to NetworkX graph...")
network_colors, G = multilayer_net.get_layers(style="hairball")

# Compute layout positions
print("\nStep 3: Computing layout with spring algorithm...")
pos = nx.spring_layout(G, iterations=50, seed=42)

# Assign positions to nodes
for node in G.nodes():
    G.nodes[node]['pos'] = pos[node]

# Compute node sizes based on degree
print("\nStep 4: Computing node sizes based on degree...")
degrees = dict(G.degree())
max_degree = max(degrees.values()) if degrees else 1
node_sizes = [10 + 40 * (degrees[node] / max_degree) for node in G.nodes()]

print(f"  - Nodes: {G.number_of_nodes()}")
print(f"  - Edges: {G.number_of_edges()}")
print(f"  - Avg degree: {sum(degrees.values()) / len(degrees):.2f}")

# Create color mapping for nodes
print("\nStep 5: Creating node color mapping...")
color_mapping = {}
for i, node in enumerate(G.nodes()):
    # Assign colors based on community/layer
    color_idx = i % len(colors_default)
    color_mapping[node] = node_sizes[i]  # Use degree for color intensity

# Generate interactive visualization
print("\nStep 6: Generating interactive visualization...")
print("  This may take a few seconds...")

fig = interactive_hairball_plot(
    G,
    nsizes=node_sizes,
    final_color_mapping=color_mapping,
    pos=pos,
    colorscale="Viridis"  # Color scheme: Viridis, Rainbow, Blues, etc.
)

if fig:
    print("✓ Interactive visualization created successfully!")
    print("\nInteractive features:")
    print("  - Hover over nodes to see IDs")
    print("  - Zoom in/out with mouse wheel")
    print("  - Click and drag to rotate")
    print("  - Pan by clicking and dragging")
    
    # Save to HTML file
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "interactive_hairball.html")
    
    # Note: fig.show() is called inside interactive_hairball_plot
    # We can also save it to a file
    try:
        fig.write_html(output_file)
        print(f"\n✓ Visualization saved to: {output_file}")
        print("  Open this file in your web browser to explore the network!")
    except Exception as e:
        print(f"\nNote: Could not save HTML file: {e}")
        print("  The interactive plot should still be displayed in your browser.")
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("Close the browser window when done exploring.")
    print("=" * 60)
else:
    print("✗ Failed to create visualization. Check that plotly is installed.")
