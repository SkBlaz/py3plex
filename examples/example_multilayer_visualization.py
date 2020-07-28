## visualization of a simple heterogeneous network
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names, colors_default
from py3plex.core import multinet

## you can try the default visualization options --- this is the simplest option/

## multilayer
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/goslim_mirna.gpickle",
    directed=False,
    input_type="gpickle_biomine")
multilayer_network.basic_stats()  ## check core imports

## a simple hairball plot
multilayer_network.visualize_network(style="hairball")
plt.show()

## going full py3plex (default 100 iterations, layout_parameters can carry additional parameters)
multilayer_network.visualize_network(style="diagonal")
plt.show()

## visualization from a simple file
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/edgeList.txt", directed=False, input_type="multiedgelist")
multilayer_network.basic_stats()
multilayer_network.visualize_network()
plt.show()

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multiL.txt", directed=True, input_type="multiedgelist")
multilayer_network.basic_stats()
multilayer_network.visualize_network(style="diagonal")
plt.show()

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multinet_k100.txt", directed=True, input_type="multiedgelist")
multilayer_network.basic_stats()
multilayer_network.visualize_network()
plt.show()

## multilayer -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=True,
    input_type="gpickle_biomine")
multilayer_network.basic_stats()  ## check core imports
#multilayer_network.visualize_network() ## visualize
#plt.show()

## You can also access individual graphical elements separately!

network_labels, graphs, multilinks = multilayer_network.get_layers(
)  ## get layers for visualizat# ion
draw_multilayer_default(graphs,
                        display=False,
                        background_shape="circle",
                        labels=network_labels)

enum = 1
color_mappings = {idx: col for idx, col in enumerate(colors_default)}
for edge_type, edges in multilinks.items():

    #    network_list,multi_edge_tuple,input_type="nodes",linepoints="-.",alphachannel=0.3,linecolor="black",curve_height=1,style="curve2_bezier",linewidth=1,invert=False,linmod="both",resolution=0.1
    print(edge_type)
    if edge_type == "refers_to":
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.05,
                        linepoints="--",
                        linecolor="lightblue",
                        curve_height=5,
                        linmod="upper",
                        linewidth=0.4)
    elif edge_type == "refers_to":
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints=":",
                        linecolor="green",
                        curve_height=5,
                        linmod="upper",
                        linewidth=0.3)
    elif edge_type == "belongs_to":
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints=":",
                        linecolor="red",
                        curve_height=5,
                        linmod="upper",
                        linewidth=0.4)
    elif edge_type == "codes_for":
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints=":",
                        linecolor="orange",
                        curve_height=5,
                        linmod="upper",
                        linewidth=0.4)
    else:
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints="-.",
                        linecolor="black",
                        curve_height=5,
                        linmod="both",
                        linewidth=0.4)
    enum += 1
plt.show()
plt.clf()

## monotone coloring
draw_multilayer_default(graphs,
                        display=False,
                        background_shape="rectangle",
                        labels=network_labels,
                        networks_color="black",
                        rectanglex=2,
                        rectangley=2,
                        background_color="default")

enum = 1
for edge_type, edges in multilinks.items():
    draw_multiedges(graphs,
                    edges,
                    alphachannel=0.2,
                    linepoints="--",
                    linecolor="black",
                    curve_height=2,
                    linmod="upper",
                    linewidth=0.4)
    enum += 1
plt.show()

## basic string layout ----------------------------------
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=False,
    label_delimiter="---",
    input_type="gpickle_biomine")
network_colors, graph = multilayer_network.get_layers(style="hairball")

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import colors_default
from collections import Counter

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_network", default="../datasets/cora.mat")
parser.add_argument("--input_type", default="sparse")
args = parser.parse_args()

network = multinet.multi_layer_network().load_network(
    input_file=args.input_network, directed=False, input_type=args.input_type
)  ## network and group objects must be present within the .mat object

network.basic_stats()  ## check core imports

partition = cw.louvain_communities(network.core_network)

## select top n communities by size
top_n = 10
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

## assign node colors
color_mappings = dict(zip(top_n_communities, colors_default[0:top_n]))

network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

## visualize the network's communities!
hairball_plot(network.core_network,
              color_list=network_colors,
              layered=False,
              layout_parameters={"iterations": 50},
              scale_by_size=True,
              layout_algorithm="force",
              legend=False)
plt.show()
hairball_plot(graph, network_colors, legend=True)
plt.show()

## string layout for larger network -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/soc-Epinions1.edgelist",
    label_delimiter="---",
    input_type="edgelist",
    directed=True)
hairball_plot(multilayer_network.core_network,
              layout_parameters={"iterations": 300})
plt.show()

## embedding-based layout (custom coordinates) -----------------------------------
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization, embedding_tools

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/goslim_mirna.gpickle",
    directed=False,
    input_type="gpickle_biomine")

multilayer_network.save_network("../datasets/test.edgelist")

## call a specific n2v compiled binary
train_node2vec_embedding.call_node2vec_binary("../datasets/test.edgelist",
                                              "../datasets/test_embedding.emb",
                                              binary="../bin/node2vec",
                                              weighted=False)

## preprocess and check embedding
multilayer_network.load_embedding("../datasets/test_embedding.emb")
output_positions = embedding_tools.get_2d_coordinates_tsne(
    multilayer_network, output_format="pos_dict")

## custom layouts are part of the custom coordinate option
layout_parameters = {}
layout_parameters['pos'] = output_positions  ## assign parameters
network_colors, graph = multilayer_network.get_layers(style="hairball")
hairball_plot(graph,
              network_colors,
              layout_algorithm="custom_coordinates",
              layout_parameters=layout_parameters)
plt.show()
