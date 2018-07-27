## decomposition with ground truth

from py3plex.core import multinet
from py3plex.algorithms.network_ranking.node_ranking import sparse_page_rank, stochastic_normalization_hin

## a simple decomposition example. Note that target nodes need to have "labels" property, to which labels are assigned in class1---class2---...and so on...

dataset = "../datasets/labeled_epigenetics.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(input_file=dataset,directed=True,input_type=dataset.split(".")[-1])

print ("Running optimization for {}".format(dataset))
multilayer_network.basic_stats() ## check core imports        
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))
print(triplet_set)
for decomposition in multilayer_network.get_decomposition(heuristic=["idf","rf"], cycle=triplet_set, parallel=True):
    print(decomposition)


