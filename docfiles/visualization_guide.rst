Visualization Guide
===================

This guide covers multilayer network visualization in Py3plex, including preset modes,
customization options, and best practices for different network scales.

.. contents:: Table of Contents
   :local:
   :depth: 2

Quick Start
-----------

Basic Multilayer Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import draw_multilayer_default
    import matplotlib.pyplot as plt
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Visualize with defaults
    draw_multilayer_default(
        network.get_layers(),
        display=True,
        labels=True
    )

Preset Visualization Modes
---------------------------

Py3plex provides three preset modes optimized for different network scales and use cases.

Minimal Mode (Large Networks >1000 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimized for networks with many nodes where detail isn't critical.

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Minimal preset for large networks
    draw_multilayer_default(
        network.get_layers(),
        # Node settings
        node_size=5,              # Small nodes
        labels=False,             # No node labels (too cluttered)
        node_labels=False,        # No node IDs
        
        # Edge settings
        edge_size=0.5,            # Thin edges
        alphalevel=0.3,           # Transparent edges (reduce clutter)
        
        # Layout
        background_shape="circle",  # Circular layout
        
        # Display
        display=True,
        remove_isolated_nodes=True  # Clean up isolated nodes
    )

**Use cases:**
- Large social networks (>1000 nodes)
- Overview visualizations
- Pattern detection at macro level
- Network topology understanding

**Advantages:**
- Fast rendering
- Reduced visual clutter
- Shows overall structure
- Works with many nodes

Balanced Mode (Medium Networks 100-1000 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default settings that work well for most networks. Good balance between detail and clarity.

.. code-block:: python

    # Balanced preset (this is the default)
    draw_multilayer_default(
        network.get_layers(),
        # Node settings
        node_size=10,             # Medium nodes
        labels=True,              # Show layer labels
        node_labels=False,        # Node IDs hidden by default
        
        # Edge settings
        edge_size=1.0,            # Normal edge width
        alphalevel=0.13,          # Semi-transparent edges
        
        # Layout
        background_shape="circle",  # Circular layout
        networks_color="rainbow",   # Auto-assign colors
        
        # Display
        display=True
    )

**Use cases:**
- Most research networks
- Exploratory data analysis
- Publication figures (moderate detail)
- Interactive exploration

**Advantages:**
- Good readability
- Reasonable performance
- Balanced aesthetics
- Suitable for most publications

Dense Mode (Small Networks <100 nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Maximum detail for small networks where every node and edge matters.

.. code-block:: python

    # Dense preset for small, detailed networks
    draw_multilayer_default(
        network.get_layers(),
        # Node settings
        node_size=20,             # Large nodes
        labels=True,              # Show all labels
        node_labels=True,         # Show node IDs
        node_font_size=10,        # Readable font
        scale_by_size=True,       # Scale by degree
        
        # Edge settings
        edge_size=2.0,            # Thick edges
        alphalevel=0.8,           # Mostly opaque
        arrowsize=0.5,            # Visible arrows (if directed)
        
        # Layout
        background_shape="rectangle",  # Rectangular layout
        networks_color="rainbow",
        
        # Display
        display=True
    )

**Use cases:**
- Small case studies
- Detailed analysis
- Node-level examination
- High-quality publication figures

**Advantages:**
- Maximum detail
- Clear node identification
- Edge weights visible
- Professional appearance

Layout Options
--------------

Py3plex supports multiple layout algorithms for different network structures.

Circular Layout (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Arranges layers in a circle. Good for showing inter-layer connections.

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        background_shape="circle",
        rectanglex=1.0,  # Circle radius x
        rectangley=1.0   # Circle radius y
    )

**Best for:**
- 2-10 layers
- Symmetric layer interactions
- Publication figures

Rectangular Layout
~~~~~~~~~~~~~~~~~~

Arranges layers in a grid. Good for many layers or hierarchical structures.

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        background_shape="rectangle",
        rectanglex=2.0,  # Width of layout
        rectangley=1.0   # Height of layout
    )

**Best for:**
- Many layers (>10)
- Hierarchical networks
- Time-series data
- Wide figures

Auto-Scaling Features
---------------------

Py3plex automatically adjusts visualization parameters based on network size.

Automatic Node Sizing
~~~~~~~~~~~~~~~~~~~~~

Scale node sizes by degree (number of connections):

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        scale_by_size=True,    # Enable auto-scaling
        node_size=10           # Base size (scaled up/down by degree)
    )

**How it works:**

- Nodes with more connections → larger size
- Isolated nodes → smaller size
- Hub nodes are easily identifiable

Automatic Color Assignment
~~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex uses colorblind-safe palettes by default:

.. code-block:: python

    # Rainbow colors (automatic assignment)
    draw_multilayer_default(
        network.get_layers(),
        networks_color="rainbow"  # Auto-assign distinct colors
    )
    
    # Custom palette
    draw_multilayer_default(
        network.get_layers(),
        networks_color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"]
    )

**Available palettes** (from ``py3plex.config``):

- ``colorblind_safe``: 8 colors safe for colorblind viewers
- ``wong``: 7-color palette (scientifically validated)
- ``tol_bright``: 7 bright colors
- ``rainbow``: Automatic generation

Automatic Layout Adjustment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Layout parameters auto-adjust to network size:

.. code-block:: python

    # For small networks, layout is compact
    small_network = multinet.multi_layer_network()
    # ... load 50-node network ...
    draw_multilayer_default(small_network.get_layers())  # Compact layout
    
    # For large networks, layout expands
    large_network = multinet.multi_layer_network()
    # ... load 1000-node network ...
    draw_multilayer_default(large_network.get_layers())  # Expanded layout

Customization Options
---------------------

Complete Parameter Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    draw_multilayer_default(
        network_list,             # List of layer subgraphs
        
        # Display control
        display=True,             # Show plot immediately
        axis=None,                # Matplotlib axis (None = create new)
        
        # Node appearance
        node_size=10,             # Base node size
        scale_by_size=False,      # Scale by degree?
        node_labels=False,        # Show node IDs?
        node_font_size=5,         # Font size for node labels
        
        # Edge appearance
        edge_size=1.0,            # Edge thickness
        alphalevel=0.13,          # Edge transparency (0=invisible, 1=opaque)
        arrowsize=0.5,            # Arrow size (for directed graphs)
        
        # Layout
        background_shape="circle",  # "circle" or "rectangle"
        rectanglex=1.0,           # Layout width/radius
        rectangley=1.0,           # Layout height/radius
        
        # Colors
        networks_color="rainbow", # "rainbow" or list of colors
        background_color="rainbow",  # Background color scheme
        
        # Labels
        labels=True,              # Show layer labels?
        label_position=1.0,       # Label distance from center
        
        # Cleanup
        remove_isolated_nodes=False,  # Remove disconnected nodes?
        
        # Debugging
        verbose=False             # Print debug info?
    )

Layer-Specific Customization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Customize individual layers:

.. code-block:: python

    import matplotlib.pyplot as plt
    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Get layers
    layers = network.get_layers()
    
    # Modify specific layer (e.g., highlight layer 0)
    for node in layers[0].nodes():
        layers[0].nodes[node]['color'] = 'red'
        layers[0].nodes[node]['size'] = 20
    
    # Visualize with custom layer
    draw_multilayer_default(layers, display=True)

Color-Coding by Community
~~~~~~~~~~~~~~~~~~~~~~~~~~

Color nodes by community membership:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    
    # Detect communities
    communities = community_louvain.best_partition(network.core_network)
    
    # Assign colors
    num_communities = len(set(communities.values()))
    colors = cm.rainbow([i/num_communities for i in range(num_communities)])
    
    # Apply to network
    for node, comm_id in communities.items():
        network.core_network.nodes[node]['color'] = colors[comm_id]
    
    # Visualize
    draw_multilayer_default(network.get_layers(), display=True)

Exporting Visualizations
-------------------------

Save to File
~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Draw network
    draw_multilayer_default(
        network.get_layers(),
        display=False,
        axis=ax
    )
    
    # Customize and save
    plt.title("Multilayer Network Visualization")
    plt.savefig('network.png', dpi=300, bbox_inches='tight')
    plt.savefig('network.pdf', bbox_inches='tight')  # Vector format
    print("Visualization saved to network.png and network.pdf")

High-Quality Publications
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Use publication settings
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['figure.dpi'] = 300
    
    # Large figure for detail
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Dense mode for publications
    draw_multilayer_default(
        network.get_layers(),
        display=False,
        axis=ax,
        node_size=15,
        labels=True,
        alphalevel=0.5,
        background_shape="circle"
    )
    
    plt.title("Figure 1: Multilayer Network Structure", fontsize=12)
    plt.savefig('publication_figure.pdf', bbox_inches='tight')
    plt.savefig('publication_figure.png', dpi=300, bbox_inches='tight')

Interactive Visualizations
--------------------------

Using Plotly (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~

For interactive exploration, use Plotly:

.. code-block:: bash

    # Install optional dependency
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

.. code-block:: python

    # Coming in future version - check documentation for updates
    # from py3plex.visualization.plotly_viz import interactive_multilayer
    # interactive_multilayer(network)

Jupyter Notebook Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Enable inline plotting
    %matplotlib inline
    
    # Or for interactive plots
    %matplotlib notebook
    
    # Visualize
    from py3plex.visualization.multilayer import draw_multilayer_default
    draw_multilayer_default(network.get_layers(), display=True)

Performance Tips
----------------

For Large Networks
~~~~~~~~~~~~~~~~~~

1. **Use minimal mode** (small nodes, no labels)
2. **Sample nodes** if network is too large:

.. code-block:: python

    import random
    
    # Sample 1000 random nodes
    all_nodes = list(network.get_nodes())
    sample_nodes = random.sample(all_nodes, min(1000, len(all_nodes)))
    
    # Create subnetwork
    subnetwork = network.get_subnetwork(sample_nodes)
    
    # Visualize sample
    draw_multilayer_default(subnetwork.get_layers(), display=True)

3. **Remove isolated nodes**:

.. code-block:: python

    draw_multilayer_default(
        network.get_layers(),
        remove_isolated_nodes=True  # Faster rendering
    )

4. **Use lower resolution** for interactive exploration:

.. code-block:: python

    plt.figure(figsize=(8, 6), dpi=100)  # Lower DPI for speed

Troubleshooting
---------------

Visualization Not Showing
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** Plot doesn't appear

**Solutions:**

.. code-block:: python

    # Jupyter notebook: Enable inline plots
    %matplotlib inline
    
    # Python script: Add plt.show()
    draw_multilayer_default(network.get_layers(), display=False)
    plt.show()
    
    # Headless server: Save to file
    import matplotlib
    matplotlib.use('Agg')  # Must be before importing pyplot

Nodes Overlapping
~~~~~~~~~~~~~~~~~

**Issue:** Nodes overlap and are hard to distinguish

**Solutions:**

.. code-block:: python

    # 1. Use smaller node size
    draw_multilayer_default(network.get_layers(), node_size=5)
    
    # 2. Increase layout area
    draw_multilayer_default(
        network.get_layers(),
        rectanglex=2.0,  # Wider layout
        rectangley=2.0   # Taller layout
    )
    
    # 3. Sample nodes
    # (See "Performance Tips" above)

Labels Too Crowded
~~~~~~~~~~~~~~~~~~

**Issue:** Layer labels overlap or are too dense

**Solutions:**

.. code-block:: python

    # 1. Disable labels for large networks
    draw_multilayer_default(network.get_layers(), labels=False)
    
    # 2. Adjust label position
    draw_multilayer_default(
        network.get_layers(),
        labels=True,
        label_position=1.2  # Move labels outward
    )
    
    # 3. Use smaller font
    draw_multilayer_default(
        network.get_layers(),
        node_font_size=3  # Smaller font
    )

Advanced Visualization Modes
-----------------------------

Py3plex provides multiple specialized visualization modes for multilayer networks,
each optimized for different analysis goals. These modes can be accessed through
the unified ``visualize_multilayer_network`` API or by calling individual plot functions.

Overview of Visualization Modes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following visualization modes are available:

1. **diagonal** (default): Layer-centric diagonal layout with inter-layer edges
2. **small_multiples**: Side-by-side comparison of layers in a grid
3. **edge_colored_projection**: Aggregated view with color-coded edges by layer
4. **supra_adjacency_heatmap**: Matrix representation of the multilayer structure
5. **radial_layers**: Concentric circles with layers as rings
6. **ego_multilayer**: Focus on a single node's neighborhood across layers

Unified API
~~~~~~~~~~~

All visualization modes can be accessed through the ``visualize_multilayer_network`` function:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.txt", input_type="multiedgelist")
    
    # Use any visualization mode
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples"  # or any other mode
    )

Small Multiples View
~~~~~~~~~~~~~~~~~~~~

Displays each layer as a separate subplot in a grid layout, making it easy to compare
layer structures side-by-side.

.. image:: ../example_images/multilayer_small_multiples_shared.png
   :width: 600px
   :align: center
   :alt: Small multiples visualization with shared layout

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # Shared layout (nodes appear at same positions across layers)
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=True,       # Same node positions in all layers
        layout="spring",          # Layout algorithm
        node_size=300,
        max_cols=3,               # Maximum columns in grid
        show_layer_titles=True,
        with_labels=True
    )
    
    # Independent layouts (optimized per layer)
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        shared_layout=False,      # Different layouts per layer
        layout="circular"
    )

**Best for:**

- Comparing layer structures
- Identifying layer-specific patterns
- Understanding node presence across layers
- Networks with 2-10 layers

**Parameters:**

- ``shared_layout``: Use same node positions across layers
- ``layout``: "spring", "circular", "random", "kamada_kawai"
- ``max_cols``: Maximum number of columns in grid
- ``show_layer_titles``: Display layer names

Edge-Colored Projection
~~~~~~~~~~~~~~~~~~~~~~~

Projects all layers onto a single 2D graph, using edge colors to indicate layer membership.
Useful for seeing the overall structure while maintaining layer information.

.. image:: ../example_images/multilayer_edge_projection_spring.png
   :width: 600px
   :align: center
   :alt: Edge-colored projection visualization

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # Basic projection
    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="spring",
        node_size=500,
        edge_alpha=0.7,           # Edge transparency
        with_labels=True
    )
    
    # Custom layer colors
    custom_colors = {
        'layer1': 'red',
        'layer2': 'blue',
        'layer3': 'green'
    }
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layer_colors=custom_colors
    )

**Best for:**

- Aggregate network structure
- Comparing edge distributions across layers
- Identifying layer-dominant connections
- Networks where edges don't heavily overlap

**Parameters:**

- ``layout``: Layout algorithm for the aggregated graph
- ``layer_colors``: Dict mapping layer names to colors
- ``edge_alpha``: Transparency level for edges (0-1)
- ``figsize``: Figure dimensions

Supra-Adjacency Heatmap
~~~~~~~~~~~~~~~~~~~~~~~~

Shows the multilayer network as a block matrix where each block represents the
adjacency matrix of one layer. Can optionally include inter-layer connections.

.. image:: ../example_images/multilayer_supra_heatmap_inter.png
   :width: 600px
   :align: center
   :alt: Supra-adjacency heatmap with inter-layer connections

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # Intra-layer only (block-diagonal structure)
    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=False,
        cmap="Blues"
    )
    
    # With inter-layer coupling
    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        include_inter_layer=True,
        inter_layer_weight=0.5,   # Weight for inter-layer edges
        cmap="viridis"
    )

**Best for:**

- Mathematical analysis of structure
- Identifying block patterns
- Understanding coupling between layers
- Spectral analysis preparation

**Parameters:**

- ``include_inter_layer``: Show inter-layer connections
- ``inter_layer_weight``: Default weight for inter-layer edges
- ``cmap``: Matplotlib colormap name
- ``figsize``: Figure dimensions

**Interpretation:**

- Diagonal blocks = intra-layer adjacency matrices
- Off-diagonal blocks = inter-layer connections
- White grid lines = layer boundaries

Radial/Concentric Layers
~~~~~~~~~~~~~~~~~~~~~~~~~

Arranges layers as concentric circles, with nodes positioned on rings and
inter-layer edges shown as radial connections.

.. image:: ../example_images/multilayer_radial_with_inter.png
   :width: 600px
   :align: center
   :alt: Radial layers visualization with concentric circles

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # With inter-layer edges
    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,          # Radius of innermost layer
        radius_step=1.5,          # Distance between layers
        node_size=200,
        draw_inter_layer_edges=True,
        edge_alpha=0.5
    )
    
    # Intra-layer only
    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        draw_inter_layer_edges=False
    )

**Best for:**

- Temporal networks (layers as time steps)
- Hierarchical multilayer networks
- Visualizing node evolution across layers
- Networks with clear layer ordering

**Parameters:**

- ``base_radius``: Radius of innermost ring
- ``radius_step``: Distance between consecutive rings
- ``draw_inter_layer_edges``: Show inter-layer connections
- ``node_size``: Size of nodes

**Interpretation:**

- Each ring = one layer
- Same node appears at same angle on all rings
- Dashed lines = inter-layer connections

Ego-Centric Multilayer View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Focuses on a single node (the "ego") and shows its neighborhood across different layers,
highlighting the ego node's position in each layer context.

.. image:: ../example_images/multilayer_ego_node3_1hop.png
   :width: 600px
   :align: center
   :alt: Ego-centric multilayer visualization showing node neighborhood

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    
    # Basic ego view
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='node_id',            # Node to focus on
        max_depth=1,              # Neighborhood depth (hops)
        layout="spring",
        node_size=100,
        ego_node_size=400         # Highlight ego node
    )
    
    # Specific layers only
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='node_id',
        layers=['layer1', 'layer2'],  # Only these layers
        max_depth=2,              # 2-hop neighborhood
        with_labels=True
    )

**Best for:**

- Analyzing individual node behavior
- Comparing local structure across layers
- Identifying layer-specific influential neighbors
- Understanding node role variations

**Parameters:**

- ``ego``: Node ID to focus on
- ``layers``: Specific layers to visualize (or None for all)
- ``max_depth``: Neighborhood depth in hops
- ``layout``: Layout algorithm per ego graph
- ``ego_node_size``: Size of the highlighted ego node

**Interpretation:**

- Red node = the ego (focal node)
- Blue nodes = neighbors of the ego
- Each subplot = ego's neighborhood in one layer

Example Workflows
~~~~~~~~~~~~~~~~~

Comparing Visualization Modes
++++++++++++++++++++++++++++++

Different modes reveal different aspects of the same network:

.. code-block:: python

    from py3plex.visualization.multilayer import visualize_multilayer_network
    import matplotlib.pyplot as plt
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.txt", input_type="multiedgelist")
    
    # Compare multiple views
    modes = [
        "small_multiples",
        "edge_colored_projection", 
        "supra_adjacency_heatmap",
        "radial_layers"
    ]
    
    for mode in modes:
        fig = visualize_multilayer_network(network, visualization_type=mode)
        fig.savefig(f"network_{mode}.png", dpi=150, bbox_inches='tight')
        plt.close()

Analyzing Specific Nodes
+++++++++++++++++++++++++

Use ego-centric view to understand individual nodes:

.. code-block:: python

    # Find high-degree nodes
    import networkx as nx
    
    # Get aggregated network
    agg_graph = nx.Graph()
    for node in network.get_nodes():
        agg_graph.add_node(node[0])
    for u, v in network.get_edges():
        agg_graph.add_edge(u[0], v[0])
    
    # Get top nodes by degree
    degrees = dict(agg_graph.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:5]
    
    # Visualize each top node's ego network
    for node in top_nodes:
        fig = visualize_multilayer_network(
            network,
            visualization_type="ego_multilayer",
            ego=node,
            max_depth=1
        )
        fig.savefig(f"ego_{node}.png", bbox_inches='tight')
        plt.close()

Choosing the Right Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this guide to select the appropriate visualization mode:

**For structural comparison:**

- Use ``small_multiples`` to compare layer structures side-by-side
- Use ``edge_colored_projection`` to see aggregated structure with layer info

**For mathematical analysis:**

- Use ``supra_adjacency_heatmap`` for matrix-based analysis
- Useful for spectral methods and linear algebra operations

**For temporal or hierarchical networks:**

- Use ``radial_layers`` when layers have natural ordering
- Shows progression or hierarchy clearly

**For local analysis:**

- Use ``ego_multilayer`` to understand individual nodes
- Compare how a node's role varies across layers

**For presentations:**

- Use ``edge_colored_projection`` for clean, simple overview
- Use ``small_multiples`` when detail matters
- Use ``radial_layers`` for visually striking displays

Next Steps
----------

- :doc:`basic_usage_analysis` - Analyze network properties
- :doc:`community_detection` - Detect communities for coloring
- :doc:`performance` - Optimize for large networks
- :doc:`tutorials/csv_loading` - Load data from CSV

For more examples, see the `visualization examples <https://github.com/SkBlaz/py3plex/tree/main/examples>`_ 
in the GitHub repository.
