## this example demonstrates the use of basic algorithms

import matplotlib.pyplot as plt
import networkx as nx

from py3plex.multilayer import *
from py3plex.algorithms import *

from collections import defaultdict

## this example apart from visualization demonstrates some common algorithms
## algorithms operate on multiplex object, as seen below.

networks = defaultdict(list)
label_dict = {}

## get the nodes
with open("testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_multiplex.edges") as me:
    for line in me:
        layer, n1, n2, weight = line.strip().split()
        networks[layer].append((n1,n2))

## get the labels
with open("testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_layers.txt") as lx:
    for line in lx:
        lid, lname = line.strip().split()
        label_dict[lid] = lname

## draw the network
multilayer_network = []
labs = []
for network_id,network_data in networks.items():
    G = nx.Graph()
    G.add_edges_from(network_data)
    print(nx.info(G))
    tmp_pos=nx.spring_layout(G)
    nx.set_node_attributes(G,'pos',tmp_pos)
    multilayer_network.append(G)
    labs.append(label_dict[network_id])

draw_multilayer_default(multilayer_network,background_shape="circle",display=True,labels=labs,networks_color="rainbow")
