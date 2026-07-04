"""Pattern Compilation.

This module compiles PatternGraph IR into execution plans that can be
 efficiently executed by the matching engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .ir import (
    AllDistinctConstraint,
    NotEqualConstraint,
    PatternEdge,
    PatternGraph,
    Predicate,
)


@dataclass
class VariablePlan:
    """Execution plan for a single variable."""

    var: str
    estimated_candidates: Optional[int] = None
    predicates: List[Predicate] = field(default_factory=list)
    layer_constraint: Optional[Any] = None


@dataclass
class JoinStep:
    """Represents a join step in the execution plan."""

    var: str
    via_edge: Optional[PatternEdge] = None
    method: Literal["initial_scan", "neighbor_expansion", "constraint_check"] = "initial_scan"
    backwards: bool = False
    constraint: Optional[Any] = None


@dataclass
class PatternPlan:
    """Complete execution plan for a pattern."""

    pattern: PatternGraph
    root_var: str
    join_order: List[JoinStep] = field(default_factory=list)
    variable_plans: Dict[str, VariablePlan] = field(default_factory=dict)
    estimated_complexity: int = -1
    injective: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/display."""
        return {
            "root_var": self.root_var,
            "injective": self.injective,
            "join_order": [
                {
                    "var": step.var,
                    "method": step.method,
                    "via_edge": str(step.via_edge) if step.via_edge else None,
                    "backwards": step.backwards,
                    "constraint": _constraint_repr(step.constraint),
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


def compile_pattern(
    pattern: PatternGraph,
    network: Any = None,
    injective: bool = True,
) -> PatternPlan:
    """Compile a pattern graph into an execution plan."""
    layer_counts: Dict[str, int] = {}
    total_nodes = 0
    if network is not None:
        layer_counts, total_nodes = _summarize_network_nodes(network)

    variable_plans: Dict[str, VariablePlan] = {}
    for var, node in pattern.nodes.items():
        plan = VariablePlan(
            var=var,
            predicates=list(node.predicates),
            layer_constraint=node.layer_constraint,
        )
        if network is not None:
            base_candidates = _estimate_candidates_from_network(node, layer_counts, total_nodes)
            if node.predicates:
                if base_candidates <= 0:
                    plan.estimated_candidates = 0
                else:
                    discounted = int(base_candidates * (0.3 ** len(node.predicates)))
                    plan.estimated_candidates = max(1, discounted)
            else:
                plan.estimated_candidates = base_candidates
        else:
            if len(node.predicates) > 0 or node.layer_constraint:
                plan.estimated_candidates = 100 // (len(node.predicates) + 1)
            else:
                plan.estimated_candidates = 1000
        variable_plans[var] = plan

    root_var = _select_root_variable(pattern, variable_plans)
    join_order = _build_join_order(pattern, root_var, variable_plans)

    estimated_complexity = 1
    for step in join_order:
        if step.method == "constraint_check":
            continue
        estimate = variable_plans[step.var].estimated_candidates
        if estimate is None:
            continue
        estimated_complexity *= max(estimate, 1)
        if estimated_complexity > 10**12:
            estimated_complexity = 10**12
            break

    return PatternPlan(
        pattern=pattern,
        root_var=root_var,
        join_order=join_order,
        variable_plans=variable_plans,
        estimated_complexity=estimated_complexity,
        injective=injective,
    )


def _summarize_network_nodes(network: Any) -> tuple[Dict[str, int], int]:
    """Count nodes per layer in one pass."""
    layer_counts: Dict[str, int] = {}
    total_nodes = 0

    if hasattr(network, "get_nodes"):
        nodes_iter = network.get_nodes()
    elif hasattr(network, "core_network"):
        nodes_iter = network.core_network.nodes()
    else:
        nodes_iter = []

    for node_tuple in nodes_iter:
        total_nodes += 1
        if isinstance(node_tuple, tuple) and len(node_tuple) >= 2:
            layer = node_tuple[1]
        else:
            layer = "default"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    return layer_counts, total_nodes


def _estimate_candidates_from_network(node: Any, layer_counts: Dict[str, int], total_nodes: int) -> int:
    """Estimate candidates from network structure and layer constraints."""
    layer_constraint = getattr(node, "layer_constraint", None)
    if layer_constraint is None or layer_constraint.kind == "wildcard":
        return total_nodes
    if layer_constraint.kind == "one":
        return layer_counts.get(layer_constraint.value, 0)
    if layer_constraint.kind == "set":
        return sum(layer_counts.get(layer, 0) for layer in layer_constraint.value)
    return total_nodes


def _select_root_variable(pattern: PatternGraph, variable_plans: Dict[str, VariablePlan]) -> str:
    """Select the best root variable to start matching."""
    if not pattern.nodes:
        raise ValueError("Pattern has no nodes")

    var_degrees = {var: 0 for var in pattern.nodes}
    for edge in pattern.edges:
        var_degrees[edge.src] += 1
        var_degrees[edge.dst] += 1

    best_var: Optional[str] = None
    best_score = float("inf")
    for var, plan in variable_plans.items():
        estimate = plan.estimated_candidates if plan.estimated_candidates is not None else 1000
        score = estimate / (var_degrees[var] + 1)
        if score < best_score or (
            score == best_score and best_var is not None and var < best_var
        ):
            best_score = score
            best_var = var

    assert best_var is not None
    return best_var


def _build_join_order(
    pattern: PatternGraph,
    root_var: str,
    variable_plans: Dict[str, VariablePlan],
) -> List[JoinStep]:
    """Build join order using deterministic greedy expansion."""
    join_order: List[JoinStep] = [JoinStep(var=root_var, method="initial_scan")]
    bound_vars = {root_var}
    remaining_vars = set(pattern.nodes.keys()) - bound_vars
    used_edge_ids: set[int] = set()

    while remaining_vars:
        candidate_steps: List[tuple[float, str, str, str, bool, PatternEdge]] = []
        for edge in pattern.edges:
            if edge.src in bound_vars and edge.dst in remaining_vars:
                candidate_steps.append(
                    (
                        _candidate_sort_key(variable_plans, edge.dst),
                        edge.dst,
                        edge.src,
                        edge.dst,
                        False,
                        edge,
                    )
                )
            elif not edge.directed and edge.dst in bound_vars and edge.src in remaining_vars:
                candidate_steps.append(
                    (
                        _candidate_sort_key(variable_plans, edge.src),
                        edge.src,
                        edge.src,
                        edge.dst,
                        False,
                        edge,
                    )
                )
            elif edge.directed and edge.dst in bound_vars and edge.src in remaining_vars:
                candidate_steps.append(
                    (
                        _candidate_sort_key(variable_plans, edge.src),
                        edge.src,
                        edge.src,
                        edge.dst,
                        True,
                        edge,
                    )
                )

        if candidate_steps:
            _, var, _, _, backwards, edge = min(candidate_steps)
            join_order.append(
                JoinStep(
                    var=var,
                    via_edge=edge,
                    method="neighbor_expansion",
                    backwards=backwards,
                )
            )
            bound_vars.add(var)
            remaining_vars.remove(var)
            used_edge_ids.add(id(edge))
            continue

        var = min(remaining_vars)
        remaining_vars.remove(var)
        bound_vars.add(var)
        join_order.append(JoinStep(var=var, method="initial_scan"))

    bound_positions = {
        step.var: idx
        for idx, step in enumerate(join_order)
        if step.method != "constraint_check"
    }

    insertions: Dict[int, List[JoinStep]] = {}

    for edge in pattern.edges:
        if id(edge) in used_edge_ids:
            continue
        if edge.src not in bound_positions or edge.dst not in bound_positions:
            continue
        src_pos = bound_positions[edge.src]
        dst_pos = bound_positions[edge.dst]
        later_var = edge.dst if dst_pos >= src_pos else edge.src
        position = max(src_pos, dst_pos) + 1
        insertions.setdefault(position, []).append(
            JoinStep(var=later_var, via_edge=edge, method="constraint_check")
        )

    for constraint in pattern.constraints:
        refs = _constraint_variables(constraint)
        if not refs or any(ref not in bound_positions for ref in refs):
            continue
        last_var = max(sorted(refs), key=lambda ref: (bound_positions[ref], ref))
        position = max(bound_positions[ref] for ref in refs) + 1
        insertions.setdefault(position, []).append(
            JoinStep(var=last_var, method="constraint_check", constraint=constraint)
        )

    if not insertions:
        return join_order

    final_order: List[JoinStep] = []
    for idx, step in enumerate(join_order):
        final_order.append(step)
        final_order.extend(insertions.get(idx + 1, []))

    return final_order


def _candidate_sort_key(variable_plans: Dict[str, VariablePlan], var: str) -> float:
    estimate = variable_plans[var].estimated_candidates
    return float("inf") if estimate is None else float(estimate)


def _constraint_variables(constraint: Any) -> List[str]:
    if isinstance(constraint, NotEqualConstraint):
        return [constraint.var1, constraint.var2]
    if isinstance(constraint, AllDistinctConstraint):
        return list(constraint.vars)
    return []


def _constraint_repr(constraint: Any) -> Optional[str]:
    if constraint is None:
        return None
    if hasattr(constraint, "to_dict"):
        return str(constraint.to_dict())
    return str(constraint)
