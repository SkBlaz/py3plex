# example network embedding using a binary
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization, embedding_tools
import json

# load network in GML
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/imdb_gml.gml", directed=True, input_type="gml")

# save this network as edgelist for node2vec
multilayer_network.save_network("../datasets/test.edgelist")

# Note: Node2Vec binary is no longer bundled with py3plex.
# Install from: https://github.com/snap-stanford/snap
# Or use pure Python alternatives: pip install node2vec
try:
    # call a specific embedding binary --- this is not limited to n2v
    train_node2vec_embedding.call_node2vec_binary("../datasets/test.edgelist",
                                                  "../datasets/test_embedding.emb",
                                                  binary="./node2vec",  # Assumes in PATH
                                                  weighted=False)

    # preprocess and check embedding
    multilayer_network.load_embedding("../datasets/test_embedding.emb")

    # visualize embedding
    embedding_visualization.visualize_embedding(multilayer_network)

    # output embedded coordinates as JSON
    output_json = embedding_tools.get_2d_coordinates_tsne(multilayer_network,
                                                          output_format="json")

    with open('../datasets/embedding_coordinates.json', 'w') as outfile:
        json.dump(output_json, outfile)
except FileNotFoundError as e:
    print(f"Node2Vec binary not found: {e}")
    print("Consider using pure Python alternatives:")
    print("  pip install node2vec")
    print("  pip install pecanpy")
