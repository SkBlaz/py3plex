## tensor-based operations examples

from py3plex.core import multinet
from py3plex.core import random_generators

## initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,8,0.05,directed=False)

## some simple visualization
visualization_params = {"display":True}
ER_multilayer.visualize_matrix(visualization_params)

## random node is accessed as follows
print(ER_multilayer[(1,1)])

## and random edge as
print(ER_multilayer[(1,1)][(2,1)])
