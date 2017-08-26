## this file contains some of the multilayer network analysis network
## algorithms, used in the BioGrid analysis
import networkx as nx
from collections import defaultdict


class multiplex_network:

    def __init__(self,networks,edges,name):
        self.networks = networks
        self.multiedges = edges
        self.name = name

    def inter_community_influence(self,minclique):

        communities = {}
        for nid,network in enumerate(self.networks):
            communities[nid] = nx.k_clique_communities(network, minclique)

        partial_mpx_community = 0
        for k,v communities.items():
            ## get length of all nodes in communities
            ## get percentage of nodes in multiplex
            ## add ratio to partial_mpx_community
            ## finally, divide by nummber of all layers
            pass
        
            
    def connectivity_ratio(self):

        ## compute ratio of inter_edges/intra_    
        pass
    
    def layerwise_modularity_variability(self):
        ## check how community formation varies accross layers
        pass

    def layerwise_modularity(self):
        ## for layer in layers:
        ## do, compute modularity and return a vector of reals
        pass

    def inter_layer_connections(self):

        ## number of inter-layer connections
        pass
    
    def multiplex_entropy(self):

        ## 
        pass

    def clustering_coefficient(self):

        ##
        pass

    def transitivity(self):

        ##
        pass
