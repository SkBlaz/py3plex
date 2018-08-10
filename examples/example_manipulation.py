## this example demonstrates how a network can be manipulated

from py3plex.core import multinet
from py3plex.core import random_generators

A = multinet.multi_layer_network()

## add a single node with type
simple_node = {"source" : "node1","type":"t1"}
A.add_nodes(simple_node)
A.monitor("Printing a single node.")
print(list(A.get_nodes(data=True)))

## add a single edge with type
simple_edge = {"source":"node1",
               "target":"node2",
               "type":"mention",
               "source_type":"t1",
               "target_type":"t2"}

A.add_edges(simple_edge)
A.monitor("Printing a single edge.")
print(list(A.get_edges(data=True)))

## multiple edges are added by simply packing existing edges into a list.
simple_edges = [{"source":"node1","target":"node6","type":"mention","source_type":"t1","target_type":"t5"},{"source":"node3","target":"node2","type":"mention","source_type":"t1","target_type":"t3"}]
A.add_edges(simple_edges)
A.monitor("Printing multiple edges")
print(list(A.get_edges(data=True)))

A.monitor("Random ER multilayer graph in progress")
ER_multilayer = random_generators.random_multilayer_ER(300,4,0.05,directed=True)
ER_multilayer.visualize_network(show=True)

# ## general multilayer networks
# multilayer_network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")

# network_edges = multilayer_network.get_edges(data=True) ## edge iterator
# network_nodes = multilayer_network.get_nodes(data=True) ## node iterator
# network_layers = multilayer_network.get_layers(style="diagonal") ## layerwise networks

# ## Multiplex networks

# multiplex_network = multinet.multi_layer_network(network_type="multiplex").load_network("../datasets/moscow_edges.txt",directed=True, input_type="multiplex_edges")

# ## multiplex networks can be couples --- to include coupled edges, use mpx_edges parameter
# network_edges = multiplex_network.get_edges(data=True,mpx_edges=False) ## edge iterator
# multiplex_network.monitor(str(len(list(network_edges)))+" Non-coupled only edges.")

# network_edges = multiplex_network.get_edges(data=True,mpx_edges=True) ## edge iterator
# multiplex_network.monitor(str(len(list(network_edges)))+" Including coupled  edges.")

# network_nodes = multiplex_network.get_nodes(data=True) ## node iterator
