"""Tests for DSL temporal extensions."""

import pytest
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.ast import WindowSpec


class TestDSLWindowSpec:
    """Test WindowSpec AST node."""
    
    def test_window_spec_creation(self):
        """Test creating WindowSpec."""
        spec = WindowSpec(window_size=100.0)
        
        assert spec.window_size == 100.0
        assert spec.step is None
        assert spec.aggregation == "list"
    
    def test_window_spec_with_step(self):
        """Test WindowSpec with step."""
        spec = WindowSpec(window_size=100.0, step=50.0)
        
        assert spec.window_size == 100.0
        assert spec.step == 50.0
    
    def test_window_spec_with_duration_string(self):
        """Test WindowSpec with duration strings."""
        spec = WindowSpec(window_size="7d", step="1d")
        
        assert spec.window_size == "7d"
        assert spec.step == "1d"


class TestDSLWindowBuilder:
    """Test DSL builder window() method."""
    
    def test_window_method_exists(self):
        """Test that window() method exists on query builder."""
        q = Q.nodes()
        
        assert hasattr(q, 'window')
    
    def test_window_method_chaining(self):
        """Test that window() returns self for chaining."""
        q = Q.nodes().window(100.0)
        
        assert q is not None
        # Check that window_spec is set
        assert q._select.window_spec is not None
        assert q._select.window_spec.window_size == 100.0
    
    def test_window_with_step(self):
        """Test window() with step parameter."""
        q = Q.nodes().window(100.0, step=50.0)
        
        assert q._select.window_spec.window_size == 100.0
        assert q._select.window_spec.step == 50.0
    
    def test_window_with_duration_strings(self):
        """Test window() with duration strings."""
        q = Q.nodes().window("7d", step="1d")
        
        assert q._select.window_spec.window_size == "7d"
        assert q._select.window_spec.step == "1d"
    
    def test_window_with_aggregation(self):
        """Test window() with aggregation parameter."""
        q = Q.nodes().window(100.0, aggregation="concat")
        
        assert q._select.window_spec.aggregation == "concat"
    
    def test_window_converts_to_ast(self):
        """Test that window() produces correct AST."""
        q = Q.nodes().window(100.0, step=50.0)
        ast = q.to_ast()
        
        assert ast.select.window_spec is not None
        assert ast.select.window_spec.window_size == 100.0
        assert ast.select.window_spec.step == 50.0


class TestDSLTemporalIntegration:
    """Test integration of existing temporal features."""
    
    def test_at_method(self):
        """Test that at() method still works."""
        q = Q.edges().at(150.0)
        
        assert q._select.temporal_context is not None
        assert q._select.temporal_context.kind == "at"
        assert q._select.temporal_context.t0 == 150.0
    
    def test_during_method(self):
        """Test that during() method still works."""
        q = Q.edges().during(100.0, 200.0)
        
        assert q._select.temporal_context is not None
        assert q._select.temporal_context.kind == "during"
        assert q._select.temporal_context.t0 == 100.0
        assert q._select.temporal_context.t1 == 200.0
    
    def test_before_method(self):
        """Test that before() method still works."""
        q = Q.edges().before(100.0)
        
        assert q._select.temporal_context is not None
        assert q._select.temporal_context.kind == "during"
        assert q._select.temporal_context.t1 == 100.0
    
    def test_after_method(self):
        """Test that after() method still works."""
        q = Q.edges().after(100.0)
        
        assert q._select.temporal_context is not None
        assert q._select.temporal_context.kind == "during"
        assert q._select.temporal_context.t0 == 100.0


class TestDSLWindowExecution:
    """Test executing windowed queries (basic tests only - full executor support TBD)."""
    
    @pytest.fixture
    def sample_temporal_network(self):
        """Create a sample temporal network for testing."""
        tnet = TemporalMultiLayerNetwork()
        
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 100.0, 'weight': 1.0},
            {'source': 'B', 'target': 'C', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 150.0, 'weight': 1.0},
            {'source': 'C', 'target': 'A', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 200.0, 'weight': 1.0},
        ]
        
        tnet.add_edges(edges)
        return tnet
    
    def test_window_query_compiles(self, sample_temporal_network):
        """Test that windowed query compiles to AST."""
        q = Q.nodes().compute("degree").window(100.0)
        ast = q.to_ast()
        
        assert ast.select.window_spec is not None
    
    def test_combining_temporal_and_window(self, sample_temporal_network):
        """Test combining temporal context and window spec."""
        q = Q.nodes().during(100.0, 200.0).window(50.0)
        ast = q.to_ast()
        
        # Both should be present
        assert ast.select.temporal_context is not None
        assert ast.select.window_spec is not None
    
    def test_window_with_compute(self, sample_temporal_network):
        """Test window query with compute."""
        q = (
            Q.nodes()
            .compute("degree")
            .window(100.0)
        )
        
        ast = q.to_ast()
        assert len(ast.select.compute) == 1
        assert ast.select.window_spec is not None


class TestDSLTemporalFilters:
    """Test temporal filters in where() clause."""
    
    def test_where_t_between(self):
        """Test t__between filter."""
        q = Q.edges().where(t__between=(100.0, 200.0))
        
        # Check that temporal_range predicate is created
        ast = q.to_ast()
        assert ast.select.where is not None
        # Should have a special predicate for temporal_range
        assert any(atom.special and atom.special.kind == "temporal_range" 
                  for atom in ast.select.where.atoms)
    
    def test_where_t_gte(self):
        """Test t__gte filter."""
        q = Q.edges().where(t__gte=100.0)
        
        ast = q.to_ast()
        assert ast.select.where is not None
        # Should have comparison for t >= 100
        assert any(atom.comparison and atom.comparison.left == "t" 
                  for atom in ast.select.where.atoms)
    
    def test_where_t_lte(self):
        """Test t__lte filter."""
        q = Q.edges().where(t__lte=200.0)
        
        ast = q.to_ast()
        assert ast.select.where is not None
    
    def test_where_t_gt(self):
        """Test t__gt filter."""
        q = Q.edges().where(t__gt=100.0)
        
        ast = q.to_ast()
        assert ast.select.where is not None
    
    def test_where_t_lt(self):
        """Test t__lt filter."""
        q = Q.edges().where(t__lt=200.0)
        
        ast = q.to_ast()
        assert ast.select.where is not None
    
    def test_combining_temporal_filters(self):
        """Test combining multiple temporal filters."""
        q = Q.edges().where(t__gte=100.0, t__lte=200.0)
        
        ast = q.to_ast()
        assert ast.select.where is not None
        # Should have two comparison atoms
        comparisons = [atom for atom in ast.select.where.atoms if atom.comparison]
        assert len(comparisons) == 2


class TestDSLTemporalErrors:
    """Test error handling for temporal queries."""
    
    def test_window_requires_temporal_network_placeholder(self):
        """Placeholder test for window on non-temporal network.
        
        Note: Full error handling will be implemented in the executor.
        This is just a marker test for the expected behavior.
        """
        # Create regular network (not temporal)
        net = multinet.multi_layer_network(directed=False)
        
        # Build query with window
        q = Q.nodes().window(100.0)
        
        # When executor support is added, this should raise a clear error:
        # with pytest.raises(ValueError, match="requires.*temporal"):
        #     q.execute(net)
        
        # For now, just verify the query builds
        assert q._select.window_spec is not None
    
    def test_t_between_invalid_value(self):
        """Test that t__between with invalid value raises error."""
        with pytest.raises(ValueError, match="t__between requires a tuple"):
            Q.edges().where(t__between=100.0)  # Should be a tuple
    
    def test_temporal_context_with_regular_network_placeholder(self):
        """Placeholder test for temporal context on non-temporal network.
        
        Note: This already has some support via TemporalMultinetView,
        but we're noting expected behavior here.
        """
        net = multinet.multi_layer_network(directed=False)
        
        # This should work with the view layer
        q = Q.edges().at(150.0)
        
        # Should not raise error at build time
        assert q._select.temporal_context is not None


class TestDSLChaining:
    """Test complex DSL chaining with temporal features."""
    
    def test_full_temporal_query_chain(self):
        """Test building a complex temporal query."""
        q = (
            Q.nodes()
            .from_layers(L["social"] + L["work"])
            .during(100.0, 200.0)
            .where(degree__gt=2)
            .compute("betweenness_centrality", "pagerank")
            .window(50.0, step=25.0)
            .order_by("pagerank", desc=True)
            .limit(10)
        )
        
        ast = q.to_ast()
        
        # Verify all components are present
        assert ast.select.layer_expr is not None
        assert ast.select.temporal_context is not None
        assert ast.select.window_spec is not None
        assert ast.select.where is not None
        assert len(ast.select.compute) == 2
        assert len(ast.select.order_by) == 1
        assert ast.select.limit == 10
    
    def test_window_with_per_layer(self):
        """Test window with per-layer grouping."""
        q = (
            Q.nodes()
            .compute("degree")
            .window(100.0)
            .per_layer()
        )
        
        ast = q.to_ast()
        assert ast.select.window_spec is not None
        assert "layer" in ast.select.group_by


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
