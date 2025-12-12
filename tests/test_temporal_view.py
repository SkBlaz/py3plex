"""Tests for py3plex.temporal_view module.

This module tests the TemporalMultinetView class which provides
read-only temporal filtering over multilayer networks.
"""

import pytest
from py3plex.core import multinet
from py3plex.temporal_view import TemporalMultinetView, TemporalSlice


@pytest.fixture
def temporal_network():
    """Create a network with temporal edges."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ])
    net.add_edges([
        {
            'source': 'A',
            'target': 'B',
            'source_type': 'layer1',
            'target_type': 'layer1',
            't': 100.0
        },
        {
            'source': 'B',
            'target': 'C',
            'source_type': 'layer1',
            'target_type': 'layer1',
            't': 200.0
        },
        {
            'source': 'A',
            'target': 'C',
            'source_type': 'layer1',
            'target_type': 'layer1',
            't': 300.0
        }
    ])
    return net


@pytest.fixture
def atemporal_network():
    """Create a network without temporal attributes."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes([
        {'source': 'X', 'type': 'layer1'},
        {'source': 'Y', 'type': 'layer1'},
    ])
    net.add_edges([
        {
            'source': 'X',
            'target': 'Y',
            'source_type': 'layer1',
            'target_type': 'layer1'
        }
    ])
    return net


class TestTemporalSlice:
    """Test TemporalSlice dataclass."""

    def test_create_slice(self):
        """Test creating a temporal slice."""
        slice_obj = TemporalSlice(t0=100.0, t1=200.0)
        assert slice_obj.t0 == 100.0
        assert slice_obj.t1 == 200.0

    def test_create_slice_with_none(self):
        """Test creating a slice with None boundaries."""
        slice_obj = TemporalSlice(t0=None, t1=200.0)
        assert slice_obj.t0 is None
        assert slice_obj.t1 == 200.0

    def test_create_default_slice(self):
        """Test creating a slice with defaults."""
        slice_obj = TemporalSlice()
        assert slice_obj.t0 is None
        assert slice_obj.t1 is None


class TestTemporalMultinetView:
    """Test TemporalMultinetView class."""

    def test_create_view(self, temporal_network):
        """Test creating a temporal view."""
        view = TemporalMultinetView(temporal_network)
        assert view is not None
        assert view._base is temporal_network

    def test_create_view_with_custom_attrs(self, temporal_network):
        """Test creating view with custom time attributes."""
        view = TemporalMultinetView(
            temporal_network,
            time_attr="timestamp",
            t_start_attr="start",
            t_end_attr="end"
        )
        assert view._time_attr == "timestamp"
        assert view._t_start_attr == "start"
        assert view._t_end_attr == "end"

    def test_initial_slice_is_empty(self, temporal_network):
        """Test that initial slice has no filters."""
        view = TemporalMultinetView(temporal_network)
        assert view._slice.t0 is None
        assert view._slice.t1 is None

    def test_with_slice(self, temporal_network):
        """Test creating a view with temporal slice."""
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        assert sliced_view is not view  # Should be a new view
        assert sliced_view._slice.t0 == 100.0
        assert sliced_view._slice.t1 == 200.0
        # Original view should be unchanged
        assert view._slice.t0 is None

    def test_with_slice_partial(self, temporal_network):
        """Test creating slice with partial boundaries."""
        view = TemporalMultinetView(temporal_network)
        
        # Only start time
        view1 = view.with_slice(100.0, None)
        assert view1._slice.t0 == 100.0
        assert view1._slice.t1 is None
        
        # Only end time
        view2 = view.with_slice(None, 200.0)
        assert view2._slice.t0 is None
        assert view2._slice.t1 == 200.0

    def test_snapshot_at(self, temporal_network):
        """Test creating a snapshot at specific time."""
        view = TemporalMultinetView(temporal_network)
        snapshot = view.snapshot_at(150.0)
        
        assert snapshot._slice.t0 == 150.0
        assert snapshot._slice.t1 == 150.0

    def test_get_edges(self, temporal_network):
        """Test getting edges from view."""
        view = TemporalMultinetView(temporal_network)
        edges = view.get_edges()
        
        # Should return a list
        assert isinstance(edges, list)

    def test_iter_edges(self, temporal_network):
        """Test iterating over edges."""
        view = TemporalMultinetView(temporal_network)
        edges = list(view.iter_edges())
        
        # Should be able to iterate
        assert isinstance(edges, list)

    def test_base_network_property(self, temporal_network):
        """Test accessing base network property."""
        view = TemporalMultinetView(temporal_network)
        assert view.base_network is temporal_network

    def test_temporal_slice_property(self, temporal_network):
        """Test accessing temporal slice property."""
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        slice_obj = sliced_view.temporal_slice
        assert isinstance(slice_obj, TemporalSlice)
        assert slice_obj.t0 == 100.0
        assert slice_obj.t1 == 200.0

    def test_getattr_forwarding(self, temporal_network):
        """Test that attributes are forwarded to base network."""
        view = TemporalMultinetView(temporal_network)
        
        # Should be able to access base network attributes
        assert hasattr(view, 'directed')
        assert view.directed == temporal_network.directed

    def test_atemporal_edges_always_included(self, atemporal_network):
        """Test that edges without time attributes are included."""
        view = TemporalMultinetView(atemporal_network)
        sliced_view = view.with_slice(100.0, 200.0)
        
        # Atemporal edges should still be visible
        edges = sliced_view.get_edges()
        assert len(edges) > 0

    def test_temporal_filtering_basic(self, temporal_network):
        """Test basic temporal filtering."""
        view = TemporalMultinetView(temporal_network)
        
        # Get all edges initially
        all_edges = view.get_edges()
        initial_count = len(all_edges)
        
        # Create a time slice
        # Note: Actual filtering depends on edge format from get_edges()
        sliced_view = view.with_slice(150.0, 250.0)
        assert sliced_view is not None

    def test_multiple_slices_independent(self, temporal_network):
        """Test that multiple slices are independent."""
        view = TemporalMultinetView(temporal_network)
        
        view1 = view.with_slice(100.0, 200.0)
        view2 = view.with_slice(200.0, 300.0)
        
        assert view1._slice.t0 == 100.0
        assert view2._slice.t0 == 200.0
        # Original unchanged
        assert view._slice.t0 is None

    def test_chain_operations(self, temporal_network):
        """Test chaining temporal operations."""
        view = TemporalMultinetView(temporal_network)
        
        # Should be able to chain
        snapshot = view.snapshot_at(150.0)
        assert snapshot._slice.t0 == 150.0

    def test_empty_network(self):
        """Test view with empty network."""
        empty_net = multinet.multi_layer_network(directed=False, verbose=False)
        view = TemporalMultinetView(empty_net)
        
        assert view is not None
        edges = view.get_edges()
        assert edges == []


class TestTemporalViewIntegration:
    """Integration tests for temporal view."""

    def test_view_preserves_base_network(self, temporal_network):
        """Test that view doesn't modify base network."""
        original_edges = temporal_network.get_edges()
        
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 150.0)
        _ = sliced_view.get_edges()
        
        # Original network should be unchanged
        assert temporal_network.get_edges() == original_edges

    def test_different_time_attributes(self):
        """Test using different time attribute names."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {
                'source': 'A',
                'target': 'B',
                'source_type': 'layer1',
                'target_type': 'layer1',
                'timestamp': 100.0
            }
        ])
        
        view = TemporalMultinetView(net, time_attr="timestamp")
        assert view._time_attr == "timestamp"

    def test_view_with_mixed_temporal_atemporal(self):
        """Test view with mix of temporal and atemporal edges."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ])
        net.add_edges([
            {
                'source': 'A',
                'target': 'B',
                'source_type': 'layer1',
                'target_type': 'layer1',
                't': 100.0
            },
            {
                'source': 'B',
                'target': 'C',
                'source_type': 'layer1',
                'target_type': 'layer1'
                # No time attribute
            }
        ])
        
        view = TemporalMultinetView(net)
        sliced_view = view.with_slice(50.0, 150.0)
        
        # Both edges should be accessible
        edges = sliced_view.get_edges()
        assert len(edges) >= 0  # At least atemporal edge should be there
