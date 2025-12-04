10-Minute Tutorial
==================

Build a complete multilayer network analysis pipeline: load data, compute metrics, detect communities, and visualize.

**You will learn:**

* Load networks from files
* Navigate and extract subnetworks
* Compute centrality and multilayer statistics
* Detect communities across layers
* Generate random walks for embeddings
* Create visualizations

Prerequisites
-------------

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

----

Part 1: Loading Networks (2 min)
--------------------------------

Create from scratch:

.. code-block:: python

    from py3plex.core import multinet

    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
        ['B', 'layer2', 'D', 'layer2', 1]
    ], input_type="list")
    network.basic_stats()

Load from file:

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist.txt",
        input_type="multiedgelist",  # Format: source target layer
        directed=False  # Set to True for directed networks
    )
    network.basic_stats()

**Supported formats:** ``multiedgelist`` (source, target, layer), ``edgelist`` (source, target), ``gpickle``, ``gml``, ``graphml``

Part 2: Exploring Structure (2 min)
-----------------------------------

Iterate through nodes and edges:

.. code-block:: python

    for node in network.get_nodes(data=True):
        print(node)  # (('1', '1'), {'type': '1'})

    for edge in network.get_edges(data=True):
        print(edge)  # (('1', '1'), ('2', '1'), {'weight': '1'})

    neighbors = list(network.get_neighbors("1", layer_id="1"))

Extract subnetworks:

.. code-block:: python

    # Single layer
    layer_1 = network.subnetwork(['1'], subset_by="layers")

    # Specific nodes across all layers
    subset = network.subnetwork(['1', '2'], subset_by="node_names")

    # Specific node-layer pairs
    pairs = network.subnetwork([('1', '1'), ('2', '1')], subset_by="node_layer_names")

Part 3: Computing Metrics (2 min)
---------------------------------

Layer-specific centrality (using NetworkX):

.. code-block:: python

    layer_1 = network.subnetwork(['1'], subset_by="layers")
    degree_cent = layer_1.monoplex_nx_wrapper("degree_centrality")
    betweenness = layer_1.monoplex_nx_wrapper("betweenness_centrality")

Multilayer centrality:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality

    calc = MultilayerCentrality(network)
    ml_degree = calc.overlapping_degree_centrality(weighted=False)
    ml_betweenness = calc.multilayer_betweenness_centrality()

Multilayer statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

    density = mls.layer_density(network, 'layer1')  # Edge density within a layer
    activity = mls.node_activity(network, node='1')  # Fraction of layers node appears in
    overlap = mls.edge_overlap(network, 'layer1', 'layer2')  # Shared edges between layers
    similarity = mls.layer_similarity(network, 'layer1', 'layer2', method='jaccard')

**Available statistics:** ``layer_density``, ``entropy_of_multiplexity``, ``node_activity``, ``edge_overlap``, ``layer_similarity``, ``algebraic_connectivity``, ``multilayer_clustering_coefficient``, and more.

Part 4: Community Detection (2 min)
-----------------------------------

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

    partition = louvain_multilayer(
        network,
        gamma=1.0,      # Resolution (higher = more communities)
        omega=1.0,      # Inter-layer coupling
        random_state=42
    )

    print(f"Communities: {len(set(partition.values()))}")
    
    from collections import Counter
    sizes = Counter(partition.values())
    print(f"Sizes: {dict(sizes)}")

Part 5: Random Walks (1 min)
----------------------------

Basic walk:

.. code-block:: python

    from py3plex.algorithms.general.walkers import basic_random_walk, node2vec_walk, generate_walks

    G = network.core_network
    start = list(G.nodes())[0]

    walk = basic_random_walk(G, start_node=start, walk_length=10, seed=42)

Node2Vec biased walks:

.. code-block:: python

    # BFS-like (local)
    walk_bfs = node2vec_walk(G, start, walk_length=20, p=1.0, q=2.0, seed=42)

    # DFS-like (explore)
    walk_dfs = node2vec_walk(G, start, walk_length=20, p=1.0, q=0.5, seed=42)

Generate walks for embeddings:

.. code-block:: python

    walks = generate_walks(G, num_walks=10, walk_length=10, p=1.0, q=1.0, seed=42)
    # Use with Word2Vec: model = Word2Vec([[str(n) for n in w] for w in walks])

Part 6: Visualization (1 min)
-----------------------------

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib.pyplot as plt

    network_colors, graph = network.get_layers(style="hairball")

    plt.figure(figsize=(10, 10))
    hairball_plot(graph, network_colors, layout_algorithm="force")
    plt.savefig("network.png", dpi=150, bbox_inches='tight')
    plt.close()

With community colors:

.. code-block:: python

    from py3plex.visualization.colors import colors_default

    top_communities = [c for c, _ in Counter(partition.values()).most_common(5)]
    color_map = dict(zip(top_communities, colors_default[:5]))
    node_colors = [color_map.get(partition.get(n), "gray") for n in network.get_nodes()]

    plt.figure(figsize=(10, 10))
    hairball_plot(graph, node_colors, layout_algorithm="force")
    plt.savefig("communities.png", dpi=150, bbox_inches='tight')
    plt.close()

Complete Example
----------------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization.colors import colors_default
    from collections import Counter
    import matplotlib.pyplot as plt

    # Load
    network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist2.txt",
        input_type="multiedgelist",
        directed=False
    )
    network.basic_stats()

    # Analyze
    layer_1 = network.subnetwork(['1'], subset_by="layers")
    degree_cent = layer_1.monoplex_nx_wrapper("degree_centrality")
    print("Top 5 by degree:", sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5])

    # Detect communities
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    print(f"Communities: {len(set(partition.values()))}")

    # Visualize
    network_colors, graph = network.get_layers(style="hairball")
    top_communities = [c for c, _ in Counter(partition.values()).most_common(3)]
    color_map = dict(zip(top_communities, colors_default[:3]))
    node_colors = [color_map.get(partition.get(n), "lightgray") for n in network.get_nodes()]

    plt.figure(figsize=(12, 12))
    hairball_plot(graph, node_colors, layout_algorithm="force")
    plt.savefig("analysis.png", dpi=150, bbox_inches='tight')
    plt.close()

Common Issues
-------------

**File Not Found:** Use absolute paths or run from repository root.

**Visualization not showing:** In Jupyter, add ``%matplotlib inline``. In scripts, use ``plt.show()`` or save to file.

**Missing dependencies:** Install extras with ``pip install git+...#egg=py3plex[viz,algos]``

Next Steps
----------

* :doc:`../concepts/multilayer_networks_101` — Theory and concepts
* :doc:`../user_guide/statistics` — All available statistics
* :doc:`../user_guide/community_detection` — Parameter tuning
* :doc:`../user_guide/visualization` — Advanced visualization
* ``examples/`` — 80+ working examples

