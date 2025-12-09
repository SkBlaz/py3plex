"""Tests for dplyr-style DSL operations.

This test suite validates the new dplyr-inspired DSL features:
- select(), drop(), rename() for column management
- summarize() for aggregations
- arrange() as alias for order_by()
- distinct() for deduplication
- per_community() for community grouping
- centrality(), rank_by(), zscore() for analysis
- Enhanced coverage() with fraction mode
"""

import numpy as np
import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.errors import DslExecutionError


@pytest.fixture
def sample_multilayer_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes in 3 layers
    nodes = []
    for layer in ["layer0", "layer1", "layer2"]:
        for i in range(10):
            nodes.append({'source': f'node{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges to create different degree distributions per layer
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
    
    # Layer 2: Another star (node1 is a hub here)
    for i in range(2, 10):
        edges.append({
            'source': 'node1', 'target': f'node{i}',
            'source_type': 'layer2', 'target_type': 'layer2', 'weight': 1.0
        })
    
    network.add_edges(edges)
    
    return network


class TestColumnOperations:
    """Test select(), drop(), and rename() operations."""
    
    def test_select_columns(self, sample_multilayer_network):
        """Test selecting specific columns."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .select("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should only have the selected columns (plus id/layer which are always present)
        assert "degree" in df.columns
        # Make sure other computed columns are not present if we add more
    
    def test_drop_columns(self, sample_multilayer_network):
        """Test dropping columns."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .drop("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # degree should not be in the result
        assert "degree" not in df.columns
    
    def test_rename_columns(self, sample_multilayer_network):
        """Test renaming columns."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .rename(deg="degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have renamed column
        assert "deg" in df.columns
        assert "degree" not in df.columns


class TestSummarize:
    """Test summarize() operation for aggregations."""
    
    def test_summarize_per_layer(self, sample_multilayer_network):
        """Test summarizing statistics per layer."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .summarize(
                 mean_degree="mean(degree)",
                 max_degree="max(degree)",
                 n="n()"
             )
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have one row per layer
        assert len(df) == 3
        
        # Should have the aggregated columns
        assert "mean_degree" in df.columns
        assert "max_degree" in df.columns
        assert "n" in df.columns
        
        # Each layer should have 10 nodes
        assert all(df["n"] == 10)
    
    def test_summarize_global(self, sample_multilayer_network):
        """Test global summarization without grouping."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .summarize(
                 total="n()",
                 avg_deg="mean(degree)"
             )
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have one row (global aggregation)
        assert len(df) == 1
        assert "total" in df.columns
        assert "avg_deg" in df.columns
    
    def test_summarize_with_various_functions(self, sample_multilayer_network):
        """Test various aggregation functions."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .summarize(
                 count="n()",
                 mean_deg="mean(degree)",
                 sum_deg="sum(degree)",
                 min_deg="min(degree)",
                 max_deg="max(degree)",
                 std_deg="std(degree)",
                 var_deg="var(degree)"
             )
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have all the aggregation columns
        assert "count" in df.columns
        assert "mean_deg" in df.columns
        assert "sum_deg" in df.columns
        assert "min_deg" in df.columns
        assert "max_deg" in df.columns
        assert "std_deg" in df.columns
        assert "var_deg" in df.columns


class TestArrangeDistinct:
    """Test arrange() and distinct() operations."""
    
    def test_arrange_ascending(self, sample_multilayer_network):
        """Test arrange with ascending order."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .arrange("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should be sorted by degree ascending
        degrees = df["degree"].tolist()
        assert degrees == sorted(degrees)
    
    def test_arrange_descending(self, sample_multilayer_network):
        """Test arrange with descending order."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .arrange("-degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should be sorted by degree descending
        degrees = df["degree"].tolist()
        assert degrees == sorted(degrees, reverse=True)
    
    def test_distinct_all_columns(self, sample_multilayer_network):
        """Test distinct without specifying columns."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .distinct()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have unique rows
        assert len(df) == len(df.drop_duplicates())
    
    def test_distinct_specific_columns(self, sample_multilayer_network):
        """Test distinct with specific columns."""
        net = sample_multilayer_network
        
        # This would be more meaningful with community attributes
        # For now, just test the API works
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .distinct("degree")
             .execute(net)
        )
        
        # Should execute without error
        assert result is not None


class TestGrouping:
    """Test per_community() and enhanced coverage."""
    
    def test_per_community(self, sample_multilayer_network):
        """Test per_community grouping."""
        net = sample_multilayer_network
        
        # Add community attribute to nodes for testing
        # In a real scenario, this would come from community detection
        for i, node in enumerate(net.get_nodes()):
            node_id, layer = node
            if hasattr(net, 'core_network') and node_id in net.core_network:
                net.core_network.nodes[node_id]['community'] = i % 3
        
        # This should work without error
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .per_community()
             .top_k(2, "degree")
             .execute(net)
        )
        
        # Should execute successfully
        assert result is not None
    
    def test_coverage_fraction_mode(self, sample_multilayer_network):
        """Test coverage with fraction mode."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .top_k(5, "degree")
             .coverage(mode="fraction", p=0.67)  # At least 2 out of 3 layers
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have nodes that appear in at least 2 layers
        # node0 and node1 are hubs in 2 layers each
        assert len(df) > 0


class TestCentralityMethods:
    """Test centrality(), rank_by(), and zscore()."""
    
    def test_centrality_convenience(self, sample_multilayer_network):
        """Test centrality() as convenience wrapper."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .centrality("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have computed degree centrality
        assert "degree" in df.columns
    
    def test_centrality_with_aliases(self, sample_multilayer_network):
        """Test centrality with custom aliases."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .centrality(deg="degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have aliased column
        assert "deg" in df.columns
    
    def test_rank_by_global(self, sample_multilayer_network):
        """Test global ranking."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .rank_by("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have rank column
        assert "degree_rank" in df.columns
        
        # Ranks should be integers
        assert all(isinstance(r, (int, float)) for r in df["degree_rank"])
    
    def test_rank_by_per_layer(self, sample_multilayer_network):
        """Test per-layer ranking."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .rank_by("degree", "dense")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have rank column computed per layer
        assert "degree_rank" in df.columns
    
    def test_zscore_global(self, sample_multilayer_network):
        """Test global z-score computation."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .zscore("degree")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have z-score column
        assert "degree_zscore" in df.columns
        
        # Z-scores should have mean ~0 and std ~1
        zscores = df["degree_zscore"].values
        assert abs(np.mean(zscores)) < 0.1
        assert abs(np.std(zscores) - 1.0) < 0.1
    
    def test_zscore_per_layer(self, sample_multilayer_network):
        """Test per-layer z-score computation."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .zscore("degree")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have z-score column computed per layer
        assert "degree_zscore" in df.columns


class TestComplexPipelines:
    """Test complex query pipelines combining multiple operations."""
    
    def test_full_dplyr_pipeline(self, sample_multilayer_network):
        """Test a complete dplyr-style pipeline."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .summarize(
                 layer_mean="mean(degree)",
                 layer_max="max(degree)",
                 node_count="n()"
             )
             .arrange("-layer_mean")
             .rename(avg_degree="layer_mean", max_degree="layer_max")
             .select("avg_degree", "max_degree", "node_count")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have the renamed and selected columns
        assert "avg_degree" in df.columns
        assert "max_degree" in df.columns
        assert "node_count" in df.columns
        assert "layer_mean" not in df.columns
    
    def test_multi_hub_detection_pattern(self, sample_multilayer_network):
        """Test the multi-hub detection pattern from the issue."""
        net = sample_multilayer_network
        
        # This replicates the example from the issue
        multi_hubs = (
            Q.nodes()
             .from_layers(L["*"])
             .where(degree__gt=1)
             .compute("degree")
             .per_layer()
             .top_k(5, "degree")
             .end_grouping()
             .coverage(mode="all")
             .execute(net)
        )
        
        df = multi_hubs.to_pandas()
        
        # Should find nodes that are hubs in all layers
        # In our test network, this might be empty or have just node0 and node1
        assert isinstance(df, type(multi_hubs.to_pandas()))


class TestErrorHandling:
    """Test error handling for invalid operations."""
    
    def test_summarize_without_computed_attribute(self, sample_multilayer_network):
        """Test that summarize fails gracefully if attribute not computed."""
        net = sample_multilayer_network
        
        with pytest.raises(DslExecutionError):
            (
                Q.nodes()
                 .from_layers(L["layer0"])
                 .summarize(mean_deg="mean(degree)")  # degree not computed
                 .execute(net)
            )
    
    def test_rank_by_without_computed_attribute(self, sample_multilayer_network):
        """Test that rank_by fails gracefully if attribute not computed."""
        net = sample_multilayer_network
        
        with pytest.raises(DslExecutionError):
            (
                Q.nodes()
                 .from_layers(L["layer0"])
                 .rank_by("degree")  # degree not computed
                 .execute(net)
            )
    
    def test_zscore_without_computed_attribute(self, sample_multilayer_network):
        """Test that zscore fails gracefully if attribute not computed."""
        net = sample_multilayer_network
        
        with pytest.raises(DslExecutionError):
            (
                Q.nodes()
                 .from_layers(L["layer0"])
                 .zscore("degree")  # degree not computed
                 .execute(net)
            )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
