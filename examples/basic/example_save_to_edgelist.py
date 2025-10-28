# simple example for saving to multiedgelists
from py3plex.core import multinet

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/goslim_mirna.gpickle",
    directed=False,
    input_type="gpickle_biomine")

# save to string-based representation
multilayer_network.save_network("../datasets/mirna_multiedgelist.list",
                                output_type="multiedgelist")

# encode each node-layer pair with an int
multilayer_network.save_network("../datasets/mirna_edgelist.list",
                                output_type="edgelist")

# save to string-based representation
multilayer_network.save_network("../datasets/mirna_multiedgelist_encoded.list",
                                output_type="multiedgelist_encoded")

# mappings are saved into the main object!
# print(multilayer_network.node_map)
# print(multilayer_network.layer_map)
