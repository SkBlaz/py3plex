# node ranking algorithms
from itertools import product
from typing import Any, List

import networkx as nx
import numpy as np
import scipy.sparse as sp

from py3plex.algorithms.node_ranking import (
    authority_matrix,
    hubs_and_authorities,
    hub_matrix,
    sparse_page_rank,
    stochastic_normalization,
)

# from networkx.algorithms.community.community_utils import is_partition

# def stochastic_normalization(matrix):
#     try:
#         matrix.setdiag(0)
#     except TypeError:
#         matrix.setdiag(np.zeros(matrix.shape[0]))
#     d[nzs] = 1 / d[nzs]
#     return matrix


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


__all__ = [
    "stochastic_normalization",
    "stochastic_normalization_hin",
    "modularity",
    "sparse_page_rank",
    "hubs_and_authorities",
    "hub_matrix",
    "authority_matrix",
]
