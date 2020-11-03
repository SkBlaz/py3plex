from py3plex.core import multinet
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from collections import Counter

network = multinet.multi_layer_network().load_network(
    input_file="../datasets/network.dat",
    directed=False,
    input_type="edgelist")

network.basic_stats()  # check core imports

network.read_ground_truth_communities("../datasets/community.dat")

partition = network.ground_truth_communities
# print(partition)
# select top n communities by size
top_n = 100
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

# assign node colors
color_mappings = dict(
    zip(top_n_communities,
        [x for x in colors_default if x != "black"][0:top_n]))

network_colors = [
    color_mappings[partition[x]]
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

# visualize the network's communities!
hairball_plot(network.core_network,
              color_list=network_colors,
              layout_parameters={"iterations": 100},
              scale_by_size=True,
              layout_algorithm="force",
              legend=False)
plt.show()
