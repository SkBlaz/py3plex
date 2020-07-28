## a simple example for wrapping entworkx functions

from py3plex.core import multinet
from py3plex.core import random_generators

multilayer_network = random_generators.random_multilayer_ER(300,
                                                            6,
                                                            0.05,
                                                            directed=False)

## treat as monoplex network
centralities = multilayer_network.monoplex_nx_wrapper("betweenness_centrality")
print(centralities)
