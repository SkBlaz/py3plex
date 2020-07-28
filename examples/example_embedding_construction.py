from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization
from py3plex.visualization.embedding_visualization import embedding_tools
import json

## load network in GML
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/imdb_gml.gml", directed=True, input_type="gml")

# save this network as edgelist for node2vec
multilayer_network.save_network("../datasets/test.edgelist")

## call a specific embedding binary --- this is not limited to n2v
train_node2vec_embedding.call_node2vec_binary("../datasets/test.edgelist",
                                              "../datasets/test_embedding.emb",
                                              binary="../bin/node2vec",
                                              weighted=False)

## preprocess and check embedding
multilayer_network.load_embedding("../datasets/test_embedding.emb")

## visualize embedding
embedding_visualization.visualize_embedding(multilayer_network)

## output embedded coordinates as JSON
output_json = embedding_tools.get_2d_coordinates_tsne(multilayer_network,
                                                      output_format="json")

with open('../datasets/embedding_coordinates.json', 'w') as outfile:
    json.dump(output_json, outfile)
