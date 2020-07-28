## A simple example for extracting different layers based on subgraphs.

from py3plex.core import multinet
from py3plex.algorithms.statistics.basic_statistics import *

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=False,
    input_type="gpickle_biomine")

names, networks, multiedges = multilayer_network.get_layers()

## print some basic statistics of each network
for name, network, multiedgelist in zip(names, networks, multiedges):
    print(name, core_network_statistics(network))
