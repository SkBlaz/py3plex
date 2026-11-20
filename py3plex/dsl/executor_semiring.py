"""Executor for semiring algebra DSL operations.

This module implements the execution logic for S builder queries (paths, closure).
"""

from typing import Any, Dict, Optional
import time

from py3plex.exceptions import Py3plexException
from py3plex.algebra import (
    get_semiring,
    WeightLiftSpec,
    get_backend,
)
from .ast import (
    SemiringPathStmt,
    SemiringClosureStmt,
)
from .errors import DslExecutionError
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
    replicas, edges, layers = _extract_graph_data(
        network, stmt.layer_expr, stmt.crossing_layers, lift_spec
    )
    
    source = _resolve_param(stmt.source, params)
    target = _resolve_param(stmt.target, params) if stmt.target is not None else None
    sources = _matching_replicas(replicas, source)
    targets = _matching_replicas(replicas, target) if target is not None else []
    if not sources:
        raise DslExecutionError(f"Source {source!r} is absent from the selected layers.")
    if target is not None and not targets:
        raise DslExecutionError(f"Target {target!r} is absent from the selected layers.")

    target_indices = set(targets)
    target_node = replicas[targets[0]][0] if targets else None
    backend = get_backend(stmt.backend)
    nodes = list(range(len(replicas)))
    values = dict.fromkeys((node for node, _ in replicas), semiring.zero())
    witnesses = {}
    witness_values = {}
    better = getattr(semiring, "better", lambda new, old: new != old and semiring.add(old, new) == new)
    iterations = 0
    converged = True
    for start in sources:
        path_result = backend.sssp(
            nodes=nodes,
            edges=edges,
            source=start,
            semiring=semiring,
            lift_spec=lift_spec,
            target=targets[0] if len(targets) == 1 else None,
            max_hops=stmt.max_hops,
        )
        iterations += path_result.iterations
        converged = converged and path_result.converged
        for idx, value in path_result.distances.items():
            node = replicas[idx][0]
            if targets and node == target_node and idx not in target_indices:
                continue
            values[node] = semiring.add(values[node], value)
            if stmt.witness and value != semiring.zero() and (
                node not in witness_values or better(value, witness_values[node])
            ):
                path = path_result.get_path(idx)
                if path is not None:
                    witnesses[node] = [replicas[step][0] for step in path]
                    witness_values[node] = value

    end_time = time.time()
    items = []
    for node, value in sorted(values.items(), key=lambda pair: str(pair[0])):
        item = {"node": node, "value": value}
        if stmt.witness:
            item["path"] = witnesses.get(node)
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
                'layers_included': layers,
                'crossing_layers_mode': stmt.crossing_layers.mode,
                'penalty': stmt.crossing_layers.penalty,
            },
            'backend': {
                'name': stmt.backend,
                'algorithm': path_result.algorithm,
            },
            'performance': {
                'total_time': end_time - start_time,
                'iterations': iterations,
            },
            'determinism': {
                'converged': converged,
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
    replicas, edges, layers = _extract_graph_data(
        network, stmt.layer_expr, stmt.crossing_layers, lift_spec
    )
    
    # Get backend
    backend = get_backend(stmt.backend)
    
    # Execute closure
    closure_result = backend.closure(
        nodes=list(range(len(replicas))),
        edges=edges,
        semiring=semiring,
        lift_spec=lift_spec,
        method=stmt.method,
    )
    
    end_time = time.time()
    
    # Convert to QueryResult
    values = {}
    for (src, dst), value in closure_result.items():
        pair = (replicas[src][0], replicas[dst][0])
        values[pair] = semiring.add(values.get(pair, semiring.zero()), value)

    items = []
    for (src, dst), value in sorted(values.items(), key=lambda pair: (str(pair[0][0]), str(pair[0][1]))):
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
                'layers_included': layers,
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


def _extract_graph_data(network, layer_expr, crossing_spec, lift_spec):
    """Build arcs on replica indices, retaining each physical edge's attributes."""
    from .executor import _evaluate_layer_expr

    active = (
        _evaluate_layer_expr(layer_expr, network)
        if layer_expr is not None
        else {str(layer) for layer in network.layers}
    )
    replicas = [] if network.core_network is None else [
        replica for replica in network.get_nodes() if str(replica[1]) in active
    ]
    indices = {replica: index for index, replica in enumerate(replicas)}
    edges = []
    if not indices:
        return replicas, edges, sorted(active)

    # Include stored coupling arcs so the crossing policy applies to them too.
    for source, target, attrs in network.get_edges(data=True, multiplex_edges=True):
        if source not in indices or target not in indices:
            continue
        if source[1] != target[1]:
            if crossing_spec.mode == "forbidden":
                continue
            if crossing_spec.mode == "penalty" and crossing_spec.penalty is not None:
                attr = lift_spec.attr
                if attr is not None and (attr in attrs or lift_spec.on_missing == "default"):
                    attrs = {**attrs, attr: attrs.get(attr, lift_spec.default) + crossing_spec.penalty}
        u, v = indices[source], indices[target]
        edges.append((u, v, attrs))
        if not network.directed and u != v:
            edges.append((v, u, attrs))
    return replicas, edges, sorted(active)


def _matching_replicas(replicas, selector):
    # A physical identifier may itself be a tuple, so match it before
    # interpreting a tuple selector as an explicit replica.
    matches = [idx for idx, (node, _) in enumerate(replicas) if node == selector]
    return matches or [idx for idx, replica in enumerate(replicas) if replica == selector]


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
