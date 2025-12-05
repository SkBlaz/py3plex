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
    >>> result = q.execute(network, k=5)
    >>> df = result.to_pandas()
    >>> 
    >>> # Compare two networks
    >>> comparison = C.compare("baseline", "treatment").using("multiplex_jaccard").execute(networks)
    >>> 
    >>> # Generate null models
    >>> nullmodels = N.configuration().samples(100).seed(42).execute(network)
    >>> 
    >>> # Find paths
    >>> paths = P.shortest("Alice", "Bob").crossing_layers().execute(network)

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

from .ast import (
    # Core AST nodes
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
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    # Execution plan
    PlanStep,
    ExecutionPlan,
    # DSL Extensions AST nodes
    CompareStmt,
    NullModelStmt,
    PathStmt,
    ExtendedQuery,
)

from .builder import (
    Q,
    QueryBuilder,
    LayerExprBuilder,
    LayerProxy,
    L,
    Param,
    # DSL Extensions builders
    C,
    CompareBuilder,
    N,
    NullModelBuilder,
    P,
    PathBuilder,
)

from .result import QueryResult

from .executor import execute_ast

from .errors import (
    DslError,
    DslSyntaxError,
    DslExecutionError,
    UnknownAttributeError,
    UnknownMeasureError,
    UnknownLayerError,
    ParameterMissingError,
    TypeMismatchError,
)

from .registry import measure_registry

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
    "PlanStep",
    "ExecutionPlan",
    # DSL Extensions AST
    "CompareStmt",
    "NullModelStmt",
    "PathStmt",
    "ExtendedQuery",
    # Builder
    "Q",
    "QueryBuilder",
    "LayerExprBuilder",
    "LayerProxy",
    "L",
    "Param",
    # DSL Extensions Builders
    "C",
    "CompareBuilder",
    "N",
    "NullModelBuilder",
    "P",
    "PathBuilder",
    # Result
    "QueryResult",
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
    # Registry
    "measure_registry",
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
