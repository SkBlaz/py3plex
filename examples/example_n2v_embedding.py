## example network embedding using a binary
from py3plex.core import multinet
from py3plex.wrappers import node2vec_embedding

multilayer_network = multinet.multi_layer_network.load_network("../datasets/imdb_gml.gml",directed=True,input_type="gml")

node2vec_embedding.learn_embedding(multinet.core_network,multinet.labels,embedding_outfile="test.emb",binary_path="./node2vec")
