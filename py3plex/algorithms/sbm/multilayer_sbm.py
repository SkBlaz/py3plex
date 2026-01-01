"""
Multilayer Stochastic Block Model implementation.

This module provides the core SBMFittedModel class and orchestration
for fitting SBM and DC-SBM to multilayer networks.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.sparse as sp

from .conversions import extract_layer_adjacencies, check_node_aligned
from .utils import (
    init_random_soft_membership,
    init_kmeans_membership,
    init_spectral_membership,
    node_entropy,
    membership_confidence
)
from .inference_vi import VariationalInference
from .diagnostics import compute_posterior_summary, assess_convergence_quality, compute_uncertainty_metrics
from .model_selection import compute_bic, compute_icl


class SBMFittedModel:
    """
    Fitted Multilayer Stochastic Block Model.
    
    This class encapsulates the results of fitting an SBM or DC-SBM
    to a multilayer network.
    
    Attributes:
        memberships_: Soft membership probabilities (n_nodes x K)
        hard_membership_: Hard block assignments (n_nodes,)
        block_affinity_: Block affinity matrices per layer
        degree_params_: Node propensities for DC-SBM (or None)
        elbo_history_: ELBO values over iterations
        converged_: Whether inference converged
        n_iter_: Number of iterations run
        uncertainty_: Dict with uncertainty metrics
        model_: Model type ("sbm" or "dc_sbm")
        layer_mode_: Layer coupling mode
        layers_: List of layer names
        node_to_idx_: Mapping from node IDs to indices
        idx_to_node_: Mapping from indices to node IDs
        K_: Number of blocks
    """
    
    def __init__(
        self,
        q: np.ndarray,
        B_layers: List[np.ndarray],
        theta: Optional[np.ndarray],
        elbo_history: List[float],
        converged: bool,
        layers: List[str],
        node_to_idx: Dict[Any, int],
        model: str,
        layer_mode: str,
        directed: bool
    ):
        """
        Initialize fitted model.
        
        Args:
            q: Soft membership matrix (n_nodes x K)
            B_layers: List of block affinity matrices
            theta: Node propensities for DC-SBM (or None)
            elbo_history: ELBO values over iterations
            converged: Whether converged
            layers: Layer names
            node_to_idx: Node ID to index mapping
            model: "sbm" or "dc_sbm"
            layer_mode: Layer coupling mode
            directed: Whether directed
        """
        self.memberships_ = q
        self.hard_membership_ = np.argmax(q, axis=1)
        self.block_affinity_ = B_layers
        self.degree_params_ = theta
        self.elbo_history_ = elbo_history
        self.converged_ = converged
        self.n_iter_ = len(elbo_history)
        
        # Compute uncertainty metrics
        self.uncertainty_ = compute_uncertainty_metrics(q)
        self.uncertainty_['node_entropy'] = node_entropy(q)
        self.uncertainty_['membership_confidence'] = membership_confidence(q)
        
        # Metadata
        self.model_ = model
        self.layer_mode_ = layer_mode
        self.directed_ = directed
        self.layers_ = layers
        self.node_to_idx_ = node_to_idx
        self.idx_to_node_ = {idx: node for node, idx in node_to_idx.items()}
        self.K_ = q.shape[1]
    
    def predict_proba(
        self,
        u: Any,
        v: Any,
        layer: str
    ) -> float:
        """
        Predict edge probability between two nodes in a layer.
        
        Args:
            u: Source node ID
            v: Target node ID
            layer: Layer name
            
        Returns:
            Predicted edge probability
        """
        # Get node indices
        u_idx = self.node_to_idx_.get(u)
        v_idx = self.node_to_idx_.get(v)
        
        if u_idx is None or v_idx is None:
            return 0.0
        
        # Get layer index
        try:
            layer_idx = self.layers_.index(layer)
        except ValueError:
            return 0.0
        
        # Get block affinity for this layer
        if len(self.block_affinity_) == 1:
            B = self.block_affinity_[0]
        else:
            B = self.block_affinity_[layer_idx]
        
        # Compute expected edge probability
        # E[A_uv] = sum_{kl} q_uk q_vl B_kl (or with theta for DC-SBM)
        expected_rate = np.sum(
            self.memberships_[u_idx][:, None] * 
            self.memberships_[v_idx][None, :] * 
            B
        )
        
        if self.degree_params_ is not None:
            expected_rate *= self.degree_params_[u_idx] * self.degree_params_[v_idx]
        
        # For Poisson, this is the rate parameter
        # For link prediction, we can return the rate directly
        return float(expected_rate)
    
    def score_edges(
        self,
        edges: List[Tuple[Any, Any, str]]
    ) -> np.ndarray:
        """
        Score a list of edges.
        
        Args:
            edges: List of (u, v, layer) tuples
            
        Returns:
            Array of predicted probabilities
        """
        scores = np.zeros(len(edges))
        
        for i, (u, v, layer) in enumerate(edges):
            scores[i] = self.predict_proba(u, v, layer)
        
        return scores
    
    def to_partition_vector(self) -> Dict[Any, int]:
        """
        Convert to partition vector compatible with py3plex utilities.
        
        Returns:
            Dict mapping node IDs to community labels
        """
        partition = {}
        
        for node, idx in self.node_to_idx_.items():
            partition[node] = int(self.hard_membership_[idx])
        
        return partition
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of fitted model.
        
        Returns:
            Dictionary with model summary
        """
        summary = {
            'model': self.model_,
            'layer_mode': self.layer_mode_,
            'n_blocks': self.K_,
            'n_nodes': len(self.node_to_idx_),
            'n_layers': len(self.layers_),
            'converged': self.converged_,
            'n_iter': self.n_iter_,
            'final_elbo': self.elbo_history_[-1] if self.elbo_history_ else None,
        }
        
        # Add posterior summary
        posterior_summary = compute_posterior_summary(
            self.memberships_,
            self.degree_params_
        )
        summary.update(posterior_summary)
        
        return summary
    
    def __repr__(self) -> str:
        """String representation."""
        summary = self.get_summary()
        return (
            f"SBMFittedModel(model={summary['model']}, "
            f"K={summary['n_blocks']}, "
            f"n_nodes={summary['n_nodes']}, "
            f"n_layers={summary['n_layers']}, "
            f"converged={summary['converged']})"
        )


def fit_single_sbm(
    A_layers: List[sp.spmatrix],
    K: int,
    layers: List[str],
    node_to_idx: Dict[Any, int],
    model: str = "dc_sbm",
    layer_mode: str = "independent",
    directed: bool = False,
    likelihood: str = "poisson",
    init: str = "spectral",
    seed: Optional[int] = None,
    max_iter: int = 500,
    tol: float = 1e-5,
    verbose: bool = False,
    **kwargs
) -> SBMFittedModel:
    """
    Fit a single SBM model with fixed K.
    
    Args:
        A_layers: List of sparse adjacency matrices
        K: Number of blocks
        layers: Layer names
        node_to_idx: Node to index mapping
        model: "sbm" or "dc_sbm"
        layer_mode: "independent", "shared_blocks", or "shared_affinity"
        directed: Whether directed
        likelihood: "bernoulli" or "poisson"
        init: Initialization method ("random", "kmeans", "spectral")
        seed: Random seed
        max_iter: Maximum iterations
        tol: Convergence tolerance
        verbose: Print progress
        **kwargs: Additional parameters
        
    Returns:
        Fitted SBMFittedModel
    """
    n_nodes = A_layers[0].shape[0]
    
    # Initialize membership
    if init == "random":
        q_init = init_random_soft_membership(n_nodes, K, seed)
    elif init == "kmeans":
        q_init = init_kmeans_membership(A_layers, K, seed=seed)
    elif init == "spectral":
        q_init = init_spectral_membership(A_layers, K, seed)
    else:
        raise ValueError(f"Unknown init method: {init}")
    
    # Run variational inference
    vi = VariationalInference(
        model=model,
        likelihood=likelihood,
        directed=directed,
        layer_mode=layer_mode,
        max_iter=max_iter,
        tol=tol,
        verbose=verbose,
        **kwargs
    )
    
    q, B_layers, theta, elbo_history, converged = vi.fit(
        A_layers, K, q_init, seed
    )
    
    # Create fitted model
    fitted_model = SBMFittedModel(
        q=q,
        B_layers=B_layers,
        theta=theta,
        elbo_history=elbo_history,
        converged=converged,
        layers=layers,
        node_to_idx=node_to_idx,
        model=model,
        layer_mode=layer_mode,
        directed=directed
    )
    
    return fitted_model
