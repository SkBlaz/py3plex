"""Core data types for sensitivity analysis.

This module defines the data structures for sensitivity analysis results,
distinct from UQ types which focus on statistical uncertainty.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np


@dataclass
class PerturbationSpec:
    """Specification for network perturbation.

    Attributes:
        method: Perturbation method ('edge_drop', 'degree_preserving_rewire', etc.)
        strength: Perturbation strength (e.g., fraction of edges to drop)
        seed: Random seed for reproducibility
        kwargs: Additional method-specific parameters
    """

    method: str
    strength: float
    seed: Optional[int] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "method": self.method,
            "strength": self.strength,
            "seed": self.seed,
            "kwargs": self.kwargs,
        }


@dataclass
class StabilityCurve:
    """Stability curve showing metric vs perturbation strength.

    Attributes:
        metric: Stability metric name (e.g., 'jaccard_at_k(20)', 'kendall_tau')
        grid: Perturbation strength grid points
        values: Stability values at each grid point
        std: Standard deviation at each grid point (across samples)
        collapse_point: Perturbation strength at which stability drops below threshold
    """

    metric: str
    grid: List[float]
    values: List[float]
    std: Optional[List[float]] = None
    collapse_point: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "metric": self.metric,
            "grid": self.grid,
            "values": self.values,
            "std": self.std,
            "collapse_point": self.collapse_point,
        }


@dataclass
class LocalInfluence:
    """Per-node or per-layer influence on stability.

    Attributes:
        scope: Scope of influence ('node', 'layer', 'edge')
        entity_id: ID of the entity (node name, layer name, edge tuple)
        influence_score: Influence score (higher = more influential on instability)
        rank_volatility: Expected rank change per unit perturbation
        top_k_probability: Probability of remaining in top-k across perturbations
    """

    scope: str  # 'node', 'layer', 'edge'
    entity_id: Any  # Node name, layer name, or edge tuple
    influence_score: float
    rank_volatility: Optional[float] = None
    top_k_probability: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "scope": self.scope,
            "entity_id": str(self.entity_id),
            "influence_score": self.influence_score,
            "rank_volatility": self.rank_volatility,
            "top_k_probability": self.top_k_probability,
        }


@dataclass
class SensitivityResult:
    """Container for sensitivity analysis results.

    This is the core result object returned by sensitivity analysis.
    It stores stability curves, influence data, and provenance.

    NOTE: This is NOT a UQ result. It does not contain mean/std/CI for values.
    It contains stability metrics, curves, and influence scores.

    Attributes:
        perturbation: Perturbation specification
        grid: Perturbation strength grid
        curves: Stability curves keyed by metric name
        influence: Local influence data (per-node, per-layer)
        baseline_result: Original query result (unperturbed)
        meta: Metadata including provenance
    """

    perturbation: PerturbationSpec
    grid: List[float]
    curves: Dict[str, StabilityCurve]
    influence: Optional[Dict[str, List[LocalInfluence]]] = None
    baseline_result: Optional[Any] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export.

        Returns:
            Dictionary representation of sensitivity results
        """
        result = {
            "perturbation": self.perturbation.to_dict(),
            "grid": self.grid,
            "curves": {name: curve.to_dict() for name, curve in self.curves.items()},
            "meta": self.meta,
        }

        if self.influence:
            result["influence"] = {
                scope: [inf.to_dict() for inf in influences]
                for scope, influences in self.influence.items()
            }

        return result

    def to_pandas(self, expand_sensitivity: bool = False) -> "pd.DataFrame":
        """Convert sensitivity curves to pandas DataFrame.

        Args:
            expand_sensitivity: If True, creates columns for each metric at each grid point
                               If False, returns curves in long format

        Returns:
            DataFrame with sensitivity data
        """
        import pandas as pd

        if not expand_sensitivity:
            # Long format: one row per (metric, grid_point)
            rows = []
            for metric_name, curve in self.curves.items():
                for grid_val, stability_val in zip(curve.grid, curve.values):
                    row = {
                        "metric": metric_name,
                        "perturbation_strength": grid_val,
                        "stability": stability_val,
                    }
                    if curve.std:
                        idx = curve.grid.index(grid_val)
                        row["stability_std"] = curve.std[idx]
                    rows.append(row)
            return pd.DataFrame(rows)
        else:
            # Wide format: one row per grid point, columns for each metric
            rows = []
            for i, grid_val in enumerate(self.grid):
                row = {"perturbation_strength": grid_val}
                for metric_name, curve in self.curves.items():
                    if i < len(curve.values):
                        row[f"{metric_name}_stability"] = curve.values[i]
                        if curve.std and i < len(curve.std):
                            row[f"{metric_name}_std"] = curve.std[i]
                rows.append(row)
            return pd.DataFrame(rows)

    def get_collapse_points(self, threshold: float = 0.5) -> Dict[str, Optional[float]]:
        """Find collapse points for all metrics.

        Collapse point is the minimum perturbation strength at which
        stability drops below the threshold.

        Args:
            threshold: Stability threshold (default: 0.5)

        Returns:
            Dictionary mapping metric names to collapse points (or None if never collapses)
        """
        collapse_points = {}

        for metric_name, curve in self.curves.items():
            collapse_point = None
            for grid_val, stability_val in zip(curve.grid, curve.values):
                if stability_val < threshold:
                    collapse_point = grid_val
                    break
            collapse_points[metric_name] = collapse_point

        return collapse_points
