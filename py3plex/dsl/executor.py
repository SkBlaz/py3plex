"""Query executor for DSL v2.

This module provides the execution engine that runs AST queries against
multilayer networks. It supports temporal queries via the TemporalMultinetView wrapper.
"""

from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Union
import networkx as nx

from .ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    PlanStep,
    ExecutionPlan,
    TemporalContext,
)
from .result import QueryResult
from .registry import measure_registry
from .operator_registry import get_operator
from .context import DSLExecutionContext
from .errors import (
    DslExecutionError,
    ParameterMissingError,
    UnknownLayerError,
    UnknownMeasureError,
)


def execute_ast(network: Any, query: Query, params: Optional[Dict[str, Any]] = None) -> Union[QueryResult, ExecutionPlan]:
    """Execute an AST query on a multilayer network.
    
    Args:
        network: Multilayer network object
        query: Query AST
        params: Parameter bindings
        
    Returns:
        QueryResult or ExecutionPlan (if explain=True)
    """
    params = params or {}
    
    # Step 1: Parameter binding
    bound_query = _bind_parameters(query, params)
    
    # Step 2: Check for EXPLAIN mode
    if bound_query.explain:
        return _build_execution_plan(network, bound_query)
    
    # Step 3: Wrap network in temporal view if needed
    actual_network = _apply_temporal_context(network, bound_query.select.temporal_context)
    
    # Step 4: Execute SELECT statement
    return _execute_select(actual_network, bound_query.select)


def _apply_temporal_context(network: Any, temporal_context: Optional[TemporalContext]) -> Any:
    """Apply temporal filtering to network if temporal context exists.
    
    Args:
        network: Base multilayer network
        temporal_context: Optional temporal context from query
        
    Returns:
        TemporalMultinetView if temporal context exists, otherwise original network
    """
    if temporal_context is None:
        return network
    
    # Import here to avoid circular dependencies
    from py3plex.temporal_view import TemporalMultinetView
    
    # Create temporal view
    view = TemporalMultinetView(network)
    
    # Apply temporal slice based on context kind
    if temporal_context.kind == "at":
        # Point-in-time snapshot
        if temporal_context.t0 is not None:
            return view.snapshot_at(temporal_context.t0)
        else:
            raise DslExecutionError("AT clause requires a timestamp")
    
    elif temporal_context.kind == "during":
        # Time range
        return view.with_slice(temporal_context.t0, temporal_context.t1)
    
    else:
        raise DslExecutionError(f"Unknown temporal context kind: {temporal_context.kind}")
    
    return view


def _bind_parameters(query: Query, params: Dict[str, Any]) -> Query:
    """Bind parameters in the query AST.
    
    Traverses the AST and replaces ParamRef nodes with actual values.
    """
    # For now, we'll handle parameter binding during condition evaluation
    # This is a simpler approach that works for the current implementation
    return query


def _resolve_param(value: Any, params: Dict[str, Any]) -> Any:
    """Resolve a value, replacing ParamRef with actual value if needed."""
    if isinstance(value, ParamRef):
        if value.name not in params:
            raise ParameterMissingError(value.name, list(params.keys()))
        return params[value.name]
    return value


def _build_execution_plan(network: Any, query: Query) -> ExecutionPlan:
    """Build an execution plan for EXPLAIN queries."""
    steps: List[PlanStep] = []
    warnings: List[str] = []
    
    select = query.select
    
    # Get node/edge counts for complexity estimation
    node_count = 0
    edge_count = 0
    if hasattr(network, 'core_network') and network.core_network:
        node_count = network.core_network.number_of_nodes()
        edge_count = network.core_network.number_of_edges()
    
    # Step 1: Target selection
    if select.target == Target.NODES:
        steps.append(PlanStep(
            f"Select all nodes from network",
            f"O(|V|) = O({node_count})"
        ))
    else:
        steps.append(PlanStep(
            f"Select all edges from network",
            f"O(|E|) = O({edge_count})"
        ))
    
    # Step 2: Layer filtering
    if select.layer_expr:
        layer_names = [t.name for t in select.layer_expr.terms]
        steps.append(PlanStep(
            f"Filter by layers: {', '.join(layer_names)}",
            "O(|V|)" if select.target == Target.NODES else "O(|E|)"
        ))
    
    # Step 3: Condition filtering
    if select.where:
        steps.append(PlanStep(
            f"Apply WHERE conditions ({len(select.where.atoms)} conditions)",
            "O(|V|)" if select.target == Target.NODES else "O(|E|)"
        ))
    
    # Step 4: Compute measures
    for compute in select.compute:
        complexity = _get_measure_complexity(compute.name, node_count, edge_count)
        steps.append(PlanStep(
            f"Compute {compute.name}" + (f" AS {compute.alias}" if compute.alias else ""),
            complexity
        ))
        
        # Add warnings for expensive operations
        if compute.name in ("betweenness_centrality", "betweenness"):
            if node_count > 10000:
                warnings.append(
                    f"Graph has ~{node_count} nodes; betweenness_centrality might be slow. "
                    "Consider sampling or approximate methods."
                )
    
    # Step 5: Ordering
    if select.order_by:
        keys = [f"{o.key} {'DESC' if o.desc else 'ASC'}" for o in select.order_by]
        steps.append(PlanStep(
            f"Order by: {', '.join(keys)}",
            "O(n log n)"
        ))
    
    # Step 6: Limit
    if select.limit:
        steps.append(PlanStep(
            f"Limit to {select.limit} results",
            "O(1)"
        ))
    
    return ExecutionPlan(steps=steps, warnings=warnings)


def _get_measure_complexity(measure: str, n: int, m: int) -> str:
    """Get complexity estimate for a measure."""
    complexities = {
        "degree": f"O(|V|) = O({n})",
        "degree_centrality": f"O(|V|) = O({n})",
        "betweenness_centrality": f"O(|V||E|) = O({n * m})",
        "betweenness": f"O(|V||E|) = O({n * m})",
        "closeness_centrality": f"O(|V|²) = O({n * n})",
        "closeness": f"O(|V|²) = O({n * n})",
        "eigenvector_centrality": f"O(|V| + |E|) iterations = O({n + m})",
        "eigenvector": f"O(|V| + |E|) iterations = O({n + m})",
        "pagerank": f"O(|V| + |E|) iterations = O({n + m})",
        "clustering": f"O(|V| * d²) where d=avg degree",
        "communities": f"O(|V| log |V|)",
        "community": f"O(|V| log |V|)",
    }
    return complexities.get(measure, "Unknown")


def _execute_select(network: Any, select: SelectStmt) -> QueryResult:
    """Execute a SELECT statement."""
    # Get core network
    if not hasattr(network, 'core_network') or network.core_network is None:
        return QueryResult(
            target=select.target.value,
            items=[],
            attributes={},
            meta={"dsl_version": "2.0", "warning": "Network has no core_network"}
        )
    
    G = network.core_network
    
    # Step 1: Get initial items
    if select.target == Target.NODES:
        items = list(network.get_nodes())
    else:
        items = list(network.get_edges())
    
    # Step 2: Apply layer filter
    if select.layer_expr:
        active_layers = _evaluate_layer_expr(select.layer_expr, network)
        items = _filter_by_layers(items, active_layers, select.target)
    
    # Step 3: Apply WHERE conditions
    if select.where:
        items = _filter_by_conditions(items, select.where, network, G)
    
    # Step 4: Compute measures
    attributes: Dict[str, Dict] = {}
    if select.compute and select.target == Target.NODES:
        # Create subgraph for computation
        subgraph = G.subgraph([item for item in items if item in G]).copy()
        
        # Build execution context for operators
        active_layers = None
        if select.layer_expr:
            active_layers = list(_evaluate_layer_expr(select.layer_expr, network))
        
        context = DSLExecutionContext(
            graph=network,
            current_layers=active_layers,
            current_nodes=items,
            params={},
        )
        
        for compute_item in select.compute:
            try:
                # First, try to resolve from operator registry
                operator = get_operator(compute_item.name)
                if operator is not None:
                    # Call custom operator with context
                    result = operator.func(context)
                    result_name = compute_item.result_name
                    
                    # Convert result to dict if it's not already
                    if isinstance(result, dict):
                        attributes[result_name] = result
                    else:
                        # If result is a scalar, assign it to all nodes
                        attributes[result_name] = {node: result for node in items}
                else:
                    # Fall back to measure registry (built-in measures)
                    measure_fn = measure_registry.get(compute_item.name)
                    values = measure_fn(subgraph, items)
                    result_name = compute_item.result_name
                    attributes[result_name] = values
            except UnknownMeasureError:
                # Re-raise unknown measure errors (they have helpful suggestions)
                raise
            except Exception as e:
                # Log specific error and continue with other measures
                import logging
                logging.getLogger(__name__).warning(
                    f"Error computing measure '{compute_item.name}': {e}"
                )
                attributes[compute_item.result_name] = {}
    
    # Step 5: Apply ORDER BY
    if select.order_by:
        items = _apply_ordering(items, select.order_by, attributes)
    
    # Step 6: Apply LIMIT
    if select.limit is not None:
        items = items[:select.limit]
    
    # Create result
    result = QueryResult(
        target=select.target.value,
        items=items,
        attributes=attributes,
        meta={"dsl_version": "2.0"}
    )
    
    # Step 7: Apply file export if specified
    if select.file_export:
        from .export import export_result
        export_result(result, select.file_export)
    
    # Step 8: Apply export if specified (for result format conversion)
    if select.export:
        if select.export == ExportTarget.PANDAS:
            return result.to_pandas()
        elif select.export == ExportTarget.NETWORKX:
            return result.to_networkx(network)
        elif select.export == ExportTarget.ARROW:
            return result.to_arrow()
    
    return result


def _evaluate_layer_expr(layer_expr: LayerExpr, network: Any) -> Set[str]:
    """Evaluate a layer expression to get the set of active layers.
    
    Supports:
        - Union (+): L["a"] + L["b"] → {"a", "b"}
        - Difference (-): L["a"] - L["b"] → {"a"} - {"b"}
        - Intersection (&): L["a"] & L["b"] → {"a"} ∩ {"b"}
    """
    if not layer_expr.terms:
        return set()
    
    # Start with first term
    result = {layer_expr.terms[0].name}
    
    # Apply operations
    for i, op in enumerate(layer_expr.ops):
        next_term = layer_expr.terms[i + 1].name
        
        if op == "+":
            result.add(next_term)
        elif op == "-":
            result.discard(next_term)
        elif op == "&":
            if next_term in result:
                result = {next_term}
            else:
                result = set()
    
    return result


def _filter_by_layers(items: List[Any], active_layers: Set[str], target: Target) -> List[Any]:
    """Filter items by layer membership."""
    if target == Target.NODES:
        # Nodes are tuples (node_id, layer)
        return [item for item in items 
                if isinstance(item, tuple) and len(item) >= 2 and item[1] in active_layers]
    else:
        # Edges are tuples of node tuples
        filtered = []
        for item in items:
            if isinstance(item, tuple) and len(item) >= 2:
                source, target_node = item[0], item[1]
                if isinstance(source, tuple) and isinstance(target_node, tuple):
                    if len(source) >= 2 and len(target_node) >= 2:
                        if source[1] in active_layers or target_node[1] in active_layers:
                            filtered.append(item)
        return filtered


def _filter_by_conditions(items: List[Any], conditions: ConditionExpr,
                          network: Any, G: nx.Graph) -> List[Any]:
    """Filter items by WHERE conditions."""
    result = []
    
    for item in items:
        if _evaluate_conditions(item, conditions, network, G):
            result.append(item)
    
    return result


def _evaluate_conditions(item: Any, conditions: ConditionExpr,
                         network: Any, G: nx.Graph) -> bool:
    """Evaluate all conditions for an item."""
    if not conditions.atoms:
        return True
    
    # Evaluate first condition
    result = _evaluate_atom(item, conditions.atoms[0], network, G)
    
    # Apply logical operators
    for i, op in enumerate(conditions.ops):
        next_result = _evaluate_atom(item, conditions.atoms[i + 1], network, G)
        
        if op == "AND":
            result = result and next_result
        elif op == "OR":
            result = result or next_result
    
    return result


def _evaluate_atom(item: Any, atom: ConditionAtom, network: Any, G: nx.Graph) -> bool:
    """Evaluate a single condition atom."""
    if atom.comparison:
        return _evaluate_comparison(item, atom.comparison, network, G)
    elif atom.special:
        return _evaluate_special(item, atom.special, network, G)
    elif atom.function:
        # Function calls would need more complex handling
        return True
    return True


def _evaluate_comparison(item: Any, comparison: Comparison,
                         network: Any, G: nx.Graph) -> bool:
    """Evaluate a comparison condition."""
    # Get actual value
    actual_value = _get_attribute_value(item, comparison.left, network, G)
    
    if actual_value is None:
        return False
    
    # Get expected value (resolve param if needed)
    expected_value = comparison.right
    
    # Compare
    op = comparison.op
    
    if op == "=":
        return str(actual_value) == str(expected_value)
    elif op == "!=":
        return str(actual_value) != str(expected_value)
    elif op == ">":
        try:
            return float(actual_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == "<":
        try:
            return float(actual_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == ">=":
        try:
            return float(actual_value) >= float(expected_value)
        except (ValueError, TypeError):
            return False
    elif op == "<=":
        try:
            return float(actual_value) <= float(expected_value)
        except (ValueError, TypeError):
            return False
    
    return False


def _evaluate_special(item: Any, special: SpecialPredicate,
                      network: Any, G: nx.Graph) -> bool:
    """Evaluate a special predicate."""
    if special.kind == "intralayer":
        # For edges: check if source and target are in same layer
        if isinstance(item, tuple) and len(item) >= 2:
            source, target = item[0], item[1]
            if isinstance(source, tuple) and isinstance(target, tuple):
                if len(source) >= 2 and len(target) >= 2:
                    return source[1] == target[1]
        return False
    
    elif special.kind == "interlayer":
        # For edges: check if source is in src_layer and target is in dst_layer
        src_layer = special.params.get("src")
        dst_layer = special.params.get("dst")
        
        if isinstance(item, tuple) and len(item) >= 2:
            source, target = item[0], item[1]
            if isinstance(source, tuple) and isinstance(target, tuple):
                if len(source) >= 2 and len(target) >= 2:
                    return source[1] == src_layer and target[1] == dst_layer
        return False
    
    return True


def _get_attribute_value(item: Any, attribute: str, network: Any, G: nx.Graph) -> Any:
    """Get an attribute value from a node or edge."""
    # Handle nodes (tuples of (node_id, layer))
    if isinstance(item, tuple) and len(item) >= 2:
        node_id, layer = item[0], item[1]
        
        if attribute == "layer":
            return str(layer)
        
        if attribute == "degree":
            if item in G:
                return G.degree(item)
            return 0
        
        # Try to get from node attributes
        if item in G:
            node_data = G.nodes.get(item, {})
            if attribute in node_data:
                return node_data[attribute]
    
    return None


def _apply_ordering(items: List[Any], order_by: List[OrderItem],
                    attributes: Dict[str, Dict]) -> List[Any]:
    """Apply ORDER BY to items."""
    if not order_by:
        return items
    
    def sort_key(item):
        values = []
        for order_item in order_by:
            key = order_item.key
            
            # Get value from computed attributes
            if key in attributes:
                value = attributes[key].get(item, 0)
            else:
                value = 0
            
            # Negate for descending
            if order_item.desc and isinstance(value, (int, float)):
                value = -value
            
            values.append(value)
        
        return tuple(values)
    
    return sorted(items, key=sort_key)
