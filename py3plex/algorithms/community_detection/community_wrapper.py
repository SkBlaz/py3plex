
## high level interface for community detection algorithms
from .community_louvain import *

def louvain_communities(network,input_type="mat",verbose=True):
    
    # if input_type == "mat":
    #     network = nx.from_scipy_sparse_matrix(network)

    if verbose:
        network.monitor("Detecting communities..")
    try:
        partition = best_partition(network.core_network)
        
    except:
        ## network is already the input!
        partition = best_partition(network)
        
    return partition
