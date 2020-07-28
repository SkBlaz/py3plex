## a class for random graph generation
import networkx as nx
import numpy as np
from .multinet import *


def random_multilayer_ER(n, l, p, directed=False):
    """ random multilayer ER """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    network = nx.fast_gnp_random_graph(n, p, seed=None, directed=directed)
    layers = dict(zip(network.nodes(), np.random.randint(l, size=n)))
    for edge in network.edges():
        G.add_edge((edge[0], layers[edge[0]]), (edge[1], layers[edge[1]]),
                   type="default")

    ## construct the ppx object
    no = multi_layer_network(network_type="multilayer").load_network(
        G, input_type="nx", directed=directed)
    return no


def random_multiplex_ER(n, l, p, directed=False):
    """ random multilayer ER """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for lx in range(l):
        network = nx.fast_gnp_random_graph(n, p, seed=None, directed=directed)
        for edge in network.edges():
            G.add_edge((edge[0], lx), (edge[1], lx), type="default")

    ## construct the ppx object
    no = multi_layer_network(network_type="multiplex").load_network(
        G, input_type="nx", directed=directed)
    return no


def random_multiplex_generator(n, m, d=0.9):

    #generate a multiplex network from a random bipartite graph
    #n: number of nodes (int)
    #m: number of layers (int)
    #d: layer dropout (to avoid cliques) (float [0..1])

    layers = range(m)
    node_to_layers = {}
    layer_to_nodes = {}
    G = nx.MultiGraph()
    for node in range(n):
        layer_list = random.sample(layers, random.choice(layers))
        node_to_layers[node] = layer_list
        for l in layer_list:
            layer_to_nodes[l] = layer_to_nodes.get(l, []) + [node]

    edge_to_layers = {}
    for l, nlist in layer_to_nodes.items():
        clique = tuple(itertools.combinations(nlist, 2))
        nnodes = len(nlist)
        edge_sample = random.sample(clique,
                                    int(d * (nnodes * (nnodes - 1)) / 2))
        for p1, p2 in edge_sample:
            if p1 < p2:
                e = tuple([p1, p2])
            else:
                e = tuple([p2, p1])

            edge_to_layers[e] = edge_to_layers.get(e, []) + [l]

    edgelist = []
    for k, v in edge_to_layers.items():
        for l in v:
            G.add_edge((k[0], l), (k[1], l), type="default", weight=1)

    return G
