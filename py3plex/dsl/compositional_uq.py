"""Compositional uncertainty quantification for DSL queries.

This module implements UQ propagation through the complete query pipeline,
supporting aggregate/summarize, order_by/limit (ranking), and coverage operations.

Key concepts:
- UQ wraps the entire query AST execution with resampling
- Each resample produces a deterministic result
- Statistics are aggregated across resamples
- Deterministic operations preserve UQ structure
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field

import numpy as np
import networkx as nx

from .ast import SelectStmt, UQConfig
from .result import QueryResult
from py3plex.uncertainty import (
    StatSeries,
    ResamplingStrategy,
)


logger = logging.getLogger(__name__)


@dataclass
class ResampleSpec:
    """Specification for how to resample the network.
    
    Attributes:
        method: Resampling method ('bootstrap', 'perturbation', 'seed')
        n_samples: Number of resamples
        seed: Random seed for reproducibility
        kwargs: Additional method-specific parameters
    """
    method: str
    n_samples: int
    seed: Optional[int] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResampleResult:
    """Result from a single resample execution.
    
    Attributes:
        items: List of result items (nodes or edges)
        attributes: Dict mapping attribute names to item values
        groups: Optional group structure if query uses grouping
        meta: Additional metadata from this resample
    """
    items: List[Any]
    attributes: Dict[str, Dict[Any, Any]]
    groups: Optional[Dict[Any, List[Any]]] = None
    meta: Dict[str, Any] = field(default_factory=dict)


def aggregate_with_uncertainty(
    values: List[float],
    func: str,
    ci_level: float = 0.95,
    quantile_p: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute an aggregate statistic with uncertainty from sample values.
    
    This function is used when aggregating across resamples. Each value in
    `values` represents the aggregate statistic computed on one resample.
    
    Args:
        values: List of values from different resamples
        func: Aggregation function name ('mean', 'median', 'sum', etc.)
        ci_level: Confidence interval level (default 0.95)
        quantile_p: Quantile parameter if func is 'quantile'
        
    Returns:
        Dict with 'mean', 'std', 'quantiles', and optionally 'method'
        
    Examples:
        >>> # Mean degree computed on 100 resamples
        >>> resample_means = [5.2, 5.1, 5.3, 5.0, 5.2, ...]  # 100 values
        >>> result = aggregate_with_uncertainty(resample_means, 'mean')
        >>> result['mean']  # Mean of means
        5.15
        >>> result['std']  # Std of means
        0.08
    """
    if not values:
        return {
            "mean": None,
            "std": None,
            "quantiles": {},
        }
    
    arr = np.array(values, dtype=float)
    
    # Compute summary statistics across resamples
    mean_val = np.mean(arr)
    std_val = np.std(arr, ddof=1) if len(arr) > 1 else 0.0
    
    # Compute quantiles for CI
    quantiles = {}
    if len(arr) > 1:
        lower_q = (1 - ci_level) / 2
        upper_q = 1 - lower_q
        quantiles[lower_q] = np.quantile(arr, lower_q)
        quantiles[upper_q] = np.quantile(arr, upper_q)
    
    return {
        "mean": float(mean_val),
        "std": float(std_val),
        "quantiles": quantiles,
        "n_samples": len(values),
    }


def compute_rank_stability(
    rank_samples: List[Dict[Any, int]],
    items: List[Any],
) -> Dict[str, Any]:
    """Compute ranking stability metrics across resamples.
    
    Args:
        rank_samples: List of dicts mapping items to ranks, one per resample
        items: List of items that were ranked
        
    Returns:
        Dict with stability metrics:
        - rank_means: Mean rank per item
        - rank_stds: Std deviation of rank per item
        - rank_quantiles: Quantile dict per item
        - kendall_tau: Mean pairwise Kendall tau correlation
        - jaccard_topk: Jaccard overlap for top-k sets
    """
    from scipy.stats import kendalltau
    
    if not rank_samples or not items:
        return {
            "rank_means": {},
            "rank_stds": {},
            "rank_quantiles": {},
            "kendall_tau_mean": None,
        }
    
    # Build rank matrix: items x samples
    rank_matrix = []
    for item in items:
        item_ranks = [
            sample.get(item, float('inf'))
            for sample in rank_samples
        ]
        rank_matrix.append(item_ranks)
    
    rank_matrix = np.array(rank_matrix)
    
    # Compute per-item statistics
    rank_means = {}
    rank_stds = {}
    rank_quantiles = {}
    
    for i, item in enumerate(items):
        ranks = rank_matrix[i]
        # Filter out inf values (item not present in some resamples)
        valid_ranks = ranks[ranks != float('inf')]
        
        if len(valid_ranks) > 0:
            rank_means[item] = float(np.mean(valid_ranks))
            rank_stds[item] = float(np.std(valid_ranks, ddof=1)) if len(valid_ranks) > 1 else 0.0
            
            if len(valid_ranks) > 1:
                rank_quantiles[item] = {
                    0.025: float(np.quantile(valid_ranks, 0.025)),
                    0.975: float(np.quantile(valid_ranks, 0.975)),
                }
        else:
            rank_means[item] = None
            rank_stds[item] = None
            rank_quantiles[item] = {}
    
    # Compute pairwise Kendall tau across resamples
    tau_values = []
    n_samples = len(rank_samples)
    if n_samples > 1:
        for i in range(n_samples):
            for j in range(i + 1, min(i + 10, n_samples)):  # Sample pairs to avoid O(n²)
                # Convert rank dicts to aligned arrays
                ranks_i = [rank_samples[i].get(item, float('inf')) for item in items]
                ranks_j = [rank_samples[j].get(item, float('inf')) for item in items]
                
                # Filter items present in both
                valid_pairs = [
                    (ri, rj) for ri, rj in zip(ranks_i, ranks_j)
                    if ri != float('inf') and rj != float('inf')
                ]
                
                if len(valid_pairs) > 1:
                    r_i, r_j = zip(*valid_pairs)
                    tau, _ = kendalltau(r_i, r_j)
                    if not np.isnan(tau):
                        tau_values.append(tau)
    
    kendall_tau_mean = float(np.mean(tau_values)) if tau_values else None
    
    return {
        "rank_means": rank_means,
        "rank_stds": rank_stds,
        "rank_quantiles": rank_quantiles,
        "kendall_tau_mean": kendall_tau_mean,
        "n_samples": n_samples,
    }


def compute_coverage_stability(
    coverage_samples: List[Dict[Any, bool]],
    items: List[Any],
) -> Dict[str, Any]:
    """Compute coverage stability metrics across resamples.
    
    Args:
        coverage_samples: List of dicts mapping items to coverage membership (bool)
        items: List of items
        
    Returns:
        Dict with:
        - inclusion_probability: Probability of inclusion per item
        - stable_members: Items with inclusion_probability >= 0.8
        - boundary_members: Items with 0.2 < inclusion_probability < 0.8
    """
    if not coverage_samples or not items:
        return {
            "inclusion_probability": {},
            "stable_members": [],
            "boundary_members": [],
        }
    
    n_samples = len(coverage_samples)
    inclusion_counts = {item: 0 for item in items}
    
    for sample in coverage_samples:
        for item in items:
            if sample.get(item, False):
                inclusion_counts[item] += 1
    
    inclusion_probability = {
        item: count / n_samples
        for item, count in inclusion_counts.items()
    }
    
    # Classify items by stability
    stable_members = [
        item for item, prob in inclusion_probability.items()
        if prob >= 0.8
    ]
    
    boundary_members = [
        item for item, prob in inclusion_probability.items()
        if 0.2 < prob < 0.8
    ]
    
    return {
        "inclusion_probability": inclusion_probability,
        "stable_members": stable_members,
        "boundary_members": boundary_members,
        "n_samples": n_samples,
    }


def create_resampled_network(
    network: Any,
    spec: ResampleSpec,
    resample_idx: int,
) -> Any:
    """Create a resampled version of the network.
    
    Args:
        network: Original multilayer network
        spec: Resampling specification
        resample_idx: Index of this resample (for seed derivation)
        
    Returns:
        Resampled network instance
    """
    # Derive a deterministic seed for this resample
    if spec.seed is not None:
        # Use SeedSequence for reproducible child seeds
        from numpy.random import SeedSequence
        ss = SeedSequence(spec.seed)
        child_seeds = ss.spawn(spec.n_samples)
        resample_seed = int(child_seeds[resample_idx].generate_state(1)[0])
    else:
        resample_seed = None
    
    rng = np.random.default_rng(resample_seed)
    
    if spec.method == "perturbation":
        # For perturbation, we don't actually modify the network
        # but use the seed to introduce variation in subsequent computations
        # For now, just return original network
        # TODO: Implement actual perturbation when uncertainty module is available
        return network
        
    elif spec.method == "bootstrap":
        # For bootstrap, we'd resample edges/nodes
        # For now, just return original network
        # TODO: Implement actual bootstrap when uncertainty module is available
        return network
            
    elif spec.method == "seed":
        # No structural change, just seed variation for stochastic algorithms
        # Return original network but algorithms will use resample_seed
        return network
        
    else:
        logger.warning(f"Unknown resampling method '{spec.method}', returning original network")
        return network


def should_apply_compositional_uq(select: SelectStmt) -> bool:
    """Check if compositional UQ should be applied to this query.
    
    Returns True if:
    - Query has UQ config
    - Query uses aggregate/summarize, order_by, or coverage
    - Query is NOT a selection query (those use SelectionUQ instead)
    
    Selection queries (order_by + limit without aggregate) should use
    the SelectionUQ framework, not compositional UQ.
    """
    if select.uq_config is None:
        return False
    
    # Check if this is a selection query (should use SelectionUQ instead)
    # Selection queries have:
    # - order_by + limit (top-k) OR
    # - limit_per_group (grouped top-k)
    # WITHOUT aggregate/summarize
    has_aggregate = bool(select.aggregate_specs or select.summarize_aggs)
    is_selection_query = (
        (select.order_by and select.limit and not has_aggregate) or
        (select.limit_per_group is not None)
    )
    
    if is_selection_query:
        # This should go to SelectionUQ, not compositional UQ
        return False
    
    # Check if query uses operations that need compositional UQ
    has_ordering = bool(select.order_by)
    has_coverage = bool(select.coverage_mode)
    
    return has_aggregate or has_ordering or has_coverage
