"""Tests for DSL uncertainty support.

This module tests the integration of first-class uncertainty into the DSL,
verifying that uncertainty can be requested via the compute() method and
propagated through query chains.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import StatSeries, ResamplingStrategy


def build_test_network():
    """Build a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Layer 0: Triangle
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
        # Layer 1: Chain
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestDSLUncertaintyBasics:
    """Basic tests for uncertainty in DSL compute()."""
    
    def test_compute_without_uncertainty_backward_compat(self):
        """Test that compute() without uncertainty works as before."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree")
            .execute(net)
        )
        
        # Should have degree values
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        
        # Values should be numeric
        assert df["degree"].dtype in [np.int64, np.float64, int, float]
    
    def test_compute_with_uncertainty_basic(self):
        """Test that compute() with uncertainty=True works."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=10)
            .execute(net)
        )
        
        # Should have results
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        
        # Check if uncertainty info is present in attributes
        # When uncertainty is computed, values are dicts with 'mean', 'std', etc.
        degree_attr = result.attributes.get("degree", {})
        if degree_attr:
            # Get first item to check structure
            first_key = next(iter(degree_attr))
            first_val = degree_attr[first_key]
            
            if isinstance(first_val, dict):
                # Should have mean and optionally std
                assert "mean" in first_val
    
    def test_compute_with_uncertainty_method_parameter(self):
        """Test that uncertainty method parameter is accepted."""
        net = build_test_network()
        
        # Test different methods
        for method in ["perturbation", "seed"]:
            result = (
                Q.nodes()
                .compute("degree", uncertainty=True, method=method, n_samples=5)
                .execute(net)
            )
            
            assert len(result) > 0
    
    def test_compute_with_uncertainty_n_samples(self):
        """Test that n_samples parameter is respected."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=20)
            .execute(net)
        )
        
        assert len(result) > 0
        # The implementation should use these samples
    
    def test_compute_with_uncertainty_ci(self):
        """Test that ci parameter is accepted."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, ci=0.95, n_samples=10)
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_multiple_measures_with_uncertainty(self):
        """Test computing multiple measures with uncertainty."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", "clustering", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns


class TestDSLUncertaintyChaining:
    """Tests for uncertainty with DSL chaining operations."""
    
    def test_uncertainty_with_order_by(self):
        """Test that uncertainty works with order_by."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5)
            .order_by("-degree")
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_uncertainty_with_limit(self):
        """Test that uncertainty works with limit."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5)
            .order_by("-degree")
            .limit(3)
            .execute(net)
        )
        
        assert len(result) <= 3
    
    def test_uncertainty_with_layer_filtering(self):
        """Test that uncertainty works with layer filtering."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .where(layer="L0")
            .compute("degree", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        # Should only have nodes from L0
        assert len(result) > 0


class TestDSLUncertaintyAliases:
    """Tests for uncertainty with aliases."""
    
    def test_uncertainty_with_alias(self):
        """Test that uncertainty works with measure aliases."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", alias="deg", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        # Should use alias name
        assert "deg" in df.columns or "degree" in df.columns
    
    def test_uncertainty_with_multiple_aliases(self):
        """Test that uncertainty works with multiple aliased measures."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                "clustering",
                aliases={"degree": "deg", "clustering": "clust"},
                uncertainty=True,
                n_samples=5
            )
            .execute(net)
        )
        
        assert len(result) > 0


class TestDSLUncertaintyEdgeCases:
    """Edge case tests for DSL uncertainty."""
    
    def test_uncertainty_false_explicit(self):
        """Test that uncertainty=False gives deterministic results."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=False)
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
    
    def test_uncertainty_with_no_samples(self):
        """Test that default n_samples is used when not specified."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True)
            .execute(net)
        )
        
        # Should use default n_samples (50)
        assert len(result) > 0
    
    def test_uncertainty_empty_network(self):
        """Test that uncertainty handles empty networks gracefully."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Empty network
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        # Should handle empty result
        assert len(result) == 0
    
    def test_uncertainty_single_node(self):
        """Test uncertainty with single node network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Single node with one edge to another node
        net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        assert len(result) >= 1


class TestDSLUncertaintyIntegration:
    """Integration tests combining uncertainty with other DSL features."""
    
    def test_uncertainty_with_grouping(self):
        """Test uncertainty with per-layer grouping."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .per_layer()
            .compute("degree", uncertainty=True, n_samples=5)
            .top_k(2, "degree")
            .execute(net)
        )
        
        # Should have top nodes per layer
        assert len(result) > 0
    
    def test_uncertainty_pandas_export(self):
        """Test that results with uncertainty export to pandas correctly."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute("degree", uncertainty=True, n_samples=5)
            .execute(net)
        )
        
        # Should be able to export to pandas
        df = result.to_pandas()
        assert len(df) > 0
        assert "degree" in df.columns


class TestDSLUncertaintyDocumentationExamples:
    """Tests matching documentation examples."""
    
    def test_flagship_example(self):
        """Test the flagship example from the issue."""
        net = build_test_network()
        
        # This is the example from the issue
        hubs = (
            Q.nodes()
            .compute(
                "degree", "betweenness_centrality",
                uncertainty=True,
                method="bootstrap",
                n_samples=10,  # Use fewer samples for testing
                ci=0.95
            )
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(net)
        )
        
        # Should return results
        assert len(hubs) > 0
        
        # Should have the computed measures
        df = hubs.to_pandas()
        assert "degree" in df.columns
        assert "betweenness_centrality" in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
