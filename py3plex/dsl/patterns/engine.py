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
        List of candidate node IDs
    """
    var = step.var
    node = pattern.nodes[var]
    
    if step.method == "initial_scan":
        # Initial scan: get all nodes matching predicates
        candidates = []
        for node_id, layer in network.get_nodes():
            # Check layer constraint
            if node.layer_constraint and not node.layer_constraint.matches(layer):
                continue
            
            # Check predicates
            if _check_node_predicates(network, node_id, layer, node.predicates):
                candidates.append(node_id)
        
        return candidates
    
    elif step.method == "neighbor_expansion":
        # Expand from a bound variable via an edge
        edge = step.via_edge
        
        # Determine source variable
        if edge.src in match:
            src_node = match[edge.src]
            src_layer = _get_node_layer(network, src_node)
            
            # Get neighbors
            candidates = []
            for neighbor_id in _get_neighbors(network, src_node, src_layer, edge):
                neighbor_layer = _get_node_layer(network, neighbor_id)
                
                # Check layer constraint
                if node.layer_constraint and not node.layer_constraint.matches(neighbor_layer):
                    continue
                
                # Check predicates
                if _check_node_predicates(network, neighbor_id, neighbor_layer, node.predicates):
                    candidates.append(neighbor_id)
            
            return candidates
        
        elif edge.dst in match:
            # Expand backwards (for undirected edges)
            dst_node = match[edge.dst]
            dst_layer = _get_node_layer(network, dst_node)
            
            # Get neighbors
            candidates = []
            for neighbor_id in _get_neighbors(network, dst_node, dst_layer, edge):
                neighbor_layer = _get_node_layer(network, neighbor_id)
                
                # Check layer constraint
                if node.layer_constraint and not node.layer_constraint.matches(neighbor_layer):
                    continue
                
                # Check predicates
                if _check_node_predicates(network, neighbor_id, neighbor_layer, node.predicates):
                    candidates.append(neighbor_id)
            
            return candidates
    
    return []


def _check_node_predicates(network: Any, node_id: Any, layer: str, predicates: List[Predicate]) -> bool:
    """Check if a node satisfies all predicates.
    
    Args:
        network: Network object
        node_id: Node identifier
        layer: Node layer
        predicates: List of predicates to check
        
    Returns:
        True if all predicates satisfied
    """
    if not predicates:
        return True
    
    for pred in predicates:
        # Get attribute value
        value = _get_node_attribute(network, node_id, layer, pred.attr)
        
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
    
    src_node = match[edge.src]
    dst_node = match[edge.dst]
    
    # Check if edge exists
    if not _has_edge(network, src_node, dst_node, edge.directed):
        return False
    
    # Check layer constraint
    if edge.layer_constraint:
        src_layer = _get_node_layer(network, src_node)
        dst_layer = _get_node_layer(network, dst_node)
        
        if not edge.layer_constraint.matches(src_layer, dst_layer):
            return False
    
    # Check edge predicates
    if edge.predicates:
        edge_data = _get_edge_data(network, src_node, dst_node)
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

def _get_node_layer(network: Any, node_id: Any) -> str:
    """Get the layer of a node.
    
    Args:
        network: Network object
        node_id: Node identifier
        
    Returns:
        Layer name
    """
    # Try to get layer from node data
    if hasattr(network, 'core_network'):
        node_data = network.core_network.nodes.get(node_id, {})
        return node_data.get('layer', node_data.get('type', 'default'))
    return 'default'


def _get_node_attribute(network: Any, node_id: Any, layer: str, attr: str) -> Any:
    """Get a node attribute value.
    
    Args:
        network: Network object
        node_id: Node identifier
        layer: Node layer
        attr: Attribute name
        
    Returns:
        Attribute value or None
    """
    if attr == "degree":
        # Special handling for degree
        if hasattr(network, 'core_network'):
            return network.core_network.degree(node_id)
        return 0
    
    # Get from node data
    if hasattr(network, 'core_network'):
        node_data = network.core_network.nodes.get(node_id, {})
        return node_data.get(attr)
    
    return None


def _get_neighbors(network: Any, node_id: Any, layer: str, edge: PatternEdge) -> List[Any]:
    """Get neighbors of a node respecting edge constraints.
    
    Args:
        network: Network object
        node_id: Node identifier
        layer: Node layer
        edge: Pattern edge with constraints
        
    Returns:
        List of neighbor node IDs
    """
    neighbors = []
    
    if hasattr(network, 'core_network'):
        # Get all neighbors
        if edge.directed:
            neighbor_iter = network.core_network.successors(node_id)
        else:
            neighbor_iter = network.core_network.neighbors(node_id)
        
        for neighbor in neighbor_iter:
            neighbors.append(neighbor)
    
    return neighbors


def _has_edge(network: Any, src: Any, dst: Any, directed: bool) -> bool:
    """Check if an edge exists between two nodes.
    
    Args:
        network: Network object
        src: Source node
        dst: Destination node
        directed: Whether to check directed edge
        
    Returns:
        True if edge exists
    """
    if hasattr(network, 'core_network'):
        if directed:
            return network.core_network.has_edge(src, dst)
        else:
            return network.core_network.has_edge(src, dst) or network.core_network.has_edge(dst, src)
    return False


def _get_edge_data(network: Any, src: Any, dst: Any) -> Dict[str, Any]:
    """Get edge data/attributes.
    
    Args:
        network: Network object
        src: Source node
        dst: Destination node
        
    Returns:
        Dictionary of edge attributes
    """
    if hasattr(network, 'core_network'):
        if network.core_network.has_edge(src, dst):
            return network.core_network[src][dst]
        elif network.core_network.has_edge(dst, src):
            return network.core_network[dst][src]
    return {}
