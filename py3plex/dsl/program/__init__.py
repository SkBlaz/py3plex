"""Graph Programs - First-class compositional program objects.

This module implements Graph Programs as immutable, typed, optimizable program
objects with rewrite rules, cost semantics, and UQ semantics.

Core Components:
    - TypeSystem: Static type system for DSL IR (implemented)
    - GraphProgram: Immutable program object with canonical AST (planned)
    - RewriteEngine: Correctness-preserving program transformations (planned)
    - CostModel: Time/memory cost estimation (planned)
    - ExecutionPlan: Optimized execution strategy (planned)
    - Distribution: UQ-aware result type (planned)
    - ProgramCache: Reproducibility-keyed caching (planned)

Example:
    >>> from py3plex.dsl.program import TypeSystem, infer_type, type_check
    >>> from py3plex.dsl import Q
    >>>
    >>> # Type check a query
    >>> query_ast = Q.nodes().compute("degree").to_ast()
    >>> type_check(query_ast)
    True
    >>>
    >>> # Infer result type
    >>> result_type = infer_type(query_ast)
    >>> print(result_type)
    NodeSet
"""

from .types import (
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
    Type,
    TypeSystem,
    TypeCheckError,
    OperatorSignature,
    OPERATOR_SIGNATURES,
    type_check,
    infer_type,
)

__all__ = [
    # Types
    "GraphType",
    "NodeSetType",
    "EdgeSetType",
    "PartitionType",
    "TableType",
    "DistributionType",
    "ScalarType",
    "NumericType",
    "StringType",
    "BoolType",
    "TimeSeriesType",
    "Type",
    "TypeSystem",
    "TypeCheckError",
    "OperatorSignature",
    "OPERATOR_SIGNATURES",
    "type_check",
    "infer_type",
]
