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

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multiedgelist.txt",
    directed=False,
    input_type="multiedgelist")

# multilayer_network = multinet.multi_layer_network().load_network("../datasets/erdos_detangler.json",directed=False, input_type="detangler_json") ## TOD
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/edgeList.txt", directed=False, input_type="multiedgelist")

# save the network as a gpickle object
multilayer_network.save_network(
    output_file="../datasets/stored_network.gpickle", output_type="gpickle")
