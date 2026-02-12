"""Tests for py3plex.comparison.executor module.

Tests the network comparison executor functions.
"""

import pytest
from py3plex.comparison.executor import compare_networks, execute_compare_stmt
from py3plex.comparison.result import ComparisonResult
from py3plex.comparison.metrics import metric_registry
from py3plex.core import multinet


class TestCompareNetworksBasic:
    """Test basic compare_networks functionality."""
    
    def test_compare_networks_default_metric(self):
        """Test comparing two networks with default metric."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_nodes([{'source': 'A', 'type': 'layer1'}])
        net_a.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_nodes([{'source': 'A', 'type': 'layer1'}])
        net_b.add_edges([
            {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        result = compare_networks(net_a, net_b)
        
        assert isinstance(result, ComparisonResult)
        assert result.metric_name == "multiplex_jaccard"
        assert result.network_a_name == "network_a"
        assert result.network_b_name == "network_b"
    
    def test_compare_networks_custom_names(self):
        """Test comparing networks with custom names."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(
            net_a, net_b,
            network_a_name="baseline",
            network_b_name="treatment"
        )
        
        assert result.network_a_name == "baseline"
        assert result.network_b_name == "treatment"
    
    def test_compare_networks_with_layers(self):
        """Test comparing networks with layer filtering."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer2'}
        ])
        
        net_b = multinet.multi_layer_network(directed=False)
        net_b.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'}
        ])
        
        result = compare_networks(net_a, net_b, layers=["layer1"])
        
        assert result.meta["layers"] == ["layer1"]
    
    def test_compare_networks_different_metrics(self):
        """Test comparing networks with different metrics."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        # Should work with any registered metric
        for metric_name in ["multiplex_jaccard"]:
            result = compare_networks(net_a, net_b, metric=metric_name)
            assert result.metric_name == metric_name


class TestCompareNetworksMeasures:
    """Test different measure types in compare_networks."""
    
    def test_global_distance_measure(self):
        """Test requesting only global distance."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(
            net_a, net_b,
            measures=["global_distance"]
        )
        
        assert "global_distance" in result.meta["measures"]
    
    def test_layerwise_distance_measure(self):
        """Test requesting layerwise distance."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(
            net_a, net_b,
            measures=["layerwise_distance"]
        )
        
        assert "layerwise_distance" in result.meta["measures"]
    
    def test_per_node_difference_measure(self):
        """Test requesting per-node differences."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(
            net_a, net_b,
            measures=["per_node_difference"]
        )
        
        assert "per_node_difference" in result.meta["measures"]
    
    def test_multiple_measures(self):
        """Test requesting multiple measures at once."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(
            net_a, net_b,
            measures=["global_distance", "layerwise_distance"]
        )
        
        assert "global_distance" in result.meta["measures"]
        assert "layerwise_distance" in result.meta["measures"]
    
    def test_default_measures(self):
        """Test that default measures is ['global_distance']."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b)
        
        assert result.meta["measures"] == ["global_distance"]


class TestCompareNetworksMetadata:
    """Test metadata in comparison results."""
    
    def test_metadata_includes_metric(self):
        """Test that metadata includes the metric name."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b, metric="multiplex_jaccard")
        
        assert result.meta["metric"] == "multiplex_jaccard"
    
    def test_metadata_includes_layers(self):
        """Test that metadata includes layer specification."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b, layers=["layer1", "layer2"])
        
        assert result.meta["layers"] == ["layer1", "layer2"]
    
    def test_metadata_includes_measures(self):
        """Test that metadata includes requested measures."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        measures = ["global_distance", "per_node_difference"]
        result = compare_networks(net_a, net_b, measures=measures)
        
        assert result.meta["measures"] == measures


class TestExecuteCompareStmt:
    """Test execute_compare_stmt for DSL integration."""
    
    def test_execute_compare_stmt_basic(self):
        """Test executing a basic COMPARE statement."""
        from py3plex.dsl.ast import CompareStmt
        
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        networks = {
            "net_a": net_a,
            "net_b": net_b
        }
        
        stmt = CompareStmt(
            network_a="net_a",
            network_b="net_b",
            metric_name="multiplex_jaccard",
            layer_expr=None,
            measures=["global_distance"]
        )
        
        result = execute_compare_stmt(networks, stmt)
        
        assert isinstance(result, ComparisonResult)
        assert result.network_a_name == "net_a"
        assert result.network_b_name == "net_b"
        assert result.metric_name == "multiplex_jaccard"
    
    def test_execute_compare_stmt_missing_network_a(self):
        """Test error when network_a is not found."""
        from py3plex.dsl.ast import CompareStmt
        
        net_b = multinet.multi_layer_network(directed=False)
        networks = {"net_b": net_b}
        
        stmt = CompareStmt(
            network_a="missing",
            network_b="net_b",
            metric_name="multiplex_jaccard",
            layer_expr=None,
            measures=None
        )
        
        with pytest.raises(ValueError, match="Network 'missing' not found"):
            execute_compare_stmt(networks, stmt)
    
    def test_execute_compare_stmt_missing_network_b(self):
        """Test error when network_b is not found."""
        from py3plex.dsl.ast import CompareStmt
        
        net_a = multinet.multi_layer_network(directed=False)
        networks = {"net_a": net_a}
        
        stmt = CompareStmt(
            network_a="net_a",
            network_b="missing",
            metric_name="multiplex_jaccard",
            layer_expr=None,
            measures=None
        )
        
        with pytest.raises(ValueError, match="Network 'missing' not found"):
            execute_compare_stmt(networks, stmt)
    
    def test_execute_compare_stmt_with_measures(self):
        """Test executing COMPARE with specific measures."""
        from py3plex.dsl.ast import CompareStmt
        
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        networks = {"net_a": net_a, "net_b": net_b}
        
        stmt = CompareStmt(
            network_a="net_a",
            network_b="net_b",
            metric_name="multiplex_jaccard",
            layer_expr=None,
            measures=["global_distance", "layerwise_distance"]
        )
        
        result = execute_compare_stmt(networks, stmt)
        
        assert result.meta["measures"] == ["global_distance", "layerwise_distance"]
    
    def test_execute_compare_stmt_default_measures(self):
        """Test that default measures is used when stmt.measures is None."""
        from py3plex.dsl.ast import CompareStmt
        
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        networks = {"net_a": net_a, "net_b": net_b}
        
        stmt = CompareStmt(
            network_a="net_a",
            network_b="net_b",
            metric_name="multiplex_jaccard",
            layer_expr=None,
            measures=None  # Should default to ["global_distance"]
        )
        
        result = execute_compare_stmt(networks, stmt)
        
        assert result.meta["measures"] == ["global_distance"]


class TestCompareNetworksEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_compare_empty_networks(self):
        """Test comparing two empty networks."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b)
        
        assert isinstance(result, ComparisonResult)
    
    def test_compare_networks_one_empty(self):
        """Test comparing when one network is empty."""
        net_a = multinet.multi_layer_network(directed=False)
        net_a.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b)
        
        assert isinstance(result, ComparisonResult)
    
    def test_compare_networks_empty_layers_list(self):
        """Test comparing with empty layers list."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b, layers=[])
        
        assert result.meta["layers"] == []
    
    def test_result_preserves_extra_metadata(self):
        """Test that extra metadata from metric is preserved."""
        net_a = multinet.multi_layer_network(directed=False)
        net_b = multinet.multi_layer_network(directed=False)
        
        result = compare_networks(net_a, net_b)
        
        # Meta should contain at minimum the basic fields
        assert "metric" in result.meta
        assert "measures" in result.meta
