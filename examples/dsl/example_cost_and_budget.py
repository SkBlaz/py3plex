"""Example: Cost estimation and budget enforcement for graph programs.

This example demonstrates:
1. Creating graph programs with cost estimates
2. Setting time budgets
3. Handling budget exceeded errors
4. Optimizing programs to fit budgets
5. Execution planning
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.program import (
    GraphProgram,
    ExecutionContext,
    BudgetExceededError,
    execute_program,
    estimate_program_cost,
    format_time_estimate,
)


def create_example_network():
    """Create a multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False)
    
    print("Creating multilayer network...")
    
    # Add nodes across two layers
    nodes = []
    for i in range(500):
        nodes.append({"source": f"person_{i}", "type": "social"})
        if i % 2 == 0:
            nodes.append({"source": f"person_{i}", "type": "work"})
    net.add_nodes(nodes)
    
    # Add edges (social network)
    edges = []
    for i in range(450):
        edges.append({
            "source": f"person_{i}",
            "target": f"person_{i+1}",
            "source_type": "social",
            "target_type": "social",
        })
    
    # Add edges (work network)
    for i in range(0, 250, 2):
        edges.append({
            "source": f"person_{i}",
            "target": f"person_{i+2}",
            "source_type": "work",
            "target_type": "work",
        })
    net.add_edges(edges)
    
    print(f"  Nodes: {net.node_count}")
    print(f"  Edges: {net.edge_count}")
    print()
    
    return net


def example_1_basic_cost_estimation():
    """Example 1: Basic cost estimation."""
    print("=" * 60)
    print("Example 1: Basic Cost Estimation")
    print("=" * 60)
    
    net = create_example_network()
    
    # Create a simple program
    program = GraphProgram.from_ast(
        Q.nodes().compute("degree").to_ast()
    )
    
    # Estimate cost
    cost = estimate_program_cost(program, net)
    
    print(f"Program: {program.explain()}")
    print()
    print(f"Estimated cost:")
    print(f"  Time: {format_time_estimate(cost.time_estimate_seconds)}")
    print(f"  Complexity: {cost.time_complexity}")
    print(f"  Confidence: {cost.confidence:.0%}")
    print()


def example_2_budget_enforcement():
    """Example 2: Budget enforcement."""
    print("=" * 60)
    print("Example 2: Budget Enforcement")
    print("=" * 60)
    
    net = create_example_network()
    
    # Create an expensive program
    program = GraphProgram.from_ast(
        Q.nodes().compute("betweenness_centrality").to_ast()
    )
    
    print("Program: Compute betweenness centrality")
    print()
    
    # Estimate cost first
    cost = estimate_program_cost(program, net)
    print(f"Estimated time: {format_time_estimate(cost.time_estimate_seconds)}")
    print()
    
    # Try with very tight budget
    print("Attempting execution with 0.1s budget...")
    try:
        context = ExecutionContext.create(time_budget="0.1s")
        result = execute_program(program, net, context)
        print("Success!")
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e}")
        print()
        print("Suggestions:")
        for i, suggestion in enumerate(e.suggestions, 1):
            print(f"  {i}. {suggestion}")
    print()
    
    # Try with reasonable budget
    print("Attempting execution with reasonable budget...")
    reasonable_budget = cost.time_estimate_seconds * 2
    context = ExecutionContext.create(
        time_budget=reasonable_budget,
        progress=False
    )
    result = execute_program(program, net, context)
    print(f"Success! Completed in {result.meta['execution_time']:.3f}s")
    print()


def example_3_execution_planning():
    """Example 3: Execution planning and explain mode."""
    print("=" * 60)
    print("Example 3: Execution Planning")
    print("=" * 60)
    
    net = create_example_network()
    
    # Create a complex program
    program = GraphProgram.from_ast(
        Q.nodes()
        .compute("degree")
        .compute("betweenness_centrality")
        .where(lambda n: n["degree"] > 5)
        .order_by("degree", reverse=True)
        .limit(10)
        .to_ast()
    )
    
    print("Complex program with multiple stages")
    print()
    
    # Get execution plan without executing
    context = ExecutionContext(explain=True, progress=False)
    result = execute_program(program, net, context)
    
    print(result.meta["plan_summary"])
    print()


def example_4_parallelization():
    """Example 4: Parallel execution."""
    print("=" * 60)
    print("Example 4: Parallel Execution")
    print("=" * 60)
    
    net = create_example_network()
    
    program = GraphProgram.from_ast(
        Q.nodes().compute("degree").to_ast()
    )
    
    # Sequential execution
    print("Sequential execution (n_jobs=1):")
    cost_seq = estimate_program_cost(program, net)
    print(f"  Estimated time: {format_time_estimate(cost_seq.time_estimate_seconds)}")
    
    # Parallel execution
    print()
    print("Parallel execution (n_jobs=4):")
    context_par = ExecutionContext(n_jobs=4, progress=False)
    
    # Create plan to see parallelization strategy
    from py3plex.dsl.program import GraphStats, create_execution_plan
    stats = GraphStats.from_network(net)
    plan = create_execution_plan(program, context_par, stats)
    
    print(f"  Estimated time: {format_time_estimate(plan.estimated_cost.time_estimate_seconds)}")
    print(f"  Parallelization strategy: {plan.parallelization_strategy}")
    print()


def example_5_optimization():
    """Example 5: Program optimization with cost constraints."""
    print("=" * 60)
    print("Example 5: Cost-Based Optimization")
    print("=" * 60)
    
    net = create_example_network()
    
    # Create program
    program = GraphProgram.from_ast(
        Q.nodes()
        .compute("degree")
        .compute("betweenness_centrality")
        .to_ast()
    )
    
    print("Original program:")
    cost_orig = estimate_program_cost(program, net)
    print(f"  Estimated time: {format_time_estimate(cost_orig.time_estimate_seconds)}")
    print()
    
    # Optimize
    print("Optimizing program...")
    from py3plex.dsl.program import CostObjective
    optimized = program.optimize(objective=CostObjective.MIN_TIME)
    
    cost_opt = estimate_program_cost(optimized, net)
    print(f"  Optimized time: {format_time_estimate(cost_opt.time_estimate_seconds)}")
    print()


def example_6_comparing_algorithms():
    """Example 6: Compare costs of different algorithms."""
    print("=" * 60)
    print("Example 6: Algorithm Cost Comparison")
    print("=" * 60)
    
    net = create_example_network()
    
    algorithms = [
        ("degree", "Degree Centrality"),
        ("betweenness_centrality", "Betweenness Centrality"),
        ("closeness_centrality", "Closeness Centrality"),
        ("pagerank", "PageRank"),
        ("clustering", "Clustering Coefficient"),
    ]
    
    print("Comparing algorithm costs:")
    print()
    
    costs = []
    for algo_name, display_name in algorithms:
        program = GraphProgram.from_ast(
            Q.nodes().compute(algo_name).to_ast()
        )
        cost = estimate_program_cost(program, net)
        costs.append((display_name, cost))
        
        print(f"{display_name:25} {format_time_estimate(cost.time_estimate_seconds):>10}  {cost.time_complexity}")
    
    print()
    print("Choose algorithms based on your time budget!")
    print()


def main():
    """Run all examples."""
    examples = [
        example_1_basic_cost_estimation,
        example_2_budget_enforcement,
        example_3_execution_planning,
        example_4_parallelization,
        example_5_optimization,
        example_6_comparing_algorithms,
    ]
    
    for example_fn in examples:
        try:
            example_fn()
        except Exception as e:
            print(f"Error in {example_fn.__name__}: {e}")
            print()


if __name__ == "__main__":
    main()
