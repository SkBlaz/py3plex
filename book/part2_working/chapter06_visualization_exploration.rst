.. _visualization-chapter:

Visualization and Exploration
========================================

Multilayer networks present unique visualization challenges: how do you clearly show multiple relationship types while preserving the overall structure? This chapter covers py3plex's visualization capabilities, from quick exploratory plots to publication-ready figures.

Overview
--------

Visualizing multilayer networks requires balancing several concerns:

* **Clarity:** Individual layers must be distinguishable
* **Structure:** Cross-layer connections should be visible
* **Scale:** Techniques must work for networks of varying sizes (10 to 10,000+ nodes)
* **Purpose:** Exploratory plots need different settings than publication figures

py3plex provides three main visualization approaches:

1. **Static multilayer plots** — Show all layers simultaneously with customizable layouts
2. **Matrix visualizations** — Display the supra-adjacency matrix structure
3. **Layer-specific views** — Examine individual layers in detail

Quick Start
-----------

Basic Multilayer Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Visualize with defaults
    draw_multilayer_default(
        network.get_layers(),  # Returns dict of layer graphs
        display=True,
        labels=True
    )

This produces a circular layout with each layer shown in a different color.

.. admonition:: API Note: Input Format
   :class: note

   ``draw_multilayer_default`` expects a dict or list of NetworkX graphs. Always use ``network.get_layers()`` to get the properly formatted dict of layer graphs. This method handles layout computation and layer separation automatically.

Preset Visualization Modes
---------------------------

Py3plex provides three preset modes optimized for different network scales.

Minimal Mode (Large Networks >1000 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimized for networks where detail isn't critical and performance matters:

.. code-block:: python

    # Large network preset
    draw_multilayer_default(
        network.get_layers(),
        node_size=5,              # Small nodes
        labels=False,             # No labels (too cluttered)
        edge_size=0.5,            # Thin edges
        alphalevel=0.3,           # Transparent edges
        background_shape="circle",
        display=True,
        remove_isolated_nodes=True
    )

**Use cases:** Large social networks, overview visualizations, pattern detection at macro level.

**Advantages:** Fast rendering, reduced clutter, shows overall structure.

Balanced Mode (Medium Networks 100-1000 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default settings that work well for most networks:

.. code-block:: python

    # Balanced preset (this is the default)
    draw_multilayer_default(
        network.get_layers(),
        node_size=10,             # Medium nodes
        labels=True,              # Show layer labels
        edge_size=1.0,            # Normal edges
        alphalevel=0.13,          # Semi-transparent
        background_shape="circle",
        networks_color="rainbow",
        display=True
    )

**Use cases:** Most research networks, exploratory analysis, publication figures with moderate detail.

**Advantages:** Good readability, reasonable performance, suitable for most publications.

Dense Mode (Small Networks <100 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Maximum detail for small networks where every node matters:

.. code-block:: python

    # Dense preset for detailed examination
    draw_multilayer_default(
        network.get_layers(),
        node_size=20,             # Large nodes
        labels=True,
        node_labels=True,         # Show node IDs
        node_font_size=10,
        scale_by_size=True,       # Scale by degree
        edge_size=2.0,            # Thick edges
        alphalevel=0.8,           # Mostly opaque
        background_shape="rectangle",
        display=True
    )

**Use cases:** Small case studies, detailed node-level analysis, high-quality publication figures.

**Advantages:** Maximum detail, clear node identification, professional appearance.

Layout Options
--------------

Circular Layout (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Arranges layers in a circle, good for showing inter-layer connections:

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        background_shape="circle",
        rectanglex=1.0,  # Circle radius
        rectangley=1.0
    )

**Best for:** 2-10 layers, symmetric interactions, publication figures.

Rectangular Layout
~~~~~~~~~~~~~~~~~~

Arranges layers in a grid, good for many layers or hierarchical structures:

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        background_shape="rectangle",
        rectanglex=2.0,  # Width
        rectangley=1.0   # Height
    )

**Best for:** Many layers (>10), hierarchical networks, time-series data, wide figures.

Auto-Scaling Features
---------------------

Node Sizing by Degree
~~~~~~~~~~~~~~~~~~~~~

Automatically scale node sizes by their degree:

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        scale_by_size=True,    # Enable auto-scaling
        node_size=10           # Base size
    )

Hub nodes become larger, making them easy to identify.

Color Assignment
~~~~~~~~~~~~~~~~

Py3plex uses colorblind-safe palettes by default:

.. code-block:: python

    # Automatic rainbow colors
    draw_multilayer_default(
        network.get_layers(),
        networks_color="rainbow"
    )
    
    # Custom palette
    draw_multilayer_default(
        network.get_layers(),
        networks_color=["#FF6B6B", "#4ECDC4", "#45B7D1"]
    )

**Available palettes** (from ``py3plex.config``):

- ``colorblind_safe``: 8 colors safe for colorblind viewers
- ``wong``: 7-color Wong palette (scientifically validated)
- ``tol_bright``: 7 bright colors

Matrix Visualizations
---------------------

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~

Visualize the full supra-adjacency matrix structure:

.. code-block:: python

    # Display matrix view
    network.visualize_matrix({"display": True})

This shows the block structure: diagonal blocks are intra-layer edges, off-diagonal blocks are inter-layer edges.

**Use cases:** Understanding network structure, debugging layer connections, small networks only (<500 nodes).

Exploration Workflows
---------------------

Layer Views
~~~~~~~~~~~

Examine individual layers:

.. code-block:: python

    # Extract and visualize a single layer
    layer_subgraph = network.get_layer("social")
    
    import networkx as nx
    import matplotlib.pyplot as plt
    
    nx.draw(layer_subgraph, with_labels=True)
    plt.show()

Cross-Layer Pattern Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the DSL to filter and visualize subsets:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Find high-degree nodes across specific layers
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["professional"])
         .where(degree__gt=10)
         .execute(network)
    )
    
    # Extract subgraph for visualization
    high_degree_nodes = list(result.node_ids)
    subgraph = network.core_network.subgraph(high_degree_nodes)

Node Neighborhoods
~~~~~~~~~~~~~~~~~~

Extract ego networks (neighborhood around a specific node):

.. code-block:: python

    import networkx as nx
    
    # Get 2-hop neighborhood around 'Alice'
    alice_ego = nx.ego_graph(network.core_network, ('Alice', 'social'), radius=2)
    
    # Visualize
    nx.draw(alice_ego, with_labels=True)

Performance Considerations
--------------------------

Visualization performance depends heavily on network size:

* **<100 nodes:** All visualization modes work well
* **100-1000 nodes:** Use balanced or minimal mode; avoid node labels
* **1000-5000 nodes:** Use minimal mode; rendering may be slow
* **>5000 nodes:** Static visualizations become impractical; use matrix view or export to specialized tools

**Tips for large networks:**

1. Use ``remove_isolated_nodes=True`` to reduce clutter
2. Set ``alphalevel=0.1`` or lower for edge transparency
3. Disable labels: ``labels=False, node_labels=False``
4. Consider sampling: visualize only high-degree nodes or a random subset

Summary
-------

Key visualization capabilities in py3plex:

* **Three preset modes** (minimal, balanced, dense) for different network scales
* **Flexible layouts** (circular, rectangular) for different structures
* **Auto-scaling** features adapt to network properties
* **Matrix visualizations** show supra-adjacency structure
* **Layer-specific views** enable detailed exploration

Choose visualization settings based on your network size and purpose. For quick exploration, use defaults. For publications, use dense mode with custom colors and layouts.

**Next chapter:** Core algorithms for multilayer analysis (community detection, centrality, dynamics)
