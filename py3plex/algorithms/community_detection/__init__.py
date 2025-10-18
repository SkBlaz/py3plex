"""
Community detection algorithms for multilayer networks.

This module provides algorithms for detecting communities in multilayer networks,
including multilayer modularity optimization, benchmark generation, and various
community detection methods.
"""

# Multilayer community detection
from .multilayer_benchmark import (
    generate_coupled_er_multilayer,
    generate_multilayer_lfr,
    generate_sbm_multilayer,
)
from .multilayer_modularity import (
    build_supra_modularity_matrix,
    louvain_multilayer,
    multilayer_modularity,
)

__all__ = [
    "multilayer_modularity",
    "build_supra_modularity_matrix",
    "louvain_multilayer",
    "generate_multilayer_lfr",
    "generate_coupled_er_multilayer",
    "generate_sbm_multilayer",
]
