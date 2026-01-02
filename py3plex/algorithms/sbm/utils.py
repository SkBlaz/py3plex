"""
Utility functions for multilayer SBM.

This module provides sparse matrix operations, initialization strategies,
and evaluation metrics for the SBM implementation.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def safe_log(x: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """
    Compute log safely, replacing log(0) with log(eps).
    
    Args:
        x: Input array
        eps: Small positive value to replace zeros
        
    Returns:
        Log of input with safe handling of zeros
    """
    return np.log(np.maximum(x, eps))


def log_sum_exp(x: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
    """
    Numerically stable log-sum-exp computation.
    
    Args:
        x: Input array
        axis: Axis along which to sum
        
    Returns:
        log(sum(exp(x))) computed stably
    """
    x_max = np.max(x, axis=axis, keepdims=True)
    return x_max.squeeze() + np.log(np.sum(np.exp(x - x_max), axis=axis))


def sparse_degree(A: sp.spmatrix, directed: bool = False) -> np.ndarray:
    """
    Compute node degrees from sparse adjacency matrix.
    
    Args:
        A: Sparse adjacency matrix (n x n)
        directed: If True, compute out-degrees; else sum of in+out
        
    Returns:
        Degree array of shape (n,)
    """
    if directed:
        degrees = np.asarray(A.sum(axis=1)).flatten()
    else:
        # For undirected, sum both directions and divide by 2 (edges counted twice)
        degrees = np.asarray(A.sum(axis=1)).flatten()
        degrees += np.asarray(A.sum(axis=0)).flatten()
        degrees = degrees / 2.0
    return degrees


def sparse_edge_count(A: sp.spmatrix, directed: bool = False) -> int:
    """
    Count total number of edges in sparse adjacency matrix.
    
    Args:
        A: Sparse adjacency matrix
        directed: If True, count directed edges; else undirected
        
    Returns:
        Number of edges
    """
    nnz = A.nnz
    if not directed:
        # For undirected, each edge is stored twice (symmetric)
        nnz = nnz // 2
    return nnz


def init_random_soft_membership(
    n_nodes: int, 
    n_blocks: int, 
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Initialize random soft membership probabilities.
    
    Args:
        n_nodes: Number of nodes
        n_blocks: Number of blocks/communities
        seed: Random seed
        
    Returns:
        Soft membership matrix of shape (n_nodes, n_blocks) with rows summing to 1
    """
    rng = np.random.RandomState(seed)
    q = rng.rand(n_nodes, n_blocks)
    q = q / q.sum(axis=1, keepdims=True)
    return q


def init_kmeans_membership(
    A_layers: List[sp.spmatrix],
    n_blocks: int,
    n_components: Optional[int] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Initialize membership using k-means on aggregated adjacency features.
    
    Args:
        A_layers: List of sparse adjacency matrices (one per layer)
        n_blocks: Number of blocks/communities
        n_components: Number of features to extract (default: min(100, n_nodes))
        seed: Random seed
        
    Returns:
        Soft membership matrix of shape (n_nodes, n_blocks)
    """
    n_nodes = A_layers[0].shape[0]
    if n_components is None:
        n_components = min(100, n_nodes)
    
    # Aggregate adjacency across layers
    A_agg = sum(A_layers)
    
    # Use simple degree-based features if small, else use low-rank representation
    if n_nodes <= n_components:
        # Use adjacency rows directly
        features = A_agg.toarray()
    else:
        # Use row sums as simple features
        # For larger graphs, could use SVD/eigenvectors (optional enhancement)
        features = np.asarray(A_agg.sum(axis=1))
    
    # K-means clustering
    kmeans = KMeans(n_clusters=n_blocks, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(features)
    
    # Convert hard labels to soft membership
    q = np.zeros((n_nodes, n_blocks))
    q[np.arange(n_nodes), labels] = 1.0
    
    return q


def init_spectral_membership(
    A_layers: List[sp.spmatrix],
    n_blocks: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Initialize membership using spectral clustering on aggregated Laplacian.
    
    Args:
        A_layers: List of sparse adjacency matrices
        n_blocks: Number of blocks/communities
        seed: Random seed
        
    Returns:
        Soft membership matrix of shape (n_nodes, n_blocks)
    """
    from scipy.sparse.linalg import eigsh
    
    n_nodes = A_layers[0].shape[0]
    
    # Aggregate adjacency
    A_agg = sum(A_layers)
    
    # Compute normalized Laplacian: L = I - D^{-1/2} A D^{-1/2}
    degrees = sparse_degree(A_agg, directed=False)
    degrees = np.maximum(degrees, 1e-10)  # Avoid division by zero
    
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(degrees))
    L_norm = sp.eye(n_nodes) - D_inv_sqrt @ A_agg @ D_inv_sqrt
    
    # Compute smallest eigenvectors
    try:
        # Ask for n_blocks smallest eigenvalues
        k = min(n_blocks + 1, n_nodes - 2)
        eigenvalues, eigenvectors = eigsh(L_norm.tocsc(), k=k, which='SM')
        
        # Use first n_blocks eigenvectors
        embedding = eigenvectors[:, :n_blocks]
        
        # K-means on spectral embedding
        kmeans = KMeans(n_clusters=n_blocks, random_state=seed, n_init=10)
        labels = kmeans.fit_predict(embedding)
        
    except Exception:
        # Fallback to random if spectral fails
        return init_random_soft_membership(n_nodes, n_blocks, seed)
    
    # Convert to soft membership
    q = np.zeros((n_nodes, n_blocks))
    q[np.arange(n_nodes), labels] = 1.0
    
    return q


def compute_ari(pred_labels: np.ndarray, true_labels: np.ndarray) -> float:
    """
    Compute Adjusted Rand Index between predicted and true labels.
    
    Args:
        pred_labels: Predicted cluster labels
        true_labels: Ground truth labels
        
    Returns:
        ARI score in [-1, 1], where 1 is perfect agreement
    """
    return adjusted_rand_score(true_labels, pred_labels)


def compute_nmi(pred_labels: np.ndarray, true_labels: np.ndarray) -> float:
    """
    Compute Normalized Mutual Information between predicted and true labels.
    
    Args:
        pred_labels: Predicted cluster labels
        true_labels: Ground truth labels
        
    Returns:
        NMI score in [0, 1], where 1 is perfect agreement
    """
    return normalized_mutual_info_score(true_labels, pred_labels)


def node_entropy(q: np.ndarray) -> np.ndarray:
    """
    Compute entropy of soft membership distributions.
    
    Higher entropy indicates more uncertainty in block assignment.
    
    Args:
        q: Soft membership matrix (n_nodes, n_blocks)
        
    Returns:
        Entropy array of shape (n_nodes,)
    """
    # Avoid log(0)
    q_safe = np.maximum(q, 1e-10)
    return -np.sum(q * np.log(q_safe), axis=1)


def membership_confidence(q: np.ndarray) -> np.ndarray:
    """
    Compute confidence of block assignments (max probability).
    
    Args:
        q: Soft membership matrix (n_nodes, n_blocks)
        
    Returns:
        Confidence array of shape (n_nodes,)
    """
    return np.max(q, axis=1)
