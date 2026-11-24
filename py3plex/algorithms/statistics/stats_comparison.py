#!/usr/bin/env python3
"""
Statistical Comparison Framework for Multilayer Networks

This module provides statistical methods to compare multilayer networks,
enabling quantification of structural or topological differences across
network ensembles or experimental conditions.

Features:
- Pairwise and multi-group comparisons
- Parametric and non-parametric tests
- Permutation-based hypothesis testing
- Bootstrap confidence intervals
- Multiple comparison correction
- Effect size estimation

References:
    - Kivelä et al. (2014), "Multilayer networks", J. Complex Networks
    - Good, P. (2013), "Permutation Tests: A Practical Guide to Resampling Methods"
    - Efron & Tibshirani (1994), "An Introduction to the Bootstrap"

Authors: py3plex contributors
Date: 2025
"""

import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, kruskal, mannwhitneyu, ttest_ind

from . import multilayer_statistics as mls
from py3plex.uncertainty.resampling_graph import _bootstrap_edges


def compare_multilayer_networks(
    networks: List[Any],
    metrics: Optional[List[str]] = None,
    test: str = "permutation",
    n_permutations: int = 1000,
    alpha: float = 0.05,
    correction: str = "fdr_bh",
    node_mapping: Optional[Dict] = None,
    layer_scope: str = "both",
    custom_metrics: Optional[Dict[str, Callable]] = None,
    *,
    assume_exchangeable: bool = False,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """
    Compare multilayer networks using statistical tests.

    This function computes various metrics for each network and performs
    statistical tests to determine if the differences are significant.

    Args:
        networks: Networks for a descriptive comparison, or a list of
            cohorts containing independent networks. A cohort contributes
            one summary per network and metric/layer.
        assume_exchangeable: Allow inference over node/layer observations
            within flat inputs when the study design makes them exchangeable.
        seed: Seed for randomized permutation tests.
        metrics: List of metric names to compute. Options include:
            - 'average_degree': Mean degree across all layers
            - 'modularity': Community structure strength (requires communities)
            - 'density': Average layer density
            - 'clustering': Average clustering coefficient
            - 'node_activity': Mean node activity across nodes
            - 'coupling_strength': Mean inter-layer coupling
            - 'entropy': Entropy of multiplexity
            Default: ['average_degree', 'density', 'clustering']
        test: Type of statistical test:
            - 'permutation': Permutation test (non-parametric)
            - 't-test': Student's t-test (parametric, 2 groups)
            - 'mann-whitney': Mann-Whitney U test (non-parametric, 2 groups)
            - 'anova': One-way ANOVA (parametric, 2+ groups)
            - 'kruskal': Kruskal-Wallis H test (non-parametric, 2+ groups)
        n_permutations: Number of permutations for permutation test
        alpha: Significance level
        correction: Multiple comparison correction method:
            - 'bonferroni': Bonferroni correction
            - 'holm': Holm-Bonferroni correction
            - 'fdr_bh': Benjamini-Hochberg FDR
            - None: No correction
        node_mapping: Reserved for paired analyses; currently rejected
        layer_scope: Which layers to analyze:
            - 'intralayer': Only within-layer metrics
            - 'interlayer': Only between-layer metrics
            - 'both': Both types
        custom_metrics: Dictionary of custom metric functions

    Returns:
        DataFrame with columns:
            - metric: Name of the metric
            - layer: Layer identifier or 'global'
            - statistic: Test statistic value
            - p_value: Raw p-value
            - adjusted_p_value: Corrected p-value
            - effect_size: Effect size (Cohen's d or similar)
            - significant: Boolean indicating significance
            - mean_group_0, mean_group_1, ...: Mean values per group

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks
        >>>
        >>> # Create sample networks
        >>> net1 = multinet.multi_layer_network(directed=False)
        >>> net1.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> net2 = multinet.multi_layer_network(directed=False)
        >>> net2.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>>
        >>> # Compare networks
        >>> results = compare_multilayer_networks(
        ...     [net1, net2],
        ...     metrics=['density', 'average_degree'],
        ...     test='permutation',
        ...     n_permutations=1000
        ... )
        >>> print(results)

    Raises:
        ValueError: If invalid parameters are provided

    Notes:
        - For small sample sizes (n < 30), prefer permutation or non-parametric tests
        - For normal distributions, parametric tests have more power
        - Always check effect sizes in addition to p-values
    """
    if len(networks) < 2:
        raise ValueError("At least 2 networks required for comparison")

    # Validate test parameter
    valid_tests = ["permutation", "t-test", "mann-whitney", "anova", "kruskal"]
    if test not in valid_tests:
        raise ValueError(
            f"Invalid test '{test}'. Must be one of: {', '.join(valid_tests)}"
        )

    # Set default metrics
    if metrics is None:
        metrics = ["average_degree", "density", "clustering"]

    if node_mapping is not None:
        raise ValueError("node_mapping requires a paired statistical test; only unpaired designs are supported.")
    if layer_scope not in {"both", "intralayer", "interlayer"}:
        raise ValueError(f"Unknown layer_scope: {layer_scope}")
    if test == "permutation" and n_permutations <= 0:
        raise ValueError("n_permutations must be positive")

    cohort_design = all(isinstance(group, (list, tuple)) for group in networks)
    if not cohort_design and any(isinstance(group, (list, tuple)) for group in networks):
        raise ValueError("Use either a flat list of networks or a list of cohorts.")
    if cohort_design:
        if any(not group for group in networks):
            raise ValueError("Each cohort must contain at least one network.")
        flat_networks = [network for group in networks for network in group]
    else:
        flat_networks = networks

    metric_values = _extract_metrics(flat_networks, metrics, layer_scope, custom_metrics)
    rng = np.random.default_rng(seed)
    results = []
    for metric_name, values_dict in metric_values.items():
        for layer_key, values in values_dict.items():
            if cohort_design:
                grouped = []
                start = 0
                for group in networks:
                    stop = start + len(group)
                    grouped.append([np.mean(sample) for sample in values[start:stop] if len(sample)])
                    start = stop
                values = grouped
            results.append(_perform_test(
                values, test=test, n_permutations=n_permutations,
                metric_name=metric_name, layer=layer_key, rng=rng,
                infer=cohort_design or assume_exchangeable,
            ))

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Handle empty results
    if len(df) == 0:
        return pd.DataFrame(
            columns=[
                "metric",
                "layer",
                "statistic",
                "p_value",
                "adjusted_p_value",
                "effect_size",
                "significant",
            ]
        )

    # Apply multiple comparison correction
    if correction and len(df) > 0:
        df = _apply_correction(df, correction, alpha)
    else:
        df["adjusted_p_value"] = df["p_value"]
        df["significant"] = df["p_value"] < alpha

    return df


def _extract_metrics(
    networks: List[Any],
    metrics: List[str],
    layer_scope: str,
    custom_metrics: Optional[Dict[str, Callable]],
) -> Dict[str, Dict[str, List[List[float]]]]:
    """
    Extract metric values from networks.

    Returns:
        Nested dict: {metric_name: {layer: [values_net1, values_net2, ...]}}
    """
    metric_values = {}

    for metric_name in metrics:
        metric_values[metric_name] = {}

        for net_idx, network in enumerate(networks):
            if layer_scope == "interlayer" and metric_name in {"average_degree", "density", "clustering", "entropy"}:
                continue
            if layer_scope == "intralayer" and metric_name == "coupling_strength":
                continue
            layers = _get_layers(network)

            if metric_name == "average_degree":
                values = _compute_average_degree(network, layers)
            elif metric_name == "density":
                values = _compute_density(network, layers)
            elif metric_name == "clustering":
                values = _compute_clustering(network, layers)
            elif metric_name == "node_activity":
                values = _compute_node_activity(network)
            elif metric_name == "coupling_strength":
                values = _compute_coupling_strength(network, layers)
            elif metric_name == "entropy":
                values = _compute_entropy(network)
            elif custom_metrics and metric_name in custom_metrics:
                values = custom_metrics[metric_name](network)
            else:
                warnings.warn(f"Unknown metric: {metric_name}, skipping", stacklevel=2)
                continue

            # Organize by layer
            for layer_key, layer_values in values.items():
                slots = metric_values[metric_name].setdefault(layer_key, [[] for _ in networks])
                slots[net_idx] = list(layer_values)

    return metric_values


def _get_layers(network: Any) -> List[str]:
    """Extract unique layer identifiers from network."""
    return list(network.layers)


def _compute_average_degree(network: Any, layers: List[str]) -> Dict[str, List[float]]:
    """Compute average degree per layer."""
    result = {"global": []}
    all_degrees = []

    for layer in layers:
        layer_degrees = []
        replicas = [node for node in network.get_nodes() if node[1] == layer]
        layer_degrees = [degree for _, degree in network.core_network.subgraph(replicas).degree()]

        if layer_degrees:
            result[f"layer_{layer}"] = layer_degrees
            all_degrees.extend(layer_degrees)

    result["global"] = all_degrees if all_degrees else [0.0]
    return result


def _compute_density(network: Any, layers: List[str]) -> Dict[str, List[float]]:
    """Compute density per layer."""
    result = {}
    densities = []

    for layer in layers:
        density = mls.layer_density(network, layer)
        result[f"layer_{layer}"] = [density]
        densities.append(density)

    result["global"] = densities if densities else [0.0]
    return result


def _compute_clustering(network: Any, layers: List[str]) -> Dict[str, List[float]]:
    """Compute clustering coefficient."""
    result = {"global": []}

    try:
        clustering = mls.multilayer_clustering_coefficient(network)
        if isinstance(clustering, dict):
            all_values = list(clustering.values())
            result["global"] = all_values if all_values else [0.0]
        else:
            result["global"] = [float(clustering)]
    except Exception as e:
        warnings.warn(f"Could not compute clustering: {e}", stacklevel=2)
        result["global"] = [0.0]

    return result


def _compute_node_activity(network: Any) -> Dict[str, List[float]]:
    """Compute node activity for all nodes."""
    activities = []
    nodes = set()

    for edge in network.get_edges(data=True):
        (n1, _), (n2, _) = edge[0], edge[1]
        nodes.add(n1)
        nodes.add(n2)

    for node in nodes:
        activity = mls.node_activity(network, node)
        activities.append(activity)

    return {"global": activities if activities else [0.0]}


def _compute_coupling_strength(
    network: Any, layers: List[str]
) -> Dict[str, List[float]]:
    """Compute inter-layer coupling strength."""
    result = {}
    all_couplings = []

    for i, layer_i in enumerate(layers):
        for layer_j in layers[i + 1 :]:
            coupling = mls.inter_layer_coupling_strength(network, layer_i, layer_j)
            key = f"coupling_{layer_i}_{layer_j}"
            result[key] = [coupling]
            all_couplings.append(coupling)

    result["global"] = all_couplings if all_couplings else [0.0]
    return result


def _compute_entropy(network: Any) -> Dict[str, List[float]]:
    """Compute entropy of multiplexity."""
    try:
        entropy = mls.entropy_of_multiplexity(network)
        return {"global": [entropy]}
    except Exception as e:
        warnings.warn(f"Could not compute entropy: {e}", stacklevel=2)
        return {"global": [0.0]}


def _perform_test(
    values_per_network: List[List[float]],
    test: str,
    n_permutations: int,
    metric_name: str,
    layer: str,
    rng: Optional[np.random.Generator] = None,
    infer: bool = True,
) -> Dict:
    """
    Perform statistical test on metric values.

    Args:
        values_per_network: List of value lists, one per network
        test: Type of test
        n_permutations: Number of permutations
        metric_name: Name of metric
        layer: Layer identifier

    Returns:
        Dictionary with test results
    """
    # Flatten and compute means
    means = [np.mean(vals) if len(vals) else np.nan for vals in values_per_network]

    # Basic result structure
    result = {
        "metric": metric_name,
        "layer": layer,
    }

    # Add group means
    for i, mean_val in enumerate(means):
        result[f"mean_group_{i}"] = mean_val

    # Perform test based on number of groups
    n_groups = len(values_per_network)

    if n_groups < 2 or any(not len(values) or not np.all(np.isfinite(values))
                           for values in values_per_network):
        return {**result, "statistic": np.nan, "p_value": np.nan, "effect_size": np.nan}

    effect_size = (_compute_cohens_d(*values_per_network) if n_groups == 2
                   else _compute_eta_squared(values_per_network))
    if not infer:
        return {**result, "statistic": np.nan, "p_value": np.nan, "effect_size": effect_size}

    try:
        if test == "permutation":
            statistic, p_value = _permutation_test(values_per_network, n_permutations, rng)
        elif test == "t-test" and n_groups == 2:
            statistic, p_value = ttest_ind(
                values_per_network[0],
                values_per_network[1],
                equal_var=False,  # Welch's t-test
            )
        elif test == "mann-whitney" and n_groups == 2:
            statistic, p_value = mannwhitneyu(
                values_per_network[0], values_per_network[1], alternative="two-sided"
            )
        elif test == "anova" and n_groups >= 2:
            statistic, p_value = f_oneway(*values_per_network)
        elif test == "kruskal" and n_groups >= 2:
            statistic, p_value = kruskal(*values_per_network)
        else:
            raise ValueError(f"Test '{test}' not compatible with {n_groups} groups")

        result["statistic"] = float(statistic)
        result["p_value"] = float(p_value)

        result["effect_size"] = effect_size

    except ValueError as e:
        warnings.warn(f"Test failed for {metric_name}/{layer}: {e}", stacklevel=2)
        result["statistic"] = np.nan
        result["p_value"] = np.nan
        result["effect_size"] = effect_size

    return result


def _permutation_test(
    values_per_network: List[List[float]],
    n_permutations: int,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[float, float]:
    """
    Perform permutation test.

    Returns:
        (test_statistic, p_value)
    """
    # Compute observed statistic (difference in means for 2 groups)
    if len(values_per_network) == 2:
        observed_stat = np.mean(values_per_network[0]) - np.mean(values_per_network[1])
    else:
        # For multiple groups, use F-statistic analog
        observed_stat = _compute_f_statistic(values_per_network)

    # Combine all values
    all_values = []
    group_sizes = []
    for vals in values_per_network:
        all_values.extend(vals)
        group_sizes.append(len(vals))

    all_values = np.array(all_values)

    # Perform permutations
    rng = np.random.default_rng() if rng is None else rng
    perm_stats = []
    for _ in range(n_permutations):
        # Shuffle values
        rng.shuffle(all_values)

        # Split back into groups
        perm_groups = []
        start = 0
        for size in group_sizes:
            perm_groups.append(all_values[start : start + size])
            start += size

        # Compute statistic
        if len(perm_groups) == 2:
            perm_stat = np.mean(perm_groups[0]) - np.mean(perm_groups[1])
        else:
            perm_stat = _compute_f_statistic(perm_groups)

        perm_stats.append(perm_stat)

    # Compute p-value
    perm_stats = np.array(perm_stats)
    p_value = (1 + np.count_nonzero(np.abs(perm_stats) >= abs(observed_stat))) / (n_permutations + 1)

    return observed_stat, p_value


def _compute_f_statistic(groups: List[np.ndarray]) -> float:
    """Compute F-statistic for multiple groups."""
    all_values = np.concatenate(groups)
    grand_mean = np.mean(all_values)
    n_total = len(all_values)
    k = len(groups)

    # Between-group variance
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

    # Within-group variance
    ss_within = sum(np.sum((g - np.mean(g)) ** 2) for g in groups)

    # F-statistic
    if ss_within == 0:
        return float("inf") if ss_between > 0 else 0.0

    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (n_total - k)

    return ms_between / ms_within if ms_within > 0 else 0.0


def _compute_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cohen's d effect size.

    Cohen's d = (mean1 - mean2) / pooled_std
    """
    if len(group1) == 0 or len(group2) == 0:
        return 0.0

    n1, n2 = len(group1), len(group2)

    # Need at least 2 samples per group for pooled std calculation
    if n1 < 2 or n2 < 2:
        return 0.0

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std



def _compute_eta_squared(groups: List[List[float]]) -> float:
    """
    Compute eta-squared effect size for multiple groups.

    η² = SS_between / SS_total
    """
    all_values = np.concatenate(groups)
    grand_mean = np.mean(all_values)

    # Total sum of squares
    ss_total = np.sum((all_values - grand_mean) ** 2)

    # Between-group sum of squares
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

    if ss_total == 0:
        return 0.0

    return ss_between / ss_total


def _apply_correction(
    df: pd.DataFrame,
    correction: str,
    alpha: float,
) -> pd.DataFrame:
    """Apply multiple comparison correction."""
    valid = np.isfinite(df["p_value"])
    p_values = df.loc[valid, "p_value"].to_numpy()
    n_tests = len(p_values)

    if correction == "bonferroni":
        adjusted = p_values * n_tests
        adjusted = np.minimum(adjusted, 1.0)
    elif correction == "holm":
        adjusted = _holm_bonferroni(p_values)
    elif correction == "fdr_bh":
        adjusted = _benjamini_hochberg(p_values)
    else:
        raise ValueError(f"Unknown correction method: {correction}")

    df["adjusted_p_value"] = np.nan
    df.loc[valid, "adjusted_p_value"] = adjusted
    df["significant"] = df["adjusted_p_value"] <= alpha

    return df


def _holm_bonferroni(p_values: np.ndarray) -> np.ndarray:
    """Apply Holm-Bonferroni correction."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    adjusted = np.zeros(n)
    for i, p in enumerate(sorted_p):
        adjusted[sorted_indices[i]] = min(1.0, p * (n - i))

    # Enforce monotonicity
    for i in range(1, n):
        adjusted[sorted_indices[i]] = max(
            adjusted[sorted_indices[i]], adjusted[sorted_indices[i - 1]]
        )

    return adjusted


def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    adjusted = np.zeros(n)
    for i in range(n - 1, -1, -1):
        adjusted[sorted_indices[i]] = min(1.0, sorted_p[i] * n / (i + 1))
        if i < n - 1:
            adjusted[sorted_indices[i]] = min(
                adjusted[sorted_indices[i]], adjusted[sorted_indices[i + 1]]
            )

    return adjusted


def bootstrap_confidence_interval(
    networks: List[Any],
    metric_func: Callable,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Tuple[float, float]]:
    """Compute conditional percentile intervals by resampling each graph's edges.

    Each draw retains the node set and multiplex couplings. The interval
    describes variability under exchangeable edge draws within each input graph.
    """
    if n_bootstrap <= 0 or not 0 < confidence_level < 1:
        raise ValueError("Require positive n_bootstrap and confidence_level in (0, 1).")

    rng = np.random.default_rng(seed)
    tail = (1 - confidence_level) / 2
    results = {}
    for i, network in enumerate(networks):
        values = [metric_func(_bootstrap_edges(network, rng)) for _ in range(n_bootstrap)]
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Non-finite bootstrap metric in network {i}.")
        low, high = np.quantile(values, [tail, 1 - tail])
        results[f"group_{i}"] = (float(low), float(high))
    return results
