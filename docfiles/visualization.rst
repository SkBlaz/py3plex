Network Visualization
=====================

Network visualization is essential for understanding structure, identifying patterns, and communicating findings. Py3plex provides specialized visualization capabilities designed specifically for multilayer networks, with support for both static publication-quality figures and interactive web-based exploration.

Why Multilayer Visualization Matters
-------------------------------------

Standard network visualization tools treat all edges and nodes uniformly, losing the rich layer information that distinguishes multilayer networks. Py3plex preserves this information through:

- **Layer-colored nodes**: Instantly see which layer each node belongs to
- **Diagonal layouts**: Show layer structure explicitly in 3D-like projections
- **Inter-layer edges**: Visualize connections that cross layer boundaries
- **Community overlays**: Combine structural groupings with layer information

Basic Visualization
-------------------

The simplest way to visualize a multilayer network is the "hairball" plot, which creates a force-directed layout with nodes colored by layer:

.. code-block:: python

    from py3plex.core import multinet
    
    # Load a multilayer network
    network = multinet.multi_layer_network().load_network(
        "../datasets/goslim_mirna.gpickle", 
        directed=False, 
        input_type="gpickle_biomine")
    
    # Create a hairball visualization
    # Nodes from different layers receive different colors automatically
    network.visualize_network(style="hairball")

**When to Use Hairball Plots:**

- Quick exploration of network structure
- Identifying clusters and isolated components
- Checking data loading (colors reveal layer distribution)
- Networks with up to ~500 nodes (larger networks become cluttered)

**Diagonal Multilayer Layout (Py3plex-Specific):**

The diagonal layout is py3plex's signature visualization, showing layers as separate groups arranged diagonally:

.. code-block:: python

    # Diagonal layout explicitly shows layer structure
    network.visualize_network(style="diagonal")

This layout is particularly effective for:

- Networks with clear layer separation
- Showing inter-layer connections explicitly
- Publication figures where layer structure matters
- Presentations explaining multilayer concepts

Interactive Visualization
-------------------------

For exploratory analysis and sharing with non-technical audiences, interactive visualizations allow zooming, panning, and hovering over nodes for details:

.. code-block:: python

    import networkx as nx
    from py3plex.visualization.multilayer import interactive_hairball_plot
    
    # Get network as NetworkX graph with layer colors
    network_colors, G = network.get_layers(style="hairball")
    
    # Compute layout positions
    pos = nx.spring_layout(G, seed=42)  # Seed for reproducibility
    
    # Compute node sizes based on degree (larger nodes = more connections)
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees.values() else 1
    node_sizes = [10 + 40 * (degrees[node] / max_degree) for node in G.nodes()]
    
    # Create color mapping for nodes
    color_mapping = {node: node_sizes[i] for i, node in enumerate(G.nodes())}
    
    # Create interactive visualization (opens in browser)
    fig = interactive_hairball_plot(G, node_sizes, color_mapping, pos, colorscale="Viridis")
    
    # Save to HTML file for sharing
    if fig:
        fig.write_html("network.html")

**Requirements for Interactive Visualization:**

.. code-block:: bash

    pip install plotly
    # or
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

**Interactive Features:**

- **Hover**: See node details (ID, layer, degree)
- **Zoom**: Mouse wheel to zoom in/out
- **Pan**: Click and drag to move the view
- **Save**: Export to PNG/SVG from the toolbar

Examples
--------

For detailed visualization examples covering various network types and styles, see:

- ``example_multilayer_visualization.py`` - Core visualization techniques and options
- ``example_visualization.py`` - Comparing different plotting styles
- ``example_community_visualization.py`` - Visualizing detected communities
- ``example_interactive_hairball.py`` - Interactive network visualization
- ``example_interactive_multilayer.py`` - Advanced interactive multilayer plots
- ``example_supra_adjacency.py`` - Visualizing supra-adjacency matrices

For comprehensive documentation on all visualization options, including presets, color schemes, and export options, see :doc:`visualization_guide`.

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
