"""Pattern Matching Engine.

This module implements the core pattern matching algorithm that executes
patterns against multilayer networks. The engine uses a backtracking approach
with early pruning based on predicates and constraints.

Strategy:
1. Generate candidates for root variable using predicates
2. Expand along edges to bind other variables
3. Apply predicates and constraints at each step
4. Backtrack when constraints violated
5. Yield complete matches
"""

import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .ir import (
    PatternGraph,
    PatternNode,
    PatternEdge,
    MatchRow,
    Predicate,
    LayerConstraint,
    EdgeLayerConstraint,
)
from .compiler import PatternPlan, JoinStep


def match_pattern(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    limit: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[MatchRow]:
    """Execute pattern matching on a network.
    
    Args:
        network: Multilayer network object
        pattern: Pattern graph to match
        plan: Compiled execution plan
        limit: Maximum number of matches to return
        timeout: Optional timeout in seconds
        
    Returns:
        List of MatchRow objects representing matches
    """
    matches = []
    start_time = time.time() if timeout else None
    
    # Generate matches using backtracking
    for match in _backtrack_match(network, pattern, plan, start_time, timeout):
        # Filter by return_vars if specified
        return_vars = pattern.get_return_vars()
        filtered_bindings = {var: match.bindings[var] for var in return_vars if var in match.bindings}
        
        matches.append(MatchRow(bindings=filtered_bindings))
        
        # Check limit
        if limit and len(matches) >= limit:
            break
        
        # Check timeout
        if timeout and start_time:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                break
    
    return matches


def _backtrack_match(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    start_time: Optional[float],
    timeout: Optional[float],
) -> Iterator[MatchRow]:
    """Generate matches using backtracking.
    
    Args:
        network: Network object
        pattern: Pattern graph
        plan: Execution plan
        start_time: Start time for timeout checking
        timeout: Timeout in seconds
        
    Yields:
        MatchRow objects
    """
    # Initialize match state
    match = MatchRow()
    
    # Execute join steps
    yield from _execute_join_steps(
        network, pattern, plan, plan.join_order, 0, match, start_time, timeout
    )


def _execute_join_steps(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    join_order: List[JoinStep],
    step_idx: int,
    match: MatchRow,
    start_time: Optional[float],
    timeout: Optional[float],
) -> Iterator[MatchRow]:
    """Recursively execute join steps with backtracking.
    
    Args:
        network: Network object
        pattern: Pattern graph
        plan: Execution plan
        join_order: List of join steps
        step_idx: Current step index
        match: Current match state
        start_time: Start time for timeout
        timeout: Timeout in seconds
        
    Yields:
        Complete MatchRow objects
    """
    # Check timeout
    if timeout and start_time:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return
    
    # Base case: all variables bound
    if step_idx >= len(join_order):
        # Check global constraints
        if _check_constraints(pattern, match):
            yield match
        return
    
    # Get current step
    step = join_order[step_idx]
    var = step.var
    
    # Generate candidates for this variable
    candidates = _generate_candidates(network, pattern, plan, step, match)
    
    # Try each candidate
    for candidate in candidates:
        # Bind variable
        new_match = MatchRow(bindings=match.bindings.copy())
        new_match[var] = candidate
        
        # Check edge constraints if this was a neighbor expansion
        if step.via_edge and not _check_edge_constraint(network, step.via_edge, new_match):
            continue
        
        # Recursively process next step
        yield from _execute_join_steps(
            network, pattern, plan, join_order, step_idx + 1, new_match, start_time, timeout
        )


def _generate_candidates(
    network: Any,
    pattern: PatternGraph,
    plan: PatternPlan,
    step: JoinStep,
    match: MatchRow,
) -> List[Any]:
    """Generate candidate nodes for a variable.
    
    Args:
        network: Network object
        pattern: Pattern graph
        plan: Execution plan
        step: Current join step
        match: Current match state
        
    Returns:
        List of candidate node IDs (tuples of (node_id, layer))
    """
    var = step.var
    node = pattern.nodes[var]
    
    if step.method == "initial_scan":
        # Initial scan: get all nodes matching predicates
        candidates = []
        for node_tuple in network.get_nodes():
            # node_tuple is (node_id, layer)
            if isinstance(node_tuple, tuple) and len(node_tuple) == 2:
                node_id, layer = node_tuple
            else:
                # Fallback for different network formats
                node_id, layer = node_tuple, 'default'
            
            # Check layer constraint
            if node.layer_constraint and not node.layer_constraint.matches(layer):
                continue
            
            # Check predicates
            if _check_node_predicates(network, (node_id, layer), layer, node.predicates):
                candidates.append((node_id, layer))
        
        return candidates
    
    elif step.method == "neighbor_expansion":
        # Expand from a bound variable via an edge
        edge = step.via_edge
        
        # Determine source variable
        if edge.src in match:
            src_node_tuple = match[edge.src]
            src_layer = src_node_tuple[1] if isinstance(src_node_tuple, tuple) else 'default'
            
            # Get neighbors
            candidates = []
            for neighbor_tuple in _get_neighbors(network, src_node_tuple, src_layer, edge):
                neighbor_layer = neighbor_tuple[1] if isinstance(neighbor_tuple, tuple) else 'default'
                
                # Check layer constraint
                if node.layer_constraint and not node.layer_constraint.matches(neighbor_layer):
                    continue
                
                # Check edge predicates
                if edge.predicates:
                    edge_data = _get_edge_data(network, src_node_tuple, neighbor_tuple)
                    edge_satisfied = True
                    for pred in edge.predicates:
                        value = edge_data.get(pred.attr)
                        if value is None or not _compare_values(value, pred.op, pred.value):
                            edge_satisfied = False
                            break
                    if not edge_satisfied:
                        continue
                
                # Check node predicates
                if _check_node_predicates(network, neighbor_tuple, neighbor_layer, node.predicates):
                    candidates.append(neighbor_tuple)
            
            return candidates
        
        elif edge.dst in match:
            # Expand backwards (for undirected edges)
            dst_node_tuple = match[edge.dst]
            dst_layer = dst_node_tuple[1] if isinstance(dst_node_tuple, tuple) else 'default'
            
            # Get neighbors
            candidates = []
            for neighbor_tuple in _get_neighbors(network, dst_node_tuple, dst_layer, edge):
                neighbor_layer = neighbor_tuple[1] if isinstance(neighbor_tuple, tuple) else 'default'
                
                # Check layer constraint
                if node.layer_constraint and not node.layer_constraint.matches(neighbor_layer):
                    continue
                
                # Check edge predicates
                if edge.predicates:
                    edge_data = _get_edge_data(network, dst_node_tuple, neighbor_tuple)
                    edge_satisfied = True
                    for pred in edge.predicates:
                        value = edge_data.get(pred.attr)
                        if value is None or not _compare_values(value, pred.op, pred.value):
                            edge_satisfied = False
                            break
                    if not edge_satisfied:
                        continue
                
                # Check node predicates
                if _check_node_predicates(network, neighbor_tuple, neighbor_layer, node.predicates):
                    candidates.append(neighbor_tuple)
            
            return candidates
    
    return []


def _check_node_predicates(network: Any, node_tuple: Any, layer: str, predicates: List[Predicate]) -> bool:
    """Check if a node satisfies all predicates.
    
    Args:
        network: Network object
        node_tuple: Node identifier (tuple of (node_id, layer))
        layer: Node layer
        predicates: List of predicates to check
        
    Returns:
        True if all predicates satisfied
    """
    if not predicates:
        return True
    
    for pred in predicates:
        # Get attribute value
        value = _get_node_attribute(network, node_tuple, layer, pred.attr)
        
        if value is None:
            return False
        
        # Check comparison
        if not _compare_values(value, pred.op, pred.value):
            return False
    
    return True


def _check_edge_constraint(network: Any, edge: PatternEdge, match: MatchRow) -> bool:
    """Check if an edge constraint is satisfied.
    
    Args:
        network: Network object
        edge: Pattern edge
        match: Current match with both endpoints bound
        
    Returns:
        True if edge constraint satisfied
    """
    if edge.src not in match or edge.dst not in match:
        return False
    
    src_node_tuple = match[edge.src]
    dst_node_tuple = match[edge.dst]
    
    # Check if edge exists
    if not _has_edge(network, src_node_tuple, dst_node_tuple, edge.directed):
        return False
    
    # Check layer constraint
    if edge.layer_constraint:
        src_layer = src_node_tuple[1] if isinstance(src_node_tuple, tuple) else 'default'
        dst_layer = dst_node_tuple[1] if isinstance(dst_node_tuple, tuple) else 'default'
        
        if not edge.layer_constraint.matches(src_layer, dst_layer):
            return False
    
    # Check edge predicates
    if edge.predicates:
        edge_data = _get_edge_data(network, src_node_tuple, dst_node_tuple)
        for pred in edge.predicates:
            value = edge_data.get(pred.attr)
            if value is None or not _compare_values(value, pred.op, pred.value):
                return False
    
    return True


def _check_constraints(pattern: PatternGraph, match: MatchRow) -> bool:
    """Check global constraints.
    
    Args:
        pattern: Pattern graph
        match: Complete match
        
    Returns:
        True if all constraints satisfied
    """
    for constraint in pattern.constraints:
        if not _evaluate_constraint(constraint, match):
            return False
    return True


def _evaluate_constraint(constraint: str, match: MatchRow) -> bool:
    """Evaluate a constraint expression.
    
    Args:
        constraint: Constraint expression (e.g., "a != b")
        match: Match state
        
    Returns:
        True if constraint satisfied
    """
    # Simple parsing for common constraints
    if " != " in constraint:
        parts = constraint.split(" != ")
        if len(parts) == 2:
            var1, var2 = parts[0].strip(), parts[1].strip()
            if var1 in match and var2 in match:
                return match[var1] != match[var2]
    
    # Handle all_distinct
    if constraint.startswith("all_distinct("):
        # Extract variable list
        import re
        m = re.match(r'all_distinct\(\[(.*?)\]\)', constraint)
        if m:
            vars_str = m.group(1)
            vars = [v.strip() for v in vars_str.split(',')]
            values = [match[v] for v in vars if v in match]
            return len(values) == len(set(values))
    
    return True


def _compare_values(value: Any, op: str, target: Any) -> bool:
    """Compare two values using an operator.
    
    Args:
        value: Left-hand side value
        op: Comparison operator
        target: Right-hand side value
        
    Returns:
        True if comparison satisfied
    """
    try:
        if op == ">":
            return value > target
        elif op == ">=":
            return value >= target
        elif op == "<":
            return value < target
        elif op == "<=":
            return value <= target
        elif op == "=":
            return value == target
        elif op == "!=":
            return value != target
    except (TypeError, ValueError):
        return False
    
    return False


# Network access helpers

def _get_node_attribute(network: Any, node_tuple: Any, layer: str, attr: str) -> Any:
    """Get a node attribute value.
    
    Args:
        network: Network object
        node_tuple: Node identifier (tuple of (node_id, layer))
        layer: Node layer
        attr: Attribute name
        
    Returns:
        Attribute value or None
    """
    if attr == "degree":
        # Special handling for degree
        if hasattr(network, 'core_network'):
            return network.core_network.degree(node_tuple)
        return 0
    
    # Get from node data
    if hasattr(network, 'core_network'):
        node_data = network.core_network.nodes.get(node_tuple, {})
        return node_data.get(attr)
    
    return None


def _get_neighbors(network: Any, node_tuple: Any, layer: str, edge: PatternEdge) -> List[Any]:
    """Get neighbors of a node respecting edge constraints.
    
    Args:
        network: Network object
        node_tuple: Node identifier (tuple of (node_id, layer))
        layer: Node layer
        edge: Pattern edge with constraints
        
    Returns:
        List of neighbor node tuples
    """
    neighbors = []
    
    if hasattr(network, 'core_network'):
        # Get all neighbors
        if edge.directed:
            neighbor_iter = network.core_network.successors(node_tuple)
        else:
            neighbor_iter = network.core_network.neighbors(node_tuple)
        
        for neighbor in neighbor_iter:
            neighbors.append(neighbor)
    
    return neighbors


def _has_edge(network: Any, src_tuple: Any, dst_tuple: Any, directed: bool) -> bool:
    """Check if an edge exists between two nodes.
    
    Args:
        network: Network object
        src_tuple: Source node tuple
        dst_tuple: Destination node tuple
        directed: Whether to check directed edge
        
    Returns:
        True if edge exists
    """
    if hasattr(network, 'core_network'):
        if directed:
            return network.core_network.has_edge(src_tuple, dst_tuple)
        else:
            return network.core_network.has_edge(src_tuple, dst_tuple) or network.core_network.has_edge(dst_tuple, src_tuple)
    return False


def _get_edge_data(network: Any, src_tuple: Any, dst_tuple: Any) -> Dict[str, Any]:
    """Get edge data/attributes.
    
    Args:
        network: Network object
        src_tuple: Source node tuple
        dst_tuple: Destination node tuple
        
    Returns:
        Dictionary of edge attributes
    """
    if hasattr(network, 'core_network'):
        # MultiGraph stores edges with integer keys (multi-edges)
        # We need to extract data from the first edge
        if network.core_network.has_edge(src_tuple, dst_tuple):
            edge_dict = network.core_network[src_tuple][dst_tuple]
            # Check if it looks like a multi-edge dict (dict-like with integer keys)
            if hasattr(edge_dict, 'keys') and edge_dict.keys() and all(isinstance(k, int) for k in edge_dict.keys()):
                # Get first edge's data
                first_key = min(edge_dict.keys())
                return dict(edge_dict[first_key])
            return dict(edge_dict) if hasattr(edge_dict, 'items') else {}
        elif network.core_network.has_edge(dst_tuple, src_tuple):
            edge_dict = network.core_network[dst_tuple][src_tuple]
            # Check if it looks like a multi-edge dict (dict-like with integer keys)
            if hasattr(edge_dict, 'keys') and edge_dict.keys() and all(isinstance(k, int) for k in edge_dict.keys()):
                # Get first edge's data
                first_key = min(edge_dict.keys())
                return dict(edge_dict[first_key])
            return dict(edge_dict) if hasattr(edge_dict, 'items') else {}
    return {}
