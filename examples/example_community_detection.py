## a simple example demonstrating the community detection capabilities

from py3plex.algorithms import community_wrapper as cw
from py3plex.core import multinet
from collections import Counter
from operator import itemgetter  

network = multinet.multi_layer_network().load_network(input_file="../datasets/homo.mat",directed=False,input_type="sparse") ## network and group objects must be present within the .mat object
partition = cw.louvain_communities(network.core_network)
top_n_communities = dict(Counter(partition.values()))
top_n = 5
top_n_id = [x[0] for e,x in enumerate(sorted(top_n_communities.items(), key = itemgetter(1), reverse = True)) if e < 5]

## top n communities!
 print(top_n_id)
