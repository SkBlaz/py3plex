"""
Supporting methods for parsers and converters.

This module provides utility functions for network parsing and conversion,
including layer splitting, multiplex edge addition, and GAF parsing.
"""

import itertools
import operator
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

import networkx as nx

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


@require(
    lambda input_network: input_network is not None, "input_network must not be None"
)
@require(
    lambda input_network: isinstance(
        input_network, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
    ),
    "input_network must be a NetworkX graph",
)
@ensure(lambda result: isinstance(result, dict), "result must be a dictionary")
@ensure(
    lambda result: all(
        isinstance(v, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))
        for v in result.values()
    ),
    "all values in result must be NetworkX graphs",
)
def split_to_layers(input_network: nx.Graph) -> Dict[Any, nx.Graph]:
    """
    Split a multilayer network into separate layer subgraphs.

    Args:
        input_network: NetworkX graph containing nodes from multiple layers.

    Returns:
        Dictionary mapping layer names to their corresponding subgraphs.

    Contracts:
        - Precondition: input_network must not be None
        - Precondition: input_network must be a NetworkX graph
        - Postcondition: result is a dictionary
        - Postcondition: all values are NetworkX graphs

    Example:
        >>> network = nx.Graph()
        >>> network.add_node(('A', 'layer1'))
        >>> network.add_node(('B', 'layer2'))
        >>> layers = split_to_layers(network)
    """
    layer_info = defaultdict(list)
    subgraph_dictionary = {}

    for node in input_network.nodes(data=True):
        try:
            layer_info[node[0][1]].append(node[0])
        except Exception:
            layer_info[node[1]["type"]].append(node[0])

    for layer, nodes in layer_info.items():
        subnetwork = input_network.subgraph(nodes)
        subgraph_dictionary[layer] = subnetwork  # nx.relabel_nodes(subnetwork,mapping)
    del layer_info

    return subgraph_dictionary


@require(
    lambda input_network: input_network is not None, "input_network must not be None"
)
@require(
    lambda input_network: isinstance(
        input_network, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
    ),
    "input_network must be a NetworkX graph",
)
@ensure(
    lambda result: isinstance(
        result, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
    ),
    "result must be a NetworkX graph",
)
def add_mpx_edges(input_network: nx.Graph) -> nx.Graph:
    """
    Add multiplex edges between corresponding nodes across layers.

    Multiplex edges connect nodes representing the same entity across
    different layers of a multilayer network.

    Args:
        input_network: NetworkX graph with multilayer structure.

    Returns:
        Network with added multiplex edges between corresponding nodes.

    Contracts:
        - Precondition: input_network must not be None
        - Precondition: input_network must be a NetworkX graph
        - Postcondition: result is a NetworkX graph

    Example:
        >>> network = nx.Graph()
        >>> network.add_node(('A', 'layer1'))
        >>> network.add_node(('A', 'layer2'))
        >>> network = add_mpx_edges(network)
    """
    _layerwise_nodes = split_to_layers(input_network)

    min_node_layer = {}
    for layer, network in _layerwise_nodes.items():
        min_node_layer[layer] = {n[0][0] for n in network.nodes(data=True)}

    for pair in itertools.combinations(list(min_node_layer.keys()), 2):
        layer_first = pair[0]
        layer_second = pair[1]
        pair_intersection = set.intersection(
            min_node_layer[layer_first], min_node_layer[layer_second]
        )

        for node in pair_intersection:
            n1 = (node, layer_first)
            n2 = (node, layer_second)
            input_network.add_edge(n1, n2, key="mpx", type="coupling")

    return input_network


def parse_gaf_to_uniprot_GO(
    gaf_mappings: str, filter_terms: Optional[int] = None
) -> Dict[str, List[str]]:
    """
    Parse Gene Association File (GAF) to map UniProt IDs to GO terms.

    Args:
        gaf_mappings: Path to GAF file.
        filter_terms: Optional minimum occurrence threshold for GO terms.

    Returns:
        Dictionary mapping UniProt IDs to lists of associated GO terms.

    Example:
        >>> mappings = parse_gaf_to_uniprot_GO("gaf_file.gaf", filter_terms=5)  # doctest: +SKIP
    """
    uniGO = defaultdict(list)
    with open(gaf_mappings) as im:
        for line in im:
            parts = line.split("\t")
            try:
                if "GO:" in parts[4]:
                    uniGO[parts[1]].append(parts[4])  # GO and ref both added
                if "GO:" in parts[3]:
                    uniGO[parts[1]].append(parts[3])
            except (IndexError, KeyError):
                # Skip malformed lines with missing fields
                continue

    all_terms = list(itertools.chain(*uniGO.values()))
    if filter_terms is not None:
        sorted_d = sorted(
            Counter(all_terms).items(), key=operator.itemgetter(1), reverse=True
        )
        top_100 = [x[0] for x in sorted_d[0:filter_terms]]
        new_map = defaultdict(list)
        for k, v in uniGO.items():
            v = [x for x in v if x in top_100]
            new_map[k] = v
        return new_map

    else:
        return uniGO
