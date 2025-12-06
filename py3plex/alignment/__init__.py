"""Multilayer network alignment and comparison module.

This module provides tools for aligning and comparing multilayer networks
using feature-based node alignment and various similarity metrics.

Typical workflow:

    from py3plex.alignment import (
        multilayer_node_features,
        align_networks,
        edge_agreement,
        degree_correlation,
    )

    alignment = align_networks(net_a, net_b)
    ea = edge_agreement(net_a, net_b, alignment.node_mapping)
    dc = degree_correlation(net_a, net_b, alignment.node_mapping)
"""

from .features import multilayer_node_features
from .metrics import cosine_similarity_matrix, degree_correlation, edge_agreement
from .solvers import AlignmentResult, align_networks

__all__ = [
    "multilayer_node_features",
    "align_networks",
    "AlignmentResult",
    "edge_agreement",
    "degree_correlation",
    "cosine_similarity_matrix",
]
