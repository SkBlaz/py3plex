# compute and visualize powerlaw distributions (and other alternatives)

import networkx as nx
from py3plex.algorithms.statistics.topology import plot_power_law
from py3plex.core import multinet

# examples use the node degrees, note that any node property applies.

# on a simple network
G = nx.powerlaw_cluster_graph(1000, 3, 0.5, 1573)
val_vect = sorted(dict(nx.degree(G)).values(), reverse=True)
plot_power_law(val_vect, "", "Node degree", "individual node")

# on py3plex objects -- consider all edges and nodes
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=False,
    input_type="gpickle_biomine")
val_vect = sorted(dict(nx.degree(multilayer_network.core_network)).values(),
                  reverse=True)
plot_power_law(val_vect, "", "Node degree", "individual node")

print(multilayer_network.test_scale_free())
