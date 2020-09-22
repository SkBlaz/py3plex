## This is the main data structure container

import networkx as nx
import itertools
from . import parsers
from . import converters
from .HINMINE.IO import *  ## parse the graph
from .HINMINE.decomposition import *  ## decompose the graph
from .supporting import *
import scipy.sparse as sp
import pandas as pd
import tqdm

try:
    from ..algorithms.statistics import topology
except:
    pass

## visualization modules
try:
    from ..visualization.multilayer import *
    from ..visualization.colors import all_color_names, colors_default
    server_mode = False
except:
    server_mode = True


class multi_layer_network:

    ## constructor
    def __init__(self,
                 verbose=True,
                 network_type="multilayer",
                 directed=True,
                 dummy_layer="null",
                 label_delimiter="---",
                 coupling_weight=1):
        """Class initializer
        
        This is the main class initializer method. User here specifies the type of the network, as well as other global parameters.

        """
        ## initialize the class
        self.coupling_weight = coupling_weight
        self.layer_name_map = {}
        self.layer_inverse_name_map = {}
        self.core_network = None
        self.directed = directed
        self.node_order_in_matrix = None
        self.dummy_layer = dummy_layer
        self.numeric_core_network = None
        self.labels = None
        self.embedding = None
        self.verbose = verbose
        self.network_type = network_type  ## assing network type
        self.sparse_enabled = False
        self.hinmine_network = None
        self.label_delimiter = label_delimiter

    def __getitem__(self, i, j=None):
        # for node in self.core_network.nodes():
        #     print(node)
        if j is None:
            return self.core_network[i]
        else:
            return self.core_network[i][j]
        pass

    def read_ground_truth_communities(self, cfile):
        """
        Parse ground truth community file and make mappings to the original nodes. This works based on node ID mappings, exact node,layer tuplets are to be added.
        Args:
            param1: ground truth communities.
        Returns:
            self.ground_truth_communities
        """

        community_assignments = {}
        with open(cfile) as cf:
            for line in cf:
                line = line.strip().split()
                community_assignments[line[0]] = line[1]

        self.ground_truth_communities = {}
        ## reorder the mampings appropriately
        for node in self.get_nodes():
            com = community_assignments[node[0]]
            self.ground_truth_communities[node] = com

    def load_network(self,
                     input_file=None,
                     directed=False,
                     input_type="gml",
                     label_delimiter="---"):
        """Main network loader

        This method loads and prepares a given network.

        Args:
            param1: network name
            param2: direction
            param3: input_type

        Returns:
             self.core_network along with self.labels(optional), self.activity etc.

        """

        self.input_file = input_file
        self.input_type = input_type
        self.directed = directed
        self.temporal_edges = None
        self.label_delimiter = label_delimiter
        if input_type == "sparse":
            self.sparse_enabled = True

        self.core_network, self.labels, self.activity = parsers.parse_network(
            self.input_file,
            self.input_type,
            directed=self.directed,
            label_delimiter=self.label_delimiter,
            network_type=self.network_type)

        if self.network_type == "multiplex":
            self.monitor("Checking multiplex edges..")
            self._couple_all_edges()

        return self

    def _couple_all_edges(self):

        unique_layers = {n[1] for n in self.core_network.nodes()}
        unique_nodes = {n[0] for n in self.core_network.nodes()}

        #        for potential_node in itertools.product(unique_nodes,unique_layers):
        #            self.core_network.add_node(potential_node)

        ## draw edges between same nodes accross layers
        for node in unique_nodes:
            for layer_first in unique_layers:
                for layer_second in unique_layers:
                    if layer_first != layer_second:
                        coupled_edge = ((node, layer_first), (node,
                                                              layer_second))
                        self.core_network.add_edge(coupled_edge[0],
                                                   coupled_edge[1],
                                                   type="coupling",
                                                   weight=self.coupling_weight)

    def load_layer_name_mapping(self, mapping_name, header=False):
        """Layer-node mapping loader method

        Args:
            param1: The name of the mapping file.

        Returns:
            self.layer_name_map is filled, returns nothing.

        """

        with open(mapping_name, "r+") as lf:
            if header:
                lf.readline()
            for line in lf:
                lid, lname = line.strip().split(" ")
                self.layer_name_map[lname] = lid
                self.layer_inverse_name_map[lid] = lname

    def load_network_activity(self, activity_file):
        """Network activity loader

        Args:
            param1: The name of the generic activity file -> 65432 61888 1377688175 RE
, n1 n2 timestamp and layer name. Note that layer node mappings MUST be loaded in order to map nodes to activity properly.

        Returns:
           self.activity is filled.

        """

        self.activity = parsers.load_edge_activity_raw(activity_file,
                                                       self.layer_name_map)
        self.activity = self.activity.sort_values(by=['timestamp'])

    def to_json(self):
        """A method for exporting the graph to a json file
        
        Args:
        self

        """

        from networkx.readwrite import json_graph
        data = json_graph.node_link_data(self.core_network)
        return data

    def to_sparse_matrix(self, replace_core=False, return_only=False):
        """
        Conver the matrix to scipy-sparse version. This is useful for classification.
        """
        if return_only:
            return nx.to_scipy_sparse_matrix(self.core_network)

        if replace_core:
            self.core_network = nx.to_scipy_sparse_matrix(self.core_network)
            self.core_sparse = None
        else:
            self.core_sparse = nx.to_scipy_sparse_matrix(self.core_network)

    def load_temporal_edge_information(self,
                                       input_file=None,
                                       input_type="edge_activity",
                                       directxed=False,
                                       layer_mapping=None):
        """ A method for loading temporal edge information """

        self.temporal_edges = parsers.load_temporal_edge_information(
            input_file, input_type=input_type, layer_mapping=layer_mapping)

    def monitor(self, message):
        """ A simple monithor method """

        print("-" * 20, "\n", message, "\n", "-" * 20)

    def get_neighbors(self, node_id, layer_id=None):
        return self.core_network.neighbors((node_id, layer_id))

    def invert(self, override_core=False):
        """
        invert the nodes to edges. Get the "edge graph". Each node is here an edge.
        """

        ## default structure for a new graph
        G = nx.MultiGraph()
        new_edges = []
        for node in self.core_network.nodes():
            ngs = [(neigh, node) for neigh in self.core_network[node]
                   if neigh != node]
            if len(ngs) > 0:
                pairs = itertools.combinations(ngs, 2)
                new_edges += list(pairs)

        for edge in new_edges:
            G.add_edge(edge[0], edge[1])

        if override_core:
            self.core_network = G
        else:
            self.core_network_inverse = G  #.add_edges_from(new_edges)

    def save_network(self, output_file=None, output_type="edgelist"):
        """ A method for saving the network 
        :param output_type -- edgelist, multiedgelist or gpickle

        """

        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network, output_file=output_file)

        if output_type == "multiedgelist_encoded":
            self.node_map, self.layer_map = parsers.save_multiedgelist(
                self.core_network,
                output_file=output_file,
                encode_with_ints=True)

        if output_type == "multiedgelist":
            parsers.save_multiedgelist(self.core_network,
                                       output_file=output_file)

        if output_type == "gpickle":
            parsers.save_gpickle(self.core_network, output_file=output_file)

    def add_dummy_layers(self):
        """
        Internal function, for conversion between objects
        """

        self.tmp_core_network = self.core_network

        if self.directed:
            self.core_network = nx.MultiDiGraph()
        else:
            self.core_network = nx.MultiGraph()

        for edge in self.tmp_core_network.edges():
            self.add_edges({
                "source": edge[0],
                "target": edge[1],
                "source_type": self.dummy_layer,
                "target_type": self.dummy_layer
            })
        del self.tmp_core_network
        return self

    def sparse_to_px(self, directed=None):
        """ convert to px format """

        if directed is None:
            directed = self.directed

        self.core_network = nx.from_scipy_sparse_matrix(
            self.core_network, directed)
        self.add_dummy_layers()
        self.sparse_enabled = False

    def summary(self):
        """
        Generate a short summary of the network in form of a dict.
        """

        unique_layers = len({n[1] for n in self.core_network.nodes()})
        nodes = len(self.core_network.nodes())
        edges = len(self.core_network.edges())
        components = len(
            list(nx.connected_components(self.core_network.to_undirected())))
        node_degree_vector = list(dict(nx.degree(self.core_network)).values())
        mean_degree = np.mean(node_degree_vector)
        return {
            "Number of layers": unique_layers,
            "Nodes": nodes,
            "Edges": edges,
            "Mean degree": mean_degree,
            "CC": components
        }

    def get_unique_entity_counts(self):
        """
        :input: self object
        """

        node_layer_tuples = set()
        unique_nodes = set()

        for edge in self.get_edges():
            node_layer_tuples.add(edge)
            unique_nodes.add(edge[0])

        return len(node_layer_tuples), len(unique_nodes)

    def basic_stats(self, target_network=None):
        """ A method for obtaining a network's statistics """

        if self.sparse_enabled:
            self.monitor(
                "Only sparse matrix is loaded for efficiency! Converting to .px for this task!"
            )
        else:

            if self.verbose:
                self.monitor("Computing core stats of the network")

            if target_network is None:
                print(nx.info(self.core_network))
                nt, n = self.get_unique_entity_counts()
                print("Number of unique node IDs: {}".format(n))

            else:
                print(nx.info(target_network))
                nt, n = self.get_unique_entity_counts()
                print("Number of unique node IDs: {}".format(n))

    def get_edges(self, data=False, multiplex_edges=False):
        """ A method for obtaining a network's edges """
        if self.network_type == "multilayer":
            for edge in self.core_network.edges(data=data):
                yield edge

        elif self.network_type == "multiplex":
            if not multiplex_edges:
                for edge in self.core_network.edges(data=data, keys=True):
                    if edge[2] == "coupling":
                        continue
                    yield edge
            else:
                for edge in self.core_network.edges(data=data):
                    yield edge
        else:
            raise Exception("Specify network type!  e.g., multilayer_network")

    def get_nodes(self, data=False):
        """ A method for obtaining a network's nodes """

        for node in self.core_network.nodes(data=data):
            yield node

    def merge_with(self, target_px_object):
        '''
        Merge two px objects.
        '''

        all_edges = []
        for edge in target_px_object.get_edges(data=True):
            n1_name = edge[0][0]
            n1_type = edge[0][1]
            n2_name = edge[1][0]
            n2_type = edge[1][1]
            edge_type = edge[2].get('type')
            weight = edge[2].get('weight')
            edge_obj = {
                "source": n1_name,
                "target": n2_name,
                "type": edge_type,
                "source_type": n1_type,
                "target_type": n2_type
            }
            all_edges.append(edge_obj)

        self.add_edges(all_edges)
        return self

    def subnetwork(self, input_list=None, subset_by="node_layer_names"):
        """
        Construct a subgraph based on a set of nodes.
        """

        input_list = set(input_list)
        if subset_by == "layers":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n[1] in input_list])

        elif subset_by == "node_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n[0] in input_list])

        elif subset_by == "node_layer_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n in input_list])

        else:
            self.monitor("Please, select layers of node_names options..")

        tmp_net = multi_layer_network()
        tmp_net.core_network = subnetwork
        return tmp_net

    def aggregate_edges(self, metric="count", normalize_by="degree"):

        layer_object = defaultdict(list)
        edge_object = {}

        for node in self.get_nodes():
            layer_object[node[1]].append(node)

        for layer, nodes in layer_object.items():
            layer_network = self.subnetwork(nodes)

            if normalize_by != "raw":
                connectivity = np.mean([
                    x[1] for x in eval("nx." + normalize_by +
                                       "(layer_network.core_network)")
                ])

            else:
                connectivity = 1

            for edge in layer_network.get_edges():
                edge_new = (edge[0][0], edge[1][0])  ## keep just the nids.
                if not edge_new in edge_object:

                    edge_object[edge_new] = 1 / connectivity

                else:
                    edge_object[edge_new] += 1 / connectivity

        if self.directed:
            outgraph = nx.DiGraph()

        else:
            outgraph = nx.Graph()

        for k, v in edge_object.items():
            outgraph.add_edge(k[0], k[1], weight=v)
        return outgraph

    def remove_layer_edges(self):

        if self.separate_layers is not None:
            self.tmp_layers = []
            for graph in self.separate_layers:
                empty_graph = graph.copy()
                empty_graph.remove_edges_from(graph.edges())
                assert len(empty_graph.edges()) == 0
                self.tmp_layers.append(empty_graph)
        else:
            self.monitor(
                "Please,first call your_object.split_to_layers() method!")

        self.monitor("Finished edge cleaning..")

    def edges_from_temporal_table(self, edge_df):

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        layer_edges = defaultdict(list)
        edges = []
        for enx, en in enumerate(node_first_names):
            edge = (str(node_first_names[enx]), str(node_second_names[enx]),
                    str(layer_names[enx]), str(layer_names[enx]), 1)
            edges.append(edge)
        return edges

    def fill_tmp_with_edges(self, edge_df):

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        layer_edges = defaultdict(list)
        for enx, en in enumerate(node_first_names):
            edge = ((str(node_first_names[enx]), str(layer_names[enx])),
                    (str(node_second_names[enx]), str(layer_names[enx])))
            layer_edges[layer_names[enx]].append(edge)

        ## fill layer by layer
        for enx, layer in enumerate(self.layer_names):
            layer_ed = layer_edges[layer]
            self.tmp_layers[enx].add_edges_from(layer_ed)

    def split_to_layers(self,
                        style="diagonal",
                        compute_layouts="force",
                        layout_parameters=None,
                        verbose=True,
                        multiplex=False,
                        convert_to_simple=False):
        """ A method for obtaining layerwise distributions """

        if self.verbose:
            self.monitor("Network splitting in progress")

        ## multilayer visualization
        if style == "diagonal":
            self.layer_names, self.separate_layers, self.multiedges = converters.prepare_for_visualization(
                self.core_network,
                compute_layouts=compute_layouts,
                layout_parameters=layout_parameters,
                verbose=verbose,
                multiplex=multiplex)
            self.real_layer_names = [
                self.layer_inverse_name_map[lid] for lid in self.layer_names
            ]

        ## hairball visualization
        if style == "hairball":
            self.layer_names, self.separate_layers, self.multiedges = converters.prepare_for_visualization_hairball(
                self.core_network, compute_layouts=True)

        if style == "none":

            self.layer_names, self.separate_layers, self.multiedges = converters.prepare_for_parsing(
                self.core_network)

            if convert_to_simple:
                if self.directed:
                    self.separate_layers = [
                        nx.DiGraph(x) for x in self.separate_layers
                    ]
                else:
                    self.separate_layers = [
                        nx.Graph(x) for x in self.separate_layers
                    ]

    def get_layers(self,
                   style="diagonal",
                   compute_layouts="force",
                   layout_parameters=None,
                   verbose=True):
        """ A method for obtaining layerwise distributions """

        if self.verbose:
            self.monitor("Network splitting in progress")

        ## multilayer visualization
        if style == "diagonal":
            return converters.prepare_for_visualization(
                self.core_network,
                compute_layouts=compute_layouts,
                layout_parameters=layout_parameters,
                verbose=verbose)

        ## hairball visualization
        if style == "hairball":
            return converters.prepare_for_visualization_hairball(
                self.core_network, compute_layouts=True)

    def _initiate_network(self):
        if self.core_network is None:
            if self.directed:
                self.core_network = nx.MultiDiGraph()
            else:
                self.core_network = nx.MultiGraph()

    def monoplex_nx_wrapper(self, method, kwargs=None):
        ''' a generic networkx function wrapper '''

        result = eval("nx." + method + "(self.core_network)")
        return result

    def _generic_edge_dict_manipulator(self, edge_dict_list, target_function):
        """
        Generic manipulator of edge dicts
        """

        if isinstance(edge_dict_list, dict):
            edge_dict = edge_dict_list
            if "source_type" in edge_dict_list.keys(
            ) and "target_type" in edge_dict_list.keys():
                edge_dict['u_for_edge'] = (edge_dict['source'],
                                           edge_dict['source_type'])
                edge_dict['v_for_edge'] = (edge_dict['target'],
                                           edge_dict['target_type'])
            else:
                edge_dict['u_for_edge'] = (edge_dict['source'],
                                           self.dummy_layer)
                edge_dict['v_for_edge'] = (edge_dict['target'],
                                           self.dummy_layer)

            del edge_dict['target']
            del edge_dict['source']
            del edge_dict['target_type']
            del edge_dict['source_type']
            eval("self.core_network." + target_function + "(**edge_dict)")

        else:
            for edge_dict in edge_dict_list:

                if "source_type" in edge_dict.keys(
                ) and "target_type" in edge_dict.keys():
                    edge_dict['u_for_edge'] = (edge_dict['source'],
                                               edge_dict['source_type'])
                    edge_dict['v_for_edge'] = (edge_dict['target'],
                                               edge_dict['target_type'])
                else:
                    edge_dict['u_for_edge'] = (edge_dict['source'],
                                               self.dummy_layer)
                    edge_dict['v_for_edge'] = (edge_dict['target'],
                                               self.dummy_layer)

                del edge_dict['target']
                del edge_dict['source']
                del edge_dict['target_type']
                del edge_dict['source_type']
                eval("self.core_network." + target_function + "(**edge_dict)")

    def _generic_edge_list_manipulator(self,
                                       edge_list,
                                       target_function,
                                       raw=False):
        """
        Generic manipulator of edge lists
        """

        if isinstance(edge_list[0], list):
            for edge in edge_list:
                n1, l1, n2, l2, w = edge
                if raw:
                    eval("self.core_network." + target_function +
                         "((n1,l1),(n2,l2))")
                else:
                    eval("self.core_network." + target_function +
                         "((n1,l1),(n2,l2),weight=" + str(w) +
                         ",type=\"default\")")

        else:
            n1, l1, n2, l2, w = edge_list
            if raw:
                eval("self.core_network." + target_function +
                     "((n1,l1),(n2,l2))")
            else:
                eval("self.core_network." + target_function +
                     "((n1,l1),(n2,l2),weight=" + str(w) +
                     ",type=\"default\"))")

    def _generic_node_dict_manipulator(self, node_dict_list, target_function):
        """
        Generic manipulator of node dict
        """

        if isinstance(node_dict_list, dict):
            node_dict = node_dict_list
            node_dict["node_for_adding"] = node_dict["source"]

            if "type" in node_dict.keys():
                node_dict["node_for_adding"] = (node_dict["source"],
                                                node_dict['type'])
            else:
                node_dict["node_for_adding"] = (node_dict["source"],
                                                self.dummy_layer)
            del node_dict["source"]
            eval("self.core_network." + target_function + "(**node_dict)")

        else:
            for node_dict in node_dict_list:
                if "type" in node_dict.keys():
                    node_dict["node_for_adding"] = (node_dict["source"],
                                                    node_dict['type'])
                else:
                    node_dict["node_for_adding"] = (node_dict["source"],
                                                    self.dummy_layer)
                del node_dict["source"]
                eval("self.core_network." + target_function + "(**node_dict)")

    def _generic_node_list_manipulator(self, node_list, target_function):
        """
        Generic manipulator of node lists
        """

        if isinstance(node_list, list):
            for node in node_list:
                n1, l1 = node
                eval("self.core_network." + target_function + "((n1,l1))")

        else:
            n1, l1 = node_list
            eval("self.core_network." + target_function + "((n1,l1))")

    def _unfreeze(self):
        if self.directed:
            self.core_network = nx.MultiDiGraph(self.core_network)
        else:
            self.core_network = nx.MultiGraph(self.core_network)

    def add_edges(self, edge_dict_list, input_type="dict"):
        """ A method for adding edges.. Types are:
        dict,list or px_edge. See examples for further use.

        dict = {"source": n1,"target":n2,"type":sth}

        list = [[n1,t1,n2,t2] ...]

        px_edge = ((n1,t1)(n2,t2))
        """

        self._initiate_network()

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list, "add_edge")

        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list, "add_edge")

        elif input_type == "px_edge":

            if edge_dict_list[2] is None:
                attr_dict = None
            else:
                attr_dict = edge_dict_list[2]

            self._unfreeze()
            self.core_network.add_edge(edge_dict_list[0],
                                       edge_dict_list[1],
                                       attr_dict=attr_dict)
        else:
            raise Exception("Please, use dict or list input.")

    def remove_edges(self, edge_dict_list, input_type="list"):
        """ A method for removing edges.. """

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list,
                                                "remove_edge",
                                                raw=True)
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list,
                                                "remove_edge",
                                                raw=True)
        else:
            raise Exception("Please, use dict or list input.")

    def add_nodes(self, node_dict_list, input_type="dict"):
        """ A method for adding nodes.. """

        self._initiate_network()

        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list, "add_node")

    def remove_nodes(self, node_dict_list, input_type="dict"):
        """
        Remove nodes from the network
        """

        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list, "remove_node")

        if input_type == "list":
            self._generic_node_list_manipulator(node_dict_list, "remove_node")

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

    def get_tensor(self, sparsity_type="bsr"):
        """
        TODO
        """

        pass

    def _encode_to_numeric(self):

        if self.network_type != "multiplex":
            new_edges = []
            nmap = {}
            n_count = 0
            n1 = []
            n2 = []
            w = []

            if self.directed:
                simple_graph = nx.DiGraph()
            else:
                simple_graph = nx.Graph()

            for edge in self.core_network.edges(data=True):
                node_first = edge[0]
                node_second = edge[1]
                if node_first not in nmap:
                    nmap[node_first] = n_count
                    n_count += 1
                if node_second not in nmap:
                    nmap[node_second] = n_count
                    n_count += 1
                try:
                    weight = float(edge[2]['weight'])
                except:
                    weight = 1

                simple_graph.add_edge(nmap[node_first],
                                      nmap[node_second],
                                      weight=weight)
            vectors = nx.to_scipy_sparse_matrix(simple_graph)
            self.numeric_core_network = vectors
            self.node_order_in_matrix = simple_graph.nodes()

        else:
            unique_layers = set(n[1] for n in self.core_network.nodes())
            individual_adj = []
            all_nodes = []
            for layer in unique_layers:
                layer_nodes = [
                    n for n in self.core_network.nodes() if n[1] == layer
                ]
                H = self.core_network.subgraph(layer_nodes)
                adj = nx.to_numpy_matrix(H)
                all_nodes += list(H.nodes())
                individual_adj.append(adj)

            whole_mat = []
            for en, adj_mat in enumerate(individual_adj):
                cross = np.identity(adj_mat.shape[0])
                one_row = []
                for j in range(len(individual_adj)):
                    if j < en or j > en:
                        one_row.append(cross)
                    if j == en:
                        one_row.append(adj_mat)

                whole_mat.append(np.hstack([x for x in one_row]))
                vectors = np.vstack([x for x in whole_mat])
            self.numeric_core_network = vectors
            self.node_order_in_matrix = all_nodes

    def get_supra_adjacency_matrix(self, mtype="sparse"):
        """
        Get sparse representation of the supra matrix.
        """

        if self.numeric_core_network is None:
            self._encode_to_numeric()


#        print(self.numeric_core_network)
        if mtype == "sparse":
            return self.numeric_core_network
        else:
            try:
                return self.numeric_core_network.todense()
            except:
                return self.numeric_core_network

    def visualize_matrix(self, kwargs={}):
        """
        Plot the matrix -- this plots the supra-adjacency matrix
        """

        if server_mode:
            return 0

        adjmat = self.get_supra_adjacency_matrix(mtype="dense")
        supra_adjacency_matrix_plot(adjmat, **kwargs)

    def visualize_network(self,
                          style="diagonal",
                          parameters_layers=None,
                          parameters_multiedges=None,
                          show=False,
                          compute_layouts="force",
                          layouts_parameters=None,
                          verbose=True,
                          orientation="upper",
                          resolution=0.01,
                          axis=None,
                          fig=None,
                          no_labels=False,
                          linewidth=1.7,
                          alphachannel=0.3,
                          linepoints="-.",
                          legend=False):
        if server_mode:
            return 0
        """ 
        network visualization.
        Either use diagonal or hairball style. Additional parameters are added with parameters_layers and parameters_edges etc.

        """

        if style == "diagonal":
            network_labels, graphs, multilinks = self.get_layers(style)
            if no_labels:
                network_labels = None
            if parameters_layers is None:
                if axis:
                    axis = draw_multilayer_default(graphs,
                                                   display=False,
                                                   background_shape="circle",
                                                   labels=network_labels,
                                                   node_size=3,
                                                   verbose=verbose)
                else:
                    ax = draw_multilayer_default(graphs,
                                                 display=False,
                                                 background_shape="circle",
                                                 labels=network_labels,
                                                 node_size=3,
                                                 verbose=verbose)
            else:
                if axis:
                    axis = draw_multilayer_default(graphs, **parameters_layers)
                else:
                    ax = draw_multilayer_default(graphs, **parameters_layers)

            if parameters_multiedges is None:
                enum = 1
                for edge_type, edges in tqdm.tqdm(multilinks.items()):
                    if edge_type == "coupling":
                        if axis:
                            axis = draw_multiedges(graphs,
                                                   edges,
                                                   alphachannel=alphachannel,
                                                   linepoints=linepoints,
                                                   linecolor="red",
                                                   curve_height=2,
                                                   linmod="bottom",
                                                   linewidth=linewidth,
                                                   resolution=resolution)
                        else:
                            ax = draw_multiedges(graphs,
                                                 edges,
                                                 alphachannel=alphachannel,
                                                 linepoints=linepoints,
                                                 linecolor="red",
                                                 curve_height=2,
                                                 linmod="bottom",
                                                 linewidth=linewidth,
                                                 resolution=resolution)
                    else:
                        if axis:
                            axis = draw_multiedges(graphs,
                                                   edges,
                                                   alphachannel=alphachannel,
                                                   linepoints="--",
                                                   linecolor="black",
                                                   curve_height=2,
                                                   linmod=orientation,
                                                   linewidth=linewidth,
                                                   resolution=resolution)
                        else:
                            ax = draw_multiedges(graphs,
                                                 edges,
                                                 alphachannel=alphachannel,
                                                 linepoints="--",
                                                 linecolor="black",
                                                 curve_height=2,
                                                 linmod=orientation,
                                                 linewidth=linewidth,
                                                 resolution=resolution)
                    enum += 1
            else:
                enum = 1
                for edge_type, edges in multilinks.items():
                    if axis:
                        axis = draw_multiedges(graphs, edges,
                                               **parameters_multiedges)
                    else:
                        ax = draw_multiedges(graphs, edges,
                                             **parameters_multiedges)
                    enum += 1
            if show:
                plt.show()

            if axis:
                return axis
            else:
                return ax

        elif style == "hairball":
            network_colors, graph = self.get_layers(style="hairball")
            if axis:
                axis = hairball_plot(graph,
                                     network_colors,
                                     layout_algorithm="force",
                                     legend=legend)
            else:
                ax = hairball_plot(graph,
                                   network_colors,
                                   layout_algorithm="force",
                                   legend=legend)
            if show:
                plt.show()
            if axis:
                return axis
            else:
                return ax
        else:
            raise Exception(
                "Please, specify visualization style using: .style. keyword")

    def get_nx_object(self):
        """ Return only core network with proper annotations """
        return self.core_network

    def test_scale_free(self):
        """
        Test the scale-free-nness of the network
        """

        val_vect = sorted(dict(nx.degree(self.core_network)).values(),
                          reverse=True)
        alpha, sigma = topology.basic_pl_stats(val_vect)
        return (alpha, sigma)

    def get_label_matrix(self):
        """ Return network labels  """
        return self.labels

    def _assign_types_for_hinmine(self):
        """
        Assing some basic types...
        """
        for node in self.get_nodes(data=True):
            node[1]['type'] = node[0][1]

    def get_decomposition_cycles(self, cycle=None):
        """ A supporting method for obtaining decomposition triplets  """
        self._assign_types_for_hinmine()
        if self.hinmine_network is None:
            self.hinmine_network = load_hinmine_object(self.core_network,
                                                       self.label_delimiter)
        return hinmine_get_cycles(self.hinmine_network)

    def get_decomposition(self,
                          heuristic="all",
                          cycle=None,
                          parallel=False,
                          alpha=1,
                          beta=1):
        """ Core method for obtaining a network's decomposition in terms of relations  """

        if heuristic == "all":
            heuristic = [
                "idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"
            ]  ## all available
        if self.hinmine_network is None:
            if self.verbose:
                print("Loading into a hinmine object..")
            self.hinmine_network = load_hinmine_object(self.core_network,
                                                       self.label_delimiter)

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

                dout = hinmine_decompose(self.hinmine_network,
                                         heuristic=x,
                                         cycle=cycle,
                                         parallel=parallel)
                decomposition = dout.decomposed['decomposition']

                ## use alpha and beta levels
                final_decomposition = alpha * decomposition + beta * induced_net

                print("Successfully decomposed: {}".format(x))

                yield (final_decomposition, dout.label_matrix, x)

            except Exception as es:
                print("No decomposition found for:", x)
                print(es)

    def load_embedding(self, embedding_file):
        """ Embedding loading method  """

        self.embedding = parsers.parse_embedding(embedding_file)
        return self

    def get_degrees(self):
        """
        A simple wrapper which computes node degrees.
        """

        return dict(nx.degree(self.core_network))

    def serialize_to_edgelist(self,
                              edgelist_file="./tmp/tmpedgelist.txt",
                              tmp_folder="tmp",
                              out_folder="out",
                              multiplex=False):

        import os
        node_dict = {e: k for k, e in enumerate(list(self.get_nodes()))}
        outstruct = []

        ## enumerated n l n l
        if multiplex:
            separate_layers = []

            for node in self.get_nodes():
                separate_layers.append(node[1])

            layer_mappings = {e: k for k, e in enumerate(set(separate_layers))}
            node_mappings = {k[0]: v for k, v in node_dict.items()}

            ## add encoded edges
            for edge in self.get_edges():
                node_zero = node_mappings[edge[0][0]]
                node_first = node_mappings[edge[1][0]]
                layer_zero = layer_mappings[edge[0][1]]
                layer_first = layer_mappings[edge[1][1]]
                el = [node_zero, layer_zero, node_first, layer_first, 1]
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
                el = [node_zero, node_first, weight]
                outstruct.append(el)

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        file = open(edgelist_file, "w")

        for el in outstruct:
            file.write(" ".join([str(x) for x in el]) + "\n")
        file.close()

        inverse_nodes = {a: b for b, a in node_dict.items()}
        #        inverse_layers = {a:b for b,a in layer_mappings.items()}

        return (inverse_nodes)

if __name__ == "__main__":

    multinet = multilayerNet("../../datasets/imdb_gml.gml")
    multinet.print_basic_stats()
