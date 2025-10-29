# reading different inputs

from py3plex.core import multinet

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multiedgelist2.txt",
    directed=False,
    input_type="multiedgelist")

multilayer_network.basic_stats()

# Let's count node properties.
node_layer_tuples = set()
unique_nodes = set()

for edge in multilayer_network.get_nodes():
    node_layer_tuples.add(edge)
    unique_nodes.add(edge[0])

print("Node layer tuples: ", len(node_layer_tuples))
print("Unique nodes: ", len(unique_nodes))

######################
## Simple networks (monoplex)
######################

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=True,
    input_type="gpickle_biomine")

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/ecommerce_0.gml", directed=True, input_type="gml")

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/ions.mat", directed=False, input_type="sparse")

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/test.edgelist", directed=False, input_type="edgelist")

######################
## Two key multilayer/plex formats
######################

## N L N L w
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multiedgelist.txt",
    directed=False,
    input_type="multiedgelist")

# L N N w
multilayer_network = multinet.multi_layer_network(network_type="multiplex").load_network(
    "../datasets/test13.edges", directed=False, input_type="multiplex_edges")

# save the network as a gpickle object
multilayer_network.save_network(
    output_file="../datasets/stored_network.gpickle", output_type="gpickle")
