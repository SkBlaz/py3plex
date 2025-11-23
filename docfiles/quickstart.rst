Quickstart Guide
================

This guide gets you started with py3plex quickly. For a more comprehensive introduction, see the :doc:`10min_tutorial`.

Quick Start with Docker
-----------------------

If you prefer using Docker, you can get started immediately without installing Python dependencies:

.. code-block:: bash

    # Clone and build
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    docker build -t py3plex:latest .

    # Create a data directory for files
    mkdir -p data

    # Create a simple multilayer network
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      create --nodes 50 --layers 3 --output /data/network.edgelist

    # Analyze it
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      load /data/network.edgelist --info

**For complete Docker documentation**, see :doc:`tutorials/docker_usage`.

Creating Your First Multilayer Network
---------------------------------------

Create a simple multilayer network from scratch:

.. code-block:: python

    from py3plex.core import multinet

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges within layers (nodes are created automatically)
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
        ['B', 'layer2', 'D', 'layer2', 1]
    ], input_type="list")

    # Display basic statistics
    network.basic_stats()

**Expected Output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 6
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'layer1': 3 nodes
      Layer 'layer2': 3 nodes

Loading Networks from Files
----------------------------

py3plex supports multiple input formats:

From Edge List
~~~~~~~~~~~~~~

Load from a simple edge list:

.. code-block:: python

    from py3plex.core import multinet

    # Load from a simple edge list
    network = multinet.multi_layer_network().load_network(
        "data.edgelist",
        input_type="edgelist",
        directed=False
    )

    network.basic_stats()

**Expected Output:**

.. code-block:: text

    Number of nodes: 3
    Number of edges: 2
    Number of unique nodes (as node-layer tuples): 3
    Number of unique node IDs (across all layers): 3
    Nodes per layer:
      Layer 'default': 3 nodes

From Multilayer Edge List
~~~~~~~~~~~~~~~~~~~~~~~~~~

Load from multilayer edge list (source target layer format):

.. code-block:: python

    # Load from multilayer edge list (source target layer format)
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist",
        input_type="multiedgelist",
        directed=False
    )

**Expected Output:**

.. code-block:: text

    Number of nodes: 4
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 7
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'layer1': 3 nodes
      Layer 'layer2': 3 nodes

From GraphML
~~~~~~~~~~~~

.. code-block:: python

    # Load from GraphML format
    network = multinet.multi_layer_network().load_network(
        "data.graphml",
        input_type="graphml"
    )

**Expected Output:**

.. code-block:: text

    # Output depends on the GraphML file structure
    # Similar to above examples

Supported Formats
~~~~~~~~~~~~~~~~~

* ``edgelist`` - Simple source-target pairs
* ``multiedgelist`` - Source, target, layer format
* ``gpickle`` - NetworkX pickle format
* ``gml`` - Graph Modeling Language
* ``graphml`` - GraphML XML format

Basic Network Analysis
----------------------

Computing Network Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get basic network information
    num_nodes = len(network.get_nodes())
    num_edges = len(network.get_edges())
    num_layers = len(network.get_layers())

    print(f"Nodes: {num_nodes}, Edges: {num_edges}, Layers: {num_layers}")

**Expected Output:**

.. code-block:: text

    Nodes: 6, Edges: 4, Layers: 3

Multilayer Statistics
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # Layer density
    density = mls.layer_density(network, 'layer1')
    print(f"Layer density: {density}")

    # Node activity (fraction of layers where node is present)
    activity = mls.node_activity(network, 'node_A')
    print(f"Node activity: {activity}")

    # Versatility centrality (importance across layers)
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    print(f"Top versatile nodes: {sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]}")

**Expected Output:**

.. code-block:: text

    Layer density: 0.3333333333333333
    Node activity: 1.0
    Top versatile nodes: [('B', 1.0), ('A', 0.5), ('C', 0.25), ('D', 0.25)]

Iterating Over Network Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Iterate through nodes
    for node in network.get_nodes(data=True):
        print(node)

    # Iterate through edges
    for edge in network.get_edges(data=True):
        print(edge)

    # Get neighbors of a node in a specific layer
    neighbors = list(network.get_neighbors('node1', layer_id='layer1'))
    print(f"Neighbors: {neighbors}")

**Expected Output:**

.. code-block:: text

    # Sample nodes (first few):
    (('A', 'layer1'), {'pos': array([...]), ...})
    (('B', 'layer1'), {'pos': array([...]), ...})
    ...

    # Sample edges:
    (('A', 'layer1'), ('B', 'layer1'), {'weight': 1, 'type': 'default'})
    (('B', 'layer1'), ('C', 'layer1'), {'weight': 1, 'type': 'default'})
    ...

    Neighbors of node 'A' in 'layer1': [('B', 'layer1')]

Community Detection
-------------------

Using Louvain Algorithm
~~~~~~~~~~~~~~~~~~~~~~~

Detect communities using Louvain modularity optimization:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain

    # Detect communities using Louvain modularity optimization
    communities = community_louvain.best_partition(network.core_network)

    # Display communities
    for node, community_id in communities.items():
        print(f"Node {node} -> Community {community_id}")

**Expected Output:**

.. code-block:: text

    # Example output (will vary based on network structure):
    Node ('A', 'layer1') -> Community 0
    Node ('B', 'layer1') -> Community 0
    Node ('C', 'layer1') -> Community 1
    Node ('A', 'layer2') -> Community 0
    Node ('B', 'layer2') -> Community 0
    Node ('D', 'layer2') -> Community 1

**Note:** Louvain algorithm requires an undirected graph. For directed multilayer networks,
you may need to convert to undirected or use multilayer-specific algorithms.

Using Infomap
~~~~~~~~~~~~~

Detect communities using Infomap (requires infomap binary):

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper

    # Detect communities using Infomap (requires infomap binary)
    communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"
    )

**Note:** Infomap requires external binary installation. See :doc:`installation` for details.

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

Compute multilayer modularity:

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_modularity as mlm

    # Compute multilayer modularity
    supra_adj = network.get_supra_adjacency_matrix()
    communities = mlm.multilayer_louvain(supra_adj)

**Expected Output:**

.. code-block:: text

    # Returns dictionary of community assignments
    {node_id: community_id, ...}

**Note:** Advanced multilayer community detection that considers layer structure.

Network Visualization
---------------------

Basic Visualization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default

    # Simple visualization
    draw_multilayer_default([network], display=True)

**Note:** This produces a visual plot. No text output to console.
See :doc:`visualization_guide` for customization options.

Customized Visualization
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization import drawing_machinery as dm

    # Customize layout and appearance
    hairball_plot(
        network.core_network,
        color_by='layer',
        layout_algorithm='force',
        edge_width=0.5,
        node_size=20
    )

**Note:** Creates customized network visualization with specified parameters.
No text output - produces visual plot.

Diagonal Projection Plot
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default

    # Diagonal projection for large multilayer networks
    draw_multilayer_default(
        [network],
        display=True,
        layout_style='diagonal'
    )

**Note:** Diagonal projection visualization useful for large multilayer networks.
No text output - produces visual plot.

Computing Centrality Measures
------------------------------

Degree Centrality
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms import centrality

    # Multilayer degree centrality
    degree_cent = centrality.multilayer_degree_centrality(network)

    # Display top nodes
    top_nodes = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 nodes by degree centrality:", top_nodes)

**Expected Output:**

.. code-block:: text

    Top 10 nodes by degree centrality: [(('B', 'layer1'), 0.4), (('B', 'layer2'), 0.4), ...]

**Note:** Centrality values depend on network structure. Values are normalized between 0 and 1.

PageRank
~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import node_ranking

    # PageRank on multilayer network
    pagerank = node_ranking.pagerank(network.core_network)

    top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 nodes by PageRank:", top_pr)

**Expected Output:**

.. code-block:: text

    Top 10 nodes by PageRank: [(('B', 'layer1'), 0.18), (('A', 'layer1'), 0.15), ...]

**Note:** PageRank scores sum to 1.0 across all nodes.

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # Versatility centrality (cross-layer importance)
    versatility = mls.versatility_centrality(network, centrality_type='betweenness')

**Expected Output:**

.. code-block:: text

    # Returns dictionary of versatility scores
    {('A',): 0.5, ('B',): 1.0, ('C',): 0.25, ('D',): 0.25}

**Note:** Versatility measures node importance across multiple layers.

Node Embeddings
---------------

Node2Vec Embeddings
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.wrappers import node2vec_embedding

    # Generate Node2Vec embeddings
    embeddings = node2vec_embedding.generate_embeddings(
        network.core_network,
        dimensions=128,
        walk_length=80,
        num_walks=10,
        p=1.0,  # Return parameter
        q=1.0   # In-out parameter
    )

    # embeddings is a matrix of shape (num_nodes, dimensions)
    print(f"Embedding shape: {embeddings.shape}")

**Expected Output:**

.. code-block:: text

    Embedding shape: (6, 128)

**Note:** Node2Vec generates low-dimensional vector representations of nodes.
Output is a numpy array of shape (num_nodes, dimensions).

Random Walks
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks

    # Generate random walks
    walks = generate_walks(
        network.core_network,
        num_walks=10,
        walk_length=80,
        p=1.0,
        q=1.0,
        seed=42
    )

    print(f"Generated {len(walks)} walks")

**Expected Output:**

.. code-block:: text

    Generated 60 walks

**Note:** Random walks are used for network sampling and embedding generation.
Each walk is a sequence of nodes traversed following the specified parameters.

Exporting Networks
------------------

Save to GraphML
~~~~~~~~~~~~~~~

.. code-block:: python

    # Export to GraphML format
    network.save_network("output.graphml", output_type="graphml")

**Note:** Network saved to ``output.graphml``. No console output.
GraphML format preserves node and edge attributes.

Save to Pickle
~~~~~~~~~~~~~~

.. code-block:: python

    # Save as NetworkX pickle
    network.save_network("output.gpickle", output_type="gpickle")

**Note:** Network saved to ``output.gpickle``. No console output.
Pickle format is fastest for loading/saving in Python.

Save Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np

    # Get supra-adjacency matrix
    adj_matrix = network.get_supra_adjacency_matrix()

    # Save as numpy array
    np.save("supra_adjacency.npy", adj_matrix)

**Expected Output:**

.. code-block:: text

    # Supra-adjacency matrix saved to supra_adjacency.npy
    # Matrix shape: (6, 6) for network with 6 node-layer tuples

**Note:** NumPy binary format for efficient matrix storage and loading.
The supra-adjacency matrix represents the entire multilayer network structure.

Next Steps
----------

After this quickstart, explore:

* :doc:`10min_tutorial` - Comprehensive 10-minute tutorial
* :doc:`basic_usage` - Detailed usage guide
* :doc:`tutorials/multilayer_centrality` - Multilayer centrality measures
* :doc:`tutorials/community_detection` - Advanced community detection
* :doc:`visualization` - Visualization techniques

Examples
--------

See the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/master/examples>`_ for:

* ``example_multilayer_visualization.py`` - Visualization examples
* ``example_community_detection.py`` - Community detection
* ``example_multilayer_statistics.py`` - Statistical analysis
* ``example_random_walks.py`` - Random walk algorithms
* ``example_multilayer_centrality.py`` - Centrality measures

Getting Help
------------

* **Documentation:** https://skblaz.github.io/py3plex/
* **Examples:** https://github.com/SkBlaz/py3plex/tree/master/examples
* **Issues:** https://github.com/SkBlaz/py3plex/issues
* **Discussions:** https://github.com/SkBlaz/py3plex/discussions
