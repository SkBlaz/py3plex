"""
Variational inference for multilayer SBM.

This module implements mean-field variational inference for SBM and DC-SBM.
"""

from typing import List, Optional, Tuple
import numpy as np
import scipy.sparse as sp

from .utils import safe_log, log_sum_exp, sparse_degree
from .objectives import compute_elbo, _block_edges, _dyad_exposure


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
        if model == "dc_sbm" and likelihood == "bernoulli":
            raise ValueError("Degree correction requires a Poisson likelihood.")
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
        matrices = []
        for matrix in A_layers:
            matrix = sp.csr_matrix(matrix, dtype=float, copy=True)
            matrix.sum_duplicates()
            matrix.setdiag(0)
            matrix.eliminate_zeros()
            if not np.isfinite(matrix.data).all() or np.any(matrix.data < 0):
                raise ValueError("SBM adjacency values must be finite and nonnegative.")
            if self.likelihood == "bernoulli":
                matrix.data.fill(1)
            matrices.append(matrix)
        A_layers = matrices
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
                theta = self._update_theta(A_layers, q, B_layers, theta)
            
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
        if not self.directed:
            B = (B + B.T) / 2
        B = np.maximum(B, 1e-10)
        return B
    
    def _update_q(self, A_layers, q, B_layers, theta, K):
        """Perform one coordinate sweep on the mean-field memberships."""
        q = q.copy()
        propensities = np.ones(len(q)) if theta is None else theta
        mass = q.T @ propensities
        contributions = []
        for layer, matrix in enumerate(A_layers):
            affinity = B_layers[layer] if len(B_layers) > 1 else B_layers[0]
            orientations = [(matrix, affinity)]
            if self.directed:
                orientations.append((matrix.T.tocsr(), affinity.T))
            for adjacency, rate in orientations:
                if self.likelihood == "bernoulli":
                    p = np.clip(rate, 1e-10, 1 - 1e-10)
                    absent = np.log1p(-p)
                    present = np.log(p) - absent
                else:
                    absent = -rate
                    present = safe_log(rate)
                contributions.append((adjacency, present, absent))

        for i, propensity in enumerate(propensities):
            mass -= propensity * q[i]
            score = np.zeros(K)
            for matrix, present, absent in contributions:
                start, stop = matrix.indptr[i:i + 2]
                neighbor_mass = matrix.data[start:stop] @ q[matrix.indices[start:stop]]
                score += present @ neighbor_mass + propensity * (absent @ mass)
            q[i] = np.exp(score - log_sum_exp(score))
            mass += propensity * q[i]
        return q

    def _update_B_layer(self, A, q, theta):
        return self._update_B_shared([A], q, theta)

    def _update_B_shared(self, A_layers, q, theta):
        weighted_q = q if theta is None else q * theta[:, None]
        exposure = len(A_layers) * _dyad_exposure(weighted_q)
        edges = sum(_block_edges(matrix, q) for matrix in A_layers)
        affinity = edges / np.maximum(exposure, 1e-10)
        if not self.directed:
            affinity = (affinity + affinity.T) / 2
        upper = 1 - 1e-10 if self.likelihood == "bernoulli" else np.inf
        return np.clip(affinity, 1e-10, upper)

    def _update_theta(self, A_layers, q, B_layers, theta):
        """Coordinate MAP update for a shared per-node Poisson propensity."""
        theta = theta.copy()
        degrees = np.zeros(len(q))
        for matrix in A_layers:
            degrees += np.asarray(matrix.sum(axis=1)).ravel()
            if self.directed:
                degrees += np.asarray(matrix.sum(axis=0)).ravel()
        affinity = sum(B_layers) if len(B_layers) > 1 else len(A_layers) * B_layers[0]
        if self.directed:
            affinity = affinity + affinity.T

        mass = q.T @ theta
        for i in range(len(theta)):
            mass -= theta[i] * q[i]
            exposure = max(0.0, q[i] @ affinity @ mass)
            theta[i] = max(1e-10, (degrees[i] + self.gamma_shape - 1) /
                           (exposure + self.gamma_rate))
            mass += theta[i] * q[i]
        return theta
