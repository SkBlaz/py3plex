Analysis of multilayers
#########################
Having discussed how the multilayer networks can be constructed, the next logical step is to discuss what analytics is offered by py3plex. In this chapter, we discuss the following functionality:

1. Looping constructs and iteration (multilayer networks)
2. Traversal (multilayer networks).
3. Bindings to NetworkX for arbitrary monolayer functinality.

Some useful constructs
*****************
Analysis of multilayer networks can be often tricky, as these structures need to be first simplified to more algorithm-friendly inputs. We next discuss some functionality supported by py3plex that potentially facilitates such endeavours. The *multinet* object is the core class around everything more or less evolves.

.. code-block:: python
   :linenos:

    from py3plex.core import multinet

    ## a multilayer object
    A = multinet.multi_layer_network().load_network("../datasets/multiedgelist.txt",input_type="multiedgelist",directed=False)

    A.basic_stats()

    ## this is nicer printing.
    A.monitor("Edge looping:")

    ## looping through edges:
    for edge in A.get_edges(data = True):
	print(edge)

    A.monitor("Node looping:")

    ## what about nodes?
    for node in A.get_nodes(data = True):
	print(node)

    C1 = A.subnetwork(['1'],subset_by="layers")
    A.monitor(list(C1.get_nodes()))

    C2 = A.subnetwork(['1'],subset_by="node_names")
    A.monitor(list(C2.get_nodes()))

    C3 = A.subnetwork([('1','1'),('2','1')],subset_by="node_layer_names")
    A.monitor(list(C3.get_nodes()))

   
Network traversal
*****************
One of the simplest examples that leads to understanding what one can do with a given multilayer entwork is the notion of network traversal. We next present an example where a multilayer network is first generated and next traversed, where the locations of the random walkers traversing across intra- as well as inter-layer edges are considered.

.. code-block:: python
   :linenos:

    from py3plex.core import multinet
    from py3plex.core import random_generators
    import numpy as np
    import queue
    import matplotlib.pyplot as plt
    import seaborn as sns

    ## some random graph
    ER_multilayer = random_generators.random_multilayer_ER(3000,10,0.05,directed=False)

    ## seed node
    all_nodes = list(ER_multilayer.get_nodes())
    all_nodes_indexed = {x:en for en,x in enumerate(all_nodes)}

    ## spread from a random node
    random_init = np.random.randint(len(all_nodes))
    random_node = all_nodes[random_init]
    spread_vector = np.zeros(len(ER_multilayer.core_network))
    Q = queue.Queue(maxsize=3000) 
    Q.put(random_node)

    layer_visit_sequence = []
    node_visit_sequence = []
    iterations = 0
    while True:
	if not Q.empty():
	    candidate = Q.get()
	    iterations+=1
	    if iterations % 100 == 0:
		print("Iterations: {}".format(iterations))
	    for neighbor in ER_multilayer.get_neighbors(candidate[0],candidate[1]):
		idx = all_nodes_indexed[neighbor]
		if spread_vector[idx] != 1:
		    layer_visit_sequence.append(candidate[1])
		    node_visit_sequence.append((neighbor,iterations))
		    Q.put(neighbor)
		    spread_vector[idx] = 1
	else:
	    break

    sns.distplot(layer_visit_sequence)
    plt.xlabel("Layer")
    plt.ylabel("Visit density")
    plt.show()

.. image:: ../example_images/spreading.png
   :width: 400

Extending functionality with networkX?
*****************
As, under the hood, most of the py3plex objects are some form of multigraphs, with some simplification, many *ad hoc* functionality is readily available! Assuming you still have the C1 network from the first example, simply call the *monoplex_nx_wrapper* method with corresponding function name:

.. code-block:: python
   :linenos:

   centralities = C1.monoplex_nx_wrapper("degree_centrality")
   A.monitor(centralities)
   
A technical note
********

If you have a network without layer information, however would like to start from there, the::
  
  A.add_dummy_layers()

Will equip each node with a dummy layer (hence all nodes are in the same layer).
