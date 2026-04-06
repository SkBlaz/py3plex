"""
Network Embedding with Node2Vec

Teaches:
- Generate node embeddings using Node2Vec algorithm
- Visualize embeddings using t-SNE dimensionality reduction
- Export embedding coordinates to JSON format
- Use external embedding tools with py3plex networks

Background:
Node2Vec learns low-dimensional representations of nodes by simulating
random walks on the network. These embeddings can be used for downstream
tasks like classification, clustering, and visualization.

Prerequisites:
- Dataset: imdb_gml.gml (IMDB collaboration network)
- Node2Vec binary (not bundled): https://github.com/snap-stanford/snap
- Alternative: pip install node2vec (pure Python implementation)

SKIP_CI: external_deps - Requires node2vec binary
"""

import json
import os

from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization, embedding_tools
from py3plex.exceptions import ExternalToolError
from py3plex.utils import get_dataset_path, get_data_path

# ===============================================================================
# Step 1: Load network and prepare for embedding
# ===============================================================================

multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("imdb_gml.gml"), directed=True, input_type="gml")

# Get the datasets directory for output files
datasets_dir = get_data_path("datasets")
json_output_path = os.path.join(datasets_dir, "embedding_coordinates.json")

# ===============================================================================
# Step 2: Export network to edgelist format for Node2Vec
# ===============================================================================

edgelist_path = os.path.join(datasets_dir, "test.edgelist")
multilayer_network.save_network(edgelist_path)

# ===============================================================================
# Step 3: Run Node2Vec embedding (requires binary or pure Python alternative)
# ===============================================================================

try:
    # Define embedding output path
    embedding_path = os.path.join(datasets_dir, "test_embedding.emb")

    # Call Node2Vec binary (assumes binary is in PATH or current directory)
    train_node2vec_embedding.call_node2vec_binary(edgelist_path,
                                                  embedding_path,
                                                  binary="./node2vec",  # Assumes in PATH
                                                  weighted=False)

    # Preprocess and check embedding
    multilayer_network.load_embedding(embedding_path)

    embedding_visualization.visualize_embedding(multilayer_network)
    output_json = embedding_tools.get_2d_coordinates_tsne(
        multilayer_network,
        output_format="json"
    )
    with open(json_output_path, 'w') as outfile:
        json.dump(output_json, outfile)
except (FileNotFoundError, ExternalToolError) as e:
    print(f"[ERROR] Node2Vec binary not found: {e}")
    print("Consider using pure Python alternatives:")
    print("pip install node2vec")
    print("pip install pecanpy")
