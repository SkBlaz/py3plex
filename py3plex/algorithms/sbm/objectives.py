"""
Objective functions for multilayer SBM.

This module implements log-likelihoods, ELBO (Evidence Lower Bound),
and prior distributions for SBM variants.
"""

from typing import List, Optional
import numpy as np
import scipy.sparse as sp
from scipy.special import gammaln

from .utils import safe_log


def _dyad_exposure(q):
    """Expected block assignments over ordered off-diagonal dyads."""
    mass = q.sum(axis=0)
    return np.outer(mass, mass) - q.T @ q


def _block_edges(A, q):
    """Expected block assignments weighted by off-diagonal edge counts."""
    return q.T @ (A @ q - A.diagonal()[:, None] * q)


def bernoulli_log_likelihood(
    A: sp.spmatrix, q: np.ndarray, B: np.ndarray, directed: bool = False
) -> float:
    """Expected Bernoulli log-likelihood over every off-diagonal dyad."""
    edge_counts = _block_edges(A, q)
    non_edges = _dyad_exposure(q) - edge_counts
    probability = np.clip(B, 1e-10, 1 - 1e-10)
    value = np.sum(edge_counts * np.log(probability) + non_edges * np.log1p(-probability))
    return float(value if directed else value / 2)


def poisson_log_likelihood(
    A: sp.spmatrix, q: np.ndarray, B: np.ndarray,
    theta: Optional[np.ndarray] = None, directed: bool = False,
) -> float:
    """Expected Poisson log-likelihood over every off-diagonal dyad."""
    weighted_q = q if theta is None else q * theta[:, None]
    rate = np.maximum(B, 1e-10)
    value = np.sum(_block_edges(A, q) * np.log(rate) - _dyad_exposure(weighted_q) * rate)
    edges = A.tocoo()
    off_diagonal = edges.row != edges.col
    counts = edges.data[off_diagonal]
    value -= gammaln(counts + 1).sum()
    if theta is not None:
        log_theta = safe_log(theta)
        value += counts @ (log_theta[edges.row[off_diagonal]] + log_theta[edges.col[off_diagonal]])
    return float(value if directed else value / 2)


def compute_elbo(
    A_layers: List[sp.spmatrix],
    q: np.ndarray,
    B_layers: List[np.ndarray],
    theta: Optional[np.ndarray] = None,
    model: str = "sbm",
    likelihood: str = "poisson",
    directed: bool = False,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma_shape: float = 1.0,
    gamma_rate: float = 1.0
) -> float:
    """
    Compute Evidence Lower Bound (ELBO) for multilayer SBM.
    
    ELBO = E[log p(A, z, theta | params)] - E[log q(z, theta)]
         = E[log p(A | z, theta, B)] + E[log p(z | alpha)] + E[log p(theta | gamma)]
           - E[log q(z)] - E[log q(theta)]
    
    Args:
        A_layers: List of sparse adjacency matrices (one per layer)
        q: Soft membership (n x K)
        B_layers: List of block affinity matrices (one per layer or shared)
        theta: Node propensities for DC-SBM (n,)
        model: "sbm" or "dc_sbm"
        likelihood: "bernoulli" or "poisson"
        directed: Whether graphs are directed
        alpha: Dirichlet prior parameter for block assignments
        beta: Prior parameter for block affinities
        gamma_shape: Gamma prior shape for theta (DC-SBM)
        gamma_rate: Gamma prior rate for theta (DC-SBM)
        
    Returns:
        ELBO value
    """
    n_nodes, K = q.shape
    
    elbo = 0.0
    
    # 1. Expected log-likelihood: E[log p(A | z, theta, B)]
    for l, A_l in enumerate(A_layers):
        B_l = B_layers[l] if len(B_layers) > 1 else B_layers[0]
        
        if likelihood == "poisson":
            ll = poisson_log_likelihood(A_l, q, B_l, theta, directed)
        else:
            ll = bernoulli_log_likelihood(A_l, q, B_l, directed)
        
        elbo += ll
    
    # 2. Prior on z: E[log p(z | alpha)]
    # A symmetric categorical prior assigns probability 1/K to each label.
    elbo -= n_nodes * np.log(K)
    
    # 3. Entropy of q(z): -E[log q(z)]
    # H(q) = -sum_i sum_k q_ik log(q_ik)
    q_safe = np.maximum(q, 1e-10)
    entropy_q = -np.sum(q * np.log(q_safe))
    elbo += entropy_q
    
    # 4. DC-SBM: Prior and entropy for theta
    if model == "dc_sbm" and theta is not None:
        # Prior: p(theta_i) = Gamma(theta_i | gamma_shape, gamma_rate)
        # E[log p(theta)] = sum_i [(gamma_shape - 1) log(theta_i) - gamma_rate * theta_i]
        #                   + const
        theta_safe = np.maximum(theta, 1e-10)
        log_prior_theta = np.sum(
            (gamma_shape - 1) * np.log(theta_safe) - gamma_rate * theta_safe
        )
        elbo += log_prior_theta
        
        # Entropy of q(theta): assume q(theta) = delta(theta_hat)
        # For point estimates, entropy is 0
        # If we had variational distribution, would add entropy here
    
    # 5. Prior on B (simplified, beta prior)
    # For now, assume uniform or weakly informative prior
    # Could add: sum_{kl} (beta - 1) log(B_kl)
    
    return elbo


def kl_divergence_dirichlet(q: np.ndarray, alpha: float) -> float:
    """
    Compute KL divergence between q(z) and Dirichlet-Categorical prior.
    
    Args:
        q: Soft membership (n x K)
        alpha: Dirichlet concentration parameter
        
    Returns:
        KL divergence
    """
    n_nodes, K = q.shape
    
    q_safe = np.maximum(q, 1e-10)
    
    # KL(q || p) = E_q[log q - log p]
    # For categorical with uniform Dirichlet:
    # = sum_i sum_k q_ik [log(q_ik) - log(1/K)]
    # = sum_i sum_k q_ik log(q_ik) + n * log(K)
    
    kl = np.sum(q * np.log(q_safe)) + n_nodes * np.log(K)
    
    return kl
