## this file contains some of the multilayer network analysis network
## algorithms, used in the BioGrid analysis

class multiplex_network:

    def __init__(self,networks,edges,name):
        self.networks = networks
        self.edges = edges
        self.name = name

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
