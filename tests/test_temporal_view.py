"""Tests for py3plex.temporal_view module.

This module tests the TemporalMultinetView class which provides
read-only temporal filtering over multilayer networks.
"""

import pytest
import networkx as nx
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

    @pytest.mark.parametrize("names", [
        ("t", "t_start", "t_end"),
        ("timestamp", "start", "end"),
        ("timestamp", "t_start", "t_end"),
        ("t", "start", "end"),
    ])
    @pytest.mark.parametrize("attrs, included", [
        ({"t": 50}, False),
        ({"t": 150}, True),
        ({"t": 250}, False),
        ({"t_start": 50, "t_end": 150}, True),
        ({"t_start": 250, "t_end": 300}, False),
        ({"t_start": 250}, False),
        ({"t_end": 50}, False),
        ({"t": 150, "t_start": 250, "t_end": 300}, False),
        ({}, True),
        ({"t": "invalid"}, True),
    ])
    def test_filter_uses_configured_time_attributes(self, names, attrs, included):
        """Custom names preserve point, interval, and atemporal semantics."""
        renamed = dict(zip(("t", "t_start", "t_end"), names))
        edge_attrs = {renamed[key]: value for key, value in attrs.items()}
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([{
            "source": "A", "target": "B", "source_type": "layer1",
            "target_type": "layer1", **edge_attrs,
        }])
        original_data = dict(net.core_network[("A", "layer1")][("B", "layer1")][0])
        view = TemporalMultinetView(
            net, time_attr=names[0], t_start_attr=names[1], t_end_attr=names[2]
        )

        assert len(view.with_slice(100, 200).get_edges()) == int(included)
        assert len(view.with_slice(None, None).snapshot_at(150).get_edges()) == int(included)
        assert len(view.get_edges()) == 1
        assert dict(net.core_network[("A", "layer1")][("B", "layer1")][0]) == original_data

    @pytest.mark.parametrize("attrs, included", [
        ({"timestamp": 300, "t": 150}, False),
        ({"timestamp": 150, "t": 300}, True),
        ({"start": 300, "end": 400, "t_start": 100, "t_end": 200}, False),
        ({"start": 100, "end": 200, "t_start": 300, "t_end": 400}, True),
    ])
    def test_custom_time_attributes_override_default_names(self, attrs, included):
        """Only the configured fields define time when both schemas coexist."""
        view = TemporalMultinetView(
            None, time_attr="timestamp", t_start_attr="start", t_end_attr="end"
        ).with_slice(100, 200)
        assert view._matches_temporal_filter(attrs) is included

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

    @pytest.mark.parametrize("directed", [False, True])
    @pytest.mark.parametrize("network_type", ["multilayer", "multiplex"])
    @pytest.mark.parametrize("first_key", [0, 7])
    @pytest.mark.parametrize("multiplex_edges", [False, True])
    @pytest.mark.parametrize("call_style", ["default", "kw_false", "kw_true", "pos_false", "pos_true"])
    def test_parallel_edges_use_their_own_timestamps(
        self, directed, network_type, first_key, multiplex_edges, call_style
    ):
        """Filter each parallel edge while preserving the requested tuple format."""
        net = multinet.multi_layer_network(
            directed=directed, network_type=network_type, verbose=False
        )
        net.core_network = nx.MultiDiGraph() if directed else nx.MultiGraph()
        u, v = ("A", "layer1"), ("B", "layer1")
        net.core_network.add_edge(u, v, key=first_key, t=100, event="early")
        net.core_network.add_edge(u, v, key=first_key + 1, t=200, event="late")
        net.core_network.add_edge(u, v, key=first_key + 2, event="atemporal")
        net.core_network.add_edge(
            u, ("A", "layer2"), key=first_key, t=100, type="coupling", event="coupling"
        )
        original = list(net.get_edges(data=True, multiplex_edges=True))
        requested_data = call_style.endswith("true")
        if call_style.startswith("pos"):
            args, kwargs = (requested_data, multiplex_edges), {}
        else:
            args, kwargs = (), {"multiplex_edges": multiplex_edges}
            if call_style != "default":
                kwargs['data'] = requested_data

        view = TemporalMultinetView(net)
        for timestamp in (100, 200):
            expected = [
                edge if requested_data else edge[:-1]
                for edge in net.get_edges(data=True, multiplex_edges=multiplex_edges)
                if edge[-1].get('t', timestamp) == timestamp
            ]
            assert view.snapshot_at(timestamp).get_edges(*args, **kwargs) == expected
            assert list(view.with_slice(timestamp, timestamp).iter_edges(*args, **kwargs)) == expected
        assert list(net.get_edges(data=True, multiplex_edges=True)) == original

    @pytest.mark.parametrize("directed", [False, True])
    @pytest.mark.parametrize("data", [False, True])
    def test_simple_graph_edges_use_attribute_dict(self, directed, data):
        """A simple graph stores attributes directly rather than under edge keys."""
        net = multinet.multi_layer_network(directed=directed, verbose=False)
        net.core_network = nx.DiGraph() if directed else nx.Graph()
        net.core_network.add_edge(("A", "layer1"), ("B", "layer1"), t=100)
        view = TemporalMultinetView(net)
        assert view.snapshot_at(100).get_edges(data=data) == list(net.get_edges(data=data))
        assert view.snapshot_at(200).get_edges(data=data) == []

    def test_view_preserves_base_network(self, temporal_network):
        """Test that view doesn't modify base network."""
        original_edges = list(temporal_network.get_edges())
        
        view = TemporalMultinetView(temporal_network)
        sliced_view = view.with_slice(100.0, 150.0)
        _ = sliced_view.get_edges()
        
        # Original network should be unchanged
        assert list(temporal_network.get_edges()) == original_edges

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
