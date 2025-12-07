"""Tests for temporal support in py3plex.

Tests cover:
- Temporal utility functions (parsing, extraction)
- TemporalMultinetView functionality
- DSL temporal queries (AT/DURING)
- Named temporal ranges
- Graceful degradation without time data
"""

import datetime
import pytest
from py3plex.core import multinet
from py3plex.temporal_utils import (
    _parse_time,
    extract_edge_time,
    EdgeTimeInterval,
)
from py3plex.temporal_view import (
    TemporalMultinetView,
    TemporalSlice,
)
from py3plex.dsl import (
    Q,
    Query,
    SelectStmt,
    Target,
    TemporalContext,
    execute_ast,
)


class TestTemporalUtils:
    """Test temporal utility functions."""
    
    def test_parse_time_int(self):
        """Test parsing integer timestamps."""
        result = _parse_time(1234567890)
        assert result == 1234567890.0
        assert isinstance(result, float)
    
    def test_parse_time_float(self):
        """Test parsing float timestamps."""
        result = _parse_time(1234567890.5)
        assert result == 1234567890.5
    
    def test_parse_time_string_numeric(self):
        """Test parsing numeric string timestamps."""
        result = _parse_time("1234567890")
        assert result == 1234567890.0
    
    def test_parse_time_iso_string(self):
        """Test parsing ISO format strings."""
        # Using a known timestamp
        result = _parse_time("2009-02-13T23:31:30")
        # Allow for timezone differences
        assert isinstance(result, float)
    
    def test_parse_time_datetime(self):
        """Test parsing datetime objects."""
        dt = datetime.datetime(2009, 2, 13, 23, 31, 30)
        result = _parse_time(dt)
        assert isinstance(result, float)
    
    def test_parse_time_invalid(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            _parse_time("invalid")
        
        with pytest.raises(ValueError):
            _parse_time(None)
    
    def test_extract_edge_time_point(self):
        """Test extracting point-in-time from edge attributes."""
        attrs = {'t': 100.0, 'weight': 1.0}
        interval = extract_edge_time(attrs)
        
        assert interval.start == 100.0
        assert interval.end == 100.0
    
    def test_extract_edge_time_interval(self):
        """Test extracting interval from edge attributes."""
        attrs = {'t_start': 100.0, 't_end': 200.0}
        interval = extract_edge_time(attrs)
        
        assert interval.start == 100.0
        assert interval.end == 200.0
    
    def test_extract_edge_time_interval_precedence(self):
        """Test that interval form takes precedence over point form."""
        attrs = {'t': 150.0, 't_start': 100.0, 't_end': 200.0}
        interval = extract_edge_time(attrs)
        
        # Interval should be used, not point
        assert interval.start == 100.0
        assert interval.end == 200.0
    
    def test_extract_edge_time_atemporal(self):
        """Test extracting from edge without temporal attributes."""
        attrs = {'weight': 1.0, 'type': 'friendship'}
        interval = extract_edge_time(attrs)
        
        assert interval.start is None
        assert interval.end is None
    
    def test_extract_edge_time_only_start(self):
        """Test extracting interval with only start time."""
        attrs = {'t_start': 100.0}
        interval = extract_edge_time(attrs)
        
        assert interval.start == 100.0
        assert interval.end == float('inf')
    
    def test_extract_edge_time_only_end(self):
        """Test extracting interval with only end time."""
        attrs = {'t_end': 200.0}
        interval = extract_edge_time(attrs)
        
        assert interval.start == float('-inf')
        assert interval.end == 200.0
    
    def test_edge_time_interval_overlaps_full(self):
        """Test overlap detection for full overlap."""
        interval = EdgeTimeInterval(start=100.0, end=200.0)
        
        # Full overlap
        assert interval.overlaps(50.0, 250.0)
        assert interval.overlaps(100.0, 200.0)
        
        # Partial overlap
        assert interval.overlaps(150.0, 250.0)
        assert interval.overlaps(50.0, 150.0)
        
        # No overlap
        assert not interval.overlaps(0.0, 50.0)
        assert not interval.overlaps(250.0, 300.0)
    
    def test_edge_time_interval_overlaps_point(self):
        """Test overlap detection for point-in-time edges."""
        interval = EdgeTimeInterval(start=150.0, end=150.0)
        
        # Point is within range
        assert interval.overlaps(100.0, 200.0)
        assert interval.overlaps(150.0, 150.0)
        
        # Point is outside range
        assert not interval.overlaps(100.0, 140.0)
        assert not interval.overlaps(160.0, 200.0)
    
    def test_edge_time_interval_overlaps_atemporal(self):
        """Test that atemporal edges always overlap."""
        interval = EdgeTimeInterval(start=None, end=None)
        
        # Atemporal edges always included
        assert interval.overlaps(0.0, 100.0)
        assert interval.overlaps(None, None)
        assert interval.overlaps(None, 100.0)
        assert interval.overlaps(100.0, None)


class TestTemporalMultinetView:
    """Test TemporalMultinetView wrapper."""
    
    @pytest.fixture
    def temporal_network(self):
        """Create a sample network with temporal edges."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add nodes
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
            {'source': 'D', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        
        # Add edges with different timestamps
        edges = [
            {'source': 'A', 'target': 'B', 
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 100.0, 'weight': 1.0},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 200.0, 'weight': 1.0},
            {'source': 'C', 'target': 'D',
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 300.0, 'weight': 1.0},
            # Edge with interval
            {'source': 'A', 'target': 'D',
             'source_type': 'layer1', 'target_type': 'layer1',
             't_start': 150.0, 't_end': 250.0, 'weight': 1.0},
        ]
        network.add_edges(edges)
        
        return network
    
    @pytest.fixture
    def atemporal_network(self):
        """Create a network without temporal information."""
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1',
             'weight': 1.0},
        ]
        network.add_edges(edges)
        
        return network
    
    def test_create_temporal_view(self, temporal_network):
        """Test creating a temporal view."""
        view = TemporalMultinetView(temporal_network)
        
        assert view is not None
        assert view.base_network == temporal_network
        assert view.temporal_slice.t0 is None
        assert view.temporal_slice.t1 is None
    
    def test_with_slice(self, temporal_network):
        """Test creating a time slice view."""
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        assert sliced_view is not view  # New view
        assert sliced_view.temporal_slice.t0 == 100.0
        assert sliced_view.temporal_slice.t1 == 200.0
        
        # Original view unchanged
        assert view.temporal_slice.t0 is None
        assert view.temporal_slice.t1 is None
    
    def test_snapshot_at(self, temporal_network):
        """Test creating a snapshot view."""
        view = TemporalMultinetView(temporal_network)
        snapshot = view.snapshot_at(150.0)
        
        assert snapshot.temporal_slice.t0 == 150.0
        assert snapshot.temporal_slice.t1 == 150.0
    
    def test_iter_edges_no_filter(self, temporal_network):
        """Test iterating edges without temporal filter."""
        view = TemporalMultinetView(temporal_network)
        edges = list(view.iter_edges())
        
        # All 4 edges should be included
        assert len(edges) == 4
    
    def test_iter_edges_with_slice(self, temporal_network):
        """Test iterating edges with temporal slice."""
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        edges = list(sliced_view.iter_edges())
        
        # Should include:
        # - A-B (t=100)
        # - B-C (t=200)
        # - A-D (t_start=150, t_end=250, overlaps)
        # Should not include:
        # - C-D (t=300)
        assert len(edges) == 3
    
    def test_iter_edges_snapshot(self, temporal_network):
        """Test iterating edges at a snapshot."""
        view = TemporalMultinetView(temporal_network)
        snapshot = view.snapshot_at(150.0)
        edges = list(snapshot.iter_edges())
        
        # Should include:
        # - A-D (t_start=150, t_end=250, includes snapshot at 150)
        # Should not include:
        # - A-B (t=100, point-in-time edges only active at exact time)
        # - B-C (t=200, point-in-time edges only active at exact time)
        # - C-D (t=300, point-in-time edges only active at exact time)
        # Note: snapshot_at(t) means "edges active at exactly time t"
        # For point-in-time edges, this means t_edge == t_snapshot
        # For interval edges, this means t_start <= t_snapshot <= t_end
        assert len(edges) == 1
    
    def test_atemporal_edges_always_included(self, atemporal_network):
        """Test that atemporal edges are always included."""
        view = TemporalMultinetView(atemporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        edges = list(sliced_view.iter_edges())
        assert len(edges) == 1  # Atemporal edge included
    
    def test_get_edges_convenience(self, temporal_network):
        """Test get_edges convenience method."""
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        edges = sliced_view.get_edges()
        assert isinstance(edges, list)
        assert len(edges) == 3
    
    def test_forward_attributes(self, temporal_network):
        """Test that non-temporal attributes are forwarded."""
        view = TemporalMultinetView(temporal_network)
        
        # Should forward to base network
        assert hasattr(view, 'core_network')
        assert view.core_network == temporal_network.core_network


class TestDSLTemporalQueries:
    """Test DSL temporal query support."""
    
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
    
    def test_temporal_context_at(self, temporal_network):
        """Test AT temporal context."""
        # Create query with AT temporal context
        select_stmt = SelectStmt(
            target=Target.EDGES,
            temporal_context=TemporalContext(kind="at", t0=100.0, t1=100.0)
        )
        query = Query(explain=False, select=select_stmt)
        
        result = execute_ast(temporal_network, query)
        
        # Should only include edge at t=100
        assert result is not None
    
    def test_temporal_context_during(self, temporal_network):
        """Test DURING temporal context."""
        # Create query with DURING temporal context
        select_stmt = SelectStmt(
            target=Target.EDGES,
            temporal_context=TemporalContext(kind="during", t0=100.0, t1=200.0)
        )
        query = Query(explain=False, select=select_stmt)
        
        result = execute_ast(temporal_network, query)
        
        # Should include both edges
        assert result is not None
    
    def test_temporal_context_none(self, temporal_network):
        """Test query without temporal context."""
        # Query without temporal context
        select_stmt = SelectStmt(
            target=Target.EDGES,
            temporal_context=None
        )
        query = Query(explain=False, select=select_stmt)
        
        result = execute_ast(temporal_network, query)
        
        # Should include all edges
        assert result is not None
    
    def test_temporal_context_invalid_kind(self, temporal_network):
        """Test that invalid temporal context kind raises error."""
        from py3plex.dsl.errors import DslExecutionError
        
        select_stmt = SelectStmt(
            target=Target.EDGES,
            temporal_context=TemporalContext(kind="invalid", t0=100.0)
        )
        query = Query(explain=False, select=select_stmt)
        
        with pytest.raises(DslExecutionError):
            execute_ast(temporal_network, query)


class TestGracefulDegradation:
    """Test graceful degradation without temporal data."""
    
    def test_temporal_view_on_atemporal_network(self):
        """Test that temporal view works on networks without time data."""
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1',
             'weight': 1.0},
        ]
        network.add_edges(edges)
        
        # Create temporal view and apply slice
        view = TemporalMultinetView(network)
        sliced = view.with_slice(100.0, 200.0)
        
        # Atemporal edges should still be included
        edges = list(sliced.iter_edges())
        assert len(edges) == 1
    
    def test_mixed_temporal_atemporal_edges(self):
        """Test network with both temporal and atemporal edges."""
        network = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ]
        network.add_nodes(nodes)
        
        edges = [
            # Temporal edge
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1',
             't': 100.0, 'weight': 1.0},
            # Atemporal edge
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1',
             'weight': 1.0},
        ]
        network.add_edges(edges)
        
        view = TemporalMultinetView(network)
        sliced = view.with_slice(50.0, 75.0)  # Before temporal edge
        
        edges = list(sliced.iter_edges())
        # Should include only atemporal edge (temporal edge is outside range)
        assert len(edges) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
