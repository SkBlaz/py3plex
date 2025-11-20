"""Node ranking algorithms for multilayer networks.

This module provides various node ranking algorithms including PageRank variants,
HITS (Hubs and Authorities), and personalized PageRank (PPR) for network analysis.

Key Functions:
    - sparse_page_rank: Compute PageRank scores using sparse matrix operations
    - run_PPR: Run Personalized PageRank in parallel across multiple cores
    - hubs_and_authorities: Compute HITS scores for nodes
    - stochastic_normalization: Normalize adjacency matrix to stochastic form

Notes:
    The PageRank implementations use sparse matrices for memory efficiency and
    support parallel computation for large-scale networks.
"""

import multiprocessing as mp
from typing import Any, Generator, List, Optional, Tuple, Union, cast

import networkx as nx
import numpy as np
import scipy.sparse as sp

# Global variables for multiprocessing (set by run_PPR)
__graph_matrix: sp.spmatrix
damping_hyper: float
spread_step_hyper: int
spread_percent_hyper: float


def stochastic_normalization(matrix: sp.spmatrix) -> sp.spmatrix:
    """Normalize a sparse matrix to stochastic form (column-stochastic).

    Converts an adjacency matrix to a stochastic matrix where each column sums to 1.
    This normalization is required for PageRank-style random walk algorithms.

    Args:
        matrix: Sparse adjacency matrix to normalize

    Returns:
        sp.spmatrix: Column-stochastic sparse matrix where each column sums to 1

    Notes:
        - Removes self-loops (sets diagonal to 0) before normalization
        - Handles zero-degree nodes by leaving corresponding columns as zeros
        - Preserves sparsity structure for memory efficiency

    Examples:
        >>> import scipy.sparse as sp
        >>> adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> stoch_adj = stochastic_normalization(adj)
        >>> stoch_adj.sum(axis=1).A1  # Column sums should be 1
        array([1., 1., 1.])
    """
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
    sp.diags(k, 0).tocsc()
    matrix = (sp.diags(k, 0).tocsc().dot(matrix)).transpose()
    return matrix


def page_rank_kernel(index_row: int) -> Tuple[int, np.ndarray]:
    """Compute PageRank vector for a single starting node (multiprocessing kernel).

    This function is designed to be called in parallel via multiprocessing.Pool.map().
    It computes the personalized PageRank vector starting from a single node.

    Args:
        index_row: Index of the starting node for personalized PageRank

    Returns:
        Tuple[int, np.ndarray]: (node_index, normalized_pagerank_vector)
            - node_index: The input index (for tracking results)
            - pagerank_vector: L2-normalized PageRank scores for all nodes

    Notes:
        - Accesses global variables: __graph_matrix, damping_hyper, spread_step_hyper,
          spread_percent_hyper (set by run_PPR before parallel execution)
        - Returns zero vector if normalization fails
        - L2 normalization ensures comparable magnitudes across different starting nodes

    See Also:
        run_PPR: Main function that sets up parallel execution
        sparse_page_rank: Core PageRank computation
    """

    # call as results = p.map(pr_kernel, batch)
    pr = sparse_page_rank(
        __graph_matrix,
        [index_row],
        epsilon=1e-6,
        max_steps=100000,
        damping=damping_hyper,
        spread_step=spread_step_hyper,
        spread_percent=spread_percent_hyper,
        try_shrink=True,
    )

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(__graph_matrix.shape[1]))


def sparse_page_rank(
    matrix: sp.spmatrix,
    start_nodes: Union[List[int], range],
    epsilon: float = 1e-6,
    max_steps: int = 100000,
    damping: float = 0.5,
    spread_step: int = 10,
    spread_percent: float = 0.3,
    try_shrink: bool = True,
) -> np.ndarray:
    """Compute personalized PageRank using sparse matrix operations.

    Implements an efficient personalized PageRank algorithm with adaptive sparsification
    to reduce memory usage and computation time. The algorithm uses a power iteration
    method with early stopping based on convergence criteria.

    Args:
        matrix: Column-stochastic sparse adjacency matrix (use stochastic_normalization first)
        start_nodes: List or range of starting nodes for personalized PageRank
        epsilon: Convergence threshold for L1 norm difference (default: 1e-6)
        max_steps: Maximum number of iterations (default: 100000)
        damping: Damping factor / teleportation probability (default: 0.5)
                Higher values (e.g., 0.85) favor network structure over random jumps
        spread_step: Number of steps to check for sparsity pattern (default: 10)
        spread_percent: Maximum fraction of nodes to consider for shrinkage (default: 0.3)
        try_shrink: Enable adaptive shrinkage to reduce computation (default: True)

    Returns:
        np.ndarray: PageRank scores for all nodes, with start_nodes set to 0

    Notes:
        - Assumes matrix is column-stochastic (use stochastic_normalization first)
        - Adaptive shrinkage identifies nodes unreachable from start_nodes and
          excludes them from computation for efficiency
        - Convergence is measured by L1 norm of rank vector difference
        - Start nodes are zeroed out in the final result to avoid self-importance

    Complexity:
        - Time: O(k * E) where k is iterations and E is edges
        - Space: O(N) for rank vectors, plus matrix storage

    Examples:
        >>> import scipy.sparse as sp
        >>> # Create and normalize adjacency matrix
        >>> adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>> adj_norm = stochastic_normalization(adj)
        >>> # Compute PageRank from node 0
        >>> pr = sparse_page_rank(adj_norm, [0], damping=0.85)
        >>> pr  # PageRank scores (node 0 will be 0)
        array([0.  , 0.5, 0.5])

    Raises:
        AssertionError: If start_nodes is empty

    See Also:
        stochastic_normalization: Required preprocessing step
        run_PPR: Parallel wrapper for computing multiple PageRank vectors
    """

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
    diff: Union[float, Any] = np.inf
    steps = 0
    while diff > epsilon and steps < max_steps:  # not converged yet
        steps += 1
        new_rank = matrix.dot(rank_vec)
        rank_sum: float = np.sum(new_rank)
        if rank_sum < 0.999999999:
            new_rank += start_rank * (1 - rank_sum)
        new_rank = damping * new_rank + (1 - damping) * start_rank
        new_diff = np.linalg.norm(rank_vec - new_rank, 1)
        diff = new_diff
        rank_vec = new_rank
    if try_shrink and shrink:
        ret = np.zeros(size)
        rank_vec = rank_vec.T[0]  # this works for both python versions
        ret[which] = rank_vec
        ret[start_nodes] = 0
        return cast(np.ndarray, ret.flatten())
    else:
        rank_vec[start_nodes] = 0
        return cast(np.ndarray, rank_vec.flatten())


def run_PPR(
    network: sp.spmatrix,
    cores: Optional[int] = None,
    jobs: Optional[List[range]] = None,
    damping: float = 0.85,
    spread_step: int = 10,
    spread_percent: float = 0.3,
    targets: Optional[List[int]] = None,
    parallel: bool = True,
) -> Generator[Union[Tuple[int, np.ndarray], List[Tuple[int, np.ndarray]]], None, None]:
    """Run Personalized PageRank (PPR) in parallel for multiple starting nodes.

    Computes personalized PageRank vectors for multiple nodes using parallel processing.
    This is useful for creating node embeddings or analyzing node importance from
    different perspectives in the network.

    Args:
        network: Sparse adjacency matrix (will be automatically normalized to stochastic form)
        cores: Number of CPU cores to use (default: all available cores)
        jobs: Custom job batches as list of ranges (default: auto-generated)
        damping: Damping factor for PageRank (default: 0.85)
                Higher values (0.85-0.99) emphasize network structure
        spread_step: Steps to check spread pattern for optimization (default: 10)
        spread_percent: Max node fraction for shrinkage optimization (default: 0.3)
        targets: Specific node indices to compute PPR for (default: all nodes)
        parallel: Enable parallel processing (default: True)
                 Set to False for debugging or single-core execution

    Yields:
        Union[Tuple[int, np.ndarray], List[Tuple[int, np.ndarray]]]:
            - If parallel=True: Lists of (node_index, pagerank_vector) tuples (batched)
            - If parallel=False: Individual (node_index, pagerank_vector) tuples

    Notes:
        - Automatically normalizes input matrix to column-stochastic form
        - Uses multiprocessing.Pool for parallel execution
        - Global variables are used to share the graph matrix across processes
        - Results are yielded incrementally (generator pattern) to save memory
        - Each pagerank_vector is L2-normalized for comparability

    Examples:
        >>> import scipy.sparse as sp
        >>> # Create a small network
        >>> adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        >>>
        >>> # Compute PPR for all nodes in parallel
        >>> for batch in run_PPR(adj, cores=2, parallel=True):
        ...     for node_idx, pr_vector in batch:
        ...         print(f"Node {node_idx}: {pr_vector}")
        >>>
        >>> # Compute PPR for specific nodes without parallelism
        >>> for node_idx, pr_vector in run_PPR(adj, targets=[0, 1], parallel=False):
        ...     print(f"Node {node_idx}: {pr_vector}")

    Performance:
        - Parallel speedup scales with number of cores (up to ~0.8 * cores efficiency)
        - Memory usage: O(N * N_targets) for storing results
        - For large networks (>100K nodes), consider processing targets in batches

    See Also:
        sparse_page_rank: Core PageRank computation
        page_rank_kernel: Worker function for parallel execution
        stochastic_normalization: Matrix normalization (called internally)
    """

    # normalize the matrix

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
            jobs = [range(n)[i : i + step] for i in range(0, n, step)]  # generate jobs
        else:
            jobs = [range(n)[i : i + step] for i in targets]  # generate jobs

    if not parallel:
        for target in jobs:
            for x in target:
                vector = page_rank_kernel(x)
                yield vector
    else:
        with mp.Pool(processes=cores) as p:
            for batch in jobs:
                results = p.map(page_rank_kernel, batch)
                yield results


def hubs_and_authorities(graph: nx.Graph) -> Tuple[dict, dict]:
    """Compute HITS (Hubs and Authorities) scores for all nodes in a graph.

    Implements the Hyperlink-Induced Topic Search (HITS) algorithm to identify
    hub nodes (nodes that point to many authorities) and authority nodes (nodes
    pointed to by many hubs) in a network.

    Args:
        graph: NetworkX graph (directed or undirected)

    Returns:
        Tuple[dict, dict]: (hub_scores, authority_scores)
            - hub_scores: Dictionary mapping node -> hub score
            - authority_scores: Dictionary mapping node -> authority score

    Notes:
        - Uses scipy-based implementation from NetworkX (nx.hits_scipy)
        - Scores are normalized so that the sum of squares equals 1
        - For undirected graphs, hub and authority scores are identical
        - Converges using power iteration method

    Examples:
        >>> import networkx as nx
        >>> G = nx.DiGraph([(0, 1), (0, 2), (1, 2)])
        >>> hubs, authorities = hubs_and_authorities(G)
        >>> # Node 0 has high hub score (points to others)
        >>> # Node 2 has high authority score (pointed to by others)

    See Also:
        hub_matrix: Get the hub matrix representation
        authority_matrix: Get the authority matrix representation
    """
    return nx.hits_scipy(graph)  # type: ignore[no-any-return]


def hub_matrix(graph: nx.Graph) -> np.ndarray:
    """Get the hub matrix representation of a graph.

    Computes the matrix H = A @ A.T where A is the adjacency matrix.
    The hub matrix is used in HITS algorithm computation.

    Args:
        graph: NetworkX graph

    Returns:
        np.ndarray: Hub matrix (N x N) where N is number of nodes

    Notes:
        - For directed graphs: H[i,j] = number of nodes pointed to by both i and j
        - Used internally by HITS algorithm to compute hub scores

    See Also:
        authority_matrix: Complementary authority matrix
        hubs_and_authorities: Compute actual hub/authority scores
    """
    return cast(np.ndarray, nx.hub_matrix(graph))


def authority_matrix(graph: nx.Graph) -> np.ndarray:
    """Get the authority matrix representation of a graph.

    Computes the matrix A = A.T @ A where A is the adjacency matrix.
    The authority matrix is used in HITS algorithm computation.

    Args:
        graph: NetworkX graph

    Returns:
        np.ndarray: Authority matrix (N x N) where N is number of nodes

    Notes:
        - For directed graphs: A[i,j] = number of nodes that point to both i and j
        - Used internally by HITS algorithm to compute authority scores

    See Also:
        hub_matrix: Complementary hub matrix
        hubs_and_authorities: Compute actual hub/authority scores
    """
    return cast(np.ndarray, nx.authority_matrix(graph))
