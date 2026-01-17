"""Program explanation utilities.

This module implements human-readable explanations of GraphPrograms.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .types import Type


@dataclass
class ExplainResult:
    """Human-readable explanation of a GraphProgram.
    
    Attributes:
        pipeline_steps: List of pipeline steps with descriptions
        type_flow: Type signatures at each step
        cost_estimates: Cost estimates for each step
        optimizations: List of applied optimizations
        cache_status: Cache hit/miss information
        total_cost: Total estimated cost
    """
    pipeline_steps: List[str]
    type_flow: List[str]
    cost_estimates: List[str]
    optimizations: List[str]
    cache_status: Optional[str] = None
    total_cost: Optional[str] = None
    
    def to_text(self) -> str:
        """Render as formatted text."""
        lines = ["=" * 60, "Graph Program Explanation", "=" * 60, ""]
        
        lines.append("Pipeline Steps:")
        for i, (step, typ, cost) in enumerate(zip(
            self.pipeline_steps,
            self.type_flow,
            self.cost_estimates
        ), 1):
            lines.append(f"  {i}. {step}")
            lines.append(f"     Type: {typ}")
            lines.append(f"     Cost: {cost}")
            lines.append("")
        
        if self.optimizations:
            lines.append("Optimizations Applied:")
            for opt in self.optimizations:
                lines.append(f"  - {opt}")
            lines.append("")
        
        if self.total_cost:
            lines.append(f"Total Estimated Cost: {total_cost}")
            lines.append("")
        
        if self.cache_status:
            lines.append(f"Cache Status: {self.cache_status}")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)


def explain_program(
    program: "GraphProgram",
    include_cost: bool = True,
    include_types: bool = True,
    include_optimizations: bool = True
) -> ExplainResult:
    """Generate human-readable explanation of a GraphProgram.
    
    Args:
        program: GraphProgram to explain
        include_cost: Include cost estimates
        include_types: Include type information
        include_optimizations: Include optimization information
        
    Returns:
        ExplainResult object
    """
    pipeline_steps = []
    type_flow = []
    cost_estimates = []
    optimizations = []
    
    # Parse AST to extract steps
    ast = program.canonical_ast
    
    # Extract target (nodes/edges/communities)
    if hasattr(ast, "select") and ast.select:
        target = ast.select.target.value if hasattr(ast.select.target, "value") else str(ast.select.target)
        pipeline_steps.append(f"SELECT {target}")
        type_flow.append(f"{target.capitalize()}Set")
        cost_estimates.append("O(V)" if target == "nodes" else "O(E)")
    
    # Extract layers filter
    if hasattr(ast, "select") and hasattr(ast.select, "layers") and ast.select.layers:
        layers_expr = _format_layers(ast.select.layers)
        pipeline_steps.append(f"FROM layers: {layers_expr}")
        type_flow.append(f"{type_flow[-1]} (filtered)")
        cost_estimates.append("O(1) filter")
    
    # Extract conditions
    if hasattr(ast, "select") and hasattr(ast.select, "conditions") and ast.select.conditions:
        conds = ast.select.conditions
        pipeline_steps.append(f"WHERE {_format_conditions(conds)}")
        type_flow.append(type_flow[-1] if type_flow else "Set")
        cost_estimates.append("O(N) filter")
    
    # Extract computations
    if hasattr(ast, "select") and hasattr(ast.select, "computes") and ast.select.computes:
        for compute in ast.select.computes:
            measure = compute.measure
            pipeline_steps.append(f"COMPUTE {measure}")
            type_flow.append("Table")
            cost_estimates.append(_estimate_compute_cost(measure))
    
    # Extract ordering
    if hasattr(ast, "select") and hasattr(ast.select, "order_by") and ast.select.order_by:
        order_items = ast.select.order_by
        for item in order_items:
            direction = "DESC" if item.desc else "ASC"
            pipeline_steps.append(f"ORDER BY {item.field} {direction}")
            type_flow.append(type_flow[-1] if type_flow else "Table")
            cost_estimates.append("O(N log N) sort")
    
    # Extract limit
    if hasattr(ast, "select") and hasattr(ast.select, "limit") and ast.select.limit:
        pipeline_steps.append(f"LIMIT {ast.select.limit}")
        type_flow.append(type_flow[-1] if type_flow else "Table")
        cost_estimates.append("O(1) slice")
    
    # Extract optimizations from provenance
    if program.metadata and program.metadata.provenance_chain:
        for transform in program.metadata.provenance_chain:
            if "optimization" in transform.lower() or "rewrite" in transform.lower():
                optimizations.append(transform)
    
    # Compute total cost
    total_cost = None
    if include_cost:
        try:
            from .cost import CostModel, GraphStats
            cost_model = CostModel()
            stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=2)
            cost = cost_model.estimate_program_cost(program, stats)
            total_cost = f"{cost.time_estimate_seconds:.3f}s (est.)"
        except Exception:
            pass
    
    return ExplainResult(
        pipeline_steps=pipeline_steps,
        type_flow=type_flow if include_types else [],
        cost_estimates=cost_estimates if include_cost else [],
        optimizations=optimizations if include_optimizations else [],
        total_cost=total_cost,
    )


def _format_layers(layers_expr) -> str:
    """Format layer expression for display."""
    if hasattr(layers_expr, "terms"):
        terms = [t.name for t in layers_expr.terms]
        ops = layers_expr.ops if hasattr(layers_expr, "ops") else []
        if ops:
            return " ".join(f"{t} {op}" for t, op in zip(terms, ops + [""]))
        return ", ".join(terms)
    return str(layers_expr)


def _format_conditions(conditions) -> str:
    """Format conditions for display."""
    if hasattr(conditions, "atoms"):
        atoms = []
        for atom in conditions.atoms:
            if hasattr(atom, "comparison"):
                comp = atom.comparison
                atoms.append(f"{comp.field} {comp.op} {comp.value}")
        return " AND ".join(atoms)
    return str(conditions)


def _estimate_compute_cost(measure: str) -> str:
    """Estimate cost for a measure."""
    costs = {
        "degree": "O(E)",
        "betweenness_centrality": "O(VE)",
        "closeness_centrality": "O(V²)",
        "pagerank": "O(kE)",
        "eigenvector_centrality": "O(kE)",
        "clustering": "O(d³)",
    }
    return costs.get(measure, "O(?)")
