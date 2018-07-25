## visualization of a simple heterogeneous network
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names,colors_default
from py3plex.core import multinet

## multilayer -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")
multilayer_network.basic_stats() ## check core imports
network_labels, graphs, multilinks = multilayer_network.get_layers() ## get layers for visualization
draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels,layout_algorithm="force")

enum = 1
color_mappings = {idx : col for idx, col in enumerate(colors_default)}
for edge_type,edges in multilinks.items():
    draw_multiedges(graphs,edges,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=5,linmod="upper",linewidth=0.4)
    enum+=1
plt.show()


### basic string layout -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network("../datasets/imdb_gml.gml",directed=False,label_delimiter="---")
network_colors, graph = multilayer_network.get_layers(style="hairball")
hairball_plot(graph,network_colors,layout_algorithm="force")
plt.show()


## embedding-based layout (custom coordinates) -----------------------------------
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization,embedding_tools

multilayer_network = multinet.multi_layer_network().load_network("../datasets/goslim_mirna.gpickle",directed=False, input_type="gpickle_biomine")

multilayer_network.save_network("../datasets/test.edgelist")

## call a specific n2v compiled binary
train_node2vec_embedding.call_node2vec_binary("../datasets/test.edgelist","../datasets/test_embedding.emb",binary="../bin/node2vec",weighted=False)

## preprocess and check embedding
multilayer_network.load_embedding("../datasets/test_embedding.emb")
output_positions = embedding_tools.get_2d_coordinates_tsne(multilayer_network,output_format="pos_dict")

## custom layouts are part of the custom coordinate option
layout_parameters = {}
layout_parameters['pos'] = output_positions ## assign parameters
network_colors, graph = multilayer_network.get_layers(style="hairball")
hairball_plot(graph,network_colors,layout_algorithm="custom_coordinates",layout_parameters=layout_parameters)
plt.show()
