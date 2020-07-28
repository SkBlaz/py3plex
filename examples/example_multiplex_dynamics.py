## visualize multiplex network dynamics

from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names, colors_default
from py3plex.core import multinet
from collections import defaultdict
import time
import matplotlib.pyplot as plt
import seaborn as sns
import copy

## first parse the layer n1 n2 w edgelist
multilayer_network = multinet.multi_layer_network().load_network(
    "../multilayer_datasets/MLKing/MLKing2013_multiplex.edges",
    directed=True,
    input_type="multiplex_edges")

## map layer ids to names
multilayer_network.load_layer_name_mapping(
    "../multilayer_datasets/MLKing/MLKing2013_layers.txt")

## Finally, load termporal edge information
multilayer_network.load_network_activity(
    "../multilayer_datasets/MLKing/MLKing2013_activity.txt")

## read correctly?
multilayer_network.basic_stats()

layout_parameters = {"iterations": 1}

## internally split to layers
multilayer_network.split_to_layers(style="diagonal",
                                   compute_layouts="force",
                                   layout_parameters=layout_parameters,
                                   multiplex=True)

## remove all internal networks' edges.
multilayer_network.remove_layer_edges(
)  ## empty graphs are stored as self.empty_layers

## do the time series splits

n = 1000  #chunk row size
partial_slices = [
    multilayer_network.activity[i:i + n]
    for i in range(0, multilayer_network.activity.shape[0], n)
]

num_edges = defaultdict(list)
for enx, time_slice in enumerate(partial_slices):
    if enx < 12:
        plt.subplot(4, 3, enx + 1)
        plt.title("Time slice: {}".format(enx + 1))
        num_edges_int = dict()
        for enx, row in time_slice.iterrows():
            real_name = multilayer_network.real_layer_names[int(row.layer_name)
                                                            - 1]
            if real_name not in num_edges_int:
                num_edges_int[real_name] = 1
            else:
                num_edges_int[real_name] += 1
        for k, v in num_edges_int.items():
            num_edges[k].append(v)
        multilayer_network.fill_tmp_with_edges(time_slice)
        draw_multilayer_default(multilayer_network.tmp_layers,
                                labels=multilayer_network.real_layer_names,
                                display=False,
                                background_shape="circle",
                                axis=None,
                                remove_isolated_nodes=True,
                                node_size=0.1,
                                edge_size=0.01)
        multilayer_network.remove_layer_edges()  ## clean the slice edges
plt.show()
#plt.savefig("../images/temporal.png",dpi=300)
sns.set_style("whitegrid")
clx = {"RT": "red", "MT": "green", "RE": "blue"}

plt.subplot(1, 1, 1)
plt.title("Temporal edge dynamics")
slices = []
for k, v in num_edges.items():
    sns.lineplot(list(range(len(v))), v, label=k, color=clx[k])
plt.legend()
plt.xlabel("Time slice")
plt.ylabel("Number of edges")
plt.show()
