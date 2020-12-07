## a simple visualization of a twitter network
from py3plex.visualization.embedding_visualization import embedding_tools
from py3plex.wrappers import train_node2vec_embedding
from collections import Counter
from py3plex.visualization.colors import colors_default
from py3plex.visualization.multilayer import draw_multiedges, draw_multilayer_default, hairball_plot, plt
from py3plex.core import multinet

## Load the relevan layer names for later
layer_map = {}
with open("../datasets/twitterlayers.txt") as twl:
    for line in twl:
        line = line.strip()
        idx, lname = line.split()
        layer_map[idx] = lname
        
## Loade the network first!
multilayer_network = multinet.multi_layer_network(network_type = "multiplex").load_network("../datasets/test13.edges", directed=False, input_type="multiplex_edges")

## Let's customize it a bit.
network_labels, graphs, multilinks = multilayer_network.get_layers()
print(network_labels)
network_labels = [layer_map[k] for k in network_labels]
draw_multilayer_default(graphs,
                        display=False,
                        background_shape="circle",
                        labels=network_labels,
                        node_size=1)


plt.show()
