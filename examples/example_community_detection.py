## a simple example demonstrating the community detection capabilities

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import colors_default
from collections import Counter

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--input_network", default="../datasets/cora.mat")
parser.add_argument("--input_type", default="sparse")
parser.add_argument("--iterations", default=200, type=int)
args = parser.parse_args()

# network and group objects must be present within the .mat object

network = multinet.multi_layer_network().load_network(
    input_file=args.input_network, directed=False, input_type=args.input_type)

# convert to generic px format (n,l,n2,l2)---dummy layers are added
if args.input_type == 'sparse':
    network.sparse_to_px()

network.basic_stats()  # check core imports

##################################
# THE LOUVAIN ALGORITHM
##################################

partition = cw.louvain_communities(network)
#print(partition)
# select top n communities by size
top_n = 10
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

# assign node colors
color_mappings = dict(
    zip(top_n_communities,
        [x for x in colors_default if x != "black"][0:top_n]))

network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]
# visualize the network's communities!
hairball_plot(network.core_network,
              color_list=network_colors,
              layout_parameters={"iterations": args.iterations},
              scale_by_size=True,
              layout_algorithm="force",
              legend=False)
plt.show()

##################################
# THE INFOMAP ALGORITHM WRAPPER EXAMPLE --- this supports multiplex networks directly
##################################

partition = cw.infomap_communities(network,
                                   binary="../bin/Infomap",
                                   multiplex=False,
                                   verbose=True)
# select top n communities by size
top_n = 5
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

# assign node colors
color_mappings = dict(
    zip(top_n_communities,
        [x for x in colors_default if x != "black"][0:top_n]))

network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

# visualize the network's communities!
hairball_plot(network.core_network,
              color_list=network_colors,
              layout_parameters={"iterations": args.iterations},
              scale_by_size=True,
              layout_algorithm="force",
              legend=False)
plt.show()

################################
# STORING the multiplex edgelist?
################################

# this creates a tmp_network.txt edgelist format suitable for use elsewhere + returns node mappings to real names.
#inverse_node_map = network.serialize_to_edgelist(edgelist_file="tmp_network.txt")
