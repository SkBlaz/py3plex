
## This is the main data structure container

import networkx as nx
from . import  parsers
from . import converters
from .HINMINE.IO import * ## parse the graph
from .HINMINE.decomposition import * ## decompose the graph
import scipy.sparse as sp

class multi_layer_network:

    ## constructor
    def __init__(self,verbose=True):
        self.core_network = None     
        self.labels = None
        self.embedding = None
        self.verbose = verbose
        
    def load_network(self,input_file=None, directed=False, input_type="gml",label_delimiter="---"):
        ## core constructor methods
        self.input_file = input_file
        self.input_type = input_type
        self.label_delimiter = label_delimiter
        self.hinmine_network = None
        self.directed = directed
        self.core_network, self.labels = parsers.parse_network(self.input_file, self.input_type, directed=self.directed, label_delimiter=self.label_delimiter)
        
        return self
    
    def monitor(self,message):
        print("-"*20,"\n",message,"\n","-"*20)

    def save_network(self,output_file=None,output_type="edgelist"):
        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network,output_file=output_file)
        
    def basic_stats(self,target_network=None):
        if self.verbose:
            self.monitor("Computing core stats")
        if target_network is None:
            print(nx.info(self.core_network))
        else:
            print(nx.info(target_network))
            
    def get_edges(self,data=False):
        return self.core_network.edges(data=data)

    def get_nodes(self,data=False):
        return self.core_network.nodes(data=data)
        
    def get_layers(self,style="diagonal"):

        if self.verbose:
            self.monitor("Network splitting in progress")

        ## multilayer visualization
        if style == "diagonal":
            return converters.prepare_for_visualization(self.core_network)

        ## hairball visualization
        if style == "hairball":
            return converters.prepare_for_visualization_hairball(self.core_network)
            
    def get_tensor(self):
        ## convert this to a tensor of some sort
        pass

    def get_nx_object(self):
        return self.core_network

    def get_label_matrix(self):
        return self.labels    

    def get_decomposition_cycles(self,cycle=None):
        
        if self.hinmine_network is None:
            self.hinmine_network = load_hinmine_object(self.core_network, self.label_delimiter)
        return hinmine_get_cycles(self.hinmine_network)
    
    def get_decomposition(self, heuristic="all", cycle=None,parallel=True, alpha=1, beta=1):

        if heuristic == "all":
            heuristic = ["idf","tf","chi","ig","gr","delta","rf","okapi"] ## all available
        if self.hinmine_network is None:
            if self.verbose:
                print("Loading into a hinmine object..")
            self.hinmine_network = load_hinmine_object(self.core_network, self.label_delimiter)

        if beta > 0:
            subset_nodes = []
            for n in self.core_network.nodes(data=True):
                if 'labels' in n[1]:
                    subset_nodes.append(n[0])
            induced_net = self.core_network.subgraph(subset_nodes)
            for e in induced_net.edges(data=True):
                e[2]['weight'] = float(e[2]['weight'])            
            induced_net = nx.to_scipy_sparse_matrix(induced_net)
            
        for x in heuristic:
            try:
                dout = hinmine_decompose(self.hinmine_network,heuristic=x, cycle=cycle, parallel = parallel)
                decomposition = dout.decomposed['decomposition']
                ## use alpha and beta levels
                final_decomposition = alpha*decomposition + beta*induced_net
                yield (final_decomposition,dout.label_matrix, x)
            except:
                print("No decomposition found for:", x)

    def load_embedding(self,embedding_file):
        self.embedding = parsers.parse_embedding(embedding_file)
        return self
            
if __name__ == "__main__":

    multinet = multilayerNet("../../datasets/imdb_gml.gml")
    multinet.print_basic_stats()
