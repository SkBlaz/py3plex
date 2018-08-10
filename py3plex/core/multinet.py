
## This is the main data structure container

import networkx as nx
from . import  parsers
from . import converters
from .HINMINE.IO import * ## parse the graph
from .HINMINE.decomposition import * ## decompose the graph
import scipy.sparse as sp

## visualization modules
from ..visualization.multilayer import *
from ..visualization.colors import all_color_names,colors_default

class multi_layer_network:

    ## constructor
    def __init__(self,verbose=True,network_type="multilayer",layer_node_code = "$LN$"):
        """Class initializer  
        
        This is the main class initializer method. User here specifies the type of the network, as well as other global parameters.

        """
        ## initialize the class
        
        self.core_network = None     
        self.labels = None
        self.embedding = None
        self.verbose = verbose
        self.network_type = network_type ## assing network type
        self.layer_node_code = layer_node_code
        
    def load_network(self,input_file=None, directed=False, input_type="gml",label_delimiter="---"):
        """Main method for loading networks"""
        ## core constructor methods
        
        self.input_file = input_file
        self.input_type = input_type
        self.label_delimiter = label_delimiter
        self.hinmine_network = None
        self.directed = directed
        self.temporal_edges = None
        self.core_network, self.labels = parsers.parse_network(self.input_file,
                                            self.input_type,
                                            directed=self.directed,
                                            label_delimiter=self.label_delimiter,
                                            network_type=self.network_type,
                                            layer_node_code = self.layer_node_code)
        
        return self

    def load_temporal_edge_information(self,input_file=None,input_type="edge_activity",directed=False,layer_mapping=None):
        """ A method for loading temporal edge information """
        
        self.temporal_edges = parsers.load_temporal_edge_information(input_file,input_type=input_type,layer_mapping=layer_mapping,layer_node_code = self.layer_node_code)
    
    def monitor(self,message):
        """ A simple monithor method """
        
        print("-"*20,"\n",message,"\n","-"*20)

    def save_network(self,output_file=None,output_type="edgelist"):
        """ A method for saving the network """
        
        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network,output_file=output_file)
        
    def basic_stats(self,target_network=None):

        """ A method for obtaining a network's statistics """
        
        if self.verbose:
            self.monitor("Computing core stats")
            
        if target_network is None:            
            print(nx.info(self.core_network))
            
        else:
            print(nx.info(target_network))
            
    def get_edges(self,data=False):
        """ A method for obtaining a network's edges """
        
        return self.core_network.edges(data=data)

    def get_nodes(self,data=False):
        """ A method for obtaining a network's nodes """
        
        return self.core_network.nodes(data=data)
        
    def get_layers(self,style="diagonal"):

        """ A method for obtaining layerwise distributions """
        
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

    def visualize_network(self,style="diagonal",parameters_layers=None,parameters_multiedges=None):

        """ network visualization method """
        
        network_labels, graphs, multilinks = self.get_layers(style)

        if style == "diagonal":
            if parameters_layers is None:                
                ax = draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels,layout_algorithm="force")
            else:
                ax = draw_multilayer_default(graphs,**parameters_layers)

            if parameters_multiedges is None:                
                enum = 1
                for edge_type,edges in multilinks.items():
                    ax = draw_multiedges(graphs,edges,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=5,linmod="upper",linewidth=0.4)
                    enum+=1
            else:
                enum = 1
                for edge_type,edges in multilinks.items():
                    ax = draw_multiedges(graphs,edges,**parameters_multiedges)
                    enum+=1                                    
            return ax
        
        elif style == "hairball":
            network_colors, graph = multilayer_network.get_layers(style="hairball")
            ax = hairball_plot(graph,network_colors,layout_algorithm="force")
            return ax

        else:
            raise Exception("Please, specify visualization style using: .style. keyword")
            
    def get_nx_object(self):
        """ Return only core network with proper annotations """
        return self.core_network

    def get_label_matrix(self):
        """ Return network labels  """
        return self.labels    

    def get_decomposition_cycles(self,cycle=None):
        """ A supporting method for obtaining decomposition triplets  """
        
        if self.hinmine_network is None:
            self.hinmine_network = load_hinmine_object(self.core_network, self.label_delimiter)
        return hinmine_get_cycles(self.hinmine_network)
    
    def get_decomposition(self, heuristic="all", cycle=None,parallel=True, alpha=1, beta=1):
        """ Core method for obtaining a network's decomposition in terms of relations  """
        
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
        """ Embedding loading method  """
        
        self.embedding = parsers.parse_embedding(embedding_file)
        return self
            
if __name__ == "__main__":

    multinet = multilayerNet("../../datasets/imdb_gml.gml")
    multinet.print_basic_stats()
