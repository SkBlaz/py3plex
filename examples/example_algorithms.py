## this example demonstrates algorithm use on a multilayer network

from py3plex.algorithms import *
from collections import defaultdict

networks = defaultdict(list)
label_dict = {}

## get the nodes
with open("../testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_multiplex.edges") as me:
    for line in me:
        layer, n1, n2, weight = line.strip().split()
        networks[layer].append((n1,n2))

## get the labels
with open("../testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_layers.txt") as lx:
    for line in lx:
        lid, lname = line.strip().split()
        label_dict[lid] = lname

## draw the network
multilayer_network = []
labs = []

for network_id, network_data in networks.items():
    G = nx.Graph()
    G.add_edges_from(network_data)
    print(nx.info(G))
    multilayer_network.append(G)
    labs.append(label_dict[network_id])

## start the analysis with an object
multi_object = multiplex_network(multilayer_network,[],labs)

## some basic info
multi_object.print_basic_info()

## variability of degrees
print(multi_object.degree_layerwise_stats())

## k-clique based multi-community influence
print(multi_object.inter_community_influence(4))

