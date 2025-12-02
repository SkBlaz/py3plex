## a simple visualization of a twitter network
# SKIP_CI: slow - Takes more than 10 seconds to complete
from py3plex.visualization.multilayer import draw_multilayer_default, plt
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

## Load the relevan layer names for later
layer_map = {}
with open(get_dataset_path("twitterlayers.txt")) as twl:
    for line in twl:
        line = line.strip()
        idx, lname = line.split()
        layer_map[idx] = lname

## Load the network first!
# Using network_type="multiplex" because:
# - This is a Twitter network where the same users appear across multiple layers
# - Each layer represents a different interaction type (retweet, mention, reply, etc.)
# - Automatic coupling edges connect the same user across all layers
# For networks with different node types per layer, use network_type="multilayer"
multilayer_network = multinet.multi_layer_network(network_type = "multiplex").load_network(get_dataset_path("test13.edges"), directed=False, input_type="multiplex_edges")

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
