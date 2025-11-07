# node ranking algorithms
from itertools import product
from typing import Any, List, Tuple, Union, cast

import networkx as nx
import numpy as np
import scipy.sparse as sp

# from networkx.algorithms.community.community_utils import is_partition

# def stochastic_normalization(matrix):
#     try:
#         matrix.setdiag(0)
#     except TypeError:
#         matrix.setdiag(np.zeros(matrix.shape[0]))
#     d[nzs] = 1 / d[nzs]
#     return matrix


def stochastic_normalization(matrix: sp.spmatrix) -> sp.spmatrix:
    """Normalize a sparse matrix stochastically.

    Args:
        matrix: Sparse matrix to normalize

    Returns:
        Stochastically normalized sparse matrix
    """
    matrix = matrix.tolil()
    try:
        matrix.setdiag(0)
    except TypeError:
        matrix.setdiag(np.zeros(matrix.shape[0]))
    matrix = matrix.tocsr()
    d = matrix.sum(axis=1).getA1()
    nzs = np.where(d > 0)
    k = 1 / d[nzs]
    matrix = (sp.diags(k, 0).tocsc().dot(matrix)).transpose()
    return matrix


def stochastic_normalization_hin(matrix: sp.spmatrix) -> sp.spmatrix:
    """Normalize a heterogeneous information network matrix stochastically.

    Args:
        matrix: Sparse matrix to normalize

    Returns:
        Stochastically normalized sparse matrix
    """
    matrix = matrix.tolil()
    try:
        matrix.setdiag(0)
    except TypeError:
        matrix.setdiag(np.zeros(matrix.shape[0]))
    matrix = matrix.tocsr()
    d = matrix.sum(axis=1).getA1()
    nzs = np.where(d > 0)
    d[nzs] = 1 / d[nzs]
    matrix = (sp.diags(d, 0).tocsc().dot(matrix)).transpose()
    return matrix


def modularity(
    G: nx.Graph, communities: List[List[Any]], weight: str = "weight"
) -> float:
    """Calculate modularity of a graph partition.

    Args:
        G: NetworkX graph
        communities: List of communities (each community is a list of nodes)
        weight: Edge weight attribute name

    Returns:
        Modularity value
    """
    multigraph = G.is_multigraph()
    directed = G.is_directed()
    m = G.size(weight=weight)
    if directed:
        out_degree = dict(G.out_degree(weight=weight))
        in_degree = dict(G.in_degree(weight=weight))
        norm = 1 / m
    else:
        out_degree = dict(G.degree(weight=weight))
        in_degree = out_degree
        norm = 1 / (2 * m)

    def val(u, v):
        try:
            if multigraph:
                w = sum(d.get(weight, 1) for k, d in G[u][v].items())
            else:
                w = G[u][v].get(weight, 1)
        except KeyError:
            w = 0
        # Double count self-loops if the graph is undirected.
        if u == v and not directed:
            w *= 2
        return w - in_degree[u] * out_degree[v] * norm

    Q = sum(val(u, v) for c in communities for u, v in product(c, repeat=2))
    return Q * norm


def page_rank_kernel(index_row: int) -> Tuple[int, np.ndarray]:
    """PageRank kernel for parallel computation.

    Note: This function expects global variables G, damping_hyper,
    spread_step_hyper, spread_percent_hyper, and graph to be defined.
    It's designed for use with multiprocessing.Pool.map().

    Args:
        index_row: Row index to compute PageRank for

    Returns:
        Tuple of (index, PageRank vector)
    """

    # call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(
        G,  # type: ignore[name-defined]
        [index_row],
        epsilon=1e-6,
        max_steps=100000,
        damping=damping_hyper,  # type: ignore[name-defined]
        spread_step=spread_step_hyper,  # type: ignore[name-defined]
        spread_percent=spread_percent_hyper,  # type: ignore[name-defined]
        try_shrink=True,
    )

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(graph.shape[1]))  # type: ignore[name-defined]


def sparse_page_rank(
    matrix: sp.spmatrix,
    start_nodes: Union[List[int], range, None],
    epsilon: float = 1e-6,
    max_steps: int = 100000,
    damping: float = 0.5,
    spread_step: int = 10,
    spread_percent: float = 0.3,
    try_shrink: bool = False,
) -> np.ndarray:
    """Compute sparse PageRank with personalization.

    Args:
        matrix: Sparse adjacency matrix (column-stochastic)
        start_nodes: List of starting node indices for personalization (can be range or None)
        epsilon: Convergence threshold
        max_steps: Maximum number of iterations
        damping: Damping factor (teleportation probability)
        spread_step: Maximum steps for spread calculation
        spread_percent: Percentage threshold for spread
        try_shrink: Whether to try matrix shrinking optimization

    Returns:
        PageRank vector
    """

    assert start_nodes is None or (len(start_nodes)) > 0

    # this method assumes that column sums are all equal to 1 (stochastic normalizaition!)
    size = matrix.shape[0]
    if start_nodes is None:
        start_nodes = range(size)
        nz = size
    else:
        nz = len(start_nodes)
    start_vec = np.zeros((size, 1))
    start_vec[start_nodes] = 1
    start_rank = start_vec / len(start_nodes)
    rank_vec = start_vec / len(start_nodes)

    # calculate the max spread:
    shrink = False
    which = np.zeros(0)
    if try_shrink:
        v = start_vec / len(start_nodes)
        steps = 0
        while nz < size * spread_percent and steps < spread_step:
            steps += 1
            v += matrix.dot(v)
            nz_new = np.count_nonzero(v)
            if nz_new == nz:
                shrink = True
                break
            nz = nz_new
        rr = np.arange(matrix.shape[0])
        which = (v[rr] > 0).reshape(size)
        if shrink:
            start_rank = start_rank[which]
            rank_vec = rank_vec[which]
            matrix = matrix[:, which][which, :]
    diff: Union[float, Any] = np.inf
    steps = 0
    while diff > epsilon and steps < max_steps:  # not converged yet
        steps += 1
        new_rank = matrix.dot(rank_vec)
        rank_sum: float = np.sum(new_rank)
        if rank_sum < 0.999999999:
            new_rank += start_rank * (1 - rank_sum)
        new_rank = damping * new_rank + (1 - damping) * start_rank
        new_diff = np.linalg.norm(rank_vec - new_rank, 1)
        diff = new_diff
        rank_vec = new_rank
    if try_shrink and shrink:
        ret = np.zeros(size)
        rank_vec = rank_vec.T[0]  # this works for both python versions
        ret[which] = rank_vec
        ret[start_nodes] = 0
        return cast(np.ndarray, ret.flatten())
    else:
        rank_vec[start_nodes] = 0
        return cast(np.ndarray, rank_vec.flatten())


def hubs_and_authorities(graph: nx.Graph) -> Tuple[dict, dict]:
    """Compute hubs and authorities scores using HITS algorithm.

    Args:
        graph: NetworkX graph

    Returns:
        Tuple of (hubs dictionary, authorities dictionary)
    """
    return nx.hits_scipy(graph)  # type: ignore[no-any-return]


def hub_matrix(graph: nx.Graph) -> sp.spmatrix:
    """Get the hub matrix of a graph.

    Args:
        graph: NetworkX graph

    Returns:
        Hub matrix
    """
    return nx.hub_matrix(graph)


def authority_matrix(graph: nx.Graph) -> sp.spmatrix:
    """Get the authority matrix of a graph.

    Args:
        graph: NetworkX graph

    Returns:
        Authority matrix
    """
    return nx.authority_matrix(graph)
