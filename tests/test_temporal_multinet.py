"""Tests for TemporalMultiLayerNetwork class."""

import pytest
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.core import multinet


class TestTemporalMultiLayerNetworkBasics:
    """Test basic TemporalMultiLayerNetwork functionality."""
    
    def test_initialization_empty(self):
        """Test creating an empty temporal network."""
        tnet = TemporalMultiLayerNetwork()
        
        assert tnet is not None
        assert tnet.number_of_edges() == 0
        assert tnet.number_of_nodes() == 0
    
    def test_initialization_with_base_network(self):
        """Test creating temporal network with existing base network."""
        base = multinet.multi_layer_network(directed=False)
        tnet = TemporalMultiLayerNetwork(base_network=base)
        
        assert tnet.base_network is base
    
    def test_add_single_edge(self):
        """Test adding a single time-stamped edge."""
        tnet = TemporalMultiLayerNetwork()
        
        tnet.add_edge('A', 'layer1', 'B', 'layer1', t=100.0)
        
        assert tnet.number_of_edges() == 1
        assert len(tnet.time_index) == 1
        assert tnet.time_index[0] == 100.0
    
    def test_add_multiple_edges(self):
        """Test adding multiple time-stamped edges."""
        tnet = TemporalMultiLayerNetwork()
        
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 
             'target_type': 'layer1', 't': 100.0},
            {'source': 'B', 'target': 'C', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 200.0},
            {'source': 'C', 'target': 'A', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 150.0},
        ]
        
        tnet.add_edges(edges)
        
        assert tnet.number_of_edges() == 3
        assert len(tnet.time_index) == 3
        # Check time index is sorted
        assert tnet.time_index == [100.0, 150.0, 200.0]
    
    def test_add_edges_tuple_format(self):
        """Test adding edges in tuple format."""
        tnet = TemporalMultiLayerNetwork()
        
        edges = [
            ('A', 'layer1', 'B', 'layer1', 100.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 200.0, 2.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        
        assert tnet.number_of_edges() == 2
    
    def test_time_range(self):
        """Test getting time range of network."""
        tnet = TemporalMultiLayerNetwork()
        
        # Empty network
        t_min, t_max = tnet.time_range()
        assert t_min is None
        assert t_max is None
        
        # Add edges
        tnet.add_edge('A', 'layer1', 'B', 'layer1', t=100.0)
        tnet.add_edge('B', 'layer1', 'C', 'layer1', t=200.0)
        
        t_min, t_max = tnet.time_range()
        assert t_min == 100.0
        assert t_max == 200.0


class TestTemporalQueries:
    """Test temporal querying functionality."""
    
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
            {'source': 'A', 'target': 'D', 'source_type': 'layer2',
             'target_type': 'layer2', 't': 120.0, 'weight': 1.0},
        ]
        
        tnet.add_edges(edges)
        return tnet
    
    def test_edges_between(self, sample_temporal_network):
        """Test filtering edges by time range."""
        edges = list(sample_temporal_network.edges_between(100.0, 150.0))
        
        # Should include edges at t=100 and t=150
        assert len(edges) == 3  # 100, 120, 150
        
        times = [e['t'] for e in edges]
        assert 100.0 in times
        assert 120.0 in times
        assert 150.0 in times
        assert 200.0 not in times
    
    def test_edges_between_layer_filter(self, sample_temporal_network):
        """Test filtering edges by time and layer."""
        edges = list(sample_temporal_network.edges_between(
            100.0, 200.0, layers=['layer1']
        ))
        
        # Should only get layer1 edges
        assert len(edges) == 3
        for edge in edges:
            assert edge['source_type'] == 'layer1'
            assert edge['target_type'] == 'layer1'
    
    def test_slice_time_window(self, sample_temporal_network):
        """Test creating a time-sliced subnetwork."""
        sliced = sample_temporal_network.slice_time_window(100.0, 150.0)
        
        assert isinstance(sliced, TemporalMultiLayerNetwork)
        assert sliced.number_of_edges() == 3
    
    def test_snapshot_at_up_to(self, sample_temporal_network):
        """Test creating cumulative snapshot."""
        snapshot = sample_temporal_network.snapshot_at(150.0, mode="up_to")
        
        # Should include edges at t <= 150
        assert isinstance(snapshot, multinet.multi_layer_network)
        # Check that we have edges from base network
        assert snapshot.core_network.number_of_edges() > 0
    
    def test_snapshot_at_exact(self, sample_temporal_network):
        """Test creating exact-time snapshot."""
        snapshot = sample_temporal_network.snapshot_at(150.0, mode="exact")
        
        # Should only include edge at exactly t=150
        assert isinstance(snapshot, multinet.multi_layer_network)


class TestWindowIteration:
    """Test sliding window iteration."""
    
    @pytest.fixture
    def sample_temporal_network(self):
        """Create a sample temporal network spanning time 0-300."""
        tnet = TemporalMultiLayerNetwork()
        
        for t in range(0, 301, 50):
            tnet.add_edge(f'N{t}', 'layer1', f'N{t+1}', 'layer1', t=float(t))
        
        return tnet
    
    def test_window_iter_non_overlapping(self, sample_temporal_network):
        """Test non-overlapping window iteration."""
        windows = list(sample_temporal_network.window_iter(
            window_size=100.0,
            return_type="temporal"
        ))
        
        assert len(windows) > 0
        
        for t_start, t_end, window_net in windows:
            assert t_end - t_start == 100.0
            assert isinstance(window_net, TemporalMultiLayerNetwork)
    
    def test_window_iter_overlapping(self, sample_temporal_network):
        """Test overlapping window iteration."""
        windows = list(sample_temporal_network.window_iter(
            window_size=100.0,
            step=50.0,
            return_type="temporal"
        ))
        
        assert len(windows) > 0
        
        # Check that windows overlap
        if len(windows) >= 2:
            w1_start, w1_end, _ = windows[0]
            w2_start, w2_end, _ = windows[1]
            
            # Second window should start 50 units after first
            assert w2_start == w1_start + 50.0
    
    def test_window_iter_snapshot_mode(self, sample_temporal_network):
        """Test window iteration with snapshot return type."""
        windows = list(sample_temporal_network.window_iter(
            window_size=100.0,
            return_type="snapshot"
        ))
        
        assert len(windows) > 0
        
        for t_start, t_end, window_net in windows:
            assert isinstance(window_net, multinet.multi_layer_network)


class TestFactoryMethods:
    """Test factory methods for creating temporal networks."""
    
    def test_from_multilayer_network(self):
        """Test creating temporal network from existing network."""
        # Create a base network with temporal edges
        base = multinet.multi_layer_network(directed=False)
        
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 100.0},
            {'source': 'B', 'target': 'C', 'source_type': 'layer1',
             'target_type': 'layer1', 't': 200.0},
        ]
        
        base.add_edges(edges)
        
        # Convert to temporal network
        tnet = TemporalMultiLayerNetwork.from_multilayer_network(base)
        
        assert isinstance(tnet, TemporalMultiLayerNetwork)
        # Note: extraction may not work perfectly if base network structure differs
        # This is a basic sanity check
    
    def test_from_pandas(self):
        """Test creating temporal network from pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")
        
        df = pd.DataFrame([
            {'source': 'A', 'target': 'B', 'layer_u': 'layer1',
             'layer_v': 'layer1', 't': 100.0, 'weight': 1.0},
            {'source': 'B', 'target': 'C', 'layer_u': 'layer1',
             'layer_v': 'layer1', 't': 200.0, 'weight': 1.0},
        ])
        
        tnet = TemporalMultiLayerNetwork.from_pandas(df)
        
        assert isinstance(tnet, TemporalMultiLayerNetwork)
        assert tnet.number_of_edges() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
