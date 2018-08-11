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

## Edges can also be added as lists: [n1,l1,n2,l2,w]
example_list_edge = [[1,1,2,1,1],[1,2,3,2,1]]

## specify that input is list, all else is recognized by Py3plex!
A.add_edges(example_list_edge,input_type="list")
print(list(A.get_edges()))

A.monitor("Random ER multilayer graph in progress")
ER_multilayer = random_generators.random_multilayer_ER(300,4,0.05,directed=False)
ER_multilayer.visualize_network(show=True)
