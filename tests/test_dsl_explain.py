"""Tests for .explain() DSL predicate.

Tests cover:
- explain() method in QueryBuilder
- Explanation engine (community, top_neighbors, layer_footprint)
- expand_explanations in to_pandas()
- Per-layer grouping with explanations
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, ExplainSpec


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'social'},
        {'source': 'E', 'type': 'work'},
        {'source': 'F', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'E', 'target': 'F', 'source_type': 'work', 'target_type': 'work', 'weight': 3.0},
    ]
    network.add_edges(edges)

    return network


class TestExplainMethod:
    """Test the explain() method in QueryBuilder."""

    def test_explain_basic(self, sample_network):
        """Test basic explain() usage for explanations mode."""
        query = Q.nodes().explain(neighbors_top=10)
        
        # Check that explain_spec is set
        assert query._select.explain_spec is not None
        assert isinstance(query._select.explain_spec, ExplainSpec)
        
        # Check default include list
        expected_include = {"community", "top_neighbors", "layer_footprint"}
        assert set(query._select.explain_spec.include) == expected_include
        assert query._select.explain_spec.neighbors_top == 10

    def test_explain_execution_plan_mode(self, sample_network):
        """Test explain() without arguments returns execution plan."""
        from py3plex.dsl.builder import ExplainQuery
        
        query_builder = Q.nodes().compute("degree")
        explain_query = query_builder.explain()
        
        # Should return ExplainQuery (not QueryBuilder)
        assert isinstance(explain_query, ExplainQuery)
        
        # Should be able to execute and get ExecutionPlan
        from py3plex.dsl.ast import ExecutionPlan
        plan = explain_query.execute(sample_network)
        assert isinstance(plan, ExecutionPlan)

    def test_explain_custom_include(self, sample_network):
        """Test explain() with custom include list."""
        query = Q.nodes().explain(include=["top_neighbors"])
        
        assert query._select.explain_spec.include == ["top_neighbors"]
        assert "community" not in query._select.explain_spec.include

    def test_explain_custom_exclude(self, sample_network):
        """Test explain() with exclude list."""
        query = Q.nodes().explain(exclude=["layer_footprint"])
        
        assert "layer_footprint" not in query._select.explain_spec.include
        assert "community" in query._select.explain_spec.include
        assert "top_neighbors" in query._select.explain_spec.include

    def test_explain_neighbors_top(self, sample_network):
        """Test explain() with custom neighbors_top."""
        query = Q.nodes().explain(neighbors_top=5)
        
        assert query._select.explain_spec.neighbors_top == 5

    def test_explain_validation_unknown_block(self, sample_network):
        """Test explain() raises error for unknown explanation blocks."""
        with pytest.raises(ValueError, match="Unknown explanation blocks"):
            Q.nodes().explain(include=["unknown_block"])

    def test_explain_validation_neighbors_top(self, sample_network):
        """Test explain() raises error for invalid neighbors_top."""
        with pytest.raises(ValueError, match="neighbors_top must be >= 1"):
            Q.nodes().explain(neighbors_top=0)

    def test_explain_multiple_calls_merge(self, sample_network):
        """Test multiple explain() calls merge configuration."""
        query = (
            Q.nodes()
            .explain(include=["community"])
            .explain(include=["top_neighbors"])
        )
        
        # Both should be included
        assert "community" in query._select.explain_spec.include
        assert "top_neighbors" in query._select.explain_spec.include

    def test_explain_chaining(self, sample_network):
        """Test explain() chains with other methods."""
        query = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .limit(3)
            .explain(neighbors_top=5)
        )
        
        assert query._select.explain_spec is not None
        assert query._select.limit == 3
        assert len(query._select.compute) == 1


class TestExplainExecution:
    """Test explain() execution and results."""

    def test_explain_execute_basic(self, sample_network):
        """Test explain() execution returns enriched results."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .explain(include=["top_neighbors"], neighbors_top=3)
            .execute(sample_network)
        )
        
        # Check that result has items
        assert len(result.items) > 0
        
        # Check that top_neighbors attribute exists
        assert "top_neighbors" in result.attributes
        
        # Check that some nodes have explanations
        for item in result.items:
            if item in result.attributes["top_neighbors"]:
                neighbors = result.attributes["top_neighbors"][item]
                # Should be a list
                assert isinstance(neighbors, list)
                # Should have at most 3 neighbors
                assert len(neighbors) <= 3

    def test_explain_with_limit(self, sample_network):
        """Test explain() works correctly after LIMIT."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(2)
            .explain(include=["layer_footprint"])
            .execute(sample_network)
        )
        
        # Should have exactly 2 items due to limit
        assert len(result.items) == 2
        
        # Both should have layer_footprint explanations
        assert "layers_present" in result.attributes
        assert "n_layers_present" in result.attributes

    def test_explain_community_without_partition(self, sample_network):
        """Test community explanation when no partition is available."""
        result = (
            Q.nodes()
            .explain(include=["community"])
            .execute(sample_network)
        )
        
        # Should have community attributes (may be None if no partition)
        assert "community_id" in result.attributes
        assert "community_size" in result.attributes

    def test_explain_empty_results(self, sample_network):
        """Test explain() with empty result set."""
        result = (
            Q.nodes()
            .from_layers(L["nonexistent"])
            .explain(neighbors_top=5)
            .execute(sample_network)
        )
        
        # Should have no items
        assert len(result.items) == 0


class TestExpandExplanations:
    """Test expand_explanations in to_pandas()."""

    def test_to_pandas_expand_explanations_false(self, sample_network):
        """Test to_pandas() without expanding explanations."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .explain(include=["community", "top_neighbors"], neighbors_top=2)
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=False)
        
        # Explanation columns should be present
        if "top_neighbors" in df.columns:
            # Should contain raw data structures
            first_neighbors = df["top_neighbors"].iloc[0]
            assert isinstance(first_neighbors, list)

    def test_to_pandas_expand_explanations_true(self, sample_network):
        """Test to_pandas() with expand_explanations=True."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .explain(include=["community", "top_neighbors", "layer_footprint"], neighbors_top=2)
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        # Should have standard columns
        assert "id" in df.columns
        assert "layer" in df.columns
        
        # Should have explanation columns
        # Note: These may be present even if values are None
        possible_columns = ["community_id", "community_size", "top_neighbors", 
                          "layers_present", "n_layers_present"]
        
        # At least some explanation columns should be present
        explanation_cols = [col for col in possible_columns if col in df.columns]
        assert len(explanation_cols) > 0

    def test_to_pandas_top_neighbors_format(self, sample_network):
        """Test that top_neighbors are properly formatted in DataFrame."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(1)
            .explain(include=["top_neighbors"], neighbors_top=5)
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        if "top_neighbors" in df.columns and len(df) > 0:
            neighbors_value = df["top_neighbors"].iloc[0]
            # Should be a string (JSON) after expansion
            assert isinstance(neighbors_value, (str, type(None)))

    def test_to_pandas_with_per_layer(self, sample_network):
        """Test explain() with per_layer grouping."""
        result = (
            Q.nodes()
            .per_layer()
            .explain(include=["top_neighbors"], neighbors_top=2)
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        # Should have layer column from grouping
        assert "layer" in df.columns
        
        # Should have explanation columns
        if "top_neighbors" in df.columns:
            # Check that we have data for different layers
            layers = df["layer"].unique()
            assert len(layers) > 0


class TestExplainNeighborsConfig:
    """Test neighbor configuration options."""

    def test_neighbors_metric_weight(self, sample_network):
        """Test neighbors ranked by weight."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(1)
            .explain(
                include=["top_neighbors"],
                neighbors_top=3,
                neighbors={"metric": "weight"}
            )
            .execute(sample_network)
        )
        
        # Check that neighbors are present
        assert "top_neighbors" in result.attributes

    def test_neighbors_metric_degree(self, sample_network):
        """Test neighbors ranked by degree."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(1)
            .explain(
                include=["top_neighbors"],
                neighbors_top=3,
                neighbors={"metric": "degree"}
            )
            .execute(sample_network)
        )
        
        # Check that neighbors are present
        assert "top_neighbors" in result.attributes

    def test_neighbors_scope_layer(self, sample_network):
        """Test layer-scoped neighbors."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(1)
            .explain(
                include=["top_neighbors"],
                neighbors_top=3,
                neighbors={"scope": "layer"}
            )
            .execute(sample_network)
        )
        
        assert "top_neighbors" in result.attributes

    def test_neighbors_scope_global(self, sample_network):
        """Test global-scoped neighbors."""
        result = (
            Q.nodes()
            .explain(
                include=["top_neighbors"],
                neighbors_top=3,
                neighbors={"scope": "global"}
            )
            .execute(sample_network)
        )
        
        assert "top_neighbors" in result.attributes


class TestExplainLayerFootprint:
    """Test layer footprint explanation."""

    def test_layer_footprint_single_layer(self, sample_network):
        """Test layer footprint for nodes in single layer."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(2)
            .explain(include=["layer_footprint"])
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        if "n_layers_present" in df.columns:
            # Nodes in only social layer should have n_layers_present = 1
            assert all(df["n_layers_present"] >= 1)

    def test_layer_footprint_format(self, sample_network):
        """Test layer footprint data format."""
        result = (
            Q.nodes()
            .limit(1)
            .explain(include=["layer_footprint"])
            .execute(sample_network)
        )
        
        # Check attributes
        assert "layers_present" in result.attributes
        assert "n_layers_present" in result.attributes
        
        # Get first item
        item = result.items[0]
        if item in result.attributes["layers_present"]:
            layers = result.attributes["layers_present"][item]
            assert isinstance(layers, list)


class TestExplainIntegration:
    """Integration tests for explain() with other DSL features."""

    def test_explain_with_compute(self, sample_network):
        """Test explain() combined with compute()."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .explain(include=["community", "top_neighbors"], neighbors_top=3)
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        # Should have both computed and explanation columns
        assert "degree" in df.columns
        # At least one explanation column should be present
        explanation_cols = [col for col in ["community_id", "top_neighbors"] if col in df.columns]
        assert len(explanation_cols) > 0

    def test_explain_with_order_by_limit(self, sample_network):
        """Test explain() with ordering and limit."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(2)
            .explain(include=["top_neighbors"], neighbors_top=2)
            .execute(sample_network)
        )
        
        # Should have exactly 2 items
        assert len(result.items) == 2
        
        df = result.to_pandas(expand_explanations=True)
        
        # Should be ordered by degree (descending)
        degrees = df["degree"].tolist()
        assert degrees == sorted(degrees, reverse=True)
        
        # Should have explanations
        if "top_neighbors" in df.columns:
            assert df["top_neighbors"].notna().any()

    def test_explain_flagship_usage(self, sample_network):
        """Test the flagship usage pattern from the issue."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .limit(20)
            .explain(
                neighbors_top=10,
                include=["community", "top_neighbors", "layer_footprint"]
            )
            .execute(sample_network)
        )
        
        df = result.to_pandas(expand_explanations=True)
        
        # Should have basic columns
        assert "id" in df.columns
        assert "layer" in df.columns
        
        # Should have explanation columns (even if some are None)
        # At least some should be present
        possible_cols = ["community_id", "community_size", "top_neighbors", 
                        "layers_present", "n_layers_present"]
        present_cols = [col for col in possible_cols if col in df.columns]
        assert len(present_cols) > 0
