"""DSL v2 for Multilayer Network Queries.

This module provides a Domain-Specific Language (DSL) version 2 for querying and
analyzing multilayer networks. DSL v2 introduces:

1. Unified AST representation
2. Pythonic builder API (Q, L, Param)
3. Multilayer-specific abstractions (layer algebra, intralayer/interlayer)
4. Improved ergonomics (ORDER BY, LIMIT, EXPLAIN, rich results)

DSL Extensions (v2.1):
5. Network comparison (C.compare())
6. Null models (N.model())
7. Path queries (P.shortest(), P.random_walk())
8. Plugin system for user-defined operators (@dsl_operator)

Example Usage:
    >>> from py3plex.dsl import Q, L, Param, C, N, P
    >>>
    >>> # Build a query using the builder API
    >>> q = (
    ...     Q.nodes()
    ...      .from_layers(L["social"] + L["work"])
    ...      .where(intralayer=True, degree__gt=5)
    ...      .compute("betweenness_centrality", alias="bc")
    ...      .order_by("bc", desc=True)
    ...      .limit(20)
    ... )
    >>>
    >>> # Execute the query
    >>> result = q.execute(network, k=5)  # doctest: +SKIP
    >>> df = result.to_pandas()  # doctest: +SKIP
    >>>
    >>> # Compare two networks
    >>> comparison = C.compare("baseline", "treatment").using("multiplex_jaccard").execute(networks)  # doctest: +SKIP
    >>>
    >>> # Generate null models
    >>> nullmodels = N.configuration().samples(100).seed(42).execute(network)  # doctest: +SKIP
    >>>
    >>> # Find paths
    >>> paths = P.shortest("Alice", "Bob").crossing_layers().execute(network)  # doctest: +SKIP
    >>>
    >>> # Define custom operators
    >>> @dsl_operator("my_measure")
    ... def my_custom_measure(context, param: float = 1.0):
    ...     # Use context.graph, context.current_layers, etc.
    ...     return result

The DSL also supports a string syntax:
    SELECT nodes
    FROM LAYER("social") + LAYER("work")
    WHERE intralayer AND degree > 5
    COMPUTE betweenness_centrality AS bc
    ORDER BY bc DESC
    LIMIT 20
    TO pandas

All frontends (string DSL, builder API) compile into a single AST which is
executed by the same engine, ensuring consistent behavior.
"""

from typing import Any, Dict, Optional

from .ast import (
    # Core AST nodes
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    ExportSpec,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    FunctionCall,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    TemporalContext,
    UQConfig,
    # Execution plan
    PlanStep,
    ExecutionPlan,
    # DSL Extensions AST nodes
    CompareStmt,
    NullModelStmt,
    PathStmt,
    DynamicsStmt,
    TrajectoriesStmt,
    ExtendedQuery,
)

from .builder import (
    Q,
    QueryBuilder,
    LayerExprBuilder,
    LayerProxy,
    L,
    Param,
    UQ,
    # DSL Extensions builders
    C,
    CompareBuilder,
    N,
    NullModelBuilder,
    P,
    PathBuilder,
    # Dynamics builders
    DynamicsBuilder,
    TrajectoriesBuilder,
)

from .layers import (
    LayerSet,
    LayerExpr as LayerSetExpr,
)

# Import pattern matching components
from .patterns import (
    PatternNode,
    PatternEdge,
    PatternGraph,
    MatchRow,
    LayerConstraint,
    EdgeLayerConstraint,
    Predicate,
    PatternQueryBuilder,
    PatternNodeBuilder,
    PatternEdgeBuilder,
    PatternQueryResult,
    PatternPlan,
    compile_pattern,
    match_pattern,
)

from .expressions import (
    F,
    FieldExpression,
    BooleanExpression,
    FieldProxy,
)

from .result import QueryResult

from .executor import execute_ast
from .export import export_result

from .errors import (
    DslError,
    DslSyntaxError,
    DslExecutionError,
    UnknownAttributeError,
    UnknownMeasureError,
    UnknownLayerError,
    ParameterMissingError,
    TypeMismatchError,
    GroupingError,
    DslMissingMetricError,
)

from .registry import measure_registry

from .operator_registry import (
    DSLOperator,
    operator_registry,
    register_operator,
    get_operator,
    list_operators,
    unregister_operator,
)

from .context import DSLExecutionContext

# Import lint module
from .lint import (
    lint,
    explain,
    ExplainResult,
    Diagnostic,
    SuggestedFix,
    SchemaProvider,
    NetworkSchemaProvider,
    EntityRef,
    AttrType,
    TypeEnvironment,
)

# Import legacy functions for backward compatibility
from py3plex.dsl_legacy import (
    execute_query,
    format_result,
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer,
    DSLSyntaxError,
    DSLExecutionError,
    detect_communities,
    get_community_partition,
    get_biggest_community,
    get_smallest_community,
    get_num_communities,
    get_community_sizes,
    get_community_size_distribution,
    # Pattern parsing functions for tests
    _tokenize_query,
    _parse_condition,
    _parse_where_clause,
    _evaluate_condition,
    _evaluate_conditions,
    _compute_measure,
    _parse_node_pattern,
    _parse_edge_pattern,
    _parse_path_pattern,
    _parse_layer_clause,
    _parse_return_clause,
    _tokenize_match_pattern,
)

__all__ = [
    # AST
    "Query",
    "SelectStmt",
    "Target",
    "ExportTarget",
    "ExportSpec",
    "LayerExpr",
    "LayerTerm",
    "ConditionExpr",
    "ConditionAtom",
    "Comparison",
    "FunctionCall",
    "SpecialPredicate",
    "ComputeItem",
    "OrderItem",
    "ParamRef",
    "TemporalContext",
    "UQConfig",
    "PlanStep",
    "ExecutionPlan",
    # DSL Extensions AST
    "CompareStmt",
    "NullModelStmt",
    "PathStmt",
    "DynamicsStmt",
    "TrajectoriesStmt",
    "ExtendedQuery",
    # Builder
    "Q",
    "QueryBuilder",
    "LayerExprBuilder",
    "LayerProxy",
    "L",
    "LayerSet",
    "LayerSetExpr",
    "Param",
    "UQ",
    # DSL Extensions Builders
    "C",
    "CompareBuilder",
    "N",
    "NullModelBuilder",
    "P",
    "PathBuilder",
    # Dynamics Builders
    "DynamicsBuilder",
    "TrajectoriesBuilder",
    # Pattern Matching
    "PatternNode",
    "PatternEdge",
    "PatternGraph",
    "MatchRow",
    "LayerConstraint",
    "EdgeLayerConstraint",
    "Predicate",
    "PatternQueryBuilder",
    "PatternNodeBuilder",
    "PatternEdgeBuilder",
    "PatternQueryResult",
    "PatternPlan",
    "compile_pattern",
    "match_pattern",
    # Expression Builder
    "F",
    "FieldExpression",
    "BooleanExpression",
    "FieldProxy",
    # Result
    "QueryResult",
    "export_result",
    # Executor
    "execute_ast",
    # Errors (v2)
    "DslError",
    "DslSyntaxError",
    "DslExecutionError",
    "UnknownAttributeError",
    "UnknownMeasureError",
    "UnknownLayerError",
    "ParameterMissingError",
    "TypeMismatchError",
    "GroupingError",
    "DslMissingMetricError",
    # Registry
    "measure_registry",
    # Operator Registry
    "DSLOperator",
    "operator_registry",
    "register_operator",
    "get_operator",
    "list_operators",
    "unregister_operator",
    "dsl_operator",
    "describe_operator",
    # Execution Context
    "DSLExecutionContext",
    # Linting and Analysis
    "lint",
    "explain",
    "ExplainResult",
    "Diagnostic",
    "SuggestedFix",
    "SchemaProvider",
    "NetworkSchemaProvider",
    "EntityRef",
    "AttrType",
    "TypeEnvironment",
    # Legacy functions (backward compatibility)
    "execute_query",
    "format_result",
    "select_nodes_by_layer",
    "select_high_degree_nodes",
    "compute_centrality_for_layer",
    "DSLSyntaxError",
    "DSLExecutionError",
    "detect_communities",
    "get_community_partition",
    "get_biggest_community",
    "get_smallest_community",
    "get_num_communities",
    "get_community_sizes",
    "get_community_size_distribution",
]

# DSL version for metadata and backwards compatibility
DSL_VERSION = "2.1"


# ============================================================================
# Public API: DSL Operator Decorator
# ============================================================================


def dsl_operator(
    name: Optional[str] = None,
    *,
    description: Optional[str] = None,
    category: Optional[str] = None,
    overwrite: bool = False,
):
    """Decorator to register a Python function as a DSL operator.

    This decorator allows users to define custom operators that can be used
    in DSL queries. The decorated function should accept a DSLExecutionContext
    as its first argument, followed by any keyword arguments.

    Args:
        name: Operator name (defaults to function name if not provided)
        description: Human-readable description (defaults to function docstring)
        category: Optional category for organization (e.g., "centrality", "dynamics")
        overwrite: If True, allow replacing existing operators

    Returns:
        Decorator function that registers the operator

    Example:
        >>> @dsl_operator("layer_resilience", category="dynamics", overwrite=True)
        ... def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1):
        ...     '''Compute resilience score for current layers.'''
        ...     # Access context.graph, context.current_layers, etc.
        ...     return 42.0

        >>> # Use in DSL:
        >>> # measure layer_resilience(alpha=0.2) on layers ["infra", "power"]
    """
    def decorator(func):
        op_name = name or func.__name__
        op_description = description or func.__doc__

        register_operator(
            name=op_name,
            func=func,
            description=op_description,
            category=category,
            overwrite=overwrite,
        )

        return func

    return decorator


def describe_operator(name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a registered operator.

    Args:
        name: Operator name

    Returns:
        Dictionary with operator metadata, or None if not found

    Example:
        >>> @dsl_operator("layer_resilience", description="Compute resilience score for current layers.", overwrite=True)
        ... def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1):
        ...     return 42.0
        >>> info = describe_operator("layer_resilience")
        >>> info["description"]
        'Compute resilience score for current layers.'
    """
    op = get_operator(name)
    if op is None:
        return None

    return {
        "name": op.name,
        "description": op.description,
        "category": op.category,
        "function": op.func.__name__,
    }
