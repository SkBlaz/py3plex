## node ranking algorithms
import numpy as np
import networkx as nx
import scipy.sparse as sp
#from networkx.algorithms.community.community_utils import is_partition
from itertools import product

# def stochastic_normalization(matrix):
#     matrix = matrix.tolil()
#     try:
#         matrix.setdiag(0)
#     except TypeError:
#         matrix.setdiag(np.zeros(matrix.shape[0]))
#     matrix = matrix.tocsr()
#     d = matrix.sum(axis=1).getA1()
#     nzs = np.where(d > 0)
#     d[nzs] = 1 / d[nzs]
#     matrix = (sp.diags(d, 0).tocsc().dot(matrix)).transpose()
#     return matrix


def stochastic_normalization(matrix):
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


def stochastic_normalization_hin(matrix):
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


def modularity(G, communities, weight='weight'):

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

    Q = np.sum(val(u, v) for c in communities for u, v in product(c, repeat=2))
    return Q * norm


def page_rank_kernel(index_row):

    ## call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(G, [index_row],
                          epsilon=1e-6,
                          max_steps=100000,
                          damping=damping_hyper,
                          spread_step=spread_step_hyper,
                          spread_percent=spread_percent_hyper,
                          try_shrink=True)

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(graph.shape[1]))


def sparse_page_rank(matrix,
                     start_nodes,
                     epsilon=1e-6,
                     max_steps=100000,
                     damping=0.5,
                     spread_step=10,
                     spread_percent=0.3,
                     try_shrink=False):

    assert (len(start_nodes)) > 0

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
    diff = np.Inf
    steps = 0
    while diff > epsilon and steps < max_steps:  # not converged yet
        steps += 1
        new_rank = matrix.dot(rank_vec)
        rank_sum = np.sum(new_rank)
        if rank_sum < 0.999999999:
            new_rank += start_rank * (1 - rank_sum)
        new_rank = damping * new_rank + (1 - damping) * start_rank
        new_diff = np.linalg.norm(rank_vec - new_rank, 1)
        diff = new_diff
        rank_vec = new_rank
    if try_shrink and shrink:
        ret = np.zeros(size)
        rank_vec = rank_vec.T[0]  ## this works for both python versions
        ret[which] = rank_vec
        ret[start_nodes] = 0
        return ret.flatten()
    else:
        rank_vec[start_nodes] = 0
        return rank_vec.flatten()


def hubs_and_authorities(graph):
    return nx.hits_scipy(graph)


def hub_matrix(graph):
    return nx.hub_matrix(graph)


def authority_matrix(graph):
    return nx.authority_matrix(graph)
