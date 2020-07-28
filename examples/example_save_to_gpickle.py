## simple example of how a network can be easily saved!
from py3plex.core import multinet

dataset = "../datasets/imdb_gml.gml"

## load as GML
multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

## save to gpickle
multilayer_network.save_network("../datasets/imdb.gpickle",
                                output_type="gpickle")
multilayer_network_new = multinet.multi_layer_network()

multilayer_network_new.load_network("../datasets/imdb.gpickle",
                                    input_type="gpickle")

## show some very basic stats
multilayer_network_new.basic_stats()
