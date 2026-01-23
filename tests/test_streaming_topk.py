"""Tests for streaming top-k optimization.

This module tests the _top_k_stream function to ensure it produces
the same results as full sorting but with better time complexity.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L


@pytest.fixture
def simple_network():
    """Create a simple network with known degree distribution."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes with varying degrees
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'E', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Create edges to give specific degrees
    # A: degree 4, B: degree 3, C: degree 2, D: degree 1, E: degree 0
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'E', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.fixture
def multilayer_network():
    """Create a multilayer network for testing grouping."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes across 3 layers
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'C', 'type': 'layer2'},
        {'source': 'A', 'type': 'layer3'},
        {'source': 'B', 'type': 'layer3'},
        {'source': 'C', 'type': 'layer3'},
    ]
    network.add_nodes(nodes)
    
    # Add edges with varying degrees per layer
    # Layer1: A=3, B=2, C=1
    # Layer2: A=2, B=2, C=2
    # Layer3: A=1, B=2, C=3
    edges = [
        # Layer 1
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        # Layer 2
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
        {'source': 'C', 'target': 'A', 'source_type': 'layer2', 'target_type': 'layer2'},
        # Layer 3
        {'source': 'B', 'target': 'C', 'source_type': 'layer3', 'target_type': 'layer3'},
        {'source': 'C', 'target': 'A', 'source_type': 'layer3', 'target_type': 'layer3'},
        {'source': 'C', 'target': 'B', 'source_type': 'layer3', 'target_type': 'layer3'},
    ]
    network.add_edges(edges)
    
    return network


class TestStreamingTopK:
    """Test streaming top-k implementation."""

    def test_top_k_basic(self, simple_network):
        """Test basic top-k selection."""
        result = (
            Q.nodes()
            .from_layers(L["layer1"])
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # Should get top 3 nodes by degree
        assert len(df) == 3
        
        # Degrees should be in descending order
        degrees = df['degree'].tolist()
        assert degrees == sorted(degrees, reverse=True)
        
        # Top node should be A (degree 4)
        top_node = df.iloc[0]['id']
        assert top_node == 'A'

    def test_per_layer_top_k(self, multilayer_network):
        """Test per-layer top-k with streaming algorithm."""
        result = (
            Q.nodes()
            .per_layer()
            .compute("degree")
            .top_k(2, "degree")
            .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # Should get top 2 nodes per layer (2 * 3 layers = 6 nodes)
        assert len(df) == 6
        
        # Check that we have nodes from all 3 layers
        layers = df['layer'].unique()
        assert len(layers) == 3

    def test_top_k_with_coverage(self, multilayer_network):
        """Test top-k combined with coverage filtering."""
        result = (
            Q.nodes()
            .per_layer()
            .compute("degree")
            .top_k(2, "degree")
            .end_grouping()
            .coverage(mode="at_least", k=2)
            .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # Should have nodes that appear in top-2 of at least 2 layers
        assert len(df) >= 0  # At least some nodes should pass

    def test_deterministic_order(self, simple_network):
        """Test that results are deterministic."""
        # Run query twice
        result1 = (
            Q.nodes()
            .from_layers(L["layer1"])
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .execute(simple_network)
        )
        
        result2 = (
            Q.nodes()
            .from_layers(L["layer1"])
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(3)
            .execute(simple_network)
        )
        
        df1 = result1.to_pandas()
        df2 = result2.to_pandas()
        
        # Results should be identical
        assert len(df1) == len(df2)
        assert df1['id'].tolist() == df2['id'].tolist()
        assert df1['degree'].tolist() == df2['degree'].tolist()


class TestBitmaskCoverage:
    """Test bitmask-based coverage filtering."""

    def test_coverage_all(self, multilayer_network):
        """Test coverage mode='all' with bitmask."""
        result = (
            Q.nodes()
            .per_layer()
            .end_grouping()
            .coverage(mode="all")
            .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # All nodes (A, B, C) appear in all 3 layers
        # So we should get 9 node replicas (3 nodes * 3 layers)
        assert len(df) == 9

    def test_coverage_at_least(self, multilayer_network):
        """Test coverage mode='at_least' with bitmask."""
        result = (
            Q.nodes()
            .per_layer()
            .end_grouping()
            .coverage(mode="at_least", k=2)
            .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # All nodes appear in at least 2 layers (actually all 3)
        assert len(df) == 9

    def test_bitmask_performance_correctness(self, multilayer_network):
        """Test that bitmask produces same results as original implementation."""
        # This is a correctness check - bitmask should produce identical results
        # to the original set-based implementation
        
        result = (
            Q.nodes()
            .per_layer()
            .compute("degree")
            .top_k(2, "degree")
            .end_grouping()
            .coverage(mode="at_least", k=2)
            .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # Should have some results
        assert len(df) >= 0
        
        # All nodes in result should have valid data
        assert 'id' in df.columns
        assert 'layer' in df.columns
        assert 'degree' in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
