from py3plex.core import multinet
from py3plex.core import random_generators

ER_multilayer = random_generators.random_multilayer_ER(200,
                                                       6,
                                                       0.09,
                                                       directed=True)
ER_multilayer.visualize_network(show=True, no_labels=True)
