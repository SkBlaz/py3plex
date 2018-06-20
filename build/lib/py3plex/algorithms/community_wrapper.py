
## high level interface for community detection algorithms
from .community_louvain import *

def louvain_communities(network,input_type="mat"):
    
    if input_type == "mat":
        network = nx.from_scipy_sparse_matrix(network)
    
    partition = best_partition(network)
    return partition
