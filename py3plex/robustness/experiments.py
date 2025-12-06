"""Experiment functions for robustness analysis on multilayer networks.

This module provides functions for estimating metric distributions under
perturbations and analyzing centrality robustness.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Union

import numpy as np

from py3plex.core import multinet
from .perturbations import Perturbation

# Type aliases
MetricScalar = float
MetricDict = Dict[str, float]
MetricValue = Union[MetricScalar, MetricDict]

# Optional scipy import for Kendall tau
try:
    from scipy.stats import kendalltau
    _KENDALLTAU_AVAILABLE = True
except ImportError:
    kendalltau = None
    _KENDALLTAU_AVAILABLE = False


def estimate_metric_distribution(
    network: multinet.multi_layer_network,
    metric_fn: Callable[[multinet.multi_layer_network], MetricValue],
    perturbation: Perturbation,
    n_samples: int = 100,
    random_state: int | None = None,
) -> dict[str, Any]:
    """Estimate the distribution of a metric under random perturbations.

    Args
    ----
    network : multi_layer_network
        Original multilayer network.
    metric_fn : callable
        Function that computes a metric on a network.
        It must accept a multi_layer_network and return either:
          - a scalar float, or
          - a dict[str, float] mapping metric names to scalar values.
    perturbation : Perturbation
        Perturbation to apply at each sample.
    n_samples : int
        Number of perturbed samples.
    random_state : int or None
        Optional seed for reproducibility.

    Returns
    -------
    result : dict
        If metric_fn returns floats::

            {
              "samples": list[float],
              "summary": {
                "mean": float,
                "std": float,
                "ci95": (low, high),
              },
            }

        If metric_fn returns dicts::

            {
              "samples": list[dict[str, float]],
              "summary": {
                metric_name: {
                  "mean": float,
                  "std": float,
                  "ci95": (low, high),
                },
                ...
              },
            }

    Raises
    ------
    ValueError
        If n_samples <= 0.

    Notes
    -----
    - 95% CI is computed as empirical 2.5th and 97.5th percentiles.
    - This function does not modify the input network.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    rng = np.random.default_rng(random_state)
    samples: list[MetricValue] = []

    for _ in range(n_samples):
        perturbed = perturbation.apply(network, rng)
        value = metric_fn(perturbed)
        samples.append(value)

    # Determine if scalar or dict
    if samples and isinstance(samples[0], dict):
        # Dict case
        summary: dict[str, dict[str, Any]] = {}
        all_keys = set()
        for s in samples:
            if isinstance(s, dict):
                all_keys.update(s.keys())

        for key in all_keys:
            vals = np.array([s.get(key, 0.0) if isinstance(s, dict) else 0.0
                            for s in samples], dtype=float)
            summary[key] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "ci95": (
                    float(np.percentile(vals, 2.5)),
                    float(np.percentile(vals, 97.5)),
                ),
            }

        return {
            "samples": samples,
            "summary": summary,
        }
    else:
        # Scalar case
        vals = np.array([float(s) for s in samples], dtype=float)
        return {
            "samples": [float(s) for s in samples],
            "summary": {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "ci95": (
                    float(np.percentile(vals, 2.5)),
                    float(np.percentile(vals, 97.5)),
                ),
            },
        }


def centrality_robustness(
    network: multinet.multi_layer_network,
    centrality_fn: Callable[[multinet.multi_layer_network], dict[Any, float]],
    perturbation: Perturbation,
    n_samples: int = 100,
    random_state: int | None = None,
) -> dict[str, Any]:
    """Analyze robustness of a node centrality measure under perturbations.

    Parameters
    ----------
    network : multi_layer_network
        Original network.
    centrality_fn : callable
        Function that computes centrality for each node.
        Must return a dict[node_id, float].
    perturbation : Perturbation
        Perturbation to apply at each sample.
    n_samples : int
        Number of perturbed samples.
    random_state : int or None
        Seed for reproducibility.

    Returns
    -------
    result : dict
        ::

            {
              "samples": list[Dict[node, float]],
              "node_stats": {
                 node: {
                    "mean": float,
                    "std": float,
                 },
                 ...
              },
              "rank_stability": {
                 "kendall_tau_mean": float or None,
                 "kendall_tau_std": float or None,
              },
            }

    Raises
    ------
    ValueError
        If n_samples <= 0.

    Notes
    -----
    - Baseline centrality is computed on the original network.
    - For each perturbed network, centrality is recomputed and aligned
      to the same node set as baseline (missing nodes are treated as 0).
    - Rank stability is measured via Kendall tau between the baseline ranking
      and each perturbed ranking. If scipy is not available, rank_stability
      values are set to None.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    rng = np.random.default_rng(random_state)

    # Compute baseline centrality
    c0 = centrality_fn(network)
    nodes = sorted(c0.keys(), key=lambda x: str(x))  # Consistent ordering
    baseline_vals = np.array([c0[n] for n in nodes], dtype=float)

    samples: list[dict[Any, float]] = []
    tau_values: list[float] = []

    for _ in range(n_samples):
        perturbed = perturbation.apply(network, rng)
        c = centrality_fn(perturbed)
        samples.append(c)

        # Build aligned values for this sample
        sample_vals = np.array([c.get(n, 0.0) for n in nodes], dtype=float)

        # Compute Kendall tau if available
        if _KENDALLTAU_AVAILABLE and kendalltau is not None:
            # Handle edge case where all values are the same
            if np.std(baseline_vals) > 0 and np.std(sample_vals) > 0:
                tau, _ = kendalltau(baseline_vals, sample_vals)
                if not np.isnan(tau):
                    tau_values.append(float(tau))

    # Build node_stats
    node_stats: dict[Any, dict[str, float]] = {}
    for node in nodes:
        vals = [c.get(node, 0.0) for c in samples]
        vals_arr = np.array(vals, dtype=float)
        node_stats[node] = {
            "mean": float(np.mean(vals_arr)),
            "std": float(np.std(vals_arr)),
        }

    # Build rank_stability
    if tau_values:
        tau_arr = np.array(tau_values, dtype=float)
        rank_stability = {
            "kendall_tau_mean": float(np.mean(tau_arr)),
            "kendall_tau_std": float(np.std(tau_arr)),
        }
    else:
        rank_stability = {
            "kendall_tau_mean": None,
            "kendall_tau_std": None,
        }

    return {
        "samples": samples,
        "node_stats": node_stats,
        "rank_stability": rank_stability,
    }
