"""Integration tests for bootstrap and null model methods in DSL.

This module tests that the DSL correctly integrates with the bootstrap
and null model engines when uncertainty is requested.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q


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
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestBootstrapIntegration:
    """Tests for bootstrap method integration with DSL."""
    
    def test_bootstrap_edges_method(self):
        """Test bootstrap method with edge resampling."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=20,
                bootstrap_unit="edges",
                bootstrap_mode="resample"
            )
            .execute(net)
        )
        
        assert len(result) > 0
        
        # Check that uncertainty information is present
        df = result.to_pandas()
        assert "degree" in df.columns
        
        # Values should be dicts with uncertainty info
        first_degree = df["degree"].iloc[0]
        if isinstance(first_degree, dict):
            assert "mean" in first_degree
            assert "std" in first_degree
            assert "n_boot" in first_degree
    
    def test_bootstrap_nodes_method(self):
        """Test bootstrap method with node resampling."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=15,
                bootstrap_unit="nodes"
            )
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_bootstrap_layers_method(self):
        """Test bootstrap method with layer resampling."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10,
                bootstrap_unit="layers"
            )
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_bootstrap_permute_mode(self):
        """Test bootstrap method with permute mode."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10,
                bootstrap_mode="permute"
            )
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_bootstrap_with_defaults(self):
        """Test bootstrap method using global defaults."""
        net = build_test_network()
        
        Q.uncertainty.defaults(
            method="bootstrap",
            n_boot=25,
            bootstrap_unit="edges",
            ci=0.90
        )
        
        try:
            result = (
                Q.nodes()
                .compute("degree", uncertainty=True)
                .execute(net)
            )
            
            assert len(result) > 0
        finally:
            Q.uncertainty.reset()
    
    def test_bootstrap_multiple_metrics(self):
        """Test bootstrap with multiple metrics."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree", "clustering",
                uncertainty=True,
                method="bootstrap",
                n_boot=10
            )
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns


class TestNullModelIntegration:
    """Tests for null model method integration with DSL."""
    
    def test_null_model_degree_preserving(self):
        """Test null model method with degree-preserving rewiring."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=20,
                null_model="degree_preserving"
            )
            .execute(net)
        )
        
        assert len(result) > 0
        
        # Check that uncertainty information is present
        df = result.to_pandas()
        assert "degree" in df.columns
        
        # Values should be dicts with null model info
        first_degree = df["degree"].iloc[0]
        if isinstance(first_degree, dict):
            assert "mean" in first_degree
            assert "zscore" in first_degree
            assert "pvalue" in first_degree
            assert "n_null" in first_degree
    
    def test_null_model_erdos_renyi(self):
        """Test null model method with Erdős-Rényi."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=15,
                null_model="erdos_renyi"
            )
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_null_model_configuration(self):
        """Test null model method with configuration model."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=10,
                null_model="configuration"
            )
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_null_model_with_defaults(self):
        """Test null model method using global defaults."""
        net = build_test_network()
        
        Q.uncertainty.defaults(
            method="null_model",
            n_null=25,
            null_model="degree_preserving"
        )
        
        try:
            result = (
                Q.nodes()
                .compute("degree", uncertainty=True)
                .execute(net)
            )
            
            assert len(result) > 0
        finally:
            Q.uncertainty.reset()
    
    def test_null_model_multiple_metrics(self):
        """Test null model with multiple metrics."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree", "clustering",
                uncertainty=True,
                method="null_model",
                n_null=10
            )
            .execute(net)
        )
        
        assert len(result) > 0
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns


class TestMethodComparison:
    """Tests comparing different uncertainty methods."""
    
    def test_bootstrap_vs_null_model(self):
        """Compare bootstrap and null model methods."""
        net = build_test_network()
        
        # Bootstrap
        bootstrap_result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=20
            )
            .execute(net)
        )
        
        # Null model
        null_result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=20
            )
            .execute(net)
        )
        
        # Both should return results
        assert len(bootstrap_result) > 0
        assert len(null_result) > 0
        
        # Bootstrap should have CI info
        boot_df = bootstrap_result.to_pandas()
        first_boot = boot_df["degree"].iloc[0]
        if isinstance(first_boot, dict):
            assert "quantiles" in first_boot or "std" in first_boot
        
        # Null model should have p-value info
        null_df = null_result.to_pandas()
        first_null = null_df["degree"].iloc[0]
        if isinstance(first_null, dict):
            assert "pvalue" in first_null or "zscore" in first_null
    
    def test_legacy_perturbation_still_works(self):
        """Test that legacy perturbation method still works."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="perturbation",
                n_samples=10
            )
            .execute(net)
        )
        
        assert len(result) > 0


class TestEdgeCases:
    """Edge case tests for uncertainty integration."""
    
    def test_invalid_method(self):
        """Test that invalid method is handled gracefully."""
        net = build_test_network()
        
        # Invalid method should be caught and logged, not crash
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="invalid_method"
            )
            .execute(net)
        )
        
        # Should still return a result (with error handling)
        assert result is not None
    
    def test_bootstrap_with_order_by(self):
        """Test bootstrap with order_by clause."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10
            )
            .order_by("-degree")
            .execute(net)
        )
        
        assert len(result) > 0
    
    def test_bootstrap_with_limit(self):
        """Test bootstrap with limit clause."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=10
            )
            .limit(3)
            .execute(net)
        )
        
        assert len(result) <= 3
    
    def test_null_model_with_layer_filtering(self):
        """Test null model with layer filtering."""
        net = build_test_network()
        
        result = (
            Q.nodes()
            .where(layer="L0")
            .compute(
                "degree",
                uncertainty=True,
                method="null_model",
                n_null=10
            )
            .execute(net)
        )
        
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
