## network statistics

from py3plex.core import multinet
from py3plex.algorithms.statistics.basic_statistics import *

multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/imdb_gml.gml", directed=True, input_type="gml")

## quick summary
print(multilayer_network.summary())

stats_frame = core_network_statistics(multilayer_network.core_network)
print(stats_frame)

top_n_by_degree = identify_n_hubs(multilayer_network.core_network, 20)
print(top_n_by_degree)
