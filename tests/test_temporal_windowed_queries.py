"""Tests for windowed query execution."""

import pytest
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q


class TestWindowedQueryExecution:
    """Test executing windowed queries."""
    
    @pytest.fixture
    def temporal_network(self):
        """Create a sample temporal network."""
        tnet = TemporalMultiLayerNetwork(directed=False)
        
        # Add edges across time
        edges = [
            ('A', 'layer1', 'B', 'layer1', 50.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 50.0, 1.0),
            ('C', 'layer1', 'A', 'layer1', 100.0, 1.0),
            ('A', 'layer1', 'D', 'layer1', 150.0, 1.0),
            ('D', 'layer1', 'B', 'layer1', 200.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 250.0, 1.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        return tnet
    
    def test_windowed_query_basic(self, temporal_network):
        """Test basic windowed query execution."""
        q = Q.nodes().compute("degree").window(100.0)
        
        result = q.execute(temporal_network)
        
        # Should return windowed results
        assert result is not None
        assert result.meta.get('windowed') is True
        assert result.meta.get('window_count', 0) > 0
    
    def test_windowed_query_with_step(self, temporal_network):
        """Test windowed query with step parameter."""
        q = Q.nodes().compute("degree").window(100.0, step=50.0)
        
        result = q.execute(temporal_network)
        
        assert result is not None
        assert result.meta.get('windowed') is True
        # Should have more windows with overlapping
        assert result.meta.get('window_count', 0) > 0
    
    def test_windowed_query_duration_strings(self, temporal_network):
        """Test windowed query with duration strings."""
        # Note: This network uses numeric timestamps, but we can still
        # test that the duration string parsing works
        q = Q.nodes().compute("degree").window("100s")
        
        result = q.execute(temporal_network)
        
        assert result is not None
        assert result.meta.get('windowed') is True
    
    def test_windowed_query_list_aggregation(self, temporal_network):
        """Test windowed query with list aggregation (default)."""
        q = Q.nodes().compute("degree").window(100.0, aggregation="list")
        
        result = q.execute(temporal_network)
        
        assert result is not None
        assert result.meta.get('aggregation') == 'list'
        # Items should be a list of QueryResult objects
        assert isinstance(result.items, list)
    
    def test_windowed_query_concat_aggregation(self, temporal_network):
        """Test windowed query with concat aggregation."""
        try:
            import pandas as pd
            
            q = Q.nodes().compute("degree").window(100.0, aggregation="concat")
            
            result = q.execute(temporal_network)
            
            assert result is not None
            assert result.meta.get('aggregation') == 'concat'
            # Should have combined results
            assert len(result.items) > 0
        except ImportError:
            pytest.skip("pandas not available")
    
    def test_windowed_query_with_temporal_filter(self, temporal_network):
        """Test combining window with temporal filter."""
        q = (
            Q.nodes()
            .during(50.0, 200.0)
            .compute("degree")
            .window(50.0)
        )
        
        result = q.execute(temporal_network)
        
        assert result is not None
        assert result.meta.get('windowed') is True
    
    def test_windowed_query_with_ordering(self, temporal_network):
        """Test windowed query with ordering."""
        q = (
            Q.nodes()
            .compute("degree")
            .window(100.0)
            .order_by("degree", desc=True)
        )
        
        result = q.execute(temporal_network)
        
        assert result is not None
        assert result.meta.get('windowed') is True
    
    def test_windowed_query_non_temporal_network_error(self):
        """Test that windowed query on non-temporal network raises error."""
        from py3plex.core import multinet
        
        # Create regular network
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 
             'target_type': 'layer1'},
        ])
        
        q = Q.nodes().window(100.0)
        
        # Should raise error
        with pytest.raises(Exception, match="TemporalMultiLayerNetwork|window"):
            q.execute(net)
    
    def test_windowed_query_invalid_duration_string(self, temporal_network):
        """Test that invalid duration string raises error."""
        q = Q.nodes().window("invalid")
        
        with pytest.raises(Exception, match="Invalid|duration"):
            q.execute(temporal_network)


class TestWindowedQueryResults:
    """Test windowed query result structure."""
    
    @pytest.fixture
    def temporal_network(self):
        """Create a simple temporal network."""
        tnet = TemporalMultiLayerNetwork(directed=False)
        
        edges = [
            ('A', 'layer1', 'B', 'layer1', 100.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 150.0, 1.0),
            ('C', 'layer1', 'A', 'layer1', 200.0, 1.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        return tnet
    
    def test_window_metadata(self, temporal_network):
        """Test that window metadata is included in results."""
        q = Q.nodes().compute("degree").window(100.0, aggregation="list")
        
        result = q.execute(temporal_network)
        
        # Check that each window result has metadata
        if isinstance(result.items, list):
            for window_result in result.items:
                assert 'window_start' in window_result.meta
                assert 'window_end' in window_result.meta
    
    def test_window_result_to_pandas(self, temporal_network):
        """Test converting windowed results to pandas."""
        try:
            import pandas as pd
            
            q = Q.nodes().compute("degree").window(100.0, aggregation="concat")
            
            result = q.execute(temporal_network)
            df = result.to_pandas()
            
            # Should have window columns
            assert 'window_start' in df.columns
            assert 'window_end' in df.columns
            assert 'degree' in df.columns
        except ImportError:
            pytest.skip("pandas not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
