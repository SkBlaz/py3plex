"""
Tests for MMSBM (Mixed-Membership SBM).
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.sbm import mmsbm_fit, fit_multilayer_sbm


def create_test_network(n_nodes=40, K=3, n_layers=2, seed=42):
    """Create a simple test network with known structure."""
    rng = np.random.default_rng(seed)
    
    net = multinet.multi_layer_network(directed=False)
    
    # Create nodes
    nodes = [f"N{i}" for i in range(n_nodes)]
    for node in nodes:
        for layer_idx in range(n_layers):
            net.add_node(node, layer=f"L{layer_idx}")
    
    # Generate edges based on block structure
    block_assignments = rng.choice(K, size=n_nodes)
    
    for layer_idx in range(n_layers):
        layer = f"L{layer_idx}"
        
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                # Higher probability within same block
                if block_assignments[i] == block_assignments[j]:
                    p = 0.4
                else:
                    p = 0.05
                
                if rng.random() < p:
                    net.add_edge(nodes[i], nodes[j], layer_src=layer, layer_dst=layer)
    
    return net, block_assignments


def test_mmsbm_basic():
    """Test basic MMSBM fitting."""
    net, true_labels = create_test_network(n_nodes=40, K=3, n_layers=2, seed=42)
    
    # Fit MMSBM
    model = mmsbm_fit(net, n_blocks=3, model="dc_sbm", seed=42, verbose=False, n_init=2, max_iter=50)
    
    # Check soft memberships
    assert hasattr(model, 'memberships_')
    assert model.memberships_.shape[0] == 40  # n_nodes
    assert model.memberships_.shape[1] == 3   # K
    
    # Check that memberships sum to 1
    membership_sums = model.memberships_.sum(axis=1)
    np.testing.assert_allclose(membership_sums, 1.0, rtol=1e-5)
    
    # Check that all memberships are non-negative
    assert np.all(model.memberships_ >= 0)


def test_mmsbm_soft_vs_hard():
    """Test that hard membership is argmax of soft membership."""
    net, _ = create_test_network(n_nodes=30, K=2, n_layers=1, seed=43)
    
    model = mmsbm_fit(net, n_blocks=2, model="sbm", seed=43, verbose=False, n_init=1, max_iter=50)
    
    # Hard membership should be argmax of soft
    expected_hard = np.argmax(model.memberships_, axis=1)
    np.testing.assert_array_equal(model.hard_membership_, expected_hard)


def test_mmsbm_different_K():
    """Test MMSBM with different K values."""
    net, _ = create_test_network(n_nodes=30, K=3, n_layers=1, seed=44)
    
    # Test with K=2
    model_k2 = mmsbm_fit(net, n_blocks=2, model="dc_sbm", seed=44, verbose=False, n_init=1, max_iter=30)
    assert model_k2.memberships_.shape[1] == 2
    
    # Test with K=4
    model_k4 = mmsbm_fit(net, n_blocks=4, model="dc_sbm", seed=44, verbose=False, n_init=1, max_iter=30)
    assert model_k4.memberships_.shape[1] == 4


def test_mmsbm_multilayer_modes():
    """Test MMSBM with different multilayer modes."""
    net, _ = create_test_network(n_nodes=30, K=2, n_layers=2, seed=45)
    
    # Test shared_blocks mode (default)
    model_shared = mmsbm_fit(
        net, n_blocks=2, layer_mode="shared_blocks",
        model="dc_sbm", seed=45, verbose=False, n_init=1, max_iter=30
    )
    assert model_shared.memberships_.shape == (30, 2)
    
    # Test independent mode
    model_ind = mmsbm_fit(
        net, n_blocks=2, layer_mode="independent",
        model="dc_sbm", seed=45, verbose=False, n_init=1, max_iter=30
    )
    assert model_ind.memberships_.shape == (30, 2)


def test_mmsbm_partition_compatibility():
    """Test that MMSBM can produce a partition for compatibility."""
    net, _ = create_test_network(n_nodes=30, K=3, n_layers=2, seed=46)
    
    model = mmsbm_fit(net, n_blocks=3, model="dc_sbm", seed=46, verbose=False, n_init=1, max_iter=30)
    
    # Get hard partition
    partition = model.to_partition_vector()
    
    # Check partition format
    assert isinstance(partition, dict)
    assert len(partition) == 30  # One entry per node
    
    # Check that partition values are in [0, K-1]
    partition_values = set(partition.values())
    assert partition_values.issubset({0, 1, 2})


def test_mmsbm_deterministic():
    """Test that MMSBM is deterministic with same seed."""
    net, _ = create_test_network(n_nodes=25, K=2, n_layers=1, seed=47)
    
    # Fit twice with same seed
    model1 = mmsbm_fit(net, n_blocks=2, model="dc_sbm", seed=100, verbose=False, n_init=1, max_iter=30)
    model2 = mmsbm_fit(net, n_blocks=2, model="dc_sbm", seed=100, verbose=False, n_init=1, max_iter=30)
    
    # Check that soft memberships are identical
    np.testing.assert_allclose(model1.memberships_, model2.memberships_, rtol=1e-10)


def test_mmsbm_convergence():
    """Test that MMSBM reports convergence status."""
    net, _ = create_test_network(n_nodes=30, K=2, n_layers=1, seed=48)
    
    model = mmsbm_fit(net, n_blocks=2, model="dc_sbm", seed=48, verbose=False, n_init=1, max_iter=100)
    
    # Check convergence attributes
    assert hasattr(model, 'converged_')
    assert hasattr(model, 'n_iter_')
    assert hasattr(model, 'elbo_history_')
    
    # ELBO history should be non-empty
    assert len(model.elbo_history_) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
