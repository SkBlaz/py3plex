## a framework for community-based node ranking

import networkx as nx
import numpy as np
from sklearn.cluster import AffinityPropagation
import multiprocessing as mp
from node_ranking import sparse_page_rank,modularity,stochastic_normalization
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.cluster.hierarchy import fcluster
import scipy.sparse as sp

def page_rank_kernel(index_row):

    ## call as results = p.map(pr_kernel, batch)
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
        return (index_row,pr)
    else:
        return (index_row,np.zeros(G.shape[1]))

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
        clusters[1 + i + len(to_merge)] = {
            'children' : [a, b]
        }
        # ^ you could optionally store other info here (e.g distances)
    return clusters

def return_infomap_communities(network):

    infomapWrapper = infomap.Infomap("--two-level --silent")

    # Add link weight as an optional third argument
    for e in network.edges():
        infomapWrapper.addLink(e[0], e[1])
    infomapWrapper.run()
    tree = infomapWrapper.tree
    print("Found %d modules with codelength: %f" % (tree.numTopModules(), tree.codelength()))
    print("\n#node module")
    part = defaultdict(list)
    for node in tree.leafIter():
        part[node.moduleIndex()].append(node.physIndex)
    return list(part.values())
    
if __name__ == "__main__":
    from infomap import infomap
    from collections import defaultdict
    from itertools import product
    import community
    from networkx.algorithms.community import LFR_benchmark_graph
    from sklearn.cluster import AffinityPropagation,DBSCAN,MiniBatchKMeans
    from scipy import cluster
    from scipy.cluster.hierarchy import fcluster
    from scipy.spatial.distance import pdist
    global _RANK_GRAPH

    print("Generating communities..")
    
    n = 500
    tau1 = 4
    tau2 = 1.5
    mu = 0.1
#    _RANK_GRAPH = nx.windmill_graph(20, 5)
    _RANK_GRAPH = LFR_benchmark_graph(n,
                                      tau1,
                                      tau2,
                                      mu,
                                      average_degree=5,
                                      min_community=30,
                                      seed=10)
    print(nx.info(_RANK_GRAPH))
    A = _RANK_GRAPH.copy()
    _RANK_GRAPH = nx.to_scipy_sparse_matrix(_RANK_GRAPH)
    _RANK_GRAPH = stochastic_normalization(_RANK_GRAPH) ## normalize
    n = _RANK_GRAPH.shape[1]
    with mp.Pool(processes=mp.cpu_count()) as p:
        results = p.map(page_rank_kernel,range(n))

    vectors = np.zeros((n, n))
    for pr_vector in results:
        if pr_vector != None:
            vectors[pr_vector[0],:] = pr_vector[1]
    
    vectors = np.nan_to_num(vectors)
    option = "cpu"
    dx_rc = defaultdict(list)
    dx_lx = defaultdict(list)
    dx_hc = defaultdict(list)

    if option == "cpu":
        mx_opt = 0
        for nclust in range(2,_RANK_GRAPH.shape[0]):
            clustering_algorithm = MiniBatchKMeans(n_clusters=nclust)
            clusters = clustering_algorithm.fit_predict(vectors)
            for a, b in zip(clusters,A.nodes()):
                dx_rc[a].append(b)
            partitions = dx_rc.values()
            mx = modularity(A, partitions, weight='weight')
            if mx > mx_opt:
                mx_opt = mx
            dx_rc = defaultdict(list)
        
        print("KM: {}".format(mx_opt))
        Z = linkage(vectors, 'ward')
        mod_hc_opt = 0
        for nclust in range(3,_RANK_GRAPH.shape[0]):
            try:
                k = nclust
                cls = fcluster(Z, k, criterion='maxclust')
                for a,b in zip(cls,A.nodes()):
                    dx_hc[a].append(b)
                partition_hi = dx_hc.values()
                mod = modularity(A, partition_hi, weight='weight')
                if mod > mod_hc_opt:
                    mod_hc_opt = mod
            except:
                pass
                
        print("Hierarchical: {}".format(mod))

    ## the louvain partition
    partition = community.best_partition(A)
    for a,b in partition.items():
        dx_lx[b].append(a)
    partition_louvain = dx_lx.values()
    print("Louvain: {}".format(modularity(A, partition_louvain, weight='weight')))

    parts_im = return_infomap_communities(A)
    print("Infomap: {}".format(modularity(A, parts_im, weight='weight')))
