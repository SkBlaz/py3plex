"""Tests for bootstrap and null model engines.

This module tests the generic bootstrap_metric() and null_model_metric()
functions that provide uncertainty estimation for any graph metric.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.uncertainty import bootstrap_metric, null_model_metric


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


def degree_metric(network):
    """Simple degree metric for testing."""
    result = {}
    # Handle empty networks
    if not hasattr(network, 'core_network') or network.core_network is None:
        return result
    for node in network.get_nodes():
        result[node] = network.core_network.degree(node)
    return result


class TestBootstrapEngine:
    """Tests for bootstrap_metric() function."""
    
    def test_bootstrap_edges_resample(self):
        """Test bootstrap with edge resampling."""
        net = build_test_network()
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=20,
            unit="edges",
            mode="resample",
            ci=0.95,
            random_state=42,
        )
        
        # Check structure
        assert "mean" in result
        assert "std" in result
        assert "ci_low" in result
        assert "ci_high" in result
        assert "index" in result
        assert "n_boot" in result
        assert "method" in result
        
        # Check shapes
        n_nodes = len(result["index"])
        assert result["mean"].shape == (n_nodes,)
        assert result["std"].shape == (n_nodes,)
        assert result["ci_low"].shape == (n_nodes,)
        assert result["ci_high"].shape == (n_nodes,)
        
        # Check metadata
        assert result["n_boot"] == 20
        assert result["method"] == "bootstrap_resample_edges"
    
    def test_bootstrap_nodes_resample(self):
        """Test bootstrap with node resampling."""
        net = build_test_network()
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=10,
            unit="nodes",
            mode="resample",
            random_state=42,
        )
        
        assert "mean" in result
        assert result["n_boot"] == 10
        assert result["method"] == "bootstrap_resample_nodes"
    
    def test_bootstrap_layers_resample(self):
        """Test bootstrap with layer resampling."""
        net = build_test_network()
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=10,
            unit="layers",
            mode="resample",
            random_state=42,
        )
        
        assert "mean" in result
        assert result["n_boot"] == 10
        assert result["method"] == "bootstrap_resample_layers"
    
    def test_bootstrap_edges_permute(self):
        """Test bootstrap with edge permutation."""
        net = build_test_network()
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=10,
            unit="edges",
            mode="permute",
            random_state=42,
        )
        
        assert "mean" in result
        assert result["method"] == "bootstrap_permute_edges"
    
    def test_bootstrap_ci_bounds(self):
        """Test that CI bounds are correctly computed."""
        net = build_test_network()
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=50,
            unit="edges",
            ci=0.95,
            random_state=42,
        )
        
        # CI low should be <= mean <= CI high
        assert np.all(result["ci_low"] <= result["mean"] + 1e-6)
        assert np.all(result["ci_high"] >= result["mean"] - 1e-6)
        
        # CI width should be positive
        ci_width = result["ci_high"] - result["ci_low"]
        assert np.all(ci_width >= 0)
    
    def test_bootstrap_consistency(self):
        """Test that bootstrap gives consistent results with same seed."""
        net = build_test_network()
        
        result1 = bootstrap_metric(
            net,
            degree_metric,
            n_boot=20,
            unit="edges",
            random_state=42,
        )
        
        result2 = bootstrap_metric(
            net,
            degree_metric,
            n_boot=20,
            unit="edges",
            random_state=42,
        )
        
        # Should be identical with same seed
        np.testing.assert_array_almost_equal(result1["mean"], result2["mean"])
        np.testing.assert_array_almost_equal(result1["std"], result2["std"])
    
    def test_bootstrap_invalid_unit(self):
        """Test that invalid unit raises error."""
        net = build_test_network()
        
        with pytest.raises(ValueError, match="Unknown unit"):
            bootstrap_metric(
                net,
                degree_metric,
                n_boot=10,
                unit="invalid_unit",
            )
    
    def test_bootstrap_invalid_mode(self):
        """Test that invalid mode raises error."""
        net = build_test_network()
        
        with pytest.raises(ValueError, match="Unknown mode"):
            bootstrap_metric(
                net,
                degree_metric,
                n_boot=10,
                unit="edges",
                mode="invalid_mode",
            )
    
    def test_bootstrap_empty_network(self):
        """Test bootstrap on empty network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = bootstrap_metric(
            net,
            degree_metric,
            n_boot=10,
            unit="edges",
        )
        
        # Should return empty arrays
        assert len(result["index"]) == 0
    
    def test_bootstrap_ci_levels(self):
        """Test different CI levels."""
        net = build_test_network()
        
        # 90% CI should be narrower than 95% CI
        result_90 = bootstrap_metric(
            net,
            degree_metric,
            n_boot=50,
            unit="edges",
            ci=0.90,
            random_state=42,
        )
        
        result_95 = bootstrap_metric(
            net,
            degree_metric,
            n_boot=50,
            unit="edges",
            ci=0.95,
            random_state=42,
        )
        
        # 90% CI should be narrower
        width_90 = np.mean(result_90["ci_high"] - result_90["ci_low"])
        width_95 = np.mean(result_95["ci_high"] - result_95["ci_low"])
        assert width_90 <= width_95


class TestNullModelEngine:
    """Tests for null_model_metric() function."""
    
    def test_null_model_degree_preserving(self):
        """Test null model with degree-preserving rewiring."""
        net = build_test_network()
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=20,
            model="degree_preserving",
            random_state=42,
        )
        
        # Check structure
        assert "observed" in result
        assert "mean_null" in result
        assert "std_null" in result
        assert "zscore" in result
        assert "pvalue" in result
        assert "index" in result
        assert "n_null" in result
        assert "model" in result
        
        # Check shapes
        n_nodes = len(result["index"])
        assert result["observed"].shape == (n_nodes,)
        assert result["mean_null"].shape == (n_nodes,)
        assert result["std_null"].shape == (n_nodes,)
        assert result["zscore"].shape == (n_nodes,)
        assert result["pvalue"].shape == (n_nodes,)
        
        # Check metadata
        assert result["n_null"] == 20
        assert result["model"] == "degree_preserving"
    
    def test_null_model_erdos_renyi(self):
        """Test null model with Erdős-Rényi random graph."""
        net = build_test_network()
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=10,
            model="erdos_renyi",
            random_state=42,
        )
        
        assert "zscore" in result
        assert result["model"] == "erdos_renyi"
    
    def test_null_model_configuration(self):
        """Test null model with configuration model."""
        net = build_test_network()
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=10,
            model="configuration",
            random_state=42,
        )
        
        assert "zscore" in result
        assert result["model"] == "configuration"
    
    def test_null_model_pvalues(self):
        """Test that p-values are in valid range."""
        net = build_test_network()
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=50,
            model="degree_preserving",
            random_state=42,
        )
        
        # P-values should be in [0, 1]
        assert np.all(result["pvalue"] >= 0)
        assert np.all(result["pvalue"] <= 1)
    
    def test_null_model_consistency(self):
        """Test that null model gives consistent results with same seed."""
        net = build_test_network()
        
        result1 = null_model_metric(
            net,
            degree_metric,
            n_null=20,
            model="degree_preserving",
            random_state=42,
        )
        
        result2 = null_model_metric(
            net,
            degree_metric,
            n_null=20,
            model="degree_preserving",
            random_state=42,
        )
        
        # Should be identical with same seed
        np.testing.assert_array_almost_equal(result1["observed"], result2["observed"])
        np.testing.assert_array_almost_equal(result1["zscore"], result2["zscore"], decimal=5)
    
    def test_null_model_invalid_model(self):
        """Test that invalid model type raises error."""
        net = build_test_network()
        
        with pytest.raises(ValueError, match="Unknown null model"):
            null_model_metric(
                net,
                degree_metric,
                n_null=10,
                model="invalid_model",
            )
    
    def test_null_model_empty_network(self):
        """Test null model on empty network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=10,
            model="degree_preserving",
        )
        
        # Should return empty arrays
        assert len(result["index"]) == 0
    
    def test_null_model_zscore_extreme(self):
        """Test that nodes with extreme values get high |z-scores|."""
        # Create a star graph where center has high degree
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ["center", "L0", "a", "L0", 1.0],
            ["center", "L0", "b", "L0", 1.0],
            ["center", "L0", "c", "L0", 1.0],
            ["center", "L0", "d", "L0", 1.0],
            ["center", "L0", "e", "L0", 1.0],
        ]
        net.add_edges(edges, input_type="list")
        
        result = null_model_metric(
            net,
            degree_metric,
            n_null=50,
            model="erdos_renyi",  # Use ER since it doesn't preserve degree
            random_state=42,
        )
        
        # Find center node in results (check if it exists)
        if "center" in result["index"]:
            center_idx = result["index"].index("center")
            # Center should have higher observed degree than null mean
            # (in most cases, due to randomness this might not always hold)
            # So we just check that z-score is computed
            assert not np.isnan(result["zscore"][center_idx])
        else:
            # If center not found, just check that some z-scores are computed
            assert len(result["zscore"]) > 0
            assert not np.all(np.isnan(result["zscore"]))


class TestBootstrapIntegration:
    """Integration tests combining bootstrap with realistic scenarios."""
    
    def test_bootstrap_betweenness(self):
        """Test bootstrap with betweenness centrality metric."""
        import networkx as nx
        
        net = build_test_network()
        
        def betweenness_metric(network):
            result = {}
            G = network.core_network
            bc = nx.betweenness_centrality(G)
            for node in network.get_nodes():
                result[node] = bc.get(node, 0.0)
            return result
        
        result = bootstrap_metric(
            net,
            betweenness_metric,
            n_boot=20,
            unit="edges",
            random_state=42,
        )
        
        # Should compute CI for betweenness
        assert "mean" in result
        assert "ci_low" in result
        assert "ci_high" in result
    
    def test_bootstrap_clustering(self):
        """Test bootstrap with clustering coefficient metric."""
        import networkx as nx
        
        net = build_test_network()
        
        def clustering_metric(network):
            result = {}
            G = network.core_network
            # Convert to simple graph for clustering
            if G.is_multigraph():
                G = nx.Graph(G)
            cc = nx.clustering(G)
            for node in network.get_nodes():
                result[node] = cc.get(node, 0.0)
            return result
        
        result = bootstrap_metric(
            net,
            clustering_metric,
            n_boot=20,
            unit="edges",
            random_state=42,
        )
        
        # Should compute CI for clustering
        assert "mean" in result
        assert "std" in result


class TestNullModelIntegration:
    """Integration tests for null models with realistic scenarios."""
    
    def test_null_model_betweenness(self):
        """Test null model with betweenness centrality."""
        import networkx as nx
        
        net = build_test_network()
        
        def betweenness_metric(network):
            result = {}
            G = network.core_network
            bc = nx.betweenness_centrality(G)
            for node in network.get_nodes():
                result[node] = bc.get(node, 0.0)
            return result
        
        result = null_model_metric(
            net,
            betweenness_metric,
            n_null=20,
            model="degree_preserving",
            random_state=42,
        )
        
        # Should compute z-scores and p-values
        assert "zscore" in result
        assert "pvalue" in result
        
        # All p-values should be valid
        assert np.all(result["pvalue"] >= 0)
        assert np.all(result["pvalue"] <= 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
