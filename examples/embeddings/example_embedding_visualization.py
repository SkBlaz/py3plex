# simple embedding visualization example
from py3plex.core import multinet
from py3plex.visualization.embedding_visualization import embedding_visualization
from py3plex.utils import get_dataset_path

# visualization steps
multilayer_network = multinet.multi_layer_network().load_embedding(
    get_dataset_path("karate.emb"))
embedding_visualization.visualize_embedding(multilayer_network)
