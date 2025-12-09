"""Tests for DSL expression builder (F field descriptor).

Tests cover:
- Basic field comparisons (>, <, ==, !=, >=, <=)
- Boolean operators (&, |, ~)
- Mixed expression and kwargs usage
- Integration with QueryBuilder
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, F, Param
from py3plex.dsl.expressions import FieldExpression, BooleanExpression


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
        {'source': 'F', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
        {'source': 'E', 'target': 'F', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


class TestFieldExpression:
    """Test the F field descriptor and FieldExpression class."""

    def test_field_creation(self):
        """Test creating field expressions."""
        expr = F.degree
        assert isinstance(expr, FieldExpression)
        assert expr._field == "degree"

    def test_greater_than(self):
        """Test > operator."""
        expr = F.degree > 5
        assert isinstance(expr, BooleanExpression)
        condition = expr.to_condition_expr()
        assert len(condition.atoms) == 1
        assert condition.atoms[0].comparison.left == "degree"
        assert condition.atoms[0].comparison.op == ">"
        assert condition.atoms[0].comparison.right == 5

    def test_greater_equal(self):
        """Test >= operator."""
        expr = F.degree >= 5
        condition = expr.to_condition_expr()
        assert condition.atoms[0].comparison.op == ">="

    def test_less_than(self):
        """Test < operator."""
        expr = F.degree < 5
        condition = expr.to_condition_expr()
        assert condition.atoms[0].comparison.op == "<"

    def test_less_equal(self):
        """Test <= operator."""
        expr = F.degree <= 5
        condition = expr.to_condition_expr()
        assert condition.atoms[0].comparison.op == "<="

    def test_equality(self):
        """Test == operator."""
        expr = F.layer == "social"
        condition = expr.to_condition_expr()
        assert condition.atoms[0].comparison.left == "layer"
        assert condition.atoms[0].comparison.op == "="
        assert condition.atoms[0].comparison.right == "social"

    def test_not_equal(self):
        """Test != operator."""
        expr = F.layer != "bots"
        condition = expr.to_condition_expr()
        assert condition.atoms[0].comparison.op == "!="


class TestBooleanOperators:
    """Test boolean operators for combining expressions."""

    def test_and_operator(self):
        """Test & (AND) operator."""
        expr = (F.degree > 5) & (F.layer == "social")
        condition = expr.to_condition_expr()
        
        assert len(condition.atoms) == 2
        assert condition.atoms[0].comparison.left == "degree"
        assert condition.atoms[0].comparison.op == ">"
        assert condition.atoms[1].comparison.left == "layer"
        assert condition.atoms[1].comparison.op == "="
        assert "AND" in condition.ops

    def test_or_operator(self):
        """Test | (OR) operator."""
        expr = (F.degree > 10) | (F.clustering < 0.5)
        condition = expr.to_condition_expr()
        
        assert len(condition.atoms) == 2
        assert "OR" in condition.ops

    def test_complex_expression(self):
        """Test complex nested expressions."""
        # (degree > 10) | ((layer == "social") & (clustering < 0.5))
        expr = (F.degree > 10) | ((F.layer == "social") & (F.clustering < 0.5))
        condition = expr.to_condition_expr()
        
        # Should have 3 atoms: degree > 10, layer == social, clustering < 0.5
        assert len(condition.atoms) == 3
        # Should have ops: [OR, AND]
        assert len(condition.ops) == 2

    def test_not_operator_simple(self):
        """Test ~ (NOT) operator on simple expression."""
        expr = ~(F.degree > 5)
        condition = expr.to_condition_expr()
        
        # Should invert to degree <= 5
        assert condition.atoms[0].comparison.op == "<="

    def test_not_operator_complex_raises(self):
        """Test that ~ on complex expressions raises NotImplementedError."""
        expr = ~((F.degree > 5) & (F.layer == "social"))
        
        with pytest.raises(NotImplementedError, match="Negation of complex expressions"):
            expr.to_condition_expr()


class TestQueryBuilderIntegration:
    """Test integration with QueryBuilder."""

    def test_simple_expression_query(self, sample_network):
        """Test query with simple expression."""
        result = (
            Q.nodes()
             .where(F.layer == "social")  # Use layer filter which doesn't change
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert len(df) > 0
        # All returned nodes should be in social layer
        assert all(df['layer'] == "social")

    def test_and_expression_query(self, sample_network):
        """Test query with AND expression."""
        result = (
            Q.nodes()
             .where((F.layer == "social") & (F.layer != "work"))
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        # Should only return nodes in social layer
        assert all(df['layer'] == "social")
        assert len(df) == 3  # Only 3 nodes in social layer

    def test_or_expression_query(self, sample_network):
        """Test query with OR expression."""
        result = (
            Q.nodes()
             .where((F.layer == "social") | (F.layer == "work"))
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert len(df) > 0
        # Each node should be in either social or work layer
        for _, row in df.iterrows():
            assert row['layer'] in ["social", "work"]

    def test_mixed_expression_and_kwargs(self, sample_network):
        """Test mixing expression and kwargs."""
        result = (
            Q.nodes()
             .where(F.layer == "social", layer="social")  # Redundant but tests mixing
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        # Should AND the conditions: both select social layer
        assert all(df['layer'] == "social")

    def test_kwargs_only_still_works(self, sample_network):
        """Test that kwargs-only filtering still works."""
        result = (
            Q.nodes()
             .where(layer="social")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == "social")
        assert len(df) == 3

    def test_with_compute(self, sample_network):
        """Test expression with COMPUTE."""
        result = (
            Q.nodes()
             .where(F.layer == "social")
             .compute("degree", "clustering")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns
        assert all(df['layer'] == "social")

    def test_with_order_and_limit(self, sample_network):
        """Test expression with ORDER BY and LIMIT."""
        result = (
            Q.nodes()
             .where(F.degree >= 1)
             .compute("degree")
             .order_by("degree", desc=True)
             .limit(3)
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert len(df) <= 3
        # Check ordering
        degrees = df['degree'].tolist()
        assert degrees == sorted(degrees, reverse=True)

    def test_parameter_ref_in_expression(self, sample_network):
        """Test using Param.ref in expressions."""
        result = (
            Q.nodes()
             .where(F.layer == Param.str("target_layer"))
             .execute(sample_network, target_layer="social")
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == "social")

    def test_from_layers_with_expression(self, sample_network):
        """Test combining from_layers with expression."""
        result = (
            Q.nodes()
             .from_layers(L["social"])
             .where(F.layer == "social")  # Redundant but tests combination
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == "social")
        assert len(df) == 3


class TestErrorHandling:
    """Test error handling for invalid expressions."""

    def test_invalid_type_in_where(self, sample_network):
        """Test that passing invalid type to where() raises TypeError."""
        with pytest.raises(TypeError, match="must be BooleanExpression"):
            Q.nodes().where("invalid_string")

    def test_invalid_combination(self):
        """Test that combining incompatible types raises TypeError."""
        with pytest.raises(TypeError):
            _ = (F.degree > 5) & "not_an_expression"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_multiple_where_calls(self, sample_network):
        """Test chaining multiple where() calls."""
        result = (
            Q.nodes()
             .where(F.layer == "social")
             .where(F.layer != "work")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == "social")
        assert len(df) == 3

    def test_empty_expression(self, sample_network):
        """Test query with no conditions."""
        result = Q.nodes().execute(sample_network)
        df = result.to_pandas()
        # Should return all nodes
        assert len(df) == 6  # We added 6 nodes in fixture

    def test_string_comparison(self, sample_network):
        """Test string value comparisons."""
        result = (
            Q.nodes()
             .where(F.layer == "work")
             .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert all(df['layer'] == "work")
        assert len(df) == 3  # work layer has 3 nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
