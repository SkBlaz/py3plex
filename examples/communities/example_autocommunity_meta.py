#!/usr/bin/env python3
"""
Example: AutoCommunity Meta-Algorithm for Principled Community Detection.

This example demonstrates the redesigned AutoCommunity as a multi-objective,
uncertainty-aware, null-model-calibrated meta-algorithm for community detection
in multilayer networks.

Key Features Demonstrated:
- Multi-objective evaluation (modularity, stability, coverage)
- Pareto dominance selection (no single scalar objective)
- Uncertainty quantification (node-level confidence)
- Null-model calibration (statistical significance)
- Consensus communities (when multiple algorithms are non-dominated)
- Graph regime diagnostics

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Evaluates multiple algorithms with UQ and null models
"""

from __future__ import annotations

import sys
from typing import Dict

try:
    from py3plex.algorithms.community_detection import AutoCommunity
    from py3plex.core import multinet, random_generators
    import numpy as np
    import pandas as pd
except ImportError as exc:
    AutoCommunity = None
    multinet = None
    random_generators = None
    np = None
    pd = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for sections."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def example_basic_usage() -> None:
    """Example 1: Basic usage with minimal configuration."""
    _print_header("Example 1: Basic AutoCommunity Usage")

    # Create a simple multilayer network with clear structure
    network = multinet.multi_layer_network(directed=False)

    # Add nodes and edges to create two communities
    nodes_layer1 = [{"source": f"N{i}", "type": "social"} for i in range(10)]
    network.add_nodes(nodes_layer1)

    # Dense connections within communities
    for i in range(5):
        for j in range(i+1, 5):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "social", "target_type": "social"
            }])

    for i in range(5, 10):
        for j in range(i+1, 10):
            network.add_edges([{
                "source": f"N{i}", "target": f"N{j}",
                "source_type": "social", "target_type": "social"
            }])

    # Sparse bridge
    network.add_edges([{
        "source": "N4", "target": "N5",
        "source_type": "social", "target_type": "social"
    }])

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run AutoCommunity with minimal config
    print("\nRunning AutoCommunity (basic configuration)...")
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "coverage")
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Display results
    print("\n" + result.explain())

    print("\n--- Community Statistics ---")
    print(f"Number of communities: {result.community_stats.n_communities}")
    print(f"Community sizes: {result.community_stats.community_sizes}")
    print(f"Coverage: {result.community_stats.coverage:.3f}")

    print("\n--- Algorithms Tested ---")
    for algo in result.algorithms_tested:
        print(f"  - {algo}")

    print("\n--- Pareto Front ---")
    for algo in result.pareto_front:
        print(f"  - {algo}")


def example_with_uncertainty() -> None:
    """Example 2: With uncertainty quantification."""
    _print_header("Example 2: AutoCommunity with Uncertainty Quantification")

    # Create a random multilayer network
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=20,
        l=2,
        p=0.3,
        directed=False,
    )

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run with UQ
    print("\nRunning AutoCommunity with uncertainty quantification...")
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "stability", "coverage")
          .uq(method="perturbation", n_samples=30)
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Display results
    print("\n" + result.explain())

    print("\n--- Community Statistics with Uncertainty ---")
    print(f"Number of communities: {result.community_stats.n_communities}")
    print(f"Stability score: {result.community_stats.stability_score:.3f}")
    print(f"Coverage: {result.community_stats.coverage:.3f}")

    # Show node-level confidence
    if result.community_stats.node_confidence:
        print("\n--- Node Confidence (Top 5) ---")
        conf_items = sorted(
            result.community_stats.node_confidence.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for node, conf in conf_items:
            print(f"  {node}: {conf:.3f}")

    # Show evaluation matrix
    print("\n--- Evaluation Matrix ---")
    print(result.evaluation_matrix.to_string(index=False))


def example_with_null_models() -> None:
    """Example 3: With null-model calibration."""
    _print_header("Example 3: AutoCommunity with Null-Model Calibration")

    # Create a network with moderate structure
    network = multinet.multi_layer_network(directed=False)

    # Add 15 nodes in one layer
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
    network.add_nodes(nodes)

    # Create three communities with some noise
    np.random.seed(DEFAULT_SEED)

    # Community 1: nodes 0-4
    for i in range(5):
        for j in range(i+1, 5):
            if np.random.rand() > 0.3:  # 70% connection probability
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    # Community 2: nodes 5-9
    for i in range(5, 10):
        for j in range(i+1, 10):
            if np.random.rand() > 0.3:
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    # Community 3: nodes 10-14
    for i in range(10, 15):
        for j in range(i+1, 15):
            if np.random.rand() > 0.3:
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run with null models
    print("\nRunning AutoCommunity with null-model calibration...")
    print("(This compares community structure to randomized null models)")

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "coverage")
          .null_model(type="configuration", samples=10)
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Display results
    print("\n" + result.explain())

    print("\n--- Null Model Results ---")
    if result.null_model_results:
        z_scores = result.null_model_results.get('z_scores', {})
        if z_scores:
            print("Z-scores (significance relative to null models):")
            for algo_id, z_score in z_scores.items():
                print(f"  {algo_id}: Z={z_score:.3f}")
                if z_score > 3.0:
                    print("    -> Highly significant (p < 0.001)")
                elif z_score > 2.0:
                    print("    -> Significant (p < 0.05)")
                else:
                    print("    -> Weak signal")
    else:
        print("(Null model results not available)")

    print("\n--- Community Statistics ---")
    print(f"Number of communities: {result.community_stats.n_communities}")
    print(f"Coverage: {result.community_stats.coverage:.3f}")


def example_full_pipeline() -> None:
    """Example 4: Full pipeline with all features."""
    _print_header("Example 4: Full AutoCommunity Pipeline")

    # Create a more complex multilayer network
    np.random.seed(DEFAULT_SEED)
    network = random_generators.random_multilayer_ER(
        n=25,
        l=2,
        p=0.25,
        directed=False,
    )

    print(f"Network: {len(network.get_layers())} layers, "
          f"{len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run full pipeline
    print("\nRunning full AutoCommunity pipeline...")
    print("(Multi-objective + UQ + Null models + Pareto selection)")

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "stability", "coverage", "entropy")
          .uq(method="perturbation", n_samples=20)
          .null_model(type="configuration", samples=10)
          .pareto(enabled=True)
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Comprehensive results display
    print("\n" + result.explain(n=10))

    print("\n--- Graph Regime Diagnostics ---")
    if result.graph_regime:
        for feature, value in result.graph_regime.items():
            print(f"  {feature}: {value:.3f}")

    print("\n--- Pareto Front ---")
    print(f"Non-dominated algorithms: {len(result.pareto_front)}")
    for algo in result.pareto_front:
        print(f"  - {algo}")

    print("\n--- Evaluation Matrix ---")
    print(result.evaluation_matrix.to_string(index=False))

    print("\n--- Community Statistics ---")
    stats = result.community_stats
    print(f"Number of communities: {stats.n_communities}")
    print(f"Community sizes: {stats.community_sizes}")
    if stats.stability_score:
        print(f"Stability score: {stats.stability_score:.3f}")
    print(f"Coverage: {stats.coverage:.3f}")
    print(f"Number of orphan nodes: {len(stats.orphan_nodes) if stats.orphan_nodes else 0}")

    # Export to DataFrame
    print("\n--- Exporting to DataFrame ---")
    df = result.to_pandas()
    print(f"DataFrame shape: {df.shape}")
    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    # Export to dict for JSON
    print("\n--- Provenance Information ---")
    prov = result.provenance
    print(f"Random seed: {prov['seed']}")
    print(f"UQ enabled: {prov['uq_enabled']}")
    print(f"Null models enabled: {prov['null_enabled']}")
    print(f"Pareto selection: {prov['pareto_enabled']}")
    print(f"Algorithms tested: {prov['n_candidates']}")
    print(f"Metrics used: {prov['n_metrics']}")


def example_consensus() -> None:
    """Example 5: Consensus communities from Pareto front."""
    _print_header("Example 5: Consensus Communities (Multiple Non-Dominated)")

    # Create a network where multiple algorithms might be non-dominated
    network = multinet.multi_layer_network(directed=False)

    # Build a network with hierarchical structure
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(20)]
    network.add_nodes(nodes)

    np.random.seed(DEFAULT_SEED)

    # Create overlapping communities
    for i in range(10):
        for j in range(i+1, 10):
            if np.random.rand() > 0.4:
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    for i in range(10, 20):
        for j in range(i+1, 20):
            if np.random.rand() > 0.4:
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    # Add cross-community links
    for _ in range(5):
        i = np.random.randint(0, 10)
        j = np.random.randint(10, 20)
        network.add_edges([{
            "source": f"N{i}", "target": f"N{j}",
            "source_type": "layer1", "target_type": "layer1"
        }])

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run with multiple algorithms
    print("\nRunning AutoCommunity to potentially trigger consensus...")

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "coverage")
          .uq(method="perturbation", n_samples=20)
          .pareto(enabled=True)
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Check if consensus was computed
    print("\n" + result.explain())

    if result.selected == "consensus":
        print("\n Consensus partition was computed!")
        print("  (Multiple algorithms were non-dominated on Pareto front)")

        print("\n--- Consensus Statistics ---")
        print(f"Number of non-dominated algorithms: {len(result.pareto_front)}")
        print(f"Algorithms in consensus: {result.pareto_front}")

        if result.community_stats.node_confidence:
            print("\n--- Node Confidence Distribution ---")
            confidences = list(result.community_stats.node_confidence.values())
            print(f"Mean confidence: {np.mean(confidences):.3f}")
            print(f"Min confidence: {np.min(confidences):.3f}")
            print(f"Max confidence: {np.max(confidences):.3f}")

            # Identify core vs. peripheral nodes
            core_threshold = 0.8
            core_nodes = [
                node for node, conf in result.community_stats.node_confidence.items()
                if conf >= core_threshold
            ]
            print(f"\nCore nodes (confidence >= {core_threshold}): {len(core_nodes)}")
            print(f"Peripheral nodes: {len(result.community_stats.node_confidence) - len(core_nodes)}")
    else:
        print(f"\n→ Single winner selected: {result.selected}")
        print("  (One algorithm dominated all others)")


def example_with_infomap() -> None:
    """Example 6: Using Infomap algorithm in AutoCommunity."""
    _print_header("Example 6: AutoCommunity with Infomap")

    # Create a simple multilayer network
    network = multinet.multi_layer_network(directed=False)

    # Add nodes and edges to create clear community structure
    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
    network.add_nodes(nodes)

    # Create 3 communities with 5 nodes each
    for comm_idx in range(3):
        start = comm_idx * 5
        end = start + 5
        for i in range(start, end):
            for j in range(i+1, end):
                network.add_edges([{
                    "source": f"N{i}", "target": f"N{j}",
                    "source_type": "layer1", "target_type": "layer1"
                }])

    # Add sparse bridges between communities
    network.add_edges([
        {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"},
        {"source": "N9", "target": "N10", "source_type": "layer1", "target_type": "layer1"}
    ])

    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{network.edge_count} edges")

    # Run AutoCommunity with infomap included
    print("\nRunning AutoCommunity with louvain, leiden, and infomap...")
    print("Note: Infomap requires a binary to be installed.")
    print("      If not available, it will be gracefully skipped.\n")

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden", "infomap")
          .metrics("modularity", "coverage")
          .seed(DEFAULT_SEED)
          .execute(network)
    )

    # Display results
    print("\n" + result.explain())

    print("\n--- Algorithms Tested ---")
    for algo in result.algorithms_tested:
        print(f"  - {algo}")

    # Check if infomap was successfully used
    if any("infomap" in algo for algo in result.algorithms_tested):
        print("\n✓ Infomap was successfully executed!")
    else:
        print("\n⚠ Infomap was not available or failed gracefully.")
        print("  AutoCommunity continued with available algorithms.")

    print("\n--- Results ---")
    print(f"Selected algorithm: {result.selected}")
    print(f"Number of communities: {result.community_stats.n_communities}")
    print(f"Coverage: {result.community_stats.coverage:.3f}")


def main() -> int:
    """Run all examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex is properly installed.", file=sys.stderr)
        return 1

    print("=" * 80)
    print("AutoCommunity Meta-Algorithm Examples")
    print("=" * 80)
    print("\nDemonstrating multi-objective, uncertainty-aware community detection")
    print("with null-model calibration and Pareto selection.")

    try:
        example_basic_usage()
        example_with_uncertainty()
        example_with_null_models()
        example_full_pipeline()
        example_consensus()
        example_with_infomap()

        print("\n" + "=" * 80)
        print(" All examples completed successfully!")
        print("=" * 80)
        print("\nKey takeaways:")
        print("1. AutoCommunity uses multi-objective evaluation (no single metric)")
        print("2. Pareto dominance selects non-dominated algorithms")
        print("3. Uncertainty quantification provides node-level confidence")
        print("4. Null-model calibration ensures statistical significance")
        print("5. Consensus communities aggregate multiple good solutions")
        print("6. All decisions are inspectable via provenance")
        print("7. Infomap can be used alongside other algorithms when available")

    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
