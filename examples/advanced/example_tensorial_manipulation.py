"""Example: Tensor-based Operations and Network Access

This example demonstrates how to:
- Generate random Erdos-Renyi multilayer networks
- Visualize the adjacency tensor as a matrix
- Access node and edge data using bracket notation (tensor-like indexing)

The network can be accessed like a tensor, with nodes and edges indexed
using bracket notation for direct data retrieval.
"""
# SKIP_CI: external_deps - Requires visualization with display=True

from py3plex.core import random_generators

# initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,
                                                       8,
                                                       0.05,
                                                       directed=False)

# some simple visualization
visualization_params = {"display": True}
ER_multilayer.visualize_matrix(visualization_params)

some_nodes = list(ER_multilayer.get_nodes())[0:5]
some_edges = list(ER_multilayer.get_edges())[0:5]

# random node is accessed as follows
print(ER_multilayer[some_nodes[0]])

# and random edge as
print(ER_multilayer[some_edges[0][0]][some_edges[0][1]])
