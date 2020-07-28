### simple supra adjacency matrix manipulation

## tensor-based operations examples

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
comNet.load_layer_name_mapping('../datasets/simple_multiplex.txt')
mat = comNet.get_supra_adjacency_matrix()
print(mat.shape)
kwargs = {"display": True}
comNet.visualize_matrix(kwargs)
## how are nodes ordered?
for edge in comNet.get_edges(data=True):
    print(edge)
print(comNet.node_order_in_matrix)
