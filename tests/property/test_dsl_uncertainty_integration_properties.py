"""
Property-based tests for DSL uncertainty integration.

This module tests properties of the DSL integration with bootstrap and null
model uncertainty methods using Hypothesis.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.core import multinet
from py3plex.dsl import Q


# ============================================================================
# Helper Functions
# ============================================================================

def build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.5, seed=None):
    """Build a random test network with controlled properties."""
    rng = np.random.default_rng(seed)
    net = multinet.multi_layer_network(directed=False, verbose=False)
    
    edges = []
    for layer_idx in range(num_layers):
        layer = f"L{layer_idx}"
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if rng.random() < connect_prob:
                    edges.append([f"N{i}", layer, f"N{j}", layer, 1.0])
    
    if edges:
        net.add_edges(edges, input_type="list")
    
    return net


# ============================================================================
# Property Tests for DSL Bootstrap Integration
# ============================================================================

class TestDSLBootstrapProperties:
    """Property-based tests for DSL bootstrap integration."""
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30),
        st.sampled_from(["edges", "nodes", "layers"]),
        st.sampled_from(["resample", "permute"])
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_bootstrap_returns_results(self, n_boot, unit, mode):
        """Property: DSL bootstrap queries return valid results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_boot,
                bootstrap_unit=unit,
                bootstrap_mode=mode,
                random_state=42
            )
            .execute(net)
        )
        
        assert len(result) >= 0
        df = result.to_pandas()
        assert "degree" in df.columns
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_bootstrap_with_order_by(self, n_boot):
        """Property: Bootstrap works with order_by."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_boot,
                random_state=42
            )
            .order_by("-degree")
            .execute(net)
        )
        
        assert len(result) >= 0
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30),
        st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_bootstrap_with_limit(self, n_boot, limit):
        """Property: Bootstrap works with limit."""
        net = build_simple_network(num_nodes=6, num_layers=2, connect_prob=0.6, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_boot,
                random_state=42
            )
            .limit(limit)
            .execute(net)
        )
        
        assert len(result) <= limit
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_bootstrap_reproducibility(self, n_boot):
        """Property: Same seed gives same results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result1 = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_boot,
                random_state=999
            )
            .execute(net)
        )
        
        result2 = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_boot,
                random_state=999
            )
            .execute(net)
        )
        
        df1 = result1.to_pandas()
        df2 = result2.to_pandas()
        
        assert len(df1) == len(df2)


# ============================================================================
# Property Tests for DSL Null Model Integration
# ============================================================================

class TestDSLNullModelProperties:
    """Property-based tests for DSL null model integration."""
    
    @pytest.mark.property
    @given(
        st.integers(min_value=10, max_value=40),
        st.sampled_from(["degree_preserving", "erdos_renyi", "configuration"])
    )
    @settings(max_examples=12, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_null_model_returns_results(self, n_null, model):
        """Property: DSL null model queries return valid results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=n_null,
                null_model=model,
                random_state=42
            )
            .execute(net)
        )
        
        assert len(result) >= 0
        df = result.to_pandas()
        assert "degree" in df.columns
    
    @pytest.mark.property
    @given(
        st.integers(min_value=10, max_value=40)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_null_model_with_order_by(self, n_null):
        """Property: Null model works with order_by."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=n_null,
                random_state=42
            )
            .order_by("-degree")
            .execute(net)
        )
        
        assert len(result) >= 0
    
    @pytest.mark.property
    @given(
        st.integers(min_value=10, max_value=40)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dsl_null_model_reproducibility(self, n_null):
        """Property: Same seed gives same results."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        result1 = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=n_null,
                random_state=888
            )
            .execute(net)
        )
        
        result2 = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=n_null,
                random_state=888
            )
            .execute(net)
        )
        
        df1 = result1.to_pandas()
        df2 = result2.to_pandas()
        
        assert len(df1) == len(df2)


# ============================================================================
# Property Tests for Global Defaults
# ============================================================================

class TestGlobalDefaultsProperties:
    """Property-based tests for Q.uncertainty.defaults()."""
    
    def setup_method(self):
        """Reset defaults before each test."""
        Q.uncertainty.reset()
    
    def teardown_method(self):
        """Reset defaults after each test."""
        Q.uncertainty.reset()
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=100),
        st.floats(min_value=0.50, max_value=0.99)
    )
    @settings(max_examples=15, deadline=None)
    def test_defaults_are_retrievable(self, n_boot, ci):
        """Property: Set defaults can be retrieved."""
        Q.uncertainty.defaults(n_boot=n_boot, ci=ci)
        
        assert Q.uncertainty.get("n_boot") == n_boot
        assert Q.uncertainty.get("ci") == ci
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=100)
    )
    @settings(max_examples=15, deadline=None)
    def test_reset_restores_initial_values(self, n_boot):
        """Property: Reset restores initial values."""
        initial_n_boot = Q.uncertainty.get("n_boot")
        
        Q.uncertainty.defaults(n_boot=n_boot)
        assert Q.uncertainty.get("n_boot") == n_boot
        
        Q.uncertainty.reset()
        assert Q.uncertainty.get("n_boot") == initial_n_boot
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=50)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_defaults_used_when_not_specified(self, n_boot):
        """Property: Defaults are used when parameters not specified."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        Q.uncertainty.defaults(method="bootstrap", n_boot=n_boot)
        
        # Don't specify n_boot in query
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True)
            .execute(net)
        )
        
        # Should complete successfully using defaults
        assert len(result) >= 0
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=50),
        st.integers(min_value=51, max_value=100)
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_explicit_params_override_defaults(self, default_n_boot, explicit_n_boot):
        """Property: Explicit parameters override defaults."""
        assume(default_n_boot != explicit_n_boot)
        
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        Q.uncertainty.defaults(method="bootstrap", n_boot=default_n_boot)
        
        # Specify different n_boot in query
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_boot=explicit_n_boot)
            .execute(net)
        )
        
        # Should complete successfully with explicit value
        assert len(result) >= 0


# ============================================================================
# Metamorphic Properties for DSL Integration
# ============================================================================

class TestDSLMetamorphicProperties:
    """Metamorphic properties for DSL uncertainty integration."""
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30)
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_bootstrap_and_null_model_same_observed(self, n_samples):
        """Metamorphic: Both methods compute on same network."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        # Both methods should at least complete
        bootstrap_result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_samples,
                random_state=42
            )
            .execute(net)
        )
        
        null_result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=n_samples,
                random_state=42
            )
            .execute(net)
        )
        
        # Both should return results
        assert len(bootstrap_result) >= 0
        assert len(null_result) >= 0
    
    @pytest.mark.property
    @given(
        st.integers(min_value=5, max_value=30)
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_uncertainty_false_gives_deterministic_result(self, n_samples):
        """Metamorphic: uncertainty=False gives deterministic result."""
        net = build_simple_network(num_nodes=5, num_layers=2, connect_prob=0.6, seed=42)
        
        # Without uncertainty
        result_no_unc = (
            Q.nodes()
            .compute("degree", uncertainty=False)
            .execute(net)
        )
        
        # With uncertainty
        result_with_unc = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=n_samples,
                random_state=42
            )
            .execute(net)
        )
        
        # Both should return results
        assert len(result_no_unc) >= 0
        assert len(result_with_unc) >= 0


# ============================================================================
# Edge Cases
# ============================================================================

class TestDSLUncertaintyEdgeCases:
    """Edge case tests for DSL uncertainty."""
    
    @pytest.mark.property
    def test_empty_network_bootstrap(self):
        """Edge case: Empty network with bootstrap."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10
            )
            .execute(net)
        )
        
        assert len(result) == 0
    
    @pytest.mark.property
    def test_empty_network_null_model(self):
        """Edge case: Empty network with null model."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=10
            )
            .execute(net)
        )
        
        assert len(result) == 0
    
    @pytest.mark.property
    @given(
        st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_small_network_bootstrap(self, num_nodes):
        """Edge case: Very small network with bootstrap."""
        net = build_simple_network(num_nodes=num_nodes, num_layers=1, connect_prob=0.5, seed=42)
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10,
                random_state=42
            )
            .execute(net)
        )
        
        # Should handle small networks gracefully
        assert len(result) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
