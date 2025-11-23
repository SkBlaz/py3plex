# set of parsers used in Py3plex.

import glob
import gzip
import itertools
import json
from typing import Any, Dict, List, Tuple, Union

import networkx as nx
import numpy as np
import pandas as pd
import scipy.io

from py3plex.logging_config import get_logger

from .nx_compat import nx_from_scipy_sparse_matrix, nx_read_gpickle, nx_write_gpickle
from .supporting import add_mpx_edges

# Optional formal verification support
try:
    from icontract import ensure, require

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

    ICONTRACT_AVAILABLE = False

logger = get_logger(__name__)


@require(
    lambda file_name: isinstance(file_name, str) and len(file_name) > 0,
    "file_name must be a non-empty string",
)
@ensure(lambda result: result[0] is not None, "result graph must not be None")
@ensure(
    lambda result: isinstance(result[0], (nx.MultiGraph, nx.MultiDiGraph)),
    "result must be a MultiGraph or MultiDiGraph",
)
def parse_gml(
    file_name: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    Parse a gml network.

    Args:
        file_name: Path to GML file
        directed: Whether to create directed graph

    Returns:
        Tuple of (multigraph, possible labels)

    Contracts:
        - Precondition: file_name must be a non-empty string
        - Postcondition: result graph is not None
        - Postcondition: result is a MultiGraph or MultiDiGraph
    """

    H = nx.read_gml(file_name)

    if directed:
        A = nx.MultiDiGraph()
    else:
        A = nx.MultiGraph()

    node_type_map = {}
    # initial type maps
    for node in H.nodes(data=True):
        node_type_map[node[0]] = node[1]

        # read into structure
    for edge in H.edges(data=True):
        node_first = (edge[0], node_type_map[edge[0]]["type"])
        node_second = (edge[1], node_type_map[edge[1]]["type"])
        edge_props = edge[2]

        A.add_node(node_first, **node_type_map[edge[0]])
        A.add_node(node_second, **node_type_map[edge[1]])
        A.add_edge(node_first, node_second, **edge_props)

    # add labels
    return (A, None)


@require(lambda nx_object: nx_object is not None, "nx_object must not be None")
@require(
    lambda nx_object: isinstance(nx_object, nx.Graph),
    "nx_object must be a NetworkX graph",
)
@ensure(lambda result: result[0] is not None, "result graph must not be None")
def parse_nx(nx_object: nx.Graph, directed: bool) -> Tuple[nx.Graph, None]:
    """
    Core parser for networkx objects.

    Args:
        nx_object: A networkx graph
        directed: Whether the graph is directed

    Returns:
        Tuple of (graph, None)

    Contracts:
        - Precondition: nx_object must not be None
        - Precondition: nx_object must be a NetworkX graph
        - Postcondition: result graph is not None
    """

    return (nx_object, None)


@require(
    lambda file_name: isinstance(file_name, str) and len(file_name) > 0,
    "file_name must be a non-empty string",
)
@ensure(lambda result: result[0] is not None, "network must not be None")
def parse_matrix(file_name: str, directed: bool) -> Tuple[Any, Any]:
    """
    Parser for matrices.

    Args:
        file_name: Path to .mat file
        directed: Whether the graph is directed

    Returns:
        Tuple of (network, group) from the .mat file

    Contracts:
        - Precondition: file_name must be a non-empty string
        - Postcondition: network must not be None
    """

    mat = scipy.io.loadmat(file_name)
    return (mat["network"], mat["group"])


def parse_matrix_to_nx(file_name: str, directed: bool) -> Union[nx.Graph, nx.DiGraph]:
    """
    Parser for matrices to NetworkX graph.

    Args:
        file_name: Path to .mat file
        directed: Whether to create directed graph

    Returns:
        NetworkX Graph or DiGraph
    """

    mat = scipy.io.loadmat(file_name)
    if directed:
        create_using = nx.DiGraph()

    else:
        create_using = nx.Graph()

    G = nx_from_scipy_sparse_matrix(mat["network"], create_using=create_using)

    if directed:
        G_final = nx.DiGraph()

    else:
        G_final = nx.Graph()

    for n in G.nodes():
        G_final.add_node((n, "generic"))

    for e in G.edges():
        G_final.add_edge((e[0], "generic"), (e[1], "generic"))

    return (G_final, None)


@require(
    lambda file_name: isinstance(file_name, str) and len(file_name) > 0,
    "file_name must be a non-empty string",
)
@ensure(lambda result: result[0] is not None, "result graph must not be None")
@ensure(
    lambda result: isinstance(result[0], (nx.MultiGraph, nx.MultiDiGraph)),
    "result must be a MultiGraph or MultiDiGraph",
)
def parse_gpickle(
    file_name: str, directed: bool = False, layer_separator: Union[str, None] = None
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    A parser for generic Gpickle as stored by Py3plex.

    Args:
        file_name: Path to gpickle file
        directed: Whether to create directed graph
        layer_separator: Optional separator for layer parsing

    Contracts:
        - Precondition: file_name must be a non-empty string
        - Postcondition: result graph is not None
        - Postcondition: result is a MultiGraph or MultiDiGraph
    """

    logger.info("Parsing gpickle..")
    if directed:
        A = nx.MultiDiGraph()
    else:
        A = nx.MultiGraph()

    G = nx_read_gpickle(file_name)

    if layer_separator is not None:
        for edge in G.edges():
            e1, e2 = edge
            try:
                layer1, n1 = e1.split(layer_separator)
                layer2, n2 = e2.split(layer_separator)
                A.add_edge((n1, layer1), (n2, layer2))
            except (ValueError, AttributeError):
                pass
    else:
        A = G

    todrop = []
    for node in A.nodes(data=True):
        if "labels" in node[1]:
            if node[1]["labels"] == "":
                todrop.append(node[0])
    A.remove_nodes_from(todrop)
    return (A, None)


def parse_gpickle_biomine(
    file_name: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    Gpickle parser for biomine graphs
    Args:
        file_name: Path to gpickle containing BioMine data
        directed: Whether to create directed graph
    """

    # convert the biomine
    input_graph = nx_read_gpickle(file_name)

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for edge in input_graph.edges(data=True):

        l1, n1 = edge[0].split("_")[:2]
        l2, n2 = edge[1].split("_")[:2]
        G.add_edge((n1, l1), (n2, l2), type=edge[2]["key"])

    return (G, None)


def parse_detangler_json(
    file_path: str, directed: bool = False
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    Parser for generic Detangler files
    Args:
        file_path: Path to Detangler JSON file
        directed: Whether to create directed graph
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    with open(file_path) as f:
        graph = json.load(f)

    id2n = {}
    for n in graph["nodes"]:
        id2n[n["id"]] = n
        layers = n["descriptors"].split(";")
        node = n["label"]
        for l in layers:
            G.add_node((node, l))
        for c in itertools.combinations(layers, 2):
            G.add_edge((node, c[0]), (node, c[1]))

    for e in graph["links"]:
        s = id2n[e["source"]]["label"]
        t = id2n[e["target"]]["label"]
        layers = e["descriptors"].split(";")
        for l in layers:
            G.add_edge((s, l), (t, l))

    return (G, None)


def parse_multi_edgelist(
    input_name: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    A generic multiedgelist parser
    n l n l w
    Args:
        input_name: Path to text file containing multiedges
        directed: Whether to create directed graph
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    with open(input_name) as IN:
        for line in IN:
            parts = line.strip().split()

            if len(parts) == 5:
                node_first, layer_first, node_second, layer_second, weight = parts

            else:
                node_first, layer_first, node_second, layer_second = parts
                weight = "1"

            if layer_first == layer_second and node_first == node_second:

                # first case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_edge(
                    (node_first, layer_first), (node_first, layer_first), weight=weight
                )
            elif layer_first == layer_second and node_first != node_second:

                # second case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_node((node_second, layer_second), type=layer_first)
                G.add_edge(
                    (node_first, layer_first),
                    (node_second, layer_second),
                    weight=weight,
                )
            else:
                # default case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_node((node_second, layer_second), type=layer_second)
                G.add_edge(
                    (node_first, layer_first),
                    (node_second, layer_second),
                    weight=weight,
                )

    return (G, None)


def parse_simple_edgelist(
    input_name: str, directed: bool
) -> Tuple[Union[nx.Graph, nx.DiGraph], None]:
    """
    Simple edgelist n n w
    Args:
        input_name: Path to text file
        directed: Whether to create directed graph
    """

    if directed:
        G = nx.DiGraph()

    else:
        G = nx.Graph()

    if ".gz" in input_name:
        handle = gzip.open(input_name, "rt")

    else:
        handle = open(input_name)

    with handle as IN:
        for line in IN:
            if line.split()[0] != "#":
                parts = line.strip().split()
                if len(parts) == 3:
                    node_first_str, node_second_str, weight_str = parts
                    weight = float(weight_str)
                elif len(parts) == 2:
                    node_first_str, node_second_str = parts
                    weight = 1.0
                else:
                    continue

                node_first = (node_first_str, "null")
                node_second = (node_second_str, "null")

                G.add_node(node_first, type="null")
                G.add_node(node_second, type="null")

                G.add_edge(node_first, node_second, weight=weight)

    return (G, None)


def parse_edgelist_multi_types(
    input_name: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """Parse an edgelist file with multiple edge types.

    Reads a text file where each line represents an edge, optionally with weights
    and edge types. Lines starting with '#' are treated as comments.

    File Format:
        node1 node2 [weight] [edge_type]

        Lines starting with '#' are ignored (comments)

    Args:
        input_name: Path to edgelist file
        directed: Whether to create a directed graph

    Returns:
        Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
            (parsed_graph, None for labels)

    Notes:
        - All nodes are assigned to a "null" layer
        - Default weight is 1 if not specified
        - Edge type is optional (4th column)
        - Handles both 2-column (node pairs) and 3+ column formats

    Examples:
        >>> # File content:
        >>> # A B 1.0 friendship
        >>> # B C 2.0 collaboration
        >>> graph, _ = parse_edgelist_multi_types('edges.txt', directed=False)  # doctest: +SKIP
    """
    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    with open(input_name) as IN:
        for line in IN:
            if line.split()[0] != "#":
                parts = line.strip().split()
                if len(parts) > 2:
                    node_first, node_second, weight = parts
                    edge_type = parts[3]
                else:
                    node_first, node_second = parts
                    weight = "1"
                    edge_type = None

                G.add_node((node_first, "null"), type="null")
                G.add_node((node_second, "null"), type="null")
                G.add_edge(node_first, node_second, weight=weight, type=edge_type)
    return (G, None)


def parse_spin_edgelist(input_name: str, directed: bool) -> Tuple[nx.Graph, None]:
    """Parse SPIN format edgelist file.

    SPIN format includes node pairs with edge tags and optional weights.

    File Format:
        node1 node2 tag [weight]

        Each line: source_node target_node edge_tag [optional_weight]

    Args:
        input_name: Path to SPIN edgelist file
        directed: Whether to create directed graph (currently creates undirected)

    Returns:
        Tuple[nx.Graph, None]: (parsed_graph, None for labels)

    Notes:
        - Currently always returns nx.Graph (undirected) regardless of directed parameter
        - Edge tag is stored in edge 'type' attribute
        - Default weight is 1 if not specified (4th column)

    Examples:
        >>> # File content:
        >>> # A B protein_interaction 0.95
        >>> # B C gene_regulation 0.80
        >>> graph, _ = parse_spin_edgelist('spin_edges.txt', directed=False)  # doctest: +SKIP
    """

    G = nx.Graph()
    with open(input_name) as IN:
        for line in IN:

            parts = line.strip().split()
            node_first = parts[0]
            node_second = parts[1]
            tag = parts[2]
            if len(parts) >= 4:
                weight = parts[3]
            else:
                weight = "1"

            G.add_node(node_first)
            G.add_node(node_second)
            G.add_edge(node_first, node_second, weight=weight, type=tag)

    return (G, None)


def parse_embedding(input_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loader for generic embedding as outputed by GenSim

    Args:
        input_name: Path to embedding file

    Returns:
        Tuple of (embedding matrix, embedding indices)
    """

    embedding_matrix: List[List[str]] = []
    embedding_indices: List[str] = []
    with open(input_name) as IN:
        for line in IN:
            parts = line.strip().split()
            if len(parts) == 2:
                pass
            else:
                embedding_matrix.append(parts[1:])
                embedding_indices.append(parts[0])
    embedding_matrix_np = np.matrix(embedding_matrix)
    embedding_indices_np = np.array(embedding_indices)
    return (embedding_matrix_np, embedding_indices_np)


def parse_multiedge_tuple_list(
    network: list, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """
    Parse a list of edge tuples into a multilayer network.

    Args:
        network: List of edge tuples (node_first, node_second, layer_first, layer_second, weight)
        directed: Whether to create directed graph
    """
    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()
    for _edgetuple in network:
        #        ((str(node_first_names[enx]),str(layer_names[enx])),(str(node_second_names[enx]),str(layer_names[enx])))

        node_first, node_second, layer_first, layer_second, weight = _edgetuple

        G.add_node((node_first, layer_first))
        G.add_node((node_second, layer_second))
        G.add_edge(
            (node_first, layer_first), (node_second, layer_second), weight=weight
        )

        # G.add_node(node_first,type=layer_first)
        # G.add_node(node_second,type=layer_second)
        # G.add_edge(node_first,node_second,weight=weight)

    return (G, None)


def parse_multiplex_edges(
    input_name: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
    """Parse a multiplex edgelist file where each line specifies layer and edge.

    File Format:
        layer node1 node2 [weight]

        Each line: layer_id source_node target_node [optional_weight]

    Args:
        input_name: Path to multiplex edgelist file
        directed: Whether to create a directed graph

    Returns:
        Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None]:
            (parsed_graph, None for labels)

    Notes:
        - Each edge belongs to a specific layer (first column)
        - Nodes are represented as (node_id, layer) tuples
        - Default weight is 1 if not specified
        - All edges have type='default' attribute
        - Automatically couples nodes across layers for multiplex structure

    Examples:
        >>> # File content:
        >>> # layer1 A B 1.5
        >>> # layer2 A B 2.0
        >>> # layer1 B C 1.0
        >>> graph, _ = parse_multiplex_edges('multiplex.txt', directed=False)  # doctest: +SKIP
        >>> # Creates nodes: (A, layer1), (A, layer2), (B, layer1), etc.
    """

    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    unique_layers = set()
    with open(input_name) as ef:
        for line in ef:
            parts = line.strip().split(" ")
            node_first = str(parts[1])
            node_second = str(parts[2])
            layer = parts[0]
            if len(parts) > 2:
                weight = parts[3]
            else:
                weight = "1"
            G.add_node((node_first, str(layer)))
            G.add_node((node_second, str(layer)))
            unique_layers.add(str(layer[0]))
            G.add_edge(
                (node_first, str(layer)),
                (node_second, str(layer)),
                weight=float(weight),
                type="default",
            )

    return (G, None)


def parse_multiplex_folder(
    input_folder: str, directed: bool
) -> Tuple[Union[nx.MultiGraph, nx.MultiDiGraph], None, pd.DataFrame]:
    """Parse a folder containing multiplex network files.

    Expects a folder with specific file formats for edges, layers, and optional activity.

    Expected Files:
        - *.edges: Edge information (format: layer_id node1 node2 weight)
        - layers.txt: Layer definitions (format: layer_id layer_name)
        - activity.txt: Optional temporal activity (format: node1 node2 timestamp layer_name)

    Args:
        input_folder: Path to folder containing multiplex network files
        directed: Whether to create a directed graph

    Returns:
        Tuple containing:
            - Union[nx.MultiGraph, nx.MultiDiGraph]: Parsed multilayer graph
            - None: Placeholder for labels (not used)
            - pd.DataFrame: Time series activity data (empty if no activity.txt)

    Notes:
        - Uses glob to find files with specific extensions
        - Layer mapping is built from layers.txt
        - Activity data is optional and returned as pandas DataFrame
        - Nodes are represented as (node_id, layer_id) tuples

    Examples:
        >>> # Folder structure:
        >>> # my_network/
        >>> #   network.edges
        >>> #   layers.txt
        >>> #   activity.txt (optional)
        >>> graph, _, activity_df = parse_multiplex_folder('my_network/', directed=False)
    """

    # 16 17 1377438155 RT -> activity n1 n2 time label
    # 1 RT -> layer name
    # 1 61450 1252 1 -> layer n1 n2 w
    # 9 9 node id, lab

    names = glob.glob(input_folder + "/*")
    edges_file = [x for x in names if ".edges" in x]
    activity_file = [x for x in names if "activity.txt" in x]
    time_series_tuples = None
    layer_file = [x for x in names if "layers.txt" in x]
    layer_dict = {}
    for lx in layer_file:
        with open(lx) as lf:
            for line in lf:
                lid, lname = line.strip().split(" ")
                layer_dict[lname] = lid

    if len(activity_file) >= 1:
        time_series_tuples = []  # defaultdict(list)
        for ac in activity_file:
            with open(ac) as acf:
                for line in acf:
                    n1, n2, timestamp, layer_name = line.strip().split(" ")
                    time_series_tuples.append(
                        {
                            "node_first": 1,
                            "node_second": n2,
                            "layer": layer_dict[layer_name],
                            "timestamp": timestamp,
                        }
                    )
        time_series_tuples = pd.DataFrame(time_series_tuples)
    else:
        time_series_tuples = pd.DataFrame()

    #    nodes_file = [x for x in names if "nodes.txt" in x]

    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    for edgefile in edges_file:
        with open(edgefile) as ef:
            for line in ef:
                parts = line.strip().split(" ")
                node_first = parts[1]
                node_second = parts[2]
                layer = parts[0]
                weight = parts[3]
                G.add_node((node_first, str(layer)))
                G.add_node((node_second, str(layer)))
                G.add_edge(
                    (node_first, str(layer)),
                    (node_second, str(layer)),
                    key="default",
                    weight=weight,
                    type="default",
                )

    return (G, None, time_series_tuples)


# main parser method
def parse_network(
    input_name: Union[str, Any],
    f_type: str = "gml",
    directed: bool = False,
    label_delimiter: Union[str, None] = None,
    network_type: str = "multilayer",
) -> Tuple[Any, Any, Any]:
    """
    A wrapper method for available parsers!

    Args:
        input_name: Path to network file or network object
        f_type: Type of file format to parse
        directed: Whether to create directed graph
        label_delimiter: Optional delimiter for labels
        network_type: Type of network (multilayer or multiplex)

    Returns:
        Tuple of (parsed_network, labels, time_series)
    """

    time_series = None
    if f_type == "gml":
        parsed_network, labels = parse_gml(input_name, directed)

    elif f_type == "nx":
        parsed_network, labels = parse_nx(input_name, directed)

    elif f_type == "multiplex_folder":
        parsed_network, labels, time_series = parse_multiplex_folder(
            input_name, directed
        )

    elif f_type == "sparse":
        parsed_network, labels = parse_matrix(input_name, directed)

    elif f_type == "sparse_network":
        parsed_network, labels = parse_matrix_to_nx(input_name, directed)

    elif f_type == "gpickle_biomine":
        parsed_network, labels = parse_gpickle_biomine(input_name, directed)

    elif f_type == "gpickle":
        parsed_network, labels = parse_gpickle(input_name, directed)

    elif f_type == "multiedgelist":
        parsed_network, labels = parse_multi_edgelist(input_name, directed)

    elif f_type == "detangler_json":
        parsed_network, labels = parse_detangler_json(input_name, directed)

    elif f_type == "edgelist":
        parsed_network, labels = parse_simple_edgelist(input_name, directed)

    elif f_type == "edgelist_spin":
        parsed_network, labels = parse_spin_edgelist(input_name, directed)

    elif f_type == "edgelist_with_edge_types":
        parsed_network, labels = parse_edgelist_multi_types(input_name, directed)

    elif f_type == "multiedge_tuple_list":
        parsed_network, labels = parse_multiedge_tuple_list(input_name, directed)  # type: ignore[arg-type]

    elif f_type == "multiplex_edges":
        parsed_network, labels = parse_multiplex_edges(input_name, directed)

    if network_type == "multilayer":
        return (parsed_network, labels, time_series)

    elif network_type == "multiplex":
        multiplex_graph = add_mpx_edges(parsed_network)
        return (multiplex_graph, labels, time_series)

    else:
        raise Exception("Please, specify heterogeneous network type.")


def load_edge_activity_raw(activity_file: str, layer_mappings: dict) -> pd.DataFrame:
    """
    Basic parser for loading generic activity files. Here, temporal edges are given as tuples -> this can be easily transformed for example into a pandas dataframe!

    Args:
        activity_file: Path to activity file
        layer_mappings: Dictionary mapping layer names to IDs

    Returns:
        DataFrame with edge activity data
    """

    time_series_tuples = []
    with open(activity_file, "r+") as acf:
        for line in acf:
            n1, n2, timestamp, layer_name = line.strip().split(" ")

            time_series_tuples.append(
                {
                    "node_first": n1,
                    "node_second": n2,
                    "layer_name": layer_mappings[layer_name],
                    "timestamp": timestamp,
                }
            )
    outframe = pd.DataFrame(time_series_tuples)
    return outframe


def load_edge_activity_file(
    fname: str, layer_mapping: Union[str, None] = None
) -> pd.DataFrame:

    # Example edge looks like this: 11 11 1375695069 RE

    if layer_mapping is not None:
        lmap = {}
        with open(layer_mapping) as lm:
            for line in lm:
                code, name = line.strip().split()
                lmap[name] = code

    outframe = pd.DataFrame()
    data = []
    with open(fname) as fn:
        for line in fn:
            node1, node2, timestamp, layer = line.strip().split()
            if layer_mapping is not None:
                layer = lmap[layer]
            data.append(
                {
                    "node_first": node1,
                    "node_second": node2,
                    "layer": layer,
                    "timestamp": timestamp,
                }
            )
    outframe = outframe.from_dict(data)
    return outframe


def load_temporal_edge_information(
    input_network: str, input_type: str, layer_mapping: Union[str, None] = None
) -> Union[pd.DataFrame, None]:

    if input_type == "edge_activity":
        return load_edge_activity_file(input_network, layer_mapping=layer_mapping)
    else:
        return None


def save_gpickle(input_network: Any, output_file: str) -> None:
    nx_write_gpickle(input_network, output_file)


def save_multiedgelist(
    input_network: Any,
    output_file: str,
    attributes: bool = False,
    encode_with_ints: bool = False,
) -> Union[Tuple[Dict[Any, str], Dict[Any, str]], None]:
    """
    Save multiedgelist -- as n1, l1, n2, l2, w

    Returns:
        When encode_with_ints is True, returns tuple of (node_encodings, type_encodings)
        Otherwise returns None
    """

    if encode_with_ints:

        unique_nodes = {n[0] for n in input_network.nodes()}
        unique_node_types = {n[1] for n in input_network.nodes()}
        node_encodings = {real: str(enc) for enc, real in enumerate(unique_nodes)}
        type_encodings = {real: str(enc) for enc, real in enumerate(unique_node_types)}
        with open(output_file, "w+") as fh:
            for edge in input_network.edges(data=True):
                n1, l1 = edge[0]
                n2, l2 = edge[1]
                fh.write(
                    "\t".join(
                        [
                            node_encodings[n1],
                            type_encodings[l1],
                            node_encodings[n2],
                            type_encodings[l2],
                        ]
                    )
                    + "\n"
                )

        return (node_encodings, type_encodings)

    else:
        with open(output_file, "w+") as fh:
            for edge in input_network.edges(data=True):
                n1, l1 = edge[0]
                n2, l2 = edge[1]
                fh.write("\t".join([n1, l1, n2, l2]) + "\n")
        return None


def save_edgelist(
    input_network: nx.Graph, output_file: str, attributes: bool = False
) -> None:
    """Save network to edgelist format.

    For multilayer networks (where nodes are tuples of (node_id, layer)),
    saves in format: node1 layer1 node2 layer2

    For regular networks, saves in format: node1 node2
    """
    # Handle case where network is None or empty
    if input_network is None or input_network.number_of_nodes() == 0:
        # Just create an empty file
        with open(output_file, "w") as fh:
            pass
        logger.info("Finished writing the network..")
        return

    # Check if this is a multilayer network by examining node structure
    is_multilayer = False
    sample_node = next(iter(input_network.nodes()))
    # Multilayer nodes are tuples of (node_id, layer)
    is_multilayer = isinstance(sample_node, tuple) and len(sample_node) == 2

    with open(output_file, "w") as fh:
        if is_multilayer:
            # Save in multilayer format: node1 layer1 node2 layer2 (space-separated)
            for edge in input_network.edges(data=attributes):
                n1, l1 = edge[0]
                n2, l2 = edge[1]
                fh.write(f"{n1} {l1} {n2} {l2}\n")
        else:
            # For regular networks, convert to integers as before
            input_network = nx.convert_node_labels_to_integers(
                input_network, first_label=0, ordering="default", label_attribute=None
            )
            # Save in simple format: node1 node2
            for edge in input_network.edges():
                fh.write(f"{edge[0]} {edge[1]}\n")

    logger.info("Finished writing the network..")


if __name__ == "__main__":
    logger.info("Testing parser")
    #    print (nx.info(parse_gml("../../datasets/imdb_gml.gml",f_type="gml",directed=False)))
    #    print (nx.info(parse_network("../../datasets/epigenetics.gpickle",f_type="gpickle_biomine",directed=False)))
    # print (nx.info(parse_network("../../datasets/multiedgelist.txt",f_type="multiedgelist",directed=False)))

    parse_embedding("../../datasets/karate.emb")
