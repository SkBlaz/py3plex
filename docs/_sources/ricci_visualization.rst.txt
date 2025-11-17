Ricci-Flow-Based Visualization
================================

Overview
--------

py3plex provides advanced visualization capabilities leveraging **Ricci flow** to create informative layouts for multilayer networks. Ricci flow transforms edge weights based on the geometric curvature of the network, which helps reveal community structure, bottlenecks, and hierarchical organization.

This page documents the Ricci-flow-based visualization utilities that build upon the :doc:`ricci_curvature` functionality.

What is Ricci-Flow-Based Visualization?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Traditional network layouts (spring, spectral, etc.) rely on heuristics to position nodes. Ricci-flow-based layouts use a more principled geometric approach:

1. **Ricci flow** adjusts edge weights based on their curvature
2. These adjusted weights reflect the "geometric distance" between nodes
3. Layouts computed from these weights naturally emphasize communities and structural features

The result is visualizations where:

* **Communities** appear as tight, well-separated clusters
* **Bottleneck edges** (negative curvature) are visually emphasized
* **Hierarchical structure** becomes more apparent

Three Visualization Styles
~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex provides three complementary visualization styles for multilayer networks:

1. **Core (Aggregated) Visualization**: Shows the combined structure across all layers
2. **Per-Layer Visualization**: Shows each layer individually with shared or independent coordinates
3. **Supra-Graph Visualization**: Shows the full multilayer structure including inter-layer connections

Installation Requirements
--------------------------

Ricci-flow-based visualizations require the optional **GraphRicciCurvature** library:

.. code-block:: bash

    pip install GraphRicciCurvature

If GraphRicciCurvature is not installed, py3plex will raise a clear error message with installation instructions.

Basic Usage
-----------

Core (Aggregated) Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest use case is visualizing the aggregated network after Ricci flow:

.. code-block:: python

    from py3plex.core import multinet
    import matplotlib.pyplot as plt

    # Load or create a multilayer network
    net = multinet.multi_layer_network().load_network(
        "path/to/multilayer_network.txt",
        input_type="multiedgelist",
        directed=False,
    )

    # Visualize core network using Ricci flow
    # (Ricci flow is computed automatically if not already done)
    fig, ax, positions = net.visualize_ricci_core(
        alpha=0.5,          # Ollivier-Ricci parameter
        iterations=10,      # Number of flow iterations
        layout_type="mds",  # Layout algorithm
        dim=2,              # 2D layout
    )

    plt.show()

This creates a 2D visualization where:

* **Node colors** indicate layer participation (how many layers the node appears in)
* **Edge colors** indicate curvature (red = negative/bottleneck, blue = positive/community)
* **Edge widths** reflect post-flow weights (thicker = stronger connection)

Per-Layer Visualization
~~~~~~~~~~~~~~~~~~~~~~~~

To compare individual layers side-by-side:

.. code-block:: python

    # Visualize layers in a grid with shared coordinate system
    fig, layer_positions = net.visualize_ricci_layers(
        layers=None,           # None means all layers
        alpha=0.5,
        iterations=10,
        layout_type="mds",
        share_layout=True,     # Use shared coordinates for comparison
        arrangement="grid",    # Display in grid of subplots
    )

    plt.show()

With ``share_layout=True``, nodes appear at the same positions across all layer plots, making it easy to see how edge structure differs between layers.

To use independent layouts for each layer:

.. code-block:: python

    # Independent layouts - each layer optimized separately
    fig, layer_positions = net.visualize_ricci_layers(
        share_layout=False,
        arrangement="grid",
    )

    plt.show()

Supra-Graph Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~

To visualize the full multilayer structure including inter-layer coupling:

.. code-block:: python

    # 2D supra-graph visualization
    fig, ax, positions = net.visualize_ricci_supra(
        alpha=0.5,
        iterations=10,
        layout_type="mds",
        dim=2,
        node_color_by="layer",     # Color nodes by layer
        edge_color_by="curvature",  # Color edges by curvature
    )

    plt.show()

For 3D visualization with layer separation:

.. code-block:: python

    # 3D supra-graph with layers separated along z-axis
    fig, ax, positions = net.visualize_ricci_supra(
        dim=3,
        layer_separation=1.0,  # Separate layers by this distance
        layout_type="spring",
    )

    plt.show()

Advanced Examples
-----------------

Customizing Node and Edge Appearance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can customize various visual properties:

.. code-block:: python

    fig, ax, positions = net.visualize_ricci_core(
        alpha=0.5,
        iterations=15,
        
        # Node appearance
        node_color_by="curvature",  # Options: "layer_overlap", "degree", "curvature"
        node_size=150,              # Fixed size, or "degree" for degree-based sizing
        cmap_nodes="plasma",        # Colormap for nodes
        
        # Edge appearance
        edge_color_by="weight",     # Options: "curvature", "weight"
        edge_width_scale=3.0,       # Scale factor for edge widths
        cmap_edges="coolwarm",      # Colormap for edges
        
        # Display options
        show_colorbar=True,
        figsize=(12, 10),
    )

Using Different Layout Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Three layout algorithms are available:

.. code-block:: python

    # MDS (Multidimensional Scaling) - recommended for distance-based layouts
    # Good for: Preserving global structure, community visualization
    fig1, ax1, pos1 = net.visualize_ricci_core(
        layout_type="mds",
        use_geodesic_distances=True,  # Use shortest path distances
    )

    # Spring (Force-Directed) - good for emphasizing local structure
    # Good for: Small to medium networks, emphasizing edge weights
    fig2, ax2, pos2 = net.visualize_ricci_core(
        layout_type="spring",
        iterations=15,
        k=0.3,  # Spring constant (passed to nx.spring_layout)
    )

    # Spectral - based on graph Laplacian eigenvectors
    # Good for: Fast computation, balanced layouts
    fig3, ax3, pos3 = net.visualize_ricci_core(
        layout_type="spectral",
    )

Pre-Computing Ricci Flow
~~~~~~~~~~~~~~~~~~~~~~~~~

For more control, you can compute Ricci flow separately:

.. code-block:: python

    # Step 1: Compute Ricci flow explicitly
    result = net.compute_ollivier_ricci_flow(
        mode="core",
        alpha=0.5,
        iterations=20,
        method="OTD",  # Optimal Transport Distance
        inplace=True,
    )

    # Step 2: Visualize with pre-computed flow
    fig, ax, positions = net.visualize_ricci_core(
        compute_if_missing=False,  # Don't recompute
        layout_type="mds",
    )

This approach is useful when:

* You want to experiment with different iterations counts
* You need to analyze curvature values before visualizing
* You're visualizing the same network multiple times

Comparing Multiple Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Visualize specific layers for comparison:

.. code-block:: python

    # Compare two specific layers
    fig, layer_pos = net.visualize_ricci_layers(
        layers=["social", "biological"],  # Only these layers
        share_layout=True,
        arrangement="grid",
        iterations=15,
    )

    # Access positions for individual layers
    social_positions = layer_pos["social"]
    biological_positions = layer_pos["biological"]

Analyzing Supra-Graph Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Visualize and analyze the supra-graph:

.. code-block:: python

    import numpy as np

    # Visualize supra-graph
    fig, ax, positions = net.visualize_ricci_supra(
        alpha=0.5,
        iterations=10,
        interlayer_alpha=0.2,  # Transparency for inter-layer edges
    )

    # Extract node positions by layer
    layer1_nodes = {node: pos for node, pos in positions.items()
                    if isinstance(node, tuple) and node[1] == "layer1"}
    
    layer2_nodes = {node: pos for node, pos in positions.items()
                    if isinstance(node, tuple) and node[1] == "layer2"}

    print(f"Layer 1 has {len(layer1_nodes)} nodes")
    print(f"Layer 2 has {len(layer2_nodes)} nodes")

API Reference
-------------

visualize_ricci_core()
~~~~~~~~~~~~~~~~~~~~~~

Visualize the aggregated core network using Ricci-flow-based layout.

**Signature:**

.. code-block:: python

    def visualize_ricci_core(
        self,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        dim: int = 2,
        curvature_attr: str = "ricciCurvature",
        weight_attr: str = "weight",
        node_color_by: str = "layer_overlap",
        edge_color_by: str = "curvature",
        node_size: Union[int, str] = 100,
        edge_width_scale: float = 2.0,
        figsize: Tuple[float, float] = (10, 8),
        ax: Optional[plt.Axes] = None,
        cmap_nodes: str = "viridis",
        cmap_edges: str = "RdBu_r",
        show_colorbar: bool = True,
        compute_if_missing: bool = True,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes, Dict[Any, np.ndarray]]:

**Key Parameters:**

* ``alpha``: Ollivier-Ricci parameter (0 to 1). Default: 0.5.
* ``iterations``: Number of Ricci flow iterations. Default: 10.
* ``layout_type``: Layout algorithm - "mds", "spring", or "spectral". Default: "mds".
* ``dim``: Layout dimensionality (2 or 3). Default: 2.
* ``node_color_by``: Node coloring scheme - "layer_overlap", "degree", or "curvature". Default: "layer_overlap".
* ``edge_color_by``: Edge coloring scheme - "curvature" or "weight". Default: "curvature".
* ``compute_if_missing``: Automatically compute Ricci flow if not done. Default: True.

**Returns:**

Tuple of ``(figure, axes, positions_dict)`` where positions_dict maps nodes to coordinate arrays.

visualize_ricci_layers()
~~~~~~~~~~~~~~~~~~~~~~~~~

Visualize individual layers using Ricci-flow-based layouts.

**Signature:**

.. code-block:: python

    def visualize_ricci_layers(
        self,
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        dim: int = 2,
        arrangement: str = "grid",
        share_layout: bool = True,
        figsize: Tuple[float, float] = (12, 8),
        node_size: int = 100,
        edge_width_scale: float = 2.0,
        compute_if_missing: bool = True,
        **kwargs
    ) -> Tuple[plt.Figure, Dict[Any, Dict[Any, np.ndarray]]]:

**Key Parameters:**

* ``layers``: List of layer IDs to visualize. If None, uses all layers. Default: None.
* ``share_layout``: Use shared coordinates across layers. Default: True.
* ``arrangement``: How to arrange layers - "grid" or "stacked". Default: "grid".

**Returns:**

Tuple of ``(figure, layer_positions_dict)`` where layer_positions_dict maps layer IDs to position dictionaries.

visualize_ricci_supra()
~~~~~~~~~~~~~~~~~~~~~~~~

Visualize the full supra-graph using Ricci-flow-based layout.

**Signature:**

.. code-block:: python

    def visualize_ricci_supra(
        self,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        dim: int = 2,
        layer_separation: Optional[float] = None,
        node_color_by: str = "layer",
        edge_color_by: str = "curvature",
        figsize: Tuple[float, float] = (12, 10),
        interlayer_alpha: float = 0.3,
        compute_if_missing: bool = True,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes, Dict[Any, np.ndarray]]:

**Key Parameters:**

* ``layer_separation``: If not None and dim=3, separates layers along z-axis. Default: None.
* ``node_color_by``: Node coloring - "layer" or "curvature". Default: "layer".
* ``interlayer_alpha``: Transparency for inter-layer edges. Default: 0.3.

**Returns:**

Tuple of ``(figure, axes, positions_dict)`` for the supra-graph.

Best Practices
--------------

Choosing Parameters
~~~~~~~~~~~~~~~~~~~

**Alpha (Ollivier-Ricci parameter):**

* ``alpha=0.5``: Standard setting, good starting point
* ``alpha < 0.5``: Emphasizes local neighborhood structure
* ``alpha > 0.5``: Emphasizes global connectivity
* ``alpha=0``: Pure neighbor-based measure (faster but less smooth)

**Iterations:**

* ``iterations=5-10``: Quick preview
* ``iterations=10-20``: Standard analysis
* ``iterations=30-50``: High-quality results for publication
* More iterations = stronger geometric effects but longer computation

**Layout Type:**

* ``layout_type="mds"``: Best for preserving distances, good for community structure
* ``layout_type="spring"``: Best for small networks, emphasizes edge weights
* ``layout_type="spectral"``: Fastest, good for balanced layouts

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ricci flow and visualization can be computationally expensive for large networks:

* **Start small**: Test on subgraphs or smaller networks first
* **Reduce iterations**: Use 5-10 iterations for initial exploration
* **Use mode="layers"**: If you only need per-layer analysis, avoid computing the full core
* **Parallel computation**: Pass ``backend_kwargs={"proc": 4}`` to use multiple CPU cores

Example with parallel computation:

.. code-block:: python

    # Use 4 CPU cores for Ricci flow computation
    fig, ax, pos = net.visualize_ricci_core(
        alpha=0.5,
        iterations=15,
        backend_kwargs={"proc": 4}
    )

Interpretation Guide
~~~~~~~~~~~~~~~~~~~~

**Node Colors (when node_color_by="layer_overlap"):**

* Brighter colors = node appears in more layers
* Darker colors = node appears in fewer layers
* Helps identify cross-layer hubs vs. layer-specific nodes

**Edge Colors (when edge_color_by="curvature"):**

* **Blue**: Positive curvature → edges within communities
* **Red**: Negative curvature → edges between communities (bottlenecks)
* **White/neutral**: Near-zero curvature → transitional regions

**Edge Widths:**

* Thicker edges = higher weight after Ricci flow
* Thinner edges = lower weight after Ricci flow
* Width reflects "geometric strength" of the connection

Common Workflows
----------------

Workflow 1: Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use Ricci flow visualization to identify and validate communities:

.. code-block:: python

    # Step 1: Visualize with Ricci flow
    fig, ax, pos = net.visualize_ricci_core(
        iterations=20,
        edge_color_by="curvature",
    )

    # Step 2: Identify bottleneck edges (red edges)
    # These likely separate communities

    # Step 3: Run community detection on flow-enhanced network
    net.compute_ollivier_ricci_flow(mode="core", iterations=20, inplace=True)
    
    # Use your preferred community detection algorithm
    # Communities should be more separable after flow

Workflow 2: Layer Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare structural differences across layers:

.. code-block:: python

    # Visualize layers with shared layout
    fig, layer_pos = net.visualize_ricci_layers(
        share_layout=True,
        arrangement="grid",
        iterations=15,
    )

    # Analyze differences:
    # - Which edges appear in which layers?
    # - How does curvature differ across layers?
    # - Are communities consistent across layers?

Workflow 3: Hierarchical Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use 3D supra-graph to reveal hierarchical structure:

.. code-block:: python

    # 3D visualization with layer separation
    fig, ax, pos = net.visualize_ricci_supra(
        dim=3,
        layer_separation=2.0,
        iterations=15,
        layout_type="spring",
    )

    # Interpret:
    # - Vertical separation shows layer structure
    # - Horizontal clustering shows communities
    # - Inter-layer edges show coupling strength

Troubleshooting
---------------

Issue: Visualization is too cluttered
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solutions:**

1. Reduce node/edge counts by filtering
2. Increase ``figsize`` parameter
3. Reduce ``node_size`` or ``edge_width_scale``
4. For supra-graphs, increase ``interlayer_alpha`` to make inter-layer edges less visible

Issue: Layout looks random or unstructured
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solutions:**

1. Increase ``iterations`` (try 20-30)
2. Try different ``layout_type`` (e.g., switch from spring to mds)
3. Increase ``alpha`` to emphasize global structure
4. Check that your network has meaningful structure to visualize

Issue: Computation is too slow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solutions:**

1. Reduce ``iterations`` to 5-10
2. Use ``layout_type="spectral"`` (fastest)
3. Reduce ``alpha`` (lower values are faster)
4. Use parallel computation: ``backend_kwargs={"proc": 4}``
5. Visualize a subgraph instead of the full network

Issue: GraphRicciCurvature import error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:**

Install the optional dependency:

.. code-block:: bash

    pip install GraphRicciCurvature

If installation fails, you may need to install dependencies first:

.. code-block:: bash

    pip install networkit numpy scipy

See Also
--------

* :doc:`ricci_curvature` - Ollivier-Ricci curvature and Ricci flow fundamentals
* :doc:`community_detection` - Community detection algorithms
* :doc:`visualization_guide` - General visualization guide
* :doc:`multilayer_concepts` - Understanding multilayer networks
* :doc:`supra` - Supra-adjacency matrix representation

References
----------

* Ni, C. C., Lin, Y. Y., Luo, F., & Gao, J. (2019). Community detection on networks with Ricci flow. *Scientific Reports*, 9(1), 9984.

* Ni, C. C., Lin, Y. Y., Gao, J., Gu, X. D., & Saucan, E. (2015). Ricci curvature of the Internet topology. *2015 IEEE Conference on Computer Communications (INFOCOM)*, 2758-2766.

* GraphRicciCurvature library: https://github.com/saibalmars/GraphRicciCurvature
