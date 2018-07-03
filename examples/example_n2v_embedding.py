## example network embedding using a binary
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding

multilayer_network = multinet.multi_layer_network().load_network("../datasets/imdb_gml.gml",directed=True,input_type="gml")

## save this network as edgelist for node2vec
multilayer_network.save_network("../datasets/test.edgelist")

train_node2vec_embedding.call_node2vec_binary("../datasets/test.edgelist","test.emb",binary="./node2vec",weighted=False)
