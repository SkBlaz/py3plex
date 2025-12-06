Design of Py3plex
=============================

This chapter explains how py3plex is architected and why it makes specific design choices. Understanding these design principles will help you use the library more effectively and debug unexpected behavior.

Architecture Overview
---------------------

Py3plex is built on three foundational principles:

1. **NetworkX compatibility** — Leverage a mature, well-tested ecosystem
2. **Modular design** — Separate concerns for flexibility and extensibility
3. **Simple, off-the-shelf functionality** — Minimize barrier to entry

The library consists of several core modules:

.. code-block:: text

    py3plex/
    ├── core/                    # Data structures (multi_layer_network class)
    ├── algorithms/              # Analysis methods
    │   ├── statistics/          # Multilayer statistics
    │   ├── centrality/          # Centrality measures
    │   ├── community_detection/ # Community algorithms
    │   └── paths/               # Path algorithms
    ├── dynamics/                # Dynamical processes (SIS, SIR, random walks)
    ├── dsl/                     # SQL-like query language
    ├── visualization/           # Plotting and visualization
    ├── io/                      # Data loading/saving
    └── cli.py                   # Command-line interface

Node-Layer Pair Representation
-------------------------------

The Fundamental Unit
~~~~~~~~~~~~~~~~~~~~

Py3plex represents multilayer networks using **node-layer pairs** as the fundamental unit. A node :math:`v` in layer :math:`\alpha` is stored as the tuple :math:`(v, \alpha)`.

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    # Add nodes explicitly as (node_id, layer_id) pairs
    network.add_nodes([
        ('Alice', 'friends'),
        ('Bob', 'friends'),
        ('Alice', 'colleagues'),
    ])
    
    # Or implicitly through edge addition
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")

**Why node-layer pairs?**

* **Unambiguous identification** — The same logical entity (Alice) has distinct identities in different layers
* **NetworkX compatibility** — Tuples are valid NetworkX node identifiers
* **Efficient lookups** — Python's tuple hashing enables fast operations
* **Natural tensor mapping** — Node-layer pairs map directly to rows/columns of the supra-adjacency matrix

The ``multi_layer_network`` Class
----------------------------------

Core Components
~~~~~~~~~~~~~~~

The ``multi_layer_network`` class wraps a NetworkX graph and adds multilayer-specific functionality:

.. code-block:: python

    network = multinet.multi_layer_network(directed=False)
    
    # The underlying NetworkX graph (MultiGraph or MultiDiGraph)
    G = network.core_network
    
    # Layer management
    layers = network.get_layers()           # ['friends', 'colleagues']
    layer_map = network.layer_name_map      # {'friends': 0, 'colleagues': 1}
    
    # Access node-layer pairs
    nodes = list(network.get_nodes())       # [('Alice', 'friends'), ...]

**Key attributes:**

* ``core_network`` — The NetworkX graph storing all node-layer pairs and edges
* ``layer_name_map`` — Mapping from layer names to internal IDs
* ``directed`` — Whether the network is directed

Multilayer vs. Multiplex Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex supports two operational modes:

**Multilayer (default):**

* General multilayer networks with arbitrary node sets per layer
* No automatic inter-layer edges
* Use for heterogeneous networks (different node types)

.. code-block:: python

    # Heterogeneous network: authors and papers
    network = multinet.multi_layer_network(network_type='multilayer')
    network.add_edges([
        ['Alice', 'authors', 'Paper1', 'papers', 1],
        ['Paper1', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

**Multiplex:**

* Same node set in all layers
* Automatically creates identity (coupling) edges with ``type='coupling'``
* Use when the same entities appear in all layers

.. code-block:: python

    # Social network: same people, different relationships
    network = multinet.multi_layer_network(network_type='multiplex')
    network.load_network('social.edges', input_type='multiplex_edges')
    
    # Coupling edges are auto-created: (Alice, friends) <-> (Alice, colleagues)
    
    # Get explicit edges only (exclude coupling)
    explicit_edges = list(network.get_edges(multiplex_edges=False))

Relationship to NetworkX
-------------------------

Direct Access to NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex does not hide NetworkX—it exposes the underlying graph for direct manipulation:

.. code-block:: python

    import networkx as nx
    
    # Access the graph directly
    G = network.core_network
    
    # Use any NetworkX function
    betweenness = nx.betweenness_centrality(G)
    communities = nx.community.louvain_communities(G)
    
    # Modify the graph directly
    G.nodes[('Alice', 'friends')]['age'] = 30

**Why this matters:**

* You can use **any NetworkX algorithm** on the multilayer network
* You can **extend py3plex** by writing functions that operate on ``core_network``
* You don't need to learn a completely new API—if you know NetworkX, you know most of py3plex

NetworkX Interoperability
~~~~~~~~~~~~~~~~~~~~~~~~~

Convert between py3plex and NetworkX:

.. code-block:: python

    # From NetworkX to py3plex
    import networkx as nx
    G = nx.karate_club_graph()
    network = multinet.multi_layer_network()
    network.load_network_from_networkx(G, layer_name='social')
    
    # From py3plex to NetworkX (extract a single layer)
    friends_layer = network.get_layer_subgraph('friends')

This enables workflows that mix py3plex's multilayer capabilities with NetworkX's extensive algorithm library.

Core Modules
------------

Algorithms
~~~~~~~~~~

**Statistics** (``py3plex/algorithms/statistics/``)
  Multilayer-specific metrics like degree distributions, layer overlap, and aggregation statistics.

**Centrality** (``py3plex/algorithms/centrality/``)
  Centrality measures adapted for multilayer networks, including explainable centrality that breaks down scores by layer.

**Community Detection** (``py3plex/algorithms/community_detection/``)
  Multilayer Louvain, Infomap, and modularity-based methods.

**Paths** (``py3plex/paths/``)
  Shortest paths, random walks, and flow algorithms that respect layer structure.

Dynamics
~~~~~~~~

**Dynamical Processes** (``py3plex/dynamics/``)
  OOP-style classes for epidemic models (SIS, SIR, SEIR), random walks, and custom dynamics. Each model has:

* ``set_seed()`` for reproducibility
* ``run()`` for execution
* ``get_measure()`` for extracting results

DSL and Query Language
~~~~~~~~~~~~~~~~~~~~~~

**Domain-Specific Language** (``py3plex/dsl/``)
  SQL-like queries for network analysis:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    result = (
        Q.nodes()
         .from_layers(L["friends"])
         .where(degree__gt=5)
         .compute("betweenness_centrality")
         .execute(network)
    )

The DSL provides:

* **Builder API** — Chainable, type-hinted query construction
* **String syntax** — SQL-like queries as strings
* **EXPLAIN mode** — Query execution plans
* **Export** — Results to pandas, JSON, CSV

Visualization
~~~~~~~~~~~~~

**Visualization** (``py3plex/visualization/``)
  Publication-ready plots including:

* **Hairball plots** — 2D/3D force-directed layouts with layer separation
* **Matrix plots** — Supra-adjacency matrix visualization
* **Diagonal layouts** — Specialized for large multilayer networks

I/O
~~~

**Input/Output** (``py3plex/io/``)
  Support for multiple formats:

* **Edgelists** — Simple text format
* **GraphML** — XML-based format
* **Arrow/Parquet** — High-performance columnar format for large networks
* **JSON** — Flexible structured format

Design Principles in Practice
------------------------------

1. Flexible Input
~~~~~~~~~~~~~~~~~

Multiple ways to accomplish the same task:

.. code-block:: python

    # Method 1: List format
    network.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type="list")
    
    # Method 2: Dict format (explicit)
    network.add_edges([{
        'source': 'A', 'target': 'B',
        'source_type': 'L1', 'target_type': 'L1'
    }])
    
    # Method 3: Load from file
    network.load_network("data.edgelist", input_type="edgelist")

2. Lazy Evaluation
~~~~~~~~~~~~~~~~~~

Expensive operations are computed only when needed:

.. code-block:: python

    # Network creation and edge addition are fast
    network = multinet.multi_layer_network()
    network.add_edges([...])  # No supra-adjacency matrix computed
    
    # Matrix is computed only when requested
    supra_adj = network.get_supra_adjacency_matrix()  # Computed here

3. Graceful Degradation
~~~~~~~~~~~~~~~~~~~~~~~

The library handles edge cases and provides informative warnings:

* Missing layers → created automatically
* Empty networks → return sensible defaults
* Invalid parameters → clear error messages

4. Extensibility
~~~~~~~~~~~~~~~~

Adding new algorithms is straightforward:

.. code-block:: python

    def my_custom_metric(network):
        """Custom multilayer metric."""
        G = network.core_network
        # Implement your algorithm using G
        return result
    
    # Use immediately
    score = my_custom_metric(network)

Why These Choices Matter
-------------------------

**NetworkX compatibility** means you can:

* Use hundreds of existing algorithms without modification
* Mix py3plex with other NetworkX-based tools
* Leverage a mature, well-documented ecosystem

**Node-layer pair representation** ensures:

* Unambiguous node identity across layers
* Efficient graph operations (hashing, lookups)
* Direct mapping to mathematical definitions

**Modular architecture** allows:

* Importing only needed functionality
* Easy testing and debugging
* Clean separation of concerns

**Multiple input methods** accommodate:

* Different data sources and formats
* User preferences and workflows
* Programmatic and interactive use

Limitations and Trade-offs
---------------------------

No design is perfect. Py3plex makes conscious trade-offs:

**Memory:**
  The supra-adjacency matrix for large networks can be memory-intensive. Use sparse matrix formats (default) and avoid materializing the full matrix when possible.

**Performance:**
  Some operations (e.g., cross-layer random walks) require iteration over node-layer pairs, which is slower than pure NetworkX on single-layer graphs.

**Coupling semantics:**
  The automatic coupling in multiplex mode assumes identity edges. For more complex inter-layer relationships, use multilayer mode and add edges explicitly.

Summary
-------

Py3plex is designed around:

1. **Node-layer pairs** as the fundamental unit
2. **NetworkX compatibility** for interoperability and extensibility
3. **Modular architecture** for flexibility
4. **Simple, practical APIs** for ease of use

These principles enable:

* Correct multilayer analysis (proper layer semantics)
* Efficient implementation (leverage NetworkX)
* Extensible design (add your own algorithms)
* Practical workflows (multiple input formats, visualization, DSL)

The following chapters will show how to use these design elements in practice: loading data, visualizing networks, and running multilayer-specific algorithms.

Further Reading
---------------

* NetworkX documentation: https://networkx.org/documentation/stable/
* Py3plex API reference: :doc:`../appendices/appendix_e_api_reference`
* Code architecture: :doc:`../appendices/appendix_a_repo_layout`
