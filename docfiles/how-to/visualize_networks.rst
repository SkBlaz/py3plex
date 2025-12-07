How to Visualize Multilayer Networks
=====================================

**Goal:** Create publication-ready visualizations of multilayer networks.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

Basic Visualization
-------------------

Quick Plot
~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'work', 'Carol', 'work', 1],
    ], input_type="list")
    
    # Visualize
    network.visualize_network(show=True)

This opens an interactive window with the network visualization.

Save to File
~~~~~~~~~~~~

.. code-block:: python

    network.visualize_network(
        output_file='network.png',
        show=False
    )

Customizing Visualizations
---------------------------

Node Sizes and Colors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import visualize_network_custom
    
    # Compute node importance
    from py3plex.dsl import Q
    result = Q.nodes().compute("degree").execute(network)
    degrees = {node: data['degree'] for node, data in result.items()}
    
    # Visualize with custom node sizes
    visualize_network_custom(
        network,
        node_sizes=degrees,
        node_color_by_layer=True,
        output_file='network_sized.png'
    )

Edge Weights
~~~~~~~~~~~~

.. code-block:: python

    visualize_network_custom(
        network,
        edge_width_by_weight=True,
        show=True
    )

Layout Algorithms
-----------------

Force-Directed Layout
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    
    hairball_plot(
        network,
        layout_algorithm='force_directed',
        output_file='force_layout.png'
    )

Circular Layout
~~~~~~~~~~~~~~~

.. code-block:: python

    hairball_plot(
        network,
        layout_algorithm='circular',
        output_file='circular_layout.png'
    )

Layer-Specific Visualization
-----------------------------

Visualize Single Layer
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Extract layer
    layer_network = Q.edges().from_layers(L["friends"]).execute(network)
    
    # Visualize
    layer_network.visualize_network(
        output_file='friends_layer.png',
        show=True
    )

Side-by-Side Layer Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, layer in enumerate(['friends', 'work', 'family']):
        layer_net = Q.edges().from_layers(L[layer]).execute(network)
        # Visualize on specific axis
        visualize_on_axis(layer_net, axes[idx], title=f'Layer: {layer}')
    
    plt.tight_layout()
    plt.savefig('layers_comparison.png', dpi=300)

Community Visualization
-----------------------

Color by Communities
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import louvain_communities
    from py3plex.visualization import visualize_communities
    
    # Detect communities
    communities = louvain_communities(network)
    
    # Visualize with community colors
    visualize_communities(
        network,
        communities,
        output_file='communities.png',
        show=True
    )

Interactive Visualization
-------------------------

Using Plotly
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import plotly_visualization
    
    # Create interactive plot
    fig = plotly_visualization(network)
    
    # Show in browser
    fig.show()
    
    # Or save as HTML
    fig.write_html('network_interactive.html')

Export for Gephi/Cytoscape
---------------------------

Export to GraphML
~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Convert to NetworkX
    G = network.to_networkx()
    
    # Export
    nx.write_graphml(G, 'network.graphml')

Then open `network.graphml` in Gephi or Cytoscape for advanced visualization.

Next Steps
----------

* **Compute statistics to visualize:** :doc:`compute_statistics`
* **Detect communities:** :doc:`run_community_detection`
* **API reference:** :doc:`../reference/api_index`
