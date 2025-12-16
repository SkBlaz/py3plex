"""Bootstrap betweenness with uncertainty-first statistics.

Shows how to resample edges, recompute betweenness, and aggregate
into StatValue objects with Bootstrap uncertainty. Dependencies:
py3plex (editable install or sys.path tweak below), numpy, networkx.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Iterable, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import networkx as nx
from py3plex.core import multinet
from py3plex.stats import Bootstrap, Provenance, StatValue

DEFAULT_BOOTSTRAPS = 20
DEFAULT_SEED = 42


def create_example_network() -> multinet.multi_layer_network:
    """Create a small multilayer network with varied betweenness roles."""
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Layer 1: A star pattern
    edges = [
        ["A", "L1", "B", "L1", 1.0],
        ["A", "L1", "C", "L1", 1.0],
        ["A", "L1", "D", "L1", 1.0],
        ["A", "L1", "E", "L1", 1.0],
    ]

    # Layer 2: A chain pattern
    edges.extend([
        ["B", "L2", "C", "L2", 1.0],
        ["C", "L2", "D", "L2", 1.0],
        ["D", "L2", "E", "L2", 1.0],
    ])

    net.add_edges(edges, input_type="list")
    return net


def compute_betweenness_with_bootstrap(
    network: multinet.multi_layer_network,
    node_id: Tuple[str, str],
    n_boot: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> StatValue:
    """Compute betweenness with bootstrap uncertainty estimation."""
    rng = np.random.default_rng(seed)
    graph = network.core_network

    if node_id not in graph:
        return StatValue(0.0, Bootstrap(np.array([0.0])), Provenance("betweenness", "bootstrap", {}))

    bc_original = nx.betweenness_centrality(graph)
    original_value = bc_original.get(node_id, 0.0)

    edges = list(graph.edges(data=True))
    n_edges = len(edges)

    if n_edges == 0:
        return StatValue(0.0, Bootstrap(np.array([0.0])), Provenance("betweenness", "bootstrap", {}))

    bootstrap_samples = []

    for _ in range(n_boot):
        indices = rng.choice(n_edges, size=n_edges, replace=True)
        resampled_edges = [edges[idx] for idx in indices]

        # Build bootstrap graph, summing weights when resampled edges repeat
        graph_boot = type(graph)()
        for u, v, data in resampled_edges:
            weight = data.get('weight', 1.0)
            if graph_boot.has_edge(u, v):
                existing_weight = graph_boot[u][v].get('weight', 1.0)
                graph_boot.add_edge(u, v, weight=existing_weight + weight)
            else:
                graph_boot.add_edge(u, v, weight=weight)

        try:
            bc_boot = nx.betweenness_centrality(graph_boot)
            sample_value = bc_boot.get(node_id, 0.0)
        except Exception:
            sample_value = 0.0

        bootstrap_samples.append(sample_value - original_value)

    uncertainty = Bootstrap(np.array(bootstrap_samples))

    return StatValue(
        value=original_value,
        uncertainty=uncertainty,
        provenance=Provenance(
            algorithm="betweenness",
            uncertainty_method="bootstrap",
            parameters={"n_boot": n_boot, "unit": "edges"},
            seed=seed,
        ),
    )


def select_nodes_to_analyze(graph: Iterable[Tuple[str, str]]) -> Tuple[Tuple[str, str], ...]:
    """Pick representative node-layer pairs to inspect."""
    return tuple(node for node in [
        ("A", "L1"),  # Central hub in L1
        ("C", "L2"),  # Middle of chain in L2
        ("E", "L1"),  # Peripheral in L1
    ] if node in graph)


def display_results(betweenness_stats: Dict[Tuple[str, str], StatValue]) -> None:
    """Print a table of betweenness stats with uncertainty."""
    print("3. Results with Uncertainty:")
    print("-" * 70)
    print(f"{'Node':<15} {'BC':<12} {'Std':<12} {'CI (95%)':<20} {'Robust':<10}")
    print("-" * 70)

    for node, stat in sorted(betweenness_stats.items(), key=lambda x: float(x[1]), reverse=True):
        ci_low, ci_high = stat.ci(0.95)
        node_str = f"{node[0]}-{node[1]}"
        print(f"{node_str:<15} {float(stat):<12.4f} {stat.std():<12.4f} "
              f"[{ci_low:.4f}, {ci_high:.4f}]  {stat.robustness():<10.3f}")

    print("-" * 70)
    print()


def explain_results(betweenness_stats: Dict[Tuple[str, str], StatValue]) -> None:
    """Provide short interpretation notes."""
    print("4. Interpretation:")
    if ("A", "L1") in betweenness_stats:
        stat_a = betweenness_stats[("A", "L1")]
        print(f"   Node A (Layer 1):")
        print(f"     - Betweenness: {float(stat_a):.4f}")
        print(f"     - Std: {stat_a.std():.4f}")
        print(f"     - Robustness: {stat_a.robustness():.3f}")
        if stat_a.robustness() > 0.8:
            print(f"     - High robustness → stable under edge resampling")
        else:
            print(f"     - Lower robustness → sensitive to network perturbations")
    print()


def demonstrate_arithmetic(betweenness_stats: Dict[Tuple[str, str], StatValue]) -> None:
    """Show arithmetic with uncertainty propagation."""
    print("5. Arithmetic with uncertain values...")
    if len(betweenness_stats) >= 2:
        nodes_list = list(betweenness_stats.keys())
        stat1 = betweenness_stats[nodes_list[0]]
        stat2 = betweenness_stats[nodes_list[1]]

        stat_sum = stat1 + stat2
        print(f"   {nodes_list[0]} + {nodes_list[1]}:")
        print(f"     Value: {float(stat_sum):.4f}")
        print(f"     Std: {stat_sum.std():.4f}")
        print(f"     (Uncertainty propagated via Monte Carlo sampling)")
    print()


def demonstrate_summary(betweenness_stats: Dict[Tuple[str, str], StatValue]) -> None:
    """Print the uncertainty summary for a key node."""
    print("6. Querying Uncertainty Details:")
    if ("A", "L1") in betweenness_stats:
        stat = betweenness_stats[("A", "L1")]
        summary = stat.uncertainty.summary(level=0.95)
        print(f"   Node A (L1) uncertainty summary:")
        for key, value in summary.items():
            if key != "ci":
                print(f"     {key}: {value}")
            else:
                print(f"     ci: [{value[0]:.4f}, {value[1]:.4f}]")
    print()


def demonstrate_reproducibility(network: multinet.multi_layer_network) -> None:
    """Show that seeding makes bootstrap outputs repeatable."""
    print("7. Reproducibility via seed:")
    if ("A", "L1") in network.core_network:
        stat_a1 = compute_betweenness_with_bootstrap(network, ("A", "L1"), n_boot=DEFAULT_BOOTSTRAPS, seed=DEFAULT_SEED)
        stat_a2 = compute_betweenness_with_bootstrap(network, ("A", "L1"), n_boot=DEFAULT_BOOTSTRAPS, seed=DEFAULT_SEED)

        print(f"   Run 1: {float(stat_a1):.6f} (std: {stat_a1.std():.6f})")
        print(f"   Run 2: {float(stat_a2):.6f} (std: {stat_a2.std():.6f})")

        if abs(float(stat_a1) - float(stat_a2)) < 1e-10:
            print(f"   ✓ Results are identical (reproducible)")
    print()


def main() -> int:
    """Demonstrate betweenness computation with Bootstrap uncertainty."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Uncertainty-First Statistics: Betweenness with Bootstrap")
    print("=" * 70)
    print()

    print("1. Creating multilayer network...")
    net = create_example_network()
    print(f"   Added {net.core_network.number_of_edges()} edges across 2 layers")
    print(f"   Network has {net.core_network.number_of_nodes()} nodes")
    print()

    print("2. Computing betweenness with Bootstrap uncertainty...")
    print(f"   (Using {DEFAULT_BOOTSTRAPS} bootstrap samples for speed)")
    print()

    nodes_to_analyze = select_nodes_to_analyze(net.core_network)
    betweenness_stats: Dict[Tuple[str, str], StatValue] = {}

    for node in nodes_to_analyze:
        betweenness_stats[node] = compute_betweenness_with_bootstrap(
            net,
            node,
            n_boot=DEFAULT_BOOTSTRAPS,
            seed=DEFAULT_SEED,
        )

    print(f"   Computed betweenness for {len(betweenness_stats)} nodes")
    print()

    display_results(betweenness_stats)
    explain_results(betweenness_stats)
    demonstrate_arithmetic(betweenness_stats)
    demonstrate_summary(betweenness_stats)
    demonstrate_reproducibility(net)

    print("=" * 70)
    print("Key Takeaways:")
    print("- Bootstrap provides empirical uncertainty estimates")
    print("- Uncertainty reflects sensitivity to network perturbations")
    print("- Robustness score quantifies reliability (0-1 scale)")
    print("- Arithmetic operations propagate uncertainty via Monte Carlo")
    print("- Provenance tracks seed for reproducibility")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
