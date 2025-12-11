How to Compute Network Statistics
==================================

**Goal:** Calculate metrics that describe the structure of your multilayer network.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

.. note:: Where to find this data
   
   Examples in this guide use:
   
   * **Programmatically created networks** (recommended for self-contained examples)
   * **Built-in generators**: ``from py3plex.algorithms import random_generators``
   * **Example files**: ``datasets/multiedgelist.txt`` in the repository
   
   For reproducibility, we'll create networks from scratch in most examples.

Quick Statistics
----------------

Get an overview of your network:

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', '1', 'B', '1', 1],
        ['B', '1', 'C', '1', 1],
        ['A', '2', 'C', '2', 1],
        ['C', '2', 'D', '2', 1],
    ], input_type="list")
    
    # Display comprehensive stats
    network.basic_stats()

**Expected output:**

.. code-block:: text

    Number of nodes: 7
    Number of edges: 4
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer '1': 3 nodes
      Layer '2': 3 nodes

Layer-Specific Statistics
--------------------------

Compute Per-Layer Density
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    layers = network.get_layers()
    
    for layer in layers:
        # Get nodes and edges in this layer
        from py3plex.dsl import Q, L
        
        nodes = Q.nodes().from_layers(L[layer]).execute(network)
        edges = Q.edges().from_layers(L[layer]).execute(network)
        
        n = len(nodes)
        m = len(edges)
        
        # Density = actual edges / possible edges
        max_edges = n * (n - 1) / 2  # undirected
        density = m / max_edges if max_edges > 0 else 0
        
        print(f"Layer {layer}: density = {density:.4f}")

Compare Layers
~~~~~~~~~~~~~~

Use the DSL for efficient comparison:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    for layer in ["layer1", "layer2", "layer3"]:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        print(f"{layer}: avg degree = {df['degree'].mean():.2f}")

**Expected output:**

.. code-block:: text

    layer1: avg degree = 3.45
    layer2: avg degree = 2.87
    layer3: avg degree = 4.12

Node-Level Statistics
----------------------

Node Activity (Layer Count)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How many layers does each node participate in?

.. code-block:: python

    from py3plex.dsl import Q
    
    # Get nodes present in multiple layers
    active_nodes = (
        Q.nodes()
         .where(layer_count__gt=1)
         .compute("layer_count")
         .order_by("-layer_count")
         .execute(network)
    )
    
    df = active_nodes.to_pandas()
    print(df.head(10))

**Expected output:**

.. code-block:: text

         node  layer_count
    0   Alice           3
    1     Bob           3
    2   Carol           2
    3    Dave           1

Degree Centrality
~~~~~~~~~~~~~~~~~

Compute degree for all nodes:

.. code-block:: python

    from py3plex.dsl import Q
    
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(10)
         .execute(network)
    )
    
    df = result.to_pandas()
    print("Top 10 by degree:")
    print(df)

Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~

Find nodes that bridge different parts of the network:

.. code-block:: python

    result = (
        Q.nodes()
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(10)
         .execute(network)
    )
    
    df = result.to_pandas()
    print("Top 10 by betweenness:")
    print(df)

Multiple Metrics at Once
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )
    
    df = result.to_pandas()
    print(df.describe())

Multilayer-Specific Statistics
-------------------------------

Node Versatility
~~~~~~~~~~~~~~~~

Versatility measures how evenly a node distributes its connections across layers:

.. code-block:: python

    from py3plex.algorithms.statistics import calculate_versatility
    
    versatility_scores = calculate_versatility(network)
    
    # Sort by versatility
    sorted_scores = sorted(
        versatility_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("Top 5 most versatile nodes:")
    for node, score in sorted_scores[:5]:
        print(f"{node}: {score:.3f}")

Edge Overlap Between Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How many connections exist in multiple layers?

.. code-block:: python

    from py3plex.algorithms.statistics import calculate_edge_overlap
    
    overlap = calculate_edge_overlap(network, 'layer1', 'layer2')
    
    print(f"Edge overlap between layer1 and layer2: {overlap:.2%}")

Inter-Layer Degree Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Are high-degree nodes in layer 1 also high-degree in layer 2?

.. code-block:: python

    from py3plex.algorithms.statistics import inter_layer_correlation
    
    correlation = inter_layer_correlation(
        network,
        'layer1',
        'layer2',
        metric='degree'
    )
    
    print(f"Degree correlation: {correlation:.3f}")

Network-Wide Statistics
------------------------

Global Clustering Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import global_clustering_coefficient
    
    gcc = global_clustering_coefficient(network)
    print(f"Global clustering: {gcc:.3f}")

Average Path Length
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import average_path_length
    
    # Note: computationally expensive for large networks
    apl = average_path_length(network)
    print(f"Average path length: {apl:.2f}")

Exporting Statistics
--------------------

Save to CSV
~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q
    
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "layer_count")
         .execute(network)
    )
    
    df = result.to_pandas()
    df.to_csv("network_statistics.csv", index=False)

Save to JSON
~~~~~~~~~~~~

.. code-block:: python

    import json
    
    stats = {
        'num_nodes': len(list(network.get_nodes())),
        'num_edges': len(list(network.get_edges())),
        'num_layers': len(network.get_layers()),
        'density_by_layer': {}
    }
    
    for layer in network.get_layers():
        nodes = Q.nodes().from_layers(L[layer]).execute(network)
        edges = Q.edges().from_layers(L[layer]).execute(network)
        stats['density_by_layer'][layer] = len(edges) / (len(nodes) ** 2)
    
    with open('stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

Common Patterns
---------------

Pattern: Compare Node Importance Across Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    layers = network.get_layers()
    all_stats = []
    
    for layer in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", "betweenness_centrality")
             .execute(network)
        )
        df = result.to_pandas()
        df['layer'] = layer
        all_stats.append(df)
    
    combined = pd.concat(all_stats, ignore_index=True)
    
    # Find nodes that are important in all layers
    pivot = combined.pivot_table(
        values='degree',
        index='node',
        columns='layer',
        aggfunc='mean'
    )
    
    print(pivot)

Pattern: Identify Layer-Specific Hubs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    for layer in network.get_layers():
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .order_by("-degree")
             .limit(5)
             .execute(network)
        )
        df = result.to_pandas()
        print(f"\nTop 5 hubs in {layer}:")
        print(df)

Next Steps
----------

* **Visualize statistics:** :doc:`visualize_networks`
* **Find communities:** :doc:`run_community_detection`
* **Understand metrics:** :doc:`../concepts/algorithm_landscape`
* **API reference:** :doc:`../reference/algorithm_reference`
