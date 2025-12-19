Multiplex Network Analysis
==========================

Multiplex networks share the same node set across layers (e.g., friendship, collaboration, transport). Typical workflows either (a) aggregate information across layers into a single weighted projection or (b) operate only on selected layers or nodes where the layer context matters.

Network Aggregation
-------------------

Aggregate edges across layers to obtain a single weighted network of base nodes. The example below builds a random multiplex graph, aggregates it twice with different normalization choices, and then inspects the resulting edge weights.

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate random multiplex network (same node IDs on every layer)
    network = random_generators.random_multiplex_ER(
        num_nodes=500, num_layers=8, probability=0.0005, directed=False)
    
    # Aggregate edges with different metrics
    aggregated1 = network.aggregate_edges(metric="count", normalize_by="degree")
    aggregated2 = network.aggregate_edges(metric="count", normalize_by="raw")

``metric="count"`` tallies how many layers support each edge. ``normalize_by="degree"`` down-weights contributions from denser layers by dividing each layer's count by that layer's average node degree, while ``normalize_by="raw"`` keeps the unnormalized counts. The resulting aggregated graphs expose weights via the ``weight`` edge attribute.

.. code-block:: python

    # Examine edge weights in aggregated networks
    for e in aggregated1.edges(data=True):
        print(e)

    for e in aggregated2.edges(data=True):
        print(e)

Subsetting Multiplex Networks
-----------------------------

Subsetting works the same way as for multilayer networks. Choose whether to filter by layers, raw node IDs, or explicit node-layer pairs depending on how much layer specificity you need:

.. code-block:: python

    from py3plex.core import multinet
    
    B = multinet.multi_layer_network(network_type="multiplex")
    # Edge rows: [src, src_layer, dst, dst_layer, weight]
    B.add_edges([[1,1,2,1,1],[1,2,3,2,1],[1,2,3,1,1],[2,1,3,2,1]], input_type="list")

    # Subset the network by layers (keeps all nodes within layer 2)
    C = B.subnetwork([2], subset_by="layers")
    print(list(C.get_nodes()))

    # Subset by node names (keeps all layers for node 1)
    C = B.subnetwork([1], subset_by="node_names")
    print(list(C.get_nodes()))

    # Subset by specific node-layer pairs (explicit multiplex entries)
    C = B.subnetwork([(1,1), (1,2)], subset_by="node_layer_names")
    print(list(C.get_nodes()))

Examples
--------

Related example scripts:

- ``example_multiplex_aggregate.py`` – Network aggregation
- ``example_multiplex_dynamics.py`` – Temporal dynamics
- ``example_multiplex_community_detection.py`` – Community detection
- ``example_new_multiplex_metrics.py`` – New multiplex centrality and robustness metrics

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
