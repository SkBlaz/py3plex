"""Partition distance metrics for comparing community structures.

This module provides distance metrics for comparing partitions:
- Variation of Information (VI)
- Normalized Mutual Information (NMI)
- Adjusted Rand Index (ARI)

These metrics are used in PartitionUQ to quantify stability.

Examples
--------
>>> import numpy as np
>>> from py3plex.uncertainty.partition_metrics import variation_of_information, nmi
>>> 
>>> p1 = np.array([0, 0, 1, 1])
>>> p2 = np.array([0, 0, 0, 1])
>>> 
>>> vi = variation_of_information(p1, p2)
>>> nmi_val = nmi(p1, p2)
"""

from __future__ import annotations

from typing import Dict, Tuple
import warnings

import numpy as np


def variation_of_information(
    partition1: np.ndarray,
    partition2: np.ndarray,
    normalized: bool = False
) -> float:
    """Compute Variation of Information between two partitions.
    
    VI(X, Y) = H(X) + H(Y) - 2*I(X, Y)
    
    where H is entropy and I is mutual information.
    
    VI is:
    - Symmetric: VI(X, Y) = VI(Y, X)
    - Non-negative: VI(X, Y) >= 0
    - Zero iff partitions are identical (up to label permutation)
    - Bounded by 2*log(n) where n is number of elements
    
    Parameters
    ----------
    partition1 : np.ndarray
        First partition, shape (n,) with integer labels
    partition2 : np.ndarray
        Second partition, shape (n,) with integer labels
    normalized : bool, default=False
        If True, normalize by log(n) to get value in [0, 2]
        
    Returns
    -------
    float
        Variation of information distance
        
    Examples
    --------
    >>> p1 = np.array([0, 0, 1, 1])
    >>> p2 = np.array([0, 0, 0, 1])
    >>> vi = variation_of_information(p1, p2)
    >>> vi > 0  # Different partitions
    True
    >>> 
    >>> p3 = np.array([5, 5, 7, 7])  # Same structure, different labels
    >>> vi2 = variation_of_information(p1, p3)
    >>> abs(vi2) < 1e-10  # Should be zero (label-invariant)
    True
    """
    if len(partition1) != len(partition2):
        raise ValueError(
            f"Partitions must have same length: {len(partition1)} != {len(partition2)}"
        )
    
    n = len(partition1)
    if n == 0:
        return 0.0
    
    # Build contingency table
    c1_max = int(partition1.max()) + 1
    c2_max = int(partition2.max()) + 1
    contingency = np.zeros((c1_max, c2_max), dtype=int)
    
    for i in range(n):
        contingency[int(partition1[i]), int(partition2[i])] += 1
    
    # Compute marginal probabilities
    p_i = contingency.sum(axis=1) / n  # P(C1=i)
    p_j = contingency.sum(axis=0) / n  # P(C2=j)
    p_ij = contingency / n  # P(C1=i, C2=j)
    
    # Compute entropies
    # H(X) = -sum_i p_i log(p_i)
    h1 = -np.sum(p_i[p_i > 0] * np.log(p_i[p_i > 0]))
    h2 = -np.sum(p_j[p_j > 0] * np.log(p_j[p_j > 0]))
    
    # Compute mutual information
    # I(X, Y) = sum_ij p_ij log(p_ij / (p_i * p_j))
    mi = 0.0
    for i in range(c1_max):
        for j in range(c2_max):
            if p_ij[i, j] > 0 and p_i[i] > 0 and p_j[j] > 0:
                mi += p_ij[i, j] * np.log(p_ij[i, j] / (p_i[i] * p_j[j]))
    
    # VI = H(X) + H(Y) - 2*I(X, Y)
    vi = h1 + h2 - 2 * mi
    
    if normalized:
        # Normalize by log(n)
        if n > 1:
            vi = vi / np.log(n)
    
    return float(vi)


def normalized_mutual_information(
    partition1: np.ndarray,
    partition2: np.ndarray,
    method: str = "arithmetic"
) -> float:
    """Compute Normalized Mutual Information between two partitions.
    
    NMI normalizes mutual information by the arithmetic or geometric
    mean of the entropies.
    
    NMI is:
    - Symmetric
    - In range [0, 1]
    - 1 iff partitions are identical (up to label permutation)
    - 0 if independent
    
    Parameters
    ----------
    partition1 : np.ndarray
        First partition, shape (n,) with integer labels
    partition2 : np.ndarray
        Second partition, shape (n,) with integer labels
    method : str, default="arithmetic"
        Normalization method:
        - "arithmetic": 2*I(X,Y) / (H(X) + H(Y))
        - "geometric": I(X,Y) / sqrt(H(X) * H(Y))
        - "max": I(X,Y) / max(H(X), H(Y))
        - "min": I(X,Y) / min(H(X), H(Y))
        
    Returns
    -------
    float
        Normalized mutual information in [0, 1]
        
    Examples
    --------
    >>> p1 = np.array([0, 0, 1, 1])
    >>> p2 = np.array([0, 0, 0, 1])
    >>> nmi_val = normalized_mutual_information(p1, p2)
    >>> 0 <= nmi_val <= 1
    True
    """
    if len(partition1) != len(partition2):
        raise ValueError(
            f"Partitions must have same length: {len(partition1)} != {len(partition2)}"
        )
    
    n = len(partition1)
    if n == 0:
        return 1.0  # Empty partitions are considered identical
    
    # Build contingency table
    c1_max = int(partition1.max()) + 1
    c2_max = int(partition2.max()) + 1
    contingency = np.zeros((c1_max, c2_max), dtype=int)
    
    for i in range(n):
        contingency[int(partition1[i]), int(partition2[i])] += 1
    
    # Compute marginal probabilities
    p_i = contingency.sum(axis=1) / n
    p_j = contingency.sum(axis=0) / n
    p_ij = contingency / n
    
    # Compute entropies
    h1 = -np.sum(p_i[p_i > 0] * np.log(p_i[p_i > 0]))
    h2 = -np.sum(p_j[p_j > 0] * np.log(p_j[p_j > 0]))
    
    # Handle edge case: if both partitions are trivial (all same label)
    if h1 == 0 and h2 == 0:
        return 1.0
    
    # Compute mutual information
    mi = 0.0
    for i in range(c1_max):
        for j in range(c2_max):
            if p_ij[i, j] > 0 and p_i[i] > 0 and p_j[j] > 0:
                mi += p_ij[i, j] * np.log(p_ij[i, j] / (p_i[i] * p_j[j]))
    
    # Normalize
    if method == "arithmetic":
        denom = (h1 + h2) / 2
        if denom == 0:
            return 1.0 if mi == 0 else 0.0
        nmi_val = mi / denom
    elif method == "geometric":
        denom = np.sqrt(h1 * h2)
        if denom == 0:
            return 1.0 if mi == 0 else 0.0
        nmi_val = mi / denom
    elif method == "max":
        denom = max(h1, h2)
        if denom == 0:
            return 1.0 if mi == 0 else 0.0
        nmi_val = mi / denom
    elif method == "min":
        denom = min(h1, h2) if min(h1, h2) > 0 else max(h1, h2)
        if denom == 0:
            return 1.0 if mi == 0 else 0.0
        nmi_val = mi / denom
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    # Clip to [0, 1] to handle numerical errors
    nmi_val = np.clip(nmi_val, 0.0, 1.0)
    
    return float(nmi_val)


def adjusted_rand_index(
    partition1: np.ndarray,
    partition2: np.ndarray
) -> float:
    """Compute Adjusted Rand Index between two partitions.
    
    ARI measures the similarity between two clusterings adjusted for chance.
    
    ARI is:
    - Symmetric
    - Bounded by 1 (perfect agreement)
    - Expected value 0 for random partitions
    - Can be negative
    
    Parameters
    ----------
    partition1 : np.ndarray
        First partition, shape (n,) with integer labels
    partition2 : np.ndarray
        Second partition, shape (n,) with integer labels
        
    Returns
    -------
    float
        Adjusted Rand Index
        
    Examples
    --------
    >>> p1 = np.array([0, 0, 1, 1])
    >>> p2 = np.array([0, 0, 0, 1])
    >>> ari = adjusted_rand_index(p1, p2)
    >>> -1 <= ari <= 1
    True
    """
    if len(partition1) != len(partition2):
        raise ValueError(
            f"Partitions must have same length: {len(partition1)} != {len(partition2)}"
        )
    
    try:
        from sklearn.metrics import adjusted_rand_score
        return float(adjusted_rand_score(partition1, partition2))
    except ImportError:
        warnings.warn(
            "sklearn not available, cannot compute adjusted_rand_index. "
            "Returning 0.0 as fallback.",
            stacklevel=2
        )
        return 0.0


# Aliases for convenience
vi = variation_of_information
nmi = normalized_mutual_information
ari = adjusted_rand_index


def pairwise_partition_distances(
    partitions: list[np.ndarray],
    metric: str = "vi"
) -> np.ndarray:
    """Compute pairwise distances between partitions.
    
    Parameters
    ----------
    partitions : list of np.ndarray
        List of partition arrays
    metric : str, default="vi"
        Distance metric: "vi", "nmi", or "ari"
        
    Returns
    -------
    np.ndarray
        Distance matrix, shape (n_partitions, n_partitions)
        
    Examples
    --------
    >>> partitions = [
    ...     np.array([0, 0, 1, 1]),
    ...     np.array([0, 0, 0, 1]),
    ...     np.array([0, 1, 0, 1]),
    ... ]
    >>> D = pairwise_partition_distances(partitions, metric="vi")
    >>> D.shape
    (3, 3)
    >>> np.allclose(D.diagonal(), 0)  # Diagonal is zero
    True
    """
    n = len(partitions)
    D = np.zeros((n, n))
    
    metric_func = {
        "vi": variation_of_information,
        "nmi": lambda p1, p2: 1 - normalized_mutual_information(p1, p2),
        "ari": lambda p1, p2: 1 - adjusted_rand_index(p1, p2),
    }.get(metric)
    
    if metric_func is None:
        raise ValueError(f"Unknown metric: {metric}")
    
    for i in range(n):
        for j in range(i + 1, n):
            d = metric_func(partitions[i], partitions[j])
            D[i, j] = d
            D[j, i] = d
    
    return D
