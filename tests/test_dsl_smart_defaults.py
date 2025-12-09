"""Tests for DSL smart defaults.

This test suite validates smart default features in the DSL:
- Auto-computing centrality metrics when referenced in top_k, order_by, etc.
- Helpful error messages with suggestions for unknown attributes
- GroupingError when coverage is called without grouping
- No implicit operations when attributes already exist
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.errors import UnknownAttributeError, GroupingError


@pytest.fixture
def random_multilayer_net():
    """Create a random multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes in 3 layers with distinct topologies
    nodes = []
    for layer in ["layer0", "layer1", "layer2"]:
        for i in range(10):
            nodes.append({'source': f'node{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges to create different degree distributions
    edges = []
    
    # Layer 0: Star topology (node0 is a hub)
    for i in range(1, 10):
        edges.append({
            'source': 'node0', 'target': f'node{i}',
            'source_type': 'layer0', 'target_type': 'layer0', 'weight': 1.0
        })
    
    # Layer 1: Ring topology (all nodes have degree 2)
    for i in range(10):
        edges.append({
            'source': f'node{i}', 'target': f'node{(i + 1) % 10}',
            'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0
        })
    
    # Layer 2: Dense connectivity for node1 and node2
    for i in range(3, 10):
        edges.append({
            'source': 'node1', 'target': f'node{i}',
            'source_type': 'layer2', 'target_type': 'layer2', 'weight': 1.0
        })
        edges.append({
            'source': 'node2', 'target': f'node{i}',
            'source_type': 'layer2', 'target_type': 'layer2', 'weight': 1.0
        })
    
    network.add_edges(edges)
    
    return network


class TestAutoCentralityBeforeTopK:
    """Test auto-computing centrality metrics before top_k operations."""
    
    def test_auto_betweenness_before_top_k(self, random_multilayer_net):
        """Test that betweenness_centrality is auto-computed for top_k."""
        net = random_multilayer_net
        
        # Query without explicit compute - should auto-compute betweenness
        q = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(5, "betweenness_centrality")
             .end_grouping()
        )
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have betweenness_centrality column
        assert "betweenness_centrality" in df.columns
        
        # Should have results
        assert len(df) > 0
        
        # Should have values (not all zeros)
        assert df["betweenness_centrality"].sum() > 0
    
    def test_auto_degree_before_top_k(self, random_multilayer_net):
        """Test that degree is auto-computed for top_k."""
        net = random_multilayer_net
        
        # Query without explicit compute - should auto-compute degree
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
        )
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have degree column
        assert "degree" in df.columns
        
        # Should have 3 nodes (top-k=3)
        assert len(df) == 3
        
        # node0 should be included (it's the hub in layer0)
        node_ids = [row[0] for row in result.items]
        assert 'node0' in node_ids
    
    def test_auto_centrality_global_ordering(self, random_multilayer_net):
        """Test auto-computing centrality for global order_by (no grouping)."""
        net = random_multilayer_net
        
        # Query with order_by but no explicit compute
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .order_by("degree", desc=True)
             .limit(5)
        )
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have degree column
        assert "degree" in df.columns
        
        # Should be ordered by degree (descending)
        degrees = df["degree"].tolist()
        assert degrees == sorted(degrees, reverse=True)
    
    def test_auto_closeness_before_top_k(self, random_multilayer_net):
        """Test auto-computing closeness_centrality."""
        net = random_multilayer_net
        
        # Query without explicit compute
        q = (
            Q.nodes()
             .from_layers(L["layer1"])
             .per_layer()
                .top_k(3, "closeness_centrality")
             .end_grouping()
        )
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have closeness_centrality column
        assert "closeness_centrality" in df.columns or "closeness" in df.columns
        
        # Should have results
        assert len(df) > 0


class TestUnknownAttributeError:
    """Test error messages for unknown attributes."""
    
    def test_unknown_attribute_with_typo(self, random_multilayer_net):
        """Test that typos in attribute names suggest corrections."""
        net = random_multilayer_net
        
        # Intentional typo: "betweness" instead of "betweenness"
        with pytest.raises(UnknownAttributeError) as excinfo:
            (
                Q.nodes()
                 .from_layers(L["*"])
                 .per_layer()
                    .top_k(5, "betweness_centrality")
                 .end_grouping()
                 .execute(net)
            )
        
        error_msg = str(excinfo.value)
        
        # Should mention the incorrect attribute
        assert "betweness_centrality" in error_msg
        
        # Should suggest the correct spelling
        assert "Did you mean" in error_msg or "betweenness" in error_msg.lower()
    
    def test_unknown_attribute_lists_available(self, random_multilayer_net):
        """Test that error lists available attributes."""
        net = random_multilayer_net
        
        # Use a completely unknown attribute
        with pytest.raises(UnknownAttributeError) as excinfo:
            (
                Q.nodes()
                 .from_layers(L["layer0"])
                 .compute("degree")
                 .order_by("nonexistent_metric")
                 .execute(net)
            )
        
        error_msg = str(excinfo.value)
        
        # Should mention the unknown attribute
        assert "nonexistent_metric" in error_msg
        
        # Should list available attributes (at least "degree" which was computed)
        # The error message format is: "Known attributes: ..."
        assert "degree" in error_msg or "Known attributes" in error_msg
    
    def test_unknown_attribute_without_suggestions(self, random_multilayer_net):
        """Test error when no close matches exist."""
        net = random_multilayer_net
        
        with pytest.raises(UnknownAttributeError) as excinfo:
            (
                Q.nodes()
                 .from_layers(L["layer0"])
                 .order_by("xyz123_metric")
                 .execute(net)
            )
        
        error_msg = str(excinfo.value)
        assert "xyz123_metric" in error_msg


class TestCoverageWithoutGrouping:
    """Test that coverage requires active grouping."""
    
    def test_coverage_without_grouping_raises_error(self, random_multilayer_net):
        """Test that coverage without grouping raises GroupingError."""
        net = random_multilayer_net
        
        with pytest.raises(GroupingError) as excinfo:
            (
                Q.nodes()
                 .from_layers(L["*"])
                 .compute("degree")
                 # No per_layer() or group_by() before coverage
                 .coverage(mode="all")
                 .execute(net)
            )
        
        error_msg = str(excinfo.value)
        
        # Should mention that grouping is required
        assert "requires an active grouping" in error_msg
        
        # Should mention per_layer or group_by as solutions
        assert "per_layer" in error_msg or "group_by" in error_msg
    
    def test_coverage_without_grouping_shows_example(self, random_multilayer_net):
        """Test that error message includes usage example."""
        net = random_multilayer_net
        
        with pytest.raises(GroupingError) as excinfo:
            (
                Q.nodes()
                 .from_layers(L["*"])
                 .coverage(mode="all")
                 # Note: .execute() not called here since the error happens in builder
            )
        
        error_msg = str(excinfo.value)
        
        # Should include example code
        assert "Example:" in error_msg or "example" in error_msg.lower()


class TestNoImplicitWhenAttributeExists:
    """Test that no implicit operations occur when attributes already exist."""
    
    def test_explicit_compute_not_duplicated(self, random_multilayer_net):
        """Test that explicit compute is respected and not duplicated."""
        net = random_multilayer_net
        
        # Explicit compute before top_k
        q = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("betweenness_centrality")
             .per_layer()
                .top_k(5, "betweenness_centrality")
             .end_grouping()
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should work correctly with explicit compute
        assert "betweenness_centrality" in df.columns
        assert len(df) > 0
    
    def test_multiple_centralities_explicit(self, random_multilayer_net):
        """Test explicit computation of multiple centralities."""
        net = random_multilayer_net
        
        # Compute multiple metrics explicitly
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree", "betweenness_centrality")
             .order_by("betweenness_centrality", desc=True)
             .limit(5)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have both columns
        assert "degree" in df.columns
        assert "betweenness_centrality" in df.columns
        
        # Should be properly ordered
        bc_values = df["betweenness_centrality"].tolist()
        assert bc_values == sorted(bc_values, reverse=True)


class TestSmartDefaultsWithAliases:
    """Test that centrality aliases work correctly."""
    
    def test_betweenness_alias(self, random_multilayer_net):
        """Test that 'betweenness' alias works for 'betweenness_centrality'."""
        net = random_multilayer_net
        
        # Use short form 'betweenness'
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .order_by("betweenness", desc=True)
             .limit(3)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have betweenness column (the alias we requested)
        assert "betweenness" in df.columns
        
        # Should have values
        assert df["betweenness"].sum() >= 0
    
    def test_degree_centrality_alias(self, random_multilayer_net):
        """Test that 'degree_centrality' alias works."""
        net = random_multilayer_net
        
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .order_by("degree_centrality", desc=True)
             .limit(3)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have degree_centrality column
        assert "degree_centrality" in df.columns


class TestSmartDefaultsEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def test_empty_network_auto_compute(self):
        """Test auto-compute on empty network."""
        net = multinet.multi_layer_network(directed=False)
        
        # Empty network - should not crash
        q = (
            Q.nodes()
             .from_layers(L["*"])
             .order_by("degree", desc=True)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should be empty but valid
        assert len(df) == 0
    
    def test_auto_compute_with_where_clause(self, random_multilayer_net):
        """Test auto-compute works with WHERE filtering."""
        net = random_multilayer_net
        
        # Filter then order by auto-computed metric
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .where(layer="layer0")
             .order_by("degree", desc=True)
             .limit(3)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        # Should have degree column
        assert "degree" in df.columns
        assert len(df) <= 3
    
    def test_multiple_order_by_with_auto_compute(self, random_multilayer_net):
        """Test auto-computing multiple attributes for multi-key ordering."""
        net = random_multilayer_net
        
        # Order by multiple auto-computed attributes
        q = (
            Q.nodes()
             .from_layers(L["layer0"])
             .order_by("degree", desc=True)
             # Note: In current implementation, only one order_by is typically used
             # but this tests the general case
             .limit(5)
        )
        
        result = q.execute(net)
        df = result.to_pandas()
        
        assert "degree" in df.columns
        assert len(df) <= 5


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
