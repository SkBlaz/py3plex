
## This is the main data structure container

import networkx as nx
import itertools
from . import  parsers
from . import converters
from .HINMINE.IO import * ## parse the graph
from .HINMINE.decomposition import * ## decompose the graph
from .supporting import *
import scipy.sparse as sp
import tqdm

## visualization modules
try:
    from ..visualization.multilayer import *
    from ..visualization.colors import all_color_names,colors_default
    server_mode  = False
except:
    server_mode = True

class multi_layer_network:

    ## constructor
    def __init__(self,verbose=True,network_type="multilayer",directed=True,dummy_layer="null",label_delimiter="---"):
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
        self.sparse_enabled = False
        self.hinmine_network = None
        self.label_delimiter = label_delimiter
        
    def __getitem__(self,i,j=None):
        if j is None:
            return self.core_network[i]
        else:
            return self.core_network[i][j]
        pass
        
    def load_network(self,input_file=None, directed=False, input_type="gml"):
        """Main method for loading networks"""
        ## core constructor methods
        
        self.input_file = input_file
        self.input_type = input_type
        self.directed = directed
        self.temporal_edges = None

        if input_type == "sparse":
            self.sparse_enabled = True
            
        self.core_network, self.labels = parsers.parse_network(self.input_file,
                                            self.input_type,
                                            directed=self.directed,
                                            label_delimiter=self.label_delimiter,
                                            network_type=self.network_type)

        if self.network_type == "multiplex":
            self.monitor("Checking multiplex edges..")
            self._to_multiplex()
        
        return self

    def to_sparse_matrix(self,replace_core=False):

        """
        Conver the matrix to scipy-sparse version. This is useful for classification.
        """
        
        if replace_core:
            self.core_network = nx.to_scipy_sparse_matrix(self.core_network)
            self.core_sparse = None
        else:
            self.core_sparse = nx.to_scipy_sparse_matrix(self.core_network)

    def load_temporal_edge_information(self,input_file=None,input_type="edge_activity",directxed=False,layer_mapping=None):
        """ A method for loading temporal edge information """
        
        self.temporal_edges = parsers.load_temporal_edge_information(input_file,input_type=input_type,layer_mapping=layer_mapping)
    
    def monitor(self,message):
        """ A simple monithor method """
        
        print("-"*20,"\n",message,"\n","-"*20)

    def invert(self):

        """
        invert the nodes to edges. Get the "edge graph". Each node is here an edge.
        """
        
        ## default structure for a new graph
        G = nx.MultiGraph()
        new_edges = []        
        for node in self.core_network.nodes():
            ngs = [(neigh,node) for neigh in self.core_network[node] if neigh != node]
            new_edges += list(itertools.product(ngs,2))
        self.core_network_inverse = G.add_edges_from(new_edges)

    def save_network(self,output_file=None,output_type="edgelist"):
        """ A method for saving the network 
        :param output_type -- edgelist, multiedgelist or gpickle

        """
        
        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network,output_file=output_file)

        if output_type == "multiedgelist_encoded":
            self.node_map,self.layer_map = parsers.save_multiedgelist(self.core_network,output_file=output_file,encode_with_ints=True)

        if output_type == "multiedgelist":
            parsers.save_multiedgelist(self.core_network,output_file=output_file)
            
        if output_type == "gpickle":
            parsers.save_gpickle(self.core_network,output_file=output_file)

    def add_dummy_layers(self):

        """
        Internal function, for conversion between objects
        """
        
        if self.directed:
            self.core_network = nx.MultiDiGraph()
        else:
            self.core_network = nx.MultiGraph()
        
        for edge in self.tmp_core_network.edges():
            self.add_edges({"source":edge[0],
                            "target":edge[1],
                            "source_type":self.dummy_layer,
                            "target_type":self.dummy_layer})
                    
    def sparse_to_px(self,directed=None):

        """ convert to px format """
        
        if directed is None:
            directed = self.directed
            
        self.tmp_core_network = nx.from_scipy_sparse_matrix(self.core_network,directed)
        self.add_dummy_layers()
        self.sparse_enabled = False
            
    def basic_stats(self,target_network=None):

        """ A method for obtaining a network's statistics """
        
        if self.sparse_enabled:
            self.monitor("Only sparse matrix is loaded for efficiency! Converting to .px for this task!")
        else:
            
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
            

    def subnetwork(self,input_list=None,subset_by="node_layer_names"):

        """
        Construct a subgraph based on a set of nodes.
        """
        
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

        """
        Generic manipulator of edge dicts
        """

        if isinstance(edge_dict_list,dict):
            edge_dict = edge_dict_list
            if "source_type" in edge_dict_list.keys() and "target_type" in edge_dict_list.keys():
                edge_dict['u_for_edge'] = (edge_dict['source'],edge_dict['source_type'])
                edge_dict['v_for_edge'] = (edge_dict['target'],edge_dict['target_type'])
            else:
                edge_dict['u_for_edge'] = (edge_dict['source'],self.dummy_layer)
                edge_dict['v_for_edge'] = (edge_dict['target'],self.dummy_layer)
                
            del edge_dict['target'];del edge_dict['source']
            del edge_dict['target_type'];del edge_dict['source_type']
            eval("self.core_network."+target_function+"(**edge_dict)")
                
        else:
            for edge_dict in edge_dict_list:

                if "source_type" in edge_dict.keys() and "target_type" in edge_dict.keys():
                    edge_dict['u_for_edge'] = (edge_dict['source'],edge_dict['source_type'])
                    edge_dict['v_for_edge'] = (edge_dict['target'],edge_dict['target_type'])
                else:
                    edge_dict['u_for_edge'] = (edge_dict['source'],self.dummy_layer)
                    edge_dict['v_for_edge'] = (edge_dict['target'],self.dummy_layer)
                
                del edge_dict['target'];del edge_dict['source']
                del edge_dict['target_type'];del edge_dict['source_type']
                eval("self.core_network."+target_function+"(**edge_dict)")
        
    def _generic_edge_list_manipulator(self,edge_list,target_function,raw=False):

        """
        Generic manipulator of edge lists
        """

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

        """
        Generic manipulator of node dict
        """
        
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

        """
        Generic manipulator of node lists
        """
        
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

        def _unfreeze(self):
            if self.directed:
                self.core_network =  nx.MultiDiGraph(self.core_network)
            else:
                self.core_network = nx.MultiGraph(self.core_network)
        
    def add_edges(self,edge_dict_list,input_type="dict"):
        """ A method for adding edges.. Types are:
        dict,list or px_edge. See examples for further use.

        dict = {"source": n1,"target":n2,"type":sth}

        list = [[n1,t1,n2,t2] ...]

        px_edge = ((n1,t1)(n2,t2))
        """
        
        self._initiate_network()

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list,"add_edge")
            
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list,"add_edge")
            
        elif input_type == "px_edge":
            
            if edge_dict_list[2] is None:
                attr_dict = None
            else:
                attr_dict = edge_dict_list[2]
                
            self._unfreeze()
            self.core_network.add_edge(edge_dict_list[0],edge_dict_list[1],attr_dict=attr_dict)
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

        """
        Remove nodes from the network
        """
        
        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list,"remove_node")

        if input_type == "list":
            self._generic_node_list_manipulator(node_dict_list,"remove_node")
            
        if self.network_type == "multiplex":
            self.core_network = add_mpx_edges(self.core_network)

    def _get_num_layers(self):

        """
        Count layers
        """
        
        self.number_of_layers = len(set(x[1] for x in self.get_nodes()))

    def _get_num_nodes(self):

        """
        Count nodes
        """
        
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

        """
        Get sparse representation of the supra matrix.
        """
        
        if mtype == "sparse":
            return nx.to_scipy_sparse_matrix(self.core_network)
        else:
            return nx.to_numpy_matrix(self.core_network)

    def visualize_matrix(self,kwargs):

        """
        Plot the matrix
        """
        
        if server_mode:
            return 0
        adjmat = self.get_supra_adjacency_matrix(mtype="dense")
        supra_adjacency_matrix_plot(adjmat,**kwargs)

    
    def visualize_network(self,style="diagonal",parameters_layers=None,parameters_multiedges=None,show=False,compute_layouts="force",layouts_parameters=None,verbose=True,orientation="upper",resolution=0.01,other_parameters=None):
        if server_mode:
            return 0

        """ 
        network visualization.
        Either use diagonal or hairball style. Additional parameters are added with parameters_layers and parameters_edges etc.
        """
        
        if style == "diagonal":
            network_labels, graphs, multilinks = self.get_layers(style)
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
            network_colors, graph = self.get_layers(style="hairball")
            ax = hairball_plot(graph,network_colors,layout_algorithm="force",other_parameters=other_parameters)
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

    def _assign_types_for_hinmine(self):
        """
        Assing some basic types...
        """
        for node in self.get_nodes(data=True):
            node[1]['type'] = node[0][1]
    
    def get_decomposition_cycles(self,cycle=None):
        """ A supporting method for obtaining decomposition triplets  """
        self._assign_types_for_hinmine()
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

                dout = hinmine_decompose(self.hinmine_network, heuristic=x, cycle=cycle, parallel = parallel)
                decomposition = dout.decomposed['decomposition']
                
                ## use alpha and beta levels
                final_decomposition = alpha*decomposition + beta*induced_net

                print("Successfully decomposed: {}".format(x))
                
                yield (final_decomposition,dout.label_matrix, x)
                
            except Exception as es:
                print("No decomposition found for:", x)
                print(es)

    def load_embedding(self,embedding_file):
        """ Embedding loading method  """
        
        self.embedding = parsers.parse_embedding(embedding_file)
        return self

    def get_degrees(self):

        """
        A simple wrapper which computes node degrees.
        """
        
        return dict(nx.degree(self.core_network))
    
    def serialize_to_edgelist(self,edgelist_file = "./tmp/tmpedgelist.txt",tmp_folder="tmp",out_folder="out",multiplex=False):

        import os
        node_dict = {e:k for k,e in enumerate(list(self.get_nodes()))}
        outstruct = []
        
        ## enumerated n l n l
        if multiplex:
            separate_layers = []

            for node in self.get_nodes():
                separate_layers.append(node[1])

            layer_mappings = {e:k for k,e in enumerate(set(separate_layers))}
            node_mappings = {k[0]:v for k,v in node_dict.items()}

            ## add encoded edges
            for edge in self.get_edges():
                node_zero = node_mappings[edge[0][0]]
                node_first = node_mappings[edge[1][0]]
                layer_zero = layer_mappings[edge[0][1]]
                layer_first = layer_mappings[edge[1][1]]
                el = [node_zero,layer_zero,node_first,layer_first,1]
                outstruct.append(el)
        else:
            ## serialize as a simple edgelist
            for edge in self.get_edges(data=True):
                node_zero = node_dict[edge[0]]
                node_first = node_dict[edge[1]]
                if "weight" in edge[2]:
                    weight = edge[2]['weight']
                else:
                    weight = 1
                el = [node_zero,node_first,weight]
                outstruct.append(el)
        
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        file = open(edgelist_file,"w")

        for el in outstruct:
            file.write(" ".join([str(x) for x in el])+"\n") 
        file.close()

        inverse_nodes = {a:b for b,a in node_dict.items()}
#        inverse_layers = {a:b for b,a in layer_mappings.items()}

            
        return (inverse_nodes)
            
if __name__ == "__main__":

    multinet = multilayerNet("../../datasets/imdb_gml.gml")
    multinet.print_basic_stats()
