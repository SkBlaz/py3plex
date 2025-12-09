"""Query executor for DSL v2.

This module provides the execution engine that runs AST queries against
multilayer networks. It supports temporal queries via the TemporalMultinetView wrapper.
"""

import copy
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
    
    # Step 4: Execute SELECT statement (pass params for dynamic resolution)
    return _execute_select(actual_network, bound_query.select, params)


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
    # Create a deep copy of the query to avoid mutating the original
    bound_query = copy.deepcopy(query)
    
    # Bind limit parameter if it's a ParamRef
    if bound_query.select and bound_query.select.limit is not None:
        bound_query.select.limit = _resolve_param(bound_query.select.limit, params)
    
    # Note: WHERE conditions are resolved dynamically during evaluation
    # This allows for more flexible parameter handling
    return bound_query


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
    
    # Step 5: Grouping and coverage
    if select.group_by:
        steps.append(PlanStep(
            f"Group results by: {', '.join(select.group_by)}",
            "O(n)"
        ))
    
    if select.limit_per_group is not None:
        steps.append(PlanStep(
            f"Apply top-{select.limit_per_group} per group",
            "O(n log n)"
        ))
    
    if select.coverage_mode:
        mode_desc = select.coverage_mode
        if select.coverage_k is not None:
            mode_desc = f"{select.coverage_mode} (k={select.coverage_k})"
        steps.append(PlanStep(
            f"Apply coverage filter across groups (mode='{mode_desc}')",
            "O(n)"
        ))
    
    # Step 6: Ordering (when not using grouping)
    if select.order_by and not select.group_by:
        keys = [f"{o.key} {'DESC' if o.desc else 'ASC'}" for o in select.order_by]
        steps.append(PlanStep(
            f"Order by: {', '.join(keys)}",
            "O(n log n)"
        ))
    
    # Step 7: Limit
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


def _execute_select(network: Any, select: SelectStmt, params: Optional[Dict[str, Any]] = None) -> QueryResult:
    """Execute a SELECT statement.
    
    Args:
        network: Multilayer network
        select: SELECT statement AST
        params: Parameter bindings for dynamic resolution
    """
    params = params or {}
    
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
        # Get edges with data to access attributes like weight
        items = list(network.get_edges(data=True))
    
    # Step 2: Apply layer filter
    if select.layer_expr:
        active_layers = _evaluate_layer_expr(select.layer_expr, network)
        items = _filter_by_layers(items, active_layers, select.target)
    
    # Step 3: Apply WHERE conditions
    if select.where:
        items = _filter_by_conditions(items, select.where, network, G, params)
    
    # Step 4: Compute measures
    attributes: Dict[str, Dict] = {}
    if select.compute:
        if select.target == Target.NODES:
            # Node measures - existing implementation
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
        else:
            # Edge measures - new implementation
            for compute_item in select.compute:
                try:
                    # Check if this is an edge-specific measure
                    measure_fn = measure_registry.get(compute_item.name, target="edges")
                    result_name = compute_item.result_name
                    
                    # Compute the measure on edges
                    values = measure_fn(G, items)
                    attributes[result_name] = values
                except UnknownMeasureError:
                    # Re-raise with context that this is an edge query
                    raise
                except DslExecutionError:
                    # Re-raise DSL execution errors (e.g., wrong target)
                    raise
                except Exception as e:
                    # Log specific error and continue with other measures
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Error computing edge measure '{compute_item.name}': {e}"
                    )
                    attributes[compute_item.result_name] = {}
    
    # Step 4.5: Apply grouping, per-group operations, and coverage filtering
    if select.group_by or select.limit_per_group is not None or select.coverage_mode:
        items = _apply_grouping_and_coverage(
            items=items,
            select=select,
            network=network,
            G=G,
            attributes=attributes,
        )
        # Skip global ORDER BY when grouping is used (ordering is per-group)
    else:
        # Step 5: Apply global ORDER BY (only when not grouping)
        if select.order_by:
            items = _apply_ordering(items, select.order_by, attributes)
    
    # Step 6: Apply global LIMIT
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


def _expand_layer_term(name: str, network: Any) -> Set[str]:
    """Expand a single layer term, handling wildcards.
    
    Args:
        name: Layer name or "*" for all layers
        network: Multilayer network object
        
    Returns:
        Set of layer names
    """
    if name == "*":
        # Expand wildcard to all layers in the network
        if hasattr(network, "layers"):
            return {str(l) for l in network.layers}
        # Fallback: derive layers from nodes
        if hasattr(network, "get_nodes"):
            return {str(layer) for (_, layer) in network.get_nodes()}
        return set()
    return {name}


def _evaluate_layer_expr(layer_expr: LayerExpr, network: Any) -> Set[str]:
    """Evaluate a layer expression to get the set of active layers.
    
    Supports:
        - Wildcard: L["*"] → all layers in network
        - Union (+): L["a"] + L["b"] → {"a", "b"}
        - Difference (-): L["a"] - L["b"] → {"a"} - {"b"}
        - Intersection (&): L["a"] & L["b"] → {"a"} ∩ {"b"}
        - Combined: L["*"] - L["foo"] → all layers except "foo"
    """
    if not layer_expr.terms:
        return set()
    
    # Start with first term (expanded if wildcard)
    result = _expand_layer_term(layer_expr.terms[0].name, network)
    
    # Apply operations
    for i, op in enumerate(layer_expr.ops):
        other = _expand_layer_term(layer_expr.terms[i + 1].name, network)
        
        if op == "+":
            result |= other
        elif op == "-":
            result -= other
        elif op == "&":
            result &= other
    
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
                          network: Any, G: nx.Graph, params: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Filter items by WHERE conditions."""
    params = params or {}
    result = []
    
    for item in items:
        if _evaluate_conditions(item, conditions, network, G, params):
            result.append(item)
    
    return result


def _evaluate_conditions(item: Any, conditions: ConditionExpr,
                         network: Any, G: nx.Graph, params: Optional[Dict[str, Any]] = None) -> bool:
    """Evaluate all conditions for an item."""
    params = params or {}
    
    if not conditions.atoms:
        return True
    
    # Evaluate first condition
    result = _evaluate_atom(item, conditions.atoms[0], network, G, params)
    
    # Apply logical operators
    for i, op in enumerate(conditions.ops):
        next_result = _evaluate_atom(item, conditions.atoms[i + 1], network, G, params)
        
        if op == "AND":
            result = result and next_result
        elif op == "OR":
            result = result or next_result
    
    return result


def _evaluate_atom(item: Any, atom: ConditionAtom, network: Any, G: nx.Graph, 
                   params: Optional[Dict[str, Any]] = None) -> bool:
    """Evaluate a single condition atom."""
    params = params or {}
    
    if atom.comparison:
        return _evaluate_comparison(item, atom.comparison, network, G, params)
    elif atom.special:
        return _evaluate_special(item, atom.special, network, G)
    elif atom.function:
        # Function calls would need more complex handling
        return True
    return True


def _evaluate_comparison(item: Any, comparison: Comparison,
                         network: Any, G: nx.Graph, params: Optional[Dict[str, Any]] = None) -> bool:
    """Evaluate a comparison condition."""
    params = params or {}
    
    # Get actual value
    actual_value = _get_attribute_value(item, comparison.left, network, G)
    
    if actual_value is None:
        return False
    
    # Get expected value (resolve param if needed)
    expected_value = _resolve_param(comparison.right, params)
    
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
    """Get an attribute value from a node or edge.
    
    For nodes (tuples of (node_id, layer)):
        - 'layer': returns the layer name
        - 'degree': returns node degree
        - other: looks up node attributes
    
    For edges (tuples of ((node_id, layer), (node_id, layer), {data})):
        - 'source_layer': returns source node's layer
        - 'target_layer': returns target node's layer
        - 'layer': returns source layer (for intralayer edges) or None
        - 'weight': returns edge weight (default 1.0)
        - other: looks up edge attributes
    """
    # Check if this is an edge (tuple with 2 node tuples as first elements)
    if isinstance(item, tuple) and len(item) >= 2:
        first_elem = item[0]
        second_elem = item[1]
        
        # Check if this is an edge: ((node, layer), (node, layer), {data}?)
        if isinstance(first_elem, tuple) and isinstance(second_elem, tuple):
            if len(first_elem) >= 2 and len(second_elem) >= 2:
                # This is an edge
                source_node, source_layer = first_elem[0], first_elem[1]
                target_node, target_layer = second_elem[0], second_elem[1]
                
                # Handle edge-specific attributes
                if attribute == "source_layer":
                    return str(source_layer)
                elif attribute == "target_layer":
                    return str(target_layer)
                elif attribute == "layer":
                    # For intralayer edges, return the common layer
                    if source_layer == target_layer:
                        return str(source_layer)
                    return None
                elif attribute == "weight":
                    # Get edge data if available
                    if len(item) >= 3 and isinstance(item[2], dict):
                        return item[2].get('weight', 1.0)
                    # Try to get from graph
                    if G.has_edge(first_elem, second_elem):
                        edge_data = G.get_edge_data(first_elem, second_elem)
                        if edge_data:
                            return edge_data.get('weight', 1.0)
                    return 1.0
                else:
                    # Try to get from edge data dict
                    if len(item) >= 3 and isinstance(item[2], dict):
                        if attribute in item[2]:
                            return item[2][attribute]
                    # Try to get from graph
                    if G.has_edge(first_elem, second_elem):
                        edge_data = G.get_edge_data(first_elem, second_elem)
                        if edge_data and attribute in edge_data:
                            return edge_data[attribute]
                return None
        
        # This is a node (tuple of (node_id, layer))
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


def _get_edge_key(edge: Any) -> Tuple[Any, Any]:
    """Get a hashable key for an edge.
    
    Converts edge tuple (u, v, {data}?) to simple (u, v) for use as dict key.
    """
    if isinstance(edge, tuple) and len(edge) >= 2:
        return (edge[0], edge[1])
    return edge


def _apply_ordering(items: List[Any], order_by: List[OrderItem],
                    attributes: Dict[str, Dict]) -> List[Any]:
    """Apply ORDER BY to items.
    
    For nodes: Uses computed attributes
    For edges: Uses computed attributes or edge data attributes (e.g., weight)
    """
    if not order_by:
        return items
    
    def sort_key(item):
        values = []
        for order_item in order_by:
            key = order_item.key
            
            # Get value from computed attributes first
            if key in attributes:
                # For edges, use hashable key
                item_key = _get_edge_key(item) if isinstance(item, tuple) and len(item) >= 3 else item
                value = attributes[key].get(item_key, 0)
            else:
                # For edges, try to get from edge data (e.g., weight)
                if isinstance(item, tuple) and len(item) >= 3 and isinstance(item[2], dict):
                    value = item[2].get(key, 0)
                else:
                    value = 0
            
            # Negate for descending
            if order_item.desc and isinstance(value, (int, float)):
                value = -value
            
            values.append(value)
        
        return tuple(values)
    
    return sorted(items, key=sort_key)


def _apply_grouping_and_coverage(
    items: List[Any],
    select: SelectStmt,
    network: Any,
    G: nx.Graph,
    attributes: Dict[str, Dict],
) -> List[Any]:
    """Apply grouping, per-group operations, and coverage filtering.
    
    This handles:
    1. Grouping items by specified fields (e.g., "layer")
    2. Per-group ordering (if order_by is specified)
    3. Per-group top-k limiting (if limit_per_group is specified)
    4. Coverage filtering across groups (if coverage_mode is specified)
    
    Args:
        items: List of items (nodes or edges)
        select: SELECT statement with grouping/coverage configuration
        network: Multilayer network
        G: Core network graph
        attributes: Computed attributes dict
        
    Returns:
        Filtered and ordered list of items
        
    Raises:
        DslExecutionError: If configuration is invalid
    """
    # Validate grouping is set up when needed
    if not select.group_by and (select.limit_per_group is not None or select.coverage_mode):
        raise DslExecutionError(
            "Grouping must be configured (via .group_by() or .per_layer()) "
            "before using .top_k() or .coverage()"
        )
    
    # Build groups
    groups: Dict[Any, List[Any]] = {}
    for item in items:
        group_key = _get_group_key(item, select, network, G)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    # Per-group ordering
    if select.order_by:
        for key in groups:
            groups[key] = _apply_ordering(groups[key], select.order_by, attributes)
    
    # Per-group top-k
    if select.limit_per_group is not None:
        k = select.limit_per_group
        for key in groups:
            groups[key] = groups[key][:k]
    
    # Coverage filtering
    if select.coverage_mode:
        # Only support coverage for node queries initially
        if select.target != Target.NODES:
            raise DslExecutionError(
                "Coverage filtering is currently supported only for node queries. "
                "Edge coverage filtering will be added in a future release."
            )
        
        # Build coverage map: identity -> set of groups it appears in
        coverage_map: Dict[Any, Set[Any]] = {}
        for group_key, group_items in groups.items():
            for item in group_items:
                identity = _get_coverage_identity(item, select, network, G)
                if identity not in coverage_map:
                    coverage_map[identity] = set()
                coverage_map[identity].add(group_key)
        
        # Apply coverage mode to determine allowed identities
        num_groups = len(groups)
        allowed_ids = set()
        mode = select.coverage_mode
        k = select.coverage_k
        
        for node_id, group_set in coverage_map.items():
            count = len(group_set)
            if mode == "all":
                if count == num_groups:
                    allowed_ids.add(node_id)
            elif mode == "any":
                if count >= 1:
                    allowed_ids.add(node_id)
            elif mode == "at_least":
                if k is not None and count >= k:
                    allowed_ids.add(node_id)
            elif mode == "exact":
                if k is not None and count == k:
                    allowed_ids.add(node_id)
        
        # Filter groups to only include allowed identities
        for group_key in groups:
            filtered_group = []
            for item in groups[group_key]:
                identity = _get_coverage_identity(item, select, network, G)
                if identity in allowed_ids:
                    filtered_group.append(item)
            groups[group_key] = filtered_group
    
    # Flatten groups back to a single list (ordered by group key for determinism)
    new_items = []
    for key in sorted(groups.keys(), key=lambda x: str(x)):
        new_items.extend(groups[key])
    
    return new_items


def _get_group_key(item: Any, select: SelectStmt, network: Any, G: nx.Graph) -> Any:
    """Get the grouping key for an item.
    
    Args:
        item: Node or edge item
        select: SELECT statement with group_by fields
        network: Multilayer network
        G: Core network graph
        
    Returns:
        Grouping key (single value or tuple)
    """
    keys = []
    for field in select.group_by:
        if field == "layer":
            # Special handling for layer field
            if isinstance(item, tuple) and len(item) >= 2:
                # Node: (node_id, layer)
                if not isinstance(item[0], tuple):
                    keys.append(str(item[1]))
                    continue
                # Edge: ((src_node, src_layer), (tgt_node, tgt_layer), {data}?)
                src = item[0]
                if isinstance(src, tuple) and len(src) >= 2:
                    keys.append(str(src[1]))
                    continue
            # Fallback to attribute lookup
            value = _get_attribute_value(item, "layer", network, G)
            keys.append(str(value) if value is not None else "None")
        else:
            # Generic attribute lookup
            value = _get_attribute_value(item, field, network, G)
            keys.append(str(value) if value is not None else "None")
    
    return tuple(keys) if len(keys) > 1 else keys[0]


def _get_coverage_identity(item: Any, select: SelectStmt, network: Any, G: nx.Graph) -> Any:
    """Get the coverage identity for an item.
    
    For nodes, the identity is typically the node ID (item[0]).
    This allows (node_id, layer1) and (node_id, layer2) to be treated
    as the same entity for coverage counting.
    
    Args:
        item: Node or edge item
        select: SELECT statement with coverage_id_field
        network: Multilayer network
        G: Core network graph
        
    Returns:
        Coverage identity (typically node ID for nodes)
    """
    id_field = select.coverage_id_field or "id"
    
    # Node queries
    if select.target == Target.NODES:
        if id_field == "id":
            # Use logical node ID (first element of tuple)
            if isinstance(item, tuple) and len(item) >= 1:
                return item[0]
            return item
        # Future: other fields via _get_attribute_value
        return _get_attribute_value(item, id_field, network, G)
    else:
        # Edge queries (if ever supported)
        if id_field == "id":
            return _get_edge_key(item)
        return _get_attribute_value(item, id_field, network, G)
