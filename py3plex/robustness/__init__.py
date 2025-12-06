"""Robustness and uncertainty analysis module for py3plex.

This module provides tools for analyzing network robustness through
perturbations and metric distribution estimation.

Example usage::

    from py3plex.robustness import (
        EdgeDrop,
        NodeDrop,
        compose,
        estimate_metric_distribution,
        centrality_robustness,
    )

    perturb = compose(EdgeDrop(p=0.1), NodeDrop(p=0.05))

    result = estimate_metric_distribution(
        network=ml_net,
        metric_fn=lambda net: net.get_number_of_edges(),
        perturbation=perturb,
        n_samples=100,
        random_state=42,
    )
"""

from .perturbations import Perturbation, EdgeDrop, EdgeAdd, NodeDrop, compose
from .experiments import estimate_metric_distribution, centrality_robustness

__all__ = [
    "Perturbation",
    "EdgeDrop",
    "EdgeAdd",
    "NodeDrop",
    "compose",
    "estimate_metric_distribution",
    "centrality_robustness",
]
