10-Minute Tutorial
==================

Create a multilayer network, compute statistics, detect communities, and visualize—all in 10 minutes. This tutorial takes you from a blank environment to advanced multilayer analysis as a single runnable flow.

.. admonition:: 📓 Run this tutorial online
   :class: tip

   You can run this tutorial in your browser without any local setup:
   
   .. image:: https://colab.research.google.com/assets/colab-badge.svg
      :target: https://colab.research.google.com/github/SkBlaz/py3plex/blob/master/notebooks/tutorial_10min.ipynb
      :alt: Open in Google Colab
   
   Or download the full executable script: :download:`tutorial_10min.py <../../examples/getting_started/tutorial_10min.py>`

**You will learn:**

* Create multilayer networks from scratch and load from files
* Display network statistics and understand the multilayer model
* Compute layer-specific and multilayer metrics
* Query networks with the SQL-like DSL
* Detect communities across layers
* Generate random walks for embeddings
* Create publication-ready visualizations

Installation
------------

.. code-block:: bash

    python -m pip install py3plex

For Docker setup or optional dependencies, see :doc:`installation`.
Run inside a virtual environment to keep dependencies isolated.

----

Part 1: Your First Network (2 min)
----------------------------------

Create a simple multilayer network and explore its basic properties.

Create from scratch:

.. literalinclude:: ../../examples/getting_started/tutorial_10min.py
   :language: python
   :start-after: def example_1_create_network():
   :end-before: return network
   :dedent: 4

The complete executable version is available at ``examples/getting_started/tutorial_10min.py`` and produces the outputs shown below.

**Output:**

.. code-block:: text

    Number of nodes: 8
    Number of edges: 4
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'layer1': 3 nodes
      Layer 'layer2': 3 nodes

**Key concept:** The network has node-layer pairs representing the same node in different layers. For example, node 'A' appears as ``('A', 'layer1')`` and ``('A', 'layer2')``.

Visualize your network:

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    draw_multilayer_default([network], display=True)

Nodes are colored by layer. Edges connect nodes within and across layers.
Set ``display=False`` in headless environments and call ``plt.show()`` or ``plt.savefig(...)`` manually.

Load from file:

.. code-block:: python

    # For larger networks, load from files
    network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist.txt",
        input_type="multiedgelist",  # Format: source target layer
        directed=False  # Set to True for directed networks
    )
    network.basic_stats()

**Supported formats:** ``multiedgelist`` (source, target, layer), ``edgelist`` (source, target), ``gpickle``, ``gml``, ``graphml``. File paths in this tutorial are relative to the repository root.

----

Part 2: Basic Analysis (2 min)
------------------------------

Compute layer-specific metrics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Layer density: how connected is each layer?
    print(f"Friends density: {mls.layer_density(network, 'friends'):.3f}")
    print(f"Colleagues density: {mls.layer_density(network, 'colleagues'):.3f}")
    
    # Node activity: what fraction of layers does Bob appear in?
    print(f"Bob's activity: {mls.node_activity(network, 'Bob'):.3f}")

**Output:**

.. code-block:: text

    Friends density: 0.667
    Colleagues density: 0.667
    Bob's activity: 1.000

* **Density 0.667** — with 3 nodes in an undirected layer there are 3 possible edges; 2 exist here
* **Activity 1.0** — Bob appears in every available layer in this example

Query with the DSL:

Py3plex includes a SQL-like DSL for querying networks without manual iteration.

.. admonition:: DSL Example: Network Queries
   :class: dsl-example

   Use SQL-like queries for network exploration:

   .. code-block:: python

       from py3plex.dsl import execute_query, Q, L
       
       # String DSL syntax
       result = execute_query(network, 'SELECT nodes WHERE degree > 1')
       print(f"Found {result['count']} high-degree nodes")
       
       # Builder API (recommended for production)
       result = (
           Q.nodes()
            .from_layers(L["friends"])
            .where(degree__gt=1)
            .compute("betweenness_centrality")
            .execute(network)
       )

   ``Q`` builds queries and ``L`` selects layers. Both forms return a result object with counts, selected nodes, and any computed measures.

See :doc:`../user_guide/dsl` for complete DSL documentation.

Explore network structure:

.. code-block:: python

    # Iterate through nodes and edges
    for node in network.get_nodes(data=True):
        print(node)  # (('Alice', 'friends'), {'type': 'friends'})

    for edge in network.get_edges(data=True):
        print(edge)  # Edge with attributes

    # Get neighbors of a node in a specific layer
    neighbors = list(network.get_neighbors("Alice", layer_id="friends"))

Extract subnetworks:

.. code-block:: python

    # Single layer
    friends_layer = network.subnetwork(['friends'], subset_by="layers")

    # Specific nodes across all layers
    subset = network.subnetwork(['Alice', 'Bob'], subset_by="node_names")

    # Specific node-layer pairs
    pairs = network.subnetwork([('Alice', 'friends'), ('Bob', 'friends')], 
                               subset_by="node_layer_names")

Use ``subset_by`` to control whether you filter by layers, node names, or explicit node-layer tuples.
----

Part 3: Advanced Metrics (2 min)
--------------------------------

Layer-specific centrality (using NetworkX wrappers):

.. code-block:: python

    friends_layer = network.subnetwork(['friends'], subset_by="layers")
    degree_cent = friends_layer.monoplex_nx_wrapper("degree_centrality")
    betweenness = friends_layer.monoplex_nx_wrapper("betweenness_centrality")

Multilayer centrality:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality

    calc = MultilayerCentrality(network)
    ml_degree = calc.overlapping_degree_centrality(weighted=False)
    ml_betweenness = calc.multilayer_betweenness_centrality()

Multilayer statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

    density = mls.layer_density(network, 'friends')  # Edge density within a layer
    activity = mls.node_activity(network, node='Alice')  # Fraction of layers node appears in
    overlap = mls.edge_overlap(network, 'friends', 'colleagues')  # Shared edges between layers
    similarity = mls.layer_similarity(network, 'friends', 'colleagues', method='jaccard')

**Available statistics:** ``layer_density``, ``entropy_of_multiplexity``, ``node_activity``, ``edge_overlap``, ``layer_similarity``, ``algebraic_connectivity``, ``multilayer_clustering_coefficient``, and more.
``layer_density`` compares existing edges to the maximum possible within a layer; ``node_activity`` is the fraction of layers a node appears in; ``edge_overlap`` and ``layer_similarity`` compare relationships across layers.

----

Part 4: Community Detection (2 min)
-----------------------------------

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

    partition = louvain_multilayer(
        network,
        gamma=1.0,      # Resolution (higher = more communities)
        omega=1.0,      # Inter-layer coupling strength
        random_state=42
    )

    print(f"Communities: {len(set(partition.values()))}")
    
    from collections import Counter
    sizes = Counter(partition.values())
    print(f"Sizes: {dict(sizes)}")

``partition`` maps each node-layer pair to a community label. Tune ``gamma`` (resolution) and ``omega`` (inter-layer coupling) to control granularity; fix ``random_state`` for reproducible runs.
----

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

    # BFS-like (local): higher q biases walks to stay close
    walk_bfs = node2vec_walk(G, start, walk_length=20, p=1.0, q=2.0, seed=42)

    # DFS-like (explore): lower q encourages exploration
    walk_dfs = node2vec_walk(G, start, walk_length=20, p=1.0, q=0.5, seed=42)

``p`` controls the likelihood of returning to the previous node, while ``q`` biases walks toward breadth-first (higher) or depth-first (lower) exploration; keep ``seed`` fixed to reproduce results.

Generate walks for embeddings:

.. code-block:: python

    walks = generate_walks(G, num_walks=10, walk_length=10, p=1.0, q=1.0, seed=42)
    # Use with Word2Vec: model = Word2Vec([[str(n) for n in w] for w in walks])
    # Set seeds for reproducibility; tune p and q to balance local/global exploration.

----

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
    from collections import Counter

    top_communities = [c for c, _ in Counter(partition.values()).most_common(5)]
    color_map = dict(zip(top_communities, colors_default[:5]))
    node_colors = [color_map.get(partition.get(n), "gray") for n in network.get_nodes()]

    plt.figure(figsize=(10, 10))
    hairball_plot(graph, node_colors, layout_algorithm="force")
    plt.savefig("communities.png", dpi=150, bbox_inches='tight')
    plt.close()

``get_layers(style="hairball")`` returns a NetworkX graph and color mapping ready for ``hairball_plot``; saving figures makes headless runs reproducible.
----

Key Concepts
------------

Understand these concepts to navigate py3plex effectively:

1. **Node-layer pairs:** Nodes are ``(node_id, layer_id)`` tuples. Alice in friends is distinct from Alice in colleagues, so each context keeps its own edges.

2. **Layer boundaries:** Every layer represents a relationship type (friends, colleagues, transit, etc.). Metrics respect layer boundaries, surfacing patterns that disappear in single-layer projections.

3. **NetworkX compatibility:** py3plex wraps NetworkX internally; use ``network.core_network`` directly with NetworkX algorithms when needed.

4. **Cross-layer measures:** Node activity and edge overlap quantify how entities and links span layers; use them to compare behaviors across contexts.

----

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
    friends_layer = network.subnetwork(['friends'], subset_by="layers")
    degree_cent = friends_layer.monoplex_nx_wrapper("degree_centrality")
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

----

DSL: Query Networks Like SQL
----------------------------

The SQL-like DSL makes many analysis tasks simpler and more intuitive:

.. admonition:: DSL Example: Advanced Analysis
   :class: dsl-example

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Find top influential nodes
       result = (
           Q.nodes()
            .where(degree__gt=3)
            .compute("betweenness_centrality", "pagerank")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

       # Display as DataFrame
       df = result.to_pandas()
       print(df)

       # Compare layers
       for layer_id in ['friends', 'colleagues']:
           layer_result = (
               Q.nodes()
                .from_layers(L[layer_id])
                .compute("degree")
                .execute(network)
           )
           print(f"Layer {layer_id}: {layer_result.count} nodes")

   See :doc:`../user_guide/dsl` for comprehensive DSL documentation!

----

Common Issues
-------------

**File Not Found:** Use absolute paths or run from repository root.

**Visualization not showing:** In Jupyter, add ``%matplotlib inline``. In scripts, use ``plt.show()`` or save to file.

**Missing dependencies:** Install extras with ``python -m pip install "py3plex[viz,algos]"``

----

Next Steps
----------

**Continue Learning:**

* :doc:`installation` — Optional dependencies and setup options
* :doc:`common_issues` — Solutions to common problems

**Advanced Topics:**

* :doc:`../user_guide/recipes_and_workflows` — Ready-to-use analysis workflows and patterns
* :doc:`../user_guide/dsl` — SQL-like DSL for querying multilayer networks
* :doc:`../user_guide/graph_ops` — Dplyr-style chainable graph operations

**Deep Dive:**

* :doc:`../concepts/multilayer_networks_101` — Theory and concepts
* :doc:`../user_guide/statistics` — All available statistics
* :doc:`../user_guide/community_detection` — Parameter tuning
* :doc:`../user_guide/visualization` — Advanced visualization

**Examples:**

* ``examples/`` directory — 50+ working examples
* :doc:`../examples/index` — Annotated example gallery
