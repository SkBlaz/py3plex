## decompose a complex network into a simple, homogeneous network according to a heuristic

#from py3plex.algorithms import *
from py3plex.core import multinet

multilayer_network = multinet.multi_layer_network().load_network(input_file="../datasets/imdb_gml.gml",directed=True,input_type="gml")

## import status
multilayer_network.basic_stats() ## check core imports
for decomposition in multilayer_network.get_decomposition():
    print(decomposition)
