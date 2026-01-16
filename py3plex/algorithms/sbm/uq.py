"""
Uncertainty quantification for SBM.

This module provides functions for:
- Label alignment across multiple runs (Hungarian algorithm)
- Per-node stability analysis
- Seed-based resampling UQ
- Deterministic reproducibility
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import spmatrix

from .multilayer_sbm import fit_single_sbm, SBMFittedModel


def align_labels_hungarian(
    partitions: List[np.ndarray],
    reference_idx: int = 0
) -> Tuple[List[np.ndarray], np.ndarray]:
    """
    Align labels across multiple partitions using the Hungarian algorithm.
    
    This function solves the label correspondence problem by finding the
    optimal permutation of labels that maximizes agreement with a reference
    partition.
    
    Args:
        partitions: List of hard partition arrays (each n_nodes,)
        reference_idx: Index of partition to use as reference (default: 0)
        
    Returns:
        Tuple of (aligned_partitions, alignment_cost)
        - aligned_partitions: List of aligned partition arrays
        - alignment_cost: Array of alignment costs (higher = more permutation needed)
        
    Example:
        >>> p1 = np.array([0, 0, 1, 1, 2])
        >>> p2 = np.array([1, 1, 0, 0, 2])  # Labels 0 and 1 swapped
        >>> aligned, costs = align_labels_hungarian([p1, p2])
        >>> assert np.array_equal(aligned[0], aligned[1])
    """
    if len(partitions) == 0:
        return [], np.array([])
    
    if len(partitions) == 1:
        return partitions, np.array([0.0])
    
    reference = partitions[reference_idx]
    n_nodes = len(reference)
    K_ref = reference.max() + 1
    
    aligned = [reference.copy()]
    costs = [0.0]
    
    for i, partition in enumerate(partitions):
        if i == reference_idx:
            continue
        
        K_part = partition.max() + 1
        K_max = max(K_ref, K_part)
        
        # Build contingency matrix: C[k_ref, k_part] = number of nodes with (ref=k_ref, part=k_part)
        contingency = np.zeros((K_max, K_max))
        for k_ref in range(K_ref):
            for k_part in range(K_part):
                contingency[k_ref, k_part] = np.sum((reference == k_ref) & (partition == k_part))
        
        # Hungarian algorithm finds minimum cost assignment
        # We want maximum overlap, so negate the contingency matrix
        cost_matrix = -contingency
        
        # Solve assignment problem
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # Create label mapping
        label_map = np.arange(K_max)  # Default: identity mapping
        for k_ref, k_part in zip(row_ind, col_ind):
            label_map[k_part] = k_ref
        
        # Apply mapping
        aligned_partition = label_map[partition]
        aligned.append(aligned_partition)
        
        # Compute alignment cost (number of misaligned nodes)
        cost = n_nodes - np.sum(aligned_partition == reference)
        costs.append(float(cost))
    
    return aligned, np.array(costs)


def compute_node_stability(
    partitions: List[np.ndarray],
    method: str = "entropy"
) -> np.ndarray:
    """
    Compute per-node stability across multiple partitions.
    
    Args:
        partitions: List of aligned partition arrays (each n_nodes,)
        method: Stability measure - "entropy" or "variance" (default: "entropy")
        
    Returns:
        Array of per-node stability scores (n_nodes,)
        - For entropy: 0 = always same community, higher = more variation
        - For variance: 0 = stable, higher = unstable
        
    Example:
        >>> p1 = np.array([0, 0, 1, 1])
        >>> p2 = np.array([0, 0, 1, 2])  # Last node unstable
        >>> stability = compute_node_stability([p1, p2], method="entropy")
        >>> assert stability[0] < stability[3]  # First node more stable
    """
    n_nodes = len(partitions[0])
    n_samples = len(partitions)
    
    if n_samples == 1:
        return np.zeros(n_nodes)
    
    if method == "entropy":
        # Compute Shannon entropy of community assignments per node
        stability = np.zeros(n_nodes)
        
        for i in range(n_nodes):
            # Get community assignments for node i across samples
            assignments = np.array([p[i] for p in partitions])
            
            # Count frequency of each community
            unique, counts = np.unique(assignments, return_counts=True)
            probs = counts / n_samples
            
            # Compute entropy: H = -sum(p * log(p))
            entropy = -np.sum(probs * np.log(probs + 1e-10))
            stability[i] = entropy
        
        return stability
    
    elif method == "variance":
        # Compute variance of community assignments
        # (useful when K is consistent across samples)
        stability = np.zeros(n_nodes)
        
        for i in range(n_nodes):
            assignments = np.array([p[i] for p in partitions])
            stability[i] = np.var(assignments)
        
        return stability
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'entropy' or 'variance'.")


def sbm_seed_resampling_uq(
    A_layers: List[spmatrix],
    K: int,
    layers: List[str],
    node_to_idx: Dict[Any, int],
    n_samples: int = 10,
    master_seed: int = 0,
    model: str = "dc_sbm",
    layer_mode: str = "independent",
    directed: bool = False,
    init: str = "spectral",
    max_iter: int = 500,
    tol: float = 1e-5,
    verbose: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Run SBM multiple times with different random seeds for UQ.
    
    This function provides deterministic UQ by:
    1. Using numpy.random.Generator with PCG64 for reproducibility
    2. Spawning child seeds using SeedSequence.spawn()
    3. Running SBM with each child seed
    4. Aligning labels using Hungarian algorithm
    5. Computing node stability metrics
    
    Args:
        A_layers: List of sparse adjacency matrices
        K: Number of blocks
        layers: Layer names
        node_to_idx: Node to index mapping
        n_samples: Number of resampling runs (default: 10)
        master_seed: Master random seed (default: 0)
        model: "sbm" or "dc_sbm"
        layer_mode: "independent", "shared_blocks", "shared_affinity", or "coupled"
        directed: Whether directed
        init: Initialization method
        max_iter: Maximum iterations per fit
        tol: Convergence tolerance
        verbose: Print progress
        **kwargs: Additional parameters for fit_single_sbm
        
    Returns:
        Dictionary with:
        - models: List of fitted SBMFittedModel objects
        - aligned_partitions: List of aligned hard partition arrays
        - alignment_costs: Array of alignment costs
        - node_stability: Array of per-node stability (entropy)
        - consensus_partition: Consensus partition (mode across samples)
        - consensus_confidence: Per-node confidence (fraction agreeing with consensus)
        - soft_membership_mean: Mean soft membership across samples (n_nodes x K)
        - soft_membership_std: Std soft membership across samples (n_nodes x K)
        
        Note: soft_membership statistics are computed WITHOUT label alignment,
        which may produce incorrect results when labels are permuted across runs.
        For accurate soft membership statistics, manual alignment is required.
        
    Example:
        >>> uq_result = sbm_seed_resampling_uq(
        ...     A_layers, K=3, layers=layers, node_to_idx=node_to_idx,
        ...     n_samples=50, master_seed=42, model="dc_sbm"
        ... )
        >>> print(uq_result['node_stability'])  # Per-node stability
        >>> print(uq_result['consensus_partition'])  # Consensus partition
    """
    # Create seed sequence for reproducible child seeds
    from numpy.random import SeedSequence, Generator, PCG64
    
    ss = SeedSequence(master_seed)
    child_seeds = ss.spawn(n_samples)
    
    if verbose:
        print(f"Running {n_samples} SBM fits with different seeds...")
    
    models = []
    partitions = []
    soft_memberships = []
    
    for i, child_ss in enumerate(child_seeds):
        # Generate integer seed from SeedSequence
        seed = Generator(PCG64(child_ss)).integers(0, 2**31 - 1)
        
        if verbose and (i + 1) % max(1, n_samples // 10) == 0:
            print(f"  Sample {i+1}/{n_samples}")
        
        # Fit model with this seed
        model = fit_single_sbm(
            A_layers=A_layers,
            K=K,
            layers=layers,
            node_to_idx=node_to_idx,
            model=model,
            layer_mode=layer_mode,
            directed=directed,
            init=init,
            seed=seed,
            max_iter=max_iter,
            tol=tol,
            verbose=False,
            **kwargs
        )
        
        models.append(model)
        partitions.append(model.hard_membership_)
        soft_memberships.append(model.memberships_)
    
    # Align labels using first partition as reference
    aligned_partitions, alignment_costs = align_labels_hungarian(partitions, reference_idx=0)
    
    # Compute node stability
    node_stability = compute_node_stability(aligned_partitions, method="entropy")
    
    # Compute consensus partition (mode)
    n_nodes = len(aligned_partitions[0])
    consensus_partition = np.zeros(n_nodes, dtype=int)
    consensus_confidence = np.zeros(n_nodes)
    
    for i in range(n_nodes):
        assignments = np.array([p[i] for p in aligned_partitions])
        unique, counts = np.unique(assignments, return_counts=True)
        consensus_partition[i] = unique[np.argmax(counts)]
        consensus_confidence[i] = counts.max() / n_samples
    
    # Compute mean and std of soft memberships
    # TODO: Apply label permutations to align soft memberships before aggregating
    # For now, compute statistics without alignment (may be incorrect if labels are permuted)
    soft_membership_mean = np.mean(soft_memberships, axis=0)
    soft_membership_std = np.std(soft_memberships, axis=0)
    
    if verbose:
        print(f"UQ complete. Mean stability (entropy): {node_stability.mean():.4f}")
        print(f"Mean consensus confidence: {consensus_confidence.mean():.4f}")
    
    return {
        'models': models,
        'aligned_partitions': aligned_partitions,
        'alignment_costs': alignment_costs,
        'node_stability': node_stability,
        'consensus_partition': consensus_partition,
        'consensus_confidence': consensus_confidence,
        'soft_membership_mean': soft_membership_mean,
        'soft_membership_std': soft_membership_std,
        'n_samples': n_samples,
        'master_seed': master_seed,
    }


def compute_co_assignment_matrix(
    partitions: List[np.ndarray]
) -> np.ndarray:
    """
    Compute co-assignment matrix across multiple partitions.
    
    C[i, j] = fraction of times nodes i and j are in the same community
    
    Args:
        partitions: List of aligned partition arrays (each n_nodes,)
        
    Returns:
        Co-assignment matrix (n_nodes x n_nodes)
    """
    n_nodes = len(partitions[0])
    n_samples = len(partitions)
    
    co_assignment = np.zeros((n_nodes, n_nodes))
    
    for partition in partitions:
        for i in range(n_nodes):
            for j in range(i, n_nodes):
                if partition[i] == partition[j]:
                    co_assignment[i, j] += 1
                    if i != j:
                        co_assignment[j, i] += 1
    
    co_assignment /= n_samples
    
    return co_assignment


__all__ = [
    'align_labels_hungarian',
    'compute_node_stability',
    'sbm_seed_resampling_uq',
    'compute_co_assignment_matrix',
]
