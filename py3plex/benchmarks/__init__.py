"""Benchmarking infrastructure for py3plex.

This module provides benchmarking utilities for evaluating and comparing
algorithms, particularly for community detection.
"""

from .budget import Budget, BudgetExhaustedException
from .metrics import (
    CommunityMetric,
    metric_registry,
    register_metric,
    get_metric,
    compute_metric,
)
from .runners import (
    CommunityAlgorithmRunner,
    CommunityRunResult,
    get_runner,
    create_runner_from_spec,
)

__all__ = [
    "Budget",
    "BudgetExhaustedException",
    "CommunityMetric",
    "metric_registry",
    "register_metric",
    "get_metric",
    "compute_metric",
    "CommunityAlgorithmRunner",
    "CommunityRunResult",
    "get_runner",
    "create_runner_from_spec",
]
