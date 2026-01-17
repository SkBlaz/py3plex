"""Graph Programs - First-class compositional program objects.

This module implements Graph Programs as immutable, typed, optimizable program
objects with rewrite rules, cost semantics, and UQ semantics.

Core Components:
    - TypeSystem: Static type system for DSL IR (implemented)
    - GraphProgram: Immutable program object with canonical AST (implemented)
    - ProgramMetadata: Provenance and version tracking (implemented)
    - RewriteEngine: Correctness-preserving program transformations (planned)
    - CostModel: Time/memory cost estimation (planned)
    - ExecutionPlan: Optimized execution strategy (planned)
    - Distribution: UQ-aware result type (planned)
    - ProgramCache: Reproducibility-keyed caching (planned)

Example:
    >>> from py3plex.dsl.program import GraphProgram, type_check, infer_type
    >>> from py3plex.dsl import Q
    >>>
    >>> # Create program from AST
    >>> query_ast = Q.nodes().compute("degree").to_ast()
    >>> program = GraphProgram.from_ast(query_ast)
    >>>
    >>> # Execute program
    >>> result = program.execute(network)
    >>>
    >>> # Type check and infer
    >>> type_check(query_ast)
    True
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

from .program import (
    GraphProgram,
    ProgramMetadata,
    compose,
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
    # Programs
    "GraphProgram",
    "ProgramMetadata",
    "compose",
]
