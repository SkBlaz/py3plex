Community Detection
===================

py3plex provides **wrappers for community detection algorithms** optimized for **multilayer networks**.

Supported Algorithms
--------------------

- **Infomap** - **Information-theoretic**, supports overlapping communities
- **Louvain** - **Modularity optimization**
- **Label Propagation** - **Semi-supervised learning**
- **NoRC (Node Ranking and Clustering)** - **PageRank-based hierarchical clustering**

Basic Usage
-----------

**Louvain:**

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    partition = cw.louvain_communities(network)

**NoRC (Node Ranking and Clustering):**

.. code-block:: python

    from py3plex.algorithms.community_detection.NoRC import NoRC_communities_main
    import networkx as nx
    
    # Create or load a graph
    G = nx.karate_club_graph()
    
    # Detect communities using k-means clustering
    communities_kmeans = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",
        verbose=True,
        community_range=[2, 3, 5, 7, 10]
    )
    
    # Or use hierarchical clustering
    communities_hierarchical = NoRC_communities_main(
        G,
        clustering_scheme="hierarchical",
        verbose=True,
        community_range=[2, 3, 5, 7, 10]
    )

**NoRC Parameters:**

- ``clustering_scheme``: "kmeans" or "hierarchical" (default: "hierarchical")
- ``parallel_step``: Number of parallel workers (default: auto-detect based on CPU count)
- ``prob_threshold``: Threshold for PageRank probabilities (default: 0.0005)
- ``community_range``: List of community counts to try (default: [1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300])
- ``lag_threshold``: Early stopping after N iterations without improvement (default: 10)
- ``fine_range``: Range for fine-grained search around optimal solution (default: 3)

**Infomap** (multiplex):

.. note::

    Infomap requires an external binary that is no longer bundled with py3plex.
    
    **Options:**
    
    - Download from: https://www.mapequation.org/infomap/
    - Install via: ``pip install infomap``
    - Use Louvain (above) as a Python-only alternative

.. code-block:: python

    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        "../datasets/simple_multiplex.edgelist", 
        directed=False, 
        input_type="multiplex_edges")
    
    # Assumes Infomap binary is in PATH or current directory
    partition = cw.infomap_communities(
        network, binary="infomap", multiplex=True, verbose=True)

Examples
--------

See **detailed examples**:

- ``example_community_detection.py`` - **Basic community detection**
- ``example_community_multiplex.py`` - **Multiplex community detection**
- ``example_community_visualization.py`` - **Visualizing communities**

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
