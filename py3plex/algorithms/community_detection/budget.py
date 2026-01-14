"""Budget specification and management for community detection algorithms.

This module defines budget structures used in algorithm selection and racing
strategies like Successive Halving. Budgets represent computational resource
constraints that can be adjusted across rounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BudgetSpec:
    """Budget specification for community detection algorithms.

    Represents computational resource constraints that can be tuned across
    successive rounds of algorithm evaluation. Not all algorithms use all
    budget parameters; algorithms ignore parameters they don't support.

    Attributes:
        max_iter: Maximum iterations (for iterative algorithms)
        n_restarts: Number of random restarts (for stochastic algorithms)
        resolution_trials: Number of resolution parameter trials
        time_limit_s: Time limit in seconds (optional, default None)
        uq_samples: Number of samples for uncertainty quantification
        n_jobs: Number of parallel jobs (default None means use system default)

    Examples:
        >>> # Conservative starting budget
        >>> b0 = BudgetSpec(max_iter=5, n_restarts=1, resolution_trials=3, uq_samples=10)
        >>>
        >>> # Grow budget by factor of 3
        >>> b1 = b0.scale(3.0)
        >>> b1.max_iter
        15

    Notes:
        - Budgets must be monotone-increasing across rounds
        - Algorithms may ignore parameters they don't support
        - Use scale() to create budget sequences deterministically
    """

    max_iter: Optional[int] = None
    n_restarts: Optional[int] = None
    resolution_trials: Optional[int] = None
    time_limit_s: Optional[float] = None
    uq_samples: Optional[int] = None
    n_jobs: Optional[int] = None

    def scale(self, factor: float, caps: Optional[Dict[str, int]] = None) -> BudgetSpec:
        """Scale budget by a multiplicative factor.

        Creates a new BudgetSpec with all integer parameters multiplied by
        factor (rounded up). Useful for creating budget sequences across rounds.

        Args:
            factor: Multiplicative scaling factor (e.g., 3.0 for 3x growth)
            caps: Optional dict of parameter caps {"max_iter": 1000, ...}

        Returns:
            New BudgetSpec with scaled parameters

        Examples:
            >>> b0 = BudgetSpec(max_iter=5, n_restarts=1)
            >>> b1 = b0.scale(3.0)
            >>> (b1.max_iter, b1.n_restarts)
            (15, 3)
            >>>
            >>> # With caps
            >>> b2 = b0.scale(100.0, caps={"max_iter": 50})
            >>> b2.max_iter
            50
        """
        import math

        if caps is None:
            caps = {}

        def scale_param(val: Optional[int], name: str) -> Optional[int]:
            if val is None:
                return None
            scaled = int(math.ceil(val * factor))
            cap = caps.get(name)
            if cap is not None:
                scaled = min(scaled, cap)
            return scaled

        return BudgetSpec(
            max_iter=scale_param(self.max_iter, "max_iter"),
            n_restarts=scale_param(self.n_restarts, "n_restarts"),
            resolution_trials=scale_param(self.resolution_trials, "resolution_trials"),
            time_limit_s=self.time_limit_s * factor if self.time_limit_s else None,
            uq_samples=scale_param(self.uq_samples, "uq_samples"),
            n_jobs=self.n_jobs,  # Don't scale n_jobs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with non-None parameters
        """
        return {
            k: v
            for k, v in {
                "max_iter": self.max_iter,
                "n_restarts": self.n_restarts,
                "resolution_trials": self.resolution_trials,
                "time_limit_s": self.time_limit_s,
                "uq_samples": self.uq_samples,
                "n_jobs": self.n_jobs,
            }.items()
            if v is not None
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BudgetSpec:
        """Create BudgetSpec from dictionary.

        Args:
            d: Dictionary with budget parameters

        Returns:
            BudgetSpec instance
        """
        return cls(**d)

    def __repr__(self) -> str:
        parts = []
        if self.max_iter is not None:
            parts.append(f"max_iter={self.max_iter}")
        if self.n_restarts is not None:
            parts.append(f"n_restarts={self.n_restarts}")
        if self.resolution_trials is not None:
            parts.append(f"resolution_trials={self.resolution_trials}")
        if self.uq_samples is not None:
            parts.append(f"uq_samples={self.uq_samples}")

        return f"BudgetSpec({', '.join(parts)})"


@dataclass
class CommunityResult:
    """Result from running a single community detection algorithm.

    Unified output format for the community detection runner contract.
    Used internally by racing strategies to evaluate and compare algorithms.

    Attributes:
        algo_id: Algorithm identifier (e.g., "louvain:default")
        partition: Community assignments {(node, layer): community_id}
        runtime_ms: Runtime in milliseconds
        budget_used: Budget actually used for this run
        warnings: List of warning messages
        meta: Additional metadata dict
        seed_used: Random seed used for this run
    """

    algo_id: str
    partition: Dict[Any, int]
    runtime_ms: float
    budget_used: BudgetSpec
    warnings: list = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    seed_used: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "algo_id": self.algo_id,
            "n_communities": len(set(self.partition.values())),
            "n_nodes": len(self.partition),
            "runtime_ms": self.runtime_ms,
            "budget_used": self.budget_used.to_dict(),
            "warnings": self.warnings,
            "meta": self.meta,
            "seed_used": self.seed_used,
        }
