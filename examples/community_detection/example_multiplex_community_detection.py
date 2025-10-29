from py3plex.core import random_generators
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet

ER_multilayer = random_generators.random_multilayer_ER(50,
                                                       8,
                                                       0.05,
                                                       directed=False)
partition = cw.louvain_communities(ER_multilayer)
print(partition)

comNet = multinet.multi_layer_network().load_network(
    '../datasets/simple_multiplex.edgelist',
    directed=False,
    input_type='multiplex_edges')
comNet.load_layer_name_mapping('../datasets/simple_multiplex.txt')
comNet.basic_stats()
part = cw.louvain_communities(comNet)
print(part)
