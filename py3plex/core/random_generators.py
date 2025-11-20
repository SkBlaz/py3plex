# a class for random graph generation
import random
from typing import Any

import networkx as nx
import numpy as np

from .multinet import itertools, multi_layer_network

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


@require(lambda n: n > 0, "number of nodes must be positive")
@require(lambda l: l > 0, "number of layers must be positive")
@require(lambda p: 0 <= p <= 1, "probability must be in [0, 1]")
@ensure(lambda result: result is not None, "result must not be None")
def random_multilayer_ER(
    n: int, l: int, p: float, directed: bool = False
) -> Any:  # Returns multi_layer_network
    """
    Generate random multilayer Erdős-Rényi network.

    Args:
        n: Number of nodes (must be positive)
        l: Number of layers (must be positive)
        p: Edge probability in [0, 1]
        directed: If True, generate directed network

    Returns:
        multi_layer_network object

    Contracts:
        - Precondition: n > 0 - must have at least one node
        - Precondition: l > 0 - must have at least one layer
        - Precondition: 0 <= p <= 1 - probability must be valid
        - Postcondition: result is not None - must return valid network
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    network = nx.gnp_random_graph(n, p, seed=None, directed=directed)

    # Ensure all layers have at least one node
    # First, assign one node to each layer
    if n >= l:
        # If we have enough nodes, assign first l nodes to layers 0..l-1
        layers = dict()
        for i in range(l):
            layers[i] = i
        # Then randomly assign remaining nodes
        for i in range(l, n):
            layers[i] = np.random.randint(l)
    else:
        # If n < l, just assign nodes to first n layers
        layers = dict(zip(range(n), range(n)))

    # Add all nodes first (including isolated ones)
    for node in network.nodes():
        G.add_node((node, layers[node]), type="default")

    # Then add edges
    for edge in network.edges():
        G.add_edge(
            (edge[0], layers[edge[0]]), (edge[1], layers[edge[1]]), type="default"
        )

    # construct the ppx object
    no = multi_layer_network(network_type="multilayer").load_network(
        G, input_type="nx", directed=directed
    )
    return no


@require(lambda n: n > 0, "number of nodes must be positive")
@require(lambda l: l > 0, "number of layers must be positive")
@require(lambda p: 0 <= p <= 1, "probability must be in [0, 1]")
@ensure(lambda result: result is not None, "result must not be None")
def random_multiplex_ER(
    n: int, l: int, p: float, directed: bool = False
) -> Any:  # Returns multi_layer_network
    """
    Generate random multiplex Erdős-Rényi network.

    Args:
        n: Number of nodes (must be positive)
        l: Number of layers (must be positive)
        p: Edge probability in [0, 1]
        directed: If True, generate directed network

    Returns:
        multi_layer_network object

    Contracts:
        - Precondition: n > 0 - must have at least one node
        - Precondition: l > 0 - must have at least one layer
        - Precondition: 0 <= p <= 1 - probability must be valid
        - Postcondition: result is not None - must return valid network
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for lx in range(l):
        network = nx.fast_gnp_random_graph(n, p, seed=None, directed=directed)
        for edge in network.edges():
            G.add_edge((edge[0], lx), (edge[1], lx), type="default")

    # construct the ppx object
    no = multi_layer_network(network_type="multiplex").load_network(
        G, input_type="nx", directed=directed
    )
    return no


@require(lambda n: n > 0, "number of nodes must be positive")
@require(lambda m: m > 0, "number of layers must be positive")
@require(lambda d: 0 <= d <= 1, "dropout parameter must be in [0, 1]")
@ensure(lambda result: result is not None, "result must not be None")
@ensure(
    lambda result: isinstance(result, nx.MultiGraph),
    "result must be a NetworkX MultiGraph",
)
def random_multiplex_generator(n: int, m: int, d: float = 0.9) -> nx.MultiGraph:
    """
    Generate a multiplex network from a random bipartite graph.

    Args:
        n: Number of nodes (must be positive)
        m: Number of layers (must be positive)
        d: Layer dropout to avoid cliques, range [0..1] (default: 0.9)

    Returns:
        Generated multiplex network as a MultiGraph

    Contracts:
        - Precondition: n > 0 - must have at least one node
        - Precondition: m > 0 - must have at least one layer
        - Precondition: 0 <= d <= 1 - dropout must be valid probability
        - Postcondition: result is not None
        - Postcondition: result is a NetworkX MultiGraph
    """

    layers = range(m)
    node_to_layers = {}
    layer_to_nodes: dict = {}
    G = nx.MultiGraph()
    for node in range(n):
        layer_list = random.sample(layers, random.choice(layers))
        node_to_layers[node] = layer_list
        for l in layer_list:
            layer_to_nodes[l] = layer_to_nodes.get(l, []) + [node]

    edge_to_layers: dict = {}
    for l, nlist in layer_to_nodes.items():
        clique = tuple(itertools.combinations(nlist, 2))
        nnodes = len(nlist)
        edge_sample = random.sample(clique, int(d * (nnodes * (nnodes - 1)) / 2))
        for p1, p2 in edge_sample:
            if p1 < p2:
                e = (p1, p2)
            else:
                e = (p2, p1)

            edge_to_layers[e] = edge_to_layers.get(e, []) + [l]

    for k, v in edge_to_layers.items():
        for l in v:
            G.add_edge((k[0], l), (k[1], l), type="default", weight=1)

    return G
