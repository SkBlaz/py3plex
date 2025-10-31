# This is the main data structure container

import itertools
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np

# Optional formal verification support
try:
    from icontract import ensure, invariant, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def invariant(*args, **kwargs):
        def decorator(cls):
            return cls

        return decorator

    ICONTRACT_AVAILABLE = False

from py3plex.logging_config import get_logger

from . import converters, parsers
from .HINMINE.decomposition import hinmine_decompose  # decompose the graph
from .HINMINE.decomposition import hinmine_get_cycles
from .HINMINE.IO import load_hinmine_object  # parse the graph
from .nx_compat import nx_from_scipy_sparse_matrix, nx_info, nx_to_scipy_sparse_matrix

logger = get_logger(__name__)
try:
    import tqdm
except ImportError:
    # Create a simple mock for tqdm when it's not available
    class MockTqdm:
        @staticmethod
        def tqdm(iterable, *args, **kwargs):
            return iterable

    tqdm = MockTqdm()

try:
    from py3plex.algorithms.statistics import topology
except ImportError:
    pass

# visualization modules
try:
    from py3plex.visualization.multilayer import (
        draw_multiedges,
        draw_multilayer_default,
        hairball_plot,
        supra_adjacency_matrix_plot,
    )

    server_mode = False
except ImportError:
    server_mode = True


class multi_layer_network:

    # constructor
    def __init__(
        self,
        verbose: bool = True,
        network_type: str = "multilayer",
        directed: bool = True,
        dummy_layer: str = "null",
        label_delimiter: str = "---",
        coupling_weight: Union[int, float] = 1,
    ) -> None:
        """Class initializer

        This is the main class initializer method. User here specifies the type of the network, as well as other global parameters.

        Args:
            verbose: Enable verbose logging output
            network_type: Type of network ('multilayer', 'multiplex', etc.)
            directed: Whether the network is directed
            dummy_layer: Name for dummy/placeholder layer
            label_delimiter: Delimiter used to separate layer names in node labels
            coupling_weight: Default weight for inter-layer edges

        """
        # initialize the class
        self.coupling_weight: Union[int, float] = coupling_weight
        self.layer_name_map: Dict[str, int] = {}
        self.layer_inverse_name_map: Dict[int, str] = {}
        self.core_network: Optional[Union[nx.MultiGraph, nx.MultiDiGraph]] = None
        self.directed: bool = directed
        self.node_order_in_matrix: Optional[List[Any]] = None
        self.dummy_layer: str = dummy_layer
        self.numeric_core_network: Optional[Any] = None
        self.labels: Optional[Any] = None
        self.embedding: Optional[Any] = None
        self.verbose: bool = verbose
        self.network_type: str = network_type  # assing network type
        self.sparse_enabled: bool = False
        self.hinmine_network: Optional[Any] = None
        self.label_delimiter: str = label_delimiter

    def __getitem__(self, i, j=None):
        # for node in self.core_network.nodes():
        #     print(node)
        if j is None:
            return self.core_network[i]
        else:
            return self.core_network[i][j]

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
        # reorder the mampings appropriately
        for node in self.get_nodes():
            com = community_assignments[node[0]]
            self.ground_truth_communities[node] = com

    def load_network(
        self,
        input_file: Optional[str] = None,
        directed: bool = False,
        input_type: str = "gml",
        label_delimiter: str = "---",
    ) -> "multi_layer_network":
        """Main network loader

        This method loads and prepares a given network.

        Args:
            input_file: Path to the network file to load
            directed: Whether the network is directed
            input_type: Format of the input file ('gml', 'graphml', 'edgelist', 'gpickle', etc.)
            label_delimiter: Delimiter used to separate layer names in node labels

        Returns:
             Self for method chaining. Populates self.core_network, self.labels, and self.activity

        """
        # crosshair: analysis_kind=asserts
        # Precondition: input_type must be from supported set
        SUPPORTED = {"edgelist", "multiedgelist", "multiplex_edges", "gml", "gpickle", "graphml", "nx", "sparse"}
        assert input_type in SUPPORTED, f"input_type must be one of {SUPPORTED}, got {input_type}"
        
        # Precondition: if not nx type, input_file should be provided
        if input_type != "nx":
            assert input_file is not None, "input_file must be provided for non-nx input types"

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
            network_type=self.network_type,
        )

        if self.network_type == "multiplex":
            self.monitor("Checking multiplex edges..")
            self._couple_all_edges()

        # Postconditions: core_network should be valid
        assert self.core_network is not None, "core_network must be initialized"
        assert self.core_network.number_of_nodes() >= 0, "node count must be non-negative"
        assert self.core_network.number_of_edges() >= 0, "edge count must be non-negative"
        
        # Postcondition: if directed=False, graph should be undirected
        if not directed and self.core_network is not None:
            assert not isinstance(self.core_network, (nx.DiGraph, nx.MultiDiGraph)), \
                "core_network should not be directed when directed=False"

        return self

    def _couple_all_edges(self):

        unique_layers = {n[1] for n in self.core_network.nodes()}
        unique_nodes = {n[0] for n in self.core_network.nodes()}

        #        for potential_node in itertools.product(unique_nodes,unique_layers):
        #            self.core_network.add_node(potential_node)

        # draw edges between same nodes accross layers
        for node in unique_nodes:
            for layer_first in unique_layers:
                for layer_second in unique_layers:
                    if layer_first != layer_second:
                        coupled_edge = ((node, layer_first), (node, layer_second))
                        self.core_network.add_edge(
                            coupled_edge[0],
                            coupled_edge[1],
                            type="coupling",
                            weight=self.coupling_weight,
                        )

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

        self.activity = parsers.load_edge_activity_raw(
            activity_file, self.layer_name_map
        )
        self.activity = self.activity.sort_values(by=["timestamp"])

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
            return nx_to_scipy_sparse_matrix(self.core_network)

        if replace_core:
            self.core_network = nx_to_scipy_sparse_matrix(self.core_network)
            self.core_sparse = None
        else:
            self.core_sparse = nx_to_scipy_sparse_matrix(self.core_network)

    def load_temporal_edge_information(
        self,
        input_file=None,
        input_type="edge_activity",
        directxed=False,
        layer_mapping=None,
    ):
        """A method for loading temporal edge information"""

        self.temporal_edges = parsers.load_temporal_edge_information(
            input_file, input_type=input_type, layer_mapping=layer_mapping
        )

    def monitor(self, message):
        """A simple monithor method"""

        logger.info("-" * 20)
        logger.info(message)
        logger.info("-" * 20)

    def get_neighbors(self, node_id, layer_id=None):
        return self.core_network.neighbors((node_id, layer_id))

    def invert(self, override_core=False):
        """
        invert the nodes to edges. Get the "edge graph". Each node is here an edge.
        """

        # default structure for a new graph
        G = nx.MultiGraph()
        new_edges = []
        for node in self.core_network.nodes():
            ngs = [(neigh, node) for neigh in self.core_network[node] if neigh != node]
            if len(ngs) > 0:
                pairs = itertools.combinations(ngs, 2)
                new_edges += list(pairs)

        for edge in new_edges:
            G.add_edge(edge[0], edge[1])

        if override_core:
            self.core_network = G
        else:
            self.core_network_inverse = G  # .add_edges_from(new_edges)

    def save_network(self, output_file=None, output_type="edgelist"):
        """A method for saving the network

        This method loads and prepares a given network.

        Args:
            param1: output file path
            param2: output file type

        """
        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network, output_file=output_file)

        if output_type == "multiedgelist_encoded":
            self.node_map, self.layer_map = parsers.save_multiedgelist(
                self.core_network, output_file=output_file, encode_with_ints=True
            )

        if output_type == "multiedgelist":
            parsers.save_multiedgelist(self.core_network, output_file=output_file)

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
            self.add_edges(
                {
                    "source": edge[0],
                    "target": edge[1],
                    "source_type": self.dummy_layer,
                    "target_type": self.dummy_layer,
                }
            )
        del self.tmp_core_network
        return self

    def sparse_to_px(self, directed=None):
        """convert to px format"""

        if directed is None:
            directed = self.directed

        self.core_network = nx_from_scipy_sparse_matrix(
            self.core_network, create_using=(nx.DiGraph() if directed else nx.Graph())
        )
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
            list(nx.connected_components(self.core_network.to_undirected()))
        )
        node_degree_vector = list(dict(nx.degree(self.core_network)).values())
        mean_degree = np.mean(node_degree_vector)
        return {
            "Number of layers": unique_layers,
            "Nodes": nodes,
            "Edges": edges,
            "Mean degree": mean_degree,
            "CC": components,
        }

    def get_unique_entity_counts(self):
        """Count unique entities in the network.

        Returns:
            tuple: (total_unique_nodes, unique_node_ids, nodes_per_layer)
                - total_unique_nodes: count of unique (node, layer) tuples
                - unique_node_ids: count of unique node IDs (across all layers)
                - nodes_per_layer: dict mapping layer to count of nodes in that layer
        """

        unique_node_layer_tuples = set()
        unique_node_ids = set()
        nodes_per_layer = {}

        # Iterate through all nodes (which are (node_id, layer) tuples in multilayer networks)
        for node in self.get_nodes():
            # Add the entire (node_id, layer) tuple as unique
            unique_node_layer_tuples.add(node)

            # Extract node_id and layer if node is a tuple
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer = node[0], node[1]
                unique_node_ids.add(node_id)

                # Count nodes per layer
                if layer not in nodes_per_layer:
                    nodes_per_layer[layer] = set()
                nodes_per_layer[layer].add(node)
            else:
                # For simple networks without layers, just count the node
                unique_node_ids.add(node)

        # Convert per-layer node sets to counts
        nodes_per_layer_counts = {
            layer: len(nodes) for layer, nodes in nodes_per_layer.items()
        }

        return (
            len(unique_node_layer_tuples),
            len(unique_node_ids),
            nodes_per_layer_counts,
        )

    def basic_stats(self, target_network=None):
        """A method for obtaining a network's statistics.

        Displays:
        - Basic network info (nodes, edges)
        - Total unique nodes (counting each (node, layer) as unique)
        - Unique node IDs (across all layers)
        - Per-layer node counts
        """

        if self.sparse_enabled:
            self.monitor(
                "Only sparse matrix is loaded for efficiency! Converting to .px for this task!"
            )
        else:

            if self.verbose:
                self.monitor("Computing core stats of the network")

            if target_network is None:
                logger.info(nx_info(self.core_network))
                total_nodes, unique_ids, nodes_per_layer = (
                    self.get_unique_entity_counts()
                )
                logger.info(
                    f"Number of unique nodes (as node-layer tuples): {total_nodes}"
                )
                logger.info(
                    f"Number of unique node IDs (across all layers): {unique_ids}"
                )

                if nodes_per_layer:
                    logger.info("Nodes per layer:")
                    for layer, count in sorted(nodes_per_layer.items()):
                        logger.info(f"  Layer '{layer}': {count} nodes")

            else:
                logger.info(nx_info(target_network))
                total_nodes, unique_ids, nodes_per_layer = (
                    self.get_unique_entity_counts()
                )
                logger.info(
                    f"Number of unique nodes (as node-layer tuples): {total_nodes}"
                )
                logger.info(
                    f"Number of unique node IDs (across all layers): {unique_ids}"
                )

                if nodes_per_layer:
                    logger.info("Nodes per layer:")
                    for layer, count in sorted(nodes_per_layer.items()):
                        logger.info(f"  Layer '{layer}': {count} nodes")

    def get_edges(self, data: bool = False, multiplex_edges: bool = False) -> Any:
        """A method for obtaining a network's edges

        Args:
            data: If True, return edge data along with edge tuples
            multiplex_edges: If True, include coupling edges in multiplex networks

        Yields:
            Edge tuples, optionally with data

        Raises:
            Exception: If network type is not specified
        """
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

    def get_nodes(self, data: bool = False) -> Any:
        """A method for obtaining a network's nodes

        Args:
            data: If True, return node data along with node identifiers

        Yields:
            Node identifiers, optionally with data
        """

        yield from self.core_network.nodes(data=data)

    def merge_with(self, target_px_object):
        """
        Merge two px objects.
        """

        all_edges = []
        for edge in target_px_object.get_edges(data=True):
            n1_name = edge[0][0]
            n1_type = edge[0][1]
            n2_name = edge[1][0]
            n2_type = edge[1][1]
            edge_type = edge[2].get("type")
            edge_weight = edge[2].get("weight")
            edge_obj = {
                "source": n1_name,
                "target": n2_name,
                "type": edge_type,
                "source_type": n1_type,
                "target_type": n2_type,
            }
            if edge_weight is not None:
                edge_obj["weight"] = edge_weight
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
                [n for n in self.core_network.nodes() if n[1] in input_list]
            )

        elif subset_by == "node_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n[0] in input_list]
            )

        elif subset_by == "node_layer_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n in input_list]
            )

        else:
            self.monitor("Please, select layers of node_names options..")

        tmp_net = multi_layer_network()
        tmp_net.core_network = subnetwork
        return tmp_net

    @require(
        lambda self: self.core_network is not None, "core_network must be initialized"
    )
    @require(
        lambda metric: metric in {"count", "mean", "max", "sum"},
        "metric must be valid aggregation method",
    )
    @ensure(lambda result: result is not None, "result must not be None")
    @ensure(
        lambda result: isinstance(result, (nx.Graph, nx.DiGraph)),
        "result must be a NetworkX graph",
    )
    def aggregate_edges(self, metric="count", normalize_by="degree"):
        """Edge aggregation method

        Count weights across layers and return a weighted network

        Args:
            param1: aggregation operator (count is default)
            param2: normalization of the values

        Returns:
             A simplified network.

        """

        layer_object = defaultdict(list)
        edge_object = {}

        for node in self.get_nodes():
            layer_object[node[1]].append(node)

        for layer, nodes in layer_object.items():
            layer_network = self.subnetwork(nodes)

            if normalize_by != "raw":
                connectivity = np.mean(
                    [
                        x[1]
                        for x in eval(
                            "nx." + normalize_by + "(layer_network.core_network)"
                        )
                    ]
                )

            else:
                connectivity = 1

            for edge in layer_network.get_edges():
                edge_new = (edge[0][0], edge[1][0])  # keep just the nids.
                if edge_new not in edge_object:

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
            self.monitor("Please,first call your_object.split_to_layers() method!")

        self.monitor("Finished edge cleaning..")

    def edges_from_temporal_table(self, edge_df):

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        edges = []
        for enx, _en in enumerate(node_first_names):
            edge = (
                str(node_first_names[enx]),
                str(node_second_names[enx]),
                str(layer_names[enx]),
                str(layer_names[enx]),
                1,
            )
            edges.append(edge)
        return edges

    def fill_tmp_with_edges(self, edge_df):

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        layer_edges = defaultdict(list)
        for enx, _en in enumerate(node_first_names):
            edge = (
                (str(node_first_names[enx]), str(layer_names[enx])),
                (str(node_second_names[enx]), str(layer_names[enx])),
            )
            layer_edges[layer_names[enx]].append(edge)

        # fill layer by layer
        for enx, layer in enumerate(self.layer_names):
            layer_ed = layer_edges[layer]
            self.tmp_layers[enx].add_edges_from(layer_ed)

    def split_to_layers(
        self,
        style="diagonal",
        compute_layouts="force",
        layout_parameters=None,
        verbose=True,
        multiplex=False,
        convert_to_simple=False,
    ):
        """A method for obtaining layerwise distributions"""

        if self.verbose:
            self.monitor("Network splitting in progress")

        # multilayer visualization
        if style == "diagonal":
            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_visualization(
                    self.core_network,
                    compute_layouts=compute_layouts,
                    layout_parameters=layout_parameters,
                    verbose=verbose,
                    multiplex=multiplex,
                )
            )

            try:
                self.real_layer_names = [
                    self.layer_inverse_name_map[lid] for lid in self.layer_names
                ]
            except (KeyError, AttributeError):
                logger.warning(
                    "self.layer_inverse_name_map not defined (name layers), please define them explicitly to have proper names present."
                )
                pass

        # hairball visualization
        if style == "hairball":
            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_visualization_hairball(
                    self.core_network, compute_layouts=True
                )
            )

        if style == "none":

            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_parsing(self.core_network)
            )

            if convert_to_simple:
                if self.directed:
                    self.separate_layers = [nx.DiGraph(x) for x in self.separate_layers]
                else:
                    self.separate_layers = [nx.Graph(x) for x in self.separate_layers]

    def get_layers(
        self,
        style="diagonal",
        compute_layouts="force",
        layout_parameters=None,
        verbose=True,
    ):
        """A method for obtaining layerwise distributions"""

        if self.verbose:
            self.monitor("Network splitting in progress")

        # multilayer visualization
        if style == "diagonal":
            return converters.prepare_for_visualization(
                self.core_network,
                compute_layouts=compute_layouts,
                network_type=self.network_type,
                layout_parameters=layout_parameters,
                verbose=verbose,
            )

        # hairball visualization
        if style == "hairball":
            return converters.prepare_for_visualization_hairball(
                self.core_network, compute_layouts=True
            )

    def _initiate_network(self):
        if self.core_network is None:
            if self.directed:
                self.core_network = nx.MultiDiGraph()
            else:
                self.core_network = nx.MultiGraph()

    def monoplex_nx_wrapper(self, method, kwargs=None):
        """a generic networkx function wrapper"""

        result = eval("nx." + method + "(self.core_network)")
        return result

    def _generic_edge_dict_manipulator(self, edge_dict_list, target_function):
        """
        Generic manipulator of edge dicts
        """

        if isinstance(edge_dict_list, dict):
            # Work with a copy to avoid mutating the original dictionary
            edge_dict = edge_dict_list.copy()
            if "source_type" in edge_dict.keys() and "target_type" in edge_dict.keys():
                edge_dict["u_for_edge"] = (
                    edge_dict["source"],
                    edge_dict["source_type"],
                )
                edge_dict["v_for_edge"] = (
                    edge_dict["target"],
                    edge_dict["target_type"],
                )
            else:
                edge_dict["u_for_edge"] = (edge_dict["source"], self.dummy_layer)
                edge_dict["v_for_edge"] = (edge_dict["target"], self.dummy_layer)

            # Remove keys only if they exist
            edge_dict.pop("target", None)
            edge_dict.pop("source", None)
            edge_dict.pop("target_type", None)
            edge_dict.pop("source_type", None)
            eval("self.core_network." + target_function + "(**edge_dict)")

        else:
            for edge_dict_item in edge_dict_list:
                # Work with a copy to avoid mutating the original dictionary
                edge_dict = edge_dict_item.copy()

                if (
                    "source_type" in edge_dict.keys()
                    and "target_type" in edge_dict.keys()
                ):
                    edge_dict["u_for_edge"] = (
                        edge_dict["source"],
                        edge_dict["source_type"],
                    )
                    edge_dict["v_for_edge"] = (
                        edge_dict["target"],
                        edge_dict["target_type"],
                    )
                else:
                    edge_dict["u_for_edge"] = (edge_dict["source"], self.dummy_layer)
                    edge_dict["v_for_edge"] = (edge_dict["target"], self.dummy_layer)

                # Remove keys only if they exist
                edge_dict.pop("target", None)
                edge_dict.pop("source", None)
                edge_dict.pop("target_type", None)
                edge_dict.pop("source_type", None)
                eval("self.core_network." + target_function + "(**edge_dict)")

    def _generic_edge_list_manipulator(self, edge_list, target_function, raw=False):
        """
        Generic manipulator of edge lists
        """

        if isinstance(edge_list[0], list):
            for edge in edge_list:
                n1, l1, n2, l2, w = edge
                if raw:
                    eval("self.core_network." + target_function + "((n1,l1),(n2,l2))")
                else:
                    eval(
                        "self.core_network."
                        + target_function
                        + "((n1,l1),(n2,l2),weight="
                        + str(w)
                        + ',type="default")'
                    )

        else:
            n1, l1, n2, l2, w = edge_list
            if raw:
                eval("self.core_network." + target_function + "((n1,l1),(n2,l2))")
            else:
                eval(
                    "self.core_network."
                    + target_function
                    + "((n1,l1),(n2,l2),weight="
                    + str(w)
                    + ',type="default"))'
                )

    def _generic_node_dict_manipulator(self, node_dict_list, target_function):
        """
        Generic manipulator of node dict
        """

        if isinstance(node_dict_list, dict):
            # Work with a copy to avoid mutating the original dictionary
            node_dict = node_dict_list.copy()

            if "type" in node_dict.keys():
                node_dict["node_for_adding"] = (node_dict["source"], node_dict["type"])
            else:
                node_dict["node_for_adding"] = (node_dict["source"], self.dummy_layer)

            # Remove keys only if they exist
            node_dict.pop("source", None)
            node_dict.pop("type", None)
            nname = node_dict["node_for_adding"]
            eval("self.core_network." + target_function + f"({nname})")

        else:
            # Handle list of node dictionaries
            for node_dict_item in node_dict_list:
                # Work with a copy to avoid mutating the original dictionary
                node_dict = node_dict_item.copy()

                if "type" in node_dict.keys():
                    node_dict["node_for_adding"] = (
                        node_dict["source"],
                        node_dict["type"],
                    )
                else:
                    node_dict["node_for_adding"] = (
                        node_dict["source"],
                        self.dummy_layer,
                    )

                # Remove keys only if they exist
                node_dict.pop("source", None)
                node_dict.pop("type", None)
                nname = node_dict["node_for_adding"]
                eval("self.core_network." + target_function + f"({nname})")

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

    def add_edges(
        self,
        edge_dict_list: Union[List[Dict], List[List], Tuple],
        input_type: str = "dict",
    ) -> None:
        """A method for adding edges.. Types are:
        dict,list or px_edge. See examples for further use.

        dict = {"source": n1,"target":n2,"type":sth}

        list = [[n1,t1,n2,t2] ...]

        px_edge = ((n1,t1)(n2,t2))

        Args:
            edge_dict_list: Edge data in dict, list, or px_edge format
            input_type: Format of edge data ('dict', 'list', or 'px_edge')

        Raises:
            Exception: If input_type is not valid
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
            self.core_network.add_edge(
                edge_dict_list[0], edge_dict_list[1], attr_dict=attr_dict
            )
        else:
            raise Exception("Please, use dict or list input.")

    def remove_edges(
        self, edge_dict_list: Union[List[Dict], List[List]], input_type: str = "list"
    ) -> None:
        """A method for removing edges..

        Args:
            edge_dict_list: Edge data in dict or list format
            input_type: Format of edge data ('dict' or 'list')

        Raises:
            Exception: If input_type is not valid
        """

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list, "remove_edge", raw=True)
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list, "remove_edge", raw=True)
        else:
            raise Exception("Please, use dict or list input.")

    def add_nodes(
        self, node_dict_list: Union[List[Dict], Dict], input_type: str = "dict"
    ) -> None:
        """A method for adding nodes..

        Args:
            node_dict_list: Node data in dict format
            input_type: Format of node data ('dict')
        """

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

        self.number_of_layers = len({x[1] for x in self.get_nodes()})

    def _get_num_nodes(self):
        """
        Count nodes
        """

        self.number_of_unique_nodes = len({x[0] for x in self.get_nodes()})

    def _node_layer_mappings(self):

        pass

    def get_tensor(self, sparsity_type="bsr"):
        """
        TODO
        """

    def _encode_to_numeric(self):

        if self.network_type != "multiplex":
            nmap = {}
            n_count = 0

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
                    weight = float(edge[2]["weight"])
                except (KeyError, IndexError, ValueError, TypeError):
                    weight = 1

                simple_graph.add_edge(
                    nmap[node_first], nmap[node_second], weight=weight
                )
            vectors = nx_to_scipy_sparse_matrix(simple_graph)
            self.numeric_core_network = vectors
            self.node_order_in_matrix = simple_graph.nodes()

        else:
            unique_layers = {n[1] for n in self.core_network.nodes()}
            individual_adj = []
            all_nodes = []
            for layer in unique_layers:
                layer_nodes = [n for n in self.core_network.nodes() if n[1] == layer]
                H = self.core_network.subgraph(layer_nodes)
                # NetworkX 3.x compatibility: use to_numpy_array instead of to_numpy_matrix
                try:
                    adj = nx.to_numpy_array(H)
                except AttributeError:
                    # Fallback for older NetworkX versions
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

                whole_mat.append(np.hstack(list(one_row)))
                vectors = np.vstack(list(whole_mat))
            self.numeric_core_network = vectors
            self.node_order_in_matrix = all_nodes

    def get_supra_adjacency_matrix(self, mtype="sparse"):
        """
        Get sparse representation of the supra matrix.

        Args:
            mtype: 'sparse' or 'dense' - matrix representation type

        Returns:
            Supra-adjacency matrix in requested format

        Warning:
            For large multilayer networks, dense matrices can consume
            significant memory (N*L)^2 * 8 bytes for float64.
        """

        if self.numeric_core_network is None:
            self._encode_to_numeric()

        # Calculate and warn about memory usage for dense matrices
        if mtype == "dense":
            num_nodes = len(self.get_nodes())
            num_layers = len(self.get_layers())
            supra_size = num_nodes * num_layers

            # Estimate memory for dense matrix (8 bytes per float64)
            estimated_bytes = supra_size * supra_size * 8
            estimated_gb = estimated_bytes / (1024**3)

            if estimated_gb > 10:
                import warnings

                warnings.warn(
                    f"Dense supra-adjacency matrix will be approximately {estimated_gb:.1f} GB "
                    f"({num_nodes} nodes × {num_layers} layers = {supra_size} × {supra_size} matrix). "
                    "This may cause memory issues. Consider using mtype='sparse' instead, "
                    "or analyzing layers independently.",
                    ResourceWarning,
                    stacklevel=2,
                )
            elif estimated_gb > 1:
                import warnings

                warnings.warn(
                    f"Dense supra-adjacency matrix will be approximately {estimated_gb:.1f} GB. "
                    "Consider using mtype='sparse' for better memory efficiency.",
                    ResourceWarning,
                    stacklevel=2,
                )

        #        print(self.numeric_core_network)
        if mtype == "sparse":
            return self.numeric_core_network
        else:
            try:
                return self.numeric_core_network.todense()
            except AttributeError:
                return self.numeric_core_network

    def visualize_matrix(self, kwargs=None):
        """
        Plot the matrix -- this plots the supra-adjacency matrix
        """

        if kwargs is None:
            kwargs = {}
        if server_mode:
            return 0

        adjmat = self.get_supra_adjacency_matrix(mtype="dense")
        supra_adjacency_matrix_plot(adjmat, **kwargs)

    def visualize_network(
        self,
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
        legend=False,
    ):
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
                    axis = draw_multilayer_default(
                        graphs,
                        display=False,
                        background_shape="circle",
                        labels=network_labels,
                        node_size=3,
                        verbose=verbose,
                    )
                else:
                    ax = draw_multilayer_default(
                        graphs,
                        display=False,
                        background_shape="circle",
                        labels=network_labels,
                        node_size=3,
                        verbose=verbose,
                    )
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
                            axis = draw_multiedges(
                                graphs,
                                edges,
                                alphachannel=alphachannel,
                                linepoints=linepoints,
                                linecolor="red",
                                curve_height=2,
                                linmod="bottom",
                                linewidth=linewidth,
                                resolution=resolution,
                            )
                        else:
                            ax = draw_multiedges(
                                graphs,
                                edges,
                                alphachannel=alphachannel,
                                linepoints=linepoints,
                                linecolor="red",
                                curve_height=2,
                                linmod="bottom",
                                linewidth=linewidth,
                                resolution=resolution,
                            )
                    else:
                        if axis:
                            axis = draw_multiedges(
                                graphs,
                                edges,
                                alphachannel=alphachannel,
                                linepoints="--",
                                linecolor="black",
                                curve_height=2,
                                linmod=orientation,
                                linewidth=linewidth,
                                resolution=resolution,
                            )
                        else:
                            ax = draw_multiedges(
                                graphs,
                                edges,
                                alphachannel=alphachannel,
                                linepoints="--",
                                linecolor="black",
                                curve_height=2,
                                linmod=orientation,
                                linewidth=linewidth,
                                resolution=resolution,
                            )
                    enum += 1
            else:
                enum = 1
                for edge_type, edges in multilinks.items():
                    if axis:
                        axis = draw_multiedges(graphs, edges, **parameters_multiedges)
                    else:
                        ax = draw_multiedges(graphs, edges, **parameters_multiedges)
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
                axis = hairball_plot(
                    graph, network_colors, layout_algorithm="force", legend=legend
                )
            else:
                ax = hairball_plot(
                    graph, network_colors, layout_algorithm="force", legend=legend
                )
            if show:
                plt.show()
            if axis:
                return axis
            else:
                return ax
        else:
            raise Exception(
                "Please, specify visualization style using: .style. keyword"
            )

    def get_nx_object(self):
        """Return only core network with proper annotations"""
        return self.core_network

    def test_scale_free(self):
        """
        Test the scale-free-nness of the network
        """

        val_vect = sorted(dict(nx.degree(self.core_network)).values(), reverse=True)
        alpha, sigma = topology.basic_pl_stats(val_vect)
        return (alpha, sigma)

    def get_label_matrix(self):
        """Return network labels"""
        return self.labels

    def _assign_types_for_hinmine(self):
        """
        Assing some basic types...
        """
        for node in self.get_nodes(data=True):
            node[1]["type"] = node[0][1]

    def get_decomposition_cycles(self, cycle=None):
        """A supporting method for obtaining decomposition triplets"""
        self._assign_types_for_hinmine()
        if self.hinmine_network is None:
            self.hinmine_network = load_hinmine_object(
                self.core_network, self.label_delimiter
            )
        return hinmine_get_cycles(self.hinmine_network)

    def get_decomposition(
        self, heuristic="all", cycle=None, parallel=False, alpha=1, beta=0
    ):
        """Core method for obtaining a network's decomposition in terms of relations"""

        if heuristic == "all":
            heuristic = [
                "idf",
                "tf",
                "chi",
                "ig",
                "gr",
                "delta",
                "rf",
                "okapi",
            ]  # all available
        if self.hinmine_network is None:
            if self.verbose:
                logger.info("Loading into a hinmine object..")
            self.hinmine_network = load_hinmine_object(
                self.core_network, self.label_delimiter
            )

        induced_net = 1
        if beta > 0:
            subset_nodes = []
            for n in self.core_network.nodes(data=True):
                if "labels" in n[1]:
                    subset_nodes.append(n[0])
            induced_net = self.core_network.subgraph(subset_nodes)
            for e in induced_net.edges(data=True):
                e[2]["weight"] = float(e[2]["weight"])
            induced_net = nx_to_scipy_sparse_matrix(induced_net)

        for x in heuristic:
            try:

                dout = hinmine_decompose(
                    self.hinmine_network, heuristic=x, cycle=cycle, parallel=parallel
                )
                decomposition = dout.decomposed["decomposition"]

                # use alpha and beta levels
                final_decomposition = alpha * decomposition + beta * induced_net

                #                print("Successfully decomposed: {}".format(x))

                yield (final_decomposition, dout.label_matrix, x)

            except Exception as es:
                logger.error("No decomposition found for: %s", x)
                logger.error(str(es))

    def load_embedding(self, embedding_file):
        """Embedding loading method"""

        self.embedding = parsers.parse_embedding(embedding_file)
        return self

    def get_degrees(self):
        """
        A simple wrapper which computes node degrees.
        """

        return dict(nx.degree(self.core_network))

    def serialize_to_edgelist(
        self,
        edgelist_file="./tmp/tmpedgelist.txt",
        tmp_folder="tmp",
        out_folder="out",
        multiplex=False,
    ):

        import os

        node_dict = {e: k for k, e in enumerate(list(self.get_nodes()))}
        outstruct = []

        # enumerated n l n l
        if multiplex:
            separate_layers = []

            for node in self.get_nodes():
                separate_layers.append(node[1])

            layer_mappings = {e: k for k, e in enumerate(set(separate_layers))}
            node_mappings = {k[0]: v for k, v in node_dict.items()}

            # add encoded edges
            for edge in self.get_edges():
                node_zero = node_mappings[edge[0][0]]
                node_first = node_mappings[edge[1][0]]
                layer_zero = layer_mappings[edge[0][1]]
                layer_first = layer_mappings[edge[1][1]]
                el = [node_zero, layer_zero, node_first, layer_first, 1]
                outstruct.append(el)
        else:
            # serialize as a simple edgelist
            for edge in self.get_edges(data=True):
                node_zero = node_dict[edge[0]]
                node_first = node_dict[edge[1]]
                if "weight" in edge[2]:
                    weight = edge[2]["weight"]
                else:
                    weight = 1
                el = [node_zero, node_first, weight]
                outstruct.append(el)

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        with open(edgelist_file, "w") as file:
            for el in outstruct:
                file.write(" ".join([str(x) for x in el]) + "\n")

        inverse_nodes = {a: b for b, a in node_dict.items()}
        #        inverse_layers = {a:b for b,a in layer_mappings.items()}

        return inverse_nodes

    def to_homogeneous_hypergraph(self):
        """
        Transform a multiplex network into a homogeneous graph using incidence gadget encoding.

        This method encodes the multiplex structure where each layer is represented by
        a unique prime number signature. Each edge becomes an edge-node connected to
        its endpoints and a cycle of length prime-1 that encodes the layer.

        Returns
        -------
        tuple (H, node_mapping, edge_info)
            H : networkx.Graph
                Homogeneous unlabeled graph encoding the multiplex structure.
            node_mapping : dict
                Maps each original node to its vertex-node in H.
            edge_info : dict
                Mapping from each edge-node in H to its (layer, endpoints) tuple.

        Examples
        --------
        >>> network = multi_layer_network(directed=False)
        >>> network.add_nodes([{'source': '1', 'type': 'A'}, {'source': '2', 'type': 'A'}], input_type='dict')
        >>> network.add_edges([{'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'}], input_type='dict')
        >>> H, node_map, edge_info = network.to_homogeneous_hypergraph()
        >>> print(f"Homogeneous graph has {len(H.nodes())} nodes")

        Notes
        -----
        This transformation uses prime-based signatures to encode layers:
        - Each layer is assigned a unique prime number (2, 3, 5, 7, ...)
        - Each edge in layer with prime p is connected to a cycle of length p
        - The cycle structure uniquely identifies the layer
        """
        from itertools import count

        from sympy import primerange

        H = nx.Graph()
        node_mapping = {}
        edge_info = {}

        # Handle empty network
        if self.core_network is None:
            return H, node_mapping, edge_info

        # Build multiplex dict from current network structure
        # Nodes in py3plex are stored as tuples: (node_id, layer_id)
        multiplex = {}

        for u, v in self.core_network.edges():
            # u and v are tuples like ('1', 'A')
            u_node, u_layer = u
            v_node, v_layer = v

            # Only include intra-layer edges (same layer)
            if u_layer == v_layer:
                if u_layer not in multiplex:
                    multiplex[u_layer] = []
                multiplex[u_layer].append((u_node, v_node))

        # Step 1: create vertex-nodes
        all_nodes = set()
        for edges in multiplex.values():
            for e in edges:
                for n in e:
                    all_nodes.add(n)

        for node in all_nodes:
            node_mapping[node] = f"v_{node}"
            H.add_node(f"v_{node}")

        # Step 2: assign prime-based signatures to layers
        primes = list(primerange(2, 2000))
        layer_to_prime = {
            layer: primes[i] for i, layer in enumerate(sorted(multiplex.keys()))
        }

        eid = count()

        for layer, edges in multiplex.items():
            p = layer_to_prime[layer]
            for u, v in edges:
                y = f"e_{next(eid)}"
                H.add_node(y)

                # connect to endpoints
                H.add_edges_from([(node_mapping[u], y), (node_mapping[v], y)])

                # attach the signature cycle C_p
                cycle_nodes = [f"{y}_s{i}" for i in range(p - 1)]
                H.add_nodes_from(cycle_nodes)
                sig_edges = [(y, cycle_nodes[0])]
                sig_edges += [
                    (cycle_nodes[i], cycle_nodes[i + 1]) for i in range(p - 2)
                ]
                sig_edges.append((cycle_nodes[-1], y))
                H.add_edges_from(sig_edges)

                edge_info[y] = (layer, (u, v))

        return H, node_mapping, edge_info

    def from_homogeneous_hypergraph(self, H):
        """
        Decode a homogeneous graph created by to_homogeneous_hypergraph.

        This method reconstructs a multiplex network from its incidence gadget encoding.
        It identifies edge-nodes by their degree and cycle structure, then reconstructs
        the original layers based on cycle lengths (prime numbers).

        Parameters
        ----------
        H : networkx.Graph
            Homogeneous graph created by to_homogeneous_hypergraph().

        Returns
        -------
        dict
            Dictionary mapping layer names to lists of edges: {layer: [(u, v), ...]}

        Examples
        --------
        >>> network = multi_layer_network()
        >>> network.add_layer("A")
        >>> network.add_nodes([("1", "A"), ("2", "A")])
        >>> network.add_edges([(("1", "A"), ("2", "A"))])
        >>> H, node_map, edge_info = network.to_homogeneous_hypergraph()
        >>> recovered = network.from_homogeneous_hypergraph(H)
        >>> print(recovered)
        {'layer_with_prime_2': [('1', '2')]}

        Notes
        -----
        The decoded layer names indicate the prime number used for encoding:
        - "layer_with_prime_2" corresponds to the first layer
        - "layer_with_prime_3" corresponds to the second layer, etc.
        """
        multiplex = {}

        for n in H.nodes():
            # Heuristic: edge-nodes are adjacent to two vertex-nodes (starting with 'v_')
            v_neighbors = [v for v in H[n] if str(v).startswith("v_")]
            if len(v_neighbors) == 2:
                # Find cycle length by checking signature nodes
                # The edge-node is connected to signature nodes forming a cycle
                all_neighbors = list(H[n])
                signature_neighbors = [
                    v for v in all_neighbors if not str(v).startswith("v_")
                ]

                # The cycle includes the edge-node itself plus all signature nodes
                # For a cycle of length p, we have: edge-node + (p-1) signature nodes
                cycle_len = len(signature_neighbors) + 1

                layer = f"layer_with_prime_{cycle_len}"
                u = str(v_neighbors[0]).replace("v_", "")
                v = str(v_neighbors[1]).replace("v_", "")
                multiplex.setdefault(layer, []).append((u, v))

        return multiplex


if __name__ == "__main__":

    multinet = multi_layer_network("../../datasets/imdb_gml.gml")
    multinet.basic_stats()
