"""Multilayer network comparison module.

This module provides functionality for comparing multilayer networks using
various distance and similarity metrics.

Example Usage:
    >>> from py3plex.comparison import compare_networks, multiplex_jaccard
    >>> 
    >>> result = compare_networks(network_a, network_b, metric="multiplex_jaccard")
    >>> print(result.global_distance)
"""

from .metrics import (
    multiplex_jaccard,
    multilayer_resistance_distance,
    layer_edge_overlap,
    degree_correlation,
    degree_change,
    MetricRegistry,
    metric_registry,
)
from .result import ComparisonResult
from .executor import compare_networks, execute_compare_stmt

__all__ = [
    "compare_networks",
    "execute_compare_stmt",
    "multiplex_jaccard",
    "multilayer_resistance_distance",
    "layer_edge_overlap",
    "degree_correlation",
    "degree_change",
    "ComparisonResult",
    "MetricRegistry",
    "metric_registry",
]
