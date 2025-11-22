## decomposition via different meta paths
# SKIP_CI: slow - Meta-path decomposition takes more than 10 seconds

from py3plex.core import multinet
import numpy as np
from py3plex.utils import get_dataset_path

# a simple decomposition example. Note that target nodes need to have "labels" property, to which labels are assigned in class1---class2---...and so on...

dataset = get_dataset_path("imdb.gpickle")

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

print(f"Running optimization for {dataset}")
multilayer_network.basic_stats()  # check core imports
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))

for tcycle in triplet_set:
    print(tcycle)
    for decomposition in multilayer_network.get_decomposition(heuristic=["tf"],
                                                              cycle=[tcycle]):
        network = decomposition[0]
        print(network.todense())
        print(np.max(network))

## HINMINE multipath -> sum across all paths.
for decomposition in multilayer_network.get_decomposition(heuristic=["tf"],
                                                          cycle=triplet_set):
    network = decomposition[0]
    print(network.todense())
    print(np.max(network))
