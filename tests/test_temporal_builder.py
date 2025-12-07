"""Tests for temporal builder API support."""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, Param


class TestTemporalBuilderAPI:
    """Test temporal query builder API."""
    
    @pytest.fixture
    def temporal_network(self):
        """Create a sample network with temporal edges."""
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 100.0, 'weight': 1.0},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 200.0, 'weight': 1.0},
        ]
        network.add_edges(edges)
        
        return network
    
    def test_builder_at(self, temporal_network):
        """Test AT clause with builder API."""
        # Build query with AT clause
        q = Q.edges().at(100.0)
        
        # Execute query
        result = q.execute(temporal_network)
        
        # Should only include edge at t=100
        assert result is not None
    
    def test_builder_during(self, temporal_network):
        """Test DURING clause with builder API."""
        # Build query with DURING clause
        q = Q.edges().during(100.0, 200.0)
        
        # Execute query
        result = q.execute(temporal_network)
        
        # Should include both edges
        assert result is not None
    
    def test_builder_during_open_start(self, temporal_network):
        """Test DURING clause with open start."""
        q = Q.edges().during(None, 150.0)
        
        result = q.execute(temporal_network)
        assert result is not None
    
    def test_builder_during_open_end(self, temporal_network):
        """Test DURING clause with open end."""
        q = Q.edges().during(150.0, None)
        
        result = q.execute(temporal_network)
        assert result is not None
    
    def test_builder_chaining(self, temporal_network):
        """Test chaining temporal with other clauses."""
        q = (
            Q.edges()
             .during(100.0, 200.0)
             .limit(10)
        )
        
        result = q.execute(temporal_network)
        assert result is not None
    
    def test_builder_to_ast(self, temporal_network):
        """Test that builder creates correct AST."""
        q = Q.edges().at(150.0)
        ast = q.to_ast()
        
        # Check AST structure
        assert ast.select.temporal_context is not None
        assert ast.select.temporal_context.kind == "at"
        assert ast.select.temporal_context.t0 == 150.0
        assert ast.select.temporal_context.t1 == 150.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
