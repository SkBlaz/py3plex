"""Sensitivity analysis execution engine.

This module implements the core logic for running sensitivity analyses,
including perturbation loops, metric computation, and result aggregation.
"""

import copy
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .types import (
    SensitivityResult,
    PerturbationSpec,
    StabilityCurve,
    LocalInfluence,
)
from .perturbations import apply_perturbation
from .metrics import (
    jaccard_at_k,
    kendall_tau,
    variation_of_information,
    community_flip_probability,
    parse_metric_spec,
)

logger = logging.getLogger(__name__)


def run_sensitivity_analysis(
    network: Any,
    query_executor: Callable,
    query_ast: Any,
    perturb: str,
    grid: List[float],
    n_samples: int = 30,
    seed: Optional[int] = None,
    metrics: Optional[List[str]] = None,
    scope: str = "global",
    **kwargs,
) -> SensitivityResult:
    """Run sensitivity analysis for a query.

    This is the main entry point for sensitivity analysis. It:
    1. Executes the baseline query on the original network
    2. For each perturbation strength in the grid:
       - Generates n_samples perturbed networks
       - Executes the query on each perturbed network
       - Computes stability metrics comparing to baseline
    3. Aggregates results into stability curves
    4. Optionally computes local influence scores

    Args:
        network: Original multilayer network
        query_executor: Function to execute query (takes network, returns QueryResult)
        query_ast: Query AST for provenance
        perturb: Perturbation method ('edge_drop', 'degree_preserving_rewire')
        grid: Perturbation strength grid (e.g., [0.0, 0.05, 0.1, 0.15, 0.2])
        n_samples: Number of samples per grid point
        seed: Random seed for reproducibility
        metrics: Stability metrics to compute (e.g., ['jaccard_at_k(20)', 'kendall_tau'])
        scope: Analysis scope ('global', 'per_node', 'per_layer')
        **kwargs: Additional perturbation-specific parameters

    Returns:
        SensitivityResult with stability curves and influence data
    """
    # Default metrics if none specified
    if metrics is None:
        metrics = ["kendall_tau"]

    # Execute baseline query
    logger.info("Executing baseline query...")
    baseline_result = query_executor(network)

    # Extract baseline ranking/partition
    baseline_data = _extract_conclusion_data(baseline_result)

    # Initialize curves
    curves = {}
    for metric_spec in metrics:
        metric_name, _ = parse_metric_spec(metric_spec)
        curves[metric_spec] = {
            "grid": [],
            "values": [],
            "std": [],
        }

    # Run perturbation loop
    logger.info(
        f"Running sensitivity analysis with {len(grid)} grid points, {n_samples} samples each..."
    )

    for p_idx, perturbation_strength in enumerate(grid):
        logger.debug(
            f"Grid point {p_idx+1}/{len(grid)}: strength={perturbation_strength}"
        )

        # Collect stability values across samples
        sample_values = {metric_spec: [] for metric_spec in metrics}

        for sample_idx in range(n_samples):
            # Compute sample-specific seed
            sample_seed = None
            if seed is not None:
                sample_seed = seed + p_idx * n_samples + sample_idx

            # Apply perturbation
            perturbed_network = apply_perturbation(
                network,
                method=perturb,
                strength=perturbation_strength,
                seed=sample_seed,
                **kwargs,
            )

            # Execute query on perturbed network
            perturbed_result = query_executor(perturbed_network)

            # Extract perturbed data
            perturbed_data = _extract_conclusion_data(perturbed_result)

            # Compute stability metrics
            for metric_spec in metrics:
                metric_name, metric_kwargs = parse_metric_spec(metric_spec)

                stability_value = _compute_stability_metric(
                    metric_name, baseline_data, perturbed_data, **metric_kwargs
                )

                sample_values[metric_spec].append(stability_value)

        # Aggregate samples for this grid point
        for metric_spec in metrics:
            values = sample_values[metric_spec]
            mean_stability = np.mean(values)
            std_stability = np.std(values)

            curves[metric_spec]["grid"].append(perturbation_strength)
            curves[metric_spec]["values"].append(mean_stability)
            curves[metric_spec]["std"].append(std_stability)

    # Convert curves to StabilityCurve objects
    stability_curves = {}
    for metric_spec, curve_data in curves.items():
        stability_curves[metric_spec] = StabilityCurve(
            metric=metric_spec,
            grid=curve_data["grid"],
            values=curve_data["values"],
            std=curve_data["std"],
            collapse_point=_find_collapse_point(
                curve_data["values"], curve_data["grid"]
            ),
        )

    # Compute local influence if requested
    influence_data = None
    if scope in ["per_node", "per_layer"]:
        logger.info(f"Computing {scope} influence scores...")
        influence_data = _compute_local_influence(
            baseline_data,
            stability_curves,
            scope,
        )

    # Build result
    perturbation_spec = PerturbationSpec(
        method=perturb,
        strength=grid[-1] if grid else 0.0,  # Max strength
        seed=seed,
        kwargs=kwargs,
    )

    result = SensitivityResult(
        perturbation=perturbation_spec,
        grid=grid,
        curves=stability_curves,
        influence=influence_data,
        baseline_result=baseline_result,
        meta={
            "n_samples": n_samples,
            "metrics": metrics,
            "scope": scope,
            "provenance": {
                "perturbation": perturbation_spec.to_dict(),
                "grid": grid,
                "n_samples": n_samples,
                "seed": seed,
            },
        },
    )

    return result


def _extract_conclusion_data(query_result: Any) -> Dict[str, Any]:
    """Extract conclusion data from query result.

    This extracts the data needed for stability comparison:
    - Ranking: Ordered list of node IDs
    - Partition: Dict of {node: community_id}
    - Values: Dict of {node: metric_value}

    Args:
        query_result: QueryResult object

    Returns:
        Dictionary with extracted conclusion data
    """
    data = {
        "ranking": [],
        "partition": {},
        "values": {},
        "raw": query_result,
    }

    # Convert to dict format
    if hasattr(query_result, "to_dict"):
        result_dict = query_result.to_dict()
    else:
        result_dict = query_result

    # Extract ranking
    if isinstance(result_dict, dict) and "data" in result_dict:
        items = result_dict["data"]

        if isinstance(items, list):
            # List of dicts (typical DSL result)
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    node_id = item["id"]
                    data["ranking"].append(node_id)

                    # Extract values (for later use)
                    for key, value in item.items():
                        if key != "id" and key != "layer":
                            if key not in data["values"]:
                                data["values"][key] = {}
                            # Handle uncertainty-wrapped values
                            if isinstance(value, dict) and "mean" in value:
                                data["values"][key][node_id] = value["mean"]
                            else:
                                data["values"][key][node_id] = value

                    # Extract community if present
                    if "community" in item or "community_id" in item:
                        comm_id = item.get("community", item.get("community_id"))
                        data["partition"][node_id] = comm_id

    return data


def _compute_stability_metric(
    metric_name: str,
    baseline_data: Dict[str, Any],
    perturbed_data: Dict[str, Any],
    **kwargs,
) -> float:
    """Compute a stability metric comparing baseline to perturbed data.

    Args:
        metric_name: Name of the metric ('jaccard_at_k', 'kendall_tau', etc.)
        baseline_data: Baseline conclusion data
        perturbed_data: Perturbed conclusion data
        **kwargs: Metric-specific parameters

    Returns:
        Stability value
    """
    if metric_name == "jaccard_at_k":
        k = kwargs.get("k", 20)
        return jaccard_at_k(
            baseline_data["ranking"],
            perturbed_data["ranking"],
            k=k,
        )
    elif metric_name == "kendall_tau":
        return kendall_tau(
            baseline_data["ranking"],
            perturbed_data["ranking"],
        )
    elif metric_name == "variation_of_information":
        return variation_of_information(
            baseline_data["partition"],
            perturbed_data["partition"],
        )
    else:
        logger.warning(f"Unknown metric: {metric_name}, returning 0.0")
        return 0.0


def _find_collapse_point(
    values: List[float], grid: List[float], threshold: float = 0.5
) -> Optional[float]:
    """Find the first grid point where stability drops below threshold.

    Args:
        values: Stability values
        grid: Grid points
        threshold: Collapse threshold

    Returns:
        Collapse point or None if never collapses
    """
    for grid_val, stability_val in zip(grid, values):
        if stability_val < threshold:
            return grid_val
    return None


def _compute_local_influence(
    baseline_data: Dict[str, Any],
    stability_curves: Dict[str, StabilityCurve],
    scope: str,
) -> Dict[str, List[LocalInfluence]]:
    """Compute local influence scores.

    This is a simplified implementation. Full implementation would:
    - Track per-node rank changes
    - Compute rank volatility
    - Estimate top-k probabilities

    Args:
        baseline_data: Baseline conclusion data
        stability_curves: Stability curves
        scope: Analysis scope ('per_node', 'per_layer')

    Returns:
        Dictionary mapping scope to list of LocalInfluence objects
    """
    influence_data = {}

    if scope == "per_node":
        # Simplified: Assign uniform influence
        # Full implementation would track per-node rank changes
        ranking = baseline_data["ranking"]
        influences = []

        for rank, node_id in enumerate(ranking):
            influence = LocalInfluence(
                scope="node",
                entity_id=node_id,
                influence_score=1.0 / (rank + 1),  # Higher rank = higher influence
                rank_volatility=None,  # Would compute from tracking
                top_k_probability=None,  # Would compute from tracking
            )
            influences.append(influence)

        influence_data["node"] = influences

    return influence_data
