#!/usr/bin/env python
"""
Example: DSL Sensitivity Analysis - Centrality Robustness
==========================================================

This example demonstrates how to assess the sensitivity of top-k centrality
rankings to network perturbations using the .sensitivity() DSL method.

**Key Concept**: Sensitivity analysis tests robustness of CONCLUSIONS
(rankings, sets, communities), NOT uncertainty of VALUES (mean, std, CI).

Comparison with UQ:
-------------------
- **UQ (.uq())**: "What is the uncertainty in betweenness centrality values?"
  → Returns mean ± std, confidence intervals

- **Sensitivity (.sensitivity())**: "How stable is the top-10 ranking under edge noise?"
  → Returns stability curves (Jaccard@k, Kendall-τ vs perturbation strength)
"""

from py3plex.core import multinet
from py3plex.dsl import Q


def main():
    """Run sensitivity analysis on centrality rankings."""
    print("=" * 70)
    print("DSL Sensitivity Analysis - Centrality Robustness")
    print("=" * 70)

    # Create a test multilayer network
    print("\n Creating test network...")
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Add nodes and edges
    edges = [
        # Layer 0: Star topology (a is hub)
        ["a", "L0", "b", "L0", 1.0],
        ["a", "L0", "c", "L0", 1.0],
        ["a", "L0", "d", "L0", 1.0],
        ["a", "L0", "e", "L0", 1.0],
        # Layer 1: Ring topology
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "d", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        ["e", "L1", "a", "L1", 1.0],
        # Inter-layer connections
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
        ["d", "L0", "d", "L1", 1.0],
        ["e", "L0", "e", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    print(
        f"Network: {len(list(net.get_nodes()))} nodes, {len(list(net.get_edges()))} edges"
    )

    # Example 1: Sensitivity of top-k centrality rankings
    print("\n" + "-" * 70)
    print("Example 1: Top-k Centrality Sensitivity to Edge Removal")
    print("-" * 70)

    result = (
        Q.nodes()
        .compute("degree")
        .order_by("-degree")
        .limit(10)
        .sensitivity(
            perturb="edge_drop",
            grid=[0.0, 0.05, 0.1, 0.15, 0.2],
            n_samples=30,
            metrics=["jaccard_at_k(10)", "kendall_tau"],
            seed=42,
        )
        .execute(net)
    )

    # Check if sensitivity was computed
    if result.has_sensitivity:
        print("\n Sensitivity analysis completed")

        # Show stability curves
        print("\nStability Curves:")
        curves = result.sensitivity_curves

        for metric_name, curve in curves.items():
            print(f"\n{metric_name}:")
            for p, stability in zip(curve.grid, curve.values):
                print(f"  p={p:.2f}: {stability:.4f}")

            # Check for collapse point
            collapse = curve.collapse_point
            if collapse is not None:
                print(f"   Collapse point: p={collapse:.2f} (stability < 0.5)")
            else:
                print(f"   No collapse detected (stability remains >= 0.5)")

        # Export to pandas
        print("\n" + "-" * 70)
        print("Stability Curves as DataFrame:")
        print("-" * 70)

        df = result.sensitivity_result.to_pandas(expand_sensitivity=False)
        print(df.to_string(index=False))
    else:
        print("\n Sensitivity analysis not performed")

    # Example 2: Compare with UQ (to show the difference)
    print("\n" + "=" * 70)
    print("Comparison: UQ vs Sensitivity")
    print("=" * 70)

    print("\n--- UQ: Value uncertainty ---")
    uq_result = (
        Q.nodes()
        .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
        .compute("degree")
        .order_by("-degree__mean")
        .limit(5)
        .execute(net)
    )

    uq_df = uq_result.to_pandas(expand_uncertainty=True)
    print(uq_df[["id", "degree", "degree_std", "degree_ci95_low", "degree_ci95_high"]])

    print("\n→ UQ gives: mean ± std, confidence intervals for VALUES")

    print("\n--- Sensitivity: Ranking stability ---")
    sens_result = (
        Q.nodes()
        .compute("degree")
        .order_by("-degree")
        .limit(5)
        .sensitivity(
            perturb="edge_drop",
            grid=[0.0, 0.1, 0.2],
            n_samples=20,
            metrics=["jaccard_at_k(5)", "kendall_tau"],
            seed=42,
        )
        .execute(net)
    )

    if sens_result.has_sensitivity:
        sens_df = sens_result.sensitivity_result.to_pandas(expand_sensitivity=False)
        print(sens_df.to_string(index=False))
        print("\n→ Sensitivity gives: stability curves for CONCLUSIONS")

    # Example 3: Interpret the results
    print("\n" + "=" * 70)
    print("Interpretation")
    print("=" * 70)

    print(
        """
When to use UQ:
- "How confident am I in this centrality VALUE?"
- "What is the measurement uncertainty?"
- Reports: mean ± std, confidence intervals

When to use Sensitivity:
- "How robust is this top-10 RANKING?"
- "At what perturbation level does the ranking collapse?"
- Reports: stability curves, tipping points, influence scores

Both are complementary:
- UQ: "Node A has degree 15 ± 2"
- Sensitivity: "Node A stays in top-10 with 95% stability up to 15% edge removal"
"""
    )

    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
