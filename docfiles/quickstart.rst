Quickstart Guide
================

This guide gets you started with py3plex quickly. For a more comprehensive introduction, see the :doc:`10min_tutorial`.

Creating Your First Multilayer Network
---------------------------------------

Let's create a simple multilayer network from scratch:

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

    Number of nodes: 5
    Number of edges: 4
    Number of layers: 2

Loading Networks from Files
----------------------------

py3plex supports multiple input formats:

From Edge List
~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Load from a simple edge list
    network = multinet.multi_layer_network().load_network(
        "data.edgelist", 
        input_type="edgelist", 
        directed=False
    )
    
    network.basic_stats()

From Multilayer Edge List
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Load from multilayer edge list (source target layer format)
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist",
        input_type="multiedgelist",
        directed=False
    )

From GraphML
~~~~~~~~~~~~

.. code-block:: python

    # Load from GraphML format
    network = multinet.multi_layer_network().load_network(
        "data.graphml",
        input_type="graphml"
    )

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

Community Detection
-------------------

Using Louvain Algorithm
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    
    # Detect communities using Louvain modularity optimization
    communities = community_louvain.best_partition(network.core_network)
    
    # Display communities
    for node, community_id in communities.items():
        print(f"Node {node} -> Community {community_id}")

Using Infomap
~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    
    # Detect communities using Infomap (requires infomap binary)
    communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"
    )

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_modularity as mlm
    
    # Compute multilayer modularity
    supra_adj = network.get_supra_adjacency_matrix()
    communities = mlm.multilayer_louvain(supra_adj)

Network Visualization
---------------------

Basic Visualization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Simple visualization
    draw_multilayer_default([network], display=True)

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

PageRank
~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import node_ranking
    
    # PageRank on multilayer network
    pagerank = node_ranking.pagerank(network.core_network)
    
    top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 nodes by PageRank:", top_pr)

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Versatility centrality (cross-layer importance)
    versatility = mls.versatility_centrality(network, centrality_type='betweenness')

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

Exporting Networks
------------------

Save to GraphML
~~~~~~~~~~~~~~~

.. code-block:: python

    # Export to GraphML format
    network.save_network("output.graphml", output_type="graphml")

Save to Pickle
~~~~~~~~~~~~~~

.. code-block:: python

    # Save as NetworkX pickle
    network.save_network("output.gpickle", output_type="gpickle")

Save Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    
    # Get supra-adjacency matrix
    adj_matrix = network.get_supra_adjacency_matrix()
    
    # Save as numpy array
    np.save("supra_adjacency.npy", adj_matrix)

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

See the `examples/ directory <https://github.com/SkBlaz/Py3Plex/tree/master/examples>`_ for:

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
