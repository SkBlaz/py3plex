"""Example: Simple Embedding Visualization

This example demonstrates how to:
- Load pre-computed network embeddings from file
- Visualize node embeddings in 2D space
- Use t-SNE or other dimensionality reduction techniques

Network embeddings represent nodes as low-dimensional vectors
that preserve network structure. Visualization helps understand:
- Node clustering patterns
- Community structure
- Structural similarity between nodes

The example uses the Karate Club network with pre-computed
node2vec embeddings stored in .emb format.
"""
# SKIP_CI: external_deps - Requires specific dataset files

from py3plex.core import multinet
from py3plex.visualization.embedding_visualization import embedding_visualization
from py3plex.utils import get_dataset_path

# visualization steps
multilayer_network = multinet.multi_layer_network().load_embedding(
    get_dataset_path("karate.emb"))
embedding_visualization.visualize_embedding(multilayer_network)
