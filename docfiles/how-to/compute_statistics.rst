How to Compute Network Statistics
==================================

**Goal:** Calculate metrics that describe the structure of your multilayer network—quick counts, per-layer comparisons, node-level rankings, and multilayer-specific measures.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`). Examples reuse the same small network unless noted.

.. note:: Imports used below
   
   Most snippets rely on the DSL helpers ``Q`` and ``L``:
   
   .. code-block:: python
   
       from py3plex.dsl import Q, L

.. note:: Where to find this data
   
   Examples in this guide use:
   
   * **Programmatically created networks** (recommended for self-contained examples)
   * **Built-in generators**: ``from py3plex.core import random_generators``
   * **Example files**: ``datasets/multiedgelist.txt`` in the repository
   
   For reproducibility, we'll create networks from scratch in most examples.

Quick Statistics
----------------

Get a fast overview (total nodes, edges, layers):

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([
        ['A', '1', 'B', '1', 1],
        ['B', '1', 'C', '1', 1],
        ['A', '2', 'C', '2', 1],
        ['C', '2', 'D', '2', 1],
    ], input_type="list")
    
    # Display comprehensive stats
    network.basic_stats()

**Example output:**

.. code-block:: text

    Number of unique nodes (as node-layer tuples): 6
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer '1': 3 nodes
      Layer '2': 3 nodes

Layer-Specific Statistics
--------------------------

Understand how structure varies per layer before aggregating the network.

Compute Per-Layer Density
~~~~~~~~~~~~~~~~~~~~~~~~~~

Density is the fraction of possible within-layer connections present.
The statistic includes isolated replicas and counts each non-loop connection once.
Directed layers count ordered pairs.

.. code-block:: python

    from py3plex.algorithms.statistics.multilayer_statistics import layer_density

    for layer in network.layers:
        print(f"Layer {layer}: density = {layer_density(network, layer):.4f}")

Compare Layers
~~~~~~~~~~~~~~

Use the DSL for efficient comparison:

.. code-block:: python

    for layer in network.layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", kind="intra")
             .execute(network)
        )
        df = result.to_pandas()
        print(f"{layer}: avg degree = {df['degree'].mean():.2f}")

**Example output (values depend on your data):**

.. code-block:: text

    layer1: avg degree = 3.45
    layer2: avg degree = 2.87
    layer3: avg degree = 4.12

Node-Level Statistics
----------------------

Once you know layer-level trends, drill down to node importance and activity.

Node Activity (Layer Count)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``layer_count`` operator reports how many selected layers contain each
physical node. The query returns one row per replica. Drop repeated physical
IDs for a one-row-per-entity summary.

.. code-block:: python

    result = Q.nodes().compute("layer_count").execute(network)
    df = result.to_pandas()
    active_nodes = (
        df.loc[df["layer_count"] > 1, ["id", "layer_count"]]
        .drop_duplicates(subset="id")
        .sort_values("layer_count", ascending=False)
    )
    print(active_nodes)

Degree Centrality
~~~~~~~~~~~~~~~~~

Compute degree for all nodes and sort in descending order:

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

Find nodes that bridge different parts of the network (higher values indicate more shortest paths go through the node):

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

Compute several measures in one pass to avoid recomputing them separately:

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

Use these measures when the interaction between layers matters, not just within-layer structure.

Node Versatility
~~~~~~~~~~~~~~~~

Versatility centrality combines a physical node’s centrality scores across layers. By default, each layer receives the same weight.

.. code-block:: python

    from py3plex.algorithms.statistics.multilayer_statistics import versatility_centrality
    
    versatility_scores = versatility_centrality(network, centrality_type="degree")
    
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

    from py3plex.algorithms.statistics.multilayer_statistics import edge_overlap
    
    overlap = edge_overlap(network, "1", "2")
    
    print(f"Edge overlap between layers 1 and 2: {overlap:.2%}")

``overlap`` is the size of the intersection divided by the size of the union of physical-node edge sets.

Inter-Layer Degree Correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Are high-degree nodes in layer 1 also high-degree in layer 2?

.. code-block:: python

    from py3plex.algorithms.statistics.multilayer_statistics import (
        inter_layer_degree_correlation,
    )

    correlation = inter_layer_degree_correlation(network, "1", "2")
    print(f"Degree correlation: {correlation:.3f}")

Network-Wide Statistics
-----------------------

These examples measure the simple undirected graph of node replicas. The
projection retains layer IDs on the nodes and includes interlayer edges.

Global Clustering Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx

    graph = nx.Graph(network.core_network)
    graph.remove_edges_from(nx.selfloop_edges(graph))
    print(f"Global clustering (transitivity): {nx.transitivity(graph):.3f}")

Average Path Length
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    largest_component = max(nx.connected_components(graph), key=len, default=set())
    if largest_component:
        connected = graph.subgraph(largest_component)
        length = nx.average_shortest_path_length(connected)
        print(f"Average path length of the largest component: {length:.2f}")

Exporting Statistics
--------------------

Persist results so you can compare runs or feed them into other tools.

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
        "num_replicas": network.core_network.number_of_nodes(),
        "num_edges": network.core_network.number_of_edges(),
        "num_layers": network.layer_count,
        "density_by_layer": {
            layer: layer_density(network, layer) for layer in network.layers
        },
    }
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

Common Patterns
---------------

Pattern: Compare Node Importance Across Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    layers = network.layers
    all_stats = []
    
    for layer in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", kind="intra")
             .compute("betweenness_centrality")
             .execute(network)
        )
        df = result.to_pandas()
        df['layer'] = layer
        all_stats.append(df)
    
    combined = pd.concat(all_stats, ignore_index=True)
    
    # Find nodes that are important in all layers
    pivot = combined.pivot_table(
        values='degree',
        index='id',
        columns='layer',
        aggfunc='mean'
    )
    
    print(pivot)

Pattern: Identify Layer-Specific Hubs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    for layer in network.layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", kind="intra")
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
