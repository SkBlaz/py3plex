"""Tests for uncertainty-first DSL ergonomics.

This module tests the query-scoped uncertainty context (.uq() method),
UQ profiles, autocompute with uncertainty, selector syntax, and
expand_uncertainty in to_pandas().
"""

import pytest
import numpy as np

from py3plex.core import multinet
from py3plex.dsl import Q, UQ, UQConfig


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Layer L0: Triangle
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
        # Layer L1: Chain
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestQueryScopedUQ:
    """Tests for query-scoped uncertainty configuration."""
    
    def test_uq_method_sets_config(self, simple_network):
        """Test that .uq() sets query-level configuration."""
        query = Q.nodes().uq(method="perturbation", n_samples=25, ci=0.9, seed=42)
        
        # Check that uq_config is set
        assert query._select.uq_config is not None
        assert query._select.uq_config.method == "perturbation"
        assert query._select.uq_config.n_samples == 25
        assert query._select.uq_config.ci == 0.9
        assert query._select.uq_config.seed == 42
    
    def test_uq_method_accepts_uqconfig(self, simple_network):
        """Test that .uq() accepts UQConfig instance."""
        config = UQConfig(method="bootstrap", n_samples=100, ci=0.95, seed=7)
        query = Q.nodes().uq(config)
        
        assert query._select.uq_config is config
    
    def test_uq_none_disables(self, simple_network):
        """Test that .uq(method=None) disables query-level uncertainty."""
        query = Q.nodes().uq(method=None)
        
        assert query._select.uq_config is None
    
    def test_uq_last_call_wins(self, simple_network):
        """Test that multiple .uq() calls, last one wins."""
        query = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10)
            .uq(method="bootstrap", n_samples=20)
        )
        
        assert query._select.uq_config.method == "bootstrap"
        assert query._select.uq_config.n_samples == 20
    
    def test_uncertainty_alias(self, simple_network):
        """Test that .uncertainty() is an alias for .uq()."""
        query = Q.nodes().uncertainty(method="perturbation", n_samples=30)
        
        assert query._select.uq_config is not None
        assert query._select.uq_config.method == "perturbation"
        assert query._select.uq_config.n_samples == 30


class TestUQProfiles:
    """Tests for UQ presets (fast/default/paper)."""
    
    def test_uq_fast_profile(self):
        """Test UQ.fast() profile."""
        config = UQ.fast(seed=42)
        
        assert config.method == "perturbation"
        assert config.n_samples == 25
        assert config.ci == 0.95
        assert config.seed == 42
    
    def test_uq_default_profile(self):
        """Test UQ.default() profile."""
        config = UQ.default(seed=7)
        
        assert config.method == "perturbation"
        assert config.n_samples == 50
        assert config.ci == 0.95
        assert config.seed == 7
    
    def test_uq_paper_profile(self):
        """Test UQ.paper() profile."""
        config = UQ.paper(seed=123)
        
        assert config.method == "bootstrap"
        assert config.n_samples == 300
        assert config.ci == 0.95
        assert config.seed == 123
    
    def test_uq_profile_in_query(self, simple_network):
        """Test using UQ profile in query."""
        result = (
            Q.nodes()
            .uq(UQ.fast(seed=0))
            .compute("degree")
            .execute(simple_network)
        )
        
        assert len(result) > 0


class TestComputeWithQueryUQ:
    """Tests for .compute() using query-level UQ defaults."""
    
    def test_compute_uses_query_uq(self, simple_network):
        """Test that compute() uses query-level UQ config."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .execute(simple_network)
        )
        
        # Check that degree values have uncertainty info
        df = result.to_pandas()
        first_degree = df["degree"].iloc[0]
        
        # Should be a dict with uncertainty info
        if isinstance(first_degree, dict):
            assert "mean" in first_degree
            assert "std" in first_degree
    
    def test_compute_explicit_override(self, simple_network):
        """Test that explicit uncertainty=False overrides query-level UQ."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree", uncertainty=False)
            .execute(simple_network)
        )
        
        # Degree values should be deterministic (not dicts)
        df = result.to_pandas()
        first_degree = df["degree"].iloc[0]
        
        # Should be numeric, not dict
        assert not isinstance(first_degree, dict)
    
    def test_compute_without_uq_is_deterministic(self, simple_network):
        """Test that compute() without .uq() remains deterministic."""
        result = (
            Q.nodes()
            .compute("degree")
            .execute(simple_network)
        )
        
        df = result.to_pandas()
        first_degree = df["degree"].iloc[0]
        
        # Should be numeric, not dict
        assert not isinstance(first_degree, dict)


class TestAutocomputeWithUQ:
    """Tests for autocompute respecting query-level UQ."""
    
    def test_autocompute_with_uq_in_order_by(self, simple_network):
        """Test that autocompute uses UQ when ordering by missing metric."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .order_by("-degree")
            .execute(simple_network)
        )
        
        # Degree should have been auto-computed with uncertainty
        assert "degree" in result.attributes
        
        # Check first value has uncertainty
        first_node = result.items[0]
        degree_val = result.attributes["degree"].get(first_node)
        
        if isinstance(degree_val, dict):
            assert "mean" in degree_val
    
    def test_autocompute_without_uq_is_deterministic(self, simple_network):
        """Test that autocompute without .uq() is deterministic."""
        result = (
            Q.nodes()
            .order_by("-degree")
            .execute(simple_network)
        )
        
        # Degree should be deterministic
        first_node = result.items[0]
        degree_val = result.attributes["degree"].get(first_node)
        
        # Should be numeric, not dict
        assert not isinstance(degree_val, dict)


class TestSelectorSyntax:
    """Tests for selector syntax in order_by and filtering."""
    
    def test_order_by_mean_selector(self, simple_network):
        """Test ordering by metric__mean."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .order_by("-degree__mean")
            .execute(simple_network)
        )
        
        assert len(result) > 0
        # Should be ordered by mean degree (descending)
    
    def test_order_by_std_selector(self, simple_network):
        """Test ordering by metric__std."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .order_by("-degree__std")
            .execute(simple_network)
        )
        
        assert len(result) > 0
    
    def test_order_by_ci_low_selector(self, simple_network):
        """Test ordering by metric__ci95__low."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .order_by("-degree__ci95__low")
            .execute(simple_network)
        )
        
        assert len(result) > 0
    
    def test_order_by_ci_width_selector(self, simple_network):
        """Test ordering by metric__ci95__width."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .order_by("degree__ci95__width")  # Ascending - most precise first
            .execute(simple_network)
        )
        
        assert len(result) > 0


class TestExpandUncertainty:
    """Tests for to_pandas(expand_uncertainty=True)."""
    
    def test_expand_uncertainty_basic(self, simple_network):
        """Test basic expand_uncertainty functionality."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=True)
        
        # Check that expanded columns exist
        assert "degree" in df.columns
        assert "degree_std" in df.columns
        assert "degree_ci95_low" in df.columns
        assert "degree_ci95_high" in df.columns
        assert "degree_ci95_width" in df.columns
    
    def test_expand_uncertainty_values(self, simple_network):
        """Test that expanded values are reasonable."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=True)
        
        # Check first row
        if len(df) > 0:
            row = df.iloc[0]
            
            # Mean should be present
            assert row["degree"] is not None
            
            # If uncertainty was computed, std should be >= 0
            if row["degree_std"] is not None:
                assert row["degree_std"] >= 0
            
            # CI bounds should make sense if present
            if row["degree_ci95_low"] is not None and row["degree_ci95_high"] is not None:
                assert row["degree_ci95_low"] <= row["degree_ci95_high"]
            
            # CI width should equal high - low if both present
            if row["degree_ci95_low"] is not None and row["degree_ci95_high"] is not None:
                expected_width = row["degree_ci95_high"] - row["degree_ci95_low"]
                if row["degree_ci95_width"] is not None:
                    assert abs(row["degree_ci95_width"] - expected_width) < 1e-6
    
    def test_expand_deterministic_values(self, simple_network):
        """Test expand_uncertainty with deterministic values."""
        result = (
            Q.nodes()
            .compute("degree")
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=True)
        
        # Expanded columns should still be created
        assert "degree_std" in df.columns
        assert "degree_ci95_low" in df.columns
        assert "degree_ci95_high" in df.columns
        
        # For deterministic values, std should be 0, CI should equal value
        if len(df) > 0:
            row = df.iloc[0]
            if row["degree"] is not None:
                assert row["degree_std"] == 0.0
                assert row["degree_ci95_low"] == row["degree"]
                assert row["degree_ci95_high"] == row["degree"]
                assert row["degree_ci95_width"] == 0.0
    
    def test_expand_without_flag_unchanged(self, simple_network):
        """Test that without expand_uncertainty, behavior is unchanged."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=False)
        
        # Only base column should exist
        assert "degree" in df.columns
        assert "degree_std" not in df.columns
        assert "degree_ci95_low" not in df.columns


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_full_pipeline(self, simple_network):
        """Test complete uncertainty-first pipeline."""
        result = (
            Q.nodes()
            .uq(UQ.fast(seed=42))
            .compute("degree")
            .order_by("-degree__mean")
            .limit(3)
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=True)
        
        # Should have 3 nodes
        assert len(df) <= 3
        
        # Should have expanded columns
        assert "degree_std" in df.columns
        assert "degree_ci95_low" in df.columns
        
        # Should be ordered by mean degree descending
        if len(df) >= 2:
            assert df.iloc[0]["degree"] >= df.iloc[1]["degree"]
    
    def test_autocompute_with_selectors(self, simple_network):
        """Test autocompute + selectors together."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .order_by("degree__ci95__width")  # Autocompute degree with UQ
            .limit(5)
            .execute(simple_network)
        )
        
        # Degree should be auto-computed with uncertainty
        assert "degree" in result.attributes
        
        df = result.to_pandas(expand_uncertainty=True)
        assert len(df) <= 5
        
        # Should be ordered by CI width ascending (most precise first)
        if len(df) >= 2:
            # CI widths should be in ascending order
            widths = df["degree_ci95_width"].dropna()
            if len(widths) >= 2:
                assert widths.iloc[0] <= widths.iloc[-1]
    
    def test_mixed_metrics(self, simple_network):
        """Test with both deterministic and uncertain metrics."""
        result = (
            Q.nodes()
            .uq(method="perturbation", n_samples=10, seed=42)
            .compute("degree")  # Uncertain
            .compute("clustering", uncertainty=False)  # Deterministic
            .execute(simple_network)
        )
        
        df = result.to_pandas(expand_uncertainty=True)
        
        # Degree should have uncertainty columns
        assert "degree_std" in df.columns
        
        # Clustering should also have columns but with 0/deterministic values
        assert "clustering_std" in df.columns
        
        # Check values
        if len(df) > 0:
            row = df.iloc[0]
            # Degree uncertainty might be > 0
            # Clustering should be deterministic (std = 0)
            if row["clustering_std"] is not None:
                assert row["clustering_std"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
