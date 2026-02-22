#!/usr/bin/env python
"""
Example: Bootstrap and Null Model Uncertainty Analysis
=======================================================

This example demonstrates the new bootstrap and null model methods for
uncertainty quantification in network analysis with py3plex.
"""

import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import uncertainty_enabled


def main():
    """Run bootstrap and null model uncertainty examples."""
    print("=" * 70)
    print("Bootstrap and Null Model Uncertainty Analysis")
    print("=" * 70)

    # Create a test network with interesting structure
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        # Layer 0: Star topology (hub-and-spoke)
        ["hub", "L0", "a", "L0", 1.0],
        ["hub", "L0", "b", "L0", 1.0],
        ["hub", "L0", "c", "L0", 1.0],
        ["hub", "L0", "d", "L0", 1.0],
        ["hub", "L0", "e", "L0", 1.0],
        # Layer 1: Triangle + chain
        ["a", "L1", "b", "L1", 1.0],
        ["b", "L1", "c", "L1", 1.0],
        ["c", "L1", "a", "L1", 1.0],
        ["d", "L1", "e", "L1", 1.0],
        # Inter-layer connections
        ["hub", "L0", "hub", "L1", 1.0],
        ["a", "L0", "a", "L1", 1.0],
        ["b", "L0", "b", "L1", 1.0],
        ["c", "L0", "c", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")

    print(f"\nNetwork: {len(list(net.get_nodes()))} nodes, {len(edges)} edges")
    print("Structure: Star topology (L0) + Triangle+Chain (L1)")

    with uncertainty_enabled(n_runs=100):
        # Example 1: Bootstrap with Edge Resampling
        print("\n" + "-" * 70)
        print("Example 1: Bootstrap Uncertainty (Edge Resampling)")
        print("-" * 70)

        bootstrap_result = (
            Q.nodes()
            .compute(
                "degree",
                uncertainty=True,
                method="bootstrap",
                n_boot=100,
                bootstrap_unit="edges",
                ci=0.95,
                random_state=42
            )
            .order_by("-degree")
            .limit(5)
            .execute(net)
        )

    print("\nTop 5 nodes by degree (with 95% CI):")
    df = bootstrap_result.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        deg = row['degree']

        if isinstance(deg, dict):
            mean = deg['mean']
            std = deg['std']
            # Quantiles might be stored with different precision
            quantiles = deg.get('quantiles', {})
            if quantiles:
                # Get the CI bounds (keys may vary slightly due to floating point)
                keys = sorted(quantiles.keys())
                ci_low = quantiles[keys[0]] if keys else mean
                ci_high = quantiles[keys[-1]] if keys else mean
            else:
                ci_low = mean - 1.96 * std
                ci_high = mean + 1.96 * std
            ci_width = ci_high - ci_low
            print(f"  {node_id:>4}: {mean:.2f} +/- {std:.2f}, CI=[{ci_low:.2f}, {ci_high:.2f}], width={ci_width:.2f}")
        else:
            print(f"  {node_id:>4}: {deg}")

    # Example 2: Bootstrap with Node Resampling
    print("\n" + "-" * 70)
    print("Example 2: Bootstrap Uncertainty (Node Resampling)")
    print("-" * 70)

    with uncertainty_enabled(n_runs=50):
        bootstrap_nodes = (
            Q.nodes()
            .compute(
                "clustering",
                uncertainty=True,
                method="bootstrap",
                n_boot=50,
                bootstrap_unit="nodes",
                random_state=42
            )
            .order_by("-clustering")
            .limit(5)
            .execute(net)
        )

    print("\nTop 5 nodes by clustering coefficient (with 95% CI):")
    df = bootstrap_nodes.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        clust = row['clustering']

        if isinstance(clust, dict):
            mean = clust['mean']
            std = clust['std']
            quantiles = clust.get('quantiles', {})
            if quantiles:
                keys = sorted(quantiles.keys())
                ci_low = quantiles[keys[0]] if keys else mean
                ci_high = quantiles[keys[-1]] if keys else mean
            else:
                ci_low = mean - 1.96 * std
                ci_high = mean + 1.96 * std
            print(f"  {node_id:>4}: {mean:.3f} +/- {std:.3f}, CI=[{ci_low:.3f}, {ci_high:.3f}]")
        else:
            print(f"  {node_id:>4}: {clust:.3f}")

    # Example 3: Null Model - Degree-Preserving
    print("\n" + "-" * 70)
    print("Example 3: Null Model Analysis (Degree-Preserving)")
    print("-" * 70)

    with uncertainty_enabled(n_runs=100):
        null_result = (
            Q.nodes()
            .compute(
                "betweenness_centrality",
                uncertainty=True,
                method="null_model",
                n_null=100,
                null_model="degree_preserving",
                random_state=42
            )
            .order_by("-betweenness_centrality")
            .limit(5)
            .execute(net)
        )

    print("\nTop 5 nodes by betweenness (with z-scores and p-values):")
    df = null_result.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        bc = row['betweenness_centrality']

        if isinstance(bc, dict):
            obs = bc['mean']
            null_mean = bc.get('mean_null', 0)
            zscore = bc.get('zscore', 0)
            pvalue = bc.get('pvalue', 1.0)
            sig = "*" if pvalue < 0.05 else ""
            print(f"  {node_id:>4}: obs={obs:.4f}, null={null_mean:.4f}, z={zscore:>6.2f}, p={pvalue:.4f} {sig}")
        else:
            print(f"  {node_id:>4}: {bc:.4f}")

    # Example 4: Comparing Methods
    print("\n" + "-" * 70)
    print("Example 4: Comparing Bootstrap vs Null Model")
    print("-" * 70)

    # Set defaults for comparison
    Q.uncertainty.defaults(random_state=42)

    with uncertainty_enabled(n_runs=50):
        # Bootstrap approach
        boot = (
            Q.nodes()
            .where(id="hub")
            .compute("degree", uncertainty=True, method="bootstrap", n_boot=50)
            .execute(net)
        )

        # Null model approach
        null = (
            Q.nodes()
            .where(id="hub")
            .compute("degree", uncertainty=True, method="null_model", n_null=50)
            .execute(net)
        )

    print("\nHub node degree - Bootstrap vs Null Model:")

    # Bootstrap
    boot_df = boot.to_pandas()
    if len(boot_df) > 0:
        boot_deg = boot_df["degree"].iloc[0]
        if isinstance(boot_deg, dict):
            print(f"  Bootstrap:  mean={boot_deg['mean']:.2f}, std={boot_deg['std']:.2f}")

    # Null model
    null_df = null.to_pandas()
    if len(null_df) > 0:
        null_deg = null_df["degree"].iloc[0]
        if isinstance(null_deg, dict):
            print(f"  Null Model: obs={null_deg['mean']:.2f}, z={null_deg.get('zscore', 0):.2f}, p={null_deg.get('pvalue', 1):.4f}")

    # Reset defaults
    Q.uncertainty.reset()

    # Example 5: Using Global Defaults
    print("\n" + "-" * 70)
    print("Example 5: Using Global Defaults")
    print("-" * 70)

    # Set global defaults
    Q.uncertainty.defaults(
        method="bootstrap",
        n_boot=75,
        ci=0.90,
        bootstrap_unit="edges",
        random_state=42
    )

    print("\nGlobal defaults set:")
    defaults = Q.uncertainty.get_all()
    print(f"  method: {defaults['method']}")
    print(f"  n_boot: {defaults['n_boot']}")
    print(f"  ci: {defaults['ci']}")
    print(f"  bootstrap_unit: {defaults['bootstrap_unit']}")

    # Use defaults (no need to specify parameters)
    result = (
        Q.nodes()
        .compute("degree", uncertainty=True)
        .order_by("-degree")
        .limit(3)
        .execute(net)
    )

    print("\nTop 3 nodes (using global defaults):")
    df = result.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        deg = row['degree']
        if isinstance(deg, dict):
            print(f"  {node_id}: {deg['mean']:.2f} +/- {deg['std']:.2f}")

    # Reset defaults
    Q.uncertainty.reset()

    # Example 6: Multiple Metrics
    print("\n" + "-" * 70)
    print("Example 6: Multiple Metrics with Uncertainty")
    print("-" * 70)

    multi_result = (
        Q.nodes()
        .compute(
            "degree", "betweenness_centrality", "clustering",
            uncertainty=True,
            method="bootstrap",
            n_boot=50,
            random_state=42
        )
        .order_by("-betweenness_centrality")
        .limit(3)
        .execute(net)
    )

    print("\nTop 3 nodes (multiple metrics with uncertainty):")
    df = multi_result.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']

        deg = row['degree']
        bc = row['betweenness_centrality']
        clust = row['clustering']

        print(f"\n  {node_id}:")

        if isinstance(deg, dict):
            print(f"    Degree:      {deg['mean']:.2f} +/- {deg['std']:.2f}")
        if isinstance(bc, dict):
            print(f"    Betweenness: {bc['mean']:.4f} +/- {bc['std']:.4f}")
        if isinstance(clust, dict):
            print(f"    Clustering:  {clust['mean']:.3f} +/- {clust['std']:.3f}")

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
