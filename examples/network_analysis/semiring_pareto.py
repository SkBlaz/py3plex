"""Pareto frontier example for multiobjective path optimization.

This example demonstrates:
- Using ParetoSet for multiobjective optimization
- Maintaining non-dominated solutions
- Deterministic ordering for reproducibility
"""

from py3plex.semiring.pareto import ParetoSet


def main():
    """Run Pareto frontier example."""
    print("=" * 60)
    print("Pareto Frontier for Multiobjective Optimization")
    print("=" * 60)
    
    # Create a Pareto set for 2D optimization (minimize both objectives)
    pareto = ParetoSet(max_size=10, epsilon=1e-9)
    
    print("\nScenario: Finding optimal routes considering:")
    print("  Objective 1: Travel time (minimize)")
    print("  Objective 2: Cost (minimize)")
    
    # Add candidate solutions (time, cost)
    candidates = [
        (10.0, 50.0, "Route A: Fast but expensive"),
        (15.0, 30.0, "Route B: Moderate time and cost"),
        (20.0, 20.0, "Route C: Slow but cheap"),
        (12.0, 55.0, "Route D: Dominated by A"),
        (25.0, 25.0, "Route E: Dominated by C"),
        (10.0, 45.0, "Route F: Better than A"),
    ]
    
    print("\nAdding candidate solutions:")
    print("-" * 40)
    
    for time, cost, desc in candidates:
        print(f"  Adding: {desc}")
        print(f"    Vector: (time={time}, cost={cost})")
        pareto.add((time, cost))
        print(f"    Pareto size: {len(pareto.vectors)}")
    
    # Display final Pareto frontier
    print("\nFinal Pareto frontier (non-dominated solutions):")
    print("-" * 40)
    
    for i, vector in enumerate(pareto.to_list(), 1):
        time, cost = vector
        print(f"  {i}. (time={time}, cost={cost})")
        
        # Find which route this corresponds to
        for t, c, desc in candidates:
            if (t, c) == vector:
                print(f"     {desc}")
                break
    
    # Test Pareto operations
    print("\nPareto set properties:")
    print(f"  Size: {len(pareto.vectors)}")
    print(f"  Max size: {pareto.max_size}")
    print(f"  Epsilon: {pareto.epsilon}")
    
    # Verify no vector dominates another
    print("\nVerification: No vector dominates another")
    vectors = pareto.to_list()
    all_non_dominated = True
    
    for i, v1 in enumerate(vectors):
        for j, v2 in enumerate(vectors):
            if i != j and pareto._dominates(v1, v2):
                print(f"  ✗ {v1} dominates {v2}")
                all_non_dominated = False
    
    if all_non_dominated:
        print("  ✓ All solutions are non-dominated")
    
    # Test union operation
    print("\nTesting union operation:")
    pareto2 = ParetoSet(max_size=10, epsilon=1e-9)
    pareto2.add((8.0, 60.0))  # Even faster but more expensive
    pareto2.add((30.0, 15.0))  # Very slow but very cheap
    
    combined = pareto.union(pareto2)
    print(f"  Original size: {len(pareto.vectors)}")
    print(f"  Additional size: {len(pareto2.vectors)}")
    print(f"  Combined size: {len(combined.vectors)}")
    
    print("\n" + "=" * 60)
    print("✓ Example completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
