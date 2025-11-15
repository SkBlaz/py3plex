"""
Curvature algorithms for multilayer networks.

This module provides support for various curvature measures on multilayer networks,
including Ollivier-Ricci curvature and Ricci flow.
"""

from .ollivier_ricci_multilayer import (
    RicciBackendNotAvailable,
    compute_ollivier_ricci_single_graph,
    compute_ollivier_ricci_flow_single_graph,
)

__all__ = [
    "RicciBackendNotAvailable",
    "compute_ollivier_ricci_single_graph",
    "compute_ollivier_ricci_flow_single_graph",
]
