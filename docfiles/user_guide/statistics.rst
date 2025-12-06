Network Statistics
==================

*How to measure and compare the structure of your multilayer network.*

.. admonition:: DSL for Quick Statistics
   :class: dsl-example

   Compute statistics efficiently with the DSL:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Compute degree and clustering for all nodes
       stats = (
           Q.nodes()
            .compute("degree", "clustering")
            .execute(network)
       )

       # Compare layers
       for layer in ["layer1", "layer2", "layer3"]:
           result = (
               Q.nodes()
                .from_layers(L[layer])
                .compute("degree")
                .execute(network)
           )
           df = result.to_pandas()
           print(f"{layer}: avg degree = {df['degree'].mean():.2f}")

   DSL makes comparative analysis straightforward!

----

Once you've loaded a multilayer network, the next question is: *what does it look like?* This chapter shows you how to compute statistics that answer fundamental questions about your network's structure:

- **How dense is each layer?** Sparse layers may indicate missing data or genuine sparsity.
- **Who participates in multiple contexts?** High-activity nodes may be bridges or hubs.
- **How similar are your layers?** Similar layers might be redundant; dissimilar layers reveal complementary information.
- **What patterns emerge across layers?** Metrics like edge overlap and inter-layer degree correlation reveal cross-layer structure.

py3plex provides three levels of network statistics:

1. **Global Statistics** — Whole network properties (density, clustering, etc.)
2. **Layer-Specific Statistics** — Per-layer measures and comparisons
3. **Node-Level Statistics** — Node activity and participation across layers

For centrality measures (degree, betweenness, PageRank, etc.), see :doc:`../concepts/algorithm_landscape`.

----

Basic Network Statistics
------------------------

Quick Stats
~~~~~~~~~~~

The fastest way to get basic information:

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist", input_type="multiedgelist"
    )
    
    # Display comprehensive stats
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 184
    Number of edges: 1691
    Number of unique nodes (as node-layer tuples): 184
    Number of unique node IDs (across all layers): 46
    Nodes per layer:
      Layer '1': 46 nodes
      Layer '2': 46 nodes
      Layer '3': 46 nodes
      Layer '4': 46 nodes

Manual Counting
~~~~~~~~~~~~~~~

.. code-block:: python

    # Count elements
    num_nodes = len(list(network.get_nodes()))
    num_edges = len(list(network.get_edges()))
    num_layers = len(network.get_layers())
    
    # Unique node IDs (across all layers)
    unique_nodes = set()
    for node, layer in network.get_nodes():
        unique_nodes.add(node)
    num_unique_nodes = len(unique_nodes)
    
    print(f"Nodes (node-layer pairs): {num_nodes}")
    print(f"Edges: {num_edges}")
    print(f"Layers: {num_layers}")
    print(f"Unique node IDs: {num_unique_nodes}")

Layer-Specific Statistics
--------------------------

The ``multilayer_statistics`` module provides comprehensive statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls

Layer Density
~~~~~~~~~~~~~

**Definition:** Fraction of possible edges that exist in a layer.

**Formula:** :math:`density = \frac{2m}{n(n-1)}` for undirected graphs

**Use case:** Measure how connected a layer is.

.. code-block:: python

    # Density of individual layers
    density_layer1 = mls.layer_density(network, 'layer1')
    density_layer2 = mls.layer_density(network, 'layer2')
    
    print(f"Layer 1 density: {density_layer1:.4f}")
    print(f"Layer 2 density: {density_layer2:.4f}")

**Interpretation:**

* 0.0 = No edges (empty layer)
* 1.0 = Complete graph (all possible edges exist)
* Typical real-world networks: 0.001 - 0.1

Layer Similarity
~~~~~~~~~~~~~~~~

**Definition:** How similar two layers are in structure.

**Methods:** Jaccard index, Pearson correlation, cosine similarity

**Use case:** Identify redundant or complementary layers.

.. code-block:: python

    # Jaccard similarity (based on edges)
    jaccard = mls.layer_similarity(
        network, 'layer1', 'layer2', method='jaccard'
    )
    
    # Pearson correlation
    pearson = mls.layer_similarity(
        network, 'layer1', 'layer2', method='pearson'
    )
    
    print(f"Jaccard similarity: {jaccard:.4f}")
    print(f"Pearson correlation: {pearson:.4f}")

**Interpretation:**

* 1.0 = Identical layers
* 0.0 = Completely different
* Negative values (Pearson) = Anti-correlated

Edge Overlap
~~~~~~~~~~~~

**Definition:** Fraction of edges that appear in both layers.

**Use case:** Measure redundancy between layers.

.. code-block:: python

    overlap = mls.edge_overlap(network, 'layer1', 'layer2')
    print(f"Edge overlap: {overlap:.4f}")

**Interpretation:**

* 1.0 = All edges in common
* 0.0 = No edges in common

Inter-Layer Degree Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Correlation between node degrees in different layers.

**Use case:** Determine if "hubs" in one layer are hubs in another.

.. code-block:: python

    correlation = mls.inter_layer_degree_correlation(
        network, 'layer1', 'layer2'
    )
    print(f"Degree correlation: {correlation:.4f}")

**Interpretation:**

* 1.0 = Perfect positive correlation (hubs in layer1 are hubs in layer2)
* 0.0 = No correlation
* -1.0 = Perfect negative correlation

Node-Level Statistics
---------------------

Node Activity
~~~~~~~~~~~~~

**Definition:** Fraction of layers in which a node appears.

**Use case:** Identify nodes that participate in multiple contexts.

.. code-block:: python

    # Activity for a single node
    activity_alice = mls.node_activity(network, 'Alice')
    print(f"Alice's activity: {activity_alice:.4f}")
    
    # Compute for all nodes
    all_activities = {}
    unique_nodes = set(node for node, layer in network.get_nodes())
    for node in unique_nodes:
        all_activities[node] = mls.node_activity(network, node)
    
    # Top 5 most active nodes
    top_active = sorted(all_activities.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Most active nodes:", top_active)

**Interpretation:**

* 1.0 = Node appears in all layers
* 0.5 = Node appears in half of layers
* Close to 0.0 = Node appears in few layers

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Node importance considering activity across layers.

**Use case:** Find nodes that are important across multiple layers.

.. code-block:: python

    # Versatility based on degree
    versatility_degree = mls.versatility_centrality(
        network, centrality_type='degree'
    )
    
    # Versatility based on betweenness
    versatility_betweenness = mls.versatility_centrality(
        network, centrality_type='betweenness'
    )
    
    # Top versatile nodes
    top_versatile = sorted(
        versatility_degree.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    print("Top 10 versatile nodes:", top_versatile)

**Interpretation:**

* Higher values = More important across multiple layers
* Combines centrality within layers with cross-layer participation

Participation Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Measures how evenly a node's connections are distributed across layers.

**Use case:** Identify nodes that bridge different layers.

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )
    
    # Detect communities first
    partition = louvain_multilayer(network)
    
    # Compute participation coefficient
    participation = mls.community_participation_coefficient(network, partition)
    
    # Top bridging nodes
    top_bridging = sorted(
        participation.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    print("Top bridging nodes:", top_bridging)

**Interpretation:**

* 1.0 = Connections evenly distributed across layers
* 0.0 = All connections in one layer

Network-Level Statistics
------------------------

Entropy of Multiplexity
~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Measures layer diversity (how evenly nodes/edges are distributed across layers).

**Use case:** Quantify structural diversity of the multilayer network.

.. code-block:: python

    entropy = mls.entropy_of_multiplexity(network)
    print(f"Entropy of multiplexity: {entropy:.4f} bits")

**Interpretation:**

* 0.0 = All activity in one layer (no diversity)
* Higher values = More evenly distributed across layers
* Maximum = log₂(number of layers)

Algebraic Connectivity
~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Second smallest eigenvalue of the Laplacian matrix.

**Use case:** Measure network robustness (higher = more robust).

.. code-block:: python

    algebraic_conn = mls.algebraic_connectivity(network, 'layer1')
    print(f"Algebraic connectivity: {algebraic_conn:.4f}")

**Interpretation:**

* 0.0 = Disconnected network
* Higher values = Better connectivity and robustness

Multilayer Clustering Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Extension of clustering coefficient to multilayer networks.

**Use case:** Measure local cohesion across layers.

.. code-block:: python

    clustering = mls.multilayer_clustering_coefficient(network)
    print(f"Multilayer clustering: {clustering:.4f}")

**Interpretation:**

* 1.0 = Every node's neighbors form a clique
* 0.0 = No clustering (tree-like structure)

Using NetworkX Statistics
--------------------------

Since py3plex networks are NetworkX graphs, you can use any NetworkX statistic:

Basic NetworkX Metrics
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    G = network.core_network
    
    # Clustering coefficient
    clustering = nx.average_clustering(G)
    print(f"Average clustering: {clustering:.4f}")
    
    # Transitivity
    transitivity = nx.transitivity(G)
    print(f"Transitivity: {transitivity:.4f}")
    
    # Density
    density = nx.density(G)
    print(f"Density: {density:.4f}")

Degree Distribution
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from collections import Counter
    
    G = network.core_network
    
    # Get degree sequence
    degrees = [d for n, d in G.degree()]
    
    # Degree distribution
    degree_dist = Counter(degrees)
    print("Degree distribution:", dict(sorted(degree_dist.items())))
    
    # Average degree
    avg_degree = sum(degrees) / len(degrees)
    print(f"Average degree: {avg_degree:.2f}")

Path-Based Statistics
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    G = network.core_network
    
    # Check if connected first
    if nx.is_connected(G.to_undirected()):
        # Average shortest path length
        avg_path = nx.average_shortest_path_length(G)
        print(f"Average shortest path: {avg_path:.2f}")
        
        # Diameter
        diameter = nx.diameter(G)
        print(f"Diameter: {diameter}")
    else:
        print("Network is not connected")
        
        # Largest component
        largest_cc = max(nx.connected_components(G.to_undirected()), key=len)
        largest_size = len(largest_cc)
        print(f"Largest component: {largest_size} nodes")

Statistical Comparison
----------------------

Comparing Networks
~~~~~~~~~~~~~~~~~~

Compare two multilayer networks:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Load two networks
    network1 = multinet.multi_layer_network().load_network("data1.multiedgelist")
    network2 = multinet.multi_layer_network().load_network("data2.multiedgelist")
    
    # Compare basic stats
    print("Network 1:")
    network1.basic_stats()
    
    print("\nNetwork 2:")
    network2.basic_stats()
    
    # Compare layer densities (if same layers)
    for layer in network1.get_layers():
        if layer in network2.get_layers():
            density1 = mls.layer_density(network1, layer)
            density2 = mls.layer_density(network2, layer)
            print(f"{layer}: {density1:.4f} vs {density2:.4f}")

Layer-by-Layer Analysis
~~~~~~~~~~~~~~~~~~~~~~~~

Systematic comparison of all layers:

.. code-block:: python

    import pandas as pd
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Collect stats for each layer
    layer_stats = []
    for layer in network.get_layers():
        # Extract layer
        layer_subnet = network.subnetwork([layer], subset_by="layers")
        G_layer = layer_subnet.core_network
        
        # Compute stats
        stats = {
            'layer': layer,
            'nodes': G_layer.number_of_nodes(),
            'edges': G_layer.number_of_edges(),
            'density': mls.layer_density(network, layer),
            'clustering': nx.average_clustering(G_layer)
        }
        layer_stats.append(stats)
    
    # Display as table
    df = pd.DataFrame(layer_stats)
    print(df.to_string(index=False))

**Output:**

.. code-block:: text

    layer  nodes  edges  density  clustering
        1     46    143   0.1384      0.4521
        2     46    139   0.1346      0.4123
        3     46    136   0.1317      0.3892
        4     46    134   0.1298      0.3756

Exporting Statistics
--------------------

Save to CSV
~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    # Collect node statistics
    node_stats = []
    unique_nodes = set(node for node, layer in network.get_nodes())
    for node in unique_nodes:
        stats = {
            'node': node,
            'activity': mls.node_activity(network, node),
            # Add more stats as needed
        }
        node_stats.append(stats)
    
    # Save
    df = pd.DataFrame(node_stats)
    df.to_csv("node_statistics.csv", index=False)

Save to JSON
~~~~~~~~~~~~

.. code-block:: python

    import json
    
    # Collect statistics
    stats = {
        'num_nodes': len(list(network.get_nodes())),
        'num_edges': len(list(network.get_edges())),
        'num_layers': len(network.get_layers()),
        'layers': {}
    }
    
    # Layer stats
    for layer in network.get_layers():
        stats['layers'][layer] = {
            'density': float(mls.layer_density(network, layer)),
            # Add more stats
        }
    
    # Save
    with open("network_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

Best Practices
--------------

1. **Always check basic stats first**

.. code-block:: python

    network.basic_stats()  # Before doing any analysis

2. **Extract layers for layer-specific analysis**

.. code-block:: python

    layer1 = network.subnetwork(['layer1'], subset_by="layers")
    # Now apply NetworkX functions

3. **Cache expensive computations**

.. code-block:: python

    # Compute once
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    
    # Reuse
    top_nodes = sorted(versatility.items(), key=lambda x: x[1], reverse=True)

4. **Handle edge cases**

.. code-block:: python

    # Check for empty layers
    layer_subnet = network.subnetwork(['layer1'], subset_by="layers")
    if len(list(layer_subnet.get_edges())) == 0:
        print("Layer is empty, skipping...")
    else:
        density = mls.layer_density(network, 'layer1')

Complete Example
----------------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    import networkx as nx
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist", input_type="multiedgelist"
    )
    
    print("=== Basic Statistics ===")
    network.basic_stats()
    
    print("\n=== Layer Statistics ===")
    for layer in network.get_layers():
        density = mls.layer_density(network, layer)
        print(f"{layer}: density = {density:.4f}")
    
    print("\n=== Node Activity ===")
    unique_nodes = set(node for node, layer in network.get_nodes())
    activities = {node: mls.node_activity(network, node) for node in unique_nodes}
    top_active = sorted(activities.items(), key=lambda x: x[1], reverse=True)[:5]
    for node, activity in top_active:
        print(f"{node}: {activity:.4f}")
    
    print("\n=== Layer Similarity ===")
    layers = network.get_layers()
    if len(layers) >= 2:
        similarity = mls.layer_similarity(
            network, layers[0], layers[1], method='jaccard'
        )
        print(f"{layers[0]} vs {layers[1]}: {similarity:.4f}")
    
    print("\n=== Global Metrics ===")
    entropy = mls.entropy_of_multiplexity(network)
    print(f"Entropy of multiplexity: {entropy:.4f} bits")

What You Learned
----------------

This chapter covered the statistical measures available for multilayer networks:

**Basic network statistics:**

- ``basic_stats()`` for quick overview of nodes, edges, and layers
- Manual counting with ``get_nodes()``, ``get_edges()``, ``get_layers()``

**Layer-specific statistics:**

- Layer density with ``layer_density()``
- Layer similarity with ``layer_similarity()`` (Jaccard, Pearson)
- Edge overlap with ``edge_overlap()``
- Inter-layer degree correlation with ``inter_layer_degree_correlation()``

**Node-level statistics:**

- Node activity with ``node_activity()`` — what fraction of layers does a node appear in?
- Versatility centrality with ``versatility_centrality()`` — importance across layers
- Participation coefficient with ``community_participation_coefficient()``

**Network-level statistics:**

- Entropy of multiplexity — how evenly distributed is the structure?
- Algebraic connectivity — how robust is the network?
- Multilayer clustering coefficient — local cohesion across layers

**Integration:**

- All NetworkX statistics work directly on ``network.core_network``
- Extract layers with ``subnetwork()`` for layer-specific analysis

What's Next?
------------

* :doc:`community_detection` — Finding communities that span layers
* :doc:`visualization` — Visualizing statistics and network structure
* :doc:`../concepts/algorithm_landscape` — Overview of all algorithms
* :doc:`../reference/algorithm_reference` — Complete API reference

**Related Examples:**

* ``example_multilayer_statistics.py`` — Statistical analysis examples
* ``example_layer_comparison.py`` — Comparing layers
* ``example_node_metrics.py`` — Node-level metrics

Repository: https://github.com/SkBlaz/py3plex/tree/master/examples
