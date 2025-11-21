10-Minute Tutorial: Getting Started with py3plex
================================================

This tutorial provides a quick introduction to py3plex, covering the most common tasks for working with multilayer networks.

What You Will Learn
-------------------

In 10 minutes, you will learn how to:

1. Create and load multilayer networks
2. Perform basic network analysis
3. Compute multilayer statistics
4. Detect communities
5. Perform random walks for embeddings
6. Visualize networks

Prerequisites
-------------

Make sure py3plex is installed:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

1. Creating Your First Multilayer Network (2 minutes)
------------------------------------------------------

Start by creating a simple multilayer network from scratch:

.. code-block:: python

    from py3plex.core import multinet

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges within layers (this automatically creates nodes)
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
        ['B', 'layer2', 'D', 'layer2', 1]
    ], input_type="list")

    # Display basic statistics
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 5
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 5
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'layer1': 3 nodes
      Layer 'layer2': 3 nodes

2. Loading Networks from Files (1 minute)
------------------------------------------

py3plex supports multiple input formats. Here is how to load from an edge list:

.. code-block:: python

    from py3plex.core import multinet

    # Load from a multiedgelist file
    # Format: source target layer
    network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist.txt",
        input_type="multiedgelist",
        directed=False
    )

    # Check what we loaded
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 5
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 5
    Number of unique node IDs (across all layers): 5
    Nodes per layer:
      Layer '1': 3 nodes
      Layer '2': 2 nodes

**Supported formats:**

- ``multiedgelist`` - source, target, layer
- ``edgelist`` - simple source, target pairs
- ``gpickle`` - NetworkX pickle format
- ``gml``, ``graphml`` - standard graph formats

3. Exploring Network Structure (2 minutes)
-------------------------------------------

Iterate Through Nodes and Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Loop through all nodes
    print("Nodes:")
    for node in network.get_nodes(data=True):
        print(node)

    # Loop through all edges
    print("\nEdges:")
    for edge in network.get_edges(data=True):
        print(edge)

    # Get neighbors of a specific node in a layer
    node_of_interest = "1"
    layer_id = "1"
    neighbors = list(network.get_neighbors(node_of_interest, layer_id=layer_id))
    print(f"\nNeighbors of {node_of_interest} in layer {layer_id}:", neighbors)

**Output (first few items):**

.. code-block:: text

    Nodes (first 5):
      (('1', '1'), {'type': '1'})
      (('2', '1'), {'type': '1'})
      (('6', '2'), {'type': '2'})
      (('3', '1'), {'type': '1'})
      (('5', '2'), {'type': '2'})
    
    Edges (first 5):
      (('1', '1'), ('2', '1'), {'weight': '1'})
      (('1', '1'), ('3', '1'), {'weight': '1'})
      (('2', '1'), ('6', '2'), {'weight': '1'})
      (('3', '1'), ('5', '2'), {'weight': '1'})
    
    Neighbors of 1 in layer 1: [('2', '1'), ('3', '1')]

Extract Subnetworks
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Extract a single layer
    layer_1 = network.subnetwork(['1'], subset_by="layers")
    print("Layer 1 nodes:", list(layer_1.get_nodes()))

    # Extract specific nodes
    node_subset = network.subnetwork(['1', '2'], subset_by="node_names")
    print("Node subset:", list(node_subset.get_nodes()))

    # Extract specific node-layer pairs
    specific_pairs = network.subnetwork(
        [('1', '1'), ('2', '1')], 
        subset_by="node_layer_names"
    )
    print("Specific pairs:", list(specific_pairs.get_nodes()))

**Output:**

.. code-block:: text

    Layer 1 nodes: 3 nodes
    Node subset: 2 node-layer pairs
    Specific pairs: [('2', '1'), ('1', '1')]

4. Computing Network Metrics (2 minutes)
-----------------------------------------

Basic Centrality Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get a single layer as NetworkX graph
    layer_1 = network.subnetwork(['1'], subset_by="layers")

    # Compute degree centrality using NetworkX wrapper
    degree_centrality = layer_1.monoplex_nx_wrapper("degree_centrality")
    print("Degree centrality:", degree_centrality)

    # Compute betweenness centrality
    betweenness = layer_1.monoplex_nx_wrapper("betweenness_centrality")
    print("Betweenness centrality:", betweenness)

**Output (top nodes shown):**

.. code-block:: text

    Degree centrality (first 5):
      ('1', '1'): 1.0000
      ('2', '1'): 0.5000
      ('3', '1'): 0.5000
    
    Betweenness centrality (first 5):
      ('1', '1'): 1.0000
      ('2', '1'): 0.0000
      ('3', '1'): 0.0000

Multilayer Centrality
~~~~~~~~~~~~~~~~~~~~~

For multilayer-specific centrality measures:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality

    # Initialize centrality calculator
    calc = MultilayerCentrality(network)
    
    # Compute multilayer degree centrality (overlapping degree at node level)
    ml_degree = calc.overlapping_degree_centrality(weighted=False)
    print("Multilayer degree centrality:", ml_degree)

    # Compute multilayer betweenness centrality
    ml_betweenness = calc.multilayer_betweenness_centrality()
    print("Multilayer betweenness centrality:", ml_betweenness)

**Output (top nodes shown):**

.. code-block:: text

    Multilayer degree centrality (first 5):
      1: 2.0000
      2: 1.0000
      3: 1.0000
      5: 0.0000
      6: 0.0000
    
    Multilayer betweenness centrality (first 5):
      ('1', '1'): 0.6667
      ('2', '1'): 0.5000
      ('3', '1'): 0.5000
      ('6', '2'): 0.0000
      ('5', '2'): 0.0000

5. Multilayer Network Statistics (2 minutes)
---------------------------------------------

py3plex provides specialized statistics for analyzing multilayer networks. Here are the most commonly used:

Basic Layer Statistics
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # Measure how densely connected each layer is
    density_layer1 = mls.layer_density(network, 'layer1')
    density_layer2 = mls.layer_density(network, 'layer2')
    print(f"Layer 1 density: {density_layer1:.3f}")
    print(f"Layer 2 density: {density_layer2:.3f}")

    # Measure diversity across layers
    entropy = mls.entropy_of_multiplexity(network)
    print(f"Layer diversity (entropy): {entropy:.3f} bits")

**Output:**

.. code-block:: text

    Layer 1 density: 0.667
    Layer 2 density: 0.000
    Layer diversity (entropy): 0.000 bits

Node-Level Statistics
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Compute node activity (how many layers a node participates in)
    activity = mls.node_activity(network, node='1')
    print(f"Node activity for node 1: {activity:.3f}")

**Output:**

.. code-block:: text

    Node activity for node 1: 0.500

Network-Level Statistics
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Measure how much layers differ in structure (edge overlap)
    edge_overlap_value = mls.edge_overlap(network, 'layer1', 'layer2')
    print(f"Edge overlap between layers: {edge_overlap_value:.3f}")
    
    # Measure layer similarity using Jaccard index
    jaccard = mls.layer_similarity(network, 'layer1', 'layer2', method='jaccard')
    print(f"Jaccard similarity between layers: {jaccard:.3f}")

**Output:**

.. code-block:: text

    Edge overlap between layers: 0.000
    Jaccard similarity between layers: 0.000

**Available statistics:**

See the ``py3plex.algorithms.statistics.multilayer_statistics`` module for all available statistics including:

- ``layer_density`` - Density of edges within a layer
- ``entropy_of_multiplexity`` - Diversity across layers
- ``node_activity`` - Number of layers a node participates in
- ``edge_overlap`` - Edge overlap between layers
- ``layer_similarity`` - Similarity between layers (Jaccard, Pearson, etc.)
- ``algebraic_connectivity`` - Connectivity measure from Laplacian
- ``community_participation_coefficient`` - How communities span layers
- ``interdependence`` - Layer interdependence measure
- ``multilayer_clustering_coefficient`` - Clustering in multilayer context
- ``multiplex_betweenness_centrality`` - Betweenness in multiplex networks
- ``multiplex_closeness_centrality`` - Closeness in multiplex networks
- And more...

6. Community Detection (2 minutes)
----------------------------------

py3plex provides Louvain-based community detection that works across multiple layers:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )

    # Detect communities using multilayer Louvain
    partition = louvain_multilayer(
        network,
        gamma=1.0,      # Resolution parameter
        omega=1.0,      # Inter-layer coupling
        random_state=42 # For reproducibility
    )

    # Examine results
    print("Number of communities:", len(set(partition.values())))
    print("\nNode assignments (first 10):")
    for node, community in list(partition.items())[:10]:
        print(f"  Node {node}: Community {community}")

    # Count community sizes
    from collections import Counter
    community_sizes = Counter(partition.values())
    print("\nCommunity sizes:", dict(community_sizes))

**Output:**

.. code-block:: text

    Number of communities: 3
    
    Node assignments (first 10):
      Node ('1', '1'): Community 0
      Node ('2', '1'): Community 0
      Node ('6', '2'): Community 1
      Node ('3', '1'): Community 0
      Node ('5', '2'): Community 2
    
    Community sizes (top 5): {0: 3, 1: 1, 2: 1}

**Note:** The ``louvain_multilayer`` function performs community detection across all layers simultaneously, taking into account both intra-layer and inter-layer connections. Parameters:

- ``gamma``: Resolution parameter (higher values = more communities)
- ``omega``: Inter-layer coupling strength (higher values = more consistency across layers)
- ``random_state``: Seed for reproducibility

7. Random Walks (1 minute)
---------------------------

Random walks are fundamental for graph embeddings (Node2Vec, DeepWalk) and analyzing network structure:

Basic Random Walk
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import basic_random_walk

    # Load a network
    network = multinet.multi_layer_network().load_network(
        "datasets/test.edgelist",
        input_type="edgelist",
        directed=False
    )
    G = network.core_network
    
    # Perform a random walk
    start_node = list(G.nodes())[0]
    walk = basic_random_walk(
        G, 
        start_node=start_node, 
        walk_length=10, 
        weighted=True,
        seed=42
    )
    print(f"Random walk: {walk[:5]}... (length: {len(walk)})")

**Output:**

.. code-block:: text

    Random walk from ('0', 'null'): [('0', 'null'), ('1', 'null'), ('4872', 'null'), ('786', 'null'), ('5382', 'null')] (length: 11)

Node2Vec Biased Walks
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import node2vec_walk

    # Biased walk with Node2Vec parameters
    # p: return parameter (higher = less likely to return)
    # q: in-out parameter (higher = stay local, lower = explore)
    
    walk_bfs = node2vec_walk(
        G, start_node, walk_length=20, 
        p=1.0, q=2.0,  # BFS-like (local)
        seed=42
    )
    
    walk_dfs = node2vec_walk(
        G, start_node, walk_length=20,
        p=1.0, q=0.5,  # DFS-like (explore)
        seed=42
    )

**Output (first 10 nodes of each walk):**

.. code-block:: text

    Node2Vec BFS-like walk: [('0', 'null'), ('1', 'null'), ('5829', 'null'), ('1', 'null'), ('3842', 'null'), ('1', 'null'), ('6364', 'null'), ('1', 'null'), ('3422', 'null'), ('1', 'null')]
    Node2Vec DFS-like walk: [('0', 'null'), ('1', 'null'), ('4872', 'null'), ('786', 'null'), ('5382', 'null'), ('260', 'null'), ('2861', 'null'), ('260', 'null'), ('5128', 'null'), ('260', 'null')]

Generating Multiple Walks
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks

    # Generate walks from all nodes for embeddings
    walks = generate_walks(
        G,
        num_walks=10,      # Walks per node
        walk_length=10,    # Steps per walk
        p=1.0, q=1.0,      # Node2Vec parameters
        seed=42
    )
    print(f"Generated {len(walks)} walks")
    
    # Use with Word2Vec for node embeddings
    # walks_str = [[str(node) for node in walk] for walk in walks]
    # model = Word2Vec(walks_str, vector_size=128, window=10)

**Output:**

.. code-block:: text

    Generated 63870 walks
    Example walk: [('4528', 'null'), ('2611', 'null'), ('4267', 'null'), ('2611', 'null'), ('2894', 'null'), ('2611', 'null'), ('6234', 'null'), ('2611', 'null'), ('3073', 'null'), ('479', 'null'), ('3125', 'null')]

**Key parameters:**

- ``walk_length``: Number of steps in the walk
- ``p``: Return parameter (controls backtracking)
- ``q``: In-out parameter (controls exploration vs. local search)
- ``weighted``: Use edge weights in sampling
- ``seed``: Random seed for reproducibility

8. Basic Visualization (1 minute)
----------------------------------

Visualize your multilayer network:

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib.pyplot as plt

    # Get network for visualization
    network_colors, graph = network.get_layers(style="hairball")

    # Create a simple hairball plot
    plt.figure(figsize=(10, 10))
    hairball_plot(
        graph,
        network_colors,
        layout_algorithm="force",
        layout_parameters={"iterations": 50}
    )
    plt.title("Multilayer Network Visualization")
    plt.savefig("my_network.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("Visualization saved to my_network.png")

**Output:**

.. code-block:: text

    Visualization saved to my_network.png

For more advanced visualizations with community colors:

.. code-block:: python

    from py3plex.visualization.colors import colors_default

    # Get communities
    partition = louvain_multilayer(network)

    # Select top N communities
    top_n = 5
    community_counts = Counter(partition.values())
    top_communities = [c for c, _ in community_counts.most_common(top_n)]

    # Assign colors
    color_map = dict(zip(
        top_communities,
        colors_default[:top_n]
    ))

    network_colors = [
        color_map.get(partition.get(node), "gray")
        for node in network.get_nodes()
    ]

    # Plot with community colors
    plt.figure(figsize=(10, 10))
    hairball_plot(graph, network_colors, layout_algorithm="force")
    plt.title("Multilayer Network with Communities")
    plt.savefig("my_network_communities.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("Community visualization saved to my_network_communities.png")

**Output:**

.. code-block:: text

    Community visualization saved to my_network_communities.png

Complete Example: Putting It All Together
------------------------------------------

Here's a complete workflow:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization.colors import colors_default
    from collections import Counter
    import matplotlib.pyplot as plt

    # Load network
    network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist2.txt",
        input_type="multiedgelist",
        directed=False
    )

    # Analyze structure
    print("=== Network Statistics ===")
    network.basic_stats()

    # Compute centrality for one layer
    layer_1 = network.subnetwork(['1'], subset_by="layers")
    degree_cent = layer_1.monoplex_nx_wrapper("degree_centrality")
    print("\n=== Top 5 Nodes by Degree (Layer 1) ===")
    for node, score in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{node}: {score:.3f}")

    # Detect communities using multilayer method
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    print(f"\n=== Communities ===")
    print(f"Number of communities: {len(set(partition.values()))}")

    # Visualize with communities
    network_colors, graph = network.get_layers(style="hairball")
    top_n = 3
    community_counts = Counter(partition.values())
    top_communities = [c for c, _ in community_counts.most_common(top_n)]
    color_map = dict(zip(top_communities, colors_default[:top_n]))
    network_colors = [
        color_map.get(partition.get(node), "lightgray")
        for node in network.get_nodes()
    ]

    plt.figure(figsize=(12, 12))
    hairball_plot(graph, network_colors, layout_algorithm="force")
    plt.title("Multilayer Network Analysis")
    plt.savefig("complete_analysis.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("\nComplete analysis saved to complete_analysis.png")

**Output:**

.. code-block:: text

    === Network Statistics ===
    Number of nodes: 184
    Number of edges: 1691
    Number of unique nodes (as node-layer tuples): 184
    Number of unique node IDs (across all layers): 46
    Nodes per layer:
      Layer '1': 46 nodes
      Layer '2': 46 nodes
      Layer '3': 46 nodes
      Layer '4': 46 nodes
    
    === Top 5 Nodes by Degree (Layer 1) ===
    ('15', '1'): 0.244
    ('7', '1'): 0.244
    ('27', '1'): 0.244
    ('28', '1'): 0.244
    ('1', '1'): 0.244
    
    === Communities ===
    Number of communities: 46
    
    Complete analysis saved to complete_analysis.png

Next Steps
----------

Now that you've completed this tutorial, explore more advanced features:

- **Multilayer Statistics**: Explore all available statistics in ``py3plex.algorithms.statistics.multilayer_statistics``
- **Multilayer Centrality**: See examples in ``examples/centrality_and_statistics/``
- **More Examples**: Check the ``examples/`` directory for 40+ examples
- **Full Documentation**: Visit https://skblaz.github.io/py3plex/

Common Issues
-------------

File Not Found
~~~~~~~~~~~~~~

Make sure you're running from the repository root or use absolute paths:

.. code-block:: python

    import os
    base_path = "/path/to/py3plex"
    network = multinet.multi_layer_network().load_network(
        os.path.join(base_path, "datasets/multiedgelist.txt"),
        input_type="multiedgelist",
        directed=False
    )

Visualization Not Showing
~~~~~~~~~~~~~~~~~~~~~~~~~~

If using Jupyter, add ``%matplotlib inline`` at the top of your notebook. For scripts, use ``plt.show()`` instead of ``plt.close()``.

Missing Dependencies
~~~~~~~~~~~~~~~~~~~~

Some features require optional dependencies:

.. code-block:: bash

    # For advanced visualization
    pip install plotly

    # For community detection with Infomap
    pip install infomap

    # For all extras
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]

Tips for Success
----------------

1. **Start Simple**: Begin with small test networks before scaling to large datasets
2. **Check Stats**: Always run ``basic_stats()`` after loading to verify your network
3. **Use Subnetworks**: Extract layers or subsets for faster prototyping
4. **Seed Your Random**: Use ``seed`` parameters in algorithms for reproducible results
5. **Visualize Early**: Quick plots help catch data loading issues early

Happy network analysis! 

