# example network embedding using a binary
# SKIP_CI: external_deps - Requires node2vec binary
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization, embedding_tools
import json
import os
from py3plex.utils import get_dataset_path, get_data_path

# load network in GML
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("imdb_gml.gml"), directed=True, input_type="gml")

# Get the datasets directory for output files
datasets_dir = get_data_path("datasets")

# save this network as edgelist for node2vec
edgelist_path = os.path.join(datasets_dir, "test.edgelist")
multilayer_network.save_network(edgelist_path)

# Note: Node2Vec binary is no longer bundled with py3plex.
# Install from: https://github.com/snap-stanford/snap
# Or use pure Python alternatives: pip install node2vec
try:
    # Define embedding output path
    embedding_path = os.path.join(datasets_dir, "test_embedding.emb")

    # call a specific embedding binary --- this is not limited to n2v
    train_node2vec_embedding.call_node2vec_binary(edgelist_path,
                                                  embedding_path,
                                                  binary="./node2vec",  # Assumes in PATH
                                                  weighted=False)

    # preprocess and check embedding
    multilayer_network.load_embedding(embedding_path)

    # visualize embedding
    embedding_visualization.visualize_embedding(multilayer_network)

    # output embedded coordinates as JSON
    output_json = embedding_tools.get_2d_coordinates_tsne(multilayer_network,
                                                          output_format="json")

    json_output_path = os.path.join(datasets_dir, 'embedding_coordinates.json')
    with open(json_output_path, 'w') as outfile:
        json.dump(output_json, outfile)
except FileNotFoundError as e:
    print(f"Node2Vec binary not found: {e}")
    print("Consider using pure Python alternatives:")
    print("  pip install node2vec")
    print("  pip install pecanpy")
