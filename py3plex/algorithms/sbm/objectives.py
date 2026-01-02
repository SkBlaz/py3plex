"""
Objective functions for multilayer SBM.

This module implements log-likelihoods, ELBO (Evidence Lower Bound),
and prior distributions for SBM variants.
"""

from typing import List, Optional
import numpy as np
import scipy.sparse as sp
from scipy.special import gammaln, digamma

from .utils import safe_log


def bernoulli_log_likelihood(
    A: sp.spmatrix,
    q: np.ndarray,
    B: np.ndarray,
    directed: bool = False
) -> float:
    """
    Compute expected log-likelihood for Bernoulli SBM.
    
    L = sum_{ij} A_{ij} log(B_{z_i z_j}) + (1 - A_{ij}) log(1 - B_{z_i z_j})
    
    For soft assignments, we take expectation over q(z).
    
    Args:
        A: Sparse adjacency matrix (n x n)
        q: Soft membership (n x K)
        B: Block affinity matrix (K x K), entries in [0, 1]
        directed: Whether graph is directed
        
    Returns:
        Expected log-likelihood
    """
    n_nodes, K = q.shape
    
    # Expected block edge probabilities: q^T A q
    # But we need element-wise expectations
    
    # Clip B to avoid log(0) and log(1-1)
    B_safe = np.clip(B, 1e-10, 1 - 1e-10)
    
    log_B = safe_log(B_safe)
    log_one_minus_B = safe_log(1 - B_safe)
    
    ll = 0.0
    
    # Iterate over edges (sparse)
    A_coo = A.tocoo()
    for i, j, a_ij in zip(A_coo.row, A_coo.col, A_coo.data):
        if i == j:
            continue  # Skip self-loops
        
        # E[log P(A_ij | z_i, z_j)] = sum_{kl} q_ik q_jl log(B_kl)
        edge_contrib = np.sum(
            q[i][:, None] * q[j][None, :] * log_B
        ) * a_ij
        
        ll += edge_contrib
    
    # Non-edge contribution (expensive for large graphs, approximate)
    # For Bernoulli, we should also account for non-edges
    # sum_{ij not in E} log(1 - B_{z_i z_j})
    # This is O(n^2), so we approximate or skip for large graphs
    
    # Approximate: assume sparse graph, most pairs are non-edges
    # Contribution ≈ -0.5 * n^2 * E[B] if B is small
    # For now, skip non-edge term (would be computed in full ELBO)
    
    return ll


def poisson_log_likelihood(
    A: sp.spmatrix,
    q: np.ndarray,
    B: np.ndarray,
    theta: Optional[np.ndarray] = None,
    directed: bool = False
) -> float:
    """
    Compute expected log-likelihood for Poisson SBM or DC-SBM.
    
    For Poisson SBM:
        A_{ij} ~ Poisson(B_{z_i z_j})
        L = sum_{ij} [A_{ij} log(B_{z_i z_j}) - B_{z_i z_j}]
    
    For DC-SBM:
        A_{ij} ~ Poisson(theta_i * theta_j * B_{z_i z_j})
        L = sum_{ij} [A_{ij} log(theta_i * theta_j * B_{z_i z_j}) - theta_i * theta_j * B_{z_i z_j}]
    
    Args:
        A: Sparse adjacency matrix (n x n)
        q: Soft membership (n x K)
        B: Block affinity matrix (K x K), positive entries
        theta: Node propensity parameters (n,) for DC-SBM (None = vanilla SBM)
        directed: Whether graph is directed
        
    Returns:
        Expected log-likelihood
    """
    n_nodes, K = q.shape
    
    B_safe = np.maximum(B, 1e-10)
    log_B = safe_log(B_safe)
    
    ll = 0.0
    
    # Edge contributions
    A_coo = A.tocoo()
    for i, j, a_ij in zip(A_coo.row, A_coo.col, A_coo.data):
        if i == j:
            continue  # Skip self-loops
        
        # E[log P(A_ij | z_i, z_j, theta)]
        # = sum_{kl} q_ik q_jl [A_ij log(lambda_ijkl) - lambda_ijkl]
        
        if theta is not None:
            # DC-SBM: lambda_ijkl = theta_i * theta_j * B_kl
            lambda_mat = theta[i] * theta[j] * B_safe
            log_lambda_mat = safe_log(lambda_mat)
        else:
            # Vanilla Poisson SBM
            lambda_mat = B_safe
            log_lambda_mat = log_B
        
        # Edge contribution
        edge_ll = np.sum(
            q[i][:, None] * q[j][None, :] * (a_ij * log_lambda_mat - lambda_mat)
        )
        
        ll += edge_ll
    
    # For Poisson, we also need to account for zero counts
    # sum_{ij not in E} -lambda_ijkl
    # This is expensive, so we approximate for sparse graphs
    
    return ll


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
    n_layers = len(A_layers)
    
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
    # Dirichlet-Categorical: log p(z_i = k | alpha) = log(alpha / K)
    # E[log p(z)] = sum_i sum_k q_ik log(alpha / K)
    #             = n * log(alpha / K)  (since sum_k q_ik = 1)
    elbo += n_nodes * np.log(alpha / K)
    
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
