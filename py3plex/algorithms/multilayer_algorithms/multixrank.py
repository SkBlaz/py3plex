"""
MultiXRank: Random Walk with Restart on Universal Multilayer Networks

This module implements the MultiXRank algorithm described in:
Baptista et al. (2022), "Universal multilayer network exploration by random walk
with restart", Communications Physics, 5, 170.

MultiXRank performs random walk with restart (RWR) on a supra-heterogeneous
adjacency matrix built from multiple multiplexes connected by bipartite blocks.

References:
    - Paper: https://doi.org/10.1038/s42005-022-00937-9
    - arXiv: https://arxiv.org/abs/2106.07869
    - Package: https://github.com/anthbapt/multixrank
    - Docs: https://multixrank-doc.readthedocs.io/
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import scipy.sparse as sp

from py3plex.logging_config import get_logger

if TYPE_CHECKING:
    from py3plex.core import multinet

logger = get_logger(__name__)


class MultiXRank:
    """
    MultiXRank: Universal multilayer network exploration by random walk with restart.

    This class implements the MultiXRank algorithm for node prioritization and
    ranking in universal multilayer networks. It builds a supra-heterogeneous
    adjacency matrix from multiple multiplexes and bipartite inter-multiplex
    connections, then performs random walk with restart.

    Attributes:
        multiplexes (Dict[str, sp.spmatrix]): Dictionary of multiplex supra-adjacency matrices
        bipartite_blocks (Dict[Tuple[str, str], sp.spmatrix]): Inter-multiplex connection matrices
        restart_prob (float): Restart probability (r) for RWR
        epsilon (float): Convergence threshold
        max_iter (int): Maximum number of iterations
        node_order (Dict[str, List]): Node ordering for each multiplex
        supra_matrix (sp.spmatrix): Built supra-heterogeneous adjacency matrix
        transition_matrix (sp.spmatrix): Column-stochastic transition matrix
    """

    def __init__(
        self,
        restart_prob: float = 0.4,
        epsilon: float = 1e-6,
        max_iter: int = 100000,
        verbose: bool = True,
    ):
        """
        Initialize MultiXRank.

        Args:
            restart_prob: Restart probability (r) for RWR. Common values: 0.3-0.5
            epsilon: Convergence threshold for L1 norm of probability difference
            max_iter: Maximum number of RWR iterations
            verbose: Whether to log progress information
        """
        self.multiplexes: Dict[str, sp.spmatrix] = {}
        self.bipartite_blocks: Dict[Tuple[str, str], sp.spmatrix] = {}
        self.restart_prob = restart_prob
        self.epsilon = epsilon
        self.max_iter = max_iter
        self.verbose = verbose
        self.node_order: Dict[str, List] = {}
        self.supra_matrix: Optional[sp.spmatrix] = None
        self.transition_matrix: Optional[sp.spmatrix] = None
        self._multiplex_dims: Dict[str, int] = {}
        self._multiplex_offsets: Dict[str, int] = {}

    def add_multiplex(
        self,
        name: str,
        supra_adjacency: Union[sp.spmatrix, np.ndarray],
        node_order: Optional[List] = None,
    ):
        """
        Add a multiplex to the universal multilayer network.

        Args:
            name: Unique identifier for this multiplex
            supra_adjacency: Supra-adjacency matrix for the multiplex (can be from
                           multi_layer_network.get_supra_adjacency_matrix())
            node_order: Optional list of node IDs in the order they appear in the matrix.
                       If None, uses integer indices.
        """
        # Convert to sparse if needed
        if not sp.issparse(supra_adjacency):
            supra_adjacency_sparse = sp.csr_matrix(supra_adjacency)
        else:
            supra_adjacency_sparse = supra_adjacency.tocsr()  # type: ignore[union-attr]

        if supra_adjacency_sparse.shape[0] != supra_adjacency_sparse.shape[1]:
            raise ValueError(f"Supra-adjacency matrix for '{name}' must be square")

        self.multiplexes[name] = supra_adjacency_sparse
        self._multiplex_dims[name] = supra_adjacency_sparse.shape[0]

        if node_order is None:
            node_order = list(range(supra_adjacency.shape[0]))
        self.node_order[name] = node_order

        if self.verbose:
            logger.info(
                f"Added multiplex '{name}' with dimension {supra_adjacency.shape[0]}"
            )

    def add_bipartite_block(
        self,
        multiplex_from: str,
        multiplex_to: str,
        bipartite_matrix: Union[sp.spmatrix, np.ndarray],
        weight: float = 1.0,
    ):
        """
        Add a bipartite block connecting two multiplexes.

        Args:
            multiplex_from: Name of source multiplex
            multiplex_to: Name of target multiplex
            bipartite_matrix: Matrix of connections (rows: from, cols: to)
            weight: Optional weight to scale this bipartite block
        """
        if multiplex_from not in self.multiplexes:
            raise ValueError(f"Source multiplex '{multiplex_from}' not found")
        if multiplex_to not in self.multiplexes:
            raise ValueError(f"Target multiplex '{multiplex_to}' not found")

        # Convert to sparse if needed
        if not sp.issparse(bipartite_matrix):
            bipartite_matrix_sparse = sp.csr_matrix(bipartite_matrix)
        else:
            bipartite_matrix_sparse = bipartite_matrix.tocsr()  # type: ignore[union-attr]

        # Verify dimensions match
        expected_rows = self._multiplex_dims[multiplex_from]
        expected_cols = self._multiplex_dims[multiplex_to]

        if bipartite_matrix_sparse.shape != (expected_rows, expected_cols):
            raise ValueError(
                f"Bipartite block dimensions {bipartite_matrix_sparse.shape} don't match "
                f"expected ({expected_rows}, {expected_cols})"
            )

        # Apply weight if specified
        if weight != 1.0:
            bipartite_matrix_sparse = bipartite_matrix_sparse * weight

        self.bipartite_blocks[(multiplex_from, multiplex_to)] = bipartite_matrix_sparse

        if self.verbose:
            logger.info(
                f"Added bipartite block from '{multiplex_from}' to '{multiplex_to}' "
                f"with {bipartite_matrix.nnz} edges"
            )

    def build_supra_heterogeneous_matrix(
        self, block_weights: Optional[Dict[Union[str, Tuple[str, str]], float]] = None
    ):
        """
        Build the supra-heterogeneous adjacency matrix S.

        This constructs the universal multilayer network matrix by:
        1. Placing each multiplex supra-adjacency on the block diagonal
        2. Adding bipartite blocks for inter-multiplex connections

        Args:
            block_weights: Optional dictionary to weight blocks. Keys can be:
                          - Multiplex names (to weight within-multiplex edges)
                          - Tuple (multiplex_from, multiplex_to) for bipartite blocks

        Returns:
            The supra-heterogeneous adjacency matrix
        """
        if not self.multiplexes:
            raise ValueError("No multiplexes added. Add at least one multiplex first.")

        # Calculate offsets for each multiplex in the full matrix
        offset = 0
        multiplex_names = sorted(self.multiplexes.keys())  # Consistent ordering
        for name in multiplex_names:
            self._multiplex_offsets[name] = offset
            offset += self._multiplex_dims[name]

        total_dim = offset

        if self.verbose:
            logger.info(
                f"Building supra-heterogeneous matrix of size {total_dim}×{total_dim}"
            )

        # Build list of matrix blocks in (data, (row, col)) format
        rows_list = []
        cols_list = []
        data_list = []

        # Add multiplex blocks on diagonal
        for name in multiplex_names:
            offset = self._multiplex_offsets[name]
            mtx = self.multiplexes[name]

            # Apply weight if specified
            if block_weights and name in block_weights:
                mtx = mtx * block_weights[name]

            # Get coordinates and data
            mtx_coo = mtx.tocoo()
            rows_list.append(mtx_coo.row + offset)
            cols_list.append(mtx_coo.col + offset)
            data_list.append(mtx_coo.data)

        # Add bipartite blocks
        for (multiplex_from, multiplex_to), block in self.bipartite_blocks.items():
            row_offset = self._multiplex_offsets[multiplex_from]
            col_offset = self._multiplex_offsets[multiplex_to]

            # Apply weight if specified
            if block_weights and (multiplex_from, multiplex_to) in block_weights:
                block = block * block_weights[(multiplex_from, multiplex_to)]

            # Get coordinates and data
            block_coo = block.tocoo()
            rows_list.append(block_coo.row + row_offset)
            cols_list.append(block_coo.col + col_offset)
            data_list.append(block_coo.data)

        # Combine all blocks
        rows = np.concatenate(rows_list)
        cols = np.concatenate(cols_list)
        data = np.concatenate(data_list)

        self.supra_matrix = sp.csr_matrix(
            (data, (rows, cols)), shape=(total_dim, total_dim)
        )

        if self.verbose:
            logger.info(
                f"Built supra-heterogeneous matrix with {self.supra_matrix.nnz} edges"
            )

        return self.supra_matrix

    def column_normalize(self, handle_dangling: str = "uniform") -> sp.spmatrix:
        """
        Column-normalize the supra-heterogeneous matrix to create a stochastic transition matrix.

        This ensures each column sums to 1, making the matrix suitable for RWR.

        Args:
            handle_dangling: How to handle dangling nodes (columns with zero sum):
                           - 'uniform': Distribute mass uniformly across all nodes
                           - 'self': Add self-loop (mass stays at the node)
                           - 'ignore': Leave as zero (not recommended for RWR)

        Returns:
            Column-stochastic transition matrix
        """
        if self.supra_matrix is None:
            raise ValueError("Must build supra-heterogeneous matrix first")

        matrix = self.supra_matrix.tocsc()  # Column-oriented for efficiency

        # Compute column sums
        col_sums = np.array(matrix.sum(axis=0)).flatten()

        # Identify dangling columns (zero out-degree)
        dangling = col_sums == 0
        n_dangling: int = int(np.sum(dangling))

        if n_dangling > 0 and self.verbose:
            logger.warning(f"Found {n_dangling} dangling nodes (zero out-degree)")

        # Handle dangling nodes
        if handle_dangling == "uniform" and n_dangling > 0:
            # Add uniform distribution for dangling nodes
            n_nodes = matrix.shape[0]
            dangling_idx = np.where(dangling)[0]

            # Add uniform column for each dangling node
            rows = np.tile(np.arange(n_nodes), n_dangling)
            cols: Any = np.repeat(dangling_idx, n_nodes)
            data = np.ones(n_nodes * n_dangling) / n_nodes

            dangling_matrix = sp.csr_matrix((data, (rows, cols)), shape=matrix.shape)
            matrix = matrix + dangling_matrix
            col_sums = np.array(matrix.sum(axis=0)).flatten()

        elif handle_dangling == "self" and n_dangling > 0:
            # Add self-loops for dangling nodes
            dangling_idx = np.where(dangling)[0]
            matrix = matrix.tolil()
            for idx in dangling_idx:
                matrix[idx, idx] = 1.0
            matrix = matrix.tocsr()
            col_sums = np.array(matrix.sum(axis=0)).flatten()

        # Normalize columns
        col_sums_inv = np.zeros_like(col_sums)
        nonzero = col_sums > 0
        col_sums_inv[nonzero] = 1.0 / col_sums[nonzero]

        # Create diagonal matrix of inverse column sums and multiply
        col_diag = sp.diags(col_sums_inv, format="csr")
        self.transition_matrix = (matrix @ col_diag).tocsr()

        if self.verbose:
            logger.info("Created column-stochastic transition matrix")

        return self.transition_matrix

    def random_walk_with_restart(
        self,
        seed_nodes: Union[List[int], Dict[str, List], np.ndarray],
        seed_weights: Optional[np.ndarray] = None,
        multiplex_name: Optional[str] = None,
    ) -> np.ndarray:
        """
        Perform Random Walk with Restart (RWR) from seed nodes.

        Args:
            seed_nodes: Seed node specification. Can be:
                       - List of global indices in the supra-matrix
                       - Dict mapping multiplex names to lists of local node indices
                       - NumPy array of global indices
            seed_weights: Optional weights for seed nodes (must match length of seed_nodes).
                         If None, uniform weights are used.
            multiplex_name: If seed_nodes is a list/array of local indices, specify
                          which multiplex they belong to

        Returns:
            Steady-state probability vector (length = total nodes across all multiplexes)
        """
        if self.transition_matrix is None:
            raise ValueError("Must build and normalize matrix first")

        n_nodes = self.transition_matrix.shape[0]

        # Convert seed nodes to global indices
        global_seed_indices = self._convert_seed_nodes_to_global(
            seed_nodes, multiplex_name
        )

        if len(global_seed_indices) == 0:
            raise ValueError("No valid seed nodes provided")

        # Initialize seed vector
        seed_vec = np.zeros(n_nodes)

        if seed_weights is not None:
            if len(seed_weights) != len(global_seed_indices):
                raise ValueError("seed_weights length must match number of seed nodes")
            for idx, weight in zip(global_seed_indices, seed_weights):
                seed_vec[idx] = weight
        else:
            seed_vec[global_seed_indices] = 1.0

        # Normalize seed vector
        seed_vec = seed_vec / np.sum(seed_vec)

        # Initialize probability vector
        p = seed_vec.copy()

        if self.verbose:
            logger.info(
                f"Starting RWR with {len(global_seed_indices)} seed nodes, "
                f"restart_prob={self.restart_prob}"
            )

        # RWR iteration: p_{t+1} = (1-r) * S * p_t + r * p_0
        converged = False
        for iteration in range(self.max_iter):
            p_new = (1 - self.restart_prob) * (
                self.transition_matrix @ p
            ) + self.restart_prob * seed_vec

            # Check convergence
            diff = np.linalg.norm(p_new - p, ord=1)

            if diff < self.epsilon:
                converged = True
                if self.verbose:
                    logger.info(
                        f"RWR converged after {iteration + 1} iterations (L1 diff: {diff:.2e})"
                    )
                break

            p = p_new

        if not converged:
            logger.warning(
                f"RWR did not converge after {self.max_iter} iterations "
                f"(L1 diff: {diff:.2e})"
            )

        return cast(np.ndarray, p)

    def _convert_seed_nodes_to_global(
        self,
        seed_nodes: Union[List[int], Dict[str, List], np.ndarray],
        multiplex_name: Optional[str] = None,
    ) -> List[int]:
        """
        Convert seed node specification to global indices.

        Args:
            seed_nodes: Seed nodes in various formats
            multiplex_name: Multiplex name if seed_nodes are local indices

        Returns:
            List of global indices in the supra-matrix
        """
        if isinstance(seed_nodes, dict):
            # Dict mapping multiplex names to local node lists
            global_indices = []
            for mplex_name, local_nodes in seed_nodes.items():
                if mplex_name not in self._multiplex_offsets:
                    raise ValueError(f"Unknown multiplex: {mplex_name}")
                offset = self._multiplex_offsets[mplex_name]
                global_indices.extend([idx + offset for idx in local_nodes])
            return global_indices

        elif multiplex_name is not None:
            # Local indices for a specific multiplex
            if multiplex_name not in self._multiplex_offsets:
                raise ValueError(f"Unknown multiplex: {multiplex_name}")
            offset = self._multiplex_offsets[multiplex_name]
            if isinstance(seed_nodes, np.ndarray):
                seed_nodes = seed_nodes.tolist()
            return [int(idx) + offset for idx in seed_nodes]

        else:
            # Assume global indices
            if isinstance(seed_nodes, np.ndarray):
                return list(seed_nodes.tolist())
            return list(seed_nodes)

    def aggregate_scores(
        self, scores: np.ndarray, aggregation: str = "sum"
    ) -> Dict[str, Dict]:
        """
        Aggregate scores per multiplex and optionally per physical node.

        Args:
            scores: Probability vector from RWR (length = total supra-matrix dimension)
            aggregation: How to aggregate scores ('sum', 'mean', 'max')

        Returns:
            Dictionary mapping multiplex names to dictionaries of node scores
        """
        if aggregation not in ["sum", "mean", "max"]:
            raise ValueError(f"Unknown aggregation method: {aggregation}")

        result = {}

        for mplex_name in sorted(self.multiplexes.keys()):
            offset = self._multiplex_offsets[mplex_name]
            dim = self._multiplex_dims[mplex_name]

            # Extract scores for this multiplex
            mplex_scores = scores[offset : offset + dim]

            # Map to node IDs
            node_scores = {}
            for i, node_id in enumerate(self.node_order[mplex_name]):
                node_scores[node_id] = mplex_scores[i]

            result[mplex_name] = node_scores

        return result

    def get_top_ranked(
        self,
        scores: np.ndarray,
        k: int = 10,
        multiplex: Optional[str] = None,
        exclude_seeds: bool = True,
        seed_nodes: Optional[Union[List[int], Dict[str, List]]] = None,
    ) -> List[Tuple]:
        """
        Get top-k ranked nodes from RWR scores.

        Args:
            scores: Probability vector from RWR
            k: Number of top nodes to return
            multiplex: If specified, only return nodes from this multiplex
            exclude_seeds: Whether to exclude seed nodes from results
            seed_nodes: Seed nodes to exclude (if exclude_seeds=True)

        Returns:
            List of (global_index, score) tuples, sorted by score descending
        """
        # Get global seed indices if excluding
        exclude_indices = set()
        if exclude_seeds and seed_nodes is not None:
            exclude_indices = set(self._convert_seed_nodes_to_global(seed_nodes, None))

        # Filter by multiplex if specified
        if multiplex is not None:
            if multiplex not in self._multiplex_offsets:
                raise ValueError(f"Unknown multiplex: {multiplex}")
            offset = self._multiplex_offsets[multiplex]
            dim = self._multiplex_dims[multiplex]
            valid_indices = set(range(offset, offset + dim))
        else:
            valid_indices = set(range(len(scores)))

        # Remove seed nodes
        valid_indices = valid_indices - exclude_indices

        # Get scores for valid indices
        valid_scores = [(idx, scores[idx]) for idx in valid_indices]

        # Sort by score descending
        valid_scores.sort(key=lambda x: x[1], reverse=True)

        return valid_scores[:k]


def multixrank_from_py3plex_networks(
    networks: Dict[str, "multinet.multi_layer_network"],
    bipartite_connections: Optional[
        Dict[Tuple[str, str], Union[sp.spmatrix, np.ndarray]]
    ] = None,
    seed_nodes: Optional[Dict[str, List]] = None,
    restart_prob: float = 0.4,
    epsilon: float = 1e-6,
    max_iter: int = 100000,
    verbose: bool = True,
) -> Tuple[MultiXRank, np.ndarray]:
    """
    Convenience function to run MultiXRank on py3plex multi_layer_network objects.

    Args:
        networks: Dictionary mapping names to multi_layer_network objects
        bipartite_connections: Optional dict of inter-network connection matrices
        seed_nodes: Dict mapping network names to lists of seed node IDs
        restart_prob: Restart probability for RWR
        epsilon: Convergence threshold
        max_iter: Maximum iterations
        verbose: Whether to log progress

    Returns:
        Tuple of (MultiXRank object, scores array)

    Example:
        >>> from py3plex.core import multinet
        >>> net1 = multinet.multi_layer_network()
        >>> net1.load_network('network1.edgelist', ...)
        >>> net2 = multinet.multi_layer_network()
        >>> net2.load_network('network2.edgelist', ...)
        >>>
        >>> networks = {'net1': net1, 'net2': net2}
        >>> seed_nodes = {'net1': ['node1', 'node2']}
        >>>
        >>> mxr, scores = multixrank_from_py3plex_networks(
        ...     networks, seed_nodes=seed_nodes
        ... )
        >>>
        >>> # Get aggregated scores per network
        >>> aggregated = mxr.aggregate_scores(scores)
    """
    mxr = MultiXRank(
        restart_prob=restart_prob, epsilon=epsilon, max_iter=max_iter, verbose=verbose
    )

    # Add multiplexes
    for name, network in networks.items():
        supra_adj = network.get_supra_adjacency_matrix(mtype="sparse")
        # Get node order from network
        node_order = (
            network.node_order_in_matrix
            if hasattr(network, "node_order_in_matrix")
            else None
        )
        mxr.add_multiplex(name, supra_adj, node_order)

    # Add bipartite connections if provided
    if bipartite_connections:
        for (from_net, to_net), matrix in bipartite_connections.items():
            mxr.add_bipartite_block(from_net, to_net, matrix)

    # Build and normalize matrix
    mxr.build_supra_heterogeneous_matrix()
    mxr.column_normalize()

    # Run RWR if seed nodes provided
    if seed_nodes:
        scores = mxr.random_walk_with_restart(seed_nodes)
        return mxr, scores
    else:
        return mxr, None
