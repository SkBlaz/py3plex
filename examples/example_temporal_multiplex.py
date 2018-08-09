## a simple example for manipulation of multiplex networks

from py3plex.visualization.multilayer import *
from py3plex.core import multinet
from py3plex.algorithms.temporal_multiplex import *

## load the network as multiplex (coupled) network. (layer n1 n2 weight)
multilayer_network = multinet.multi_layer_network(network_type="multiplex").load_network("../datasets/moscow_edges.txt",directed=True, input_type="multiplex_edges")

multilayer_network.basic_stats() ## check core imports

multilayer_network.load_temporal_edge_information("../datasets/moscow_activity.txt",input_type="edge_activity",layer_mapping="../datasets/moscow_layer_mapping.txt")

## split timeframe to 50 equally sized slices
time_network_slices = split_to_temporal_slices(multilayer_network,slices=5)

multilayer_network.monitor("Proceeding to visualization part..")
## for each slice -- plot the network

frame_images = []

for time,network_slice in time_network_slices.items():

    print(network_slice.basic_stats())
    
    ## obtain visualization layers
    network_labels, graphs, multilinks = network_slice.get_layers()

    multilayer_network.monitor("Drawing in progress")
    
    ## draw the type-wise projection
    a = draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels,layout_algorithm="force")

    multilayer_network.monitor("Adding edges..")
    ## add trans-layer edges (i.e., multiplex)    
    enum = 1
    color_mappings = {idx : col for idx, col in enumerate(colors_default)}
    for edge_type,edges in multilinks.items():
        draw_multiedges(graphs,edges,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=5,linmod="upper",linewidth=0.4)
        enum+=1
    #plt.show()
    frame_images.append(a)
    plt.show()
    plt.clf()

