
## This is the main data structure container

import networkx as nx
from . import  parsers
from . import converters
from .HINMINE.IO import * ## parse the graph
from .HINMINE.decomposition import * ## decompose the graph
from .supporting import *
import scipy.sparse as sp
import tqdm

## visualization modules
from ..visualization.multilayer import *
from ..visualization.colors import all_color_names,colors_default

class multi_layer_network:

    ## constructor
    def __init__(self,verbose=True,network_type="multilayer",directed=True,dummy_layer="null"):
        """Class initializer
        
        This is the main class initializer method. User here specifies the type of the network, as well as other global parameters.

        """
        ## initialize the class
        
        self.core_network = None
        self.directed = directed
        self.dummy_layer = dummy_layer
        self.labels = None
        self.embedding = None
        self.verbose = verbose
        self.network_type = network_type ## assing network type

    def __getitem__(self,i,j=None):
        if j is None:
            return self.core_network[i]
        else:
            return self.core_network[i][j]
        pass
        
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
                                            network_type=self.network_type)

        if self.network_type == "multiplex":
            self.monitor("Checking multiplex edges..")
            self._to_multiplex()
        
        return self

    def load_temporal_edge_information(self,input_file=None,input_type="edge_activity",directxed=False,layer_mapping=None):
        """ A method for loading temporal edge information """
        
        self.temporal_edges = parsers.load_temporal_edge_information(input_file,input_type=input_type,layer_mapping=layer_mapping)
    
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
            
    def get_edges(self,data=False,multiplex_edges=False):
        """ A method for obtaining a network's edges """
        if self.network_type == "multilayer":        
            for edge in self.core_network.edges(data=data):
                yield edge
                
        elif self.network_type == "multiplex":
            if not multiplex_edges:
                for edge in self.core_network.edges(data=data,keys=True):
                    if edge[2] == "mpx":
                        continue
                    yield edge            
            else:            
                for edge in self.core_network.edges(data=data):
                    yield edge
        else:
            raise Exception("Specify network type!  e.g., multilayer_network")
                
    def get_nodes(self,data=False):
        """ A method for obtaining a network's nodes """
        
        for node in self.core_network.nodes(data=data):
            yield node
            

    def subnetwork(self,input_list=None,subset_by="layers"):

        input_list = set(input_list)
        if subset_by == "layers":
            subnetwork = self.core_network.subgraph([n for n in self.core_network.nodes() if n[1] in input_list])
            
        elif subset_by == "node_names":
            subnetwork = self.core_network.subgraph([n for n in self.core_network.nodes() if n[0] in input_list])

        elif subset_by == "node_layer_names":
            subnetwork = self.core_network.subgraph([n for n in self.core_network.nodes() if n in input_list])

        else:
            self.monitor("Please, select layers of node_names options..")

        tmp_net = multi_layer_network()
        tmp_net.core_network = subnetwork
        return tmp_net
            
    def get_layers(self,style="diagonal",compute_layouts="force",layout_parameters=None,verbose=True):

        """ A method for obtaining layerwise distributions """
        
        if self.verbose:
            self.monitor("Network splitting in progress")

        ## multilayer visualization
        if style == "diagonal":
            return converters.prepare_for_visualization(self.core_network,compute_layouts=compute_layouts,layout_parameters=layout_parameters,verbose=verbose)

        ## hairball visualization
        if style == "hairball":
            return converters.prepare_for_visualization_hairball(self.core_network,compute_layouts=True)

    def _initiate_network(self):
        if self.core_network is None:
            if self.directed:
                self.core_network = nx.MultiDiGraph()
            else:
                self.core_network = nx.MultiGraph()


    def monoplex_nx_wrapper(self,method,kwargs=None):
        ''' a generic networkx function wrapper '''
        
        result = eval("nx."+method+"(self.core_network)")
        return result
                
    def _generic_edge_dict_manipulator(self,edge_dict_list,target_function):

        if isinstance(edge_dict_list,dict):
            edge_dict = edge_dict_list
            if "source_type" in edge_dict_list.keys() and "target_type" in edge_dict_list.keys():
                edge_dict['v_for_edge'] = (edge_dict['target'],edge_dict['source_type'])
                edge_dict['u_for_edge'] = (edge_dict['source'],edge_dict['target_type'])
            else:
                edge_dict['v_for_edge'] = (edge_dict['target'],self.dummy_layer)
                edge_dict['u_for_edge'] = (edge_dict['source'],self.dummy_layer)
                
            del edge_dict['target'];del edge_dict['source']
            del edge_dict['target_type'];del edge_dict['source_type']
            eval("self.core_network."+target_function+"(**edge_dict)")
                
        else:
            for edge_dict in edge_dict_list:

                if "source_type" in edge_dict.keys() and "target_type" in edge_dict.keys():
                    edge_dict['v_for_edge'] = (edge_dict['target'],edge_dict['source_type'])
                    edge_dict['u_for_edge'] = (edge_dict['source'],edge_dict['target_type'])
                else:
                    edge_dict['v_for_edge'] = (edge_dict['target'],self.dummy_layer)
                    edge_dict['u_for_edge'] = (edge_dict['source'],self.dummy_layer)
                
                del edge_dict['target'];del edge_dict['source']
                del edge_dict['target_type'];del edge_dict['source_type']
                eval("self.core_network."+target_function+"(**edge_dict)")
        
    def _generic_edge_list_manipulator(self,edge_list,target_function,raw=False):

        if isinstance(edge_list[0],list):
            for edge in edge_list:
                n1,l1,n2,l2,w = edge
                if raw:
                    eval("self.core_network."+target_function+"((n1,l1),(n2,l2))")
                else:
                    eval("self.core_network."+target_function+"((n1,l1),(n2,l2),weight="+str(w)+",type=\"default\")")
            
        else:
            n1,l1,n2,l2,w = edge_list
            if raw:
                eval("self.core_network."+target_function+"((n1,l1),(n2,l2))")
            else:
                eval("self.core_network."+target_function+"((n1,l1),(n2,l2),weight="+str(w)+",type=\"default\"))")
    
    def _generic_node_dict_manipulator(self,node_dict_list,target_function):
        
        if isinstance(node_dict_list,dict):
            node_dict = node_dict_list
            node_dict["node_for_adding"] = node_dict["source"]
            
            if "type" in node_dict.keys():
                node_dict["node_for_adding"] = (node_dict["source"],node_dict['type'])
            else:
                node_dict["node_for_adding"] = (node_dict["source"],self.dummy_layer)                
            del node_dict["source"]
            eval("self.core_network."+target_function+"(**node_dict)")
            
        else:                
            for node_dict in node_dict_list:
                if "type" in node_dict.keys():
                    node_dict["node_for_adding"] = (node_dict["source"],node_dict['type'])
                else:
                    node_dict["node_for_adding"] = (node_dict["source"],self.dummy_layer)          
                del node_dict["source"]
                eval("self.core_network."+target_function+"(**node_dict)")                    

    def _generic_node_list_manipulator(self,node_list,target_function):

        if isinstance(node_list,list):
            for node in node_list:
                n1,l1 = node
                eval("self.core_network."+target_function+"((n1,l1))")
            
        else:
            n1,l1 = node_list
            eval("self.core_network."+target_function+"((n1,l1))")

            
    def _to_multiplex(self):
        self.network_type = "multiplex"
        self.core_network = add_mpx_edges(self.core_network)
                
    def add_edges(self,edge_dict_list,input_type="dict"):
        """ A method for adding edges.. """
        
        self._initiate_network()

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list,"add_edge")
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list,"add_edge")
        else:
            raise Exception("Please, use dict or list input.")

        if self.network_type == "multiplex":
            self.core_network = add_mpx_edges(self.core_network)

    def remove_edges(self,edge_dict_list,input_type="list"):
        """ A method for removing edges.. """
        
        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list,"remove_edge",raw=True)
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list,"remove_edge",raw=True)
        else:
            raise Exception("Please, use dict or list input.")

        if self.network_type == "multiplex":
            self.core_network = add_mpx_edges(self.core_network)
            
    def add_nodes(self,node_dict_list,input_type="dict"):
        """ A method for adding nodes.. """

        self._initiate_network()

        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list,"add_node")
            
        if self.network_type == "multiplex":
            self.core_network = add_mpx_edges(self.core_network)

    def remove_nodes(self,node_dict_list,input_type="dict"):
        
        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list,"remove_node")

        if input_type == "list":
            self._generic_node_list_manipulator(node_dict_list,"remove_node")
            
        if self.network_type == "multiplex":
            self.core_network = add_mpx_edges(self.core_network)

    def _get_num_layers(self):
        self.number_of_layers = len(set(x[1] for x in self.get_nodes()))

    def _get_num_nodes(self):
        self.number_of_unique_nodes = len(set(x[0] for x in self.get_nodes()))
            
    def _node_layer_mappings(self):
        
        pass
            
    def get_tensor(self,sparsity_type = "bsr"):
        ## convert this to a tensor of some sort
        ## maximum number of layers
        ## maximum number of nodes
        ## are nodes/layers strings? if so, do the encoding
        
        pass

    def get_supra_adjacency_matrix(self,mtype="sparse"):

        if mtype == "sparse":
            return nx.to_scipy_sparse_matrix(self.core_network)
        else:
            return nx.to_numpy_matrix(self.core_network)

    def visualize_matrix(self,kwargs):
        adjmat = self.get_supra_adjacency_matrix(mtype="dense")
        supra_adjacency_matrix_plot(adjmat,**kwargs)

    
    def visualize_network(self,style="diagonal",parameters_layers=None,parameters_multiedges=None,show=False,compute_layouts="force",layouts_parameters=None,verbose=True,orientation="upper",resolution=0.01):

        """ network visualization method """
        
        network_labels, graphs, multilinks = self.get_layers(style)

        if style == "diagonal":
            if parameters_layers is None:                
                ax = draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels,nodesize=6)
            else:
                ax = draw_multilayer_default(graphs,**parameters_layers)

            if parameters_multiedges is None:                
                enum = 1
                for edge_type,edges in tqdm.tqdm(multilinks.items()):
                    if edge_type == "mpx":
                        
                        ax = draw_multiedges(graphs,edges,alphachannel=0.2,linepoints="-",linecolor="red",curve_height=2,linmod="bottom",linewidth=1.7,resolution=resolution)
                    else:
                        ax = draw_multiedges(graphs,edges,alphachannel=0.05,linepoints="-.",linecolor="black",curve_height=2,linmod=orientation,linewidth=0.4,resolution=resolution)                      
                    enum+=1
            else:
                enum = 1
                for edge_type,edges in multilinks.items():
                    ax = draw_multiedges(graphs,edges,**parameters_multiedges)
                    enum+=1
            if show:
                plt.show()
            return ax
        
        elif style == "hairball":
            network_colors, graph = multilayer_network.get_layers(style="hairball")
            ax = hairball_plot(graph,network_colors,layout_algorithm="force")
            if show:
                plt.show()
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
