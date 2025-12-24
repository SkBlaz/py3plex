"""
Tests for py3plex.dsl.serializer module.

This module tests AST to DSL string serialization.
"""

import pytest

from py3plex.dsl.ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    FunctionCall,
    ComputeItem,
    OrderItem,
)
from py3plex.dsl.serializer import (
    ast_to_dsl,
    _serialize_select,
    _serialize_layer_expr,
    _serialize_conditions,
    _serialize_atom,
    _serialize_comparison,
)


class TestAstToDsl:
    """Test the main ast_to_dsl function."""

    def test_simple_select_nodes(self):
        """Test serializing simple SELECT nodes query."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=None,
                where=None,
                compute=None,
                order_by=None,
                limit=None
            )
        )
        result = ast_to_dsl(query)
        assert "SELECT nodes" in result

    def test_simple_select_edges(self):
        """Test serializing simple SELECT edges query."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.EDGES,
                layer_expr=None,
                where=None,
                compute=None,
                order_by=None,
                limit=None
            )
        )
        result = ast_to_dsl(query)
        assert "SELECT edges" in result

    def test_explain_prefix(self):
        """Test that EXPLAIN prefix is included when set."""
        query = Query(
            explain=True,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=None,
                where=None,
                compute=None,
                order_by=None,
                limit=None
            )
        )
        result = ast_to_dsl(query)
        assert result.startswith("EXPLAIN")
        assert "SELECT nodes" in result


class TestSerializeSelect:
    """Test the _serialize_select function."""

    def test_select_with_layer(self):
        """Test serializing SELECT with FROM clause."""
        stmt = SelectStmt(
            target=Target.NODES,
            layer_expr=LayerExpr(terms=[LayerTerm("social")]),
            where=None,
            compute=None,
            order_by=None,
            limit=None
        )
        result = _serialize_select(stmt)
        assert "SELECT nodes" in result
        assert "FROM" in result
        assert "social" in result

    def test_select_with_compute(self):
        """Test serializing SELECT with COMPUTE clause."""
        stmt = SelectStmt(
            target=Target.NODES,
            layer_expr=None,
            where=None,
            compute=[
                ComputeItem(name="degree", alias=None),
                ComputeItem(name="betweenness", alias="bc")
            ],
            order_by=None,
            limit=None
        )
        result = _serialize_select(stmt)
        assert "COMPUTE" in result
        assert "degree" in result
        assert "betweenness AS bc" in result

    def test_select_with_order_by(self):
        """Test serializing SELECT with ORDER BY clause."""
        stmt = SelectStmt(
            target=Target.NODES,
            layer_expr=None,
            where=None,
            compute=None,
            order_by=[
                OrderItem(key="degree", desc=True),
                OrderItem(key="id", desc=False)
            ],
            limit=None
        )
        result = _serialize_select(stmt)
        assert "ORDER BY" in result
        assert "degree DESC" in result
        assert "id ASC" in result

    def test_select_with_limit(self):
        """Test serializing SELECT with LIMIT clause."""
        stmt = SelectStmt(
            target=Target.NODES,
            layer_expr=None,
            where=None,
            compute=None,
            order_by=None,
            limit=10
        )
        result = _serialize_select(stmt)
        assert "LIMIT 10" in result


class TestSerializeLayerExpr:
    """Test the _serialize_layer_expr function."""

    def test_simple_layer_name(self):
        """Test serializing simple layer name."""
        expr = LayerExpr(terms=[LayerTerm("social")])
        result = _serialize_layer_expr(expr)
        assert "social" in result

    def test_layer_union(self):
        """Test serializing layer union expression."""
        expr = LayerExpr(
            terms=[LayerTerm("social"), LayerTerm("work")],
            ops=["+"]
        )
        result = _serialize_layer_expr(expr)
        assert "social" in result
        assert "work" in result


class TestSerializeConditions:
    """Test the _serialize_conditions function."""

    def test_single_condition(self):
        """Test serializing single condition."""
        conditions = ConditionExpr(
            atoms=[
                ConditionAtom(
                    comparison=Comparison(
                        left="degree",
                        op=">",
                        right=5
                    )
                )
            ]
        )
        result = _serialize_conditions(conditions)
        assert "degree" in result
        assert ">" in result
        assert "5" in result

    def test_multiple_conditions_with_and(self):
        """Test serializing multiple AND conditions."""
        conditions = ConditionExpr(
            atoms=[
                ConditionAtom(
                    comparison=Comparison(left="degree", op=">", right=5)
                ),
                ConditionAtom(
                    comparison=Comparison(left="layer", op="==", right="social")
                )
            ],
            ops=["AND"]
        )
        result = _serialize_conditions(conditions)
        assert "degree" in result
        assert "layer" in result
        assert "AND" in result or "and" in result


class TestSerializeAtom:
    """Test the _serialize_atom function."""

    def test_simple_comparison(self):
        """Test serializing simple comparison."""
        atom = ConditionAtom(
            comparison=Comparison(left="degree", op=">", right=10)
        )
        result = _serialize_atom(atom)
        assert "degree" in result
        assert ">" in result
        assert "10" in result

    def test_function_call_condition(self):
        """Test serializing function call condition."""
        atom = ConditionAtom(
            function=FunctionCall(name="is_active", args=[])
        )
        result = _serialize_atom(atom)
        assert "is_active" in result


class TestSerializeComparison:
    """Test the _serialize_comparison function."""

    def test_numeric_comparison(self):
        """Test serializing numeric comparison."""
        comp = Comparison(left="degree", op=">", right=5)
        result = _serialize_comparison(comp)
        assert "degree" in result
        assert ">" in result
        assert "5" in result

    def test_string_comparison(self):
        """Test serializing string comparison."""
        comp = Comparison(left="name", op="==", right="Alice")
        result = _serialize_comparison(comp)
        assert "name" in result
        assert "==" in result
        assert "Alice" in result

    def test_boolean_comparison(self):
        """Test serializing boolean comparison."""
        comp = Comparison(left="active", op="==", right=True)
        result = _serialize_comparison(comp)
        assert "active" in result
        assert "True" in result or "true" in result

    def test_different_operators(self):
        """Test serializing different comparison operators."""
        operators = ["<", "<=", ">", ">=", "==", "!="]
        for op in operators:
            comp = Comparison(left="x", op=op, right=0)
            result = _serialize_comparison(comp)
            assert op in result
            assert "x" in result


class TestCompleteQuerySerialization:
    """Test serialization of complete queries."""

    def test_complex_query_serialization(self):
        """Test serializing a complex query with multiple clauses."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=LayerExpr(terms=[LayerTerm("social")]),
                where=ConditionExpr(
                    atoms=[
                        ConditionAtom(
                            comparison=Comparison(
                                left="degree",
                                op=">",
                                right=3
                            )
                        )
                    ]
                ),
                compute=[
                    ComputeItem(name="betweenness", alias="bc")
                ],
                order_by=[
                    OrderItem(key="bc", desc=True)
                ],
                limit=10
            )
        )
        result = ast_to_dsl(query)
        
        # Check all parts are present
        assert "SELECT nodes" in result
        assert "FROM" in result
        assert "social" in result
        assert "WHERE" in result
        assert "degree" in result
        assert ">" in result
        assert "3" in result
        assert "COMPUTE" in result
        assert "betweenness AS bc" in result
        assert "ORDER BY" in result
        assert "bc DESC" in result
        assert "LIMIT 10" in result

    def test_roundtrip_consistency(self):
        """Test that serialization produces consistent DSL strings."""
        # Create a simple query
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=LayerExpr(terms=[LayerTerm("test")]),
                where=None,
                compute=None,
                order_by=None,
                limit=None
            )
        )
        
        # Serialize twice
        result1 = ast_to_dsl(query)
        result2 = ast_to_dsl(query)
        
        # Should be identical
        assert result1 == result2
