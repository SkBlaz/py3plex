## visualize multiplex network dynamics

from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names,colors_default
from py3plex.core import multinet
import time
import matplotlib.pyplot as plt
import copy

## first parse the layer n1 n2 w edgelist
multilayer_network = multinet.multi_layer_network().load_network("../multilayer_datasets/MLKing/MLKing2013_multiplex.edges",directed=True, input_type="multiplex_edges")

## map layer ids to names
multilayer_network.load_layer_name_mapping("../multilayer_datasets/MLKing/MLKing2013_layers.txt")

## Finally, load termporal edge information
multilayer_network.load_network_activity("../multilayer_datasets/MLKing/MLKing2013_activity.txt")

## read correctly?
multilayer_network.basic_stats()

layout_parameters = {"iterations": 5}

## internally split to layers
multilayer_network.split_to_layers(style="diagonal",compute_layouts="force",layout_parameters=layout_parameters,multiplex=True)

## remove all internal networks' edges.
multilayer_network.remove_layer_edges() ## empty graphs are stored as self.empty_layers

## do the time series splits

n = 20000  #chunk row size
partial_slices = [multilayer_network.activity[i:i+n] for i in range(0,multilayer_network.activity.shape[0],n)]

for enx, time_slice in enumerate(partial_slices):
    
    fig, ax = plt.subplots(num=enx, clear=True)
    multilayer_network.fill_tmp_with_edges(time_slice)
    draw_multilayer_default(multilayer_network.tmp_layers,display=False,background_shape="circle",labels=multilayer_network.real_layer_names,axis=ax,remove_isolated_nodes=True)
    plt.savefig("../frames/"+str(enx)+"_frame.png")
    multilayer_network.remove_layer_edges() ## clean the slice edges
