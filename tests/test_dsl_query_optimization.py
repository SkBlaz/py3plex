"""Tests for DSL query optimization features.

Tests cover:
- Early LIMIT optimization when ORDER BY uses existing attributes
- Performance improvements from query reordering
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L


@pytest.fixture
def large_network():
    """Create a larger multilayer network for optimization testing."""
    network = multinet.multi_layer_network(directed=False)

    # Create multiple layers with many nodes
    layers = ['social', 'work', 'hobby']
    nodes_per_layer = 50
    
    nodes = []
    for layer in layers:
        for i in range(nodes_per_layer):
            nodes.append({'source': f'Node{i}', 'type': layer})
    network.add_nodes(nodes)

    # Add edges to create degree distribution
    edges = []
    for layer in layers:
        # Create a small-world-like structure
        for i in range(nodes_per_layer - 1):
            # Connect to next node (ring)
            edges.append({
                'source': f'Node{i}',
                'target': f'Node{i+1}',
                'source_type': layer,
                'target_type': layer,
                'weight': 1.0
            })
        # Close the ring
        edges.append({
            'source': f'Node{nodes_per_layer-1}',
            'target': 'Node0',
            'source_type': layer,
            'target_type': layer,
            'weight': 1.0
        })
        
        # Add some high-degree hubs
        for i in range(0, nodes_per_layer, 10):
            for j in range(i + 1, min(i + 5, nodes_per_layer)):
                edges.append({
                    'source': f'Node{i}',
                    'target': f'Node{j}',
                    'source_type': layer,
                    'target_type': layer,
                    'weight': 1.0
                })
    
    network.add_edges(edges)
    return network


class TestQueryOptimization:
    """Test query optimization strategies."""

    def test_early_limit_with_degree_ordering(self, large_network):
        """Test early LIMIT when ordering by existing degree attribute."""
        # Query: Get top 10 nodes by degree, then compute betweenness
        # Optimization should apply LIMIT before computing betweenness
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality")
             .order_by("-degree")
             .limit(10)
             .execute(large_network)
        )
        
        # Should return exactly 10 nodes
        assert len(result.items) == 10
        
        # Betweenness should be computed ONLY on the 10 nodes (optimization!)
        # because we can order by degree (already available) before computing
        assert "betweenness_centrality" in result.attributes
        assert len(result.attributes["betweenness_centrality"]) == 10  # Only 10, not 50!
    
    def test_no_early_limit_when_ordering_by_computed_attr(self, large_network):
        """Test that early LIMIT is NOT applied when ordering by computed attribute."""
        # Query: Order by betweenness (computed), take top 10
        # Optimization should NOT apply because we need to compute betweenness
        # on all nodes to know which are top 10
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality")
             .order_by("-betweenness_centrality")
             .limit(10)
             .execute(large_network)
        )
        
        # Should still return exactly 10 nodes
        assert len(result.items) == 10
        
        # Betweenness should be computed on ALL social nodes (not just top 10)
        # because we need to compute it to know which are top 10
        assert "betweenness_centrality" in result.attributes
        # Note: attributes dict contains values for all nodes that were computed,
        # but the result items list only contains the limited items
        # This is expected behavior - we computed on 50 nodes to find top 10
        assert len(result.attributes["betweenness_centrality"]) == 50
    
    def test_early_limit_with_layer_ordering(self, large_network):
        """Test early LIMIT when ordering by layer attribute."""
        # Query: Order by layer (always available), limit, then compute
        result = (
            Q.nodes()
             .compute("betweenness_centrality")
             .order_by("layer")
             .limit(20)
             .execute(large_network)
        )
        
        # Should return exactly 20 nodes
        assert len(result.items) == 20
        
        # All items should have betweenness computed
        assert "betweenness_centrality" in result.attributes
        assert len(result.attributes["betweenness_centrality"]) == 20
    
    def test_no_early_limit_without_order_by(self, large_network):
        """Test that early LIMIT is NOT applied without ORDER BY."""
        # Query: Just limit without ordering
        # Optimization should NOT apply (arbitrary which items are kept)
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality")
             .limit(15)
             .execute(large_network)
        )
        
        # Should return exactly 15 nodes
        assert len(result.items) == 15
        
        # Betweenness is computed on ALL social nodes (50), not just 15
        # because without ORDER BY, we don't know which 15 to compute on first
        assert "betweenness_centrality" in result.attributes
        assert len(result.attributes["betweenness_centrality"]) == 50
    
    def test_no_early_limit_with_grouping(self, large_network):
        """Test that early LIMIT is NOT applied when grouping is active."""
        # Query: Group by layer, order, limit per group
        # Early LIMIT optimization should NOT apply (per-group limit is different)
        result = (
            Q.nodes()
             .per_layer()
             .top_k(5, "degree")
             .end_grouping()
             .compute("betweenness_centrality")
             .execute(large_network)
        )
        
        # Should have results from multiple layers (up to 5 per layer)
        assert len(result.items) > 5  # More than one layer's worth
        
        # All items should have betweenness computed
        assert "betweenness_centrality" in result.attributes
    
    def test_optimization_correctness_with_where_clause(self, large_network):
        """Test that optimization works correctly with WHERE clause."""
        # Query: Filter, order by degree, limit, compute
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=1)  # Filter first
             .compute("betweenness_centrality")
             .order_by("-degree")
             .limit(10)
             .execute(large_network)
        )
        
        # Should return up to 10 nodes (might be fewer if filter is very restrictive)
        assert len(result.items) <= 10
        
        # All items should have betweenness computed
        if len(result.items) > 0:
            assert "betweenness_centrality" in result.attributes
            assert len(result.attributes["betweenness_centrality"]) == len(result.items)
    
    def test_multiple_computed_attributes_with_optimization(self, large_network):
        """Test optimization with multiple computed attributes."""
        # Query: Order by degree, limit, then compute multiple measures
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality", "clustering")
             .order_by("-degree")
             .limit(10)
             .execute(large_network)
        )
        
        # Should return exactly 10 nodes
        assert len(result.items) == 10
        
        # Both measures should be computed
        assert "betweenness_centrality" in result.attributes
        assert "clustering" in result.attributes
        assert len(result.attributes["betweenness_centrality"]) == 10
        assert len(result.attributes["clustering"]) == 10


class TestQueryOptimizationEdgeCases:
    """Test edge cases for query optimization."""
    
    def test_empty_network_with_optimization(self):
        """Test that optimization works with empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        result = (
            Q.nodes()
             .compute("betweenness_centrality")
             .order_by("-degree")
             .limit(10)
             .execute(network)
        )
        
        assert len(result.items) == 0
    
    def test_limit_larger_than_items(self, large_network):
        """Test that optimization works when limit > number of items."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .compute("betweenness_centrality")
             .order_by("-degree")
             .limit(1000)  # More than we have
             .execute(large_network)
        )
        
        # Should return all social layer nodes
        assert len(result.items) <= 1000
        assert "betweenness_centrality" in result.attributes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
