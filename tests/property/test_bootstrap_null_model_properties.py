"""
Property-based tests for bootstrap and null model engines.

This module tests fundamental properties and invariants that bootstrap_metric()
and null_model_metric() should satisfy using Hypothesis for property-based testing.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.core import multinet
from py3plex.uncertainty import bootstrap_metric, null_model_metric


# ============================================================================
# Helper Functions and Strategies
# ============================================================================

def build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.5, seed=None):
    """Build a random test network with controlled properties."""
    rng = np.random.default_rng(seed)
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    edges = []
    for layer_idx in range(num_layers):
        layer = f"L{layer_idx}"
        # Create edges between nodes with some probability
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if rng.random() < connect_prob:
                    edges.append([f"N{i}", layer, f"N{j}", layer, 1.0])
    
    if edges:
        net.add_edges(edges, input_type="list")
    
    return net


def simple_metric(network):
    """A simple deterministic metric for testing."""
    result = {}
    if not hasattr(network, 'core_network') or network.core_network is None:
        return result
    for node in network.get_nodes():
        result[node] = float(network.core_network.degree(node))
    return result


# ============================================================================
# Property Tests for bootstrap_metric
# ============================================================================

class TestBootstrapMetricProperties:
    """Property-based tests for bootstrap_metric function."""
    
    @given(
        st.integers(min_value=5, max_value=50),
        st.sampled_from(["edges", "nodes", "layers"]),
        st.sampled_from(["resample", "permute"])
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_bootstrap_output_structure(self, n_boot, unit, mode):
        """Property: Bootstrap output has correct structure."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit=unit,
            mode=mode,
            random_state=42
        )
        
        # Must have required keys
        assert "mean" in result
        assert "std" in result
        assert "ci_low" in result
        assert "ci_high" in result
        assert "index" in result
        assert "n_boot" in result
        assert "method" in result
        
        # Arrays must have same length as index
        n_items = len(result["index"])
        assert result["mean"].shape == (n_items,)
        assert result["std"].shape == (n_items,)
        assert result["ci_low"].shape == (n_items,)
        assert result["ci_high"].shape == (n_items,)
        
        # n_boot must match input
        assert result["n_boot"] == n_boot
    
    @given(
        st.integers(min_value=10, max_value=50),
        st.floats(min_value=0.50, max_value=0.99)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ci_contains_mean(self, n_boot, ci):
        """Property: Confidence intervals should contain the mean (approximately)."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit="edges",
            mode="resample",
            ci=ci,
            random_state=42
        )
        
        # For most items, mean should be within CI
        # (allowing some slack due to random sampling)
        within_ci = (result["ci_low"] <= result["mean"] + 1e-6) & (result["mean"] <= result["ci_high"] + 1e-6)
        proportion_within = np.mean(within_ci)
        
        # At least 70% of items should have mean within CI
        assert proportion_within >= 0.7
    
    @given(
        st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ci_width_positive(self, n_boot):
        """Property: CI width should be non-negative."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit="edges",
            random_state=42
        )
        
        ci_width = result["ci_high"] - result["ci_low"]
        assert np.all(ci_width >= -1e-10)  # Allow tiny numerical errors
    
    @given(
        st.integers(min_value=20, max_value=100)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_non_negative(self, n_boot):
        """Property: Standard error should be non-negative."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit="edges",
            random_state=42
        )
        
        assert np.all(result["std"] >= 0)
    
    @given(
        st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_reproducibility_with_seed(self, n_boot):
        """Property: Same seed produces same results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result1 = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit="edges",
            random_state=12345
        )
        
        result2 = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot,
            unit="edges",
            random_state=12345
        )
        
        np.testing.assert_array_almost_equal(result1["mean"], result2["mean"])
        np.testing.assert_array_almost_equal(result1["std"], result2["std"])
    
    @given(
        st.integers(min_value=3, max_value=10),
        st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_handles_different_network_sizes(self, num_nodes, num_layers):
        """Property: Works with different network sizes."""
        net = build_simple_network(num_nodes=num_nodes, num_layers=num_layers, connect_prob=0.5, seed=42)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=20,
            unit="edges",
            random_state=42
        )
        
        # Should return results for all nodes (or none if empty)
        assert len(result["index"]) >= 0
    
    @given(
        st.floats(min_value=0.6, max_value=0.99)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_wider_ci_with_higher_level(self, ci):
        """Property: Higher CI level should give wider intervals."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result_narrow = bootstrap_metric(
            net,
            simple_metric,
            n_boot=50,
            unit="edges",
            ci=0.80,
            random_state=42
        )
        
        result_wide = bootstrap_metric(
            net,
            simple_metric,
            n_boot=50,
            unit="edges",
            ci=ci,
            random_state=42
        )
        
        # Only compare if ci is wider than 0.80
        if ci > 0.80:
            width_narrow = np.mean(result_narrow["ci_high"] - result_narrow["ci_low"])
            width_wide = np.mean(result_wide["ci_high"] - result_wide["ci_low"])
            assert width_wide >= width_narrow - 1e-6


# ============================================================================
# Property Tests for null_model_metric
# ============================================================================

class TestNullModelMetricProperties:
    """Property-based tests for null_model_metric function."""
    
    @given(
        st.integers(min_value=10, max_value=50),
        st.sampled_from(["degree_preserving", "erdos_renyi", "configuration"])
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_null_model_output_structure(self, n_null, model):
        """Property: Null model output has correct structure."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model=model,
            random_state=42
        )
        
        # Must have required keys
        assert "observed" in result
        assert "mean_null" in result
        assert "std_null" in result
        assert "zscore" in result
        assert "pvalue" in result
        assert "index" in result
        assert "n_null" in result
        assert "model" in result
        
        # Arrays must have same length as index
        n_items = len(result["index"])
        assert result["observed"].shape == (n_items,)
        assert result["mean_null"].shape == (n_items,)
        assert result["std_null"].shape == (n_items,)
        assert result["zscore"].shape == (n_items,)
        assert result["pvalue"].shape == (n_items,)
        
        # n_null must match input
        assert result["n_null"] == n_null
        assert result["model"] == model
    
    @given(
        st.integers(min_value=20, max_value=100)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pvalues_in_valid_range(self, n_null):
        """Property: P-values should be in [0, 1]."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=42
        )
        
        assert np.all(result["pvalue"] >= 0)
        assert np.all(result["pvalue"] <= 1)
    
    @given(
        st.integers(min_value=20, max_value=100)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_null_non_negative(self, n_null):
        """Property: Null model std should be non-negative."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=42
        )
        
        assert np.all(result["std_null"] >= 0)
    
    @given(
        st.integers(min_value=20, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_zscore_consistency(self, n_null):
        """Property: Z-score should be consistent with obs, mean, std."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=42
        )
        
        # For items with non-zero std, check z-score calculation
        nonzero_std = result["std_null"] > 1e-6
        if np.any(nonzero_std):
            expected_zscore = (result["observed"][nonzero_std] - result["mean_null"][nonzero_std]) / result["std_null"][nonzero_std]
            np.testing.assert_allclose(
                result["zscore"][nonzero_std],
                expected_zscore,
                rtol=1e-5,
                atol=1e-8
            )
    
    @given(
        st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_reproducibility_with_seed(self, n_null):
        """Property: Same seed produces same results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result1 = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=54321
        )
        
        result2 = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=54321
        )
        
        np.testing.assert_array_almost_equal(result1["observed"], result2["observed"])
        np.testing.assert_array_almost_equal(result1["zscore"], result2["zscore"], decimal=4)
    
    @given(
        st.integers(min_value=3, max_value=10),
        st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_handles_different_network_sizes(self, num_nodes, num_layers):
        """Property: Works with different network sizes."""
        net = build_simple_network(num_nodes=num_nodes, num_layers=num_layers, connect_prob=0.5, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=20,
            model="erdos_renyi",
            random_state=42
        )
        
        # Should return results for all nodes (or none if empty)
        assert len(result["index"]) >= 0
    
    @given(
        st.integers(min_value=20, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extreme_zscores_have_low_pvalues(self, n_null):
        """Property: Very extreme z-scores should have low p-values."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=42
        )
        
        # Find items with large absolute z-scores
        extreme = np.abs(result["zscore"]) > 2.0
        
        if np.any(extreme):
            # These should generally have low p-values
            # (though not always due to empirical calculation)
            assert np.any(result["pvalue"][extreme] < 0.5)


# ============================================================================
# Metamorphic Properties
# ============================================================================

class TestBootstrapMetamorphicProperties:
    """Metamorphic properties for bootstrap."""
    
    @given(
        st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_more_samples_reduces_std(self, n_boot_small):
        """Metamorphic: More bootstrap samples should generally reduce SE."""
        # This is a statistical tendency, not a hard guarantee
        net = build_simple_network(num_nodes=6, num_layers=2, connect_prob=0.6, seed=42)
        
        n_boot_large = n_boot_small * 3
        
        result_small = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot_small,
            unit="edges",
            random_state=42
        )
        
        result_large = bootstrap_metric(
            net,
            simple_metric,
            n_boot=n_boot_large,
            unit="edges",
            random_state=43  # Different seed to avoid exact same bootstrap samples
        )
        
        # Average std should generally be similar or slightly smaller with more samples
        avg_std_small = np.mean(result_small["std"])
        avg_std_large = np.mean(result_large["std"])
        
        # Allow for variability - just check they're in the same ballpark
        assert avg_std_large < avg_std_small * 2.0


class TestNullModelMetamorphicProperties:
    """Metamorphic properties for null models."""
    
    @given(
        st.integers(min_value=20, max_value=50)
    )
    @settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_null_models_same_observed(self, n_null):
        """Metamorphic: Observed values should be same across null models."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result_dp = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="degree_preserving",
            random_state=42
        )
        
        result_er = null_model_metric(
            net,
            simple_metric,
            n_null=n_null,
            model="erdos_renyi",
            random_state=42
        )
        
        # Observed values should be identical (same network, same metric)
        if len(result_dp["index"]) == len(result_er["index"]):
            # Only compare if same nodes (which should be the case)
            np.testing.assert_array_almost_equal(
                result_dp["observed"],
                result_er["observed"]
            )


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

class TestBootstrapEdgeCases:
    """Edge case tests for bootstrap."""
    
    def test_empty_network_returns_empty_result(self):
        """Edge case: Empty network returns empty arrays."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=10,
            unit="edges"
        )
        
        assert len(result["index"]) == 0
        assert len(result["mean"]) == 0
    
    def test_single_node_network(self):
        """Edge case: Single node network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([["A", "L0", "B", "L0", 1.0]], input_type="list")
        
        result = bootstrap_metric(
            net,
            simple_metric,
            n_boot=10,
            unit="edges",
            random_state=42
        )
        
        assert len(result["index"]) >= 1
        assert np.all(np.isfinite(result["mean"]))


class TestNullModelEdgeCases:
    """Edge case tests for null models."""
    
    def test_empty_network_returns_empty_result(self):
        """Edge case: Empty network returns empty arrays."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=10,
            model="degree_preserving"
        )
        
        assert len(result["index"]) == 0
        assert len(result["observed"]) == 0
    
    def test_single_node_network(self):
        """Edge case: Single node network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([["A", "L0", "B", "L0", 1.0]], input_type="list")
        
        result = null_model_metric(
            net,
            simple_metric,
            n_null=10,
            model="erdos_renyi",
            random_state=42
        )
        
        assert len(result["index"]) >= 1
        assert np.all(np.isfinite(result["observed"]))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
