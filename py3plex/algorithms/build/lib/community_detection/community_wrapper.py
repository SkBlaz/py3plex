# high level interface for community detection algorithms
from .community_louvain import best_partition


def louvain_communities(network, input_type="mat", verbose=True):

    # if input_type == "mat":
    #     network = nx.from_scipy_sparse_matrix(network)

    if verbose:
        print("Detecting communities..")

    partition = best_partition(network)
    return partition
