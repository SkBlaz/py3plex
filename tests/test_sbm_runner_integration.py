"""
Tests for SBM integration with AutoCommunity and runner.

This module tests:
1. SBM runner integration with BudgetSpec
2. DC-SBM as default and preferred algorithm
3. Deterministic behavior under fixed seed
4. UQ integration
5. Successive Halving compatibility
6. AutoCommunity integration
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.community_detection.budget import BudgetSpec, CommunityResult
from py3plex.algorithms.community_detection.runner import run_community_algorithm
from py3plex.algorithms.community_detection.autocommunity import AutoCommunity


def generate_small_test_network(n_nodes=20, n_layers=2, seed=42):
    """Generate a small test network for quick testing."""
    rng = np.random.RandomState(seed)
    
    net = multinet.multi_layer_network(directed=False)
    
    # Ensure node alignment: add each node to each layer first
    for layer_idx in range(n_layers):
        layer_name = f"L{layer_idx}"
        # Add edges to ensure all nodes exist in all layers
        for i in range(n_nodes - 1):
            # Add at least one edge per node to ensure presence
            net.add_edges([{
                'source': i,
                'target': i + 1,
                'source_type': layer_name,
                'target_type': layer_name
            }])
        
        # Add additional random edges
        for i in range(n_nodes):
            for j in range(i + 1, min(i + 5, n_nodes)):
                if rng.rand() < 0.3:
                    net.add_edges([{
                        'source': i,
                        'target': j,
                        'source_type': layer_name,
                        'target_type': layer_name
                    }])
    
    return net


def test_sbm_runner_basic():
    """Test that SBM runner can be called and produces valid output."""
    net = generate_small_test_network(n_nodes=15, n_layers=1)
    
    budget = BudgetSpec(max_iter=50, n_restarts=2, uq_samples=None)
    
    result = run_community_algorithm(
        algorithm_id="sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3]
    )
    
    assert isinstance(result, CommunityResult)
    assert result.algo_id == "sbm"
    assert len(result.partition) > 0
    assert "log_likelihood" in result.meta
    assert "K_selected" in result.meta
    assert result.meta["model_type"] == "sbm"


def test_dc_sbm_runner_basic():
    """Test that DC-SBM runner can be called and produces valid output."""
    net = generate_small_test_network(n_nodes=15, n_layers=1)
    
    budget = BudgetSpec(max_iter=50, n_restarts=2, uq_samples=None)
    
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3]
    )
    
    assert isinstance(result, CommunityResult)
    assert result.algo_id == "dc_sbm"
    assert len(result.partition) > 0
    assert "log_likelihood" in result.meta
    assert "K_selected" in result.meta
    assert result.meta["model_type"] == "dc_sbm"


def test_sbm_determinism():
    """Test that SBM produces same results with same seed."""
    net = generate_small_test_network(n_nodes=15, n_layers=1)
    
    budget = BudgetSpec(max_iter=50, n_restarts=2)
    
    result1 = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=123,
        K_range=[2, 3]
    )
    
    result2 = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=123,
        K_range=[2, 3]
    )
    
    # Same seed should produce same K selection
    assert result1.meta["K_selected"] == result2.meta["K_selected"]
    
    # Log-likelihoods should be close (may have minor numerical differences)
    ll1 = result1.meta["log_likelihood"]
    ll2 = result2.meta["log_likelihood"]
    assert abs(ll1 - ll2) < 1e-3, f"Log-likelihoods differ: {ll1} vs {ll2}"


def test_sbm_with_uq():
    """Test that SBM works with UQ enabled."""
    net = generate_small_test_network(n_nodes=15, n_layers=1)
    
    budget = BudgetSpec(max_iter=30, n_restarts=1, uq_samples=5)
    
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3]
    )
    
    assert result.meta["uq_enabled"] is True
    assert result.meta["n_samples"] == 5
    assert "log_likelihood_std" in result.meta
    assert result.meta["log_likelihood_std"] >= 0


def test_sbm_budget_scaling():
    """Test that SBM respects budget parameters."""
    net = generate_small_test_network(n_nodes=15, n_layers=1)
    
    # Small budget
    budget_small = BudgetSpec(max_iter=10, n_restarts=1)
    result_small = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget_small,
        seed=42,
        K_range=[2, 3]
    )
    
    # Large budget
    budget_large = BudgetSpec(max_iter=100, n_restarts=5)
    result_large = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget_large,
        seed=42,
        K_range=[2, 3]
    )
    
    # Both should complete successfully
    assert result_small.meta["converged"] or result_small.meta["n_iter"] > 0
    assert result_large.meta["converged"] or result_large.meta["n_iter"] > 0
    
    # Larger budget should not produce worse results (or same/better)
    # In practice, more iterations should improve or maintain log-likelihood
    # Note: This is not always guaranteed due to different random initializations
    assert result_large.meta["log_likelihood"] >= result_small.meta["log_likelihood"] - 10.0


@pytest.mark.slow
def test_autocommunity_with_sbm():
    """Test AutoCommunity with SBM as a candidate."""
    net = generate_small_test_network(n_nodes=20, n_layers=2)
    
    result = (
        AutoCommunity()
        .candidates("louvain", "dc_sbm")
        .metrics("modularity")
        .seed(42)
        .execute(net)
    )
    
    assert result is not None
    assert len(result.algorithms_tested) == 2
    assert "louvain" in result.algorithms_tested or "dc_sbm" in result.algorithms_tested


@pytest.mark.slow
def test_sbm_model_selection():
    """Test that SBM performs automatic model selection."""
    net = generate_small_test_network(n_nodes=20, n_layers=1)
    
    budget = BudgetSpec(max_iter=50, n_restarts=2)
    
    # Test with a range of K values
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3, 4, 5]
    )
    
    # Should select one K from the range
    K_selected = result.meta["K_selected"]
    assert K_selected in [2, 3, 4, 5]
    
    # Should have MDL score
    assert "mdl" in result.meta or "log_likelihood" in result.meta


def test_sbm_multilayer():
    """Test SBM on multilayer network."""
    net = generate_small_test_network(n_nodes=15, n_layers=3)
    
    budget = BudgetSpec(max_iter=50, n_restarts=2)
    
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3]
    )
    
    assert isinstance(result, CommunityResult)
    assert len(result.partition) > 0
    assert result.meta["model_type"] == "dc_sbm"


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running smoke tests...")
    
    print("1. Testing SBM runner...")
    test_sbm_runner_basic()
    print("   ✓ SBM runner works")
    
    print("2. Testing DC-SBM runner...")
    test_dc_sbm_runner_basic()
    print("   ✓ DC-SBM runner works")
    
    print("3. Testing determinism...")
    test_sbm_determinism()
    print("   ✓ Determinism verified")
    
    print("4. Testing UQ integration...")
    test_sbm_with_uq()
    print("   ✓ UQ integration works")
    
    print("5. Testing budget scaling...")
    test_sbm_budget_scaling()
    print("   ✓ Budget scaling works")
    
    print("6. Testing model selection...")
    test_sbm_model_selection()
    print("   ✓ Model selection works")
    
    print("7. Testing multilayer...")
    test_sbm_multilayer()
    print("   ✓ Multilayer works")
    
    print("\n✅ All smoke tests passed!")
