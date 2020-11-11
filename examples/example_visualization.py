# simple plot of a larger file
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_tools
from py3plex.algorithms.community_detection import community_wrapper as cw
from collections import Counter


def plot_intact_embedding(num_it):

    # string layout for larger network -----------------------------------
    multilayer_network = multinet.multi_layer_network().load_network(
        "../datasets/intact02.gpickle", input_type="gpickle",
        directed=False).add_dummy_layers()
    multilayer_network.basic_stats()

    # use embedding to first initialize the nodes..

    # call a specific n2v compiled binary
    train_node2vec_embedding.call_node2vec_binary(
        "../datasets/IntactEdgelistedges.txt",
        "../datasets/test_embedding.emb",
        binary="../bin/node2vec",
        weighted=False)

    # preprocess and check embedding -- for speed, install parallel tsne from https://github.com/DmitryUlyanov/Multicore-TSNE, py3plex knows how to use it.

    multilayer_network.load_embedding("../datasets/test_embedding.emb")

    # load the positions and select the projection algorithm
    output_positions = embedding_tools.get_2d_coordinates_tsne(
        multilayer_network, output_format="pos_dict")

    # custom layouts are part of the custom coordinate option
    layout_parameters = {"iterations": num_it}
    layout_parameters['pos'] = output_positions  # assign parameters
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)

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
        for x in multilayer_network.get_nodes()
    ]

    f = plt.figure()
    # gravity=0.2,strongGravityMode=False,barnesHutTheta=1.2,edgeWeightInfluence=1,scalingRatio=2.0
    hairball_plot(graph,
                  network_colors,
                  layout_algorithm="custom_coordinates_initial_force",
                  layout_parameters=layout_parameters,
                  nodesize=0.02,
                  alpha_channel=0.30,
                  edge_width=0.001,
                  scale_by_size=False)

    f.savefig("../datasets/" + str(num_it) + "intact.png",
              bbox_inches='tight',
              dpi=300)


def plot_intact_basic(num_it=10):

    print("Plotting intact")
    multilayer_network = multinet.multi_layer_network().load_network(
        "../datasets/intact02.gpickle", input_type="gpickle",
        directed=False).add_dummy_layers()
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)

    # select top n communities by size
    top_n = 3
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    # assign node colors
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]

    layout_parameters = {"iterations": num_it, "forceImport": True}
    f = plt.figure()
    hairball_plot(graph,
                  network_colors,
                  legend=False,
                  layout_parameters=layout_parameters)
    f.savefig("../example_images/intact_" + str(num_it) + "_BH_basic.png",
              bbox_inches='tight',
              dpi=300)


def plot_intact_BH(num_it=10):

    print("Plotting intact")
    multilayer_network = multinet.multi_layer_network().load_network(
        "../datasets/intact02.gpickle", input_type="gpickle",
        directed=False).add_dummy_layers()
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)

    # select top n communities by size
    top_n = 3
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    # assign node colors
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]

    layout_parameters = {"iterations": num_it}
    f = plt.figure()
    hairball_plot(graph,
                  network_colors,
                  legend=False,
                  layout_parameters=layout_parameters)
    f.savefig("../example_images/intact_" + str(num_it) + "_BH.png",
              bbox_inches='tight',
              dpi=300)


if __name__ == "__main__":
    import time
    import numpy as np
    iteration_range = [0, 10, 100]
    for iterations in iteration_range:
        mean_times = []
        for j in range(2):
            start = time.time()
            # plot_intact_BH(iterations)
            plot_intact_embedding(iterations)
            end = (time.time() - start) / 60
            mean_times.append(end)
        print("Mean time for BK {}, iterations: {}".format(
            np.mean(mean_times), iterations))

    # mean_times = []
    # for j in range(iterations):
    #     start = time.time()
    #     plot_intact_embedding()
    #     end = (time.time() - start)/60
    #     mean_times.append(end)
    # print("Mean time for Py3 {}".format(np.mean(mean_times)))
