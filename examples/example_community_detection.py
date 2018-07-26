## a simple example demonstrating the community detection capabilities

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names
from collections import Counter
from operator import itemgetter

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_network",default="../datasets/cora.mat")
parser.add_argument("--input_type",default="sparse")
args = parser.parse_args()

network = multinet.multi_layer_network().load_network(input_file=args.input_network,directed=False,input_type=args.input_type) ## network and group objects must be present within the .mat object
partition = cw.louvain_communities(network.core_network)

## select top n communities by size
top_n = 5
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]
## assign node colors
network_colors = [partition[x] if partition[x] in top_n_communities else -1 for x in network.get_nodes()]

## visualize the network's communities!
hairball_plot(network.core_network,color_list = network_colors,layered=False,layout_parameters={"iterations" : 50},scale_by_size=True,layout_algorithm="force",legend=True)
plt.show()
