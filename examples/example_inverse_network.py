## a simple example on how to create an inverse network
from py3plex.core import multinet

## load some network
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/epigenetics.gpickle",
    directed=True,
    input_type="gpickle_biomine")
multilayer_network.basic_stats()

## override the core network object? If no, then it is stored as obj.core_network_inverse
multilayer_network.invert(override_core=True)
multilayer_network.basic_stats()
