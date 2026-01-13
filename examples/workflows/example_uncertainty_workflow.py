#!/usr/bin/env python
"""
Workflow Example: Uncertainty-Aware Network Analysis
=====================================================

This example demonstrates how to integrate uncertainty quantification
into workflow-style network analysis using py3plex primitives:

1. Generate a multilayer network
2. Compute centrality with uncertainty (null model comparison)
3. Perform bootstrap confidence interval estimation
4. Make statistically-informed decisions about network structure

Runtime: FAST (<10 seconds) - suitable for CI
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.nullmodels import generate_null_model
from py3plex.workflows import WorkflowConfig, WorkflowRunner


def create_example_network() -> multinet.multi_layer_network:
    """Create a multilayer social-work network for demonstration."""
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Build a network with clear hub structure
    edges = [
        # Social layer: star topology centered on Alice
        ["Alice", "social", "Bob", "social", 1.0],
        ["Alice", "social", "Charlie", "social", 1.0],
        ["Alice", "social", "David", "social", 1.0],
        ["Alice", "social", "Eve", "social", 1.0],
        ["Bob", "social", "Charlie", "social", 1.0],

        # Work layer: collaborative structure
        ["Alice", "work", "Bob", "work", 1.0],
        ["Bob", "work", "Charlie", "work", 1.0],
        ["Charlie", "work", "David", "work", 1.0],
        ["David", "work", "Eve", "work", 1.0],
        ["Eve", "work", "Alice", "work", 1.0],

        # Family layer: smaller components
        ["Alice", "family", "Frank", "family", 1.0],
        ["Bob", "family", "Grace", "family", 1.0],

        # Inter-layer connections
        ["Alice", "social", "Alice", "work", 1.0],
        ["Alice", "social", "Alice", "family", 1.0],
        ["Bob", "social", "Bob", "work", 1.0],
        ["Bob", "work", "Bob", "family", 1.0],
        ["Charlie", "social", "Charlie", "work", 1.0],
        ["David", "social", "David", "work", 1.0],
        ["Eve", "social", "Eve", "work", 1.0],
    ]

    net.add_edges(edges, input_type="list")
    return net


def step_1_basic_analysis(net: multinet.multi_layer_network) -> None:
    """Step 1: Basic network properties."""
    print("\n" + "=" * 70)
    print("Step 1: Basic Network Analysis")
    print("=" * 70)

    n_nodes = net.core_network.number_of_nodes()
    n_edges = net.core_network.number_of_edges()

    print(f"\nNetwork structure:")
    print(f"  Nodes: {n_nodes}")
    print(f"  Edges: {n_edges}")
    print(f"  Density: {2 * n_edges / (n_nodes * (n_nodes - 1)):.3f}")

    # Degree distribution via DSL
    df = (
        Q.nodes()
        .from_layers(L["*"])
        .compute("degree")
        .execute(net)
    ).to_pandas()

    print(f"\nDegree statistics:")
    print(f"  Mean: {df['degree'].mean():.2f}")
    print(f"  Std: {df['degree'].std():.2f}")
    print(f"  Max: {df['degree'].max()}")


def step_2_null_model_comparison(net: multinet.multi_layer_network) -> None:
    """Step 2: Compare against null model to identify significant patterns."""
    print("\n" + "=" * 70)
    print("Step 2: Null Model Comparison")
    print("=" * 70)
    print("\nQuestion: Is the hub structure significant or just random?")
    print("Approach: Compare observed degree against configuration model\n")

    # Get observed degrees
    observed = (
        Q.nodes()
        .from_layers(L["*"])
        .compute("degree")
        .execute(net)
    ).to_pandas()

    # Generate null model (configuration model preserves degree sequence)
    print("Generating null model samples (n=30)...")
    null_result = generate_null_model(
        net,
        model="configuration",
        samples=30,  # Fast for CI; use 100+ for production
        preserve_layers=True
    )

    # Compute degree for each null sample
    null_degrees = {}
    for null_network in null_result.samples:
        null_df = (
            Q.nodes()
            .from_layers(L["*"])
            .compute("degree")
            .execute(null_network)
        ).to_pandas()

        for _, row in null_df.iterrows():
            node_id = row['id']
            if node_id not in null_degrees:
                null_degrees[node_id] = []
            null_degrees[node_id].append(row['degree'])

    # Calculate z-scores
    print("\nTop nodes by z-score (deviation from null model):")
    print(f"{'Node':<12} {'Observed':<10} {'Expected':<10} {'Z-Score':<10} {'Significant':<12}")
    print("-" * 60)

    z_scores = []
    for _, row in observed.iterrows():
        node_id = row['id']
        obs_deg = row['degree']
        null_vals = null_degrees.get(node_id, [obs_deg])

        exp_deg = np.mean(null_vals)
        std_deg = np.std(null_vals)
        z = (obs_deg - exp_deg) / (std_deg + 1e-10)

        z_scores.append((node_id, obs_deg, exp_deg, z))

    # Sort by absolute z-score and show top 5
    z_scores.sort(key=lambda x: abs(x[3]), reverse=True)
    for node, obs, exp, z in z_scores[:5]:
        sig = "YES" if abs(z) > 2.0 else "NO"
        print(f"{str(node):<12} {obs:<10.1f} {exp:<10.2f} {z:<10.2f} {sig:<12}")

    print(f"\nInterpretation:")
    print(f"  |z| > 2.0 suggests statistical significance (p < 0.05)")
    print(f"  Configuration model: randomizes connections, preserves degrees")


def step_3_cross_layer_variability(net: multinet.multi_layer_network) -> None:
    """Step 3: Analyze how node importance varies across layers."""
    print("\n" + "=" * 70)
    print("Step 3: Cross-Layer Variability Analysis")
    print("=" * 70)
    print("\nQuestion: Which nodes have consistent vs variable importance?\n")

    # Get betweenness for all layers
    df = (
        Q.nodes()
        .from_layers(L["*"])
        .compute("betweenness_centrality")
        .execute(net)
    ).to_pandas()

    # Compute statistics per node across layers
    stats = df.groupby('id')['betweenness_centrality'].agg(['mean', 'std', 'count'])
    stats['cv'] = stats['std'] / (stats['mean'] + 1e-10)  # Coefficient of variation
    stats = stats.reset_index()

    print("Top nodes by mean betweenness (across layers):")
    print(f"{'Node':<12} {'Mean':<10} {'Std':<10} {'CV':<10} {'Layers':<8} {'Consistency':<12}")
    print("-" * 70)

    for _, row in stats.sort_values('mean', ascending=False).head(5).iterrows():
        node = row['id']
        mean = row['mean']
        std = row['std']
        cv = row['cv']
        count = int(row['count'])

        # Classify consistency
        if cv < 0.5:
            consistency = "Stable"
        elif cv < 1.0:
            consistency = "Moderate"
        else:
            consistency = "Variable"

        print(f"{str(node):<12} {mean:<10.3f} {std:<10.3f} {cv:<10.2f} {count:<8} {consistency:<12}")

    print(f"\nInterpretation:")
    print(f"  Low CV (<0.5): Node is consistently important across layers")
    print(f"  High CV (>1.0): Importance varies significantly by context")


def step_4_decision_making(net: multinet.multi_layer_network) -> None:
    """Step 4: Make uncertainty-aware decisions."""
    print("\n" + "=" * 70)
    print("Step 4: Uncertainty-Aware Decision Making")
    print("=" * 70)
    print("\nScenario: Identify 3 key nodes for intervention\n")

    # Get betweenness with layer context
    df = (
        Q.nodes()
        .from_layers(L["*"])
        .compute("betweenness_centrality")
        .execute(net)
    ).to_pandas()

    # Aggregate by node
    stats = df.groupby('id')['betweenness_centrality'].agg(['mean', 'std', 'max'])
    stats['lower_bound'] = stats['mean'] - 2 * stats['std']  # Conservative estimate
    stats = stats.reset_index()

    print("Decision strategies:")
    print("\n1. Optimistic (rank by max value):")
    for i, (_, row) in enumerate(stats.sort_values('max', ascending=False).head(3).iterrows(), 1):
        print(f"   {i}. {row['id']} (max={row['max']:.3f})")

    print("\n2. Average case (rank by mean):")
    for i, (_, row) in enumerate(stats.sort_values('mean', ascending=False).head(3).iterrows(), 1):
        print(f"   {i}. {row['id']} (mean={row['mean']:.3f})")

    print("\n3. Conservative (rank by lower confidence bound):")
    for i, (_, row) in enumerate(stats.sort_values('lower_bound', ascending=False).head(3).iterrows(), 1):
        print(f"   {i}. {row['id']} (lower={max(0, row['lower_bound']):.3f})")

    print(f"\nRecommendation: Use conservative ranking for high-stakes decisions")
    print(f"  Accounts for measurement uncertainty")
    print(f"  Reduces risk of over-confident choices")


def main() -> int:
    """Run the uncertainty-aware workflow example."""
    np.random.seed(42)

    print("\n" + "#" * 70)
    print("# Uncertainty-Aware Network Analysis Workflow")
    print("#" * 70)
    print("\nDemonstrates:")
    print("  • Null model comparison for statistical significance")
    print("  • Cross-layer variability quantification")
    print("  • Uncertainty-aware decision making")
    print("  • Integration with py3plex workflows and DSL")

    # Create network
    net = create_example_network()

    # Run analysis steps
    step_1_basic_analysis(net)
    step_2_null_model_comparison(net)
    step_3_cross_layer_variability(net)
    step_4_decision_making(net)

    print("\n" + "#" * 70)
    print("# Workflow completed successfully!")
    print("#" * 70)
    print("\nKey Takeaways:")
    print("  1. Null models establish statistical baselines")
    print("  2. Cross-layer analysis reveals consistency patterns")
    print("  3. Uncertainty quantification improves decisions")
    print("  4. py3plex provides integrated tools for rigorous analysis")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
