"""Unit tests for the comparison module.

This module tests network comparison functionality including
MetricRegistry, multiplex_jaccard, layer_edge_overlap, and compare_networks.
"""

import pytest
from py3plex.core import multinet
from py3plex.comparison import (
    compare_networks,
    multiplex_jaccard,
    layer_edge_overlap,
    degree_correlation,
    degree_change,
    MetricRegistry,
    metric_registry,
    ComparisonResult,
)


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def network_a():
    """Create first network for comparison."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n3", "L1", 1.0],
        ["n1", "L2", "n3", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def network_b():
    """Create second network for comparison."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n4", "L1", 1.0],
        ["n1", "L2", "n3", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def identical_network():
    """Create network identical to network_a."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n3", "L1", 1.0],
        ["n1", "L2", "n3", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


# ============================================================================
# MetricRegistry Tests
# ============================================================================


class TestMetricRegistry:
    """Unit tests for MetricRegistry."""

    def test_create_registry(self):
        """Test creating a new MetricRegistry."""
        registry = MetricRegistry()
        assert registry is not None
        assert registry.list_metrics() == []

    def test_register_metric(self):
        """Test registering a metric function."""
        registry = MetricRegistry()

        @registry.register("test_metric", description="Test metric")
        def test_metric_fn(net_a, net_b, **kwargs):
            return {"distance": 0.0}

        assert registry.has("test_metric")
        assert "test_metric" in registry.list_metrics()

    def test_get_registered_metric(self):
        """Test retrieving a registered metric."""
        registry = MetricRegistry()

        @registry.register("test_metric")
        def test_metric_fn(net_a, net_b, **kwargs):
            return {"distance": 0.0}

        fn = registry.get("test_metric")
        assert fn is not None
        assert callable(fn)

    def test_get_unknown_metric_raises_error(self):
        """Test that getting an unknown metric raises ValueError."""
        registry = MetricRegistry()
        with pytest.raises(ValueError, match="Unknown metric"):
            registry.get("nonexistent_metric")

    def test_has_metric(self):
        """Test checking if a metric exists."""
        registry = MetricRegistry()

        @registry.register("test_metric")
        def test_metric_fn(net_a, net_b, **kwargs):
            return {"distance": 0.0}

        assert registry.has("test_metric")
        assert not registry.has("nonexistent")


# ============================================================================
# Global Registry Tests
# ============================================================================


class TestGlobalRegistry:
    """Tests for the global metric_registry."""

    def test_global_registry_exists(self):
        """Test that global registry exists and has metrics."""
        assert metric_registry is not None
        metrics = metric_registry.list_metrics()
        assert len(metrics) > 0

    def test_multiplex_jaccard_registered(self):
        """Test that multiplex_jaccard is registered."""
        assert metric_registry.has("multiplex_jaccard")

    def test_layer_edge_overlap_registered(self):
        """Test that layer_edge_overlap is registered."""
        assert metric_registry.has("layer_edge_overlap")

    def test_degree_correlation_registered(self):
        """Test that degree_correlation is registered."""
        assert metric_registry.has("degree_correlation")

    def test_degree_change_registered(self):
        """Test that degree_change is registered."""
        assert metric_registry.has("degree_change")


# ============================================================================
# Multiplex Jaccard Tests
# ============================================================================


class TestMultiplexJaccard:
    """Unit tests for multiplex_jaccard metric."""

    def test_multiplex_jaccard_basic(self, network_a, network_b):
        """Test basic multiplex Jaccard computation."""
        result = multiplex_jaccard(network_a, network_b)
        assert result is not None
        assert "global_distance" in result

    def test_multiplex_jaccard_returns_numeric(self, network_a, network_b):
        """Test that Jaccard returns a numeric distance."""
        result = multiplex_jaccard(network_a, network_b)
        assert isinstance(result["global_distance"], (int, float))
        assert 0.0 <= result["global_distance"] <= 1.0

    def test_multiplex_jaccard_identical_networks(self, network_a, identical_network):
        """Test Jaccard distance between identical networks."""
        result = multiplex_jaccard(network_a, identical_network)
        # Identical networks should have distance close to 0
        assert result["global_distance"] <= 0.1


# ============================================================================
# Layer Edge Overlap Tests
# ============================================================================


class TestLayerEdgeOverlap:
    """Unit tests for layer_edge_overlap metric."""

    def test_layer_edge_overlap_basic(self, network_a, network_b):
        """Test basic layer edge overlap computation."""
        result = layer_edge_overlap(network_a, network_b)
        assert result is not None
        assert "global_distance" in result

    def test_layer_edge_overlap_returns_numeric(self, network_a, network_b):
        """Test that layer edge overlap returns numeric value."""
        result = layer_edge_overlap(network_a, network_b)
        distance = result.get("global_distance", 0)
        assert isinstance(distance, (int, float))


# ============================================================================
# Degree Correlation Tests
# ============================================================================


class TestDegreeCorrelation:
    """Unit tests for degree_correlation metric."""

    def test_degree_correlation_basic(self, network_a, network_b):
        """Test basic degree correlation computation."""
        result = degree_correlation(network_a, network_b)
        assert result is not None
        assert "correlation" in result or "distance" in result

    def test_degree_correlation_returns_numeric(self, network_a, network_b):
        """Test that degree correlation returns numeric value."""
        result = degree_correlation(network_a, network_b)
        correlation = result.get("correlation", result.get("distance", 0))
        assert isinstance(correlation, (int, float))


# ============================================================================
# Degree Change Tests
# ============================================================================


class TestDegreeChange:
    """Unit tests for degree_change metric."""

    def test_degree_change_basic(self, network_a, network_b):
        """Test basic degree change computation."""
        result = degree_change(network_a, network_b)
        assert result is not None
        assert "global_distance" in result or "per_node_difference" in result

    def test_degree_change_returns_numeric(self, network_a, network_b):
        """Test that degree change returns numeric value."""
        result = degree_change(network_a, network_b)
        distance = result.get("global_distance", 0)
        assert isinstance(distance, (int, float))


# ============================================================================
# ComparisonResult Tests
# ============================================================================


class TestComparisonResult:
    """Unit tests for ComparisonResult."""

    def test_create_result(self):
        """Test creating a ComparisonResult."""
        result = ComparisonResult(
            metric_name="test_metric",
            network_a_name="net_a",
            network_b_name="net_b",
            global_distance=0.5,
            layerwise_distance={"L1": 0.3, "L2": 0.7},
        )
        assert result.metric_name == "test_metric"
        assert result.global_distance == 0.5
        assert len(result.layerwise_distance) == 2

    def test_result_to_dict(self):
        """Test converting result to dictionary (via to_pandas)."""
        result = ComparisonResult(
            metric_name="test_metric",
            network_a_name="net_a",
            network_b_name="net_b",
            global_distance=0.5,
            layerwise_distance={"L1": 0.3},
        )
        
        df = result.to_pandas()
        assert df is not None
        assert "metric" in df.columns
        assert df["metric"][0] == "test_metric"

    def test_result_repr(self):
        """Test result string representation."""
        result = ComparisonResult(
            metric_name="test_metric",
            network_a_name="net_a",
            network_b_name="net_b",
            global_distance=0.5,
        )
        
        repr_str = repr(result)
        assert "ComparisonResult" in repr_str or "test_metric" in repr_str


# ============================================================================
# compare_networks Tests
# ============================================================================


class TestCompareNetworks:
    """Unit tests for compare_networks executor."""

    def test_compare_networks_basic(self, network_a, network_b):
        """Test basic network comparison."""
        result = compare_networks(
            network_a,
            network_b,
            metric="multiplex_jaccard",
        )
        assert isinstance(result, ComparisonResult)
        assert result.metric_name == "multiplex_jaccard"

    def test_compare_networks_all_metrics(self, network_a, network_b):
        """Test all registered metrics."""
        metrics = ["multiplex_jaccard", "layer_edge_overlap", "degree_correlation", "degree_change"]
        
        for metric_name in metrics:
            result = compare_networks(
                network_a,
                network_b,
                metric=metric_name,
            )
            assert isinstance(result, ComparisonResult)
            assert result.metric_name == metric_name

    def test_compare_networks_invalid_metric(self, network_a, network_b):
        """Test that invalid metric raises ValueError."""
        with pytest.raises(ValueError, match="Unknown metric"):
            compare_networks(
                network_a,
                network_b,
                metric="nonexistent_metric",
            )

    def test_compare_identical_networks(self, network_a, identical_network):
        """Test comparing identical networks."""
        result = compare_networks(
            network_a,
            identical_network,
            metric="multiplex_jaccard",
        )
        # Identical networks should have low distance
        assert result.global_distance <= 0.1
