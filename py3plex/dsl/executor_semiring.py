"""Executor for semiring algebra DSL operations.

This module implements the execution logic for S builder queries (paths, closure).
"""

from typing import Any, Dict, List, Optional, Tuple
import time

from py3plex.exceptions import Py3plexException
from py3plex.algebra import (
    get_semiring,
    WeightLiftSpec,
    sssp,
    closure,
    get_backend,
)
from .ast import (
    SemiringPathStmt,
    SemiringClosureStmt,
    CrossingLayersSpec,
)
from .result import QueryResult


def execute_semiring_path_stmt(
    network: Any,
    stmt: SemiringPathStmt,
    params: Optional[Dict[str, Any]] = None,
) -> QueryResult:
    """Execute semiring path statement.
    
    Args:
        network: Multilayer network
        stmt: SemiringPathStmt AST node
        params: Parameter bindings
        
    Returns:
        QueryResult with path data and provenance
    """
    params = params or {}
    start_time = time.time()
    
    # Resolve semiring
    semiring_name = stmt.semiring_spec.name
    if semiring_name is None:
        semiring_name = "min_plus"  # Default
    
    semiring = get_semiring(semiring_name)
    
    # Build weight lift spec
    lift_spec = WeightLiftSpec(
        attr=stmt.lift_spec.attr,
        transform=stmt.lift_spec.transform,
        default=stmt.lift_spec.default,
        on_missing=stmt.lift_spec.on_missing,
    )
    
    # Extract nodes and edges from network
    nodes, edges = _extract_graph_data(network, stmt.layer_expr, stmt.crossing_layers)
    
    # Resolve source/target (handle parameters)
    source = _resolve_param(stmt.source, params)
    target = _resolve_param(stmt.target, params) if stmt.target else None
    
    # Get backend
    backend = get_backend(stmt.backend)
    
    # Execute SSSP
    path_result = backend.sssp(
        nodes=nodes,
        edges=edges,
        source=source,
        semiring=semiring,
        lift_spec=lift_spec,
        target=target,
        max_hops=stmt.max_hops,
    )
    
    end_time = time.time()
    
    # Convert to QueryResult
    items = []
    for node, value in path_result.distances.items():
        item = {
            'node': node,
            'value': value,
        }
        if stmt.witness and path_result.predecessors:
            path = path_result.get_path(node)
            item['path'] = path if path else None
        items.append(item)
    
    # Build provenance
    provenance = {
        'algebra': {
            'semiring': {
                'name': semiring_name,
                'properties': semiring.props,
            },
            'lift': {
                'attr': stmt.lift_spec.attr,
                'transform': stmt.lift_spec.transform,
                'default': stmt.lift_spec.default,
                'on_missing': stmt.lift_spec.on_missing,
            },
            'problem': {
                'kind': 'paths',
                'source': source,
                'target': target,
                'max_hops': stmt.max_hops,
                'k_best': stmt.k_best,
            },
            'multilayer': {
                'layers_included': _get_layer_names(stmt.layer_expr),
                'crossing_layers_mode': stmt.crossing_layers.mode,
                'penalty': stmt.crossing_layers.penalty,
            },
            'backend': {
                'name': stmt.backend,
                'algorithm': path_result.algorithm,
            },
            'performance': {
                'total_time': end_time - start_time,
                'iterations': path_result.iterations,
            },
            'determinism': {
                'converged': path_result.converged,
                'stable_ordering': True,
            },
        },
    }
    
    return QueryResult(
        target='paths',
        items=items,
        attributes={},
        meta={'provenance': provenance},
    )


def execute_semiring_closure_stmt(
    network: Any,
    stmt: SemiringClosureStmt,
    params: Optional[Dict[str, Any]] = None,
) -> QueryResult:
    """Execute semiring closure statement.
    
    Args:
        network: Multilayer network
        stmt: SemiringClosureStmt AST node
        params: Parameter bindings
        
    Returns:
        QueryResult with closure data
    """
    params = params or {}
    start_time = time.time()
    
    # Resolve semiring
    semiring_name = stmt.semiring_spec.name
    if semiring_name is None:
        semiring_name = "boolean"  # Default for closure
    
    semiring = get_semiring(semiring_name)
    
    # Build weight lift spec
    lift_spec = WeightLiftSpec(
        attr=stmt.lift_spec.attr,
        transform=stmt.lift_spec.transform,
        default=stmt.lift_spec.default,
        on_missing=stmt.lift_spec.on_missing,
    )
    
    # Extract nodes and edges
    nodes, edges = _extract_graph_data(network, stmt.layer_expr, stmt.crossing_layers)
    
    # Get backend
    backend = get_backend(stmt.backend)
    
    # Execute closure
    closure_result = backend.closure(
        nodes=nodes,
        edges=edges,
        semiring=semiring,
        lift_spec=lift_spec,
        method=stmt.method,
    )
    
    end_time = time.time()
    
    # Convert to QueryResult
    items = []
    for (src, dst), value in closure_result.items():
        # Skip zero values for sparse output
        if stmt.output_format == "sparse" and value == semiring.zero():
            continue
        items.append({
            'source': src,
            'target': dst,
            'value': value,
        })
    
    # Build provenance
    provenance = {
        'algebra': {
            'semiring': {
                'name': semiring_name,
                'properties': semiring.props,
            },
            'lift': {
                'attr': stmt.lift_spec.attr,
                'transform': stmt.lift_spec.transform,
                'default': stmt.lift_spec.default,
                'on_missing': stmt.lift_spec.on_missing,
            },
            'problem': {
                'kind': 'closure',
                'method': stmt.method,
            },
            'multilayer': {
                'layers_included': _get_layer_names(stmt.layer_expr),
                'crossing_layers_mode': stmt.crossing_layers.mode,
            },
            'backend': {
                'name': stmt.backend,
            },
            'performance': {
                'total_time': end_time - start_time,
            },
            'determinism': {
                'stable_ordering': True,
            },
        },
    }
    
    return QueryResult(
        target='closure',
        items=items,
        attributes={},
        meta={'provenance': provenance},
    )


def _extract_graph_data(
    network: Any,
    layer_expr: Optional[Any],
    crossing_spec: CrossingLayersSpec,
) -> Tuple[List[Any], List[Tuple[Any, Any, Dict[str, Any]]]]:
    """Extract nodes and edges from multilayer network.
    
    Args:
        network: Multilayer network
        layer_expr: Optional layer expression for filtering
        crossing_spec: Cross-layer edge handling spec
        
    Returns:
        Tuple of (nodes, edges)
    """
    # Get included layers
    layers_result = network.get_layers()
    # get_layers() returns a tuple: (layer_names, layer_graphs, ...)
    all_layer_names = layers_result[0] if isinstance(layers_result, tuple) else layers_result
    
    if layer_expr:
        included_layers = set(_get_layer_names(layer_expr))
    else:
        # All layers
        included_layers = set(all_layer_names)
    
    # Collect nodes
    nodes = []
    for layer in included_layers:
        try:
            layer_nodes = network.get_nodes(layer)
            for node in layer_nodes:
                # Use simple node identifiers (not tuples)
                nodes.append(node)
        except Exception:
            # Fallback: iterate over all nodes and filter by layer
            pass
    
    # Deduplicate
    nodes = list(set(nodes))
    
    # If no nodes collected via get_nodes, collect from edges
    if not nodes:
        # Collect all unique node IDs from edges
        node_set = set()
        for edge_data in network.get_edges(data=True):
            if len(edge_data) == 3:
                (u_node, u_layer), (v_node, v_layer), data = edge_data
                if u_layer in included_layers:
                    node_set.add(u_node)
                if v_layer in included_layers:
                    node_set.add(v_node)
        nodes = list(node_set)
    
    # Collect edges
    edges = []
    for edge_data in network.get_edges(data=True):
        if len(edge_data) != 3:
            continue
        
        (u_node, u_layer), (v_node, v_layer), data = edge_data
        
        # Check layer constraints
        if u_layer not in included_layers or v_layer not in included_layers:
            continue
        
        # Check cross-layer policy
        is_cross_layer = (u_layer != v_layer)
        if is_cross_layer:
            if crossing_spec.mode == "forbidden":
                continue
            elif crossing_spec.mode == "penalty" and crossing_spec.penalty is not None:
                # Add penalty to weight
                data = data.copy()
                weight_attr = data.get('weight', 1.0)
                data['weight'] = weight_attr + crossing_spec.penalty
        
        # Store with simple node identifiers
        edges.append((u_node, v_node, data))
    
    return nodes, edges


def _get_layer_names(layer_expr: Optional[Any]) -> List[str]:
    """Extract layer names from layer expression."""
    if layer_expr is None:
        return []
    
    # Call get_layer_names method if available
    if hasattr(layer_expr, 'get_layer_names'):
        return layer_expr.get_layer_names()
    
    # Fallback: extract from terms
    if hasattr(layer_expr, 'terms'):
        return [term.name for term in layer_expr.terms]
    
    return []


def _resolve_param(value: Any, params: Dict[str, Any]) -> Any:
    """Resolve parameter reference to actual value."""
    from .ast import ParamRef
    if isinstance(value, ParamRef):
        if value.name not in params:
            raise Py3plexException(
                f"Parameter '{value.name}' not provided. "
                f"Available parameters: {list(params.keys())}"
            )
        return params[value.name]
    return value
