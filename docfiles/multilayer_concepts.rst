Core Concepts and Architecture
==============================

This guide explains the **fundamental concepts** and **architectural design** of py3plex.

What are Multilayer Networks?
------------------------------

A **multilayer network** is a complex network structure that goes beyond traditional **single-layer graphs** by incorporating **multiple types of relationships**, **node types**, or **interaction contexts**.

Key Characteristics
~~~~~~~~~~~~~~~~~~~

**Traditional (Single-Layer) Networks:**

* **One type** of node
* **One type** of edge
* **Homogeneous** structure

**Multilayer Networks:**

* **Multiple node types**
* **Multiple edge types**
* **Multiple layers** of interaction
* **Inter-layer** and **intra-layer** connections

Types of Multilayer Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Multiplex Networks**
  **Multiple layers** with the **same set of nodes** but **different types of edges**.
  
  *Example:* Social network with **friendship**, **colleague**, and **family** layers.

**Heterogeneous Networks (HINs)**
  **Different node types** with **type-specific relationships**.
  
  *Example:* Academic network with **authors**, **papers**, and **venues**.

**Temporal Networks**
  Networks that **evolve over time**, with **time-sliced layers**.
  
  *Example:* Communication network across **different time periods**.

**Interdependent Networks**
  **Multiple networks** where nodes in one network **depend on nodes** in another.
  
  *Example:* **Power grid** and **communication network** interdependency.

Core Data Structure
-------------------

The ``multi_layer_network`` Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **central data structure** in py3plex is the ``multi_layer_network`` class, which provides:

* **Layer Management:** Add, remove, and query network layers
* **Node and Edge Operations:** Efficient addition and retrieval
* **NetworkX Integration:** Full compatibility with NetworkX algorithms
* **Matrix Representations:** Supra-adjacency and layer-specific matrices

Basic Structure
^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network()
    
    # The underlying NetworkX graph
    nx_graph = network.core_network  # MultiDiGraph or MultiGraph
    
    # Layer management
    layers = network.get_layers()  # List of layer names
    layer_map = network.layer_name_map  # Layer name to ID mapping

Internal Representation
^^^^^^^^^^^^^^^^^^^^^^^

py3plex represents multilayer networks using:

1. **Core NetworkX Graph:** A ``MultiDiGraph`` or ``MultiGraph`` storing all nodes and edges
2. **Layer Encoding:** Nodes are encoded as ``node_id---layer_id`` using a delimiter (default: ``---``)
3. **Layer Mapping:** Bidirectional mapping between layer names and integer IDs
4. **Attributes:** Node and edge attributes stored in the NetworkX graph

Example:

.. code-block:: python

    # Node 'A' in 'layer1' is stored as 'A---layer1'
    network.add_nodes([('A', 'layer1')])
    
    # Access the encoded node
    encoded_nodes = network.core_network.nodes()
    # ['A---layer1']

Network Construction
--------------------

Creating Networks from Scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

py3plex supports multiple input formats:

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
    nodes = network.get_nodes(data=True)
    
    # Get nodes in a specific layer
    layer_nodes = network.get_nodes(layer='layer1')
    
    # Get all edges
    edges = network.get_edges(data=True)
    
    # Get neighbors of a node in a layer
    neighbors = network.get_neighbors('Alice', layer_id='social')
    
    # Get all layers
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``core_network`` attribute is a standard NetworkX graph:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create py3plex network
    mlnet = multinet.multi_layer_network()
    mlnet.add_edges([['A', 'L1', 'B', 'L1', 1]])
    
    # Access underlying NetworkX graph
    G = mlnet.core_network
    
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

The **supra-adjacency matrix** is a block matrix representation of a multilayer network:

.. math::

    \mathbf{S} = \begin{bmatrix}
    A_1 & C_{12} & \cdots & C_{1L} \\
    C_{21} & A_2 & \cdots & C_{2L} \\
    \vdots & \vdots & \ddots & \vdots \\
    C_{L1} & C_{L2} & \cdots & A_L
    \end{bmatrix}

Where:

* :math:`A_\alpha` is the adjacency matrix of layer :math:`\alpha`
* :math:`C_{\alpha\beta}` is the coupling matrix between layers :math:`\alpha` and :math:`\beta`

Construction in py3plex
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    # ... add nodes and edges ...
    
    # Get supra-adjacency matrix (sparse by default)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Shape: (total_nodes, total_nodes)
    # where total_nodes = sum of nodes across all layers
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

* :doc:`basic_usage` - Practical usage examples
* :doc:`tutorials/multilayer_centrality` - Centrality measures
* :doc:`tutorials/multilayer_modularity` - Community detection
* :doc:`algorithm_guide` - Algorithm selection guide
* :doc:`architecture` - Detailed architecture documentation
