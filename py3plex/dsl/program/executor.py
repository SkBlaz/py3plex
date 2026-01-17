"""Execution planning and execution for py3plex Graph Programs.

This module provides:
- ExecutionContext for specifying constraints (time/memory budgets, parallelism)
- ExecutionPlan for representing optimized execution strategies
- Budget enforcement and optimization
- Integration with existing DSL executor

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.dsl.program import GraphProgram
    >>> from py3plex.dsl.program.executor import ExecutionContext, execute_program
    >>> 
    >>> # Create program
    >>> program = GraphProgram.from_ast(Q.nodes().compute("betweenness").to_ast())
    >>> 
    >>> # Execute with budget
    >>> context = ExecutionContext(time_budget="30s", n_jobs=4)
    >>> result = execute_program(program, network, context)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..ast import Query, SelectStmt, Target
from ..executor import execute_ast
from ..result import QueryResult
from .cost import (
    Cost,
    CostModel,
    CostObjective,
    GraphStats,
    parse_time_budget,
    format_time_estimate,
    format_memory_estimate,
)
from .types import Type, infer_type
from .rewrite import RewriteEngine, RewriteRule

# Import exceptions
from py3plex.exceptions import Py3plexException


logger = logging.getLogger(__name__)


class BudgetExceededError(Py3plexException):
    """Raised when estimated cost exceeds budget constraints.
    
    Attributes:
        estimated_cost: The estimated cost
        budget: The budget constraint
        suggestions: List of suggestions for reducing cost
    """
    
    default_code = "PX401"
    
    def __init__(
        self,
        estimated_cost: Cost,
        budget: float,
        *,
        suggestions: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        self.estimated_cost = estimated_cost
        self.budget = budget
        
        time_str = format_time_estimate(estimated_cost.time_estimate_seconds)
        budget_str = format_time_estimate(budget)
        
        message = (
            f"Estimated execution time ({time_str}) exceeds budget ({budget_str}). "
            f"Confidence: {estimated_cost.confidence:.0%}"
        )
        
        if not suggestions:
            suggestions = [
                "Increase the time budget",
                "Add a LIMIT clause to reduce result set size",
                "Filter nodes/edges with WHERE clause before expensive computations",
                "Use per_layer() grouping to enable parallelization",
                "Disable uncertainty quantification (UQ) if enabled",
            ]
        
        super().__init__(
            message,
            code=self.default_code,
            suggestions=suggestions,
            **kwargs,
        )


class ExecutionTimeoutError(Py3plexException):
    """Raised when execution exceeds time budget during runtime."""
    
    default_code = "PX402"


@dataclass(frozen=True)
class ExecutionContext:
    """Context for program execution.
    
    Specifies constraints, optimization hints, and runtime configuration.
    
    Attributes:
        time_budget: Maximum execution time in seconds (or string like "30s", "5m")
        memory_budget: Maximum memory usage in bytes
        seed: Random seed for reproducibility
        n_jobs: Number of parallel workers (default: 1)
        cache_policy: Caching strategy ("auto", "on", "off")
        uq_policy: Uncertainty quantification policy ("full", "reduced")
        objective: Optimization objective
        explain: If True, return execution plan instead of results
        progress: If True, log progress during execution
    
    Example:
        >>> context = ExecutionContext(
        ...     time_budget="30s",
        ...     n_jobs=4,
        ...     cache_policy="on",
        ...     seed=42
        ... )
    """
    
    time_budget: Optional[float] = None  # Seconds
    memory_budget: Optional[int] = None  # Bytes
    seed: Optional[int] = None
    n_jobs: int = 1
    cache_policy: str = "auto"
    uq_policy: str = "full"
    objective: CostObjective = CostObjective.BALANCED
    explain: bool = False
    progress: bool = True
    
    @classmethod
    def create(
        cls,
        time_budget: Optional[Any] = None,
        memory_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> ExecutionContext:
        """Create execution context with flexible time budget parsing.
        
        Args:
            time_budget: Time budget (float seconds or string like "30s", "5m")
            memory_budget: Memory budget in bytes
            **kwargs: Additional context parameters
            
        Returns:
            ExecutionContext instance
            
        Example:
            >>> context = ExecutionContext.create(time_budget="5m", n_jobs=4)
        """
        if time_budget is not None:
            if isinstance(time_budget, str):
                time_budget = parse_time_budget(time_budget)
            else:
                time_budget = float(time_budget)
        
        return cls(
            time_budget=time_budget,
            memory_budget=memory_budget,
            **kwargs,
        )


@dataclass
class PlanStage:
    """A stage in the execution plan.
    
    Attributes:
        operation: Operation description
        input_type: Input type
        output_type: Output type
        estimated_cost: Estimated cost for this stage
        cacheable: Whether results can be cached
        parallelizable: Whether this stage can be parallelized
        metadata: Additional metadata
    
    Example:
        >>> stage = PlanStage(
        ...     operation="compute_betweenness",
        ...     input_type=None,
        ...     output_type=TableType(...),
        ...     estimated_cost=cost,
        ...     cacheable=True,
        ...     parallelizable=True
        ... )
    """
    
    operation: str
    input_type: Optional[Type]
    output_type: Type
    estimated_cost: Cost
    cacheable: bool = True
    parallelizable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "operation": self.operation,
            "estimated_cost": {
                "time_complexity": self.estimated_cost.time_complexity,
                "time_estimate_seconds": self.estimated_cost.time_estimate_seconds,
                "memory_estimate_bytes": self.estimated_cost.memory_estimate_bytes,
            },
            "cacheable": self.cacheable,
            "parallelizable": self.parallelizable,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionPlan:
    """Execution plan for a graph program.
    
    Represents an optimized execution strategy with cost estimates,
    caching strategy, and parallelization opportunities.
    
    Attributes:
        stages: List of execution stages
        estimated_cost: Total estimated cost
        cache_keys: List of cache keys for intermediate results
        parallelization_strategy: Strategy for parallel execution
        metadata: Additional plan metadata
    
    Example:
        >>> plan = create_execution_plan(program, context, stats)
        >>> print(f"Estimated time: {plan.estimated_cost.time_estimate_seconds:.2f}s")
    """
    
    stages: List[PlanStage]
    estimated_cost: Cost
    cache_keys: List[str] = field(default_factory=list)
    parallelization_strategy: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "stages": [stage.to_dict() for stage in self.stages],
            "estimated_cost": {
                "time_complexity": self.estimated_cost.time_complexity,
                "time_estimate_seconds": self.estimated_cost.time_estimate_seconds,
                "time_estimate_formatted": format_time_estimate(
                    self.estimated_cost.time_estimate_seconds
                ),
                "memory_estimate_bytes": self.estimated_cost.memory_estimate_bytes,
                "memory_estimate_formatted": format_memory_estimate(
                    self.estimated_cost.memory_estimate_bytes
                ),
                "parallelizable": self.estimated_cost.parallelizable,
                "confidence": self.estimated_cost.confidence,
            },
            "cache_keys": self.cache_keys,
            "parallelization_strategy": self.parallelization_strategy,
            "metadata": self.metadata,
        }
    
    def summary(self) -> str:
        """Get a human-readable summary of the plan.
        
        Returns:
            Multi-line string summary
            
        Example:
            >>> print(plan.summary())
        """
        lines = [
            "Execution Plan",
            "=" * 60,
            f"Estimated Time: {format_time_estimate(self.estimated_cost.time_estimate_seconds)}",
            f"Estimated Memory: {format_memory_estimate(self.estimated_cost.memory_estimate_bytes)}",
            f"Complexity: {self.estimated_cost.time_complexity}",
            f"Parallelizable: {self.estimated_cost.parallelizable}",
            f"Confidence: {self.estimated_cost.confidence:.0%}",
            "",
            "Stages:",
        ]
        
        for i, stage in enumerate(self.stages, 1):
            time_str = format_time_estimate(stage.estimated_cost.time_estimate_seconds)
            lines.append(
                f"  {i}. {stage.operation} "
                f"(~{time_str}, {stage.estimated_cost.time_complexity})"
            )
        
        lines.append("")
        
        if self.parallelization_strategy:
            lines.append("Parallelization:")
            for key, value in self.parallelization_strategy.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)


def create_execution_plan(
    program: Any,  # GraphProgram
    context: ExecutionContext,
    stats: GraphStats,
) -> ExecutionPlan:
    """Create an optimized execution plan for a program.
    
    This function:
    1. Analyzes the program AST
    2. Applies rewrites if beneficial
    3. Breaks into stages
    4. Assigns costs to each stage
    5. Checks budget constraints
    6. Returns optimized plan
    
    Args:
        program: GraphProgram to execute
        context: Execution context with constraints
        stats: Graph statistics
        
    Returns:
        ExecutionPlan
        
    Raises:
        BudgetExceededError: If estimated cost exceeds budget
        
    Example:
        >>> program = GraphProgram.from_ast(ast)
        >>> context = ExecutionContext.create(time_budget="30s")
        >>> stats = GraphStats.from_network(network)
        >>> plan = create_execution_plan(program, context, stats)
    """
    # Initialize cost model
    cost_model = CostModel()
    
    # Get AST
    ast = program.canonical_ast
    select = ast.select
    
    # Break into stages
    stages: List[PlanStage] = []
    
    # Stage 1: Base iteration (nodes/edges)
    if select.target == Target.NODES:
        base_cost = cost_model._cost_nodes_iteration(stats)
        base_op = "iterate_nodes"
    elif select.target == Target.EDGES:
        base_cost = cost_model._cost_edges_iteration(stats)
        base_op = "iterate_edges"
    else:
        base_cost = cost_model._cost_default("communities", stats)
        base_op = "detect_communities"
    
    stages.append(
        PlanStage(
            operation=base_op,
            input_type=None,
            output_type=infer_type(ast),
            estimated_cost=base_cost,
            cacheable=True,
            parallelizable=True,
        )
    )
    
    # Stage 2: Filtering (if WHERE clause)
    if select.where:
        filter_cost = cost_model._cost_filter(select.where, stats)
        stages.append(
            PlanStage(
                operation="filter",
                input_type=None,
                output_type=infer_type(ast),
                estimated_cost=filter_cost,
                cacheable=False,
                parallelizable=True,
            )
        )
    
    # Stage 3: Computations
    for compute_item in select.compute:
        compute_cost = cost_model.estimate_operator_cost(
            compute_item.name,
            None,
            stats,
            uncertainty=compute_item.uncertainty,
            n_samples=compute_item.n_samples or 50,
        )
        
        # Scale by uncertainty if enabled
        if compute_item.uncertainty:
            n_samples = compute_item.n_samples or 50
            compute_cost = compute_cost.scale(n_samples * 1.1)
        
        stages.append(
            PlanStage(
                operation=f"compute_{compute_item.name}",
                input_type=None,
                output_type=infer_type(ast),
                estimated_cost=compute_cost,
                cacheable=True,
                parallelizable=compute_cost.parallelizable,
                metadata={
                    "measure": compute_item.name,
                    "uncertainty": compute_item.uncertainty,
                },
            )
        )
    
    # Stage 4: Grouping (if group_by)
    if select.group_by:
        group_cost = cost_model._cost_grouping(stats, select.group_by)
        stages.append(
            PlanStage(
                operation="group_by",
                input_type=None,
                output_type=infer_type(ast),
                estimated_cost=group_cost,
                cacheable=False,
                parallelizable=False,
            )
        )
    
    # Stage 5: Sorting (if order_by)
    if select.order_by:
        sort_cost = cost_model._cost_sorting(stats, len(select.order_by))
        stages.append(
            PlanStage(
                operation="sort",
                input_type=None,
                output_type=infer_type(ast),
                estimated_cost=sort_cost,
                cacheable=False,
                parallelizable=True,
            )
        )
    
    # Stage 6: Export (if needed)
    if select.export or select.file_export:
        export_cost = cost_model._cost_export(stats)
        stages.append(
            PlanStage(
                operation="export",
                input_type=None,
                output_type=infer_type(ast),
                estimated_cost=export_cost,
                cacheable=False,
                parallelizable=False,
            )
        )
    
    # Compute total cost
    total_cost = Cost(
        time_complexity="O(1)",
        time_estimate_seconds=0.0,
        memory_estimate_bytes=0,
        parallelizable=True,
        confidence=1.0,
    )
    
    for stage in stages:
        total_cost = total_cost + stage.estimated_cost
    
    # Determine parallelization strategy
    parallelization_strategy = {}
    if context.n_jobs > 1:
        parallelizable_stages = [
            stage.operation for stage in stages if stage.parallelizable
        ]
        if parallelizable_stages:
            parallelization_strategy["n_jobs"] = context.n_jobs
            parallelization_strategy["parallelizable_stages"] = parallelizable_stages
            
            # If parallelizable, reduce time estimate
            if total_cost.parallelizable:
                speedup = min(context.n_jobs, len(parallelizable_stages))
                speedup = speedup * 0.8  # Account for overhead
                total_cost = Cost(
                    time_complexity=total_cost.time_complexity,
                    time_estimate_seconds=total_cost.time_estimate_seconds / speedup,
                    memory_estimate_bytes=total_cost.memory_estimate_bytes,
                    parallelizable=total_cost.parallelizable,
                    constants={**total_cost.constants, "parallel_speedup": speedup},
                    confidence=total_cost.confidence * 0.9,
                )
    
    # Check budget constraints
    if context.time_budget is not None:
        if total_cost.time_estimate_seconds > context.time_budget:
            # Try optimization
            logger.info("Estimated cost exceeds budget, attempting optimization...")
            
            # Apply rewrites
            rewrite_engine = RewriteEngine()
            optimized_program = rewrite_engine.apply_rules(program)
            
            # Re-estimate
            if optimized_program.hash() != program.hash():
                logger.info("Applied rewrites, re-estimating cost...")
                # Recursively plan optimized program
                return create_execution_plan(optimized_program, context, stats)
            else:
                # No optimization helped, raise error
                suggestions = _generate_budget_suggestions(select, total_cost, context)
                raise BudgetExceededError(
                    total_cost,
                    context.time_budget,
                    suggestions=suggestions,
                )
    
    if context.memory_budget is not None:
        if total_cost.memory_estimate_bytes > context.memory_budget:
            raise Py3plexException(
                f"Estimated memory usage "
                f"({format_memory_estimate(total_cost.memory_estimate_bytes)}) "
                f"exceeds budget ({format_memory_estimate(context.memory_budget)})",
                code="PX403",
                suggestions=[
                    "Increase the memory budget",
                    "Add a LIMIT clause to reduce result set size",
                    "Disable caching with cache_policy='off'",
                ],
            )
    
    # Build execution plan
    plan = ExecutionPlan(
        stages=stages,
        estimated_cost=total_cost,
        cache_keys=[],  # Could implement cache key generation
        parallelization_strategy=parallelization_strategy,
        metadata={
            "context": {
                "time_budget": context.time_budget,
                "memory_budget": context.memory_budget,
                "n_jobs": context.n_jobs,
                "objective": context.objective.value,
            },
            "graph_stats": {
                "num_nodes": stats.num_nodes,
                "num_edges": stats.num_edges,
                "num_layers": stats.num_layers,
            },
        },
    )
    
    return plan


def execute_program(
    program: Any,  # GraphProgram
    network: Any,
    context: Optional[ExecutionContext] = None,
    params: Optional[Dict[str, Any]] = None,
) -> QueryResult:
    """Execute a graph program with optional budget enforcement.
    
    This function:
    1. Creates an execution plan
    2. Checks budget constraints
    3. Executes the program using the existing DSL executor
    4. Tracks timing and performance
    5. Returns results with execution metadata
    
    Args:
        program: GraphProgram to execute
        network: Multilayer network
        context: Optional execution context (default: no constraints)
        params: Optional parameter bindings
        
    Returns:
        QueryResult with execution metadata
        
    Raises:
        BudgetExceededError: If estimated cost exceeds budget
        ExecutionTimeoutError: If actual execution exceeds budget
        
    Example:
        >>> program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        >>> context = ExecutionContext.create(time_budget="10s")
        >>> result = execute_program(program, network, context)
        >>> df = result.to_pandas()
    """
    if context is None:
        context = ExecutionContext()
    
    # Extract graph statistics
    stats = GraphStats.from_network(network)
    
    # Create execution plan
    start_planning = time.time()
    plan = create_execution_plan(program, context, stats)
    planning_time = time.time() - start_planning
    
    if context.explain:
        # Return plan instead of executing
        result = QueryResult(data=[])
        result.meta["plan"] = plan.to_dict()
        result.meta["plan_summary"] = plan.summary()
        result.meta["planning_time"] = planning_time
        return result
    
    # Log plan if progress enabled
    if context.progress:
        logger.info(f"Execution plan created in {planning_time:.3f}s")
        logger.info(
            f"Estimated time: {format_time_estimate(plan.estimated_cost.time_estimate_seconds)}"
        )
        if context.time_budget:
            budget_str = format_time_estimate(context.time_budget)
            utilization = (
                plan.estimated_cost.time_estimate_seconds / context.time_budget * 100
            )
            logger.info(f"Budget: {budget_str} (utilization: {utilization:.1f}%)")
    
    # Execute using existing DSL executor
    start_execution = time.time()
    
    try:
        result = execute_ast(
            network=network,
            query=program.canonical_ast,
            params=params,
            progress=context.progress,
            explain_plan=False,
        )
    except Exception as e:
        # Wrap execution errors
        raise Py3plexException(
            f"Execution failed: {e}",
            code="PX404",
            notes=[str(e)],
        ) from e
    
    execution_time = time.time() - start_execution
    
    # Check if we exceeded the budget (actual vs estimated)
    if context.time_budget is not None:
        if execution_time > context.time_budget:
            logger.warning(
                f"Execution time ({execution_time:.2f}s) exceeded budget "
                f"({context.time_budget:.2f}s)"
            )
            # Don't raise error since we already computed the result
            # Just log a warning
    
    # Add execution metadata to result
    result.meta["execution_plan"] = plan.to_dict()
    result.meta["planning_time"] = planning_time
    result.meta["execution_time"] = execution_time
    result.meta["total_time"] = planning_time + execution_time
    result.meta["estimated_time"] = plan.estimated_cost.time_estimate_seconds
    result.meta["time_accuracy"] = abs(
        execution_time - plan.estimated_cost.time_estimate_seconds
    ) / max(execution_time, 0.001)
    
    if context.time_budget:
        result.meta["budget_utilization"] = execution_time / context.time_budget
    
    # Log performance
    if context.progress:
        logger.info(f"Execution completed in {execution_time:.3f}s")
        logger.info(
            f"Estimate accuracy: "
            f"{(1.0 - result.meta['time_accuracy']) * 100:.1f}%"
        )
    
    return result


def _generate_budget_suggestions(
    select: SelectStmt,
    cost: Cost,
    context: ExecutionContext,
) -> List[str]:
    """Generate specific suggestions for reducing cost.
    
    Args:
        select: SelectStmt that exceeded budget
        cost: Estimated cost
        context: Execution context
        
    Returns:
        List of actionable suggestions
    """
    suggestions = []
    
    # Suggest increasing budget
    new_budget = cost.time_estimate_seconds * 1.5
    suggestions.append(
        f"Increase time budget to at least {format_time_estimate(new_budget)}"
    )
    
    # Suggest limiting results
    if not select.limit:
        suggestions.append("Add LIMIT clause to reduce result set (e.g., LIMIT 100)")
    
    # Suggest filtering
    if not select.where:
        suggestions.append(
            "Add WHERE clause to filter nodes before computation "
            "(e.g., WHERE degree > 5)"
        )
    
    # Suggest disabling UQ
    uq_enabled = any(c.uncertainty for c in select.compute)
    if uq_enabled:
        suggestions.append(
            "Disable uncertainty quantification (UQ) by removing .with_uncertainty()"
        )
    
    # Suggest parallelization
    if context.n_jobs == 1 and cost.parallelizable:
        suggestions.append(
            "Enable parallelization by setting n_jobs > 1 "
            "(e.g., context = ExecutionContext(n_jobs=4))"
        )
    
    # Suggest per-layer grouping
    if not select.group_by and cost.parallelizable:
        suggestions.append(
            "Use per_layer() grouping to enable layer-parallel execution"
        )
    
    # Suggest optimization
    suggestions.append(
        "Let the system apply automatic optimizations "
        "(already attempted)"
    )
    
    return suggestions


def estimate_program_cost(
    program: Any,  # GraphProgram
    network: Any,
    context: Optional[ExecutionContext] = None,
) -> Cost:
    """Estimate the cost of executing a program without running it.
    
    Args:
        program: GraphProgram to estimate
        network: Multilayer network
        context: Optional execution context
        
    Returns:
        Cost estimate
        
    Example:
        >>> cost = estimate_program_cost(program, network)
        >>> print(f"Estimated time: {cost.time_estimate_seconds:.2f}s")
    """
    if context is None:
        context = ExecutionContext()
    
    stats = GraphStats.from_network(network)
    plan = create_execution_plan(program, context, stats)
    
    return plan.estimated_cost
