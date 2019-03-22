### simple supra adjacency matrix manipulation

## tensor-based operations examples

from py3plex.core import multinet
from py3plex.core import random_generators

## initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,8,0.05,directed=False)
mtx = ER_multilayer.get_supra_adjacency_matrix()

comNet = multinet.multi_layer_network(network_type="multiplex").load_network('../datasets/simple_multiplex.edgelist',directed=False,input_type='multiplex_edges')
comNet.basic_stats()
comNet.load_layer_name_mapping('../datasets/simple_multiplex.txt')
mat = comNet.get_supra_adjacency_matrix()

## how are nodes ordered?
orderings = dict(zip(comNet.node_order_in_matrix,list(comNet.get_nodes())))
print(orderings)
