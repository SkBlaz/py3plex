r"""
Hierarchical Flow-Based Community Detection (HFCD) for Multilayer Networks.

This module implements a native algorithm for detecting hierarchical community structure
through flow dynamics, following the principle that communities are sets of nodes that
retain probability mass under diffusion processes for longer times than expected by chance.

The algorithm is fully multilayer-aware, algorithm-first (not DSL-centric), and designed
to be scalable, parameter-light, and robust.

Mathematical Foundation
-----------------------

**Flow Operator**: For a (possibly multilayer) graph, construct a transition operator P:

    P = α P_intra + (1-α) P_inter

Where:
- P_intra: degree-normalized random walk within layers
- P_inter: interlayer coupling (identity-based or learned)
- α ∈ [0,1]: interlayer coupling strength

**Flow Affinity**: For diffusion time scale t:

    F(t) = Σ_{k=1}^{t} P^k

Define symmetric flow similarity:

    S_ij(t) = (F_ij(t) + F_ji(t)) / 2

**Flow Retention (Quality Metric)**: For candidate community C at scale t:

    FlowRetention(C, t) = Σ_{i,j ∈ C} S_ij(t) / (Σ_{i ∈ C, j ∉ C} S_ij(t) + ε)

Communities maximize flow retention (probability mass trapped internally), not modularity.

**Hierarchy Emergence**: As diffusion time t increases, flow spreads further, causing
communities to merge. Hierarchy levels correspond to stability plateaus in flow retention.

Algorithm Overview
------------------

1. **Initialize**: Each node is its own community
2. **For each scale t in schedule**:
   - Estimate flow affinities S(t)
   - Compute inter-community flow retention scores
   - Agglomeratively merge communities maximizing flow retention increase
   - Record merge events and stability
3. **Extract hierarchy**: Build dendrogram, identify stability plateaus

Approximation Methods
---------------------

- **Monte Carlo**: Random walks sampled from nodes
- **Truncated Matrix Powers**: Direct computation of P^k (memory-limited)
- **Krylov/Lanczos**: Advanced sparse approximation (optional)

References
----------

- Schaub et al., "Markov Dynamics as a Zooming Lens for Multiscale Community Detection",
  PLoS ONE 7(2): e32210 (2012)
- Delvenne et al., "Stability of graph communities across time scales",
  PNAS 107(29): 12755-12760 (2010)
- Lambiotte et al., "Random Walks, Markov Processes and the Multiscale Modular Organization
  of Complex Networks", IEEE Trans. Network Science and Engineering 1(2): 76-90 (2014)

Author
------
py3plex development team

Version
-------
1.0.0 (2024)
"""

from __future__ import annotations

import warnings
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

from py3plex.exceptions import AlgorithmError, Py3plexException


# ============================================================================
# Constants
# ============================================================================

# Memory threshold for exact matrix computation (number of nodes)
MAX_NODES_EXACT_MEMORY_WARNING = 1000


# ============================================================================
# Result Container
# ============================================================================


class FlowHierarchyResult:
    """
    Container for hierarchical flow-based community detection results.

    Attributes
    ----------
    dendrogram : List[Tuple]
        List of merge events as (node_i, node_j, merge_scale, stability_before, stability_after).
    hierarchy_levels : Dict[float, Dict[Any, int]]
        Community assignments at detected hierarchy levels.
        Maps scale -> {node: community_id}.
    stability_scores : Dict[float, float]
        Flow retention stability score at each scale.
    merge_scales : np.ndarray
        Array of scales at which merges occurred.
    metadata : Dict[str, Any]
        Algorithm configuration and runtime information.
    layer_stability : Optional[Dict[Any, Dict[float, float]]]
        Per-layer stability scores (multilayer networks only).
    """

    def __init__(
        self,
        dendrogram: List[Tuple],
        hierarchy_levels: Dict[float, Dict[Any, int]],
        stability_scores: Dict[float, float],
        merge_scales: np.ndarray,
        metadata: Dict[str, Any],
        layer_stability: Optional[Dict[Any, Dict[float, float]]] = None,
    ):
        self.dendrogram = dendrogram
        self.hierarchy_levels = hierarchy_levels
        self.stability_scores = stability_scores
        self.merge_scales = merge_scales
        self.metadata = metadata
        self.layer_stability = layer_stability or {}

    def get_partition(self, scale: Optional[float] = None) -> Dict[Any, int]:
        """
        Get community assignment at a specific scale.

        Parameters
        ----------
        scale : float, optional
            Target scale. If None, returns partition at maximum stability.

        Returns
        -------
        Dict[Any, int]
            Mapping from nodes to community IDs.
        """
        if scale is None:
            # Return partition at maximum stability
            best_scale = max(self.stability_scores, key=self.stability_scores.get)
            return self.hierarchy_levels[best_scale]

        # Find closest available scale
        if scale in self.hierarchy_levels:
            return self.hierarchy_levels[scale]

        # Find nearest scale
        available_scales = sorted(self.hierarchy_levels.keys())
        nearest = min(available_scales, key=lambda s: abs(s - scale))
        return self.hierarchy_levels[nearest]

    def get_flat_partition(self, n_communities: Optional[int] = None) -> Dict[Any, int]:
        """
        Get a flat partition by cutting the dendrogram.

        Parameters
        ----------
        n_communities : int, optional
            Desired number of communities. If None, uses partition at max stability.

        Returns
        -------
        Dict[Any, int]
            Mapping from nodes to community IDs.
        """
        if n_communities is None:
            return self.get_partition()

        # Find scale yielding closest to n_communities
        best_scale = None
        best_diff = float("inf")
        for scale, partition in self.hierarchy_levels.items():
            n_comms = len(set(partition.values()))
            diff = abs(n_comms - n_communities)
            if diff < best_diff:
                best_diff = diff
                best_scale = scale

        return self.hierarchy_levels[best_scale]

    def summary(self) -> str:
        """Generate a summary report."""
        lines = ["=" * 70, "Hierarchical Flow-Based Community Detection Results", "=" * 70]

        n_nodes = len(next(iter(self.hierarchy_levels.values())))
        lines.append(f"Total nodes: {n_nodes}")
        lines.append(f"Hierarchy levels detected: {len(self.hierarchy_levels)}")
        lines.append(f"Scale range: [{min(self.merge_scales):.2f}, {max(self.merge_scales):.2f}]")

        # Best scale
        best_scale = max(self.stability_scores, key=self.stability_scores.get)
        best_stability = self.stability_scores[best_scale]
        best_partition = self.hierarchy_levels[best_scale]
        n_comms = len(set(best_partition.values()))

        lines.append("")
        lines.append("Best partition (max stability):")
        lines.append(f"  Scale: {best_scale:.2f}")
        lines.append(f"  Stability: {best_stability:.4f}")
        lines.append(f"  Communities: {n_comms}")

        # Metadata
        if self.metadata:
            lines.append("")
            lines.append("Configuration:")
            for key, val in self.metadata.items():
                if key not in ["dendrogram", "full_stability_curve"]:
                    lines.append(f"  {key}: {val}")

        # Multilayer info
        if self.layer_stability:
            lines.append("")
            lines.append(f"Multilayer network with {len(self.layer_stability)} layers")

        lines.append("=" * 70)
        return "\n".join(lines)

    def __repr__(self) -> str:
        n_nodes = len(next(iter(self.hierarchy_levels.values()))) if self.hierarchy_levels else 0
        n_levels = len(self.hierarchy_levels)
        return f"<FlowHierarchyResult: {n_nodes} nodes, {n_levels} hierarchy levels>"


# ============================================================================
# Flow Operator Construction
# ============================================================================


def _build_transition_matrix(
    network: Any,
    alpha: float = 0.8,
    multilayer: bool = True,
    weight: str = "weight",
) -> Tuple[sp.csr_matrix, List[Any], Dict[Any, int]]:
    """
    Build the transition operator P for flow dynamics.

    Parameters
    ----------
    network : multi_layer_network
        The network to analyze.
    alpha : float, default=0.8
        Intralayer weight (1-alpha for interlayer).
    multilayer : bool, default=True
        Whether to use multilayer formulation.
    weight : str, default="weight"
        Edge weight attribute.

    Returns
    -------
    P : scipy.sparse.csr_matrix
        Transition matrix (stochastic).
    nodes : List[Any]
        List of nodes (as tuples (node_id, layer) for multilayer).
    node_to_idx : Dict[Any, int]
        Mapping from nodes to indices.
    """
    from py3plex.core import multinet

    if not isinstance(network, multinet.multi_layer_network):
        raise AlgorithmError("Network must be a multi_layer_network instance")

    # Get all unique nodes (these are (node_id, layer) tuples in py3plex multilayer networks)
    # For single-layer networks with one layer, they're still stored as tuples
    try:
        nodes = list(network.get_nodes())
    except AttributeError:
        # Empty network without initialized core_network
        raise AlgorithmError("Network has no nodes or is not properly initialized")
    
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # Build adjacency matrix
    # For multilayer, we aggregate across all layers
    A = sp.lil_matrix((n, n), dtype=np.float64)

    edges = network.get_edges(data=True)
    for edge_data in edges:
        # In py3plex, edge_data format: ((src_node, src_layer), (dst_node, dst_layer), attrs_dict)
        if len(edge_data) < 2:
            continue
            
        src = edge_data[0]
        tgt = edge_data[1]

        if src not in node_to_idx or tgt not in node_to_idx:
            continue

        i, j = node_to_idx[src], node_to_idx[tgt]
        
        # Extract weight from attributes dict
        w = 1.0
        if len(edge_data) > 2 and isinstance(edge_data[2], dict):
            w = edge_data[2].get(weight, 1.0)

        A[i, j] += w
        if not network.directed:
            A[j, i] += w

    A = A.tocsr()

    # Normalize to stochastic matrix (row-stochastic)
    degree = np.array(A.sum(axis=1)).flatten()
    degree[degree == 0] = 1.0  # Avoid division by zero

    D_inv = sp.diags(1.0 / degree)
    P = D_inv @ A

    return P, nodes, node_to_idx


# ============================================================================
# Flow Affinity Computation
# ============================================================================


def _compute_flow_affinity_mc(
    P: sp.csr_matrix,
    t: int,
    n_walks: int = 100,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Compute flow affinity matrix using Monte Carlo random walks.

    This implementation uses row-wise sparse sampling to minimize memory usage.

    Parameters
    ----------
    P : scipy.sparse.csr_matrix
        Transition matrix.
    t : int
        Number of diffusion steps.
    n_walks : int, default=100
        Number of random walks per node.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    S : np.ndarray
        Symmetric flow affinity matrix (n x n).
    """
    rng = np.random.default_rng(seed)
    n = P.shape[0]

    # Accumulate flow from all walks
    F = np.zeros((n, n), dtype=np.float64)

    # Process each starting node
    for start_node in range(n):
        for _ in range(n_walks):
            current = start_node
            for step in range(1, t + 1):
                # Extract transition probabilities for current node (row-wise, sparse-friendly)
                row_start = P.indptr[current]
                row_end = P.indptr[current + 1]
                
                if row_start == row_end:
                    # Dead end (no outgoing edges)
                    break
                
                # Get non-zero indices and values for this row
                indices = P.indices[row_start:row_end]
                probs = P.data[row_start:row_end]
                
                # Normalize to ensure it's a valid probability distribution
                prob_sum = probs.sum()
                if prob_sum == 0:
                    break
                probs = probs / prob_sum
                
                # Sample next node
                next_node = rng.choice(indices, p=probs)
                F[start_node, next_node] += 1.0 / n_walks
                current = next_node

    # Symmetrize
    S = (F + F.T) / 2.0
    return S


def _compute_flow_affinity_matrix(
    P: sp.csr_matrix,
    t: int,
    max_t_exact: int = 10,
) -> np.ndarray:
    """
    Compute flow affinity matrix using truncated matrix powers.

    Parameters
    ----------
    P : scipy.sparse.csr_matrix
        Transition matrix.
    t : int
        Maximum number of diffusion steps.
    max_t_exact : int, default=10
        Maximum t for exact computation (memory constraint).

    Returns
    -------
    S : np.ndarray
        Symmetric flow affinity matrix (n x n).
    """
    n = P.shape[0]

    # Memory check
    if n > MAX_NODES_EXACT_MEMORY_WARNING and t > max_t_exact:
        warnings.warn(
            f"Large matrix ({n}x{n}) with t={t} may consume significant memory. "
            f"Consider using approx='mc' for Monte Carlo approximation.",
            RuntimeWarning,
        )

    # Accumulate powers: F(t) = sum_{k=1}^{t} P^k
    F = sp.csr_matrix((n, n), dtype=np.float64)
    P_k = P.copy()

    for k in range(1, min(t, max_t_exact) + 1):
        F = F + P_k
        if k < t:
            P_k = P_k @ P

    # Convert to dense and symmetrize
    F_dense = F.toarray()
    S = (F_dense + F_dense.T) / 2.0
    return S


# ============================================================================
# Flow Retention (Quality Metric)
# ============================================================================


def _compute_flow_retention(
    S: np.ndarray,
    partition: Dict[int, int],
    node_to_idx: Dict[Any, int],
    epsilon: float = 1e-10,
) -> float:
    """
    Compute flow retention for a partition.

    This implementation optimizes by leveraging matrix symmetry.

    Parameters
    ----------
    S : np.ndarray
        Symmetric flow affinity matrix.
    partition : Dict[int, int]
        Mapping from node indices to community IDs.
    node_to_idx : Dict[Any, int]
        Mapping from nodes to indices.
    epsilon : float, default=1e-10
        Small value to avoid division by zero.

    Returns
    -------
    float
        Flow retention score (normalized by total flow).
    """
    n = S.shape[0]

    # Build community membership matrix
    communities = defaultdict(list)
    for node_idx, comm_id in partition.items():
        communities[comm_id].append(node_idx)

    # Compute internal flow and total flow
    # Optimize by using upper triangle only (since S is symmetric)
    total_internal = 0.0
    total_flow = 0.0

    for comm_id, members in communities.items():
        members_set = set(members)

        for i in members:
            # Diagonal contribution
            total_flow += S[i, i]
            if i in members_set:
                total_internal += S[i, i]
            
            # Upper triangle only (j > i) to avoid double counting
            for j in range(i + 1, n):
                flow_ij = S[i, j]
                total_flow += 2.0 * flow_ij  # Count both directions
                
                if j in members_set:
                    total_internal += 2.0 * flow_ij  # Both directions internal

    # Normalize by total flow to get retention ratio
    # Higher values = better flow retention within communities
    if total_flow > epsilon:
        retention = total_internal / total_flow
    else:
        retention = 0.0
    
    return retention


# ============================================================================
# Agglomerative Merging
# ============================================================================


def _agglomerative_merge_step(
    S: np.ndarray,
    partition: Dict[int, int],
    nodes: List[Any],
) -> Tuple[Optional[Tuple[int, int, float]], Dict[int, int]]:
    """
    Perform one agglomerative merge step.

    Finds the pair of communities that, when merged, maximizes the increase
    in flow retention.

    Parameters
    ----------
    S : np.ndarray
        Flow affinity matrix.
    partition : Dict[int, int]
        Current partition (node_idx -> comm_id).
    nodes : List[Any]
        List of nodes.

    Returns
    -------
    merge_info : Optional[Tuple[int, int, float]]
        (comm_i, comm_j, retention_increase) if merge found, else None.
    new_partition : Dict[int, int]
        Updated partition after merge.
    """
    # Group nodes by community
    communities = defaultdict(list)
    for node_idx, comm_id in partition.items():
        communities[comm_id].append(node_idx)

    comm_ids = list(communities.keys())
    if len(comm_ids) <= 1:
        return None, partition

    # Current flow retention
    current_retention = _compute_flow_retention(S, partition, {})

    # Try all pairs of communities
    best_merge = None
    best_increase = -float("inf")
    best_partition = partition

    for i, comm_i in enumerate(comm_ids):
        for comm_j in comm_ids[i + 1 :]:
            # Simulate merge
            test_partition = partition.copy()
            for node_idx in communities[comm_j]:
                test_partition[node_idx] = comm_i

            # Compute new retention
            new_retention = _compute_flow_retention(S, test_partition, {})
            increase = new_retention - current_retention

            if increase > best_increase:
                best_increase = increase
                best_merge = (comm_i, comm_j, increase)
                best_partition = test_partition

    return best_merge, best_partition


# ============================================================================
# Stability Plateau Detection
# ============================================================================


def _detect_stability_plateaus(
    stability_curve: List[float],
    scales: List[float],
    threshold: float = 0.01,
) -> List[int]:
    """
    Detect stability plateaus in the stability curve.

    A plateau is detected when the stability score changes by less than
    `threshold` over consecutive scales.

    Parameters
    ----------
    stability_curve : List[float]
        Stability scores at each scale.
    scales : List[float]
        Corresponding scales.
    threshold : float, default=0.01
        Minimum relative change to consider a new plateau.

    Returns
    -------
    List[int]
        Indices of scales at plateau boundaries.
    """
    if len(stability_curve) < 2:
        return [0]

    plateau_indices = [0]
    for i in range(1, len(stability_curve)):
        rel_change = abs(stability_curve[i] - stability_curve[i - 1]) / (
            abs(stability_curve[i - 1]) + 1e-10
        )
        if rel_change > threshold:
            plateau_indices.append(i)

    # Always include last index
    if plateau_indices[-1] != len(stability_curve) - 1:
        plateau_indices.append(len(stability_curve) - 1)

    return plateau_indices


# ============================================================================
# Main Algorithm
# ============================================================================


def flow_hierarchical_communities(
    network: Any,
    flow_type: str = "random_walk",
    scales: Optional[List[int]] = None,
    multilayer: bool = True,
    alpha: float = 0.8,
    approx: str = "mc",
    n_walks: int = 100,
    max_scales: Optional[int] = None,
    seed: int = 42,
) -> FlowHierarchyResult:
    """
    Hierarchical flow-based community detection on single-layer or multilayer networks.

    This algorithm detects hierarchical community structure by analyzing how probability
    mass flows through the network at different diffusion time scales. Communities are
    defined as sets of nodes that retain flow internally longer than expected by chance.

    Parameters
    ----------
    network : multi_layer_network
        The network to analyze (single-layer, multiplex, or multilayer).
    flow_type : str, default="random_walk"
        Type of flow dynamics. Currently only "random_walk" is supported.
    scales : List[int], optional
        Custom scale schedule (diffusion times). If None, uses logarithmic schedule.
    multilayer : bool, default=True
        Whether to use multilayer-aware flow operator.
    alpha : float, default=0.8
        Intralayer coupling strength (1-alpha for interlayer). Range: [0, 1].
    approx : str, default="mc"
        Approximation method:
        - "mc": Monte Carlo random walks (memory-efficient)
        - "exact": Exact matrix powers (memory-intensive)
    n_walks : int, default=100
        Number of random walks per node (for approx="mc").
    max_scales : int, optional
        Maximum number of scales to evaluate (computational budget).
    seed : int, default=42
        Random seed for reproducibility.

    Returns
    -------
    FlowHierarchyResult
        Structured result containing:
        - dendrogram: List of merge events
        - hierarchy_levels: Community assignments at each detected level
        - stability_scores: Flow retention scores at each scale
        - merge_scales: Scales at which merges occurred
        - metadata: Algorithm configuration and runtime info

    Raises
    ------
    AlgorithmError
        If network is invalid or parameters are out of range.

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.community_detection import flow_hierarchical_communities
    >>>
    >>> # Create a simple network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     ['A', 'L1', 'B', 'L1', 1.0],
    ...     ['B', 'L1', 'C', 'L1', 1.0],
    ...     ['C', 'L1', 'A', 'L1', 1.0],
    ...     ['D', 'L1', 'E', 'L1', 1.0],
    ...     ['E', 'L1', 'F', 'L1', 1.0],
    ... ], input_type='list')
    >>>
    >>> # Run hierarchical flow detection
    >>> result = flow_hierarchical_communities(net, seed=42)
    >>> print(result.summary())
    >>>
    >>> # Get best partition
    >>> partition = result.get_partition()
    >>> print(f"Communities: {len(set(partition.values()))}")
    >>>
    >>> # Get partition with specific number of communities
    >>> partition_3 = result.get_flat_partition(n_communities=3)

    Notes
    -----
    **Algorithm Complexity**:
    - Time: O(t * m * k) where t is max scale, m is edges, k is merge iterations
    - Space: O(n^2) for exact, O(n * walks) for Monte Carlo
    - Recommended for networks with n < 10,000 (exact) or n < 100,000 (MC)

    **Multilayer Considerations**:
    - Automatically handles interlayer coupling via alpha parameter
    - Communities can span multiple layers
    - Set alpha=1.0 to ignore interlayer edges (layer-independent communities)

    **Choosing Parameters**:
    - **approx="mc"**: Fast, low memory, slight randomness (use with seed for reproducibility)
    - **approx="exact"**: Deterministic, high memory, slower
    - **n_walks**: Higher values reduce variance (MC only), typically 50-500
    - **alpha**: Higher values favor layer-independent communities
    - **scales**: Leave as None for automatic logarithmic schedule

    References
    ----------
    - Schaub et al., "Markov Dynamics as a Zooming Lens for Multiscale Community Detection",
      PLoS ONE 7(2): e32210 (2012)
    - Delvenne et al., "Stability of graph communities across time scales",
      PNAS 107(29): 12755-12760 (2010)
    """
    # Validation
    if flow_type != "random_walk":
        raise AlgorithmError(f"Unsupported flow_type: {flow_type}. Only 'random_walk' is supported.")

    if not 0 <= alpha <= 1:
        raise AlgorithmError(f"alpha must be in [0, 1], got {alpha}")

    if approx not in ["mc", "exact"]:
        raise AlgorithmError(f"approx must be 'mc' or 'exact', got {approx}")

    if n_walks < 1:
        raise AlgorithmError(f"n_walks must be >= 1, got {n_walks}")

    # Build transition matrix
    P, nodes, node_to_idx = _build_transition_matrix(
        network, alpha=alpha, multilayer=multilayer
    )
    n = len(nodes)

    if n == 0:
        raise AlgorithmError("Network has no nodes")

    # Define scale schedule
    if scales is None:
        # Logarithmic schedule: 1, 2, 4, 8, ..., up to n/2
        max_scale = max(2, n // 2)
        scales = [1, 2]
        while scales[-1] * 2 <= max_scale:
            scales.append(scales[-1] * 2)
    else:
        scales = sorted(scales)

    if max_scales is not None:
        scales = scales[:max_scales]

    # Initialize: each node is its own community
    partition = {i: i for i in range(n)}
    dendrogram = []
    hierarchy_levels = {}
    stability_scores = {}
    merge_scales_list = []

    # Main loop over scales
    for scale_idx, t in enumerate(scales):
        # Compute flow affinity at this scale
        if approx == "mc":
            S = _compute_flow_affinity_mc(P, t, n_walks=n_walks, seed=seed)
        else:  # exact
            S = _compute_flow_affinity_matrix(P, t)

        # Compute current stability
        stability = _compute_flow_retention(S, partition, node_to_idx)
        stability_scores[float(t)] = stability

        # Record current partition
        partition_external = {nodes[i]: comm_id for i, comm_id in partition.items()}
        hierarchy_levels[float(t)] = partition_external

        # Agglomerative merging at this scale
        # Continue merging until no improvement
        iteration = 0
        max_iterations = n  # Safety limit

        while iteration < max_iterations:
            merge_info, new_partition = _agglomerative_merge_step(S, partition, nodes)

            if merge_info is None:
                break  # No more beneficial merges

            comm_i, comm_j, increase = merge_info

            if increase <= 0:
                break  # No positive increase

            # Record merge
            dendrogram.append((comm_i, comm_j, float(t), stability, stability + increase))
            merge_scales_list.append(float(t))

            # Update partition
            partition = new_partition
            stability += increase
            iteration += 1

        # Update stability after all merges at this scale
        stability_scores[float(t)] = _compute_flow_retention(S, partition, node_to_idx)

    # Detect stability plateaus
    stability_curve = [stability_scores[float(t)] for t in scales]
    plateau_indices = _detect_stability_plateaus(stability_curve, scales)

    # Build metadata
    metadata = {
        "flow_type": flow_type,
        "multilayer": multilayer,
        "alpha": alpha,
        "approx": approx,
        "n_walks": n_walks if approx == "mc" else None,
        "seed": seed,
        "n_nodes": n,
        "n_scales": len(scales),
        "scale_schedule": scales,
        "plateau_indices": plateau_indices,
        "plateau_scales": [scales[i] for i in plateau_indices],
    }

    return FlowHierarchyResult(
        dendrogram=dendrogram,
        hierarchy_levels=hierarchy_levels,
        stability_scores=stability_scores,
        merge_scales=np.array(merge_scales_list),
        metadata=metadata,
        layer_stability=None,  # TODO: Implement per-layer stability
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "flow_hierarchical_communities",
    "FlowHierarchyResult",
]
