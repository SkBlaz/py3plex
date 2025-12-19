Core Concepts and Architecture
==============================

This guide explains the fundamental concepts and architectural design of py3plex, with an emphasis on how multilayer data are represented internally and how node-layer pairs flow through the library.

What are Multilayer Networks?
-----------------------------

A multilayer network is a graph where nodes can participate in multiple contexts (layers), and edges may connect node instances within the same layer (intra-layer) or across layers (inter-layer). Each **node-layer pair** is treated as a distinct entity; the same node label may appear in several layers, but each occurrence is independent unless coupled by an inter-layer edge.

Key Characteristics
~~~~~~~~~~~~~~~~~~~

**Traditional (Single-Layer) Networks**

* One node type
* One edge type
* Single interaction context

**Multilayer Networks**

* Multiple node types (per-layer semantics)
* Multiple edge types
* Multiple layers of interaction
* Both inter-layer and intra-layer connections

Types of Multilayer Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Multiplex Networks**
  Multiple layers with the same set of nodes but different edge semantics.

  *Example:* Social network with friendship, colleague, and family layers.

**Heterogeneous Networks (HINs)**
  Different node types, each with type-specific relationships.

  *Example:* Academic network with authors, papers, and venues.

**Temporal Networks**
  Networks that evolve over time, represented as time-sliced layers.

  *Example:* Communication network across different time periods.

**Interdependent Networks**
  Multiple networks where nodes in one network depend on nodes in another.

  *Example:* Power grid and communication network interdependency.

Core Data Structure
-------------------

The ``multi_layer_network`` Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The central data structure in py3plex is the ``multi_layer_network`` class, which provides:

* Layer management: add, remove, and query network layers
* Node and edge operations: efficient addition and retrieval
* NetworkX integration: works directly with NetworkX algorithms that support multigraphs
* Matrix representations: supra-adjacency and layer-specific matrices

Basic Structure
^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network()
    
    # The underlying NetworkX graph (MultiDiGraph or MultiGraph)
    nx_graph = network.core_network
    
    # Layer management
    layers = network.get_layers()  # List of layer names
    layer_map = network.layer_name_map  # Layer name to ID mapping

Internal Representation
^^^^^^^^^^^^^^^^^^^^^^^

py3plex represents multilayer networks using:

1. **Core NetworkX graph:** A ``MultiDiGraph`` or ``MultiGraph`` storing all node-layer pairs and edges
2. **Layer encoding:** Node-layer pairs are encoded as ``node_id---layer_id`` using a delimiter (default: ``---``)
3. **Layer mapping:** Bidirectional mapping between layer names and integer IDs for compact matrix construction
4. **Attributes:** Node and edge attributes stored on the underlying NetworkX graph
5. **Node ordering:** Methods that return matrices follow the node-layer ordering from ``network.get_nodes()``

Example:

.. code-block:: python

    # Node 'A' in 'layer1' is stored internally as 'A---layer1'
    network.add_nodes([('A', 'layer1')])
    
    # Access the encoded node
    encoded_nodes = list(network.core_network.nodes())
    # ['A---layer1']

Network Construction
--------------------

Creating Networks from Scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nodes and edges are specified as ``(node_id, layer_name)`` tuples so each occurrence of a node is bound to a specific layer.

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    # Add layers explicitly (optional)
    network.add_layer('social')
    network.add_layer('professional')
    
    # Add nodes (layer is created if it doesn't exist)
    network.add_nodes([
        ('Alice', 'social'),
        ('Bob', 'social'),
        ('Alice', 'professional'),
        ('Bob', 'professional')
    ])
    
    # Add edges within layers (intra-layer)
    network.add_edges([
        [('Alice', 'social'), ('Bob', 'social'), 1.0]
    ])
    
    # Add edges between layers (inter-layer)
    network.add_edges([
        [('Alice', 'social'), ('Alice', 'professional'), 1.0]
    ])

Loading from Files
~~~~~~~~~~~~~~~~~~

py3plex supports multiple input formats; the loader creates layers on demand when they are discovered in the input.

.. code-block:: python

    # From edge list
    network = multinet.multi_layer_network().load_network(
        "data.edgelist",
        input_type="edgelist",
        directed=False
    )
    
    # From multilayer edge list (source, target, layer)
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist",
        input_type="multiedgelist"
    )
    
    # From GraphML
    network = multinet.multi_layer_network().load_network(
        "data.graphml",
        input_type="graphml"
    )

Network Operations
------------------

Querying Network Elements
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all nodes
    nodes = network.get_nodes(data=True)  # yields (node, data_dict)
    
    # Get nodes in a specific layer
    layer_nodes = network.get_nodes(layer='layer1')
    
    # Get all edges
    edges = network.get_edges(data=True)
    
    # Get neighbors of a node in a layer
    neighbors = network.get_neighbors(('Alice', 'social'))
    
    # Get all layers (sorted by internal ID)
    layers = network.get_layers()

Network Transformations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Aggregate multiple layers into one
    aggregated = network.aggregate_layers(['layer1', 'layer2'], 'combined')
    
    # Extract a single layer as a NetworkX graph
    layer_graph = network.get_layer_subgraph('layer1')
    
    # Project to a node type (for heterogeneous networks)
    projected = network.project_to_node_type('author')

Matrix Representations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get supra-adjacency matrix (all layers stacked)
    supra_adj = network.get_supra_adjacency_matrix()
    # Row/column ordering matches network.get_nodes() (node-layer pairs)
    
    # Get adjacency matrix for a single layer
    layer_adj = network.get_adjacency_matrix(layer='layer1')
    
    # Get inter-layer coupling matrix
    coupling = network.get_coupling_matrix()

Architectural Design
--------------------

Modular Structure
~~~~~~~~~~~~~~~~~

py3plex follows a modular architecture:

.. code-block:: text

    py3plex/
    ├── core/                   # Core data structures
    │   ├── multinet.py         # multi_layer_network class
    │   ├── parsers.py          # I/O for various formats
    │   └── converters.py       # Format conversion utilities
    ├── algorithms/             # Network algorithms
    │   ├── community_detection/
    │   ├── statistics/
    │   ├── multilayer_algorithms/
    │   └── general/
    ├── visualization/          # Plotting and rendering
    │   ├── multilayer.py
    │   ├── drawing_machinery.py
    │   └── layout_algorithms.py
    └── wrappers/               # High-level interfaces

Design Principles
~~~~~~~~~~~~~~~~~

**1. NetworkX Compatibility**
  All operations are compatible with NetworkX, allowing use of NetworkX algorithms.

**2. Lazy Evaluation**
  Expensive operations (e.g., matrix construction) are computed on demand.

**3. Graceful Degradation**
  Optional features fail gracefully if dependencies are missing.

**4. Extensibility**
  Easy to extend with custom algorithms and visualizations.

Data Flow
~~~~~~~~~

.. code-block:: text

    Input Data (files, NetworkX, edge lists)
        ↓
    Parsers → multi_layer_network object
        ↓
    Network Operations (add, remove, query)
        ↓
    ├→ Algorithms → Metrics, Communities, Centrality
    ├→ Visualization → Plots, Layouts
    └→ Export → Files, Matrices, NetworkX

Integration with NetworkX
--------------------------

Full NetworkX Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``core_network`` attribute is a standard NetworkX graph that stores encoded node-layer pairs, so any NetworkX algorithm that supports multigraphs works directly. Algorithms that expect simple graphs may require preprocessing (e.g., edge aggregation or conversion to a simple graph):

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create py3plex network
    mlnet = multinet.multi_layer_network()
    mlnet.add_edges([
        [('A', 'L1'), ('B', 'L1'), 1]
    ])
    
    # Access underlying NetworkX graph
    G = mlnet.core_network
    # Encoded nodes appear as strings (e.g., 'A---L1')
    
    # Use any NetworkX function
    betweenness = nx.betweenness_centrality(G)
    communities = nx.community.louvain_communities(G)
    diameter = nx.diameter(G) if nx.is_connected(G) else float('inf')

Converting to/from NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # From NetworkX to py3plex
    import networkx as nx
    from py3plex.core import multinet
    
    G = nx.karate_club_graph()
    mlnet = multinet.multi_layer_network()
    mlnet.load_network_from_networkx(G)
    
    # From py3plex to NetworkX
    G_export = mlnet.core_network

Supra-Adjacency Matrix
----------------------

Mathematical Definition
~~~~~~~~~~~~~~~~~~~~~~~

The **supra-adjacency matrix** is a block matrix representation of a multilayer network where rows and columns correspond to node-layer pairs. If layer :math:`\alpha` has :math:`n_\alpha` nodes, the overall matrix has size :math:`(\sum_\alpha n_\alpha) \times (\sum_\alpha n_\alpha)`. Blocks are ordered by the layer mapping in ``network.layer_name_map`` (the same ordering returned by ``network.get_layers()``):

.. math::

    \mathbf{S} = \begin{bmatrix}
    A_1 & C_{12} & \cdots & C_{1L} \\
    C_{21} & A_2 & \cdots & C_{2L} \\
    \vdots & \vdots & \ddots & \vdots \\
    C_{L1} & C_{L2} & \cdots & A_L
    \end{bmatrix}

Where:

* :math:`A_\alpha` is the :math:`n_\alpha \times n_\alpha` adjacency matrix of layer :math:`\alpha`
* :math:`C_{\alpha\beta}` is the :math:`n_\alpha \times n_\beta` coupling matrix between layers :math:`\alpha` and :math:`\beta`

Construction in py3plex
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    # ... add nodes and edges ...
    
    # Get supra-adjacency matrix (sparse by default)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Shape: (total_node_layer_pairs, total_node_layer_pairs)
    # where total_node_layer_pairs = sum of nodes in each layer (node repeated per layer)
    print(f"Supra-adjacency shape: {supra_adj.shape}")

Layer-Specific Operations
--------------------------

Working with Individual Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get layer as NetworkX subgraph
    layer_graph = network.get_layer_subgraph('layer1')
    
    # Compute layer-specific metrics
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    density = mls.layer_density(network, 'layer1')
    clustering = nx.average_clustering(layer_graph)

Inter-Layer Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Inter-layer degree correlation
    correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')
    
    # Edge overlap between layers
    overlap = mls.edge_overlap(network, 'layer1', 'layer2')
    
    # Layer similarity
    similarity = mls.layer_similarity(network, 'layer1', 'layer2')

Extensibility
-------------

Adding Custom Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~

Extend py3plex by adding custom algorithms:

.. code-block:: python

    from py3plex.core import multinet
    import networkx as nx
    
    def my_custom_centrality(ml_network):
        """Compute custom centrality for multilayer network."""
        G = ml_network.core_network
        
        # Implement your algorithm
        centrality = {}
        for node in G.nodes():
            # Custom computation
            centrality[node] = compute_score(node, G)
        
        return centrality

Custom Visualization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import drawing_machinery as dm
    import matplotlib.pyplot as plt
    
    def custom_plot(ml_network):
        """Create custom visualization."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Use drawing machinery primitives
        pos = dm.compute_layout(ml_network.core_network, 'force')
        dm.draw_nodes(ax, ml_network.core_network, pos)
        dm.draw_edges(ax, ml_network.core_network, pos)
        
        plt.show()

Next Steps
----------

* :doc:`getting_started/tutorial_10min` - Practical usage examples
* :doc:`tutorials/multilayer_centrality` - Centrality measures
* :doc:`tutorials/multilayer_modularity` - Community detection
* :doc:`algorithm_guide` - Algorithm selection guide
* :doc:`architecture` - Detailed architecture documentation
