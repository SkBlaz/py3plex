"""Tests for temporal streaming algorithms."""

import pytest
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.algorithms.temporal import (
    streaming_pagerank,
    streaming_community_change,
)


class TestStreamingPageRank:
    """Test streaming PageRank algorithm."""
    
    @pytest.fixture
    def simple_temporal_network(self):
        """Create a simple temporal network for testing."""
        tnet = TemporalMultiLayerNetwork(directed=True)
        
        # Create a simple chain: A -> B -> C -> A over time
        edges = [
            ('A', 'layer1', 'B', 'layer1', 100.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 150.0, 1.0),
            ('C', 'layer1', 'A', 'layer1', 200.0, 1.0),
            ('A', 'layer1', 'D', 'layer1', 250.0, 1.0),
            ('D', 'layer1', 'A', 'layer1', 300.0, 1.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        return tnet
    
    def test_streaming_pagerank_runs(self, simple_temporal_network):
        """Test that streaming PageRank runs without error."""
        windows = list(streaming_pagerank(
            simple_temporal_network,
            window_size=100.0,
            max_iter_per_window=5,
        ))
        
        assert len(windows) > 0
        
        for t_start, t_end, scores in windows:
            assert isinstance(scores, dict)
            assert t_end > t_start
    
    def test_streaming_pagerank_normalization(self, simple_temporal_network):
        """Test that PageRank scores are normalized."""
        windows = list(streaming_pagerank(
            simple_temporal_network,
            window_size=100.0,
            normalize=True,
        ))
        
        for t_start, t_end, scores in windows:
            if scores:  # If there are nodes in this window
                total = sum(scores.values())
                # Allow small floating point error
                assert abs(total - 1.0) < 1e-6, f"Scores don't sum to 1: {total}"
    
    def test_streaming_pagerank_incremental(self, simple_temporal_network):
        """Test that PageRank updates incrementally across windows."""
        initial_scores = {'A': 0.5, 'B': 0.3, 'C': 0.2}
        
        windows = list(streaming_pagerank(
            simple_temporal_network,
            window_size=100.0,
            initial_scores=initial_scores,
        ))
        
        # Just check it runs with initial scores
        assert len(windows) > 0
    
    def test_streaming_pagerank_empty_window(self):
        """Test PageRank with empty windows."""
        tnet = TemporalMultiLayerNetwork(directed=True)
        
        # Add edge far in the future
        tnet.add_edge('A', 'layer1', 'B', 'layer1', t=1000.0)
        
        windows = list(streaming_pagerank(
            tnet,
            window_size=50.0,
            step=50.0,
        ))
        
        # Should handle empty windows gracefully
        assert windows is not None


class TestStreamingCommunityChange:
    """Test streaming community change detection."""
    
    @pytest.fixture
    def temporal_network_with_communities(self):
        """Create a temporal network with evolving communities."""
        tnet = TemporalMultiLayerNetwork(directed=False)
        
        # Time 0-100: Two separate triangles
        for src, tgt in [('A', 'B'), ('B', 'C'), ('C', 'A')]:
            tnet.add_edge(src, 'layer1', tgt, 'layer1', t=50.0)
        
        for src, tgt in [('D', 'E'), ('E', 'F'), ('F', 'D')]:
            tnet.add_edge(src, 'layer1', tgt, 'layer1', t=50.0)
        
        # Time 100-200: Bridge between communities
        tnet.add_edge('A', 'layer1', 'D', 'layer1', t=150.0)
        
        # Time 200-300: More connections
        tnet.add_edge('B', 'layer1', 'E', 'layer1', t=250.0)
        tnet.add_edge('C', 'layer1', 'F', 'layer1', t=250.0)
        
        return tnet
    
    def simple_community_detector(self, network):
        """Simple community detector based on connected components."""
        import networkx as nx
        
        graph = network.core_network if hasattr(network, 'core_network') else network
        
        # Use connected components as communities
        communities = {}
        for i, component in enumerate(nx.connected_components(graph)):
            for node in component:
                communities[node] = i
        
        return communities
    
    def test_streaming_community_change_runs(self, temporal_network_with_communities):
        """Test that streaming community change detection runs."""
        results = list(streaming_community_change(
            temporal_network_with_communities,
            self.simple_community_detector,
            window_size=100.0,
        ))
        
        assert len(results) > 0
        
        for t_start, t_end, communities, change_score in results:
            assert isinstance(communities, dict)
            assert isinstance(change_score, float)
            assert 0.0 <= change_score <= 1.0
    
    def test_streaming_community_first_window_zero_change(self, temporal_network_with_communities):
        """Test that first window has zero change score."""
        results = list(streaming_community_change(
            temporal_network_with_communities,
            self.simple_community_detector,
            window_size=100.0,
        ))
        
        if results:
            # First window should have change score of 0
            _, _, _, first_change = results[0]
            assert first_change == 0.0
    
    def test_streaming_community_change_metrics(self, temporal_network_with_communities):
        """Test different change metrics."""
        for metric in ["jaccard", "node_moves"]:
            results = list(streaming_community_change(
                temporal_network_with_communities,
                self.simple_community_detector,
                window_size=100.0,
                change_metric=metric,
            ))
            
            assert len(results) > 0
    
    def test_streaming_community_with_nmi(self, temporal_network_with_communities):
        """Test NMI metric (if sklearn available)."""
        try:
            import sklearn
            
            results = list(streaming_community_change(
                temporal_network_with_communities,
                self.simple_community_detector,
                window_size=100.0,
                change_metric="nmi",
            ))
            
            assert len(results) > 0
        except ImportError:
            pytest.skip("sklearn not available for NMI metric")


class TestStreamingDegree:
    """Test streaming degree centrality."""
    
    def test_streaming_degree_import(self):
        """Test that streaming degree centrality can be imported."""
        from py3plex.algorithms.temporal.centrality import streaming_degree_centrality
        
        assert streaming_degree_centrality is not None
    
    def test_streaming_degree_basic(self):
        """Test basic streaming degree centrality."""
        from py3plex.algorithms.temporal.centrality import streaming_degree_centrality
        
        tnet = TemporalMultiLayerNetwork(directed=False)
        
        edges = [
            ('A', 'layer1', 'B', 'layer1', 100.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 150.0, 1.0),
            ('C', 'layer1', 'D', 'layer1', 200.0, 1.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        
        results = list(streaming_degree_centrality(
            tnet,
            window_size=100.0,
        ))
        
        assert len(results) > 0
        
        for t_start, t_end, centrality in results:
            assert isinstance(centrality, dict)


class TestCommunityEvents:
    """Test community event detection."""
    
    def test_detect_community_events_import(self):
        """Test that detect_community_events can be imported."""
        from py3plex.algorithms.temporal.community import detect_community_events
        
        assert detect_community_events is not None
    
    def test_detect_community_events_basic(self):
        """Test basic community event detection."""
        from py3plex.algorithms.temporal.community import detect_community_events
        
        tnet = TemporalMultiLayerNetwork(directed=False)
        
        # Create simple temporal network
        edges = [
            ('A', 'layer1', 'B', 'layer1', 100.0, 1.0),
            ('B', 'layer1', 'C', 'layer1', 150.0, 1.0),
        ]
        
        tnet.add_edges(edges, input_type="tuple")
        
        def simple_detector(net):
            import networkx as nx
            graph = net.core_network if hasattr(net, 'core_network') else net
            communities = {}
            for i, comp in enumerate(nx.connected_components(graph)):
                for node in comp:
                    communities[node] = i
            return communities
        
        results = list(detect_community_events(
            tnet,
            simple_detector,
            window_size=100.0,
            change_threshold=0.3,
        ))
        
        assert len(results) > 0
        
        for t_start, t_end, event_type, change_score in results:
            # Current implementation returns "stable" or "high_change"
            # Future enhancements may add "merge" and "split" detection
            assert event_type in ["stable", "high_change"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
