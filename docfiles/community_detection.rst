Community Detection
===================

Community detection identifies groups of densely connected nodes within a network. In multilayer networks, this task becomes richer: communities can span layers, and nodes may belong to different communities in different layers.

Py3plex provides **wrappers for community detection algorithms** optimized for **multilayer networks**.

Understanding Community Detection in Multilayer Networks
----------------------------------------------------------

In single-layer networks, community detection is straightforward: find groups of nodes that are more connected to each other than to the rest of the network. Multilayer networks add complexity:

**Intra-layer vs. Inter-layer Communities:**

- **Intra-layer communities:** Dense groups within a single layer (e.g., friend groups within your Facebook network)
- **Inter-layer communities:** Groups that are consistent across layers (e.g., the same friend group appearing in Facebook, Twitter, and Instagram)

**Why This Matters:**

Finding communities that persist across layers reveals robust social structures. A group that only appears in one layer might be context-specific (work colleagues), while a group appearing in all layers indicates a strong, multi-context relationship (close friends).

Supported Algorithms
--------------------

Py3plex supports several community detection algorithms, each with different strengths:

- **Infomap** - **Information-theoretic approach**, uses random walk dynamics to find communities. Supports overlapping communities where nodes belong to multiple groups.
- **Louvain** - **Modularity optimization**, fast and scalable. Finds non-overlapping communities by maximizing network modularity.
- **Label Propagation** - **Semi-supervised learning**, propagates known labels to discover community boundaries.
- **NoRC (Node Ranking and Clustering)** - **PageRank-based hierarchical clustering**, uses random walk probabilities to identify community structure.

Basic Usage
-----------

**Louvain Algorithm:**

The Louvain algorithm is the most commonly used method due to its speed and accuracy. It works by optimizing modularity through iterative node reassignment:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    # Detect communities using Louvain
    # Returns a dictionary mapping node IDs to community IDs
    partition = cw.louvain_communities(network)
    
    # Analyze results
    from collections import Counter
    community_sizes = Counter(partition.values())
    print(f"Number of communities: {len(community_sizes)}")
    print(f"Largest community: {max(community_sizes.values())} nodes")
    print(f"Smallest community: {min(community_sizes.values())} nodes")

**Interpreting Louvain Results:**

The partition dictionary maps each node to a community ID (integer). Nodes with the same community ID belong to the same group. Typical results show a power-law distribution: a few large communities and many small ones.

**NoRC (Node Ranking and Clustering):**

NoRC uses PageRank probabilities to cluster nodes. It's particularly effective for networks with hierarchical community structure:

.. code-block:: python

    from py3plex.algorithms.community_detection.NoRC import NoRC_communities_main
    import networkx as nx
    
    # Create or load a graph
    G = nx.karate_club_graph()  # Famous benchmark network
    
    # Detect communities using k-means clustering
    # Try different numbers of communities to find optimal structure
    communities_kmeans = NoRC_communities_main(
        G,
        clustering_scheme="kmeans",     # Use k-means for final clustering
        verbose=True,                    # Show progress
        community_range=[2, 3, 5, 7, 10] # Number of communities to try
    )
    
    # Or use hierarchical clustering for dendrogram-style results
    communities_hierarchical = NoRC_communities_main(
        G,
        clustering_scheme="hierarchical",
        verbose=True,
        community_range=[2, 3, 5, 7, 10]
    )
    
    print(f"Best partition found: {len(set(communities_kmeans.values()))} communities")

**NoRC Parameters Explained:**

- ``clustering_scheme``: "kmeans" (faster, good for large networks) or "hierarchical" (more accurate, shows nested structure)
- ``parallel_step``: Number of parallel workers for PageRank computation. Default auto-detects based on CPU count.
- ``prob_threshold``: Minimum PageRank probability to include. Default 0.0005 filters out negligible contributions.
- ``community_range``: List of community counts to evaluate. The algorithm finds the best fit within this range.
- ``lag_threshold``: Early stopping after N iterations without improvement. Default 10 prevents overfitting.
- ``fine_range``: Range for fine-grained search around the optimal solution. Default 3 refines the final answer.

**Infomap Algorithm (Multiplex Networks):**

Infomap is particularly powerful for multiplex networks, where it can detect communities that span multiple layers:

.. note::

    Infomap requires an external binary that is no longer bundled with py3plex.
    
    **Options:**
    
    - Download from: https://www.mapequation.org/infomap/
    - Install via: ``pip install infomap``
    - Use Louvain (above) as a Python-only alternative

.. code-block:: python

    # Load multiplex network (same nodes, different relationship layers)
    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        "../datasets/simple_multiplex.edgelist", 
        directed=False, 
        input_type="multiplex_edges")
    
    # Infomap requires the binary to be installed
    # Either in PATH or specify full path to binary
    partition = cw.infomap_communities(
        network, 
        binary="infomap",   # Path to infomap binary
        multiplex=True,      # Enable multiplex mode
        verbose=True         # Show progress
    )
    
    # Results include cross-layer community assignments
    for node, community in list(partition.items())[:10]:
        print(f"Node {node}: Community {community}")

**When to Use Each Algorithm:**

- **Louvain:** Fast, scalable, good default choice. Best for large networks (>10k nodes) when speed matters.
- **Infomap:** Best for multiplex networks and when you need overlapping communities. More accurate but slower.
- **NoRC:** Best when you expect hierarchical structure or need to explore different granularities.
- **Label Propagation:** Best when you have partial ground truth labels and want to propagate them.

Visualizing Communities
-----------------------

Once communities are detected, visualize them to validate and interpret results:

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization.colors import colors_default
    import matplotlib.pyplot as plt
    
    # Get network for visualization
    network_colors, graph = network.get_layers(style="hairball")
    
    # Map communities to colors
    partition = cw.louvain_communities(network)
    unique_communities = list(set(partition.values()))
    color_map = {c: colors_default[i % len(colors_default)] 
                 for i, c in enumerate(unique_communities)}
    
    # Assign colors to nodes
    node_colors = [color_map[partition.get(node, 0)] for node in graph.nodes()]
    
    # Create visualization
    plt.figure(figsize=(12, 10))
    hairball_plot(graph, node_colors, layout_algorithm="force")
    plt.title(f"Network Communities ({len(unique_communities)} communities)")
    plt.savefig("communities.png", dpi=150, bbox_inches='tight')
    plt.show()

**What to Look For:**

- Well-separated color clusters indicate strong community structure
- Mixed colors suggest weaker boundaries or overlapping communities
- Isolated nodes often represent noise or require investigation

Examples
--------

See **detailed examples** for complete community detection workflows:

- ``example_community_detection.py`` - **Basic community detection** with Louvain and analysis
- ``example_community_multiplex.py`` - **Multiplex community detection** with Infomap
- ``example_community_visualization.py`` - **Visualizing communities** with custom colors
- ``example_community_comparison.py`` - **Comparing algorithms** on the same network
- ``example_modularity.py`` - **Modularity optimization** and quality metrics

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples

Further Reading
---------------

- :doc:`user_guide/community_detection` - Advanced community detection techniques
- :doc:`user_guide/visualization` - Visualization options for communities
- :doc:`getting_started/tutorial_10min` - Complete workflow including community detection
