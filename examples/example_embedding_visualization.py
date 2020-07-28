## simple embedding visualization example
from py3plex.core import multinet
from py3plex.visualization.embedding_visualization import embedding_visualization

## visualization steps
multilayer_network = multinet.multi_layer_network().load_embedding(
    "../datasets/karate.emb")
embedding_visualization.visualize_embedding(multilayer_network)
