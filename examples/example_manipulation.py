## this example demonstrates how a network can be manipulated

from py3plex.core import multinet

## general multilayer networks

multilayer_network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")

network_edges = multilayer_network.get_edges(data=True) ## edge iterator
network_nodes = multilayer_network.get_nodes(data=True) ## node iterator
network_layers = multilayer_network.get_layers(style="diagonal") ## layerwise networks

## Multiplex networks

multiplex_network = multinet.multi_layer_network(network_type="multiplex").load_network("../datasets/moscow_edges.txt",directed=True, input_type="multiplex_edges")

## multiplex networks can be couples --- to include coupled edges, use mpx_edges parameter
network_edges = multiplex_network.get_edges(data=True,mpx_edges=False) ## edge iterator
multiplex_network.monitor(str(len(list(network_edges)))+" Non-coupled only edges.")

network_edges = multiplex_network.get_edges(data=True,mpx_edges=True) ## edge iterator
multiplex_network.monitor(str(len(list(network_edges)))+" Including coupled  edges.")

network_nodes = multiplex_network.get_nodes(data=True) ## node iterator
