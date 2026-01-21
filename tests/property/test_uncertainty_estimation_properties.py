"""
Property-based tests for uncertainty estimation functions.

Tests the mathematical properties and invariants that uncertainty estimation
should satisfy.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.core import multinet
from py3plex.uncertainty import (
    StatSeries,
    ResamplingStrategy,
    estimate_uncertainty,
    uncertainty_enabled,
    get_uncertainty_config,
    UncertaintyMode,
)
from py3plex.algorithms.centrality_toolkit import multilayer_pagerank


# ============================================================================
# Helper Functions
# ============================================================================

def build_test_network(num_nodes=5, num_layers=2):
    """Build a deterministic test network."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    # Create a simple connected structure
    for layer_idx in range(num_layers):
        layer = f"L{layer_idx}"
        for i in range(num_nodes - 1):
            net.add_edges([
                [f"N{i}", layer, f"N{i+1}", layer, 1.0]
            ], input_type="list")
    
    return net


# ============================================================================
# Property Tests for estimate_uncertainty
# ============================================================================

class TestEstimateUncertaintyProperties:
    """Property-based tests for estimate_uncertainty function."""
    
    @given(st.integers(min_value=2, max_value=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_statseries_for_dict_metrics(self, n_runs):
        """Property: Returns StatSeries when metric returns dict."""
        net = build_test_network()
        
        def dict_metric(network):
            return {node: 1.0 for node in network.get_nodes()}
        
        result = estimate_uncertainty(
            net,
            dict_metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        assert isinstance(result, StatSeries)
        assert len(result) > 0
    
    @given(st.integers(min_value=2, max_value=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_float_for_scalar_metrics(self, n_runs):
        """Property: Returns float when metric returns scalar."""
        net = build_test_network()
        
        def scalar_metric(network):
            return float(len(list(network.get_nodes())))
        
        result = estimate_uncertainty(
            net,
            scalar_metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        assert isinstance(result, (int, float, np.number))
    
    @given(
        st.integers(min_value=2, max_value=10),
        st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_result_length_matches_network_size(self, num_nodes, n_runs):
        """Property: Result length matches number of nodes."""
        net = build_test_network(num_nodes=num_nodes)
        
        def node_metric(network):
            return {node: 1.0 for node in network.get_nodes()}
        
        result = estimate_uncertainty(
            net,
            node_metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        # Number of nodes in network (each node appears in each layer)
        expected_size = len(list(net.get_nodes()))
        assert len(result) == expected_size
    
    @given(st.integers(min_value=3, max_value=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_seed_reproducibility(self, n_runs):
        """Property: Same seed gives same results."""
        net = build_test_network()
        
        def metric(network):
            return {node: float(hash(str(node)) % 100) for node in network.get_nodes()}
        
        result1 = estimate_uncertainty(
            net,
            metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        result2 = estimate_uncertainty(
            net,
            metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        np.testing.assert_array_almost_equal(result1.mean, result2.mean)
        np.testing.assert_array_almost_equal(result1.std, result2.std)
    
    @given(st.integers(min_value=10, max_value=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_perturbation_creates_variance(self, n_runs):
        """Property: Perturbation strategy should create non-zero variance."""
        net = build_test_network(num_nodes=6)
        
        def metric(network):
            # Metric that's sensitive to network structure
            degrees = {}
            for node in network.get_nodes():
                degrees[node] = network.core_network.degree(node)
            return degrees
        
        result = estimate_uncertainty(
            net,
            metric,
            n_runs=n_runs,
            resampling=ResamplingStrategy.PERTURBATION,
            perturbation_params={"edge_drop_p": 0.1},
            random_seed=42
        )
        
        # With edge drops, we should get some variance
        assert result.std is not None
        # At least some nodes should have non-zero std
        # (might not be all due to small network and randomness)
        assert np.sum(result.std > 0) > 0


# ============================================================================
# Property Tests for multilayer_pagerank with uncertainty
# ============================================================================

class TestPageRankUncertaintyProperties:
    """Property-based tests for PageRank with uncertainty."""
    
    @given(st.integers(min_value=3, max_value=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pagerank_deterministic_sum_equals_one(self, num_nodes):
        """Property: PageRank values sum to 1 in deterministic mode."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = multilayer_pagerank(net, uncertainty=False)
        
        total = np.sum(result.mean)
        # PageRank should sum to approximately 1
        assert 0.95 < total < 1.05
    
    @given(st.integers(min_value=3, max_value=8))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pagerank_values_positive(self, num_nodes):
        """Property: All PageRank values are positive."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = multilayer_pagerank(
            net,
            uncertainty=True,
            n_runs=5,
            resampling=ResamplingStrategy.SEED,
            random_seed=42
        )
        
        assert np.all(result.mean > 0)
    
    @given(st.integers(min_value=3, max_value=8))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pagerank_std_non_negative(self, num_nodes):
        """Property: PageRank std values are non-negative when present."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = multilayer_pagerank(
            net,
            uncertainty=True,
            n_runs=5,
            resampling=ResamplingStrategy.PERTURBATION,
            random_seed=42
        )
        
        if result.std is not None:
            assert np.all(result.std >= 0)
    
    @given(
        st.integers(min_value=3, max_value=8),
        st.floats(min_value=0.7, max_value=0.95)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pagerank_alpha_affects_results(self, num_nodes, alpha):
        """Property: Different alpha values give different results."""
        net = build_test_network(num_nodes=num_nodes)
        
        result1 = multilayer_pagerank(net, alpha=0.85, uncertainty=False)
        result2 = multilayer_pagerank(net, alpha=alpha, uncertainty=False)
        
        # Results should differ (unless alpha happens to be exactly 0.85)
        if abs(alpha - 0.85) > 0.01:
            assert not np.allclose(result1.mean, result2.mean)


# ============================================================================
# Property Tests for Context Manager
# ============================================================================

class TestUncertaintyContextProperties:
    """Property-based tests for uncertainty context management."""
    
    @given(st.integers(min_value=2, max_value=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_context_preserves_n_runs(self, n_runs):
        """Property: Context manager preserves n_runs setting."""
        with uncertainty_enabled(n_runs=n_runs):
            cfg = get_uncertainty_config()
            assert cfg.default_n_runs == n_runs
    
    @given(st.sampled_from(list(ResamplingStrategy)))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_context_preserves_strategy(self, strategy):
        """Property: Context manager preserves resampling strategy."""
        with uncertainty_enabled(resampling=strategy):
            cfg = get_uncertainty_config()
            assert cfg.default_resampling == strategy
    
    def test_context_sets_mode_to_on(self):
        """Property: uncertainty_enabled sets mode to ON."""
        original_mode = get_uncertainty_config().mode
        
        with uncertainty_enabled():
            cfg = get_uncertainty_config()
            assert cfg.mode == UncertaintyMode.ON
        
        # After exiting, mode should be restored
        final_mode = get_uncertainty_config().mode
        assert final_mode == original_mode
    
    def test_nested_contexts_work(self):
        """Property: Nested contexts work correctly."""
        with uncertainty_enabled(n_runs=10):
            cfg1 = get_uncertainty_config()
            assert cfg1.default_n_runs == 10
            
            with uncertainty_enabled(n_runs=20):
                cfg2 = get_uncertainty_config()
                assert cfg2.default_n_runs == 20
            
            # After inner context, outer should be restored
            cfg3 = get_uncertainty_config()
            assert cfg3.default_n_runs == 10


# ============================================================================
# Metamorphic Properties
# ============================================================================

class TestMetamorphicProperties:
    """Metamorphic properties - relationships between inputs and outputs."""
    
    @pytest.mark.slow
    @given(st.integers(min_value=10, max_value=20))
    @settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_more_runs_gives_valid_results(self, base_runs):
        """Property: More runs should give valid statistical results."""
        # This is a weaker version of the CI width test - just check validity
        net = build_test_network(num_nodes=6)
        
        result_few = multilayer_pagerank(
            net,
            uncertainty=True,
            n_runs=base_runs,
            resampling=ResamplingStrategy.PERTURBATION,
            random_seed=42
        )
        
        result_many = multilayer_pagerank(
            net,
            uncertainty=True,
            n_runs=base_runs * 2,
            resampling=ResamplingStrategy.PERTURBATION,
            random_seed=43  # Different seed to avoid exact same samples
        )
        
        # Both should have quantiles
        assert result_few.quantiles is not None
        assert result_many.quantiles is not None
        
        # Both should have valid confidence intervals
        # Lower quantile should be <= upper quantile for all nodes
        assert np.all(
            result_few.quantiles[0.025] <= result_few.quantiles[0.975]
        )
        assert np.all(
            result_many.quantiles[0.025] <= result_many.quantiles[0.975]
        )
        
        # Both should have non-negative std
        assert np.all(result_few.std >= 0)
        assert np.all(result_many.std >= 0)
        
        # The means should be similar (same network, same algorithm)
        # They might differ due to perturbations but should be in same ballpark
        mean_diff = np.abs(result_few.mean - result_many.mean)
        # Mean difference should be reasonable
        assert np.mean(mean_diff) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
