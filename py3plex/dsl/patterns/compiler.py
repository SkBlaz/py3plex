"""Pattern Compilation.

This module compiles PatternGraph IR into execution plans that can be
efficiently executed by the matching engine. The compiler:

1. Analyzes the pattern structure
2. Determines candidate generation strategies for each variable
3. Selects optimal join order based on selectivity heuristics
4. Produces a PatternPlan that guides execution
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .ir import PatternGraph, PatternNode, PatternEdge


@dataclass
class VariablePlan:
    """Execution plan for a single variable.
    
    Attributes:
        var: Variable name
        estimated_candidates: Estimated number of candidate nodes
        predicates: List of predicates to apply
        layer_constraint: Layer constraint if any
    """
    var: str
    estimated_candidates: int = -1  # -1 means unknown
    predicates: List[Any] = field(default_factory=list)
    layer_constraint: Optional[Any] = None


@dataclass
class JoinStep:
    """Represents a join step in the execution plan.
    
    Attributes:
        var: Variable being bound in this step
        via_edge: Edge used for the join (if expanding from neighbors)
        method: Join method ("initial_scan", "neighbor_expansion", "constraint_check")
    """
    var: str
    via_edge: Optional[PatternEdge] = None
    method: str = "initial_scan"


@dataclass
class PatternPlan:
    """Complete execution plan for a pattern.
    
    Attributes:
        pattern: Original pattern graph
        root_var: Variable to start matching from
        join_order: Sequence of join steps
        variable_plans: Plans for each variable
        estimated_complexity: Rough complexity estimate
    """
    pattern: PatternGraph
    root_var: str
    join_order: List[JoinStep] = field(default_factory=list)
    variable_plans: Dict[str, VariablePlan] = field(default_factory=dict)
    estimated_complexity: int = -1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/display."""
        return {
            "root_var": self.root_var,
            "join_order": [
                {
                    "var": step.var,
                    "method": step.method,
                    "via_edge": str(step.via_edge) if step.via_edge else None,
                }
                for step in self.join_order
            ],
            "variable_plans": {
                var: {
                    "var": plan.var,
                    "estimated_candidates": plan.estimated_candidates,
                    "num_predicates": len(plan.predicates),
                    "layer_constraint": str(plan.layer_constraint) if plan.layer_constraint else None,
                }
                for var, plan in self.variable_plans.items()
            },
            "estimated_complexity": self.estimated_complexity,
        }


def compile_pattern(pattern: PatternGraph) -> PatternPlan:
    """Compile a pattern graph into an execution plan.
    
    The compilation strategy:
    1. Select root variable with most restrictive predicates
    2. Build join order using a greedy approach (expand along edges)
    3. Estimate selectivity for each variable
    
    Args:
        pattern: Pattern graph to compile
        
    Returns:
        PatternPlan with execution strategy
    """
    # Create variable plans for each node
    variable_plans = {}
    for var, node in pattern.nodes.items():
        plan = VariablePlan(
            var=var,
            predicates=node.predicates,
            layer_constraint=node.layer_constraint,
        )
        # Estimate selectivity based on number of predicates
        # More predicates = fewer candidates
        if len(node.predicates) > 0 or node.layer_constraint:
            plan.estimated_candidates = 100 // (len(node.predicates) + 1)
        else:
            plan.estimated_candidates = 1000  # Arbitrary large number
        variable_plans[var] = plan
    
    # Select root variable: prefer one with most predicates
    root_var = _select_root_variable(pattern, variable_plans)
    
    # Build join order using greedy expansion
    join_order = _build_join_order(pattern, root_var)
    
    # Estimate overall complexity (rough heuristic)
    complexity = 1
    for plan in variable_plans.values():
        complexity *= max(plan.estimated_candidates, 1)
    
    return PatternPlan(
        pattern=pattern,
        root_var=root_var,
        join_order=join_order,
        variable_plans=variable_plans,
        estimated_complexity=complexity,
    )


def _select_root_variable(pattern: PatternGraph, variable_plans: Dict[str, VariablePlan]) -> str:
    """Select the best root variable to start matching.
    
    Heuristic: Choose variable with:
    1. Most restrictive predicates (lowest estimated candidates)
    2. Highest degree in pattern graph (most connections)
    
    Args:
        pattern: Pattern graph
        variable_plans: Variable plans with estimates
        
    Returns:
        Variable name to use as root
    """
    if not pattern.nodes:
        raise ValueError("Pattern has no nodes")
    
    # Calculate degree in pattern graph
    var_degrees = {var: 0 for var in pattern.nodes}
    for edge in pattern.edges:
        var_degrees[edge.src] += 1
        var_degrees[edge.dst] += 1
    
    # Score each variable: lower candidates + higher degree = better
    best_var = None
    best_score = float('inf')
    
    for var, plan in variable_plans.items():
        # Score: candidates / (degree + 1)
        score = plan.estimated_candidates / (var_degrees[var] + 1)
        if score < best_score:
            best_score = score
            best_var = var
    
    return best_var


def _build_join_order(pattern: PatternGraph, root_var: str) -> List[JoinStep]:
    """Build join order using greedy expansion.
    
    Starting from root_var, expand along edges to unbound variables.
    
    Args:
        pattern: Pattern graph
        root_var: Variable to start from
        
    Returns:
        List of join steps
    """
    join_order = []
    bound_vars = set()
    
    # Step 1: Initial scan of root variable
    join_order.append(JoinStep(var=root_var, method="initial_scan"))
    bound_vars.add(root_var)
    
    # Step 2: Expand along edges
    remaining_vars = set(pattern.nodes.keys()) - bound_vars
    
    while remaining_vars:
        # Find an edge connecting a bound variable to an unbound one
        found = False
        for edge in pattern.edges:
            if edge.src in bound_vars and edge.dst in remaining_vars:
                # Expand from src to dst
                join_order.append(JoinStep(
                    var=edge.dst,
                    via_edge=edge,
                    method="neighbor_expansion"
                ))
                bound_vars.add(edge.dst)
                remaining_vars.remove(edge.dst)
                found = True
                break
            elif not edge.directed and edge.dst in bound_vars and edge.src in remaining_vars:
                # For undirected edges, can also expand from dst to src
                join_order.append(JoinStep(
                    var=edge.src,
                    via_edge=edge,
                    method="neighbor_expansion"
                ))
                bound_vars.add(edge.src)
                remaining_vars.remove(edge.src)
                found = True
                break
        
        if not found:
            # No more edges to expand - handle disconnected components
            # Just pick any remaining variable
            var = remaining_vars.pop()
            join_order.append(JoinStep(var=var, method="initial_scan"))
            bound_vars.add(var)
    
    return join_order
