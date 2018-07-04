## a simple example demonstrating the community detection capabilities

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names

from collections import Counter
from operator import itemgetter  

network = multinet.multi_layer_network().load_network(input_file="../datasets/cora.mat",directed=False,input_type="sparse") ## network and group objects must be present within the .mat object
partition = cw.louvain_communities(network.core_network)

## select top n communities by size
top_n = 10
top_n_communities = dict(Counter(partition.values()))
top_n_id = [x[0] for e,x in enumerate(sorted(top_n_communities.items(), key = itemgetter(1), reverse = False)) if e < top_n]

## assign node colors
#network_colors = [partition[x] if x in top_n_id else -1 for x in network.get_nodes()]

## visualize the network's communities!
hairball_plot(network.core_network,color_list = list(partition.values()),layered=False,layout_parameters={"iterations" : 50},scale_by_size=True)
plt.show()
