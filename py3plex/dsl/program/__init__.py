"""Graph Programs - First-class compositional program objects.

This module implements Graph Programs as immutable, typed, optimizable program
objects with rewrite rules, cost semantics, and UQ semantics.

Core Components:
    - TypeSystem: Static type system for DSL IR (implemented)
    - GraphProgram: Immutable program object with canonical AST (implemented)
    - ProgramMetadata: Provenance and version tracking (implemented)
    - RewriteEngine: Correctness-preserving program transformations (implemented)
    - CostModel: Time/memory cost estimation (planned)
    - ExecutionPlan: Optimized execution strategy (planned)
    - Distribution: UQ-aware result type (planned)
    - ProgramCache: Reproducibility-keyed caching (planned)

Example:
    >>> from py3plex.dsl.program import GraphProgram, type_check, infer_type, apply_rewrites
    >>> from py3plex.dsl import Q
    >>>
    >>> # Create program from AST
    >>> query_ast = Q.nodes().compute("degree").to_ast()
    >>> program = GraphProgram.from_ast(query_ast)
    >>>
    >>> # Optimize with rewrites
    >>> optimized = apply_rewrites(program)
    >>>
    >>> # Execute program
    >>> result = optimized.execute(network)
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

from .rewrite import (
    Match,
    RewriteContext,
    RuleGuard,
    RewriteRule,
    RewriteEngine,
    apply_rewrites,
    get_standard_rules,
    get_aggressive_rules,
    get_conservative_rules,
)

from .cost import (
    Cost,
    CostModel,
    CostObjective,
    GraphStats,
    parse_time_budget,
    format_time_estimate,
    format_memory_estimate,
)

from .executor import (
    ExecutionContext,
    ExecutionPlan,
    PlanStage,
    BudgetExceededError,
    ExecutionTimeoutError,
    create_execution_plan,
    execute_program,
    estimate_program_cost,
)

from .distribution import (
    Distribution,
    UQMode,
    UQMetadata,
    propagate_distribution,
)

from .cache import (
    ProgramCache,
    CacheKey,
    graph_fingerprint,
    program_fingerprint,
    execution_fingerprint,
    environment_signature,
    get_global_cache,
    clear_global_cache,
)

from .diff import (
    ProgramDiff,
    DiffNode,
    DiffType,
    diff_programs,
)

from .explain import (
    ExplainResult,
    explain_program,
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
    # Rewrites
    "Match",
    "RewriteContext",
    "RuleGuard",
    "RewriteRule",
    "RewriteEngine",
    "apply_rewrites",
    "get_standard_rules",
    "get_aggressive_rules",
    "get_conservative_rules",
    # Cost Model
    "Cost",
    "CostModel",
    "CostObjective",
    "GraphStats",
    "parse_time_budget",
    "format_time_estimate",
    "format_memory_estimate",
    # Executor
    "ExecutionContext",
    "ExecutionPlan",
    "PlanStage",
    "BudgetExceededError",
    "ExecutionTimeoutError",
    "create_execution_plan",
    "execute_program",
    "estimate_program_cost",
    # Distribution
    "Distribution",
    "UQMode",
    "UQMetadata",
    "propagate_distribution",
    # Cache
    "ProgramCache",
    "CacheKey",
    "graph_fingerprint",
    "program_fingerprint",
    "execution_fingerprint",
    "environment_signature",
    "get_global_cache",
    "clear_global_cache",
    # Diff
    "ProgramDiff",
    "DiffNode",
    "DiffType",
    "diff_programs",
    # Explain
    "ExplainResult",
    "explain_program",
]
