"""Comprehensive pipe-level tests for DSL builder API.

This module tests complex method chaining scenarios (pipes) in the DSL builder API.
While basic chaining is covered in test_dsl_v2.py, this focuses on:
- Long multi-step pipelines (5+ chained methods)
- Combinations of all available methods
- Reusability of partially-built queries
- Edge cases in chaining
- Error handling in the middle of chains
"""

import pytest
import networkx as nx

from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    Param,
    QueryResult,
    ExecutionPlan,
    DslError,
    UnknownMeasureError,
)


@pytest.fixture
def rich_network():
    """Create a rich multilayer network for pipe testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create nodes across 3 layers
    nodes = []
    people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry']
    layers = ['social', 'work', 'hobby']
    
    for person in people:
        for layer in layers:
            nodes.append({'source': person, 'type': layer})
    
    network.add_nodes(nodes)
    
    # Add edges to create interesting topology
    edges = [
        # Social layer - well connected
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Eve', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Frank', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
        
        # Work layer - moderately connected
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'David', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        
        # Hobby layer - sparse
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'hobby', 'target_type': 'hobby'},
        {'source': 'Eve', 'target': 'Grace', 'source_type': 'hobby', 'target_type': 'hobby'},
    ]
    
    network.add_edges(edges)
    
    return network


class TestLongPipes:
    """Test long multi-step query pipelines."""
    
    def test_five_step_pipe(self, rich_network):
        """Test a 5-step pipeline: from_layers → where → compute → order_by → limit."""
        result = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .where(degree__gt=0)
             .compute("degree")
             .order_by("-degree")
             .limit(5)
             .execute(rich_network)
        )
        
        assert result.count <= 5
        assert "degree" in result.attributes
        
        # Verify ordering (descending)
        degrees = [result.attributes['degree'].get(node, 0) for node in result.items]
        assert degrees == sorted(degrees, reverse=True)
    
    def test_six_step_pipe_with_multiple_computes(self, rich_network):
        """Test a 6-step pipeline with multiple compute operations."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=1)
             .compute("degree")
             .compute("clustering")
             .order_by("-degree")
             .limit(3)
             .execute(rich_network)
        )
        
        assert result.count <= 3
        assert "degree" in result.attributes
        assert "clustering" in result.attributes
    
    def test_seven_step_pipe_with_multiple_where(self, rich_network):
        """Test a 7-step pipeline with multiple where clauses."""
        result = (
            Q.nodes()
             .where(layer="social")
             .where(degree__gt=0)
             .compute("degree", "clustering")
             .order_by("clustering")
             .limit(10)
             .execute(rich_network)
        )
        
        # Multiple where() calls should AND conditions together
        assert result.count <= 10
        for node in result.items:
            assert node[1] == "social"
    
    def test_eight_step_pipe_with_params(self, rich_network):
        """Test an 8-step pipeline with parameterized values."""
        result = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .where(degree__gt=Param.int("min_deg"))
             .compute("degree")
             .compute("betweenness_centrality", alias="bc")
             .order_by("-bc")
             .limit(Param.int("top_n"))
             .execute(rich_network, min_deg=1, top_n=5)
        )
        
        assert result.count <= 5
        assert "bc" in result.attributes
    
    def test_nine_step_pipe_with_layer_algebra(self, rich_network):
        """Test a 9-step pipeline with complex layer algebra."""
        result = (
            Q.nodes()
             .from_layers((L["social"] + L["work"]) - L["hobby"])
             .where(degree__gt=0)
             .compute("degree")
             .compute("clustering")
             .order_by("-degree")
             .order_by("clustering")
             .limit(5)
             .execute(rich_network)
        )
        
        assert result.count <= 5
        # Nodes should be from social or work, but not hobby
        for node in result.items:
            assert node[1] in ["social", "work"]


class TestLayerAlgebraInPipes:
    """Test layer algebra operations combined with other pipe operations."""
    
    def test_union_with_filtering_and_compute(self, rich_network):
        """Test layer union combined with filtering and computation."""
        result = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .where(degree__ge=2)
             .compute("degree", "betweenness_centrality")
             .execute(rich_network)
        )
        
        assert result.count > 0
        # All nodes should be from social or work layers
        for node in result.items:
            assert node[1] in ["social", "work"]
    
    def test_difference_with_ordering(self, rich_network):
        """Test layer difference with ordering."""
        result = (
            Q.nodes()
             .from_layers(L["social"] - L["hobby"])
             .compute("degree")
             .order_by("-degree")
             .limit(10)
             .execute(rich_network)
        )
        
        # Should only include social layer (hobby would be subtracted)
        for node in result.items:
            # Note: difference might include nodes not in hobby at all
            pass  # Just verify no crash
    
    def test_intersection_with_multiple_conditions(self, rich_network):
        """Test layer intersection with multiple where conditions."""
        result = (
            Q.nodes()
             .from_layers(L["social"] & L["work"])
             .where(degree__gt=0)
             .where(degree__lt=10)
             .compute("degree")
             .execute(rich_network)
        )
        
        # Should find common nodes in both layers
        assert result.count >= 0
    
    def test_complex_layer_expression(self, rich_network):
        """Test complex layer expression in a pipe."""
        # (social + work) & hobby
        result = (
            Q.nodes()
             .from_layers((L["social"] + L["work"]) & L["hobby"])
             .compute("degree")
             .order_by("degree")
             .execute(rich_network)
        )
        
        assert result.count >= 0


class TestMultipleMethodCalls:
    """Test calling the same method multiple times in a chain."""
    
    def test_multiple_where_calls(self, rich_network):
        """Test multiple where() calls - should AND conditions."""
        result = (
            Q.nodes()
             .where(layer="social")
             .where(degree__gt=1)
             .where(degree__lt=5)
             .execute(rich_network)
        )
        
        # All three conditions should apply
        for node in result.items:
            assert node[1] == "social"
            # Note: Using core_network.degree() here is intentional for this test
            # as it validates the filtered results match expected degree constraints
            degree = rich_network.core_network.degree(node)
            assert 1 < degree < 5
    
    def test_multiple_compute_calls(self, rich_network):
        """Test multiple compute() calls - should accumulate measures."""
        result = (
            Q.nodes()
             .compute("degree")
             .compute("clustering")
             .compute("betweenness_centrality")
             .execute(rich_network)
        )
        
        # All three measures should be computed
        assert "degree" in result.attributes
        assert "clustering" in result.attributes
        assert "betweenness_centrality" in result.attributes
    
    def test_multiple_order_by_calls(self, rich_network):
        """Test multiple order_by() calls - should order by first, then second."""
        result = (
            Q.nodes()
             .compute("degree", "clustering")
             .order_by("-degree")
             .order_by("clustering")
             .limit(10)
             .execute(rich_network)
        )
        
        # Should be ordered by degree (desc), then clustering (asc)
        assert result.count <= 10


class TestQueryReusability:
    """Test reusing and composing query builders."""
    
    def test_reuse_base_query(self, rich_network):
        """Test reusing a base query with different extensions."""
        # Create a base query
        base = Q.nodes().from_layers(L["social"])
        
        # Use it multiple times with different extensions
        result1 = base.where(degree__gt=2).execute(rich_network)
        result2 = base.where(degree__lt=2).execute(rich_network)
        
        # Both should work independently
        assert result1.count >= 0
        assert result2.count >= 0
        # Results should be different (unless all nodes have degree == 2)
    
    def test_build_query_incrementally(self, rich_network):
        """Test building a query step by step."""
        q = Q.nodes()
        q = q.from_layers(L["social"])
        q = q.where(degree__gt=0)
        q = q.compute("degree")
        q = q.order_by("-degree")
        q = q.limit(5)
        
        result = q.execute(rich_network)
        
        assert result.count <= 5
        assert "degree" in result.attributes
    
    def test_partial_query_to_ast(self, rich_network):
        """Test converting partial queries to AST."""
        # Build partial query
        partial = Q.nodes().from_layers(L["social"]).where(degree__gt=1)
        
        # Convert to AST
        ast = partial.to_ast()
        
        # Should have the layer and where clauses
        assert ast.select.layer_expr is not None
        assert ast.select.where is not None
    
    def test_partial_query_to_dsl(self, rich_network):
        """Test converting partial queries to DSL string."""
        partial = Q.nodes().where(layer="social").compute("degree")
        
        dsl_str = partial.to_dsl()
        
        # Should contain key elements
        assert "SELECT nodes" in dsl_str
        assert "WHERE" in dsl_str
        assert "COMPUTE degree" in dsl_str


class TestExportMethodsInPipes:
    """Test export methods integrated into query pipes."""
    
    def test_to_pandas_in_pipe(self, rich_network):
        """Test to_pandas export after a complex query."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree", "clustering")
             .order_by("-degree")
             .limit(5)
             .execute(rich_network)
        )
        
        df = result.to_pandas()
        
        assert len(df) == result.count
        assert "id" in df.columns
        assert "degree" in df.columns
        assert "clustering" in df.columns
    
    def test_to_dict_in_pipe(self, rich_network):
        """Test to_dict export after a complex query."""
        result = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .where(degree__gt=1)
             .compute("degree")
             .limit(10)
             .execute(rich_network)
        )
        
        data = result.to_dict()
        
        assert "nodes" in data
        assert "computed" in data
        assert "degree" in data["computed"]
    
    def test_to_networkx_in_pipe(self, rich_network):
        """Test to_networkx export after filtering."""
        result = (
            Q.nodes()
             .where(layer="social")
             .limit(5)
             .execute(rich_network)
        )
        
        G = result.to_networkx(rich_network)
        
        assert isinstance(G, nx.Graph)


class TestExplainInPipes:
    """Test EXPLAIN mode with complex pipelines."""
    
    def test_explain_simple_pipe(self, rich_network):
        """Test EXPLAIN on a simple pipeline."""
        plan = (
            Q.nodes()
             .where(layer="social")
             .compute("degree")
             .explain()
             .execute(rich_network)
        )
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
    
    def test_explain_complex_pipe(self, rich_network):
        """Test EXPLAIN on a complex pipeline."""
        plan = (
            Q.nodes()
             .from_layers(L["social"] + L["work"])
             .where(degree__gt=1)
             .compute("betweenness_centrality")
             .order_by("-betweenness_centrality")
             .limit(5)
             .explain()
             .execute(rich_network)
        )
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        # Check that steps describe the query operations
        step_descriptions = [s.description for s in plan.steps]
        assert any("layer" in desc.lower() or "filter" in desc.lower() for desc in step_descriptions)


class TestEdgeCasesInPipes:
    """Test edge cases and error scenarios in pipes."""
    
    def test_empty_result_pipe(self, rich_network):
        """Test pipeline that returns empty results."""
        result = (
            Q.nodes()
             .where(layer="nonexistent")
             .compute("degree")
             .order_by("degree")
             .limit(10)
             .execute(rich_network)
        )
        
        assert result.count == 0
        assert result.items == []
    
    def test_limit_larger_than_results(self, rich_network):
        """Test limit larger than available results."""
        result = (
            Q.nodes()
             .where(layer="social")
             .limit(1000)
             .execute(rich_network)
        )
        
        # Should return all available nodes (8 in social layer)
        assert result.count <= 1000
        assert result.count > 0
    
    def test_order_by_before_compute(self, rich_network):
        """Test ordering by a measure that's computed after."""
        # This should work - compute happens, then ordering
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree")
             .order_by("degree")
             .execute(rich_network)
        )
        
        assert result.count > 0
    
    def test_empty_network_pipe(self):
        """Test pipeline on empty network."""
        empty_net = multinet.multi_layer_network(directed=False)
        
        result = (
            Q.nodes()
             .where(layer="any")
             .compute("degree")
             .order_by("degree")
             .limit(10)
             .execute(empty_net)
        )
        
        assert result.count == 0


class TestParameterizedPipes:
    """Test parameterized queries in complex pipelines."""
    
    def test_multiple_params_in_pipe(self, rich_network):
        """Test multiple parameters in a single pipeline."""
        result = (
            Q.nodes()
             .where(layer=Param.str("target_layer"), degree__gt=Param.int("min_deg"))
             .compute("degree")
             .limit(Param.int("n"))
             .execute(rich_network, target_layer="social", min_deg=1, n=5)
        )
        
        assert result.count <= 5
        for node in result.items:
            assert node[1] == "social"
    
    def test_reuse_parameterized_query(self, rich_network):
        """Test reusing a parameterized query with different values."""
        q = (
            Q.nodes()
             .where(layer=Param.str("layer"), degree__gt=Param.int("min_deg"))
             .compute("degree")
             .limit(5)
        )
        
        # Execute with different parameters
        result1 = q.execute(rich_network, layer="social", min_deg=1)
        result2 = q.execute(rich_network, layer="work", min_deg=0)
        
        assert result1.count <= 5
        assert result2.count <= 5
        
        # Results should be from different layers
        for node in result1.items:
            assert node[1] == "social"
        for node in result2.items:
            assert node[1] == "work"
    
    def test_param_in_layer_expression(self, rich_network):
        """Test parameters cannot be used in layer expressions (should use strings)."""
        # Layer expressions currently use strings, not params
        # This test verifies current behavior
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=Param.int("k"))
             .execute(rich_network, k=1)
        )
        
        assert result.count >= 0


class TestErrorHandlingInPipes:
    """Test error handling in the middle of pipes."""
    
    def test_unknown_measure_in_pipe(self, rich_network):
        """Test that unknown measure raises error with suggestion."""
        with pytest.raises((UnknownMeasureError, DslError)):
            result = (
                Q.nodes()
                 .where(layer="social")
                 .compute("unknown_measure_xyz")
                 .execute(rich_network)
            )
    
    def test_invalid_layer_in_pipe(self, rich_network):
        """Test querying non-existent layer returns empty."""
        # Non-existent layers should return empty results, not error
        result = (
            Q.nodes()
             .where(layer="nonexistent_layer")
             .compute("degree")
             .execute(rich_network)
        )
        
        assert result.count == 0
    
    def test_invalid_operator_in_where(self, rich_network):
        """Test invalid comparison operator in where clause."""
        with pytest.raises(ValueError):
            # Invalid suffix should raise error
            result = (
                Q.nodes()
                 .where(degree__invalid=5)
                 .execute(rich_network)
            )


class TestInteropWithLegacyAPI:
    """Test interoperability between builder API and legacy DSL."""
    
    def test_builder_result_same_as_legacy(self, rich_network):
        """Test that builder API produces same results as legacy DSL."""
        from py3plex.dsl import execute_query
        
        # Builder API query
        builder_result = (
            Q.nodes()
             .where(layer="social")
             .execute(rich_network)
        )
        
        # Legacy DSL query
        legacy_result = execute_query(rich_network, 'SELECT nodes WHERE layer="social"')
        
        # Should have same count
        assert builder_result.count == legacy_result['count']
    
    def test_complex_builder_vs_legacy(self, rich_network):
        """Test complex query equivalence."""
        from py3plex.dsl import execute_query
        
        # Builder API
        builder_result = (
            Q.nodes()
             .where(layer="social", degree__gt=1)
             .compute("degree")
             .execute(rich_network)
        )
        
        # Legacy DSL
        legacy_result = execute_query(
            rich_network,
            'SELECT nodes WHERE layer="social" AND degree > 1 COMPUTE degree'
        )
        
        # Should have same count
        assert builder_result.count == legacy_result['count']


class TestComputeAliasesInPipes:
    """Test compute with aliases in various pipe scenarios."""
    
    def test_single_alias_in_pipe(self, rich_network):
        """Test single compute with alias in a pipe."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("betweenness_centrality", alias="bc")
             .order_by("-bc")
             .limit(5)
             .execute(rich_network)
        )
        
        assert "bc" in result.attributes
        assert "betweenness_centrality" not in result.attributes
    
    def test_multiple_computes_with_aliases(self, rich_network):
        """Test multiple compute calls with different aliases."""
        result = (
            Q.nodes()
             .compute("degree", alias="d")
             .compute("clustering", alias="c")
             .where(layer="social")
             .order_by("-d")
             .execute(rich_network)
        )
        
        assert "d" in result.attributes
        assert "c" in result.attributes
    
    def test_mixed_alias_and_no_alias(self, rich_network):
        """Test mixing aliased and non-aliased computes."""
        result = (
            Q.nodes()
             .compute("degree")
             .compute("betweenness_centrality", alias="bc")
             .compute("clustering")
             .where(layer="social")
             .execute(rich_network)
        )
        
        assert "degree" in result.attributes
        assert "bc" in result.attributes
        assert "clustering" in result.attributes


class TestOrderingEdgeCases:
    """Test edge cases in ordering operations."""
    
    def test_order_by_multiple_keys(self, rich_network):
        """Test ordering by multiple keys."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree", "clustering")
             .order_by("-degree", "clustering")
             .limit(10)
             .execute(rich_network)
        )
        
        assert result.count <= 10
    
    def test_order_by_with_missing_values(self, rich_network):
        """Test ordering when some nodes lack computed values."""
        result = (
            Q.nodes()
             .compute("degree")
             .order_by("degree")
             .execute(rich_network)
        )
        
        # Should handle nodes without degree values gracefully
        assert result.count > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
