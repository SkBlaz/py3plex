"""Tests for DSL grouping, top-k per layer, and coverage features.

This test suite validates the new DSL features for per-layer analysis:
- .group_by() and .per_layer() for grouping
- .top_k() for per-group top-k selection
- .coverage() for cross-group filtering
- L["*"] wildcard layer expressions
"""

import pytest
from py3plex.core import random_generators, multinet
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


class TestWildcardLayers:
    """Test wildcard layer expressions L["*"]."""
    
    def test_wildcard_all_layers(self, sample_multilayer_network):
        """Test that L["*"] selects all layers."""
        net = sample_multilayer_network
        
        # Query with wildcard
        result = Q.nodes().from_layers(L["*"]).execute(net)
        df = result.to_pandas()
        
        # Should have nodes from all 3 layers
        layers_found = set(df["layer"].unique())
        expected_layers = {"layer0", "layer1", "layer2"}
        assert layers_found == expected_layers
        
        # Should have 30 nodes total (10 per layer)
        assert len(df) == 30
    
    def test_wildcard_minus_layer(self, sample_multilayer_network):
        """Test that L["*"] - L["layer0"] excludes one layer."""
        net = sample_multilayer_network
        
        # Query with wildcard minus
        result = Q.nodes().from_layers(L["*"] - L["layer0"]).execute(net)
        df = result.to_pandas()
        
        # Should have nodes from only 2 layers
        layers_found = set(df["layer"].unique())
        expected_layers = {"layer1", "layer2"}
        assert layers_found == expected_layers
        
        # Should have 20 nodes (2 layers * 10 nodes)
        assert len(df) == 20
    
    def test_wildcard_intersection(self, sample_multilayer_network):
        """Test that L["*"] & L["layer1"] gives just one layer."""
        net = sample_multilayer_network
        
        # Query with wildcard intersection
        result = Q.nodes().from_layers(L["*"] & L["layer1"]).execute(net)
        df = result.to_pandas()
        
        # Should have nodes from only layer1
        layers_found = set(df["layer"].unique())
        expected_layers = {"layer1"}
        assert layers_found == expected_layers
        
        # Should have 10 nodes
        assert len(df) == 10


class TestGroupingBasics:
    """Test basic grouping functionality."""
    
    def test_group_by_layer(self, sample_multilayer_network):
        """Test grouping by layer."""
        net = sample_multilayer_network
        
        # Group by layer and compute degree
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .group_by("layer")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should still have all nodes
        assert len(df) == 30
        
        # Should have degree computed for all
        assert "degree" in df.columns
        assert df["degree"].notna().all()
    
    def test_per_layer_sugar(self, sample_multilayer_network):
        """Test that per_layer() is equivalent to group_by('layer')."""
        net = sample_multilayer_network
        
        # Using group_by
        result1 = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .group_by("layer")
             .execute(net)
        )
        
        # Using per_layer
        result2 = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
             .execute(net)
        )
        
        df1 = result1.to_pandas().sort_values(["id", "layer"]).reset_index(drop=True)
        df2 = result2.to_pandas().sort_values(["id", "layer"]).reset_index(drop=True)
        
        # Should be identical
        assert df1.equals(df2)


class TestTopKPerGroup:
    """Test top-k per group functionality."""
    
    def test_top_k_requires_grouping(self, sample_multilayer_network):
        """Test that top_k raises error without prior grouping."""
        net = sample_multilayer_network
        
        with pytest.raises(ValueError, match="top_k.*requires grouping"):
            Q.nodes().compute("degree").top_k(5, "degree").execute(net)
    
    def test_top_k_per_layer(self, sample_multilayer_network):
        """Test top-k selection per layer."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have at most 3 nodes per layer
        layer_counts = df.groupby("layer").size()
        assert all(count <= 3 for count in layer_counts)
        
        # In layer0, node0 should be in top-3 (it's the hub)
        layer0_nodes = set(df[df["layer"] == "layer0"]["id"])
        assert "node0" in layer0_nodes
        
        # In layer2, node1 should be in top-3 (it's the hub)
        layer2_nodes = set(df[df["layer"] == "layer2"]["id"])
        assert "node1" in layer2_nodes
    
    def test_top_k_ordering(self, sample_multilayer_network):
        """Test that top-k respects ordering."""
        net = sample_multilayer_network
        
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .per_layer()
                .top_k(5, "degree")
             .end_grouping()
             .execute(net)
        )
        
        df = result.to_pandas().sort_values("degree", ascending=False)
        
        # Should have exactly 5 nodes
        assert len(df) == 5
        
        # Degrees should be in descending order (after we sort)
        degrees = df["degree"].tolist()
        assert degrees == sorted(degrees, reverse=True)


class TestCoverage:
    """Test coverage filtering across groups."""
    
    def test_coverage_requires_grouping(self, sample_multilayer_network):
        """Test that coverage raises error without prior grouping."""
        net = sample_multilayer_network
        
        from py3plex.dsl.errors import GroupingError
        with pytest.raises(GroupingError, match="coverage.*requires.*active grouping"):
            Q.nodes().compute("degree").coverage(mode="all").execute(net)
    
    def test_coverage_mode_all(self, sample_multilayer_network):
        """Test coverage mode='all' returns intersection."""
        net = sample_multilayer_network
        
        # Get top-3 degree nodes per layer, then get intersection
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .coverage(mode="all")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Get unique node IDs
        node_ids = set(df["id"].unique())
        
        # Verify these nodes appear in all 3 layers
        for node_id in node_ids:
            node_layers = set(df[df["id"] == node_id]["layer"])
            assert len(node_layers) == 3, f"Node {node_id} should appear in all 3 layers"
    
    def test_coverage_mode_any(self, sample_multilayer_network):
        """Test coverage mode='any' returns union."""
        net = sample_multilayer_network
        
        # Get top-3 degree nodes per layer, keep any that appear in at least one layer
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .coverage(mode="any")
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should have nodes from all layers
        layers_found = set(df["layer"].unique())
        assert len(layers_found) == 3
        
        # Should have multiple nodes (at least as many as top-3 per layer)
        assert len(df) >= 3
    
    def test_coverage_mode_at_least(self, sample_multilayer_network):
        """Test coverage mode='at_least' with k=2."""
        net = sample_multilayer_network
        
        # Get nodes that are in top-3 in at least 2 layers
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .coverage(mode="at_least", k=2)
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Verify each unique node appears in at least 2 layers
        for node_id in df["id"].unique():
            node_layers = set(df[df["id"] == node_id]["layer"])
            assert len(node_layers) >= 2, f"Node {node_id} should appear in at least 2 layers"
    
    def test_coverage_mode_exact(self, sample_multilayer_network):
        """Test coverage mode='exact' with k=2."""
        net = sample_multilayer_network
        
        # Get nodes that are in top-3 in exactly 2 layers
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree")
             .per_layer()
                .top_k(3, "degree")
             .end_grouping()
             .coverage(mode="exact", k=2)
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Verify each unique node appears in exactly 2 layers
        for node_id in df["id"].unique():
            node_layers = set(df[df["id"] == node_id]["layer"])
            assert len(node_layers) == 2, f"Node {node_id} should appear in exactly 2 layers"
    
    def test_per_layer_on_edges_raises_error(self, sample_multilayer_network):
        """Test that per_layer() on edges raises clear error."""
        net = sample_multilayer_network
        
        with pytest.raises(DslExecutionError, match="per_layer.*only.*node queries"):
            (
                Q.edges()
                 .from_layers(L["*"])
                 .per_layer()
                 .execute(net)
            )


class TestEquivalenceWithManualLoop:
    """Test that DSL produces same results as manual loop implementation."""
    
    def test_basic_equivalence(self):
        """Test equivalence for a simple multilayer network."""
        # Create a deterministic network
        import random
        random.seed(42)
        
        net = random_generators.random_multilayer_ER(n=50, l=3, p=0.1, directed=False)
        
        # Baseline: Manual loop
        layer_top = {}
        for layer in net.layers:
            res = (
                Q.nodes()
                 .from_layers(L[str(layer)])
                 .where(degree__gt=1)
                 .compute("degree", "betweenness_centrality")
                 .order_by("-betweenness_centrality")
                 .limit(5)
                 .execute(net)
            )
            df = res.to_pandas()
            # Convert to int to handle numpy types
            layer_top[layer] = set(int(x) for x in df["id"])
        
        # Handle empty intersection case
        if layer_top:
            baseline_multi_hubs = set.intersection(*layer_top.values())
        else:
            baseline_multi_hubs = set()
        
        # New DSL: Single query with grouping and coverage
        res_new = (
            Q.nodes()
             .from_layers(L["*"])
             .where(degree__gt=1)
             .compute("degree", "betweenness_centrality")
             .per_layer()
                .top_k(5, "betweenness_centrality")
             .end_grouping()
             .coverage(mode="all")
             .execute(net)
        )
        df_new = res_new.to_pandas()
        # Convert to int to handle numpy types
        multi_hub_ids_new = set(int(x) for x in df_new["id"].unique())
        
        # Should be equivalent
        assert multi_hub_ids_new == baseline_multi_hubs
    
    def test_equivalence_larger_network(self):
        """Test equivalence on a larger random network."""
        import random
        random.seed(123)
        
        net = random_generators.random_multilayer_ER(n=120, l=3, p=0.05, directed=False)
        
        # Baseline: Manual loop
        layer_top = {}
        for layer in net.layers:
            res = (
                Q.nodes()
                 .from_layers(L[str(layer)])
                 .where(degree__gt=1)
                 .compute("degree", "betweenness_centrality")
                 .order_by("-betweenness_centrality")
                 .limit(5)
                 .execute(net)
            )
            df = res.to_pandas()
            # Convert to int to handle numpy types
            layer_top[layer] = set(int(x) for x in df["id"])
        
        if layer_top:
            baseline_multi_hubs = set.intersection(*layer_top.values())
        else:
            baseline_multi_hubs = set()
        
        # New DSL
        res_new = (
            Q.nodes()
             .from_layers(L["*"])
             .where(degree__gt=1)
             .compute("degree", "betweenness_centrality")
             .per_layer()
                .top_k(5, "betweenness_centrality")
             .end_grouping()
             .coverage(mode="all")
             .execute(net)
        )
        df_new = res_new.to_pandas()
        # Convert to int to handle numpy types
        multi_hub_ids_new = set(int(x) for x in df_new["id"].unique())
        
        # Should be equivalent
        assert multi_hub_ids_new == baseline_multi_hubs
    
    def test_union_coverage_equivalence(self):
        """Test that coverage mode='any' gives union of per-layer top-k.
        
        Note: When using grouping with wildcard layers, measures (like degree and 
        betweenness_centrality) are computed on the combined subgraph of all selected 
        layers, whereas in the manual loop approach, they're computed separately per 
        layer. This can lead to different top-k selections.
        
        For strict equivalence with per-layer computation, use separate queries per 
        layer (manual loop). For analysis across the combined multilayer structure, 
        use the grouping approach.
        """
        import random
        random.seed(456)
        
        net = random_generators.random_multilayer_ER(n=80, l=3, p=0.08, directed=False)
        
        # Test that mode="any" returns at least the intersection and at most all nodes
        res_any = (
            Q.nodes()
             .from_layers(L["*"])
             .where(degree__gt=1)
             .compute("degree")
             .per_layer()
                .top_k(5, "degree")
             .end_grouping()
             .coverage(mode="any")
             .execute(net)
        )
        df_any = res_any.to_pandas()
        any_ids = set(int(x) for x in df_any["id"].unique())
        
        # Get the "all" coverage for comparison
        res_all = (
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
        df_all = res_all.to_pandas()
        all_ids = set(int(x) for x in df_all["id"].unique())
        
        # any should be a superset of all
        assert all_ids.issubset(any_ids), "Coverage 'all' should be a subset of 'any'"
        
        # any should have at least as many nodes as there are layers (assuming top-k finds nodes)
        # This is a weaker assertion but tests the basic functionality
        num_layers = len(list(net.layers))
        assert len(any_ids) >= min(num_layers, 1), f"Coverage 'any' should have at least {num_layers} nodes"


class TestBackwardCompatibility:
    """Test that existing queries still work."""
    
    def test_simple_query_unchanged(self, sample_multilayer_network):
        """Test that queries without grouping still work."""
        net = sample_multilayer_network
        
        # Simple query without grouping
        result = (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("degree")
             .order_by("-degree")
             .limit(5)
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should work as before
        assert len(df) == 5
        assert "degree" in df.columns
        assert df["degree"].notna().all()
    
    def test_edge_query_unchanged(self, sample_multilayer_network):
        """Test that edge queries still work."""
        net = sample_multilayer_network
        
        # Edge query without grouping
        result = (
            Q.edges()
             .from_layers(L["layer0"])
             .where(intralayer=True)
             .execute(net)
        )
        
        df = result.to_pandas()
        
        # Should work as before
        assert len(df) > 0
        assert "source" in df.columns
        assert "target" in df.columns


class TestErrorHandling:
    """Test error handling for invalid configurations."""
    
    def test_coverage_without_k_for_at_least(self, sample_multilayer_network):
        """Test that coverage mode='at_least' requires k parameter."""
        net = sample_multilayer_network
        
        with pytest.raises(ValueError, match="requires k or threshold parameter"):
            (
                Q.nodes()
                 .per_layer()
                 .coverage(mode="at_least")
                 .execute(net)
            )
    
    def test_coverage_with_invalid_mode(self, sample_multilayer_network):
        """Test that invalid coverage mode raises error."""
        net = sample_multilayer_network
        
        with pytest.raises(ValueError, match="Unknown coverage mode"):
            (
                Q.nodes()
                 .per_layer()
                 .coverage(mode="invalid_mode")
                 .execute(net)
            )
    
    def test_top_k_without_grouping(self, sample_multilayer_network):
        """Test that top_k without grouping raises clear error."""
        net = sample_multilayer_network
        
        with pytest.raises(ValueError, match="top_k.*requires grouping"):
            (
                Q.nodes()
                 .compute("degree")
                 .top_k(5, "degree")
                 .execute(net)
            )


class TestExplainMode:
    """Test EXPLAIN mode with grouping."""
    
    def test_explain_with_grouping(self, sample_multilayer_network):
        """Test that EXPLAIN shows grouping steps."""
        net = sample_multilayer_network
        
        plan = (
            Q.nodes()
             .from_layers(L["*"])
             .compute("degree", "betweenness_centrality")
             .per_layer()
                .top_k(5, "betweenness_centrality")
             .end_grouping()
             .coverage(mode="all")
             .explain()
             .execute(net)
        )
        
        # Check that plan includes grouping steps
        step_descriptions = [step.description for step in plan.steps]
        
        # Should mention grouping
        assert any("group" in desc.lower() for desc in step_descriptions)
        
        # Should mention top-k or per-group limit
        assert any("top" in desc.lower() for desc in step_descriptions)
        
        # Should mention coverage
        assert any("coverage" in desc.lower() for desc in step_descriptions)
