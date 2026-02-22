#!/usr/bin/env python3
"""
Example 8: Pipeline with Uncertainty-First Statistics

Demonstrate the uncertainty-first statistics system (`py3plex.stats`) inside a
pipeline: compute deterministic stats, bootstrap stats with empirical
uncertainty, filter by robustness, and show arithmetic on `StatValue` objects.
Dependencies: numpy, networkx.

Runtime: FAST (< 10 seconds)
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict

import networkx as nx
import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.core import multinet
from py3plex.pipeline import LoadStep, Pipeline, PipelineStep
from py3plex.stats import Bootstrap, Delta, Gaussian, Provenance, StatValue

DEFAULT_SEED = 42


class ComputeUncertaintyStats(PipelineStep):
    """
    Pipeline step that computes network statistics with uncertainty.

    This step demonstrates how to compute statistics as StatValue objects
    instead of plain floats, making uncertainty first-class in the pipeline.

    Parameters:
        metrics: List of metric names to compute ('degree', 'clustering')
        use_bootstrap: If True, estimate uncertainty via bootstrap
        n_boot: Number of bootstrap samples (if use_bootstrap=True)
        seed: Random seed for reproducibility
    """

    def __init__(self, metrics=None, use_bootstrap=False, n_boot=20, seed=42):
        self.metrics = metrics or ['degree', 'clustering']
        self.use_bootstrap = use_bootstrap
        self.n_boot = n_boot
        self.seed = seed

    def transform(self, network: multinet.multi_layer_network) -> Dict[str, Any]:
        """Compute statistics with uncertainty."""
        results = {
            'network': network,
            'stats': {},
            'uncertainty_method': 'bootstrap' if self.use_bootstrap else 'delta'
        }

        G = network.core_network
        nodes = list(G.nodes())

        for metric in self.metrics:
            if metric == 'degree':
                results['stats']['degree'] = self._compute_degree_with_uncertainty(
                    network, nodes
                )
            elif metric == 'clustering':
                results['stats']['clustering'] = self._compute_clustering_with_uncertainty(
                    network, nodes
                )

        return results

    def _compute_degree_with_uncertainty(self, network, nodes):
        """Compute degree with uncertainty (deterministic or bootstrap)."""
        G = network.core_network

        if not self.use_bootstrap:
            # Deterministic: degree has no uncertainty
            degree_stats = {}
            for node in nodes:
                degree = G.degree(node)
                degree_stats[node] = StatValue(
                    value=degree,
                    uncertainty=Delta(0.0),
                    provenance=Provenance("degree", "delta", {})
                )
            return degree_stats
        else:
            # Bootstrap: resample edges to estimate uncertainty
            return self._bootstrap_degree(network, nodes)

    def _bootstrap_degree(self, network, nodes):
        """Bootstrap degree by resampling edges."""
        G = network.core_network
        edges = list(G.edges(data=True))
        n_edges = len(edges)

        if n_edges == 0:
            return {node: StatValue(0, Delta(0.0), Provenance("degree", "delta", {}))
                    for node in nodes}

        rng = np.random.default_rng(self.seed)

        # Original degrees
        original_degrees = {node: G.degree(node) for node in nodes}

        # Bootstrap samples
        degree_samples = {node: [] for node in nodes}

        for i in range(self.n_boot):
            # Resample edges
            indices = rng.choice(n_edges, size=n_edges, replace=True)
            resampled_edges = [edges[idx] for idx in indices]

            # Create bootstrap graph
            G_boot = type(G)()
            for u, v, data in resampled_edges:
                weight = data.get('weight', 1.0)
                if G_boot.has_edge(u, v):
                    existing_weight = G_boot[u][v].get('weight', 1.0)
                    G_boot.add_edge(u, v, weight=existing_weight + weight)
                else:
                    G_boot.add_edge(u, v, weight=weight)

            # Compute degrees on bootstrap sample
            for node in nodes:
                boot_degree = G_boot.degree(node) if node in G_boot else 0
                # Store difference from original
                degree_samples[node].append(boot_degree - original_degrees[node])

        # Create StatValue objects with Bootstrap uncertainty
        degree_stats = {}
        for node in nodes:
            samples = np.array(degree_samples[node])
            degree_stats[node] = StatValue(
                value=original_degrees[node],
                uncertainty=Bootstrap(samples),
                provenance=Provenance(
                    "degree",
                    "bootstrap",
                    {"n_boot": self.n_boot, "unit": "edges"},
                    seed=self.seed
                )
            )

        return degree_stats

    def _compute_clustering_with_uncertainty(self, network, nodes):
        """Compute clustering coefficient (deterministic for simplicity)."""
        G = network.core_network

        # Convert to simple graph if needed (clustering doesn't support MultiGraph)
        if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
            simple_G = nx.Graph()
            for u, v in G.edges():
                simple_G.add_edge(u, v)
            G = simple_G

        clustering_stats = {}

        try:
            clustering = nx.clustering(G)
            for node in nodes:
                if node in clustering:
                    # For clustering, we use a small Gaussian uncertainty
                    # since clustering is in [0, 1] and sensitive to edge sampling
                    value = clustering[node]
                    # Rough uncertainty estimate based on degree
                    degree = G.degree(node) if node in G else 0
                    # Higher degree -> more stable clustering
                    std_estimate = 0.1 / (1 + degree) if degree > 0 else 0.1

                    clustering_stats[node] = StatValue(
                        value=value,
                        uncertainty=Gaussian(0.0, std_estimate),
                        provenance=Provenance("clustering", "analytic", {})
                    )
                else:
                    clustering_stats[node] = StatValue(
                        0.0,
                        Delta(0.0),
                        Provenance("clustering", "delta", {})
                    )
        except Exception as e:
            # If clustering computation fails, return deterministic zeros
            for node in nodes:
                clustering_stats[node] = StatValue(
                    0.0,
                    Delta(0.0),
                    Provenance("clustering", "delta", {})
                )

        return clustering_stats


class AnalyzeRobustness(PipelineStep):
    """
    Pipeline step that analyzes robustness of computed statistics.

    Filters nodes based on uncertainty metrics like robustness score,
    standard deviation, or CI width.

    Parameters:
        metric: Which statistic to analyze ('degree', 'clustering')
        min_robustness: Minimum robustness threshold (0-1)
        max_std: Maximum standard deviation allowed
    """

    def __init__(self, metric='degree', min_robustness=0.5, max_std=None):
        self.metric = metric
        self.min_robustness = min_robustness
        self.max_std = max_std

    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter nodes by uncertainty criteria."""
        stats = data['stats'][self.metric]

        robust_nodes = []
        uncertain_nodes = []

        for node, stat_value in stats.items():
            robustness = stat_value.robustness()
            std = stat_value.std()

            passes_robustness = robustness >= self.min_robustness
            passes_std = (self.max_std is None) or (std <= self.max_std)

            if passes_robustness and passes_std:
                robust_nodes.append({
                    'node': node,
                    'value': float(stat_value),
                    'std': std,
                    'robustness': robustness,
                    'ci': stat_value.ci(0.95)
                })
            else:
                uncertain_nodes.append({
                    'node': node,
                    'value': float(stat_value),
                    'std': std,
                    'robustness': robustness
                })

        data['robust_nodes'] = robust_nodes
        data['uncertain_nodes'] = uncertain_nodes

        return data


def _run_deterministic_pipeline() -> Dict[str, Any]:
    """Run deterministic (delta uncertainty) pipeline and print highlights."""
    print("8a. Deterministic Statistics Pipeline (Delta uncertainty)")
    print("-" * 70)

    pipe = Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=40, l=2, p=0.12)),
            (
                "stats",
                ComputeUncertaintyStats(
                    metrics=["degree", "clustering"],
                    use_bootstrap=False,
                ),
            ),
            (
                "analyze",
                AnalyzeRobustness(
                    metric="degree",
                    min_robustness=0.9,  # High threshold - deterministic stats will pass
                ),
            ),
        ]
    )

    print("\nRunning deterministic pipeline...")
    result = pipe.run()

    print(f"\nResults:")
    print(f"  Uncertainty method: {result['uncertainty_method']}")
    print(f"  Robust nodes: {len(result['robust_nodes'])}")
    print(f"  Uncertain nodes: {len(result['uncertain_nodes'])}")

    if result["robust_nodes"]:
        sample = result["robust_nodes"][0]
        print(f"\n  Sample node: {sample['node']}")
        print(f"    Value: {sample['value']}")
        print(f"    Std: {sample['std']:.4f}")
        print(f"    Robustness: {sample['robustness']:.4f}")
        print(f"    CI: {sample['ci']}")
    print()
    return result


def _run_bootstrap_pipeline() -> Dict[str, Any]:
    """Run bootstrap-based pipeline and print robustness summaries."""
    print("8b. Bootstrap Statistics Pipeline (empirical uncertainty)")
    print("-" * 70)

    pipe = Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=40, l=2, p=0.12)),
            (
                "stats",
                ComputeUncertaintyStats(
                    metrics=["degree"],
                    use_bootstrap=True,
                    n_boot=20,
                    seed=DEFAULT_SEED,
                ),
            ),
            (
                "analyze",
                AnalyzeRobustness(
                    metric="degree",
                    min_robustness=0.7,  # Lower threshold - some nodes may fail
                    max_std=2.0,
                ),
            ),
        ]
    )

    print("\nRunning bootstrap pipeline...")
    result = pipe.run()

    print(f"\nResults:")
    print(f"  Uncertainty method: {result['uncertainty_method']}")
    print(f"  Robust nodes: {len(result['robust_nodes'])}")
    print(f"  Uncertain nodes: {len(result['uncertain_nodes'])}")

    robust_sorted = sorted(
        result["robust_nodes"], key=lambda x: x["robustness"], reverse=True
    )[:3]

    print(f"\n  Top 3 most robust nodes:")
    for i, node_info in enumerate(robust_sorted, 1):
        print(f"    {i}. Node {node_info['node']}:")
        print(f"       Degree: {node_info['value']:.1f} +/- {node_info['std']:.2f}")
        print(f"       Robustness: {node_info['robustness']:.3f}")
        ci_low, ci_high = node_info["ci"]
        print(f"       95% CI: [{ci_low:.2f}, {ci_high:.2f}]")

    if result["uncertain_nodes"]:
        uncertain_sorted = sorted(
            result["uncertain_nodes"], key=lambda x: x["robustness"]
        )[:3]

        print(f"\n  Top 3 most uncertain nodes:")
        for i, node_info in enumerate(uncertain_sorted, 1):
            print(f"    {i}. Node {node_info['node']}:")
            print(f"       Degree: {node_info['value']:.1f} +/- {node_info['std']:.2f}")
            print(f"       Robustness: {node_info['robustness']:.3f}")
    print()
    return result


def _demo_arithmetic_with_uncertainty(result_boot: Dict[str, Any]) -> None:
    """Show how arithmetic on StatValue propagates uncertainty."""
    print("8c. Arithmetic with StatValue objects")
    print("-" * 70)

    degree_stats = result_boot["stats"]["degree"]
    if len(degree_stats) < 2:
        print("Not enough nodes to demonstrate arithmetic.")
        print()
        return

    nodes_list = list(degree_stats.keys())
    stat_a = degree_stats[nodes_list[0]]
    stat_b = degree_stats[nodes_list[1]]

    print(f"\nNode {nodes_list[0]}: degree = {float(stat_a):.2f} +/- {stat_a.std():.2f}")
    print(f"Node {nodes_list[1]}: degree = {float(stat_b):.2f} +/- {stat_b.std():.2f}")

    stat_sum = stat_a + stat_b
    print(f"\nSum: {float(stat_sum):.2f} +/- {stat_sum.std():.2f}")
    print("  (Uncertainty propagated via Monte Carlo)")

    stat_avg = (stat_a + stat_b) / 2
    print(f"\nAverage: {float(stat_avg):.2f} +/- {stat_avg.std():.2f}")
    print()


def main() -> int:
    """Run the uncertainty-aware pipeline example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 8: Pipeline with Uncertainty-First Statistics")
    print("=" * 70)
    print()

    _run_deterministic_pipeline()
    result_boot = _run_bootstrap_pipeline()
    _demo_arithmetic_with_uncertainty(result_boot)

    print("=" * 70)
    print("Key Takeaways:")
    print("-" * 70)
    print("- Pipeline steps can compute StatValue objects with uncertainty")
    print("- Deterministic stats use Delta(0) for perfect certainty")
    print("- Bootstrap provides empirical uncertainty estimates")
    print("- Robustness filtering helps identify stable vs uncertain nodes")
    print("- StatValue objects support arithmetic with uncertainty propagation")
    print("- All uncertainty info is tracked in provenance for reproducibility")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
