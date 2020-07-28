## a simple visualization module useful for ad-hoc tasks

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import colors_default
from collections import Counter


def visualize_network(input_file, input_type, directed, top_n_communities):

    network = multinet.multi_layer_network().load_network(
        input_file=args.input_network,
        directed=directed,
        input_type=args.input_type)

    network.basic_stats()  ## check core imports

    partition = cw.louvain_communities(network.core_network)

    ## select top n communities by size
    top_n = top_n_communities
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    ## assign node colors
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in network.get_nodes()
    ]

    ## visualize the network's communities!
    hairball_plot(network.core_network,
                  color_list=network_colors,
                  layered=False,
                  layout_parameters={"iterations": args.iterations},
                  scale_by_size=True,
                  layout_algorithm="force",
                  legend=False)
    plt.show()


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_network", default="../datasets/cora.mat")
    parser.add_argument("--input_type", default="sparse")
    parser.add_argument("--iterations", default=200, type=int)
    parser.add_argument("--directed", default=False)
    parser.add_argument("--top_n_communities", default=5, type=int)

    args = parser.parse_args()
    visualize_network(args.input_network, args.input_type, args.directed,
                      args.top_n_communities)
