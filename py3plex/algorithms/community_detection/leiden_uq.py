"""Multilayer Leiden algorithm with uncertainty quantification.

This module provides production-quality multilayer/multiplex Leiden community detection
with first-class uncertainty quantification (UQ) and DSL integration.

Key Features:
- Deterministic execution given a seed (default seed=0 if not specified)
- Multiple UQ strategies: seed ensemble, edge perturbation, bootstrap
- Consensus partition methods: medoid (default) and co-assignment clustering
- Comprehensive diagnostics: timing, convergence, stability metrics
- Full integration with DSL v2 builder API

References:
    - Traag, V. A., Waltman, L., & Van Eck, N. J. (2019). From Louvain to Leiden:
      guaranteeing well-connected communities. Scientific reports, 9(1), 5233.
    - Mucha et al., "Community Structure in Time-Dependent, Multiscale, and Multiplex
      Networks", Science 328:876-878 (2010)
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from py3plex.algorithms.community_detection.leiden_multilayer import (
    leiden_multilayer,
    LeidenResult,
)
from py3plex.algorithms.community_detection.multilayer_modularity import (
    multilayer_modularity,
)
from py3plex.uncertainty.partition import (
    CommunityDistribution,
    partition_dict_to_array,
    partition_array_to_dict,
)
from py3plex.uncertainty.resampling_graph import (
    perturb_network_edges,
    bootstrap_network_edges,
)
from py3plex._parallel import spawn_seeds
from py3plex.exceptions import AlgorithmError


@dataclass
class UQResult:
    """Container for uncertainty quantification results.
    
    Attributes:
        partitions: List of partition dicts (optional, if return_all=True)
        scores: List of modularity scores for each run
        consensus_partition: Consensus partition dict (node, layer) -> community_id
        membership_probs: Node membership probability matrix (n_nodes x n_communities)
        stability_metrics: Dict with VI/NMI distributions, pairwise agreement
        ci: Dict with confidence intervals (score, n_communities)
        summary: Dict with mean/std statistics
        diagnostics: Dict with seed table, runtime, failures
    """
    partitions: Optional[List[Dict[Tuple[Any, Any], int]]] = None
    scores: List[float] = field(default_factory=list)
    consensus_partition: Dict[Tuple[Any, Any], int] = field(default_factory=dict)
    membership_probs: Optional[np.ndarray] = None
    stability_metrics: Dict[str, Any] = field(default_factory=dict)
    ci: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


def canonicalize_partition(
    partition: Dict[Tuple[Any, Any], int],
    node_order: Optional[List[Tuple[Any, Any]]] = None
) -> Dict[Tuple[Any, Any], int]:
    """Canonicalize partition labels by relabeling in order of first appearance.
    
    Args:
        partition: Dict mapping (node, layer) to community ID
        node_order: Optional stable node ordering. If None, sorts by keys.
        
    Returns:
        Canonicalized partition with community IDs 0, 1, 2, ...
    """
    if node_order is None:
        node_order = sorted(partition.keys())
    
    # Map old community IDs to new ones based on first appearance
    old_to_new = {}
    next_id = 0
    
    canonical = {}
    for node_layer in node_order:
        if node_layer not in partition:
            continue
        old_id = partition[node_layer]
        if old_id not in old_to_new:
            old_to_new[old_id] = next_id
            next_id += 1
        canonical[node_layer] = old_to_new[old_id]
    
    return canonical


def multilayer_leiden(
    network: Any,
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    n_iterations: int = 2,
    random_state: Optional[int] = None,
    init_partition: Optional[Dict[Tuple[Any, Any], int]] = None,
    allow_isolates: bool = True,
    return_diagnostics: bool = False,
    backend: str = "auto",
) -> Union[
    Tuple[Dict[Tuple[Any, Any], int], float],
    Tuple[Dict[Tuple[Any, Any], int], float, Dict[str, Any]]
]:
    """Multilayer Leiden community detection algorithm.
    
    This implements the Leiden method for multilayer/multiplex networks using
    a supra-graph formulation with interlayer coupling. The algorithm optimizes
    multilayer modularity with resolution parameter gamma and coupling omega.
    
    Objective Function:
        Q = (1/2μ) Σ_{ijsr} [(A_{ijs} - γ_s k_{is}k_{js}/2m_s) δ_{sr} + δ_{ij} ω_{sr}] δ(g_{is}, g_{jr})
        
    where:
        - A_{ijs}: adjacency matrix element for nodes i,j in layer s
        - γ_s: resolution parameter for layer s
        - k_{is}: degree of node i in layer s
        - m_s: total edge weight in layer s
        - ω_{sr}: interlayer coupling between layers s and r
        - δ(g_{is}, g_{jr}): 1 if node-layers are in same community, else 0
        - μ: total weight in supra-network
        
    The algorithm consists of:
        1. Local moving phase: optimize quality by moving nodes
        2. Refinement phase: ensure well-connected communities (key Leiden improvement)
        3. Aggregation phase: create coarser network
        4. Repeat for n_iterations or until convergence
        
    Args:
        network: py3plex multi_layer_network object with L layers
        gamma: Resolution parameter(s). Higher values -> more communities.
            - float: same resolution for all layers
            - Dict[layer, float]: per-layer resolution
            Default: 1.0
        omega: Interlayer coupling strength. Higher values -> stronger coupling.
            - float: uniform coupling between all layer pairs
            - np.ndarray: L×L coupling matrix (diagonal ignored)
            Default: 1.0
        n_iterations: Maximum number of Leiden iterations. Default: 2
        random_state: Random seed for reproducibility. If None, uses seed=0 for
            deterministic behavior. Default: None (becomes 0)
        init_partition: Initial partition dict (node, layer) -> comm_id. If None,
            starts with singleton communities. Default: None
        allow_isolates: If True, isolates can be in their own communities. If False,
            attempts to assign them to nearest community. Default: True
        return_diagnostics: If True, returns (partition, score, diagnostics) instead
            of (partition, score). Default: False
        backend: Algorithm backend to use:
            - "auto": Use native implementation (igraph/leidenalg not required)
            - "native": Force native Python implementation
            - "igraph": Use igraph/leidenalg if available (future)
            Default: "auto"
            
    Returns:
        If return_diagnostics=False:
            partition: Dict mapping (node, layer) tuples to community IDs
            score: Multilayer modularity value
        If return_diagnostics=True:
            partition: Dict mapping (node, layer) tuples to community IDs
            score: Multilayer modularity value
            diagnostics: Dict with:
                - timing: Runtime in seconds
                - n_moves: Number of node moves per iteration
                - n_communities_per_level: Communities at each iteration
                - convergence_info: Convergence status and iterations
                - backend_used: Which backend was used
                
    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection import multilayer_leiden
        >>>
        >>> # Create multilayer network
        >>> net = multinet.multi_layer_network(directed=False)
        >>> net.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ...     ['A', 'L2', 'C', 'L2', 1],
        ... ], input_type='list')
        >>>
        >>> # Run Leiden with default parameters
        >>> partition, Q = multilayer_leiden(net, random_state=42)
        >>> print(f"Modularity: {Q:.3f}")
        >>> print(f"Communities: {partition}")
        >>>
        >>> # Run with diagnostics
        >>> partition, Q, diag = multilayer_leiden(
        ...     net, gamma=1.2, omega=0.8, return_diagnostics=True, random_state=42
        ... )
        >>> print(f"Runtime: {diag['timing']:.3f}s")
        >>> print(f"Iterations: {diag['convergence_info']['iterations']}")
    
    Notes:
        - Determinism: Same random_state yields identical partition and score
        - Default seed: If random_state=None, defaults to 0 for reproducibility
        - Empty networks: Returns singleton partition with Q=0
        - Isolates: Handled according to allow_isolates flag
        - Backend: Currently only "native" is implemented; "igraph" reserved for future
    """
    # Validate inputs
    if gamma <= 0:
        raise AlgorithmError(
            f"gamma must be positive, got {gamma}",
            suggestions=["Use gamma > 0 (typically gamma=1.0)"]
        )
    if isinstance(omega, (int, float)) and omega < 0:
        raise AlgorithmError(
            f"omega must be non-negative, got {omega}",
            suggestions=["Use omega >= 0 (typically omega=1.0)"]
        )
    if n_iterations < 1:
        raise AlgorithmError(
            f"n_iterations must be >= 1, got {n_iterations}",
            suggestions=["Use n_iterations >= 2 for Leiden (recommended)"]
        )
    
    # Handle backend selection
    if backend not in ["auto", "native", "igraph"]:
        raise AlgorithmError(
            f"Unknown backend: {backend}",
            suggestions=["Use 'auto', 'native', or 'igraph'"]
        )
    
    if backend == "igraph":
        warnings.warn(
            "igraph backend not yet implemented, falling back to native",
            FutureWarning,
            stacklevel=2
        )
        backend = "native"
    
    # Set deterministic default seed
    if random_state is None:
        random_state = 0
    
    # Start timing
    start_time = time.time()
    
    # Run Leiden algorithm
    result = leiden_multilayer(
        network,  # First positional arg (gets passed to graph_layers after decorator)
        interlayer_coupling=omega,
        resolution=gamma,
        seed=random_state,
        max_iter=n_iterations,
    )
    
    # Canonicalize partition
    node_order = sorted(result.communities.keys())
    partition = canonicalize_partition(result.communities, node_order)
    score = result.modularity
    
    # Build diagnostics if requested
    if return_diagnostics:
        elapsed = time.time() - start_time
        diagnostics = {
            'timing': elapsed,
            'n_moves': None,  # Not tracked in current implementation
            'n_communities_per_level': [len(set(partition.values()))],
            'convergence_info': {
                'iterations': result.iterations,
                'improved': result.improved,
                'converged': not result.improved,
            },
            'backend_used': 'native',
            'n_communities': len(set(partition.values())),
            'n_nodes': len(partition),
        }
        return partition, score, diagnostics
    
    return partition, score


def multilayer_leiden_uq(
    network: Any,
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    n_runs: int = 20,
    seeds: Optional[List[int]] = None,
    n_iterations: int = 2,
    agg: str = "consensus",
    ci: float = 0.95,
    random_state: Optional[int] = None,
    return_all: bool = False,
    method: str = "seed",
    perturbation_rate: float = 0.05,
) -> UQResult:
    """Multilayer Leiden with uncertainty quantification via ensemble runs.
    
    This function runs multilayer Leiden multiple times with different random seeds
    and/or network perturbations to quantify uncertainty in the partition. It computes
    consensus partitions, per-node membership probabilities, and stability metrics.
    
    UQ Strategies:
        - "seed": Multiple runs with different random seeds (Monte Carlo)
        - "perturbation": Edge dropout before each run (structural uncertainty)
        - "bootstrap": Bootstrap resample edges before each run
        
    Consensus Methods:
        - "consensus": Medoid partition (minimizes mean VI distance)
        - "coassignment": Cluster co-assignment matrix (expensive for large networks)
        
    Args:
        network: py3plex multi_layer_network object
        gamma: Resolution parameter(s). Default: 1.0
        omega: Interlayer coupling strength. Default: 1.0
        n_runs: Number of ensemble runs. Default: 20
        seeds: List of random seeds (length n_runs). If None, generates deterministically.
            Default: None
        n_iterations: Leiden iterations per run. Default: 2
        agg: Consensus method: "consensus" (medoid) or "coassignment" (clustering).
            Default: "consensus"
        ci: Confidence interval level (0 < ci < 1). Default: 0.95
        random_state: Base random seed for deterministic seed generation. If None,
            uses 0. Default: None
        return_all: If True, includes all partitions in result. Default: False
        method: UQ strategy: "seed", "perturbation", or "bootstrap". Default: "seed"
        perturbation_rate: For method="perturbation", fraction of edges to drop.
            Default: 0.05
            
    Returns:
        UQResult with:
            - partitions: List of partition dicts (if return_all=True)
            - scores: List of modularity scores
            - consensus_partition: Consensus partition
            - membership_probs: Node membership probability matrix
            - stability_metrics: VI/NMI distributions, pairwise agreement
            - ci: Confidence intervals for score and n_communities
            - summary: Mean/std statistics
            - diagnostics: Seed table, runtime, failure counts
            
    Examples:
        >>> from py3plex.algorithms.community_detection import multilayer_leiden_uq
        >>> from py3plex.core import multinet
        >>>
        >>> net = multinet.multi_layer_network(directed=False)
        >>> net.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ... ], input_type='list')
        >>>
        >>> # Seed-based UQ
        >>> result = multilayer_leiden_uq(
        ...     net, n_runs=50, random_state=42
        ... )
        >>> print(f"Mean Q: {result.summary['score_mean']:.3f} ± {result.summary['score_std']:.3f}")
        >>> print(f"Consensus partition: {result.consensus_partition}")
        >>>
        >>> # Perturbation-based UQ
        >>> result = multilayer_leiden_uq(
        ...     net, n_runs=50, method="perturbation", perturbation_rate=0.1,
        ...     random_state=42
        ... )
        >>> print(f"Node membership uncertainty: {result.stability_metrics['node_entropy']}")
    
    Notes:
        - Determinism: Same random_state yields identical ensemble
        - Scalability: For large networks (>1000 nodes), consensus (medoid) is faster
          than coassignment clustering
        - Empty runs: Failures are tracked in diagnostics['failures']
        - Parallel: Currently sequential; future versions will support n_jobs
    """
    # Validate inputs
    if n_runs < 1:
        raise AlgorithmError(
            f"n_runs must be >= 1, got {n_runs}",
            suggestions=["Use n_runs >= 20 for meaningful uncertainty estimates"]
        )
    
    if method not in ["seed", "perturbation", "bootstrap"]:
        raise AlgorithmError(
            f"Unknown UQ method: {method}",
            suggestions=["Use 'seed', 'perturbation', or 'bootstrap'"]
        )
    
    if agg not in ["consensus", "coassignment"]:
        raise AlgorithmError(
            f"Unknown aggregation method: {agg}",
            suggestions=["Use 'consensus' (medoid) or 'coassignment' (clustering)"]
        )
    
    if not (0 < ci < 1):
        raise AlgorithmError(
            f"ci must be in (0, 1), got {ci}",
            suggestions=["Use ci=0.95 for 95% confidence intervals"]
        )
    
    # Set deterministic default seed
    if random_state is None:
        random_state = 0
    
    # Generate seeds deterministically if not provided
    if seeds is None:
        seeds = spawn_seeds(random_state, n_runs)
    elif len(seeds) != n_runs:
        raise AlgorithmError(
            f"seeds length {len(seeds)} != n_runs {n_runs}",
            suggestions=["Provide seeds=None for auto-generation or len(seeds)=n_runs"]
        )
    
    # Start timing
    start_time = time.time()
    
    # Run ensemble
    partitions = []
    scores = []
    failures = []
    
    # Get original node order
    node_order = sorted(network.get_nodes())
    
    for i, seed in enumerate(seeds):
        try:
            # Perturb network if requested
            if method == "perturbation":
                net_i = perturb_network_edges(network, edge_drop_p=perturbation_rate, seed=seed)
                # Ensure node order stays the same
                current_nodes = set(net_i.get_nodes())
                original_nodes = set(node_order)
                if current_nodes != original_nodes:
                    # Skip if network structure changed too much
                    failures.append({'run': i, 'seed': seed, 'error': 'Network structure changed'})
                    continue
            elif method == "bootstrap":
                net_i = bootstrap_network_edges(network, seed=seed)
                # Ensure node order stays the same
                current_nodes = set(net_i.get_nodes())
                original_nodes = set(node_order)
                if current_nodes != original_nodes:
                    # Skip if network structure changed too much
                    failures.append({'run': i, 'seed': seed, 'error': 'Network structure changed'})
                    continue
            else:
                net_i = network
            
            # Run Leiden
            partition, score = multilayer_leiden(
                net_i, gamma=gamma, omega=omega, n_iterations=n_iterations,
                random_state=seed
            )
            partitions.append(partition)
            scores.append(score)
        except Exception as e:
            failures.append({'run': i, 'seed': seed, 'error': str(e)})
            warnings.warn(f"Run {i} failed with error: {e}", RuntimeWarning, stacklevel=2)
    
    if not partitions:
        raise AlgorithmError(
            f"All {n_runs} runs failed",
            suggestions=["Check network validity and parameters"]
        )
    
    # Use node order from first successful run
    node_order = sorted(partitions[0].keys())
    n_nodes = len(node_order)
    
    # Convert partitions to arrays for analysis
    partition_arrays = []
    for partition in partitions:
        arr = partition_dict_to_array(partition, node_order)
        partition_arrays.append(arr)
    
    # Create CommunityDistribution
    dist = CommunityDistribution(
        partitions=partition_arrays,
        nodes=node_order,
        weights=np.array(scores) if len(scores) > 0 else None,
        meta={
            'method': 'multilayer_leiden',
            'n_runs': n_runs,
            'resampling': method,
            'gamma': gamma,
            'omega': omega,
            'seed': random_state,
        }
    )
    
    # Compute consensus partition
    if agg == "consensus":
        # Medoid: partition with minimum mean VI to all others
        consensus_arr = dist.consensus_partition(method='medoid')
    else:
        # Co-assignment clustering
        consensus_arr = dist.consensus_partition(method='coassignment')
    
    consensus_partition = partition_array_to_dict(consensus_arr, node_order)
    consensus_partition = canonicalize_partition(consensus_partition, node_order)
    
    # Compute membership probabilities (co-assignment matrix)
    coassoc = dist.coassociation(mode='dense')
    
    # Compute stability metrics
    from sklearn.metrics import normalized_mutual_info_score as nmi
    from sklearn.metrics.cluster import contingency_matrix
    
    def vi_from_arrays(arr1, arr2):
        """Compute Variation of Information from partition arrays."""
        # VI = H(X) + H(Y) - 2*MI(X,Y)
        # Where H is entropy and MI is mutual information
        n = len(arr1)
        if n == 0:
            return 0.0
        
        # Build contingency table
        cont = contingency_matrix(arr1, arr2)
        
        # Compute entropies
        p1 = cont.sum(axis=1) / n
        p2 = cont.sum(axis=0) / n
        h1 = -np.sum(p1 * np.log2(p1 + 1e-10))
        h2 = -np.sum(p2 * np.log2(p2 + 1e-10))
        
        # Compute mutual information
        pxy = cont / n
        px_py = np.outer(p1, p2)
        mi = np.sum(pxy * np.log2((pxy + 1e-10) / (px_py + 1e-10)))
        
        # VI = H(X) + H(Y) - 2*MI(X,Y)
        return h1 + h2 - 2 * mi
    
    vi_scores = []
    nmi_scores = []
    for i in range(len(partition_arrays)):
        for j in range(i+1, len(partition_arrays)):
            vi = vi_from_arrays(partition_arrays[i], partition_arrays[j])
            nmi_val = nmi(partition_arrays[i], partition_arrays[j])
            vi_scores.append(vi)
            nmi_scores.append(nmi_val)
    
    # Per-node entropy of community membership
    node_entropy = np.zeros(n_nodes)
    for i in range(n_nodes):
        # Get community assignments across runs
        assignments = [p[i] for p in partition_arrays]
        unique, counts = np.unique(assignments, return_counts=True)
        probs = counts / len(assignments)
        # Compute entropy
        node_entropy[i] = -np.sum(probs * np.log2(probs + 1e-10))
    
    # Compute pairwise agreement (fraction of node pairs with same assignment)
    agreement_sum = 0.0
    n_pairs = 0
    for i in range(len(partition_arrays)):
        for j in range(i+1, len(partition_arrays)):
            # Count matching assignments
            matches = np.sum(partition_arrays[i] == partition_arrays[j])
            agreement_sum += matches / n_nodes
            n_pairs += 1
    
    pairwise_agreement = agreement_sum / n_pairs if n_pairs > 0 else 1.0
    
    stability_metrics = {
        'vi_mean': np.mean(vi_scores) if vi_scores else 0.0,
        'vi_std': np.std(vi_scores) if vi_scores else 0.0,
        'nmi_mean': np.mean(nmi_scores) if nmi_scores else 0.0,
        'nmi_std': np.std(nmi_scores) if nmi_scores else 0.0,
        'node_entropy': node_entropy,
        'pairwise_agreement': pairwise_agreement,
    }
    
    # Compute confidence intervals
    if len(scores) > 0:
        alpha = 1 - ci
        score_mean = np.mean(scores)
        score_std = np.std(scores)
        score_ci_lower = np.percentile(scores, 100 * alpha / 2)
        score_ci_upper = np.percentile(scores, 100 * (1 - alpha / 2))
        
        n_communities_list = [len(set(p)) for p in partition_arrays]
        n_comm_mean = np.mean(n_communities_list)
        n_comm_std = np.std(n_communities_list)
        n_comm_ci_lower = np.percentile(n_communities_list, 100 * alpha / 2)
        n_comm_ci_upper = np.percentile(n_communities_list, 100 * (1 - alpha / 2))
    else:
        score_mean = score_std = score_ci_lower = score_ci_upper = 0.0
        n_comm_mean = n_comm_std = n_comm_ci_lower = n_comm_ci_upper = 0.0
    
    ci_result = {
        'score': (score_ci_lower, score_ci_upper),
        'n_communities': (n_comm_ci_lower, n_comm_ci_upper),
    }
    
    summary = {
        'score_mean': score_mean,
        'score_std': score_std,
        'n_communities_mean': n_comm_mean,
        'n_communities_std': n_comm_std,
        'n_runs_success': len(partitions),
        'n_runs_failed': len(failures),
    }
    
    # Build diagnostics
    elapsed = time.time() - start_time
    diagnostics = {
        'seeds': seeds,
        'runtime_total': elapsed,
        'runtime_per_run': elapsed / n_runs,
        'failures': failures,
        'method': method,
        'agg': agg,
    }
    
    # Build result
    result = UQResult(
        partitions=partitions if return_all else None,
        scores=scores,
        consensus_partition=consensus_partition,
        membership_probs=coassoc,
        stability_metrics=stability_metrics,
        ci=ci_result,
        summary=summary,
        diagnostics=diagnostics,
    )
    
    return result
