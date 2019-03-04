### simple supra adjacency matrix manipulation

## tensor-based operations examples

from py3plex.core import multinet
from py3plex.core import random_generators

## initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,8,0.05,directed=False)

mtx = ER_multilayer.get_supra_adjacency_matrix()
print(mtx)
print(mtx.shape)
