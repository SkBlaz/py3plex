## tensor-based operations examples

from py3plex.core import multinet
from py3plex.core import random_generators

## initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,
                                                       8,
                                                       0.05,
                                                       directed=False)

## some simple visualization
visualization_params = {"display": True}
ER_multilayer.visualize_matrix(visualization_params)

some_nodes = [node for node in ER_multilayer.get_nodes()][0:5]
some_edges = [node for node in ER_multilayer.get_edges()][0:5]

## random node is accessed as follows
print(ER_multilayer[some_nodes[0]])

## and random edge as
print(ER_multilayer[some_edges[0][0]][some_edges[0][1]])
