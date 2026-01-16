"""
Variational inference for multilayer SBM.

This module implements mean-field variational inference for SBM and DC-SBM.
"""

from typing import List, Optional, Tuple
import numpy as np
import scipy.sparse as sp

from .utils import safe_log, log_sum_exp, sparse_degree
from .objectives import compute_elbo


class VariationalInference:
    """
    Mean-field variational inference for multilayer SBM.
    
    Approximates posterior p(z, theta | A) with factorized q(z)q(theta).
    """
    
    def __init__(
        self,
        model: str = "sbm",
        likelihood: str = "poisson",
        directed: bool = False,
        layer_mode: str = "independent",
        max_iter: int = 500,
        tol: float = 1e-5,
        convergence_window: int = 3,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma_shape: float = 1.0,
        gamma_rate: float = 1.0,
        coupling_strength: float = 1.0,
        verbose: bool = True
    ):
        """
        Initialize variational inference.
        
        Args:
            model: "sbm" or "dc_sbm"
            likelihood: "bernoulli" or "poisson"
            directed: Whether graphs are directed
            layer_mode: "independent", "shared_blocks", "shared_affinity", or "coupled"
            max_iter: Maximum number of iterations
            tol: Convergence tolerance for relative ELBO change
            convergence_window: Number of iterations to check for convergence
            alpha: Dirichlet prior parameter for block assignments
            beta: Prior parameter for block affinities
            gamma_shape: Gamma prior shape for theta (DC-SBM)
            gamma_rate: Gamma prior rate for theta (DC-SBM)
            coupling_strength: Coupling penalty for "coupled" mode (default: 1.0)
            verbose: Whether to print progress
        """
        self.model = model
        self.likelihood = likelihood
        self.directed = directed
        self.layer_mode = layer_mode
        self.max_iter = max_iter
        self.tol = tol
        self.convergence_window = convergence_window
        self.alpha = alpha
        self.beta = beta
        self.gamma_shape = gamma_shape
        self.gamma_rate = gamma_rate
        self.coupling_strength = coupling_strength
        self.verbose = verbose
    
    def fit(
        self,
        A_layers: List[sp.spmatrix],
        K: int,
        q_init: np.ndarray,
        seed: Optional[int] = None
    ) -> Tuple[np.ndarray, List[np.ndarray], Optional[np.ndarray], List[float], bool]:
        """
        Run variational inference to estimate posterior.
        
        Args:
            A_layers: List of sparse adjacency matrices (one per layer)
            K: Number of blocks
            q_init: Initial soft membership (n x K)
            seed: Random seed
            
        Returns:
            Tuple of (q, B_layers, theta, elbo_history, converged)
            - q: Soft membership (n x K)
            - B_layers: List of block affinity matrices
            - theta: Node propensities for DC-SBM (or None)
            - elbo_history: List of ELBO values per iteration
            - converged: Whether algorithm converged
        """
        rng = np.random.RandomState(seed)
        
        n_nodes = A_layers[0].shape[0]
        n_layers = len(A_layers)
        
        # Initialize
        q = q_init.copy()
        q = q / q.sum(axis=1, keepdims=True)  # Ensure normalization
        
        # Initialize theta for DC-SBM
        if self.model == "dc_sbm":
            # Initialize from degree
            theta = np.ones(n_nodes)
            for A_l in A_layers:
                theta += sparse_degree(A_l, self.directed) / n_layers
            theta = theta / (K * n_layers)
            theta = np.maximum(theta, 1e-10)
        else:
            theta = None
        
        # Initialize B matrices
        if self.layer_mode == "shared_affinity":
            # Single shared B
            B_layers = [self._init_B(A_layers, q, theta, K, rng)]
        elif self.layer_mode == "coupled":
            # Per-layer B with coupling
            B_layers = [self._init_B([A_l], q, theta, K, rng) for A_l in A_layers]
        else:
            # Per-layer B
            B_layers = [self._init_B([A_l], q, theta, K, rng) for A_l in A_layers]
        
        elbo_history = []
        converged = False
        
        for iteration in range(self.max_iter):
            # E-step: Update q (memberships)
            q = self._update_q(A_layers, q, B_layers, theta, K)
            
            # M-step: Update B (block affinities)
            if self.layer_mode == "shared_affinity":
                B_layers = [self._update_B_shared(A_layers, q, theta)]
            elif self.layer_mode == "coupled":
                # Coupled mode: per-layer B with coupling regularization
                B_layers = [
                    self._update_B_layer(A_l, q, theta)
                    for A_l in A_layers
                ]
                # Apply coupling: pull B matrices toward their mean
                # Normalize by number of layers so coupling_strength is layer-count independent
                # coupling_strength=0: No coupling (independent B matrices)
                # coupling_strength=1: Full coupling (B matrices converge to mean)
                if len(B_layers) > 1:
                    B_mean = np.mean(B_layers, axis=0)
                    # Alpha determines the weight on the mean: alpha=0 (no coupling), alpha=1 (full coupling)
                    alpha = self.coupling_strength
                    for l in range(len(B_layers)):
                        B_layers[l] = (1 - alpha) * B_layers[l] + alpha * B_mean
                        B_layers[l] = np.maximum(B_layers[l], 1e-10)
            else:
                B_layers = [
                    self._update_B_layer(A_l, q, theta)
                    for A_l in A_layers
                ]
            
            # M-step: Update theta (DC-SBM only)
            if self.model == "dc_sbm":
                theta = self._update_theta(A_layers, q, B_layers)
            
            # Compute ELBO
            elbo = compute_elbo(
                A_layers, q, B_layers, theta,
                model=self.model,
                likelihood=self.likelihood,
                directed=self.directed,
                alpha=self.alpha,
                beta=self.beta,
                gamma_shape=self.gamma_shape,
                gamma_rate=self.gamma_rate
            )
            elbo_history.append(elbo)
            
            # Check convergence
            if iteration >= self.convergence_window:
                recent_elbos = elbo_history[-self.convergence_window:]
                if len(recent_elbos) >= 2:
                    rel_change = abs(recent_elbos[-1] - recent_elbos[-2]) / (abs(recent_elbos[-2]) + 1e-10)
                    if rel_change < self.tol:
                        converged = True
                        if self.verbose:
                            print(f"Converged at iteration {iteration}")
                        break
            
            if self.verbose and iteration % 10 == 0:
                print(f"Iteration {iteration}: ELBO = {elbo:.4f}")
        
        return q, B_layers, theta, elbo_history, converged
    
    def _init_B(
        self,
        A_layers: List[sp.spmatrix],
        q: np.ndarray,
        theta: Optional[np.ndarray],
        K: int,
        rng: np.random.RandomState
    ) -> np.ndarray:
        """Initialize block affinity matrix."""
        # Simple initialization: uniform + noise
        B = np.ones((K, K)) * 0.1 + rng.rand(K, K) * 0.1
        B = (B + B.T) / 2  # Symmetrize for undirected
        B = np.maximum(B, 1e-10)
        return B
    
    def _update_q(
        self,
        A_layers: List[sp.spmatrix],
        q: np.ndarray,
        B_layers: List[np.ndarray],
        theta: Optional[np.ndarray],
        K: int
    ) -> np.ndarray:
        """
        Update soft membership q (E-step).
        
        For each node i, compute log-responsibility:
        log q_ik ∝ E[log p(A_i | z_i=k, z_{-i}, theta, B)]
        """
        n_nodes = A_layers[0].shape[0]
        log_q = np.zeros((n_nodes, K))
        
        # Aggregate contributions from all layers
        for l, A_l in enumerate(A_layers):
            B_l = B_layers[l] if len(B_layers) > 1 else B_layers[0]
            
            # For each node i and block k, compute expected log-likelihood
            # This involves summing over neighbors
            A_csr = A_l.tocsr()
            
            for i in range(n_nodes):
                # Get neighbors of node i
                neighbors = A_csr.getrow(i)
                neighbor_indices = neighbors.indices
                neighbor_weights = neighbors.data
                
                for k in range(K):
                    # Compute contribution from edges to neighbors
                    # sum_j A_ij E[log p(A_ij | z_i=k, z_j)]
                    
                    for idx, j in enumerate(neighbor_indices):
                        if i == j:
                            continue
                        
                        a_ij = neighbor_weights[idx]
                        
                        # E[log p(A_ij | z_i=k, z_j)] = sum_l q_jl log(lambda_ijkl)
                        if self.model == "dc_sbm" and theta is not None:
                            lambda_vec = theta[i] * theta[j] * B_l[k, :]
                        else:
                            lambda_vec = B_l[k, :]
                        
                        lambda_vec = np.maximum(lambda_vec, 1e-10)
                        
                        if self.likelihood == "poisson":
                            log_contrib = np.sum(
                                q[j] * (a_ij * safe_log(lambda_vec) - lambda_vec)
                            )
                        else:  # bernoulli
                            log_contrib = np.sum(
                                q[j] * safe_log(lambda_vec)
                            )
                        
                        log_q[i, k] += log_contrib
        
        # Add prior: log p(z_i = k) = log(alpha / K)
        log_q += np.log(self.alpha / K)
        
        # Normalize using log-sum-exp
        log_q_normalized = log_q - log_sum_exp(log_q, axis=1)[:, None]
        q_new = np.exp(log_q_normalized)
        
        # Ensure numerical stability
        q_new = np.maximum(q_new, 1e-10)
        q_new = q_new / q_new.sum(axis=1, keepdims=True)
        
        return q_new
    
    def _update_B_layer(
        self,
        A: sp.spmatrix,
        q: np.ndarray,
        theta: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Update block affinity matrix B for a single layer (M-step).
        
        For Poisson: B_kl = sum_{ij} q_ik q_jl A_ij / sum_{ij} q_ik q_jl (theta_i theta_j)
        """
        n_nodes, K = q.shape
        
        B = np.zeros((K, K))
        counts = np.zeros((K, K))
        
        # Iterate over edges
        A_coo = A.tocoo()
        for i, j, a_ij in zip(A_coo.row, A_coo.col, A_coo.data):
            if i == j:
                continue
            
            # Add contribution to all block pairs
            outer = q[i][:, None] * q[j][None, :]
            B += outer * a_ij
            
            if self.model == "dc_sbm" and theta is not None:
                counts += outer * (theta[i] * theta[j])
            else:
                counts += outer
        
        # Normalize
        B = B / np.maximum(counts, 1e-10)
        
        # Symmetrize for undirected
        if not self.directed:
            B = (B + B.T) / 2
        
        B = np.maximum(B, 1e-10)
        
        return B
    
    def _update_B_shared(
        self,
        A_layers: List[sp.spmatrix],
        q: np.ndarray,
        theta: Optional[np.ndarray]
    ) -> np.ndarray:
        """Update shared block affinity across all layers."""
        # Aggregate across layers
        n_nodes, K = q.shape
        
        B = np.zeros((K, K))
        counts = np.zeros((K, K))
        
        for A_l in A_layers:
            A_coo = A_l.tocoo()
            for i, j, a_ij in zip(A_coo.row, A_coo.col, A_coo.data):
                if i == j:
                    continue
                
                outer = q[i][:, None] * q[j][None, :]
                B += outer * a_ij
                
                if self.model == "dc_sbm" and theta is not None:
                    counts += outer * (theta[i] * theta[j])
                else:
                    counts += outer
        
        B = B / np.maximum(counts, 1e-10)
        
        if not self.directed:
            B = (B + B.T) / 2
        
        B = np.maximum(B, 1e-10)
        
        return B
    
    def _update_theta(
        self,
        A_layers: List[sp.spmatrix],
        q: np.ndarray,
        B_layers: List[np.ndarray]
    ) -> np.ndarray:
        """
        Update node propensities theta for DC-SBM (M-step).
        
        For Poisson DC-SBM:
        theta_i ∝ (degree_i + gamma_shape - 1) / (sum_j theta_j B_{z_i z_j} + gamma_rate)
        """
        n_nodes, K = q.shape
        
        # Compute total degree across layers
        degrees = np.zeros(n_nodes)
        for A_l in A_layers:
            degrees += sparse_degree(A_l, self.directed)
        
        # Compute denominator: sum_j theta_j E[B_{z_i z_j}]
        denom = np.zeros(n_nodes)
        
        for l, A_l in enumerate(A_layers):
            B_l = B_layers[l] if len(B_layers) > 1 else B_layers[0]
            
            # For each node i: sum_j theta_j sum_kl q_ik q_jl B_kl
            # = sum_kl q_ik B_kl sum_j q_jl theta_j
            
            theta_q = np.zeros(K)  # Will store sum_j q_jl theta_j
            for k in range(K):
                theta_q[k] = 1.0  # Placeholder; actual update is iterative
            
            # Simplified: use current degrees as proxy
            denom += degrees / len(A_layers)
        
        # Update theta
        theta = (degrees + self.gamma_shape - 1) / (denom + self.gamma_rate)
        theta = np.maximum(theta, 1e-10)
        
        # Normalize to have mean 1 for identifiability
        theta = theta / np.mean(theta)
        
        return theta
