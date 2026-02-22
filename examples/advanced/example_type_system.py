#!/usr/bin/env python3
"""Example demonstrating the py3plex type system for DSL programs.

This script shows how to use the type system for:
1. Type inference from AST nodes
2. Type checking DSL queries
3. Type unification for composable operations
4. Working with UQ-aware types
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from py3plex.dsl.program import (
    TypeSystem,
    NodeSetType,
    EdgeSetType,
    TableType,
    DistributionType,
    NumericType,
    StringType,
    infer_type,
    type_check,
    TypeCheckError,
)
from py3plex.dsl.ast import (
    SelectStmt,
    Target,
    ComputeItem,
    OrderItem,
    UQConfig,
    ExportTarget,
    LayerExpr,
    LayerTerm,
)


def example_1_basic_type_inference():
    """Example 1: Basic type inference."""
    print("=" * 60)
    print("Example 1: Basic Type Inference")
    print("=" * 60)
    
    # Create a simple node query
    query = SelectStmt(target=Target.NODES)
    
    # Infer the type
    result_type = infer_type(query)
    
    print(f"Query: SELECT nodes")
    print(f"Inferred type: {result_type}")
    print(f"Type class: {type(result_type).__name__}")
    print()


def example_2_type_inference_with_compute():
    """Example 2: Type inference with computed metrics."""
    print("=" * 60)
    print("Example 2: Type Inference with Computed Metrics")
    print("=" * 60)
    
    # Query with computed metrics
    query = SelectStmt(
        target=Target.NODES,
        compute=[
            ComputeItem(name="degree"),
            ComputeItem(name="betweenness_centrality", alias="bc"),
        ],
    )
    
    result_type = infer_type(query)
    
    print(f"Query: SELECT nodes COMPUTE degree, betweenness_centrality")
    print(f"Inferred type: {result_type}")
    print(f"Has metrics: {result_type.has_metrics}")
    print()


def example_3_type_inference_with_layers():
    """Example 3: Type inference with layer filtering."""
    print("=" * 60)
    print("Example 3: Type Inference with Layer Filtering")
    print("=" * 60)
    
    # Query with layer filtering
    layer_expr = LayerExpr(
        terms=[LayerTerm(name="social"), LayerTerm(name="work")],
        ops=["+"],
    )
    query = SelectStmt(target=Target.NODES, layer_expr=layer_expr)
    
    result_type = infer_type(query)
    
    print(f"Query: SELECT nodes FROM layers social + work")
    print(f"Inferred type: {result_type}")
    print(f"Layers: {result_type.layers}")
    print()


def example_4_type_inference_with_export():
    """Example 4: Type inference with export to DataFrame."""
    print("=" * 60)
    print("Example 4: Type Inference with Export")
    print("=" * 60)
    
    # Query with export to pandas
    query = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree"), ComputeItem(name="pagerank")],
        export=ExportTarget.PANDAS,
    )
    
    result_type = infer_type(query)
    
    print(f"Query: SELECT nodes COMPUTE degree, pagerank EXPORT pandas")
    print(f"Inferred type: {result_type}")
    print(f"Columns: {list(result_type.columns.keys())}")
    print(f"Column types:")
    for col, col_type in sorted(result_type.columns.items()):
        print(f"  {col}: {col_type}")
    print()


def example_5_uq_type_inference():
    """Example 5: Type inference with uncertainty quantification."""
    print("=" * 60)
    print("Example 5: UQ-Aware Type Inference")
    print("=" * 60)
    
    # Query with UQ
    query = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree", uncertainty=True)],
        uq_config=UQConfig(method="bootstrap", n_samples=100),
    )
    
    result_type = infer_type(query)
    
    print(f"Query: SELECT nodes COMPUTE degree WITH UQ")
    print(f"Inferred type: {result_type}")
    print(f"Is Distribution? {isinstance(result_type, DistributionType)}")
    if isinstance(result_type, DistributionType):
        print(f"Inner type: {result_type.inner}")
    print()


def example_6_type_checking_valid():
    """Example 6: Type checking a valid query."""
    print("=" * 60)
    print("Example 6: Type Checking (Valid Query)")
    print("=" * 60)
    
    # Valid query with order_by on computed metric
    query = SelectStmt(
        target=Target.NODES,
        compute=[ComputeItem(name="degree")],
        order_by=[OrderItem(key="degree", desc=True)],
    )
    
    print(f"Query: SELECT nodes COMPUTE degree ORDER BY degree DESC")
    try:
        is_valid = type_check(query)
        print(f"Type check result: {'OK Valid' if is_valid else 'FAIL Invalid'}")
    except TypeCheckError as e:
        print(f"Type check error: {e}")
    print()


def example_7_type_checking_invalid():
    """Example 7: Type checking an invalid query."""
    print("=" * 60)
    print("Example 7: Type Checking (Invalid Query)")
    print("=" * 60)
    
    # Invalid query: order_by without computing the metric
    query = SelectStmt(
        target=Target.NODES,
        autocompute=False,  # Disable autocompute
        order_by=[OrderItem(key="degree")],  # degree not computed
    )
    
    print(f"Query: SELECT nodes ORDER BY degree (without computing it)")
    try:
        is_valid = type_check(query)
        print(f"Type check result: {'OK Valid' if is_valid else 'FAIL Invalid'}")
    except TypeCheckError as e:
        print(f"Type check error: FAIL {e}")
    print()


def example_8_type_unification():
    """Example 8: Type unification."""
    print("=" * 60)
    print("Example 8: Type Unification")
    print("=" * 60)
    
    ts = TypeSystem()
    
    # Unify NodeSetType with different layers
    t1 = NodeSetType(layers=frozenset({"social", "work"}), has_metrics=True)
    t2 = NodeSetType(layers=frozenset({"social"}), has_metrics=True)
    unified = ts.unify(t1, t2)
    
    print(f"Type 1: {t1}")
    print(f"Type 2: {t2}")
    print(f"Unified: {unified}")
    print(f"Unified layers: {unified.layers}")
    print()
    
    # Unify Distribution with non-Distribution
    t3 = DistributionType(NumericType())
    t4 = NumericType()
    unified2 = ts.unify(t3, t4)
    
    print(f"Type 3: {t3}")
    print(f"Type 4: {t4}")
    print(f"Unified: {unified2}")
    print()


def example_9_type_serialization():
    """Example 9: Type serialization for caching."""
    print("=" * 60)
    print("Example 9: Type Serialization")
    print("=" * 60)
    
    # Create a complex type
    original = TableType(
        columns={
            "node": StringType(),
            "degree": NumericType(),
            "bc": DistributionType(NumericType()),
        }
    )
    
    print(f"Original type: {original}")
    
    # Serialize
    serialized = original.to_dict()
    print(f"Serialized: {serialized}")
    
    # Deserialize
    from py3plex.dsl.program.types import Type
    
    restored = Type.from_dict(serialized)
    print(f"Restored type: {restored}")
    print(f"Equal? {original == restored}")
    print()


def example_10_typesystem_operations():
    """Example 10: Using TypeSystem class."""
    print("=" * 60)
    print("Example 10: TypeSystem Operations")
    print("=" * 60)
    
    ts = TypeSystem()
    
    # Show available operator signatures
    print(f"Registered operators: {len(ts.signatures)}")
    print(f"Sample operators: {list(ts.signatures.keys())[:5]}")
    print()
    
    # Get signature for a specific operator
    nodes_sig = ts.get_operator_signature("nodes")
    if nodes_sig:
        print(f"Operator: {nodes_sig.name}")
        print(f"Input types: {nodes_sig.input_types}")
        print(f"Output type: {nodes_sig.output_type}")
        print(f"Description: {nodes_sig.description}")
    print()
    
    # Type check using TypeSystem
    query = SelectStmt(
        target=Target.NODES, compute=[ComputeItem(name="degree")]
    )
    
    is_valid = ts.check(query)
    result_type = ts.infer(query)
    
    print(f"Query type check: {'OK Valid' if is_valid else 'FAIL Invalid'}")
    print(f"Inferred result type: {result_type}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("  py3plex Type System Examples")
    print("*" * 60)
    print()
    
    examples = [
        example_1_basic_type_inference,
        example_2_type_inference_with_compute,
        example_3_type_inference_with_layers,
        example_4_type_inference_with_export,
        example_5_uq_type_inference,
        example_6_type_checking_valid,
        example_7_type_checking_invalid,
        example_8_type_unification,
        example_9_type_serialization,
        example_10_typesystem_operations,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("*" * 60)
    print("  All examples completed!")
    print("*" * 60)
    print()


if __name__ == "__main__":
    main()
