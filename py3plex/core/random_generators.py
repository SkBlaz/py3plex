## a class for random graph generation
import networkx as nx
import numpy as np
from .multinet import *

def random_multilayer_ER(n,l,p,directed=False):
    """ random multilayer ER """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
        
    network = nx.fast_gnp_random_graph(n, p, seed=None, directed=directed)
    layers = dict(zip(network.nodes(),np.random.randint(l, size=n)))
    for edge in network.edges():
        G.add_edge((edge[0],layers[edge[0]]),(edge[1],layers[edge[1]]),type="default")
    
    ## construct the ppx object
    no = multi_layer_network(network_type="multilayer").load_network(G,input_type="nx",directed=directed)
    return no

def random_multiplex_ER(n,l,p,directed=False):
    """ random multilayer ER """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
        
    for lx in range(l):
        network = nx.fast_gnp_random_graph(n, p, seed=None, directed=directed)        
        for edge in network.edges():
            G.add_edge((edge[0],lx),(edge[1],lx),type="default")
    
    ## construct the ppx object
    no = multi_layer_network(network_type="multiplex").load_network(G,input_type="nx",directed=directed)
    return no
