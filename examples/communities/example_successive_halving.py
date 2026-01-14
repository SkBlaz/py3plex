#!/usr/bin/env python3
"""
Example: Community Detection with Successive Halving Algorithm Selection.

Demonstrates:
- How to use AutoCommunity with Successive Halving strategy
- Racing-based efficient algorithm selection
- Deterministic reproducibility with seed control
- Accessing racing history and provenance

Prerequisites:
- py3plex with community detection algorithms installed

SKIP_CI: slow - Successive Halving evaluates multiple algorithms
"""

from __future__ import annotations

import sys
from typing import Dict

try:
    from py3plex.algorithms.community_detection import AutoCommunity
    from py3plex.core import multinet
except ImportError as exc:  # pragma: no cover
    AutoCommunity = None
    multinet = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty header for sections."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def example_basic_successive_halving() -> None:
    """Example 1: Basic Successive Halving with AutoCommunity."""
    _print_header("Example 1: Basic Successive Halving")

    # Create a network with two clear communities
    network = multinet.multi_layer_network(directed=False)

    # Community 1: nodes 0-4 (densely connected)
    nodes_c1 = [{"source": f"N{i}", "type": "layer1"} for i in range(5)]
    network.add_nodes(nodes_c1)

    edges_c1 = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(5)
        for j in range(i + 1, 5)
    ]

    # Community 2: nodes 5-9 (densely connected)
    nodes_c2 = [{"source": f"N{i}", "type": "layer1"} for i in range(5, 10)]
    network.add_nodes(nodes_c2)

    edges_c2 = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(5, 10)
        for j in range(i + 1, 10)
    ]

    # Bridge between communities (weak connection)
    bridge = [
        {"source": "N4", "target": "N5", "source_type": "layer1", "target_type": "layer1"}
    ]

    network.add_edges(edges_c1 + edges_c2 + bridge)

    print(
        f"Network: {len(list(network.get_nodes()))} nodes, " f"{network.edge_count} edges"
    )

    # Run AutoCommunity with Successive Halving
    print("\nRunning Successive Halving...")
    result = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity", "coverage")
        .strategy("successive_halving", eta=2, rounds=2)
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    # Show winner
    print(f"\nWinner: {result.selected}")
    print(f"Communities found: {result.community_stats.n_communities}")

    # Show racing history summary
    if "racing_history" in result.provenance:
        history = result.provenance["racing_history"]
        print(f"\nRacing summary:")
        print(f"  Total rounds: {len(history['rounds'])}")
        print(f"  Status: {history['status']}")
        print(f"  Total runtime: {history['total_runtime_ms']:.2f} ms")

        # Show elimination progression
        print("\n  Elimination progression:")
        for i, round_rec in enumerate(history["rounds"]):
            print(f"    Round {i}: {len(round_rec['algorithms'])} algorithms")
            print(f"      Survivors: {round_rec['survivors']}")
            if round_rec["eliminated"]:
                print(f"      Eliminated: {round_rec['eliminated']}")


def example_custom_budget() -> None:
    """Example 2: Successive Halving with custom budget configuration."""
    _print_header("Example 2: Custom Budget Configuration")

    # Create a simple network
    network = multinet.multi_layer_network(directed=False)

    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
    network.add_nodes(nodes)

    edges = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(10)
        for j in range(i + 1, 10)
        if (i + j) % 3 == 0
    ]
    network.add_edges(edges)

    print(
        f"Network: {len(list(network.get_nodes()))} nodes, " f"{network.edge_count} edges"
    )

    # Run with custom budget
    print("\nRunning with custom budget configuration...")
    result = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity", "coverage")
        .strategy(
            "successive_halving",
            eta=2,
            budget0={"max_iter": 10, "uq_samples": 15},
            budget_growth=2.0,
            utility_method="mean_minus_std",
        )
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    print(f"\nWinner: {result.selected}")

    # Show budget progression
    if "racing_history" in result.provenance:
        history = result.provenance["racing_history"]
        print("\nBudget progression:")
        for i, round_rec in enumerate(history["rounds"]):
            budget = round_rec["budget"]
            print(f"  Round {i}:")
            print(f"    max_iter: {budget.get('max_iter', 'N/A')}")
            print(f"    uq_samples: {budget.get('uq_samples', 'N/A')}")


def example_with_uq() -> None:
    """Example 3: Successive Halving with uncertainty quantification."""
    _print_header("Example 3: With Uncertainty Quantification")

    # Create a network
    network = multinet.multi_layer_network(directed=False)

    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(12)]
    network.add_nodes(nodes)

    edges = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(12)
        for j in range(i + 1, 12)
        if (i % 4) == (j % 4) or abs(i - j) == 1
    ]
    network.add_edges(edges)

    print(
        f"Network: {len(list(network.get_nodes()))} nodes, " f"{network.edge_count} edges"
    )

    # Run with UQ enabled
    print("\nRunning with UQ enabled...")
    result = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity", "coverage")
        .uq(method="seed", n_samples=20)
        .strategy("successive_halving", eta=2)
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    print(f"\nWinner: {result.selected}")

    # Show statistics
    stats = result.community_stats
    print(f"\nCommunity statistics:")
    print(f"  Number of communities: {stats.n_communities}")
    print(f"  Coverage: {stats.coverage:.3f}" if stats.coverage else "  Coverage: N/A")
    print(
        f"  Stability: {stats.stability_score:.3f}"
        if stats.stability_score
        else "  Stability: N/A"
    )


def example_provenance() -> None:
    """Example 4: Accessing full provenance and history."""
    _print_header("Example 4: Provenance and History")

    # Create a simple network
    network = multinet.multi_layer_network(directed=False)

    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(8)]
    network.add_nodes(nodes)

    edges = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(8)
        for j in range(i + 1, 8)
        if abs(i - j) <= 2
    ]
    network.add_edges(edges)

    # Run with Successive Halving
    result = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity")
        .strategy("successive_halving", eta=2)
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    # Access full provenance
    prov = result.provenance

    print("Provenance metadata:")
    print(f"  Engine: {prov['engine']}")
    print(f"  Version: {prov['py3plex_version']}")
    print(f"  Timestamp: {prov['timestamp_utc']}")
    print(f"  Seed: {prov['seed']}")
    print(f"  Strategy: {prov['strategy']}")

    print("\nRacer configuration:")
    racer_config = prov.get("racer_config", {})
    print(f"  eta: {racer_config.get('eta', 'N/A')}")
    print(f"  utility_method: {racer_config.get('utility_method', 'N/A')}")

    # Show detailed round history
    if "racing_history" in prov:
        history = prov["racing_history"]
        print(f"\nDetailed racing history:")

        for round_rec in history["rounds"]:
            round_num = round_rec["round"]
            print(f"\n  Round {round_num}:")

            # Show utilities for each algorithm
            utilities = round_rec.get("utilities", {})
            for algo_id, utility in utilities.items():
                print(f"    {algo_id}: utility = {utility:.4f}")

            # Show metrics
            metrics = round_rec.get("metrics", [])
            if metrics:
                print(f"    Metrics:")
                for metric_rec in metrics:
                    algo_id = metric_rec["algo_id"]
                    modularity = metric_rec.get("modularity", "N/A")
                    print(f"      {algo_id}: modularity = {modularity}")


def example_comparison_with_default() -> None:
    """Example 5: Compare Successive Halving vs default Pareto strategy."""
    _print_header("Example 5: Strategy Comparison")

    # Create a network
    network = multinet.multi_layer_network(directed=False)

    nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
    network.add_nodes(nodes)

    edges = [
        {
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "layer1",
            "target_type": "layer1",
        }
        for i in range(10)
        for j in range(i + 1, 10)
        if (i // 3) == (j // 3)
    ]
    network.add_edges(edges)

    print(
        f"Network: {len(list(network.get_nodes()))} nodes, " f"{network.edge_count} edges"
    )

    # Run with default Pareto strategy
    print("\n--- Default Pareto Strategy ---")
    result_default = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity", "coverage")
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    print(f"Winner: {result_default.selected}")
    print(f"Communities: {result_default.community_stats.n_communities}")

    # Run with Successive Halving
    print("\n--- Successive Halving Strategy ---")
    result_sh = (
        AutoCommunity()
        .candidates("louvain", "leiden")
        .metrics("modularity", "coverage")
        .strategy("successive_halving", eta=2)
        .seed(DEFAULT_SEED)
        .execute(network)
    )

    print(f"Winner: {result_sh.selected}")
    print(f"Communities: {result_sh.community_stats.n_communities}")

    # Compare runtime (from provenance)
    print("\n--- Comparison ---")

    if "racing_history" in result_sh.provenance:
        sh_runtime = result_sh.provenance["racing_history"]["total_runtime_ms"]
        print(f"Successive Halving runtime: {sh_runtime:.2f} ms")

    print(f"Default winner: {result_default.selected}")
    print(f"SH winner: {result_sh.selected}")


def main() -> int:
    """Run all examples."""
    if IMPORT_ERROR:
        print(f"Import error: {IMPORT_ERROR}", file=sys.stderr)
        print("Please ensure py3plex is properly installed.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("Successive Halving Community Detection Examples")
    print("=" * 70)
    print("\nDemonstrates efficient algorithm selection via racing.")

    try:
        example_basic_successive_halving()
        example_custom_budget()
        example_with_uq()
        example_provenance()
        example_comparison_with_default()

        print("\n" + "=" * 70)
        print(" All examples completed successfully!")
        print("=" * 70)
        print("\nKey takeaways:")
        print("1. Successive Halving efficiently races algorithms with increasing budgets")
        print("2. Deterministic with seed control")
        print("3. Full provenance tracking of racing history")
        print("4. Configurable budgets, utilities, and elimination strategies")

    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
