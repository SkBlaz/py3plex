Network Visualization
=====================

py3plex provides specialized visualization for multilayer networks, with support for both 
static and interactive visualizations.

Basic Visualization
-------------------

Hairball plot (standard network layout):

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/goslim_mirna.gpickle", 
        directed=False, 
        input_type="gpickle_biomine")
    
    network.visualize_network(style="hairball")

Diagonal multilayer layout (py3plex-specific):

.. code-block:: python

    network.visualize_network(style="diagonal")

Interactive Visualization
-------------------------

For interactive exploration in web browsers or Jupyter notebooks:

.. code-block:: python

    import networkx as nx
    from py3plex.visualization.multilayer import interactive_hairball_plot
    
    # Get network as NetworkX graph
    network_colors, G = network.get_layers(style="hairball")
    
    # Compute layout
    pos = nx.spring_layout(G, seed=42)
    
    # Compute node properties
    degrees = dict(G.degree())
    node_sizes = [10 + 40 * (degrees[node] / max(degrees.values())) for node in G.nodes()]
    color_mapping = {node: node_sizes[i] for i, node in enumerate(G.nodes())}
    
    # Create interactive visualization
    fig = interactive_hairball_plot(G, node_sizes, color_mapping, pos, colorscale="Viridis")
    
    # Save to HTML
    if fig:
        fig.write_html("network.html")

**Requirements:** Install plotly for interactive features:

.. code-block:: bash

    pip install plotly
    # or
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

Examples
--------

For detailed visualization examples, see:

- ``example_multilayer_visualization.py`` - Core visualization techniques
- ``example_visualization.py`` - Various plotting styles
- ``example_community_visualization.py`` - Community detection visualization
- ``example_interactive_hairball.py`` - Interactive network visualization
- ``example_interactive_multilayer.py`` - Advanced interactive multilayer plots
- ``example_supra_adjacency.py`` - Supra-adjacency matrices

For comprehensive documentation on visualization options, see :doc:`visualization_guide`.

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
