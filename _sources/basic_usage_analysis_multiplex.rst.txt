Multiplex Network Analysis
==========================

Multiplex networks have the same nodes across different layers, enabling specialized analysis techniques.

Network Aggregation
-------------------

Combine information across layers into a single network:

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate random multiplex network
    network = random_generators.random_multiplex_ER(
        num_nodes=500, num_layers=8, probability=0.0005, directed=False)
    
    # Aggregate edges with different metrics
    aggregated1 = network.aggregate_edges(metric="count", normalize_by="degree")
    aggregated2 = network.aggregate_edges(metric="count", normalize_by="raw")

The first network divides the contribution of an individual edge by the average node degree in a given layer, and the second one simply sums them.

.. code-block:: python

    # Examine edge weights in aggregated networks
    for e in aggregated1.edges(data=True):
        print(e)

    for e in aggregated2.edges(data=True):
        print(e)

Subsetting Multiplex Networks
------------------------------

Subsetting operates in the same manner as for multilayer networks:

.. code-block:: python

    from py3plex.core import multinet
    
    B = multinet.multi_layer_network(network_type="multiplex")
    B.add_edges([[1,1,2,1,1],[1,2,3,2,1],[1,2,3,1,1],[2,1,3,2,1]], input_type="list")

    # Subset the network by layers
    C = B.subnetwork([2], subset_by="layers")
    print(list(C.get_nodes()))

    # Subset by node names
    C = B.subnetwork([1], subset_by="node_names")
    print(list(C.get_nodes()))

    # Subset by specific node-layer pairs
    C = B.subnetwork([(1,1),(1,2)], subset_by="node_layer_names")
    print(list(C.get_nodes()))

Examples
--------

See:

- ``example_multiplex_aggregate.py`` - Network aggregation
- ``example_multiplex_dynamics.py`` - Temporal dynamics
- ``example_multiplex_community_detection.py`` - Community detection
- ``example_new_multiplex_metrics.py`` - New multiplex centrality and robustness metrics

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
