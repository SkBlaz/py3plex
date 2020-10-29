Community detection (multiplex)
=====================

Community detection is considered when a given network's topology is considered at meso-scales.
py3plex supports both the widely used InfoMap, for which it offers a wrapper:

.. code-block:: python
   :linenos:

	from py3plex.algorithms.community_detection import community_wrapper as cw
	from py3plex.core import multinet

	network = multinet.multi_layer_network(network_type = "multiplex").load_network(input_file="../datasets/simple_multiplex.edgelist",directed=False,input_type="multiplex_edges")
	partition = cw.infomap_communities(network, binary="../bin/Infomap", multiplex=True, verbose=True)
	print(partition)


But also the multiplex Louvain (pip install louvain):

.. code-block:: python
   :linenos:

	## multiplex community detection!

	from py3plex.algorithms.community_detection import community_wrapper as cw
	from py3plex.core import multinet

	network = multinet.multi_layer_network(network_type = "multiplex").load_network(input_file="../datasets/multiplex_example.edgelist",directed=True,input_type="multiplex_edges")
	partition = cw.infomap_communities(network, binary="../bin/Infomap", multiplex=True, verbose=True)
	print(partition)

	## get communities with multiplex louvain
	import igraph as ig
	import louvain

	#optimiser = louvain.Optimiser()
	network.split_to_layers(style = "none")
	network_list = []

	## cast this to igraph
	unique_node_id_counter = 0
	node_hash = {}
	for layer in network.separate_layers:
		g = ig.Graph()
		edges_all = []
		for edge in layer.edges():
			first_node = int(edge[0][0])
			second_node = int(edge[1][0])        
			g.add_vertex(first_node)
			g.add_vertex(second_node)
			edges_all.append((first_node,second_node))
		print(edges_all)
		g.add_edges(edges_all)    
		network_list.append(g)

	membership, improv = louvain.find_partition_multiplex(network_list, louvain.ModularityVertexPartition)

	## for each node we get community assignment.
	network.monitor(membership)
	network.monitor(improv)


Simple, homogeneous community detection is also possible!

.. code-block:: python
   :linenos:

   network = multinet.multi_layer_network().load_network(input_file="../datasets/cora.mat",
                                                      directed=False,
                                                      input_type="sparse")

	partition = cw.louvain_communities(network)
	#print(partition)
	# select top n communities by size
	top_n = 10
	partition_counts = dict(Counter(partition.values()))
	top_n_communities = list(partition_counts.keys())[0:top_n]

	# assign node colors
	color_mappings = dict(zip(top_n_communities,[x for x in colors_default if x != "black"][0:top_n]))

	network_colors = [color_mappings[partition[x]] if partition[x] in top_n_communities else "black" for x in network.get_nodes()]
	# visualize the network's communities!
	hairball_plot(network.core_network,
				  color_list=network_colors,
				  layout_parameters={"iterations": args.iterations},
				  scale_by_size=True,
				  layout_algorithm="force",
				  legend=False)
	plt.show()

.. image:: ../example_images/communities2.png
   :width: 500
