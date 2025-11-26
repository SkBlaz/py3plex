py3plex Core Model
==================

This guide explains how py3plex represents multilayer networks internally and how to work with the core data structures.

The ``multi_layer_network`` Class
----------------------------------

The central data structure in py3plex is the ``multi_layer_network`` class, which provides a high-level API for working with multilayer networks while maintaining full compatibility with NetworkX.

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network()
    
    # The underlying NetworkX graph
    nx_graph = network.core_network  # MultiDiGraph or MultiGraph
    
    # Layer management
    layers = network.get_layers()  # List of layer names
    layer_map = network.layer_name_map  # Layer name to ID mapping

Key Components
~~~~~~~~~~~~~~

**1. Core NetworkX Graph**

At its heart, py3plex uses a NetworkX ``MultiDiGraph`` (for directed networks) or ``MultiGraph`` (for undirected networks) to store all nodes and edges.

.. code-block:: python

    # Access the underlying graph
    G = network.core_network
    
    # Use any NetworkX function
    import networkx as nx
    betweenness = nx.betweenness_centrality(G)

**2. Layer Encoding**

Nodes are internally encoded as ``(node_id, layer_id)`` tuples to distinguish the same logical node across different layers.

.. code-block:: python

    # Node 'Alice' in layer 'friends' is stored as ('Alice', 'friends')
    network.add_nodes([('Alice', 'friends')])
    
    # Access all node-layer pairs
    for node_layer_pair in network.get_nodes():
        print(node_layer_pair)  # ('Alice', 'friends'), ('Bob', 'friends'), ...

**3. Layer Mapping**

py3plex maintains bidirectional mappings between layer names and internal layer IDs for efficient lookups.

.. code-block:: python

    # Get layer mapping
    layer_map = network.layer_name_map
    # {'friends': 0, 'colleagues': 1, ...}

**4. Attributes**

Node and edge attributes are stored directly in the underlying NetworkX graph and can be accessed and modified using standard NetworkX patterns.

.. code-block:: python

    # Add node with attributes
    network.core_network.nodes[('Alice', 'friends')]['age'] = 30
    
    # Add edge with attributes
    network.add_edges([
        [('Alice', 'friends'), ('Bob', 'friends'), {'weight': 0.8, 'type': 'close'}]
    ])

Internal Representation
-----------------------

Node-Layer Pairs
~~~~~~~~~~~~~~~~

The key concept in py3plex's internal model is the **node-layer pair**: a tuple ``(node_id, layer_id)`` that uniquely identifies a node in a specific layer.

.. code-block:: python

    # Same logical node, different layers
    alice_friends = ('Alice', 'friends')
    alice_colleagues = ('Alice', 'colleagues')
    
    # These are treated as different nodes internally
    network.add_nodes([alice_friends, alice_colleagues])

This representation allows:

* The same logical entity to appear in multiple layers
* Different attributes per node-layer pair
* Efficient layer-specific operations

Edge Types
~~~~~~~~~~

**Intra-Layer Edges**

Edges connecting nodes within the same layer:

.. code-block:: python

    # Edge within 'friends' layer
    network.add_edges([
        [('Alice', 'friends'), ('Bob', 'friends'), 1.0]
    ])

**Inter-Layer Edges**

Edges connecting nodes across different layers:

.. code-block:: python

    # Connect Alice across layers (identity edge)
    network.add_edges([
        [('Alice', 'friends'), ('Alice', 'colleagues'), 1.0]
    ])
    
    # Connect different nodes across layers
    network.add_edges([
        [('Alice', 'friends'), ('Bob', 'colleagues'), 0.5]
    ])

Supra-Adjacency Matrix
----------------------

The supra-adjacency matrix is a block matrix representation that encodes the entire multilayer network structure.

Mathematical Definition
~~~~~~~~~~~~~~~~~~~~~~~

For a multilayer network with :math:`L` layers, the supra-adjacency matrix :math:`\mathbf{S}` is:

.. math::

    \mathbf{S} = \begin{bmatrix}
    A_1 & C_{12} & \cdots & C_{1L} \\
    C_{21} & A_2 & \cdots & C_{2L} \\
    \vdots & \vdots & \ddots & \vdots \\
    C_{L1} & C_{L2} & \cdots & A_L
    \end{bmatrix}

Where:

* :math:`A_\alpha` is the adjacency matrix of layer :math:`\alpha` (intra-layer connections)
* :math:`C_{\alpha\beta}` is the coupling matrix between layers :math:`\alpha` and :math:`\beta` (inter-layer connections)

Construction
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    # ... add nodes and edges ...
    
    # Get supra-adjacency matrix (sparse by default for efficiency)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Dense version (for small networks only)
    supra_adj_dense = network.get_supra_adjacency_matrix(sparse=False)
    
    # Shape: (total_nodes, total_nodes)
    # where total_nodes = sum of nodes across all layers
    print(f"Shape: {supra_adj.shape}")

Visualization
~~~~~~~~~~~~~

Visualize the supra-adjacency matrix structure:

.. code-block:: python

    from py3plex.core import multinet, random_generators
    import matplotlib.pyplot as plt
    
    # Generate a small multilayer network
    network = random_generators.random_multilayer_ER(
        num_nodes=50, num_layers=3, probability=0.1, directed=False
    )
    
    # Visualize the supra-adjacency matrix
    network.visualize_matrix({"display": True})

The visualization shows the block structure with:

* Diagonal blocks: intra-layer connections
* Off-diagonal blocks: inter-layer connections

Network Construction
--------------------

Creating Networks from Scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Method 1: Add edges directly**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    # Add edges in list format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Bob', 'friends', 'Carol', 'friends', 1.0],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1.0],
    ], input_type="list")

**Method 2: Add nodes and edges separately**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Add nodes explicitly
    network.add_nodes([
        ('Alice', 'friends'),
        ('Bob', 'friends'),
        ('Alice', 'colleagues'),
        ('Bob', 'colleagues')
    ])
    
    # Add edges between existing nodes
    network.add_edges([
        [('Alice', 'friends'), ('Bob', 'friends'), 1.0],
        [('Alice', 'colleagues'), ('Bob', 'colleagues'), 1.0]
    ])

**Method 3: Define layers first**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Define layers explicitly
    network.add_layer('friends')
    network.add_layer('colleagues')
    
    # Add content (nodes are created automatically with edges)
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0]
    ], input_type="list")

Loading from Files
~~~~~~~~~~~~~~~~~~

py3plex supports multiple input formats. See :doc:`../user_guide/io_and_formats` for complete documentation.

.. code-block:: python

    from py3plex.core import multinet
    
    # From simple edge list (source target)
    network = multinet.multi_layer_network().load_network(
        "data.edgelist",
        input_type="edgelist",
        directed=False
    )
    
    # From multilayer edge list (source target layer)
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist",
        input_type="multiedgelist",
        directed=False
    )
    
    # From GraphML
    network = multinet.multi_layer_network().load_network(
        "data.graphml",
        input_type="graphml"
    )
    
    # From NetworkX graph
    import networkx as nx
    G = nx.karate_club_graph()
    network = multinet.multi_layer_network()
    network.load_network_from_networkx(G)

Network Operations
------------------

Querying Network Elements
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all node-layer pairs
    nodes = network.get_nodes(data=True)  # With attributes
    nodes = network.get_nodes(data=False)  # Without attributes
    
    # Get nodes in a specific layer
    layer_nodes = network.get_nodes(layer='friends')
    
    # Get all edges
    edges = network.get_edges(data=True)
    
    # Get neighbors of a node in a layer
    neighbors = list(network.get_neighbors('Alice', layer_id='friends'))
    
    # Get all layers
    layers = network.get_layers()
    print(f"Layers: {layers}")

Basic Statistics
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get basic network statistics
    network.basic_stats()
    
    # Output:
    # Number of nodes: X
    # Number of edges: Y
    # Number of unique nodes (as node-layer tuples): Z
    # Number of unique node IDs (across all layers): W
    # Nodes per layer:
    #   Layer 'friends': N1 nodes
    #   Layer 'colleagues': N2 nodes

Subnetwork Extraction
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Extract a single layer
    layer_1 = network.subnetwork(['friends'], subset_by="layers")
    
    # Extract specific nodes (all their appearances)
    node_subset = network.subnetwork(['Alice', 'Bob'], subset_by="node_names")
    
    # Extract specific node-layer pairs
    specific_pairs = network.subnetwork(
        [('Alice', 'friends'), ('Bob', 'friends')],
        subset_by="node_layer_names"
    )

Matrix Representations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get supra-adjacency matrix (all layers stacked)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Get adjacency matrix for a single layer
    layer_subgraph = network.subnetwork(['friends'], subset_by="layers")
    layer_adj = nx.adjacency_matrix(layer_subgraph.core_network)

Integration with NetworkX
--------------------------

Full NetworkX Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since py3plex builds on NetworkX, you can use any NetworkX algorithm:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create py3plex network
    mlnet = multinet.multi_layer_network()
    mlnet.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
    ], input_type="list")
    
    # Access underlying NetworkX graph
    G = mlnet.core_network
    
    # Use any NetworkX function
    betweenness = nx.betweenness_centrality(G)
    print(f"Betweenness centrality: {betweenness}")
    
    # Shortest paths
    try:
        path = nx.shortest_path(G, ('A', 'L1'), ('C', 'L1'))
        print(f"Shortest path: {path}")
    except nx.NetworkXNoPath:
        print("No path exists")
    
    # Connected components
    if not G.is_directed():
        components = list(nx.connected_components(G))
        print(f"Number of components: {len(components)}")

NetworkX Wrappers
~~~~~~~~~~~~~~~~~

py3plex provides convenience wrappers for common NetworkX functions:

.. code-block:: python

    # Extract a layer
    layer_1 = network.subnetwork(['layer1'], subset_by="layers")
    
    # Apply NetworkX algorithms via wrapper
    degree_centrality = layer_1.monoplex_nx_wrapper("degree_centrality")
    betweenness = layer_1.monoplex_nx_wrapper("betweenness_centrality")
    
    # Results are dictionaries mapping node-layer pairs to values
    print(f"Degree centrality: {degree_centrality}")

Converting Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # From NetworkX to py3plex
    import networkx as nx
    from py3plex.core import multinet
    
    G = nx.karate_club_graph()
    mlnet = multinet.multi_layer_network()
    # NetworkX graphs are imported as single-layer networks
    mlnet.load_network_from_networkx(G)
    
    # From py3plex to NetworkX (already a NetworkX graph!)
    G_export = mlnet.core_network
    
    # Save as standard NetworkX formats
    nx.write_graphml(G_export, "output.graphml")
    nx.write_gml(G_export, "output.gml")

Performance Considerations
--------------------------

Sparse vs. Dense Matrices
~~~~~~~~~~~~~~~~~~~~~~~~~~

For large networks, always use sparse matrix representations:

.. code-block:: python

    # Good: Sparse matrix (efficient for large networks)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Bad: Dense matrix (memory-intensive)
    # Only use for small networks (< 1000 nodes)
    supra_adj_dense = network.get_supra_adjacency_matrix(sparse=False)

Memory Usage
~~~~~~~~~~~~

Node-layer pairs mean that a node appearing in :math:`L` layers occupies :math:`L` times the memory of a single-layer network. For networks with many layers:

* Consider layer-specific analysis when possible
* Use subnetwork extraction to work with smaller portions
* See :doc:`../deployment/performance_scalability` for optimization strategies

Tensor-Like Indexing
~~~~~~~~~~~~~~~~~~~~

You can access nodes and edges using tensor-like notation:

.. code-block:: python

    from py3plex.core import multinet, random_generators
    
    # Create a network
    network = random_generators.random_multilayer_ER(100, 3, 0.05, directed=False)
    
    # Get some nodes and edges
    some_nodes = list(network.get_nodes())[0:5]
    some_edges = list(network.get_edges())[0:5]
    
    # Access node directly (returns node attributes)
    node_data = network[some_nodes[0]]
    print(f"Node {some_nodes[0]} data: {node_data}")
    
    # Access edge (returns edge attributes)
    edge_data = network[some_edges[0][0]][some_edges[0][1]]
    print(f"Edge data: {edge_data}")

Design Principles
-----------------

py3plex follows several key design principles:

**1. NetworkX Compatibility**

All operations maintain compatibility with NetworkX, allowing seamless use of the rich NetworkX ecosystem.

**2. Lazy Evaluation**

Expensive operations like supra-adjacency matrix construction are computed on demand and cached when appropriate.

**3. Graceful Degradation**

Optional features (like Infomap community detection or advanced visualizations) fail gracefully with informative error messages if dependencies are missing.

**4. Extensibility**

The modular design makes it easy to extend py3plex with custom algorithms and visualizations.

**5. Flexibility**

Multiple ways to construct and manipulate networks to suit different workflows and use cases.

Comparison with Other Representations
--------------------------------------

Why Node-Layer Pairs?
~~~~~~~~~~~~~~~~~~~~~

Alternative representations exist, but py3plex's node-layer pair approach offers key advantages:

**Alternative: Separate graphs per layer**

*Drawback:* Loses inter-layer information, requires manual bookkeeping for cross-layer operations.

**Alternative: Single graph with edge type attributes**

*Drawback:* Cannot distinguish node context across layers, loses layer-specific node attributes.

**py3plex approach: Node-layer pairs**

*Advantages:*

* Preserves both intra-layer and inter-layer structure
* Allows layer-specific node attributes
* Compatible with NetworkX algorithms
* Efficient for multilayer-specific operations

Next Steps
----------

* :doc:`../user_guide/networks` - Creating and manipulating networks in practice
* :doc:`../user_guide/statistics` - Computing multilayer network statistics
* :doc:`design_principles` - High-level design philosophy
* :doc:`algorithm_landscape` - Overview of available algorithms
* :doc:`../user_guide/io_and_formats` - Complete I/O documentation
* :doc:`../reference/api_index` - Full API reference

**Academic References:**

* De Domenico et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X* 3(4): 041022.
* Kivelä et al. (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271.
