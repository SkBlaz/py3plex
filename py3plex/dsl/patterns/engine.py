"""Pattern Matching Engine.

This module implements the core pattern matching algorithm that executes
patterns against multilayer networks.
"""

import time
from typing import Any, Dict, Iterator, List, Optional, Set

from .compiler import JoinStep, PatternPlan
from .ir import (
    AllDistinctConstraint,
    MatchRow,
    NotEqualConstraint,
    PatternEdge,
    PatternGraph,
    Predicate,
)


def match_pattern(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    limit: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[MatchRow]:
    """Execute pattern matching on a network."""
    matches: List[MatchRow] = []
    start_time = time.time() if timeout else None
    layer_index = _build_layer_index(network)

    for match in _backtrack_match(network, pattern, plan, start_time, timeout, layer_index):
        return_vars = pattern.get_return_vars()
        filtered_bindings = {
            var: match.bindings[var] for var in return_vars if var in match.bindings
        }
        matches.append(MatchRow(bindings=filtered_bindings))

        if limit and len(matches) >= limit:
            break

        if timeout and start_time:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                break

    return matches


def _build_layer_index(network: Any) -> Dict[str, List[Any]]:
    """Build a layer-to-nodes index once per query."""
    index: Dict[str, List[Any]] = {}
    if hasattr(network, "get_nodes"):
        nodes_iter = network.get_nodes()
    elif hasattr(network, "core_network"):
        nodes_iter = network.core_network.nodes()
    else:
        nodes_iter = []

    for node_tuple in nodes_iter:
        if isinstance(node_tuple, tuple) and len(node_tuple) >= 2:
            layer = node_tuple[1]
        else:
            layer = "default"
        index.setdefault(layer, []).append(node_tuple)
    return index


def _backtrack_match(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    start_time: Optional[float],
    timeout: Optional[float],
    layer_index: Dict[str, List[Any]],
) -> Iterator[MatchRow]:
    """Generate matches using backtracking."""
    match = MatchRow()
    yield from _execute_join_steps(
        network,
        pattern,
        plan,
        plan.join_order,
        0,
        match,
        set(),
        start_time,
        timeout,
        layer_index,
    )


def _execute_join_steps(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    join_order: List[JoinStep],
    step_idx: int,
    match: MatchRow,
    bound_values: Set[Any],
    start_time: Optional[float],
    timeout: Optional[float],
    layer_index: Dict[str, List[Any]],
) -> Iterator[MatchRow]:
    """Recursively execute join steps with backtracking."""
    if timeout and start_time:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return

    if step_idx >= len(join_order):
        if _check_constraints(pattern, match):
            yield MatchRow(bindings=dict(match.bindings))
        return

    step = join_order[step_idx]
    var = step.var

    if step.method == "constraint_check":
        if step.constraint is not None:
            if not _evaluate_constraint(step.constraint, match):
                return
        else:
            if not step.via_edge or not _check_edge_constraint(network, step.via_edge, match):
                return
        yield from _execute_join_steps(
            network,
            pattern,
            plan,
            join_order,
            step_idx + 1,
            match,
            bound_values,
            start_time,
            timeout,
            layer_index,
        )
        return

    candidates = _generate_candidates(network, pattern, plan, step, match, layer_index)
    injective = getattr(plan, "injective", True)

    for candidate in candidates:
        if injective and candidate in bound_values:
            continue

        added_to_bound = False
        if candidate not in bound_values:
            bound_values.add(candidate)
            added_to_bound = True

        match[var] = candidate
        try:
            if step.via_edge and not _check_edge_constraint(network, step.via_edge, match):
                continue

            yield from _execute_join_steps(
                network,
                pattern,
                plan,
                join_order,
                step_idx + 1,
                match,
                bound_values,
                start_time,
                timeout,
                layer_index,
            )
        finally:
            match.bindings.pop(var, None)
            if added_to_bound:
                bound_values.discard(candidate)


def _generate_candidates(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    step: JoinStep,
    match: MatchRow,
    layer_index: Dict[str, List[Any]],
) -> List[Any]:
    """Generate candidate nodes for a variable."""
    var = step.var
    node = pattern.nodes[var]

    if step.method == "initial_scan":
        candidates: List[Any] = []
        node_iter = _initial_scan_nodes(network, node.layer_constraint, layer_index)
        for node_tuple in node_iter:
            if isinstance(node_tuple, tuple) and len(node_tuple) >= 2:
                _, layer = node_tuple[0], node_tuple[1]
            else:
                layer = "default"
            if node.layer_constraint and not node.layer_constraint.matches(layer):
                continue
            if _check_node_predicates(network, node_tuple, layer, node.predicates):
                candidates.append(node_tuple)
        return candidates

    if step.method != "neighbor_expansion" or step.via_edge is None:
        return []

    edge = step.via_edge
    candidates: List[Any] = []

    if step.var == edge.dst and edge.src in match:
        anchor_tuple = match[edge.src]
        backwards = False
        bind_as_src = False
    elif step.var == edge.src and edge.dst in match:
        anchor_tuple = match[edge.dst]
        backwards = step.backwards
        bind_as_src = True
    else:
        return []

    anchor_layer = anchor_tuple[1] if isinstance(anchor_tuple, tuple) and len(anchor_tuple) >= 2 else "default"
    for neighbor_tuple in _get_neighbors(
        network,
        anchor_tuple,
        anchor_layer,
        edge,
        backwards=backwards,
    ):
        neighbor_layer = neighbor_tuple[1] if isinstance(neighbor_tuple, tuple) and len(neighbor_tuple) >= 2 else "default"

        if bind_as_src:
            src_node_tuple = neighbor_tuple
            dst_node_tuple = anchor_tuple
            src_layer = neighbor_layer
            dst_layer = anchor_layer
        else:
            src_node_tuple = anchor_tuple
            dst_node_tuple = neighbor_tuple
            src_layer = anchor_layer
            dst_layer = neighbor_layer

        if node.layer_constraint and not node.layer_constraint.matches(neighbor_layer):
            continue

        if edge.layer_constraint and not edge.layer_constraint.matches(src_layer, dst_layer):
            continue

        if edge.predicates and not _check_edge_predicates_any_parallel(
            network,
            src_node_tuple,
            dst_node_tuple,
            edge,
            edge.directed,
        ):
            continue

        if _check_node_predicates(network, neighbor_tuple, neighbor_layer, node.predicates):
            candidates.append(neighbor_tuple)

    return candidates


def _initial_scan_nodes(
    network: Any,
    layer_constraint: Any,
    layer_index: Dict[str, List[Any]],
) -> List[Any]:
    """Get initial-scan nodes using the prebuilt layer index when possible."""
    if layer_constraint is not None:
        if layer_constraint.kind == "one":
            return list(layer_index.get(layer_constraint.value, []))
        if layer_constraint.kind == "set":
            nodes: List[Any] = []
            for layer in sorted(layer_constraint.value):
                nodes.extend(layer_index.get(layer, []))
            return nodes

    if hasattr(network, "get_nodes"):
        return list(network.get_nodes())
    if hasattr(network, "core_network"):
        return list(network.core_network.nodes())
    return []


def _check_node_predicates(
    network: Any,
    node_tuple: Any,
    layer: str,
    predicates: List[Predicate],
) -> bool:
    """Check if a node satisfies all predicates."""
    if not predicates:
        return True

    for pred in predicates:
        value = _get_node_attribute(network, node_tuple, layer, pred.attr)
        if value is None:
            return False
        if not _compare_values(value, pred.op, pred.value):
            return False

    return True


def _check_edge_constraint(network: Any, edge: PatternEdge, match: MatchRow) -> bool:
    """Check if an edge constraint is satisfied."""
    if edge.src not in match or edge.dst not in match:
        return False

    src_node_tuple = match[edge.src]
    dst_node_tuple = match[edge.dst]

    if not _has_edge(network, src_node_tuple, dst_node_tuple, edge.directed):
        return False

    if edge.layer_constraint:
        src_layer = src_node_tuple[1] if isinstance(src_node_tuple, tuple) and len(src_node_tuple) >= 2 else "default"
        dst_layer = dst_node_tuple[1] if isinstance(dst_node_tuple, tuple) and len(dst_node_tuple) >= 2 else "default"
        if not edge.layer_constraint.matches(src_layer, dst_layer):
            return False

    if edge.predicates:
        if not _check_edge_predicates_any_parallel(
            network,
            src_node_tuple,
            dst_node_tuple,
            edge,
            edge.directed,
        ):
            return False

    return True


def _check_constraints(pattern: PatternGraph, match: MatchRow) -> bool:
    """Check global constraints."""
    for constraint in pattern.constraints:
        if not _evaluate_constraint(constraint, match):
            return False
    return True


def _evaluate_constraint(constraint: Any, match: MatchRow) -> bool:
    """Evaluate a structured constraint."""
    if isinstance(constraint, NotEqualConstraint):
        if constraint.var1 in match and constraint.var2 in match:
            return match[constraint.var1] != match[constraint.var2]
        return True

    if isinstance(constraint, AllDistinctConstraint):
        values = [match[var] for var in constraint.vars if var in match]
        return len(values) == len(set(values))

    if isinstance(constraint, str):
        if "!=" in constraint:
            left, right = [part.strip() for part in constraint.split("!=", 1)]
            if left in match and right in match:
                return match[left] != match[right]
            return True
        if constraint.startswith("all_distinct(") and constraint.endswith(")"):
            inner = constraint[len("all_distinct(") : -1]
            vars_list = [part.strip() for part in inner.split(",") if part.strip()]
            values = [match[var] for var in vars_list if var in match]
            return len(values) == len(set(values))

    return True


def _compare_values(value: Any, op: str, target: Any) -> bool:
    """Compare two values using an operator."""
    try:
        if op == ">":
            return value > target
        if op == ">=":
            return value >= target
        if op == "<":
            return value < target
        if op == "<=":
            return value <= target
        if op == "=":
            return value == target
        if op == "!=":
            return value != target
    except (TypeError, ValueError):
        return False

    return False


# Network access helpers

def _get_node_attribute(network: Any, node_tuple: Any, layer: str, attr: str) -> Any:
    """Get a node attribute value."""
    if attr == "degree":
        if hasattr(network, "core_network"):
            return network.core_network.degree(node_tuple)
        return 0
    if attr == "layer_degree":
        if hasattr(network, "core_network"):
            node_layer = node_tuple[1] if isinstance(node_tuple, tuple) and len(node_tuple) >= 2 else "default"
            return sum(
                1
                for neighbor in network.core_network.neighbors(node_tuple)
                if isinstance(neighbor, tuple) and len(neighbor) >= 2 and neighbor[1] == node_layer
            )
        return 0

    if hasattr(network, "core_network"):
        node_data = network.core_network.nodes.get(node_tuple, {})
        return node_data.get(attr)

    return None


def _get_neighbors(
    network: Any,
    node_tuple: Any,
    layer: str,
    edge: PatternEdge,
    backwards: bool = False,
) -> List[Any]:
    """Get neighbors of a node respecting edge direction."""
    neighbors: List[Any] = []
    if not hasattr(network, "core_network"):
        return neighbors

    graph = network.core_network
    if edge.directed:
        if backwards:
            if hasattr(graph, "predecessors"):
                neighbor_iter = graph.predecessors(node_tuple)
            else:
                neighbor_iter = graph.neighbors(node_tuple)
        else:
            if hasattr(graph, "successors"):
                neighbor_iter = graph.successors(node_tuple)
            else:
                neighbor_iter = graph.neighbors(node_tuple)
    else:
        neighbor_iter = graph.neighbors(node_tuple)

    for neighbor in neighbor_iter:
        neighbors.append(neighbor)
    return neighbors


def _has_edge(network: Any, src_tuple: Any, dst_tuple: Any, directed: bool) -> bool:
    """Check if an edge exists between two nodes."""
    if hasattr(network, "core_network"):
        if directed:
            return network.core_network.has_edge(src_tuple, dst_tuple)
        return network.core_network.has_edge(src_tuple, dst_tuple) or network.core_network.has_edge(dst_tuple, src_tuple)
    return False


def _iter_edge_data(network: Any, src_tuple: Any, dst_tuple: Any, directed: bool = False):
    """Yield attribute dicts for all parallel edges between two nodes."""
    if not hasattr(network, "core_network"):
        return

    graph = network.core_network
    if graph.has_edge(src_tuple, dst_tuple):
        edge_view = graph[src_tuple][dst_tuple]
        if hasattr(graph, "is_multigraph") and graph.is_multigraph():
            for attrdict in edge_view.values():
                yield dict(attrdict)
        else:
            yield dict(edge_view)
    elif not directed and graph.has_edge(dst_tuple, src_tuple):
        edge_view = graph[dst_tuple][src_tuple]
        if hasattr(graph, "is_multigraph") and graph.is_multigraph():
            for attrdict in edge_view.values():
                yield dict(attrdict)
        else:
            yield dict(edge_view)


def _check_edge_predicates_any_parallel(
    network: Any,
    src_tuple: Any,
    dst_tuple: Any,
    edge: PatternEdge,
    directed: bool = False,
) -> bool:
    """Return True if any single parallel edge satisfies all predicates."""
    for attrdict in _iter_edge_data(network, src_tuple, dst_tuple, directed):
        satisfied = True
        for pred in edge.predicates:
            value = attrdict.get(pred.attr)
            if value is None or not _compare_values(value, pred.op, pred.value):
                satisfied = False
                break
        if satisfied:
            return True
    return False


def _get_edge_data(network: Any, src_tuple: Any, dst_tuple: Any) -> Dict[str, Any]:
    """Get edge data/attributes for the first matching edge."""
    for attrdict in _iter_edge_data(network, src_tuple, dst_tuple, directed=False):
        return attrdict
    return {}
