# An example how nx functions can be used.

from py3plex.core import random_generators

# generate a toy network
ER_net = random_generators.random_multilayer_ER(300, 6, 0.05, directed=False)

# compute node centralities --- this will be applied to the network object
centralities = ER_net.monoplex_nx_wrapper("degree_centrality")

# get top nodes by centrality
print(sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:5])
