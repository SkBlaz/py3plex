# this example demonstrates how a network can be manipulated

from py3plex.core import multinet
from py3plex.core import random_generators

# An example general multilayer network
A = multinet.multi_layer_network()

# add a single node with type
simple_node = {"source": "node1", "type": "t1"}
A.add_nodes(simple_node)
A.monitor("Printing a single node.")
print(list(A.get_nodes(data=True)))

# add a single edge with type
simple_edge = {
    "source": "node1",
    "target": "node2",
    "type": "mention",
    "source_type": "t1",
    "weight": 2,  # add arbitrary attributes!
    "target_type": "t2"
}

A.add_edges(simple_edge)
A.monitor("Printing a single edge.")
print(list(A.get_edges(data=True)))

# multiple edges are added by simply packing existing edges into a list.
simple_attributed_edges = [{
    "source": "node1",
    "target": "node6",
    "type": "mention",
    "source_type": "t1",
    "target_type": "t5"
}, {
    "source": "node3",
    "target": "node2",
    "type": "mention",
    "source_type": "t1",
    "target_type": "t3"
}]
A.add_edges(simple_attributed_edges)
A.monitor("Printing multiple edges")
print(list(A.get_edges(data=True)))

# Edges can also be added as lists: [n1,l1,n2,l2,w]
example_list_edge = [["node3", "t2", "node2", "t6", 1],
                     ["node3", "t2", "node2", "t6", 1]]

# specify that input is list, all else is recognized by Py3plex!
A.add_edges(example_list_edge, input_type="list")
print(list(A.get_edges()))

A.monitor("Random ER multilayer graph in progress")
ER_multilayer = random_generators.random_multilayer_ER(300,
                                                       6,
                                                       0.05,
                                                       directed=False)
ER_multilayer.visualize_network(show=True)

# dealing with multiplex networks
B = multinet.multi_layer_network(network_type="multiplex")
B.add_edges(
    [[1, 1, 2, 1, 1], [1, 2, 3, 2, 1], [1, 2, 3, 1, 1], [2, 1, 3, 2, 1]],
    input_type="list")

# subset the network by layers
C = B.subnetwork([2], subset_by="layers")
print(list(C.get_nodes()))

C = B.subnetwork([2], subset_by="node_names")
print(list(C.get_nodes()))

C = B.subnetwork([(1, 1), (1, 2)], subset_by="node_layer_names")
print(list(C.get_nodes()))

# coupled edges
B.monitor(list(B.get_edges(multiplex_edges=True)))

# non-coupled edges
B.monitor(list(B.get_edges(multiplex_edges=False)))

# visualize this toy example
# B.visualize_network(show=True,resolution=0.01)

# nodes can also be removed easily
B.remove_edges(
    [[1, 1, 2, 1, 1], [1, 2, 3, 2, 1], [1, 2, 3, 1, 1], [2, 1, 3, 2, 1]],
    input_type="list")
print(list(B.get_edges()))

B.remove_nodes([(1, 1), (3, 1)], input_type="list")
print(list(B.get_nodes()))
