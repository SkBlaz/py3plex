## an example of numeric encoding (supra adjacency)

from py3plex.core import multinet
from py3plex.core import random_generators

## initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,
                                                       8,
                                                       0.05,
                                                       directed=False)
mtx = ER_multilayer.get_supra_adjacency_matrix()

comNet = multinet.multi_layer_network(
    network_type="multiplex",
    coupling_weight=1).load_network('../datasets/simple_multiplex.edgelist',
                                    directed=False,
                                    input_type='multiplex_edges')
comNet.basic_stats()
comNet._encode_to_numeric()
vectors = comNet.numeric_core_network
node_list = comNet.node_order_in_matrix
print(vectors.shape)
