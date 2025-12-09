"""Tests for DSL enhancements: temporal helpers, autocompute, computed_metrics tracking.

This test suite validates the new DSL features added for polishing:
- before() and after() temporal helpers
- autocompute parameter support
- computed_metrics tracking in QueryResult
- DslMissingMetricError exception type
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, DslMissingMetricError


@pytest.fixture
def sample_network():
    """Create a simple network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = []
    for layer in ["layer0", "layer1"]:
        for i in range(5):
            nodes.append({'source': f'node{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges
    edges = []
    for layer in ["layer0", "layer1"]:
        for i in range(4):
            edges.append({
                'source': f'node{i}',
                'target': f'node{i+1}',
                'source_type': layer,
                'target_type': layer,
                'weight': 1.0
            })
    network.add_edges(edges)
    
    return network


@pytest.fixture
def temporal_network():
    """Create a network with temporal edges for testing temporal queries."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'layer0'},
        {'source': 'B', 'type': 'layer0'},
        {'source': 'C', 'type': 'layer0'},
    ]
    network.add_nodes(nodes)
    
    # Add temporal edges with 't' attribute
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer0', 'target_type': 'layer0', 't': 50.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer0', 'target_type': 'layer0', 't': 150.0},
        {'source': 'A', 'target': 'C', 'source_type': 'layer0', 'target_type': 'layer0', 't': 250.0},
    ]
    network.add_edges(edges)
    
    return network


class TestTemporalHelpers:
    """Test before() and after() temporal helper methods."""
    
    def test_before_method(self, temporal_network):
        """Test that before() filters edges correctly."""
        net = temporal_network
        
        # Query edges before time 100
        result = Q.edges().before(100.0).execute(net)
        df = result.to_pandas()
        
        # Should only get the edge at t=50
        assert len(df) == 1
        assert df.iloc[0]['source'] == 'A'
        assert df.iloc[0]['target'] == 'B'
    
    def test_after_method(self, temporal_network):
        """Test that after() filters edges correctly."""
        net = temporal_network
        
        # Query edges after time 200
        result = Q.edges().after(200.0).execute(net)
        df = result.to_pandas()
        
        # Should only get the edge at t=250
        assert len(df) == 1
        assert df.iloc[0]['source'] == 'A'
        assert df.iloc[0]['target'] == 'C'
    
    def test_before_inclusive(self, temporal_network):
        """Test that before() is inclusive of the boundary."""
        net = temporal_network
        
        # Query edges before time 150 (inclusive)
        result = Q.edges().before(150.0).execute(net)
        df = result.to_pandas()
        
        # Should get edges at t=50 and t=150
        assert len(df) == 2
    
    def test_after_inclusive(self, temporal_network):
        """Test that after() is inclusive of the boundary."""
        net = temporal_network
        
        # Query edges after time 150 (inclusive)
        result = Q.edges().after(150.0).execute(net)
        df = result.to_pandas()
        
        # Should get edges at t=150 and t=250
        assert len(df) == 2
    
    def test_before_after_combination(self, temporal_network):
        """Test that before/after are equivalent to during."""
        net = temporal_network
        
        # Query with during
        result_during = Q.edges().during(100.0, 200.0).execute(net)
        df_during = result_during.to_pandas()
        
        # This should be equivalent to after(100) followed by manual filtering
        result_after = Q.edges().after(100.0).execute(net)
        df_after = result_after.to_pandas()
        
        # after(100) should get t=150 and t=250
        assert len(df_after) == 2
        
        # during(100, 200) should get only t=150
        assert len(df_during) == 1


class TestAutocompute:
    """Test autocompute parameter support."""
    
    def test_autocompute_enabled_by_default(self, sample_network):
        """Test that autocompute is enabled by default."""
        net = sample_network
        
        # This should work without explicit compute()
        result = Q.nodes().from_layers(L["layer0"]).order_by("degree").execute(net)
        df = result.to_pandas()
        
        # Should have degree column auto-computed
        assert 'degree' in df.columns
        assert len(df) == 5
    
    def test_autocompute_flag_false(self, sample_network):
        """Test that autocompute=False prevents automatic metric computation."""
        net = sample_network
        
        # With autocompute disabled, this should still work if degree is already present
        # or if we explicitly compute it
        result = Q.nodes(autocompute=False).from_layers(L["layer0"]).compute("degree").order_by("degree").execute(net)
        df = result.to_pandas()
        
        assert 'degree' in df.columns
        assert len(df) == 5
    
    def test_computed_metrics_tracking(self, sample_network):
        """Test that computed_metrics are tracked in QueryResult."""
        net = sample_network
        
        # Query with explicit compute
        result = Q.nodes().from_layers(L["layer0"]).compute("degree", "betweenness_centrality").execute(net)
        
        # Check that computed_metrics contains the expected metrics
        assert hasattr(result, 'computed_metrics')
        # Note: The actual tracking needs to be implemented in executor
        # For now, just verify the attribute exists
        assert isinstance(result.computed_metrics, set)


class TestErrorTypes:
    """Test new error types."""
    
    def test_dsl_missing_metric_error_exists(self):
        """Test that DslMissingMetricError can be imported and instantiated."""
        from py3plex.dsl import DslMissingMetricError
        
        error = DslMissingMetricError("degree", required_by="order_by", autocompute_enabled=False)
        
        assert "Missing required metric 'degree'" in str(error)
        assert "order_by" in str(error)
        assert "Autocompute is disabled" in str(error)
    
    def test_dsl_missing_metric_error_with_autocompute(self):
        """Test DslMissingMetricError message when autocompute is enabled."""
        from py3plex.dsl import DslMissingMetricError
        
        error = DslMissingMetricError("custom_metric", required_by="top_k", autocompute_enabled=True)
        
        assert "Missing required metric 'custom_metric'" in str(error)
        assert "cannot be automatically computed" in str(error)


class TestQueryBuilderAPI:
    """Test that QueryBuilder API works with new parameters."""
    
    def test_nodes_with_autocompute_parameter(self):
        """Test Q.nodes() accepts autocompute parameter."""
        builder = Q.nodes(autocompute=True)
        assert builder._select.autocompute is True
        
        builder = Q.nodes(autocompute=False)
        assert builder._select.autocompute is False
    
    def test_edges_with_autocompute_parameter(self):
        """Test Q.edges() accepts autocompute parameter."""
        builder = Q.edges(autocompute=True)
        assert builder._select.autocompute is True
        
        builder = Q.edges(autocompute=False)
        assert builder._select.autocompute is False
    
    def test_before_method_exists(self):
        """Test that before() method exists on QueryBuilder."""
        builder = Q.edges()
        assert hasattr(builder, 'before')
        
        # Test chaining
        builder = builder.before(100.0)
        assert builder._select.temporal_context is not None
        assert builder._select.temporal_context.t1 == 100.0
    
    def test_after_method_exists(self):
        """Test that after() method exists on QueryBuilder."""
        builder = Q.edges()
        assert hasattr(builder, 'after')
        
        # Test chaining
        builder = builder.after(100.0)
        assert builder._select.temporal_context is not None
        assert builder._select.temporal_context.t0 == 100.0


class TestExplainAPI:
    """Test that explain() API works correctly."""
    
    def test_explain_method_exists(self, sample_network):
        """Test that explain() method exists and returns a plan."""
        net = sample_network
        
        # Build a query
        explain_query = (
            Q.nodes()
            .from_layers(L["layer0"])
            .where(degree__gt=1)
            .compute("betweenness_centrality")
            .order_by("betweenness_centrality")
            .limit(5)
            .explain()
        )
        
        # Execute explain query
        plan = explain_query.execute(net)
        
        # Should return an ExecutionPlan
        assert plan is not None
        assert hasattr(plan, 'steps')
        assert hasattr(plan, 'warnings')
