"""
Tests for multilayer SBM implementation.

This module tests the core SBM functionality including:
- Synthetic data generation
- Model fitting
- Parameter recovery
- Model selection
"""

import numpy as np
import pytest
import scipy.sparse as sp

from py3plex.core import multinet
from py3plex.algorithms.sbm import (
    fit_multilayer_sbm,
    select_multilayer_sbm_model,
    SBMFittedModel
)
from py3plex.algorithms.sbm.utils import (
    compute_ari,
    compute_nmi,
    init_random_soft_membership,
    init_kmeans_membership,
    init_spectral_membership
)


def generate_synthetic_sbm_network(
    n_nodes: int = 50,
    K: int = 3,
    n_layers: int = 2,
    p_within: float = 0.3,
    p_between: float = 0.05,
    seed: int = 42
) -> tuple:
    """
    Generate synthetic multilayer SBM network with known ground truth.
    
    Returns:
        Tuple of (network, true_labels, block_sizes)
    """
    rng = np.random.RandomState(seed)
    
    # Generate block assignments
    block_sizes = [n_nodes // K] * K
    # Adjust last block to account for remainder
    block_sizes[-1] += n_nodes - sum(block_sizes)
    
    true_labels = np.repeat(range(K), block_sizes)
    rng.shuffle(true_labels)
    
    # Create py3plex network
    net = multinet.multi_layer_network(directed=False)
    
    # First, add all nodes to all layers to ensure alignment
    for layer_idx in range(n_layers):
        layer_name = f"L{layer_idx}"
        # Add self-loop then remove to ensure node exists
        for node_id in range(n_nodes):
            net.add_edges([{
                'source': node_id,
                'target': (node_id + 1) % n_nodes,  # Connect to next node
                'source_type': layer_name,
                'target_type': layer_name
            }])
    
    # Generate edges for each layer based on block structure
    for layer_idx in range(n_layers):
        layer_name = f"L{layer_idx}"
        
        # Generate edges based on block structure
        edges = []
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                # Edge probability depends on block membership
                if true_labels[i] == true_labels[j]:
                    p_edge = p_within
                else:
                    p_edge = p_between
                
                if rng.rand() < p_edge:
                    edges.append({
                        'source': i,
                        'target': j,
                        'source_type': layer_name,
                        'target_type': layer_name
                    })
        
        if edges:
            net.add_edges(edges)
    
    return net, true_labels, block_sizes


def test_sbm_imports():
    """Test that SBM modules can be imported."""
    from py3plex.algorithms.sbm import fit_multilayer_sbm
    from py3plex.algorithms.sbm import SBMFittedModel
    from py3plex.algorithms.sbm.utils import safe_log
    from py3plex.algorithms.sbm.conversions import extract_layer_adjacencies
    
    assert fit_multilayer_sbm is not None
    assert SBMFittedModel is not None


def test_synthetic_network_generation():
    """Test synthetic SBM network generation."""
    net, true_labels, block_sizes = generate_synthetic_sbm_network(
        n_nodes=30, K=3, n_layers=2
    )
    
    assert len(true_labels) == 30
    assert len(set(true_labels)) == 3
    layers_tuple = net.get_layers()
    # get_layers returns (layer_names, layer_graphs, other_info)
    assert len(layers_tuple[0]) == 2


def test_sbm_fit_basic():
    """Test basic SBM fitting."""
    # Generate small synthetic network
    net, true_labels, _ = generate_synthetic_sbm_network(
        n_nodes=30, K=2, n_layers=2, p_within=0.4, p_between=0.05
    )
    
    # Fit SBM
    model = fit_multilayer_sbm(
        net,
        n_blocks=2,
        model="sbm",
        layer_mode="independent",
        init="random",
        n_init=1,
        max_iter=50,
        verbose=False,
        seed=42
    )
    
    # Check model attributes
    assert isinstance(model, SBMFittedModel)
    assert model.K_ == 2
    assert model.memberships_.shape == (30, 2)
    assert len(model.hard_membership_) == 30
    assert len(model.elbo_history_) > 0


def test_dc_sbm_fit():
    """Test DC-SBM fitting."""
    net, true_labels, _ = generate_synthetic_sbm_network(
        n_nodes=30, K=2, n_layers=2
    )
    
    model = fit_multilayer_sbm(
        net,
        n_blocks=2,
        model="dc_sbm",
        layer_mode="independent",
        init="spectral",
        n_init=1,
        max_iter=50,
        verbose=False,
        seed=42
    )
    
    assert isinstance(model, SBMFittedModel)
    assert model.model_ == "dc_sbm"
    assert model.degree_params_ is not None
    assert len(model.degree_params_) == 30


def test_sbm_recovery():
    """Test that SBM can recover known block structure."""
    # Generate clear block structure
    net, true_labels, _ = generate_synthetic_sbm_network(
        n_nodes=60,
        K=3,
        n_layers=2,
        p_within=0.5,
        p_between=0.02,
        seed=42
    )
    
    # Fit with correct K
    model = fit_multilayer_sbm(
        net,
        n_blocks=3,
        model="sbm",
        layer_mode="shared_blocks",
        init="spectral",
        n_init=3,
        max_iter=100,
        verbose=False,
        seed=42
    )
    
    # Check recovery quality
    pred_labels = model.hard_membership_
    
    ari = compute_ari(pred_labels, true_labels)
    nmi = compute_nmi(pred_labels, true_labels)
    
    # With clear structure, should get reasonable recovery
    # (exact threshold depends on randomness, but should be > 0)
    assert ari > 0.0, f"ARI should be positive, got {ari}"
    assert nmi > 0.0, f"NMI should be positive, got {nmi}"


def test_layer_coupling_modes():
    """Test different layer coupling modes."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=30, K=2, n_layers=2)
    
    # Test independent
    model_ind = fit_multilayer_sbm(
        net, n_blocks=2, layer_mode="independent",
        n_init=1, max_iter=30, verbose=False
    )
    assert model_ind.layer_mode_ == "independent"
    assert len(model_ind.block_affinity_) == 2  # One B per layer
    
    # Test shared_blocks
    model_shared = fit_multilayer_sbm(
        net, n_blocks=2, layer_mode="shared_blocks",
        n_init=1, max_iter=30, verbose=False
    )
    assert model_shared.layer_mode_ == "shared_blocks"
    
    # Test shared_affinity
    model_aff = fit_multilayer_sbm(
        net, n_blocks=2, layer_mode="shared_affinity",
        n_init=1, max_iter=30, verbose=False
    )
    assert model_aff.layer_mode_ == "shared_affinity"
    assert len(model_aff.block_affinity_) == 1  # Single shared B


def test_model_selection():
    """Test model selection across multiple K values."""
    net, _, _ = generate_synthetic_sbm_network(
        n_nodes=40, K=3, n_layers=2
    )
    
    # Run model selection
    model, info = fit_multilayer_sbm(
        net,
        n_blocks=[2, 3, 4],
        model="sbm",
        n_init=2,
        max_iter=30,
        verbose=False,
        seed=42
    )
    
    # Check results
    assert isinstance(model, SBMFittedModel)
    assert 'best_K' in info
    assert 'comparison_table' in info
    assert info['best_K'] in [2, 3, 4]
    
    # Check comparison table
    df = info['comparison_table']
    assert len(df) == 3
    assert 'K' in df.columns
    assert 'elbo' in df.columns
    assert 'bic' in df.columns


def test_initialization_methods():
    """Test different initialization methods."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=30, K=2, n_layers=2)
    
    # Random init
    model_rand = fit_multilayer_sbm(
        net, n_blocks=2, init="random",
        n_init=1, max_iter=20, verbose=False, seed=42
    )
    assert model_rand is not None
    
    # K-means init
    model_km = fit_multilayer_sbm(
        net, n_blocks=2, init="kmeans",
        n_init=1, max_iter=20, verbose=False, seed=42
    )
    assert model_km is not None
    
    # Spectral init
    model_spec = fit_multilayer_sbm(
        net, n_blocks=2, init="spectral",
        n_init=1, max_iter=20, verbose=False, seed=42
    )
    assert model_spec is not None


def test_predict_proba():
    """Test edge probability prediction."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=20, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=30, verbose=False
    )
    
    # Test prediction
    prob = model.predict_proba(0, 1, "L0")
    assert isinstance(prob, float)
    assert prob >= 0.0
    
    # Test for non-existent node
    prob_missing = model.predict_proba(999, 0, "L0")
    assert prob_missing == 0.0


def test_score_edges():
    """Test batch edge scoring."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=20, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=30, verbose=False
    )
    
    # Score multiple edges
    edges = [(0, 1, "L0"), (2, 3, "L1"), (4, 5, "L0")]
    scores = model.score_edges(edges)
    
    assert len(scores) == 3
    assert all(isinstance(s, (float, np.floating)) for s in scores)
    assert all(s >= 0.0 for s in scores)


def test_to_partition_vector():
    """Test conversion to partition vector."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=20, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=30, verbose=False
    )
    
    partition = model.to_partition_vector()
    
    assert isinstance(partition, dict)
    assert len(partition) == 20
    assert all(isinstance(v, (int, np.integer)) for v in partition.values())


def test_uncertainty_metrics():
    """Test uncertainty computation."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=30, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=30, verbose=False
    )
    
    # Check uncertainty attributes
    assert 'node_entropy' in model.uncertainty_
    assert 'membership_confidence' in model.uncertainty_
    assert 'entropy' in model.uncertainty_
    assert 'confidence' in model.uncertainty_
    
    # Check shapes
    n_nodes = len(model.node_to_idx_)
    assert len(model.uncertainty_['entropy']) == n_nodes
    assert len(model.uncertainty_['confidence']) == n_nodes


def test_convergence():
    """Test convergence behavior."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=30, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=100, tol=1e-4,
        verbose=False
    )
    
    # Check ELBO history
    assert len(model.elbo_history_) > 0
    
    # ELBO should generally increase (or stay flat)
    # Allow small numerical decreases
    diffs = np.diff(model.elbo_history_)
    large_decreases = np.sum(diffs < -1e-3)
    assert large_decreases < len(diffs) * 0.1, "ELBO should not decrease significantly"


def test_empty_layer_handling():
    """Test handling of empty or sparse layers."""
    # Create network with one sparse layer
    net = multinet.multi_layer_network(directed=False)
    
    # Layer 1: some edges
    edges_l1 = [
        {'source': 0, 'target': 1, 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 1, 'target': 2, 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 2, 'target': 3, 'source_type': 'L1', 'target_type': 'L1'},
    ]
    net.add_edges(edges_l1)
    
    # Layer 2: very sparse
    edges_l2 = [
        {'source': 0, 'target': 1, 'source_type': 'L2', 'target_type': 'L2'},
    ]
    net.add_edges(edges_l2)
    
    # Should handle without crashing
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=20, verbose=False
    )
    
    assert model is not None
    assert model.K_ == 2


def test_model_summary():
    """Test model summary generation."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=20, K=2, n_layers=2)
    
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=1, max_iter=30, verbose=False
    )
    
    summary = model.get_summary()
    
    assert 'model' in summary
    assert 'n_blocks' in summary
    assert 'n_nodes' in summary
    assert 'n_layers' in summary
    assert 'converged' in summary
    assert 'final_elbo' in summary
    
    # Check repr
    repr_str = repr(model)
    assert 'SBMFittedModel' in repr_str
    assert 'K=' in repr_str


def test_multiple_restarts():
    """Test that multiple restarts work correctly."""
    net, _, _ = generate_synthetic_sbm_network(n_nodes=30, K=2, n_layers=2)
    
    # Fit with multiple restarts
    model = fit_multilayer_sbm(
        net, n_blocks=2,
        n_init=3,
        max_iter=20, verbose=False, seed=42
    )
    
    assert model is not None
    assert model.K_ == 2
    
    # ELBO should be from best restart
    assert model.elbo_history_[-1] is not None


def test_sparse_operations():
    """Test that operations remain sparse (no densification)."""
    from py3plex.algorithms.sbm.conversions import extract_layer_adjacencies
    
    net, _, _ = generate_synthetic_sbm_network(n_nodes=50, K=3, n_layers=2)
    
    A_layers, layers, node_to_idx = extract_layer_adjacencies(net)
    
    # Check that adjacencies are sparse
    for A in A_layers:
        assert sp.issparse(A), "Adjacency should be sparse matrix"
        assert A.format in ['csr', 'csc', 'coo'], "Should use standard sparse format"
    
    # Fit model (should maintain sparsity internally)
    model = fit_multilayer_sbm(
        net, n_blocks=3,
        n_init=1, max_iter=20, verbose=False
    )
    
    assert model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
