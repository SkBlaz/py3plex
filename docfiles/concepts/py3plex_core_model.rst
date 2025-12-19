The py3plex Core Model
======================

*In which we look under the hood at how py3plex represents multilayer networks, understand the node-layer pair representation, and learn to work with the supra-adjacency matrix.*

----

In the previous chapter, you learned *what* multilayer networks are conceptually. Now we'll see *how* py3plex represents them in code—and why these design choices matter for your analysis.

Understanding the internal representation will help you:

- Debug unexpected behavior (why does my network have twice as many nodes as I expected?)
- Integrate with NetworkX (how do I use existing algorithms on my multilayer network?)
- Scale to large networks (when should I use sparse matrices? how much memory will this take?)
- Extend py3plex (how do I add my own algorithms?)

Network Types: Multilayer vs Multiplex
---------------------------------------

py3plex supports two network types that determine how layers and inter-layer connections are handled:

**Multilayer Networks** (``network_type='multilayer'``, default)

General multilayer networks where each layer can have a different set of nodes. No automatic coupling edges are created.

* Use when layers represent different node types (e.g., authors, papers, venues)
* Use when nodes naturally appear in only some layers
* Inter-layer edges must be explicitly added

.. code-block:: python

    from py3plex.core import multinet
    
    # Heterogeneous network: authors and papers are different node types
    network = multinet.multi_layer_network(network_type='multilayer')
    network.add_edges([
        {'source': 'author1', 'target': 'paper1',
         'source_type': 'authors', 'target_type': 'papers'}
    ])

**Multiplex Networks** (``network_type='multiplex'``)

Special case where all layers share the same set of nodes but with different relationship types. After loading, coupling edges are automatically created between each node and its counterparts in other layers.

* Use when the same entities (people, cities) are connected via multiple relationship types
* Coupling edges are auto-generated with ``type='coupling'``
* Filter coupling edges using ``get_edges(multiplex_edges=False)``

.. code-block:: python

    # Social network: same people, different relationship types
    network = multinet.multi_layer_network(network_type='multiplex')
    network.load_network('friends_and_colleagues.edges', input_type='multiplex_edges')
    
    # Coupling edges are auto-created between (Alice, friends) <-> (Alice, colleagues)
    
    # Get only explicit edges (exclude auto-coupling)
    explicit_edges = list(network.get_edges(multiplex_edges=False))
    
    # Get all edges including coupling
    all_edges = list(network.get_edges(multiplex_edges=True))

**Comparison Table:**

===============  ===================  ===================
Feature          multilayer           multiplex
===============  ===================  ===================
Node sets        Different per layer  Same across layers
Coupling edges   Manual               Automatic
Load behavior    As-is                + coupling edges
get_edges()      All edges            Filters coupling
Use case         Heterogeneous nets   Same entities
===============  ===================  ===================

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

The supra-adjacency matrix is a block matrix representation that encodes the entire multilayer network structure in one object. It respects the ordering of node-layer pairs, so always check how nodes are ordered in your network before interpreting row/column indices.

Mathematical Definition
~~~~~~~~~~~~~~~~~~~~~~~

For a multilayer network with :math:`L` layers, the supra-adjacency matrix :math:`\mathbf{S}` is built by stacking each layer's adjacency and the inter-layer coupling blocks. We assume node-layer pairs are ordered by layer, then by node within each layer:

.. math::

    \mathbf{S} = \begin{bmatrix}
    A_1 & C_{12} & \cdots & C_{1L} \\
    C_{21} & A_2 & \cdots & C_{2L} \\
    \vdots & \vdots & \ddots & \vdots \\
    C_{L1} & C_{L2} & \cdots & A_L
    \end{bmatrix}

Where:

* :math:`A_\alpha \in \mathbb{R}^{n_\alpha \times n_\alpha}` is the adjacency matrix of layer :math:`\alpha` (intra-layer connections)
* :math:`C_{\alpha\beta} \in \mathbb{R}^{n_\alpha \times n_\beta}` is the coupling matrix between layers :math:`\alpha` and :math:`\beta` (inter-layer connections)
* The full matrix has size :math:`(\sum_{\alpha=1}^L n_\alpha) \times (\sum_{\alpha=1}^L n_\alpha)`

In multiplex networks, :math:`n_\alpha` is typically the same for all layers, so :math:`\mathbf{S}` becomes an :math:`(N \cdot L) \times (N \cdot L)` matrix. For undirected networks, :math:`A_\alpha = A_\alpha^\top` and :math:`C_{\alpha\beta} = C_{\beta\alpha}^\top`; for directed networks these blocks can be asymmetric. Identity coupling corresponds to :math:`C_{\alpha\beta} = \omega I` (with coupling weight :math:`\omega`) when layers share node identities.

Numeric Example
~~~~~~~~~~~~~~~

Consider a simple multiplex network with 3 nodes (A, B, C) and 2 layers. In layer 1, A-B are connected. In layer 2, B-C are connected. The nodes are the same across layers (multiplex structure).

**Network structure:**

.. code-block:: text

    Layer 1:        Layer 2:
    A --- B   C     A   B --- C

**Node ordering:** We order nodes as (A,L1), (B,L1), (C,L1), (A,L2), (B,L2), (C,L2).

**Intra-layer blocks:**

Layer 1 adjacency matrix (A₁):

.. code-block:: text

         A   B   C
    A [  0   1   0 ]
    B [  1   0   0 ]
    C [  0   0   0 ]

Layer 2 adjacency matrix (A₂):

.. code-block:: text

         A   B   C
    A [  0   0   0 ]
    B [  0   0   1 ]
    C [  0   1   0 ]

**Inter-layer coupling blocks (C₁₂ and C₂₁):**

In a multiplex network, we typically add identity coupling—each node connects to itself across layers with the chosen coupling weight (here 1.0):

.. code-block:: text

    C₁₂ = C₂₁ᵀ = 
         A   B   C
    A [  1   0   0 ]
    B [  0   1   0 ]
    C [  0   0   1 ]

**Full supra-adjacency matrix (6×6):**

.. code-block:: text

              Layer 1        |     Layer 2
           A    B    C       |  A    B    C
    L1  A [ 0    1    0      |  1    0    0 ]
        B [ 1    0    0      |  0    1    0 ]
        C [ 0    0    0      |  0    0    1 ]
       ---|------------------+---------------
    L2  A [ 1    0    0      |  0    0    0 ]
        B [ 0    1    0      |  0    0    1 ]
        C [ 0    0    1      |  0    1    0 ]

The diagonal 3×3 blocks are the within-layer adjacencies (A₁ and A₂). The off-diagonal 3×3 blocks are the coupling matrices (C₁₂ and C₂₁).

**What this enables:**

* **Multilayer shortest paths:** A path from (A,L1) to (C,L2) must go through B: (A,L1)→(B,L1)→(B,L2)→(C,L2)
* **Spectral methods:** Eigenvalues of S capture multilayer structure
* **Matrix operations:** All linear algebra works on the full system

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

Memory Implications
~~~~~~~~~~~~~~~~~~~

Let :math:`n_\text{total} = \sum_{\alpha=1}^L n_\alpha` (the number of node-layer pairs). The supra-adjacency matrix is :math:`n_\text{total} \times n_\text{total}`. If every layer has :math:`N` nodes, then :math:`n_\text{total} = N \cdot L`.

Worked estimates (assuming equal nodes per layer):

* **Small network (100 nodes, 3 layers):** 300×300 = 90,000 entries → ~720 KB dense
* **Medium network (1,000 nodes, 5 layers):** 5,000×5,000 = 25 million entries → ~200 MB dense
* **Large network (10,000 nodes, 10 layers):** 100,000×100,000 = 10 billion entries → ~80 GB dense (impractical)

**Always use sparse=True** for networks with more than ~1,000 total node-layer pairs. Sparse matrices only store non-zero entries, reducing memory from :math:`O(n_\text{total}^2)` potential entries to roughly :math:`O(\text{edges} + \text{coupling edges})` actual non-zeros.

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

How py3plex Uses NetworkX Under the Hood
----------------------------------------

py3plex is built on top of NetworkX, using it as the storage and algorithm backend. Understanding this architecture helps you leverage the full NetworkX ecosystem.

The Role of MultiGraph/MultiDiGraph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Internally, py3plex stores all nodes and edges in a single NetworkX ``MultiGraph`` (for undirected) or ``MultiDiGraph`` (for directed networks). The multilayer structure is encoded through the node representation:

.. code-block:: python

    # What you write in py3plex:
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")
    
    # What's actually stored in NetworkX:
    # Nodes: ('Alice', 'friends'), ('Bob', 'friends'), 
    #        ('Alice', 'colleagues'), ('Bob', 'colleagues')
    # Edges: (('Alice', 'friends'), ('Bob', 'friends')),
    #        (('Alice', 'colleagues'), ('Bob', 'colleagues'))

This means:

1. **All NetworkX algorithms work directly** on the underlying graph
2. **Node-layer tuples are just nodes** to NetworkX—it doesn't "know" about layers
3. **Attributes are stored as NetworkX attributes** and persist across operations

Attribute Propagation
~~~~~~~~~~~~~~~~~~~~~

When you add nodes or edges with attributes, they're stored in the NetworkX graph:

.. code-block:: python

    # Node attributes
    network.core_network.nodes[('Alice', 'friends')]['age'] = 30
    network.core_network.nodes[('Alice', 'friends')]['role'] = 'admin'
    
    # Edge attributes
    network.core_network[('Alice', 'friends')][('Bob', 'friends')]['weight'] = 0.8
    network.core_network[('Alice', 'friends')][('Bob', 'friends')]['type'] = 'close'

Attributes are preserved when you:

* Extract subnetworks (filtered nodes keep their attributes)
* Iterate over nodes/edges with ``data=True``
* Save and load networks (in formats that support attributes)

Using NetworkX Functions Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because ``network.core_network`` is a standard NetworkX graph, you can use any NetworkX function:

.. code-block:: python

    import networkx as nx
    
    G = network.core_network
    
    # Standard NetworkX algorithms
    betweenness = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G)
    components = list(nx.connected_components(G.to_undirected()))
    
    # Shortest paths (work across layers if inter-layer edges exist)
    path = nx.shortest_path(G, ('Alice', 'friends'), ('Bob', 'colleagues'))
    
    # Community detection (treats node-layer pairs as nodes)
    communities = nx.community.louvain_communities(G)

**Caveat:** NetworkX doesn't know about layer semantics. It treats ('Alice', 'friends') and ('Alice', 'colleagues') as unrelated nodes. py3plex's multilayer algorithms add the layer-aware logic.

Design Trade-offs
-----------------

Node-Layer Pairs vs. Alternative Representations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex's node-layer pair representation is one of several possible designs. Here's why it was chosen:

**Alternative 1: Separate graphs per layer**

.. code-block:: python

    # Instead of py3plex:
    layer1 = nx.Graph()
    layer2 = nx.Graph()
    layer1.add_edge('Alice', 'Bob')
    layer2.add_edge('Alice', 'Bob')

*Pros:*

* Simple, familiar
* Easy layer-specific analysis

*Cons:*

* No representation of inter-layer edges
* Manual bookkeeping for cross-layer operations
* Can't compute multilayer paths or centrality directly

**Alternative 2: Single graph with edge type attributes**

.. code-block:: python

    # Instead of py3plex:
    G = nx.MultiGraph()
    G.add_edge('Alice', 'Bob', type='friends')
    G.add_edge('Alice', 'Bob', type='colleagues')

*Pros:*

* Single graph structure
* Edges carry type information

*Cons:*

* Nodes can't have layer-specific attributes
* Same node in different contexts is the same node (can't have Alice be central in one layer and peripheral in another)
* Inter-layer edges to the same node are impossible

**py3plex approach: Node-layer pairs**

.. code-block:: python

    # py3plex representation:
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")

*Pros:*

* Preserves both intra-layer and inter-layer structure
* Allows layer-specific node attributes
* Compatible with NetworkX algorithms
* Enables proper multilayer-specific operations
* Supports identity coupling and cross-layer edges

*Cons:*

* Node names are tuples (less intuitive for simple cases)
* Memory usage is multiplied by number of layers
* NetworkX algorithms treat node-layer pairs as independent nodes (need py3plex wrappers for multilayer semantics)

**py3plex's choice:** The node-layer pair approach was chosen because it correctly models multilayer semantics while maintaining NetworkX compatibility. The downsides (tuple names, memory) are acceptable trade-offs for the flexibility and correctness gained.

Consequences for Algorithm Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The node-layer pair design has implications:

1. **Layer extraction is subsetting:** To get layer 1, you filter nodes where the layer component equals "layer1"
2. **Identity coupling is explicit:** Cross-layer edges between the same entity must be added explicitly (or automatically in multiplex mode)
3. **Supra-matrix is derivable:** The supra-adjacency matrix can be computed from the graph structure
4. **NetworkX algorithms work but need interpretation:** Betweenness on the full graph treats cross-layer edges as normal edges

Consequences for I/O
~~~~~~~~~~~~~~~~~~~~

The node-layer pair representation affects serialization:

1. **Standard formats work:** GraphML, GML can store tuple nodes
2. **Human-readable formats need mapping:** Edgelists typically use separate columns for node and layer
3. **Arrow/Parquet are efficient:** Modern columnar formats handle the structure naturally

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

You can access nodes and edges using tensor-like notation on the underlying NetworkX graph:

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
    
    # Access edge (returns the adjacency dict for that pair)
    edge_data = network[some_edges[0][0]][some_edges[0][1]]
    print(f"Edge data: {edge_data}")  # For MultiGraph, edge keys map to attribute dicts

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

Alternative representations exist, but py3plex's node-layer pair approach offers key advantages over the two common options:

* **Separate graphs per layer:** Simple, but loses inter-layer information and requires manual bookkeeping for cross-layer operations.
* **Single graph with edge type attributes:** Keeps everything in one graph, but cannot distinguish node context across layers or attach layer-specific node attributes.
* **Node-layer pairs (py3plex):** Preserves both intra-layer and inter-layer structure, supports layer-specific attributes, and stays compatible with NetworkX algorithms while enabling multilayer-specific operations.

What You Learned
----------------

This chapter covered the internal architecture of py3plex:

**Core concepts:**

- The ``multi_layer_network`` class as the central data structure
- Node-layer pairs ``(node_id, layer_id)`` as the fundamental representation
- The difference between ``network_type='multilayer'`` and ``network_type='multiplex'``

**Data structures:**

- The underlying NetworkX MultiGraph/MultiDiGraph
- Layer mappings and layer extraction
- The supra-adjacency matrix and its block structure

**Design trade-offs:**

- Why node-layer pairs were chosen over alternatives
- Memory implications of the representation
- When to use sparse vs. dense matrices

**NetworkX integration:**

- Accessing the core graph with ``network.core_network``
- Using any NetworkX algorithm directly
- The ``monoplex_nx_wrapper()`` convenience method

What's Next?
------------

* :doc:`design_principles` — The philosophy behind py3plex's API design
* :doc:`algorithm_landscape` — Overview of available algorithms
* :doc:`../user_guide/networks` — Practical guide to network operations
* :doc:`../user_guide/statistics` — Computing multilayer statistics
* :doc:`../user_guide/io_and_formats` — Complete I/O documentation

**Academic References:**

* De Domenico et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X* 3(4): 041022.
* Kivelä et al. (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271.

----

*Next chapter: :doc:`design_principles` — understanding py3plex's design philosophy.*
