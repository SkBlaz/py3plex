# a class for random graph generation
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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


@dataclass
class SBMMetadata:
    """Ground-truth information for a multilayer SBM sample.

    Attributes
    ----------
    block_memberships : np.ndarray
        Array of shape (n_nodes,) with integer block labels in {0, ..., n_blocks-1}.
        Shared across layers in this simple multiplex model.

    block_matrix : np.ndarray
        Array of shape (n_blocks, n_blocks) with edge probabilities p_ab.
        Same for all layers in this simple model.

    node_ids : List[str]
        Node identifiers used in the resulting multi_layer_network (e.g. "v0", "v1", ...).

    layer_names : List[str]
        Names of the layers used in the multi_layer_network (e.g. "L0", "L1", ...).
    """

    block_memberships: np.ndarray
    block_matrix: np.ndarray
    node_ids: List[str]
    layer_names: List[str]


def _sample_sbm_adjacency(
    block_memberships: np.ndarray,
    block_matrix: np.ndarray,
    directed: bool,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample an adjacency matrix for a single layer according to a stochastic block model.

    Parameters
    ----------
    block_memberships : np.ndarray
        Shape (n_nodes,), integer block labels in {0, ..., n_blocks-1}.
    block_matrix : np.ndarray
        Shape (n_blocks, n_blocks), probabilities in [0, 1].
    directed : bool
        If False, generate an undirected graph (symmetric adjacency, no self-loops).
        If True, generate a directed graph (i -> j) independently of (j -> i).
    rng : np.random.Generator
        Random number generator instance.

    Returns
    -------
    adj : np.ndarray
        Binary adjacency matrix of shape (n_nodes, n_nodes) with entries 0 or 1.
    """
    n_nodes = block_memberships.shape[0]
    n_blocks = block_matrix.shape[0]

    # adjacency as dense 0/1 matrix
    adj = np.zeros((n_nodes, n_nodes), dtype=np.int8)

    # nodes_in_block[b] = indices of nodes in block b
    nodes_in_block: List[np.ndarray] = []
    for b in range(n_blocks):
        nodes = np.where(block_memberships == b)[0]
        nodes_in_block.append(nodes)

    # iterate over block pairs
    for a in range(n_blocks):
        idx_a = nodes_in_block[a]
        if idx_a.size == 0:
            continue

        # if undirected, only handle upper-triangular in block-index space to avoid double work
        start_b = 0 if directed else a
        for b in range(start_b, n_blocks):
            idx_b = nodes_in_block[b]
            if idx_b.size == 0:
                continue

            p = float(block_matrix[a, b])
            if p <= 0.0:
                continue

            if not directed and a == b:
                # intra-block, undirected: only sample upper triangle
                k = idx_a.size
                if k <= 1:
                    continue
                triu_rows, triu_cols = np.triu_indices(k, k=1)
                m = triu_rows.shape[0]
                if m == 0:
                    continue

                bern = rng.random(m) < p
                if not np.any(bern):
                    continue

                src = idx_a[triu_rows[bern]]
                dst = idx_a[triu_cols[bern]]
                adj[src, dst] = 1
                adj[dst, src] = 1
            else:
                # bipartite or directed case
                k_a = idx_a.size
                k_b = idx_b.size
                if k_a == 0 or k_b == 0:
                    continue

                bern = rng.random((k_a, k_b)) < p
                if not np.any(bern):
                    continue

                rows, cols = np.where(bern)
                src = idx_a[rows]
                dst = idx_b[cols]
                adj[src, dst] = 1

                if (not directed) and (a != b):
                    # mirror for undirected, distinct blocks
                    adj[dst, src] = 1

    # remove self-loops
    np.fill_diagonal(adj, 0)
    return adj


def random_multilayer_SBM(
    n_layers: int,
    n_nodes: int,
    n_blocks: int,
    p_in: float,
    p_out: float,
    coupling: float = 0.0,
    directed: bool = False,
    seed: Optional[int] = None,
) -> Tuple[multi_layer_network, SBMMetadata]:
    """Generate a simple multiplex multilayer stochastic block model (SBM) network.

    This function creates a multilayer network with:
    - `n_nodes` nodes shared across all layers,
    - `n_layers` layers,
    - `n_blocks` latent communities (blocks),
    - within-block edge probability `p_in`,
    - between-block edge probability `p_out`,
    - optional diagonal inter-layer coupling with probability `coupling`
      between replicas of the same node across layers.

    The block memberships are shared across layers in this simple model,
    and the same block probability matrix is used for all layers.

    Parameters
    ----------
    n_layers : int
        Number of layers.
    n_nodes : int
        Number of nodes (shared across all layers).
    n_blocks : int
        Number of blocks (communities).
    p_in : float
        Edge probability for edges within the same block.
    p_out : float
        Edge probability for edges between different blocks.
    coupling : float, optional
        Probability of inter-layer edges between replicas of the same node
        in different layers. Defaults to 0.0 (no inter-layer edges).
    directed : bool, optional
        Whether to generate directed layers. Defaults to False.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    network : multi_layer_network
        The generated multilayer network.
    metadata : SBMMetadata
        Ground-truth metadata containing block memberships and block matrix.

    Notes
    -----
    - Node IDs are strings "v0", "v1", ..., "v{n_nodes-1}".
    - Layer names are strings "L0", "L1", ..., "L{n_layers-1}".
    - Edges are inserted via the py3plex list-based API:
      [src_node, src_layer, dst_node, dst_layer, weight].

    Examples
    --------
    >>> from py3plex.core.random_generators import random_multilayer_SBM
    >>> net, meta = random_multilayer_SBM(
    ...     n_layers=3, n_nodes=20, n_blocks=2,
    ...     p_in=0.5, p_out=0.05, coupling=0.1, seed=42
    ... )
    >>> print(len(meta.block_memberships))
    20
    >>> print(len(meta.layer_names))
    3
    """
    rng = np.random.default_rng(seed)

    # validate inputs
    if n_layers <= 0:
        raise ValueError("n_layers must be positive")
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if n_blocks <= 0 or n_blocks > n_nodes:
        raise ValueError("n_blocks must be in [1, n_nodes]")
    if not (0.0 <= p_in <= 1.0 and 0.0 <= p_out <= 1.0):
        raise ValueError("p_in and p_out must be within [0, 1]")
    if not (0.0 <= coupling <= 1.0):
        raise ValueError("coupling must be within [0, 1]")

    # node IDs and layers
    node_ids: List[str] = [f"v{i}" for i in range(n_nodes)]
    layer_names: List[str] = [f"L{i}" for i in range(n_layers)]

    # block memberships: assign nodes uniformly at random to blocks
    block_memberships = rng.integers(low=0, high=n_blocks, size=n_nodes)

    # block probability matrix: p_in on diagonal, p_out off-diagonal
    block_matrix = np.full((n_blocks, n_blocks), p_out, dtype=float)
    np.fill_diagonal(block_matrix, p_in)

    # create the multilayer network
    mnet = multi_layer_network(directed=directed, verbose=False)

    # collect edges
    all_edges: List[List[Any]] = []

    # intra-layer edges
    for layer_name in layer_names:
        adj = _sample_sbm_adjacency(
            block_memberships=block_memberships,
            block_matrix=block_matrix,
            directed=directed,
            rng=rng,
        )

        src_idx, dst_idx = np.where(adj)
        for i, j in zip(src_idx, dst_idx):
            if directed or i < j:  # avoid duplicates for undirected
                edge = [node_ids[i], layer_name, node_ids[j], layer_name, 1]
                all_edges.append(edge)

    # inter-layer coupling edges
    if coupling > 0.0:
        for node_idx, node_id in enumerate(node_ids):
            for i, layer_i in enumerate(layer_names):
                for j, layer_j in enumerate(layer_names):
                    if i < j:  # only one direction per pair
                        if rng.random() < coupling:
                            edge = [node_id, layer_i, node_id, layer_j, 1]
                            all_edges.append(edge)

    # add edges to network
    if all_edges:
        mnet.add_edges(all_edges, input_type="list")

    # create metadata
    metadata = SBMMetadata(
        block_memberships=block_memberships,
        block_matrix=block_matrix,
        node_ids=node_ids,
        layer_names=layer_names,
    )

    return mnet, metadata


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
