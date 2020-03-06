Analysis of multiplex networks
#########################
Multiplex networks are more convenient for analysis, hence many existing approaches can be considered, and were implemented as a part of py3plex. The main ones are discussed next:


Aggregations
*******
One of the most common way to approach multiplex network analysis is by aggregating information across layers. Let that be the information bound to nodes or edges, both can be aggregated into a single *homogeneous* network that can readily be analysed. An example of aggregation is given below, on a random multiplex ER (multiple ERs across same node set).

.. code-block:: python
   :linenos:

    ### aggregate a multiplex network

    import networkx as nx
    from py3plex.core import multinet
    from py3plex.core import random_generators

    ## initiate an instance of a random graph
    ER_multilayer = random_generators.random_multiplex_ER(500,8,0.0005,directed=False)
    ER_multilayer.basic_stats()
    ## simple networkx object
    aggregated_network1 = ER_multilayer.aggregate_edges(metric="count",normalize_by="degree")
    print(nx.info(aggregated_network1))

    ## unnormalized counts for edge weights
    aggregated_network2 = ER_multilayer.aggregate_edges(metric="count",normalize_by="raw")
    print(nx.info(aggregated_network2))

    ## The two networks have the same number of links (all)
    ## However, the weights differ!
    for e in aggregated_network2.edges(data=True):
	print(e)

    for e in aggregated_network1.edges(data=True):
	print(e)

The first network divides the contribution of an individual edge with the average node degree in a given layer, and the second one simply sums them.


Subsetting
*******
Subsetting operates in the same manner than for multilayers, hence:

.. code-block:: python
   :linenos:

    B = multinet.multi_layer_network(network_type="multiplex")
    B.add_edges([[1,1,2,1,1],[1,2,3,2,1],[1,2,3,1,1],[2,1,3,2,1]],input_type="list")

    ## subset the network by layers
    C = B.subnetwork([2],subset_by="layers")
    print(list(C.get_nodes()))

    C = B.subnetwork([1],subset_by="node_names")
    print(list(C.get_nodes()))

    C = B.subnetwork([(1,1),(1,2)],subset_by="node_layer_names")
    print(list(C.get_nodes()))
