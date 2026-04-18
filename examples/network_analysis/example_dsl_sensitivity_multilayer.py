#!/usr/bin/env python
"""
Example: DSL Sensitivity Analysis - Multilayer Network Robustness
==================================================================

This example demonstrates sensitivity analysis specific to multilayer networks,
including layer-specific perturbations and cross-layer stability assessment.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def main():
    """Run multilayer sensitivity analysis."""
    print("=" * 70)
    print("DSL Sensitivity Analysis - Multilayer Network Robustness")
    print("=" * 70)

    # Create a multilayer social network
    print("\n Creating multilayer network...")
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Layer 1: Physical interactions (office)
    office_edges = [
        ["Alice", "office", "Bob", "office", 1.0],
        ["Alice", "office", "Carol", "office", 1.0],
        ["Bob", "office", "David", "office", 1.0],
        ["Carol", "office", "David", "office", 1.0],
        ["David", "office", "Eve", "office", 1.0],
    ]

    # Layer 2: Digital communication (email)
    email_edges = [
        ["Alice", "email", "Bob", "email", 1.0],
        ["Alice", "email", "David", "email", 1.0],
        ["Bob", "email", "Carol", "email", 1.0],
        ["Bob", "email", "Eve", "email", 1.0],
        ["Carol", "email", "David", "email", 1.0],
        ["David", "email", "Eve", "email", 1.0],
    ]

    # Layer 3: Project collaboration
    project_edges = [
        ["Alice", "project", "Carol", "project", 1.0],
        ["Alice", "project", "Eve", "project", 1.0],
        ["Bob", "project", "David", "project", 1.0],
        ["Carol", "project", "Eve", "project", 1.0],
    ]

    # Inter-layer edges (same person across layers)
    inter_layer = [
        ["Alice", "office", "Alice", "email", 1.0],
        ["Alice", "email", "Alice", "project", 1.0],
        ["Bob", "office", "Bob", "email", 1.0],
        ["Bob", "email", "Bob", "project", 1.0],
        ["Carol", "office", "Carol", "email", 1.0],
        ["Carol", "email", "Carol", "project", 1.0],
        ["David", "office", "David", "email", 1.0],
        ["David", "email", "David", "project", 1.0],
        ["Eve", "office", "Eve", "email", 1.0],
        ["Eve", "email", "Eve", "project", 1.0],
    ]

    all_edges = office_edges + email_edges + project_edges + inter_layer
    net.add_edges(all_edges, input_type="list")

    print(
        f"Network: {net.node_count} nodes, {net.edge_count} edges"
    )
    print(f"Layers: {net.layers}")

    # Example 1: Aggregate centrality across layers
    print("\n" + "-" * 70)
    print("Example 1: Multilayer Centrality Sensitivity")
    print("-" * 70)

    result = (
        Q.nodes()
        .from_layers(L["*"])  # All layers
        .compute("degree")
        .order_by("-degree")
        .limit(10)
        .sensitivity(
            perturb="edge_drop",
            grid=[0.0, 0.1, 0.2, 0.3],
            n_samples=20,
            metrics=["jaccard_at_k(5)", "kendall_tau"],
            layer_aware=True,  # Preserve layer structure
            seed=42,
        )
        .execute(net)
    )

    if result.has_sensitivity:
        print("\n Multilayer sensitivity analysis completed")

        # Show how top nodes change
        print("\nTop 5 nodes (baseline):")
        df = result.to_pandas()
        print(df.head(5)[["id", "layer", "degree"]])

        # Show stability
        print("\nStability curves:")
        curves = result.sensitivity_curves
        for metric_name, curve in curves.items():
            print(f"\n{metric_name}:")
            for p, stability in zip(curve.grid, curve.values):
                print(f"  Edge drop {p*100:.0f}%: stability={stability:.4f}")

    # Example 2: Layer-specific sensitivity
    print("\n" + "=" * 70)
    print("Example 2: Layer-Specific Robustness")
    print("=" * 70)

    for layer in ["office", "email", "project"]:
        print(f"\n--- Layer: {layer} ---")

        layer_result = (
            Q.nodes()
            .from_layers(L[layer])
            .compute("degree")
            .order_by("-degree")
            .limit(3)
            .sensitivity(
                perturb="edge_drop",
                grid=[0.0, 0.2, 0.4],
                n_samples=15,
                metrics=["jaccard_at_k(3)"],
                layer_aware=True,
                seed=42,
            )
            .execute(net)
        )

        if layer_result.has_sensitivity:
            curve = layer_result.sensitivity_curves["jaccard_at_k(3)"]
            print(f"Stability at 20% edge drop: {curve.values[1]:.4f}")
            print(f"Stability at 40% edge drop: {curve.values[2]:.4f}")

            if curve.collapse_point:
                print(f" Collapses at: {curve.collapse_point*100:.0f}% edge drop")
            else:
                print(" Stable across all perturbations")

    # Example 3: Degree-preserving rewiring (topology change)
    print("\n" + "=" * 70)
    print("Example 3: Topology Change Sensitivity (Degree-Preserving)")
    print("=" * 70)

    result_rewire = (
        Q.nodes()
        .compute("degree")
        .order_by("-degree")
        .limit(5)
        .sensitivity(
            perturb="degree_preserving_rewire",  # Preserve degrees, change topology
            grid=[0.0, 0.1, 0.2, 0.3],
            n_samples=15,
            metrics=["kendall_tau"],
            layer_aware=True,
            seed=42,
        )
        .execute(net)
    )

    if result_rewire.has_sensitivity:
        curve = result_rewire.sensitivity_curves["kendall_tau"]
        print("\nKendall-tau (ranking correlation) vs rewiring:")
        for p, tau in zip(curve.grid, curve.values):
            print(f"  {p*100:.0f}% rewired: tau={tau:.4f}")

        # Interpretation
        print("\nInterpretation:")
        if curve.values[-1] > 0.7:
            print(" Ranking is robust to topology changes")
        elif curve.values[-1] > 0.4:
            print(" Ranking is moderately sensitive")
        else:
            print(" Ranking is highly sensitive to topology")

    # Example 4: Export and visualization
    print("\n" + "=" * 70)
    print("Example 4: Export Stability Curves")
    print("=" * 70)

    result = (
        Q.nodes()
        .compute("degree")
        .order_by("-degree")
        .sensitivity(
            perturb="edge_drop",
            grid=[0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
            n_samples=20,
            metrics=["jaccard_at_k(5)", "kendall_tau"],
            seed=42,
        )
        .execute(net)
    )

    if result.has_sensitivity:
        # Export to pandas
        df_curves = result.sensitivity_result.to_pandas(expand_sensitivity=False)
        print("\nStability curves as DataFrame:")
        print(df_curves.to_string(index=False))

        # Get collapse points
        collapse = result.sensitivity_result.get_collapse_points(threshold=0.5)
        print("\nCollapse points (stability < 0.5):")
        for metric, point in collapse.items():
            if point:
                print(f"  {metric}: {point*100:.1f}% edge drop")
            else:
                print(f"  {metric}: Never collapses")

    print("\n" + "=" * 70)
    print("Key Takeaways for Multilayer Networks:")
    print("=" * 70)
    print(
        """
1. Layer-aware perturbations preserve multilayer structure
2. Different layers may have different robustness profiles
3. Aggregate metrics can mask layer-specific vulnerabilities
4. Degree-preserving rewiring tests topology dependence
5. Collapse points identify critical perturbation thresholds

Use sensitivity analysis to:
- Identify critical layers for network resilience
- Assess robustness of multilayer centrality measures
- Test sensitivity to missing data (edge_drop)
- Evaluate topology-dependence (rewiring)
"""
    )

    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
