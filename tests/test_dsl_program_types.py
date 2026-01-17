"""Tests for the DSL type system (py3plex.dsl.program.types).

This test suite verifies type inference, type checking, and type unification
for the DSL intermediate representation.
"""

import pytest
from py3plex.dsl.program.types import (
    # Types
    Type,
    GraphType,
    NodeSetType,
    EdgeSetType,
    PartitionType,
    TableType,
    DistributionType,
    ScalarType,
    NumericType,
    StringType,
    BoolType,
    TimeSeriesType,
    # Type system
    TypeSystem,
    OperatorSignature,
    OPERATOR_SIGNATURES,
    # Functions
    infer_type,
    type_check,
    # Errors
    TypeCheckError,
)
from py3plex.dsl.ast import (
    Query,
    SelectStmt,
    Target,
    ComputeItem,
    OrderItem,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    UQConfig,
    ExportTarget,
)


# ============================================================================
# Type Creation and Serialization Tests
# ============================================================================


def test_graph_type_creation():
    """Test GraphType creation and string representation."""
    t = GraphType()
    assert str(t) == "Graph"
    assert repr(t) == "Graph"


def test_nodeset_type_creation():
    """Test NodeSetType creation with and without layers."""
    # Without layers
    t1 = NodeSetType()
    assert str(t1) == "NodeSet"
    assert t1.layers is None
    assert not t1.has_metrics
    
    # With layers
    t2 = NodeSetType(layers={"social", "work"})
    assert "social" in str(t2)
    assert "work" in str(t2)
    assert t2.layers == {"social", "work"}
    
    # With metrics
    t3 = NodeSetType(has_metrics=True)
    assert t3.has_metrics


def test_edgeset_type_creation():
    """Test EdgeSetType creation."""
    t1 = EdgeSetType()
    assert str(t1) == "EdgeSet"
    
    t2 = EdgeSetType(layers={"social"})
    assert "social" in str(t2)


def test_partition_type_creation():
    """Test PartitionType creation."""
    t1 = PartitionType()
    assert str(t1) == "Partition"
    
    t2 = PartitionType(partition_name="louvain")
    assert "louvain" in str(t2)


def test_table_type_creation():
    """Test TableType creation."""
    t1 = TableType()
    assert str(t1) == "Table"
    assert len(t1.columns) == 0
    
    t2 = TableType(columns={"node": StringType(), "degree": NumericType()})
    assert t2.has_column("node")
    assert t2.has_column("degree")
    assert not t2.has_column("missing")
    assert isinstance(t2.get_column_type("degree"), NumericType)


def test_distribution_type_creation():
    """Test DistributionType creation."""
    inner = NumericType()
    t = DistributionType(inner)
    assert "Distribution" in str(t)
    assert "Numeric" in str(t)
    assert t.inner == inner


def test_timeseries_type_creation():
    """Test TimeSeriesType creation."""
    t1 = TimeSeriesType()
    assert "TimeSeries" in str(t1)
    
    t2 = TimeSeriesType(element_type=NumericType())
    assert "Numeric" in str(t2)


def test_type_serialization():
    """Test type serialization to/from dict."""
    # Simple types
    t1 = NumericType()
    d1 = t1.to_dict()
    t1_restored = Type.from_dict(d1)
    assert isinstance(t1_restored, NumericType)
    
    # Complex type with metadata
    t2 = NodeSetType(layers={"social", "work"}, has_metrics=True)
    d2 = t2.to_dict()
    assert d2["type"] == "NodeSetType"
    assert set(d2["layers"]) == {"social", "work"}
    assert d2["has_metrics"] is True
    
    t2_restored = Type.from_dict(d2)
    assert isinstance(t2_restored, NodeSetType)
    assert t2_restored.layers == {"social", "work"}
    assert t2_restored.has_metrics
    
    # Distribution type
    t3 = DistributionType(NumericType())
    d3 = t3.to_dict()
    t3_restored = Type.from_dict(d3)
    assert isinstance(t3_restored, DistributionType)
    assert isinstance(t3_restored.inner, NumericType)


def test_type_equality():
    """Test type equality checking."""
    t1 = NumericType()
    t2 = NumericType()
    t3 = StringType()
    
    assert t1 == t2
    assert t1 != t3
    
    # NodeSetType equality with layers
    n1 = NodeSetType(layers={"social"})
    n2 = NodeSetType(layers={"social"})
    n3 = NodeSetType(layers={"work"})
    
    assert n1 == n2
    assert n1 != n3


# ============================================================================
# Operator Signature Tests
# ============================================================================


def test_operator_signatures_exist():
    """Test that key operator signatures are defined."""
    assert "nodes" in OPERATOR_SIGNATURES
    assert "edges" in OPERATOR_SIGNATURES
    assert "where" in OPERATOR_SIGNATURES
    assert "compute" in OPERATOR_SIGNATURES
    assert "to_pandas" in OPERATOR_SIGNATURES
    assert "uq" in OPERATOR_SIGNATURES


def test_operator_signature_input_checking():
    """Test OperatorSignature input type checking."""
    sig = OperatorSignature(
        name="test_op",
        input_types=[NodeSetType(), NumericType()],
        output_type=TableType(),
    )
    
    # Correct inputs
    is_valid, error = sig.check_inputs([NodeSetType(), NumericType()])
    assert is_valid
    assert error is None
    
    # Wrong number of inputs
    is_valid, error = sig.check_inputs([NodeSetType()])
    assert not is_valid
    assert "Expected 2 inputs" in error
    
    # Wrong type
    is_valid, error = sig.check_inputs([StringType(), NumericType()])
    assert not is_valid
    assert "Input 0" in error


def test_type_compatibility_in_signatures():
    """Test type compatibility checking in signatures."""
    sig = OperatorSignature(
        name="test",
        input_types=[NodeSetType()],
        output_type=NodeSetType(),
    )
    
    # NodeSet with layers is compatible with NodeSet without layers
    is_valid, _ = sig.check_inputs([NodeSetType(layers={"social"})])
    assert is_valid
    
    # NodeSet with metrics is compatible
    is_valid, _ = sig.check_inputs([NodeSetType(has_metrics=True)])
    assert is_valid


# ============================================================================
# Type Inference Tests
# ============================================================================


def test_infer_basic_node_query():
    """Test type inference for basic node query."""
    stmt = SelectStmt(target=Target.NODES)
    result_type = infer_type(stmt)
    assert isinstance(result_type, NodeSetType)
    assert not result_type.has_metrics


def test_infer_edge_query():
    """Test type inference for edge query."""
    stmt = SelectStmt(target=Target.EDGES)
    result_type = infer_type(stmt)
    assert isinstance(result_type, EdgeSetType)


def test_infer_community_query():
    """Test type inference for community query."""
    stmt = SelectStmt(target=Target.COMMUNITIES)
    result_type = infer_type(stmt)
    assert isinstance(result_type, PartitionType)


def test_infer_with_compute():
    """Test type inference with compute operations."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree"), ComputeItem(name="betweenness_centrality")]
    )
    result_type = infer_type(stmt)
    assert isinstance(result_type, NodeSetType)
    assert result_type.has_metrics


def test_infer_with_layers():
    """Test type inference with layer filtering."""
    layer_expr = LayerExpr(terms=[LayerTerm(name="social"), LayerTerm(name="work")], ops=["+"])
    stmt = SelectStmt(target=Target.NODES, layer_expr=layer_expr)
    result_type = infer_type(stmt)
    assert isinstance(result_type, NodeSetType)
    assert result_type.layers == {"social", "work"}


def test_infer_with_uq():
    """Test type inference with uncertainty quantification."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree", uncertainty=True)],
        uq_config=UQConfig(method="bootstrap", n_samples=100)
    )
    result_type = infer_type(stmt)
    assert isinstance(result_type, DistributionType)
    assert isinstance(result_type.inner, NodeSetType)
    assert result_type.inner.has_metrics


def test_infer_to_pandas_export():
    """Test type inference with pandas export."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree")],
        export=ExportTarget.PANDAS
    )
    result_type = infer_type(stmt)
    assert isinstance(result_type, TableType)
    assert result_type.has_column("node")
    assert result_type.has_column("layer")
    assert result_type.has_column("degree")


def test_infer_to_networkx_export():
    """Test type inference with NetworkX export."""
    stmt = SelectStmt(
        target=Target.NODES,
        export=ExportTarget.NETWORKX
    )
    result_type = infer_type(stmt)
    assert isinstance(result_type, GraphType)


def test_infer_full_query():
    """Test type inference for a complete Query object."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree")]
    )
    query = Query(explain=False, select=stmt)
    result_type = infer_type(query)
    assert isinstance(result_type, NodeSetType)
    assert result_type.has_metrics


# ============================================================================
# Type Checking Tests
# ============================================================================


def test_type_check_basic_query():
    """Test type checking for basic query."""
    stmt = SelectStmt(target=Target.NODES)
    assert type_check(stmt) is True


def test_type_check_with_valid_order_by():
    """Test type checking with valid order_by."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree")],
        order_by=[OrderItem(key="degree")]
    )
    assert type_check(stmt) is True


def test_type_check_with_invalid_order_by():
    """Test type checking with invalid order_by (missing metric)."""
    stmt = SelectStmt(
        target=Target.NODES,
        autocompute=False,  # Disable autocompute
        order_by=[OrderItem(key="degree")]  # degree not computed
    )
    with pytest.raises(TypeCheckError) as exc_info:
        type_check(stmt)
    assert "degree" in str(exc_info.value)
    assert "not computed" in str(exc_info.value)


def test_type_check_with_autocompute():
    """Test that autocompute allows missing metrics."""
    stmt = SelectStmt(
        target=Target.NODES,
        autocompute=True,  # Enable autocompute
        order_by=[OrderItem(key="degree")]  # degree will be autocomputed
    )
    # Should not raise
    assert type_check(stmt) is True


def test_type_check_uq_without_compute():
    """Test that UQ without compute raises error."""
    stmt = SelectStmt(
        target=Target.NODES,
        uq_config=UQConfig(method="bootstrap")
    )
    with pytest.raises(TypeCheckError) as exc_info:
        type_check(stmt)
    assert "UQ requires computed metrics" in str(exc_info.value)


def test_type_check_limit_per_group_without_group_by():
    """Test that limit_per_group without group_by raises error."""
    stmt = SelectStmt(
        target=Target.NODES,
        limit_per_group=10
    )
    with pytest.raises(TypeCheckError) as exc_info:
        type_check(stmt)
    assert "requires group_by" in str(exc_info.value)


def test_type_check_invalid_export():
    """Test that invalid export combinations raise errors."""
    stmt = SelectStmt(
        target=Target.COMMUNITIES,
        export=ExportTarget.NETWORKX
    )
    with pytest.raises(TypeCheckError) as exc_info:
        type_check(stmt)
    assert "communities" in str(exc_info.value).lower()
    assert "NetworkX" in str(exc_info.value)


def test_type_check_condition_with_missing_attribute():
    """Test type checking condition with missing attribute."""
    stmt = SelectStmt(
        target=Target.NODES,
        autocompute=False,
        where=ConditionExpr(
            atoms=[ConditionAtom(comparison=Comparison(left="nonexistent_metric", op=">", right=5))]
        )
    )
    with pytest.raises(TypeCheckError) as exc_info:
        type_check(stmt)
    assert "nonexistent_metric" in str(exc_info.value)


def test_type_check_condition_with_computed_attribute():
    """Test type checking condition with computed attribute."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree")],
        where=ConditionExpr(
            atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=5))]
        )
    )
    # Should not raise
    assert type_check(stmt) is True


# ============================================================================
# Type System Class Tests
# ============================================================================


def test_type_system_initialization():
    """Test TypeSystem initialization."""
    ts = TypeSystem()
    assert len(ts.signatures) > 0
    assert "nodes" in ts.signatures


def test_type_system_infer():
    """Test TypeSystem.infer method."""
    ts = TypeSystem()
    stmt = SelectStmt(target=Target.NODES)
    result_type = ts.infer(stmt)
    assert isinstance(result_type, NodeSetType)


def test_type_system_check():
    """Test TypeSystem.check method."""
    ts = TypeSystem()
    stmt = SelectStmt(target=Target.NODES)
    assert ts.check(stmt) is True


def test_type_system_register_operator():
    """Test registering custom operator signature."""
    ts = TypeSystem()
    sig = OperatorSignature(
        name="custom_op",
        input_types=[NodeSetType()],
        output_type=TableType()
    )
    ts.register_operator(sig)
    assert "custom_op" in ts.signatures
    assert ts.get_operator_signature("custom_op") == sig


def test_type_system_unify_same_types():
    """Test unifying identical types."""
    ts = TypeSystem()
    t1 = NumericType()
    t2 = NumericType()
    unified = ts.unify(t1, t2)
    assert unified == NumericType()


def test_type_system_unify_numeric_types():
    """Test unifying numeric and scalar types."""
    ts = TypeSystem()
    t1 = NumericType()
    t2 = ScalarType()
    unified = ts.unify(t1, t2)
    assert isinstance(unified, NumericType)


def test_type_system_unify_nodesets():
    """Test unifying NodeSetType instances."""
    ts = TypeSystem()
    t1 = NodeSetType(layers={"social", "work"}, has_metrics=True)
    t2 = NodeSetType(layers={"social"}, has_metrics=True)
    unified = ts.unify(t1, t2)
    assert isinstance(unified, NodeSetType)
    assert unified.layers == {"social"}  # Intersection
    assert unified.has_metrics


def test_type_system_unify_nodesets_no_metrics():
    """Test unifying NodeSetType when one has no metrics."""
    ts = TypeSystem()
    t1 = NodeSetType(has_metrics=True)
    t2 = NodeSetType(has_metrics=False)
    unified = ts.unify(t1, t2)
    assert isinstance(unified, NodeSetType)
    assert not unified.has_metrics  # Both must have metrics


def test_type_system_unify_distributions():
    """Test unifying Distribution types."""
    ts = TypeSystem()
    t1 = DistributionType(NumericType())
    t2 = DistributionType(NumericType())
    unified = ts.unify(t1, t2)
    assert isinstance(unified, DistributionType)
    assert isinstance(unified.inner, NumericType)


def test_type_system_unify_distribution_with_non_distribution():
    """Test unifying Distribution with non-Distribution (prefers Distribution)."""
    ts = TypeSystem()
    t1 = DistributionType(NumericType())
    t2 = NumericType()
    unified = ts.unify(t1, t2)
    assert isinstance(unified, DistributionType)
    assert isinstance(unified.inner, NumericType)


def test_type_system_unify_tables():
    """Test unifying TableType instances."""
    ts = TypeSystem()
    t1 = TableType(columns={"a": NumericType(), "b": StringType()})
    t2 = TableType(columns={"a": NumericType(), "c": StringType()})
    unified = ts.unify(t1, t2)
    assert isinstance(unified, TableType)
    assert set(unified.columns.keys()) == {"a"}  # Intersection


def test_type_system_unify_incompatible_types():
    """Test unifying incompatible types returns None."""
    ts = TypeSystem()
    t1 = NumericType()
    t2 = StringType()
    unified = ts.unify(t1, t2)
    assert unified is None


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_empty_compute_list():
    """Test query with empty compute list."""
    stmt = SelectStmt(target=Target.NODES, compute=[])
    result_type = infer_type(stmt)
    assert isinstance(result_type, NodeSetType)
    assert not result_type.has_metrics


def test_multiple_compute_items():
    """Test query with multiple compute items."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[
            ComputeItem(name="degree"),
            ComputeItem(name="betweenness_centrality", alias="bc"),
            ComputeItem(name="pagerank", uncertainty=True)
        ],
        export=ExportTarget.PANDAS
    )
    result_type = infer_type(stmt)
    assert isinstance(result_type, TableType)
    assert result_type.has_column("degree")
    assert result_type.has_column("bc")  # Aliased
    assert result_type.has_column("pagerank")


def test_nested_distribution_types():
    """Test nested Distribution types (Distribution[Distribution[T]])."""
    inner_inner = NumericType()
    inner = DistributionType(inner_inner)
    outer = DistributionType(inner)
    
    assert str(outer) == "Distribution[Distribution[Numeric]]"


def test_type_check_error_preserves_node():
    """Test that TypeCheckError preserves the problematic node."""
    stmt = SelectStmt(
        target=Target.NODES,
        limit_per_group=10
    )
    try:
        type_check(stmt)
        assert False, "Should have raised TypeCheckError"
    except TypeCheckError as e:
        assert e.node == stmt


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_pipeline_type_checking():
    """Test type checking for a complete query pipeline."""
    stmt = SelectStmt(
        target=Target.NODES,
        layer_expr=LayerExpr(terms=[LayerTerm(name="social")], ops=[]),
        compute=[
            ComputeItem(name="degree"),
            ComputeItem(name="betweenness_centrality", alias="bc")
        ],
        where=ConditionExpr(
            atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=5))]
        ),
        order_by=[OrderItem(key="bc", desc=True)],
        limit=10,
        export=ExportTarget.PANDAS
    )
    
    # Type check
    assert type_check(stmt) is True
    
    # Infer type
    result_type = infer_type(stmt)
    assert isinstance(result_type, TableType)
    assert result_type.has_column("node")
    assert result_type.has_column("layer")
    assert result_type.has_column("degree")
    assert result_type.has_column("bc")


def test_uq_pipeline_type_checking():
    """Test type checking for UQ pipeline."""
    stmt = SelectStmt(
        target=Target.NODES,
        compute=[
            ComputeItem(name="degree", uncertainty=True),
            ComputeItem(name="pagerank", uncertainty=True)
        ],
        uq_config=UQConfig(method="bootstrap", n_samples=100, ci=0.95),
        export=ExportTarget.PANDAS
    )
    
    # Type check
    assert type_check(stmt) is True
    
    # Infer type
    result_type = infer_type(stmt)
    assert isinstance(result_type, TableType)
    assert result_type.has_column("degree")
    assert result_type.has_column("pagerank")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
