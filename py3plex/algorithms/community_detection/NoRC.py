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
from scipy.cluster.hierarchy import fcluster, linkage

from sklearn.cluster import MiniBatchKMeans

from py3plex.core.nx_compat import nx_info, nx_to_scipy_sparse_matrix

from .node_ranking import modularity, sparse_page_rank, stochastic_normalization

global _RANK_GRAPH


def page_rank_kernel(index_row):
    """Compute normalized PageRank vector for a given node.
    
    Args:
        index_row: Node index for which to compute PageRank
        
    Returns:
        Tuple of (node_index, normalized_pagerank_vector)
    """
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

    # Optimization: Compute norm once and reuse
    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / norm  # Reuse computed norm instead of recalculating
        return (index_row, pr)
    else:
        return (index_row, np.zeros(_RANK_GRAPH.shape[1]))


def NoRC_communities_main(
    input_graph,
    clustering_scheme="hierarchical",
    max_com_num=100,
    verbose=False,
    parallel_step=None,
    prob_threshold=0.0005,
    community_range=None,
    fine_range=3,
    lag_threshold=10,
):
    if community_range is None:
        community_range = [1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300]
    
    # Optimize: Use CPU count if parallel_step not specified
    if parallel_step is None:
        parallel_step = max(1, mp.cpu_count() - 1)
    
    if verbose:
        print(f"Walking with {parallel_step} parallel workers..")
    global _RANK_GRAPH
    _RANK_GRAPH = input_graph
    # Optimization: Use reference instead of copy - graph is not modified, only read for nodes() and modularity
    # This saves memory as we avoid duplicating the entire graph structure
    A = input_graph
    _RANK_GRAPH = nx_to_scipy_sparse_matrix(_RANK_GRAPH)
    _RANK_GRAPH = stochastic_normalization(_RANK_GRAPH)  # normalize
    n = _RANK_GRAPH.shape[1]
    
    # Optimization: Cache node list to avoid repeated A.nodes() calls
    node_list = list(A.nodes())
    
    # Pre-allocate lists for COO matrix construction (more memory efficient)
    row_indices = []
    col_indices = []
    values = []
    
    jobs = [range(n)[i : i + parallel_step] for i in range(0, n, parallel_step)]
    with mp.Pool(processes=parallel_step) as p:
        for batch in tqdm.tqdm(jobs):
            results = p.map(page_rank_kernel, batch)
            for nid, result_vector in results:
                # Optimize: Use direct comparison instead of argwhere
                mask = result_vector > prob_threshold
                cols = np.flatnonzero(mask)
                if cols.size > 0:
                    vals = result_vector[cols]
                    # Directly append to COO matrix components
                    row_indices.append(np.full(cols.size, nid, dtype=np.int32))
                    col_indices.append(cols.astype(np.int32))
                    values.append(vals)
    
    # Concatenate once at the end for better memory efficiency
    if row_indices:
        row_indices = np.concatenate(row_indices)
        col_indices = np.concatenate(col_indices)
        values = np.concatenate(values)
        nnz = len(values)
        print(f"Compressed to {(nnz * 100) / n**2:.4f}% of the initial size")
        vectors = sp.coo_matrix((values, (row_indices, col_indices)), shape=(n, n)).tocsr()
    else:
        print("No edges above threshold, using empty sparse matrix")
        vectors = sp.csr_matrix((n, n))
    
    mx_opt = 0
    opt_clust = None
    if clustering_scheme == "kmeans":
        if verbose:
            print("Doing kmeans search")
        nopt = 0
        lag_num = 0
        for nclust in tqdm.tqdm(community_range):
            clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
            clusters = clustering_algorithm.fit_predict(vectors)
            # Optimization: Vectorized partition building
            dx_hc = defaultdict(list)
            for cluster_id, node in zip(clusters, node_list):
                dx_hc[cluster_id].append(node)
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
        for nclust in range(max(1, nopt - fine_range), nopt + fine_range + 1, 1):
            if nclust != nopt and nclust >= 1:
                clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
                clusters = clustering_algorithm.fit_predict(vectors)
                # Optimization: Vectorized partition building
                dx_hc = defaultdict(list)
                for cluster_id, node in zip(clusters, node_list):
                    dx_hc[cluster_id].append(node)
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
        # Convert sparse matrix to dense for linkage
        # Note: scipy's linkage requires dense arrays
        if verbose:
            if vectors.nnz / (vectors.shape[0] * vectors.shape[1]) < 0.1:
                print(f"Matrix sparsity: {vectors.nnz / (vectors.shape[0] * vectors.shape[1]):.4f}")
            print("Doing hierarchical search")
        Z = linkage(vectors.toarray(), "average")
        mod_hc_opt = -1  # Start at -1 to accept any modularity value
        opt_clust = None
        nopt = 0
        lag_num = 0
        for nclust in tqdm.tqdm(community_range):
            try:
                cls = fcluster(Z, nclust, criterion="maxclust")
                # Optimization: Vectorized partition building
                dx_hc = defaultdict(list)
                for cluster_id, node in zip(cls, node_list):
                    dx_hc[cluster_id].append(node)
                partition_hi = dx_hc.values()
                mod = modularity(A, partition_hi, weight="weight")
                if mod > mod_hc_opt:
                    lag_num = 0
                    if verbose:
                        print(
                            f"Improved modularity: {mod}, found {len(partition_hi)} communities."
                        )
                    mod_hc_opt = mod
                    opt_clust = dx_hc
                    nopt = nclust
                    if mod == 1:
                        return opt_clust
                else:
                    lag_num += 1
                    if verbose:
                        print(f"No improvement for {lag_num} iterations.")
                    
                    if lag_num > lag_threshold:
                        break
            except (ValueError, IndexError) as e:
                # Handle clustering errors gracefully
                if verbose:
                    print(f"Warning: Clustering with {nclust} clusters failed: {e}")
        
        # fine grained search
        if verbose:
            print(f"Fine graining around {nopt}")
        for nclust in range(max(1, nopt - fine_range), nopt + fine_range + 1, 1):
            if nclust != nopt and nclust >= 1:
                try:
                    cls = fcluster(Z, nclust, criterion="maxclust")
                    # Optimization: Vectorized partition building
                    dx_hc = defaultdict(list)
                    for cluster_id, node in zip(cls, node_list):
                        dx_hc[cluster_id].append(node)
                    partition_hi = dx_hc.values()
                    mod = modularity(A, partition_hi, weight="weight")
                    if mod > mod_hc_opt:
                        if verbose:
                            print(
                                f"Improved modularity: {mod}, found {len(partition_hi)} communities."
                            )
                        mod_hc_opt = mod
                        opt_clust = dx_hc
                        if mod == 1:
                            return opt_clust
                except (ValueError, IndexError) as e:
                    # Handle clustering errors gracefully
                    if verbose:
                        print(f"Warning: Fine-grained clustering with {nclust} clusters failed: {e}")
        
        return opt_clust


if __name__ == "__main__":

    #                             tau1,
    #                             tau2,
    #                             mu,

    graph = nx.powerlaw_cluster_graph(1000, 5, 0.1)
    print(nx_info(graph))
    communities1 = NoRC_communities_main(
        graph, verbose=True, clustering_scheme="kmeans"
    )
    communities1 = NoRC_communities_main(
        graph, verbose=True, clustering_scheme="hierarchical"
    )
