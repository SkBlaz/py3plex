# node ranking algorithms
import multiprocessing as mp
from typing import Any, Generator, List, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp

# Import main functions from node_ranking module to avoid duplication
from .node_ranking import (
    authority_matrix,
    hub_matrix,
    hubs_and_authorities,
    sparse_page_rank,
    stochastic_normalization,
    stochastic_normalization_hin,
)

# Global variables for multiprocessing (set by run_PPR)
__graph_matrix: sp.spmatrix
damping_hyper: float
spread_step_hyper: int
spread_percent_hyper: float


def page_rank_kernel(index_row: int) -> Tuple[int, np.ndarray]:
    """
    Kernel function for parallel PageRank computation.
    
    Args:
        index_row: Row index to compute PageRank for
        
    Returns:
        Tuple of (row_index, pagerank_vector)
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
    """
    Run Personalized PageRank in parallel.
    
    Args:
        network: Sparse matrix representing the network
        cores: Number of CPU cores to use
        jobs: List of job ranges
        damping: Damping factor
        spread_step: Spread step parameter
        spread_percent: Spread percentage parameter
        targets: Target node indices
        parallel: Whether to use parallel processing
        
    Yields:
        PageRank vectors for each node
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


__all__ = [
    "stochastic_normalization",
    "stochastic_normalization_hin",
    "sparse_page_rank",
    "run_PPR",
    "page_rank_kernel",
    "hubs_and_authorities",
    "hub_matrix",
    "authority_matrix",
]
