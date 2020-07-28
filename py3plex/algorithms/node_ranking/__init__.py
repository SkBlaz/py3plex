## node ranking algorithms
import numpy as np
import networkx as nx
import scipy.sparse as sp
import multiprocessing as mp
from itertools import product


def stochastic_normalization(matrix):
    matrix = matrix.tolil()

    try:
        matrix.setdiag(0)
    except TypeError:
        matrix.setdiag(np.zeros(matrix.shape[0]))

    matrix = matrix.tocsr()
    d = matrix.sum(axis=1).getA1()
    nzs = np.where(d > 0)
    k = np.zeros(matrix.shape[1])
    nz = 1 / d[nzs]
    k[nzs] = nz
    a = sp.diags(k, 0).tocsc()
    matrix = (sp.diags(k, 0).tocsc().dot(matrix)).transpose()
    return matrix


def page_rank_kernel(index_row):

    ## call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(__graph_matrix, [index_row],
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
        return (index_row, np.zeros(__graph_matrix.shape[1]))


def sparse_page_rank(matrix,
                     start_nodes,
                     epsilon=1e-6,
                     max_steps=100000,
                     damping=0.5,
                     spread_step=10,
                     spread_percent=0.3,
                     try_shrink=True):

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


def run_PPR(network,
            cores=None,
            jobs=None,
            damping=0.85,
            spread_step=10,
            spread_percent=0.3,
            targets=None,
            parallel=True):

    ## normalize the matrix

    network = stochastic_normalization(network)
    global __graph_matrix
    global damping_hyper
    global spread_step_hyper
    global spread_percent_hyper

    damping_hyper = damping
    spread_step_hyper = spread_step
    spread_percent_hyper = spread_percent

    __graph_matrix = network
    if cores is None:
        cores = mp.cpu_count()

    n = network.shape[1]
    step = cores

    if jobs is None:
        if targets is None:
            jobs = [range(n)[i:i + step]
                    for i in range(0, n, step)]  ## generate jobs
        else:
            jobs = [range(n)[i:i + step] for i in targets]  ## generate jobs

    if parallel == False:
        for target in jobs:
            for x in target:
                vector = page_rank_kernel(x)
                yield vector
    else:
        with mp.Pool(processes=cores) as p:
            for batch in jobs:
                results = p.map(page_rank_kernel, batch)
                yield results


def hubs_and_authorities(graph):
    return nx.hits_scipy(graph)


def hub_matrix(graph):
    return nx.hub_matrix(graph)


def authority_matrix(graph):
    return nx.authority_matrix(graph)
