"""DSL linting and analysis module.

This module provides static analysis and linting for DSL queries,
including type checking, schema validation, and performance hints.

Public API:
    lint(query, graph, schema) -> List[Diagnostic]
    explain(query, graph, schema) -> ExplainResult
"""

from typing import Any, List, Optional, Dict
from dataclasses import dataclass

from ..ast import Query
from .diagnostic import Diagnostic, SuggestedFix
from .schema import SchemaProvider, NetworkSchemaProvider, EntityRef
from .types import AttrType, TypeEnvironment
from .type_resolver import TypeResolver
from .lint_context import LintContext
from .rules import get_all_rules


@dataclass
class ExplainResult:
    """Result of an EXPLAIN query with linting information.
    
    Attributes:
        ast_summary: Human-readable summary of the AST
        type_info: Dictionary mapping node IDs to inferred types
        cost_estimate: Rough cost classification
        diagnostics: List of diagnostics from linting
        plan_steps: List of execution plan steps
    """
    ast_summary: str
    type_info: Dict[str, str]
    cost_estimate: str
    diagnostics: List[Diagnostic]
    plan_steps: List[str]


def lint(
    query: Query,
    graph: Optional[Any] = None,
    schema: Optional[SchemaProvider] = None,
) -> List[Diagnostic]:
    """Lint a DSL query.
    
    Analyzes the query for potential issues including:
    - Unknown layers or attributes
    - Type mismatches
    - Unsatisfiable or redundant predicates
    - Performance issues
    
    Args:
        query: Query AST to lint
        graph: Optional py3plex network for schema extraction
        schema: Optional schema provider (auto-created from graph if not provided)
        
    Returns:
        List of diagnostics found
        
    Example:
        >>> from py3plex.dsl import Q, L, lint
        >>> from py3plex.core import multinet
        >>> 
        >>> network = multinet.multi_layer_network()
        >>> # ... build network ...
        >>> 
        >>> query = Q.nodes().from_layers(L["social"]).where(degree__gt=5).build()
        >>> diagnostics = lint(query, graph=network)
        >>> 
        >>> for diag in diagnostics:
        ...     print(f"{diag.severity}: {diag.message}")
    """
    # Create schema from graph if needed
    if schema is None and graph is not None:
        schema = NetworkSchemaProvider(graph)
    
    # Run type resolution
    type_resolver = TypeResolver(schema)
    type_env = type_resolver.resolve(query)
    
    # Create lint context
    context = LintContext(
        query="",  # Could be enhanced to track original query string
        schema=schema,
        type_env=type_env,
    )
    
    # Run all lint rules
    diagnostics = []
    for rule in get_all_rules():
        try:
            rule_diagnostics = rule.apply(query, context)
            diagnostics.extend(rule_diagnostics)
        except Exception as e:
            # Log but don't fail on rule errors
            import logging
            logging.getLogger(__name__).warning(f"Error in rule {rule.code}: {e}")
    
    return diagnostics


def explain(
    query: Query,
    graph: Optional[Any] = None,
    schema: Optional[SchemaProvider] = None,
) -> ExplainResult:
    """Explain a DSL query with type information and cost estimates.
    
    Provides detailed information about:
    - Query structure (AST)
    - Inferred types for all expressions
    - Estimated execution cost
    - Potential issues (via linting)
    
    Args:
        query: Query AST to explain
        graph: Optional py3plex network for schema extraction
        schema: Optional schema provider
        
    Returns:
        ExplainResult with detailed query information
        
    Example:
        >>> result = explain(query, graph=network)
        >>> print(result.ast_summary)
        >>> print(f"Cost: {result.cost_estimate}")
        >>> for diag in result.diagnostics:
        ...     print(diag)
    """
    # Create schema from graph if needed
    if schema is None and graph is not None:
        schema = NetworkSchemaProvider(graph)
    
    # Run type resolution
    type_resolver = TypeResolver(schema)
    type_env = type_resolver.resolve(query)
    
    # Get diagnostics
    diagnostics = lint(query, graph, schema)
    
    # Build AST summary
    ast_summary = _build_ast_summary(query)
    
    # Build type info
    type_info = {}
    for attr, attr_type in type_env.attribute_types.items():
        type_info[f"attr:{attr}"] = attr_type.value
    for computed, computed_type in type_env.computed_types.items():
        type_info[f"computed:{computed}"] = computed_type.value
    
    # Estimate cost
    cost_estimate = _estimate_cost(query, schema)
    
    # Build plan steps
    plan_steps = _build_plan_steps(query)
    
    return ExplainResult(
        ast_summary=ast_summary,
        type_info=type_info,
        cost_estimate=cost_estimate,
        diagnostics=diagnostics,
        plan_steps=plan_steps,
    )


def _build_ast_summary(query: Query) -> str:
    """Build a human-readable summary of the AST."""
    lines = []
    
    if query.explain:
        lines.append("EXPLAIN mode: enabled")
    
    if query.select:
        select = query.select
        lines.append(f"Target: {select.target.value}")
        
        if select.layer_expr:
            layers = [t.name for t in select.layer_expr.terms]
            lines.append(f"Layers: {', '.join(layers)}")
        
        if select.where:
            lines.append(f"WHERE conditions: {len(select.where.atoms)} atom(s)")
        
        if select.compute:
            measures = [c.name for c in select.compute]
            lines.append(f"COMPUTE: {', '.join(measures)}")
        
        if select.order_by:
            keys = [o.key for o in select.order_by]
            lines.append(f"ORDER BY: {', '.join(keys)}")
        
        if select.limit:
            lines.append(f"LIMIT: {select.limit}")
    
    return "\n".join(lines)


def _estimate_cost(query: Query, schema: Optional[SchemaProvider]) -> str:
    """Estimate query execution cost."""
    if not query.select:
        return "O(1)"
    
    select = query.select
    
    # Get counts if schema available
    if schema:
        node_count = schema.get_node_count()
        edge_count = schema.get_edge_count()
    else:
        node_count = 1000  # Default estimate
        edge_count = 5000
    
    # Base cost
    if select.where:
        base_cost = "O(V)" if select.target.value == "nodes" else "O(E)"
    else:
        base_cost = "O(V)" if select.target.value == "nodes" else "O(E)"
    
    # Add compute cost
    if select.compute:
        for compute in select.compute:
            if compute.name in ("betweenness_centrality", "betweenness"):
                return f"O(V * E) ≈ O({node_count * edge_count})"
            elif compute.name in ("closeness_centrality", "closeness"):
                return f"O(V²) ≈ O({node_count * node_count})"
    
    # Add sorting cost
    if select.order_by:
        return f"{base_cost} + O(n log n) sorting"
    
    return base_cost


def _build_plan_steps(query: Query) -> List[str]:
    """Build execution plan steps."""
    steps = []
    
    if not query.select:
        return steps
    
    select = query.select
    
    steps.append(f"1. Select {select.target.value}")
    
    if select.layer_expr:
        layers = [t.name for t in select.layer_expr.terms]
        steps.append(f"2. Filter by layers: {', '.join(layers)}")
    
    if select.where:
        steps.append(f"3. Apply WHERE conditions ({len(select.where.atoms)} condition(s))")
    
    if select.compute:
        for i, compute in enumerate(select.compute, 1):
            steps.append(f"{len(steps)+1}. Compute {compute.name}")
    
    if select.order_by:
        steps.append(f"{len(steps)+1}. Sort results")
    
    if select.limit:
        steps.append(f"{len(steps)+1}. Limit to {select.limit} results")
    
    return steps


__all__ = [
    # Main API
    "lint",
    "explain",
    "ExplainResult",
    # Core types
    "Diagnostic",
    "SuggestedFix",
    "SchemaProvider",
    "NetworkSchemaProvider",
    "EntityRef",
    "AttrType",
    "TypeEnvironment",
    "TypeResolver",
    "LintContext",
]
