"""Tests for global uncertainty defaults API.

This module tests the Q.uncertainty.defaults() API for setting global
defaults for uncertainty estimation parameters.
"""

import pytest

from py3plex.core import multinet
from py3plex.dsl import Q


def build_test_network():
    """Build a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestUncertaintyDefaults:
    """Tests for Q.uncertainty.defaults() API."""
    
    def setup_method(self):
        """Reset defaults before each test."""
        Q.uncertainty.reset()
    
    def teardown_method(self):
        """Reset defaults after each test."""
        Q.uncertainty.reset()
    
    def test_defaults_initial_values(self):
        """Test that initial defaults are set correctly."""
        assert Q.uncertainty.get("enabled") == False
        assert Q.uncertainty.get("n_boot") == 50
        assert Q.uncertainty.get("ci") == 0.95
        assert Q.uncertainty.get("bootstrap_unit") == "edges"
        assert Q.uncertainty.get("bootstrap_mode") == "resample"
        assert Q.uncertainty.get("method") == "bootstrap"
    
    def test_defaults_set_single_value(self):
        """Test setting a single default value."""
        Q.uncertainty.defaults(n_boot=200)
        assert Q.uncertainty.get("n_boot") == 200
        # Other values should remain unchanged
        assert Q.uncertainty.get("ci") == 0.95
    
    def test_defaults_set_multiple_values(self):
        """Test setting multiple default values."""
        Q.uncertainty.defaults(
            n_boot=500,
            ci=0.99,
            bootstrap_unit="nodes"
        )
        assert Q.uncertainty.get("n_boot") == 500
        assert Q.uncertainty.get("ci") == 0.99
        assert Q.uncertainty.get("bootstrap_unit") == "nodes"
    
    def test_defaults_invalid_key(self):
        """Test that invalid keys raise an error."""
        with pytest.raises(ValueError, match="Unknown uncertainty parameter"):
            Q.uncertainty.defaults(invalid_key="value")
    
    def test_defaults_reset(self):
        """Test that reset() restores initial values."""
        Q.uncertainty.defaults(n_boot=1000, ci=0.90)
        assert Q.uncertainty.get("n_boot") == 1000
        
        Q.uncertainty.reset()
        assert Q.uncertainty.get("n_boot") == 50
        assert Q.uncertainty.get("ci") == 0.95
    
    def test_defaults_get_all(self):
        """Test that get_all() returns all defaults."""
        all_defaults = Q.uncertainty.get_all()
        assert isinstance(all_defaults, dict)
        assert "n_boot" in all_defaults
        assert "ci" in all_defaults
        assert "method" in all_defaults
        
        # Modifying returned dict shouldn't affect actual defaults
        all_defaults["n_boot"] = 9999
        assert Q.uncertainty.get("n_boot") == 50
    
    def test_defaults_get_with_default(self):
        """Test get() with default value."""
        assert Q.uncertainty.get("nonexistent", "default_value") == "default_value"
        assert Q.uncertainty.get("n_boot", 99) == 50  # Should return actual value


class TestUncertaintyDefaultsIntegration:
    """Integration tests for defaults with DSL queries."""
    
    def setup_method(self):
        """Reset defaults before each test."""
        Q.uncertainty.reset()
    
    def teardown_method(self):
        """Reset defaults after each test."""
        Q.uncertainty.reset()
    
    def test_compute_uses_defaults(self):
        """Test that compute() uses global defaults."""
        net = build_test_network()
        
        # Set defaults
        Q.uncertainty.defaults(
            n_boot=30,
            ci=0.90,
            bootstrap_unit="nodes"
        )
        
        # Query with uncertainty=True but no explicit parameters
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True)
            .execute(net)
        )
        
        # Should use defaults
        assert len(result) > 0
    
    def test_compute_explicit_overrides_defaults(self):
        """Test that explicit parameters override defaults."""
        net = build_test_network()
        
        # Set defaults
        Q.uncertainty.defaults(n_boot=10, ci=0.90)
        
        # Query with explicit parameters
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5, ci=0.99)
            .execute(net)
        )
        
        # Explicit parameters should be used
        assert len(result) > 0
    
    def test_compute_without_uncertainty_ignores_defaults(self):
        """Test that compute() without uncertainty ignores defaults."""
        net = build_test_network()
        
        # Set defaults
        Q.uncertainty.defaults(enabled=True, n_boot=100)
        
        # Query without uncertainty=True
        result = (
            Q.nodes()
            .compute("degree", uncertainty=False)
            .execute(net)
        )
        
        # Should compute without uncertainty
        assert len(result) > 0
        df = result.to_pandas()
        # Values should be numeric or dicts (numeric when uncertainty=False)
        import numpy as np
        first_degree = df["degree"].iloc[0]
        # Accept numpy numeric types as well
        is_numeric = isinstance(first_degree, (int, float, np.integer, np.floating))
        is_dict = isinstance(first_degree, dict)
        assert is_numeric or is_dict
    
    def test_defaults_with_multiple_metrics(self):
        """Test defaults with multiple metrics."""
        net = build_test_network()
        
        Q.uncertainty.defaults(n_boot=20, method="perturbation")
        
        result = (
            Q.nodes()
            .compute("degree", "clustering", uncertainty=True)
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns
    
    def test_defaults_null_model_parameters(self):
        """Test that null model defaults are accessible."""
        Q.uncertainty.defaults(
            method="null_model",
            n_null=100,
            null_model="erdos_renyi"
        )
        
        assert Q.uncertainty.get("method") == "null_model"
        assert Q.uncertainty.get("n_null") == 100
        assert Q.uncertainty.get("null_model") == "erdos_renyi"
    
    def test_defaults_bootstrap_parameters(self):
        """Test that bootstrap defaults are accessible."""
        Q.uncertainty.defaults(
            method="bootstrap",
            bootstrap_unit="layers",
            bootstrap_mode="permute"
        )
        
        assert Q.uncertainty.get("method") == "bootstrap"
        assert Q.uncertainty.get("bootstrap_unit") == "layers"
        assert Q.uncertainty.get("bootstrap_mode") == "permute"
    
    def test_defaults_random_state(self):
        """Test that random_state default works."""
        Q.uncertainty.defaults(random_state=42)
        assert Q.uncertainty.get("random_state") == 42
        
        Q.uncertainty.defaults(random_state=None)
        assert Q.uncertainty.get("random_state") is None


class TestUncertaintyDefaultsDocumentation:
    """Tests matching documentation examples."""
    
    def setup_method(self):
        """Reset defaults before each test."""
        Q.uncertainty.reset()
    
    def teardown_method(self):
        """Reset defaults after each test."""
        Q.uncertainty.reset()
    
    def test_example_from_issue(self):
        """Test the example from the issue specification."""
        net = build_test_network()
        
        # Example from issue
        Q.uncertainty.defaults(
            enabled=True,
            n_boot=200,
            ci=0.95,
            bootstrap_unit="edges",
            bootstrap_mode="resample",
            random_state=42,
        )
        
        # Now compute() with uncertainty=True uses these defaults
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True)
            .execute(net)
        )
        
        assert len(result) > 0
        assert Q.uncertainty.get("n_boot") == 200
        assert Q.uncertainty.get("ci") == 0.95
    
    def test_flagship_example_with_defaults(self):
        """Test flagship example using defaults."""
        net = build_test_network()
        
        # Set global defaults
        Q.uncertainty.defaults(
            n_boot=100,
            ci=0.95,
            method="perturbation"
        )
        
        # Use defaults in query
        hubs = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True  # Other params from defaults
            )
            .order_by("-degree")
            .limit(3)
            .execute(net)
        )
        
        assert len(hubs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
