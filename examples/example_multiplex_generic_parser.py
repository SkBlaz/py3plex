## parser for generic multiplex networks (../multiplex_datasets)

from py3plex.core import multinet

multilayer_network = multinet.multi_layer_network().load_network("../multilayer_datasets/MLKing",directed=True, input_type="multiplex_folder")

## read correctly?
multilayer_network.basic_stats()

## a very basic example of how to get temporal info
samples = 10
for timestamp, activated_edges in multilayer_network.activity.items():
    samples+=1
    print(timestamp,activated_edges[0:3])
    if samples > 10:
        break

## neighborhood of a specific node.
node_of_interest = "68"
nbrs = multilayer_network.get_neighbors(node_of_interest,layer_id=str(1)) # simply iterate through layers..
print(list(nbrs))



## check edges..
# for edge in multilayer_network.get_edges(data=True):
#     print(edge)
