from py3plex.core import multinet
from py3plex.core import random_generators

ER_multilayer = random_generators.random_multilayer_ER(500,6,0.02,directed=False)
ER_multilayer.visualize_network(show=True)
