from py3plex.core import multinet

## a multilayer object
A = multinet.multi_layer_network().load_network(
    "../datasets/multiedgelist.txt",
    input_type="multiedgelist",
    directed=False)

A.basic_stats()

## this is nicer printing.
A.monitor("Edge looping:")

## looping through edges:
for edge in A.get_edges(data=True):
    print(edge)

A.monitor("Node looping:")

## what about nodes?
for node in A.get_nodes(data=True):
    print(node)

C1 = A.subnetwork(['1'], subset_by="layers")
A.monitor(list(C1.get_nodes()))

C2 = A.subnetwork(['1'], subset_by="node_names")
A.monitor(list(C2.get_nodes()))

C3 = A.subnetwork([('1', '1'), ('2', '1')], subset_by="node_layer_names")
A.monitor(list(C3.get_nodes()))

centralities = C1.monoplex_nx_wrapper("degree_centrality")
A.monitor(centralities)
