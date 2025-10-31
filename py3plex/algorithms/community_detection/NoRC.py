"""
Node Ranking and Clustering (NoRC) module for community detection.

This module implements algorithms for node ranking and hierarchical clustering
in networks, including parallel PageRank computation and hierarchical merging.
"""

import multiprocessing as mp
from collections import defaultdict

import networkx as nx
import numpy as np
import scipy.sparse as sp
import tqdm
from numpy.lib.stride_tricks import as_strided
from scipy.cluster.hierarchy import fcluster

# import community
from sklearn.cluster import MiniBatchKMeans

from py3plex.core.nx_compat import nx_info, nx_to_scipy_sparse_matrix
from py3plex.algorithms.node_ranking.node_ranking import (
    modularity,
    sparse_page_rank,
    stochastic_normalization,
)
from .clustering_utils import create_tree

global _RANK_GRAPH


def page_rank_kernel(index_row):

    # call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(
        _RANK_GRAPH,
        [index_row],
        epsilon=1e-6,
        max_steps=100000,
        damping=0.90,
        spread_step=10,
        spread_percent=0.1,
        try_shrink=True,
    )

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(_RANK_GRAPH.shape[1]))


def sum(X, v):
    rows, cols = X.shape
    row_start_stop = as_strided(X.indptr, shape=(rows, 2), strides=2 * X.indptr.strides)
    for row, (start, stop) in enumerate(row_start_stop):
        data = X.data[start:stop]
        data -= v[row]


def NoRC_communities_main(
    input_graph,
    clustering_scheme="hierarchical",
    max_com_num=100,
    verbose=False,
    sparisfy=True,
    parallel_step=6,
    prob_threshold=0.0005,
    community_range=None,
    fine_range=3,
    lag_threshold=10,
):
    if community_range is None:
        community_range = [1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300]
    if verbose:
        print("Walking..")
    global _RANK_GRAPH
    _RANK_GRAPH = input_graph
    A = _RANK_GRAPH.copy()
    _RANK_GRAPH = nx_to_scipy_sparse_matrix(_RANK_GRAPH)
    _RANK_GRAPH = stochastic_normalization(_RANK_GRAPH)  # normalize
    n = _RANK_GRAPH.shape[1]
    edgelist_triplets = []
    jobs = [range(n)[i : i + parallel_step] for i in range(0, n, parallel_step)]
    with mp.Pool(processes=parallel_step) as p:
        for batch in tqdm.tqdm(jobs):
            results = p.map(page_rank_kernel, batch)
            for nid, result_vector in results:
                cols = np.argwhere(result_vector > prob_threshold).flatten().astype(int)
                vals = result_vector[cols].flatten()
                ixx = np.repeat(nid, cols.shape[0]).flatten().astype(int)
                arx = np.vstack((ixx, cols, vals)).T
                edgelist_triplets.append(arx)
    sparse_edgelist = np.concatenate(edgelist_triplets, axis=0)
    print(
        f"Compressed to {(sparse_edgelist.shape[0] * 100) / n**2}% of the initial size"
    )
    vectors = sp.coo_matrix(
        (
            sparse_edgelist[:, 2],
            (sparse_edgelist[:, 0].astype(int), sparse_edgelist[:, 1].astype(int)),
        )
    ).tocsr()
    mx_opt = 0
    if clustering_scheme == "kmeans":
        if verbose:
            print("Doing kmeans search")
        nopt = 0
        lag_num = 0
        for nclust in tqdm.tqdm(community_range):
            dx_hc = defaultdict(list)
            clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
            clusters = clustering_algorithm.fit_predict(vectors)
            for a, b in zip(clusters, A.nodes()):
                dx_hc[a].append(b)
            partitions = dx_hc.values()
            mx = modularity(A, partitions, weight="weight")
            if mx > mx_opt:
                lag_num = 0
                if verbose:
                    print(
                        f"Improved modularity: {mx}, found {len(partitions)} communities."
                    )
                mx_opt = mx
                opt_clust = dx_hc
                nopt = nclust
                if mx == 1:
                    nopt = nclust
                    return opt_clust
            else:
                lag_num += 1
                if verbose:
                    print(f"No improvement for {lag_num} iterations.")

                if lag_num > lag_threshold:
                    break

        # fine grained search
        if verbose:
            print(f"Fine graining around {nopt}")
        for nclust in range(nopt - fine_range, nopt + fine_range, 1):
            if nclust != nopt:
                dx_hc = defaultdict(list)
                clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
                clusters = clustering_algorithm.fit_predict(vectors)
                for a, b in zip(clusters, A.nodes()):
                    dx_hc[a].append(b)
                partitions = dx_hc.values()
                mx = modularity(A, partitions, weight="weight")
                if mx > mx_opt:
                    if verbose:
                        print(
                            f"Improved modularity: {mx}, found {len(partitions)} communities."
                        )
                    mx_opt = mx
                    opt_clust = dx_hc
                    if mx == 1:
                        nopt = nclust
                        return opt_clust

        return opt_clust

    if clustering_scheme == "hierarchical":

        Z = linkage(vectors.todense(), "average")
        mod_hc_opt = 0
        for nclust in tqdm.tqdm(community_range):
            dx_hc = defaultdict(list)
            try:
                cls = fcluster(Z, nclust, criterion="maxclust")
                for a, b in zip(cls, A.nodes()):
                    dx_hc[a].append(b)
                partition_hi = dx_hc.values()
                mod = modularity(A, partition_hi, weight="weight")
                if mod > mod_hc_opt:
                    if verbose:
                        print(
                            f"\nImproved modularity: {mod}, communities: {len(partition_hi)}"
                        )

                    mod_hc_opt = mod
                    opt_clust = dx_hc
                    if mod == 1:
                        return opt_clust
            except Exception as es:
                print(es)
        return opt_clust


if __name__ == "__main__":

    # n = 50
    # tau1 = 4
    # tau2 = 1.5
    # mu = 0.1
    # graph = LFR_benchmark_graph(n,
    #                             tau1,
    #                             tau2,
    #                             mu,
    #                             average_degree=5,
    #                             min_community=30,
    #                             seed=10)

    graph = nx.powerlaw_cluster_graph(1000, 5, 0.1)
    print(nx_info(graph))
    communities1 = NoRC_communities_main(
        graph, verbose=True, clustering_scheme="kmeans"
    )
    communities1 = NoRC_communities_main(
        graph, verbose=True, clustering_scheme="hierarchical"
    )
