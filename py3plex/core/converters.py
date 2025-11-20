# converters
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from py3plex.logging_config import get_logger
from py3plex.visualization.layout_algorithms import (
    compute_force_directed_layout,
    compute_random_layout,
    np,
)

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


@require(lambda network: network is not None, "network must not be None")
@require(
    lambda network: network.number_of_nodes() > 0, "network must have at least one node"
)
@require(
    lambda compute_layouts: compute_layouts
    in {"force", "random", "custom_coordinates"},
    "compute_layouts must be 'force', 'random', or 'custom_coordinates'",
)
@ensure(
    lambda network, result: all("pos" in network.nodes[n] for n in network.nodes()),
    "all nodes must have 'pos' attribute after layout computation",
)
def compute_layout(
    network: nx.Graph,
    compute_layouts: str,
    layout_parameters: Optional[Dict[str, Any]],
    verbose: bool,
) -> nx.Graph:
    """
    Compute and normalize layout for a network.

    Args:
        network: NetworkX graph to compute layout for
        compute_layouts: Layout algorithm to use ('force', 'random', 'custom_coordinates')
        layout_parameters: Optional parameters for layout algorithms
        verbose: Whether to print verbose output

    Returns:
        Network with 'pos' attribute added to nodes

    Contracts:
        - Precondition: network must not be None and must have at least one node
        - Precondition: compute_layouts must be a valid algorithm name
        - Postcondition: all nodes have 'pos' attribute (layout preserves nodes)
    """

    if compute_layouts == "force":
        tmp_pos = compute_force_directed_layout(
            network, layout_parameters, verbose=verbose
        )
    elif compute_layouts == "random":
        tmp_pos = compute_random_layout(network)

    elif compute_layouts == "custom_coordinates":
        tmp_pos = layout_parameters["pos"]

    keys = []
    value_pairs = []
    for k, v in tmp_pos.items():
        value_pairs.append(v)
        keys.append(k)

    # Use ndarray instead of deprecated matrix
    coordinate_matrix = np.array(value_pairs)
    x_min = np.min(coordinate_matrix[:, 0])
    x_max = np.max(coordinate_matrix[:, 0])
    y_min = np.min(coordinate_matrix[:, 1])
    y_max = np.max(coordinate_matrix[:, 1])

    # Normalize coordinates, handling degenerate cases
    x_range = x_max - x_min
    y_range = y_max - y_min
    if x_range > 0:
        norm_x = (coordinate_matrix[:, 0] - x_min) / x_range
    else:
        norm_x = np.zeros(len(coordinate_matrix))

    if y_range > 0:
        norm_y = (coordinate_matrix[:, 1] - y_min) / y_range
    else:
        norm_y = np.zeros(len(coordinate_matrix))

    coordinate_matrix[:, 0] = norm_x
    coordinate_matrix[:, 1] = norm_y

    tmp_pos = {}
    for enx, j in enumerate(keys):
        tmp_pos[j] = coordinate_matrix[enx]

    for node in network.nodes(data=True):
        coordinates = tmp_pos[node[0]]
        if network.degree(node[0]) == 0:
            coordinates = np.array(coordinates) / 2
        elif network.degree(node[0]) == 1:
            coordinates = np.array(coordinates) / 2
        if np.abs(coordinates[0]) > 1 or np.abs(coordinates[1]) > 1:
            coordinates = np.random.rand(1) * coordinates / np.linalg.norm(coordinates)

        node[1]["pos"] = coordinates


def prepare_for_visualization(
    multinet: nx.Graph,
    network_type: str = "multilayer",
    compute_layouts: str = "force",
    layout_parameters: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
    multiplex: bool = False,
) -> Tuple[List[Any], List[nx.Graph], Any]:
    """
    This functions takes a multilayer object and returns individual layers, their names, as well as multilayer edges spanning over multiple layers.

    Args:
        multinet: multilayer network object
        network_type: "multilayer" or "multiplex"
        compute_layouts: Layout algorithm ('force', 'random', etc.)
        layout_parameters: Optional layout parameters
        verbose: Whether to print progress information
        multiplex: Whether to treat as multiplex network

    Returns:
        tuple: (layer_names, layer_networks_list, multiedges)
            - layer_names: List of layer names
            - layer_networks_list: List of NetworkX graph objects for each layer
            - multiedges: Dictionary of edges spanning multiple layers

    """

    if network_type == "multilayer":
        multiplex = False
    else:
        multiplex = True

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])
        except Exception:
            pass

    networks = {layer_name: multinet.subgraph(v) for layer_name, v in layers.items()}

    if multiplex:
        compute_layout(multinet, compute_layouts, layout_parameters, verbose)
    else:
        for _layer, network in networks.items():
            compute_layout(network, compute_layouts, layout_parameters, verbose)

    if verbose:
        logger.info("Finished with layout..")
    inverse_mapping = {}

    # construct the inverse mapping
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = k

    multiedges = defaultdict(list)
    for edge in multinet.edges(data=True):
        try:
            if edge[0][1] != edge[1][1]:
                multiedges[edge[2]["type"]].append(edge)
        except Exception:
            multiedges["default_inter"].append(edge)
            pass

    names_list: List[Any] = list(networks.keys())
    networks_list: List[nx.Graph] = list(networks.values())
    return (names_list, networks_list, multiedges)


def prepare_for_visualization_hairball(multinet, compute_layouts=False):
    """
    Compute layout for a hairball visualization

    Args:
        param1 (obj): multilayer object

    Returns:
        tuple: (names, prepared network)

    """

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])
        except (IndexError, TypeError, KeyError):
            # Node format doesn't match expected multilayer format
            layers[1].append(node)

    inverse_mapping = {}
    enumerated_layers = {name: ind for ind, name in enumerate(set(layers.keys()))}
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = enumerated_layers[k]
    ordered_names = [inverse_mapping[x] for x in multinet.nodes()]
    [x[1] for x in multinet.nodes()]
    return (ordered_names, multinet)


def prepare_for_parsing(multinet):
    """
    Compute layout for a hairball visualization

    Args:
        param1 (obj): multilayer object

    Returns:
        tuple: (names, prepared network)

    """

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])
        except Exception as err:
            logger.debug("Layer parsing error: %s", err)

    networks = {layer_name: multinet.subgraph(v) for layer_name, v in layers.items()}

    inverse_mapping = {}

    # construct the inverse mapping
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = k

    multiedges = defaultdict(list)
    for edge in multinet.edges(data=True):
        try:
            if edge[0][1] != edge[1][1]:
                multiedges[edge[2]["type"]].append(edge)
        except Exception as err:
            multiedges["default_inter"].append(edge)
            logger.debug("Multiedge parsing error: %s", err)

    # Handle empty networks gracefully
    if networks:
        names, networks = zip(*networks.items())
    else:
        names, networks = (), ()
    return (names, networks, multiedges)
