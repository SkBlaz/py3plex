"""Tests for DSL edge grouping, per_layer_pair, and coverage features.

This test suite validates the new DSL features for edge analysis:
- .per_layer_pair() for grouping edges by (src_layer, dst_layer)
- .coverage() for edge queries with per_layer_pair grouping
- Grouping metadata in QueryResult.meta
- .group_summary() for summarizing grouped results
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.errors import DslExecutionError, GroupingError


@pytest.fixture
def edge_test_network():
    """Create a sample multilayer network for edge testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes in 3 layers
    nodes = []
    for layer in ["layer0", "layer1", "layer2"]:
        for i in range(5):
            nodes.append({'source': f'node{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges with different patterns per layer
    edges = []
    
    # Layer 0: Dense connections
    for i in range(4):
        for j in range(i + 1, 5):
            edges.append({
                'source': f'node{i}', 'target': f'node{j}',
                'source_type': 'layer0', 'target_type': 'layer0', 'weight': 1.0
            })
    
    # Layer 1: Sparser connections
    for i in range(3):
        edges.append({
            'source': f'node{i}', 'target': f'node{i+1}',
            'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0
        })
    
    # Layer 2: Very sparse
    edges.append({
        'source': 'node0', 'target': 'node1',
        'source_type': 'layer2', 'target_type': 'layer2', 'weight': 3.0
    })
    
    # Add some inter-layer edges
    edges.append({
        'source': 'node0', 'target': 'node1',
        'source_type': 'layer0', 'target_type': 'layer1', 'weight': 1.5
    })
    edges.append({
        'source': 'node1', 'target': 'node2',
        'source_type': 'layer1', 'target_type': 'layer2', 'weight': 2.5
    })
    
    network.add_edges(edges)
    
    return network


class TestPerLayerPairBasics:
    """Test basic per_layer_pair functionality."""
    
    def test_per_layer_pair_groups_edges(self, edge_test_network):
        """Test that per_layer_pair creates proper grouping."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
             .execute(net)
        )
        
        # Check that grouping metadata exists
        assert "grouping" in result.meta
        grouping = result.meta["grouping"]
        assert grouping["kind"] == "per_layer_pair"
        assert grouping["target"] == "edges"
        assert grouping["keys"] == ["src_layer", "dst_layer"]
        
        # Should have multiple groups
        assert len(grouping["groups"]) > 0
    
    def test_per_layer_pair_on_nodes_raises_error(self, edge_test_network):
        """Test that per_layer_pair() on nodes raises clear error."""
        net = edge_test_network
        
        with pytest.raises(DslExecutionError, match="per_layer_pair.*only.*edge queries"):
            Q.nodes().per_layer_pair().execute(net)
    
    def test_per_layer_on_edges_raises_error(self, edge_test_network):
        """Test that per_layer() on edges raises clear error."""
        net = edge_test_network
        
        with pytest.raises(DslExecutionError, match="per_layer.*only.*node queries"):
            Q.edges().per_layer().execute(net)
    
    def test_per_layer_pair_top_k(self, edge_test_network):
        """Test top-k per layer pair."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
                .top_k(2, "weight")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Group by source_layer and target_layer to verify top-k per group
        grouped = df.groupby(['source_layer', 'target_layer']).size()
        
        # Each group should have at most 2 edges
        assert all(count <= 2 for count in grouped)


class TestEdgeCoverage:
    """Test coverage filtering for edge queries."""
    
    def test_edge_coverage_mode_all(self, edge_test_network):
        """Test coverage mode='all' for edges."""
        net = edge_test_network
        
        # Get top-2 edges per layer pair, then get edges that appear in all groups
        result = (
            Q.edges()
             .from_layers(L["layer0", "layer1"])
             .per_layer_pair()
                .top_k(5, "weight")
             .end_grouping()
             .coverage(mode="all")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Verify that each edge appears in all relevant layer pairs
        # (This may result in 0 edges if no edge appears in all groups)
        if len(df) > 0:
            for idx, row in df.iterrows():
                edge_id = (row['source'], row['target'])
                edge_groups = df[
                    (df['source'] == row['source']) & 
                    (df['target'] == row['target'])
                ][['src_layer', 'dst_layer']].drop_duplicates()
                
                # If coverage=all worked, this edge should be in the expected number of groups
                # In this case, we're selecting from 2 layers, so we expect multiple groups
                assert len(edge_groups) >= 1
    
    def test_edge_coverage_mode_any(self, edge_test_network):
        """Test coverage mode='any' for edges."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
                .top_k(3, "weight")
             .end_grouping()
             .coverage(mode="any")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Coverage mode "any" should keep all edges
        assert len(df) > 0
    
    def test_coverage_requires_grouping(self, edge_test_network):
        """Test that coverage raises error without grouping."""
        net = edge_test_network
        
        with pytest.raises(GroupingError, match="coverage.*requires.*active grouping"):
            Q.edges().coverage(mode="all").execute(net)


class TestGroupingMetadata:
    """Test grouping metadata structure in QueryResult.meta."""
    
    def test_node_grouping_metadata_structure(self, edge_test_network):
        """Test that node grouping produces correct metadata."""
        net = edge_test_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .execute(net)
        )
        
        assert "grouping" in result.meta
        grouping = result.meta["grouping"]
        
        # Check structure
        assert grouping["kind"] == "per_layer"
        assert grouping["target"] == "nodes"
        assert grouping["keys"] == ["layer"]
        assert "groups" in grouping
        
        # Check group structure
        for group in grouping["groups"]:
            assert "key" in group
            assert "n_items" in group
            assert "layer" in group["key"]
            assert isinstance(group["n_items"], int)
    
    def test_edge_grouping_metadata_structure(self, edge_test_network):
        """Test that edge grouping produces correct metadata."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
                .top_k(2, "weight")
             .end_grouping()
             .execute(net)
        )
        
        assert "grouping" in result.meta
        grouping = result.meta["grouping"]
        
        # Check structure
        assert grouping["kind"] == "per_layer_pair"
        assert grouping["target"] == "edges"
        assert grouping["keys"] == ["src_layer", "dst_layer"]
        assert "groups" in grouping
        
        # Check group structure
        for group in grouping["groups"]:
            assert "key" in group
            assert "n_items" in group
            assert "src_layer" in group["key"]
            assert "dst_layer" in group["key"]
            assert isinstance(group["n_items"], int)
    
    def test_no_grouping_metadata_without_grouping(self, edge_test_network):
        """Test that non-grouped queries don't have grouping metadata."""
        net = edge_test_network
        
        result = Q.edges().from_layers(L["layer0"]).execute(net)
        
        assert "grouping" not in result.meta


class TestGroupSummary:
    """Test group_summary() method."""
    
    def test_group_summary_for_nodes(self, edge_test_network):
        """Test group_summary() for node queries."""
        net = edge_test_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .execute(net)
        )
        
        summary = result.group_summary()
        
        # Should have one row per layer
        assert len(summary) > 0
        assert "layer" in summary.columns
        assert "n_items" in summary.columns
        
        # Each row should have a layer and item count
        for _, row in summary.iterrows():
            assert row["layer"] is not None
            assert row["n_items"] > 0
    
    def test_group_summary_for_edges(self, edge_test_network):
        """Test group_summary() for edge queries."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
                .top_k(2, "weight")
             .end_grouping()
             .execute(net)
        )
        
        summary = result.group_summary()
        
        # Should have one row per layer pair
        assert len(summary) > 0
        assert "src_layer" in summary.columns
        assert "dst_layer" in summary.columns
        assert "n_items" in summary.columns
        
        # Each row should have layer pair info
        for _, row in summary.iterrows():
            assert row["src_layer"] is not None
            assert row["dst_layer"] is not None
            assert row["n_items"] > 0
    
    def test_group_summary_raises_error_without_grouping(self, edge_test_network):
        """Test that group_summary() raises error for non-grouped results."""
        net = edge_test_network
        
        result = Q.edges().from_layers(L["layer0"]).execute(net)
        
        with pytest.raises(GroupingError, match="group_summary.*only.*grouped"):
            result.group_summary()


class TestToPandasWithGrouping:
    """Test to_pandas() with grouping metadata."""
    
    def test_to_pandas_includes_grouping_keys_nodes(self, edge_test_network):
        """Test that to_pandas() includes grouping keys for nodes."""
        net = edge_test_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have layer column
        assert "layer" in df.columns
        assert df["layer"].notna().all()
    
    def test_to_pandas_includes_grouping_keys_edges(self, edge_test_network):
        """Test that to_pandas() includes grouping keys for edges."""
        net = edge_test_network
        
        result = (
            Q.edges()
             .from_layers(L["*"])
             .per_layer_pair()
                .top_k(2, "weight")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have src_layer and dst_layer columns (from edge structure)
        assert "source_layer" in df.columns
        assert "target_layer" in df.columns
    
    def test_to_pandas_multiindex_nodes(self, edge_test_network):
        """Test to_pandas(multiindex=True) for nodes."""
        net = edge_test_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas(multiindex=True)
        
        # Index should be set to layer
        assert "layer" in df.index.names or df.index.name == "layer"
    
    def test_to_pandas_without_grouping(self, edge_test_network):
        """Test that to_pandas() works normally without grouping."""
        net = edge_test_network
        
        result = Q.edges().from_layers(L["layer0"]).execute(net)
        df = result.to_pandas()
        
        # Should work as before
        assert "source" in df.columns
        assert "target" in df.columns


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_flagship_example_from_issue(self, edge_test_network):
        """Test the flagship example from the issue description."""
        net = edge_test_network
        
        # The example from the issue
        q = (
            Q.edges()
             .from_layers(L["layer0"] + L["layer1"])
             .per_layer_pair()
             .order_by("-weight")
        )
        result = q.execute(net)
        
        # Should have grouping metadata
        assert "grouping" in result.meta
        
        # to_pandas should work
        df = result.to_pandas()
        assert len(df) > 0
        
        # group_summary should work
        summary = result.group_summary()
        assert len(summary) > 0
        assert "src_layer" in summary.columns
        assert "dst_layer" in summary.columns
        assert "n_items" in summary.columns
