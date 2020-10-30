# ncd

import networkx as nx
import numpy as np
import tqdm
import multiprocessing as mp
from .node_ranking import sparse_page_rank, modularity, stochastic_normalization
from scipy.cluster.hierarchy import linkage
from scipy.cluster.hierarchy import fcluster
import scipy.sparse as sp
from collections import defaultdict
#import community
from sklearn.cluster import MiniBatchKMeans
global _RANK_GRAPH


def page_rank_kernel(index_row):

    # call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(_RANK_GRAPH, [index_row],
                          epsilon=1e-6,
                          max_steps=100000,
                          damping=0.90,
                          spread_step=10,
                          spread_percent=0.1,
                          try_shrink=True)

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(G.shape[1]))


def create_tree(centers):
    clusters = {}
    to_merge = linkage(centers, method='single')
    for i, merge in enumerate(to_merge):
        if merge[0] <= len(to_merge):
            # if it is an original point read it from the centers array
            a = centers[int(merge[0]) - 1]
        else:
            # other wise read the cluster that has been created
            a = clusters[int(merge[0])]

        if merge[1] <= len(to_merge):
            b = centers[int(merge[1]) - 1]
        else:
            b = clusters[int(merge[1])]
        # the clusters are 1-indexed by scipy
        clusters[1 + i + len(to_merge)] = {'children': [a, b]}
        # ^ you could optionally store other info here (e.g distances)
    return clusters


def sum(X, v):
    rows, cols = X.shape
    row_start_stop = as_strided(X.indptr,
                                shape=(rows, 2),
                                strides=2 * X.indptr.strides)
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
        community_range=[1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300],
        fine_range=3,
        lag_threshold=10):
    if verbose:
        print("Walking..")
    global _RANK_GRAPH
    _RANK_GRAPH = input_graph
    A = _RANK_GRAPH.copy()
    _RANK_GRAPH = nx.to_scipy_sparse_matrix(_RANK_GRAPH)
    _RANK_GRAPH = stochastic_normalization(_RANK_GRAPH)  # normalize
    n = _RANK_GRAPH.shape[1]
    edgelist_triplets = []
    jobs = [range(n)[i:i + parallel_step] for i in range(0, n, parallel_step)]
    with mp.Pool(processes=parallel_step) as p:
        for batch in tqdm.tqdm(jobs):
            results = p.map(page_rank_kernel, batch)
            for nid, result_vector in results:
                cols = np.argwhere(
                    result_vector > prob_threshold).flatten().astype(int)
                vals = result_vector[cols].flatten()
                ixx = np.repeat(nid, cols.shape[0]).flatten().astype(int)
                arx = np.vstack((ixx, cols, vals)).T
                edgelist_triplets.append(arx)
    sparse_edgelist = np.concatenate(edgelist_triplets, axis=0)
    print("Compressed to {}% of the initial size".format(
        (sparse_edgelist.shape[0] * 100) / n**2))
    vectors = sp.coo_matrix(
        (sparse_edgelist[:, 2], (sparse_edgelist[:, 0].astype(int),
                                 sparse_edgelist[:, 1].astype(int)))).tocsr()
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
            mx = modularity(A, partitions, weight='weight')
            if mx > mx_opt:
                lag_num = 0
                if verbose:
                    print("Improved modularity: {}, found {} communities.".
                          format(mx, len(partitions)))
                mx_opt = mx
                opt_clust = dx_hc
                nopt = nclust
                if mx == 1:
                    nopt = nclust
                    return opt_clust
            else:
                lag_num += 1
                if verbose:
                    print("No improvement for {} iterations.".format(lag_num))

                if lag_num > lag_threshold:
                    break

        # fine grained search
        if verbose:
            print("Fine graining around {}".format(nopt))
        for nclust in range(nopt - fine_range, nopt + fine_range, 1):
            if nclust != nopt:
                dx_hc = defaultdict(list)
                clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
                clusters = clustering_algorithm.fit_predict(vectors)
                for a, b in zip(clusters, A.nodes()):
                    dx_hc[a].append(b)
                partitions = dx_hc.values()
                mx = modularity(A, partitions, weight='weight')
                if mx > mx_opt:
                    if verbose:
                        print("Improved modularity: {}, found {} communities.".
                              format(mx, len(partitions)))
                    mx_opt = mx
                    opt_clust = dx_hc
                    if mx == 1:
                        nopt = nclust
                        return opt_clust

        return opt_clust

    if clustering_scheme == "hierarchical":

        Z = linkage(vectors.todense(), 'average')
        mod_hc_opt = 0
        for nclust in tqdm.tqdm(community_range):
            dx_hc = defaultdict(list)
            try:
                cls = fcluster(Z, nclust, criterion='maxclust')
                for a, b in zip(cls, A.nodes()):
                    dx_hc[a].append(b)
                partition_hi = dx_hc.values()
                mod = modularity(A, partition_hi, weight='weight')
                if mod > mod_hc_opt:
                    if verbose:
                        print("\nImproved modularity: {}, communities: {}".
                              format(mod, len(partition_hi)))

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
    print(nx.info(graph))
    communities1 = NoRC_communities_main(graph,
                                         verbose=True,
                                         clustering_scheme="kmeans")
    communities1 = NoRC_communities_main(graph,
                                         verbose=True,
                                         clustering_scheme="hierarchical")
