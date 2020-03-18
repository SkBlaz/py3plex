from py3plex.core import multinet
import pandas
import tqdm
from py3plex.core import random_generators
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names,colors_default
import networkx as nx
from numpy import array

## An example general multilayer network
A = multinet.multi_layer_network()

B = multinet.multi_layer_network()

## Edges can also be added as lists: [n1,l1,n2,l2,w]
layer_1 = [["1","layer1","2","layer1",0.18114714],
           ["1","layer1","4","layer1",0.02990695],
           ["1","layer1","5","layer1",0.03590235],
           ["2","layer1","4","layer1",0.08797787],
           ["2","layer1","5","layer1",0.03461894],
           ["3","layer1","4","layer1",0.05023782],
           ["3","layer1","5","layer1",0.14783362],
           ["4","layer1","5","layer1",0.13015703]]

layer_2 = [["1D","layer2","2D","layer2",1],
           ["1D","layer2","3D","layer2",2],
           ["1D","layer2","4D","layer2",3],
           ["1D","layer2","5D","layer2",4],
           ["2D","layer2","3D","layer2",1],
           ["2D","layer2","4D","layer2",2],
           ["2D","layer2","5D","layer2",3],
           ["3D","layer2","4D","layer2",1],
           ["3D", "layer2", "5D", "layer2", 2],
           ["4D", "layer2", "5D", "layer2", 1]]

inter_layer_edges = [["1","layer1","1D","layer2",1],
                     ["2","layer1","2D","layer2",1],
                     ["3","layer1","3D","layer2",1],
                     ["4","layer1","4D","layer2",1],
                     ["5","layer1","5D","layer2",1]]

## specify that input is list, all else is recognized by Py3plex!
A.add_edges(layer_1,input_type="list")
A.add_edges(layer_2,input_type="list")
A.add_edges(inter_layer_edges,input_type="list")
print(list(A.get_edges()))

multilayer_network = A
multilayer_network.visualize_network(style="diagonal")
plt.show()

A.basic_stats()

centralities = A.monoplex_nx_wrapper("degree_centrality")
A.monitor(centralities)

import networkx as nx
G = nx.cycle_graph(4)
sim = nx.simrank_similarity(G)
lol = [[sim[u][v] for v in sorted(sim[u])] for u in sorted(sim)]

print("Similarity", lol)
