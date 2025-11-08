"""
Py3plex - A Python library for multilayer network analysis and visualization.

This package provides tools for constructing, analyzing, and visualizing
heterogeneous and multilayer networks.
"""

# Version information
__version__ = "0.95a"
__api_version__ = "0.95a"

from py3plex.exceptions import (
    AlgorithmError,
    CentralityComputationError,
    CommunityDetectionError,
    ConversionError,
    DecompositionError,
    EmbeddingError,
    IncompatibleNetworkError,
    InvalidEdgeError,
    InvalidLayerError,
    InvalidNodeError,
    NetworkConstructionError,
    ParsingError,
    Py3plexException,
    VisualizationError,
)

from py3plex.profiling import (
    benchmark,
    get_monitor,
    profile_performance,
    timed_section,
)

# Convenient top-level imports for common use cases
# This allows: from py3plex import multi_layer_network
from py3plex.core.multinet import multi_layer_network
from py3plex.core import random_generators

__all__ = [
    # Version info
    "__version__",
    "__api_version__",
    # Exceptions
    "Py3plexException",
    "NetworkConstructionError",
    "InvalidLayerError",
    "InvalidNodeError",
    "InvalidEdgeError",
    "ParsingError",
    "VisualizationError",
    "AlgorithmError",
    "CommunityDetectionError",
    "CentralityComputationError",
    "DecompositionError",
    "EmbeddingError",
    "ConversionError",
    "IncompatibleNetworkError",
    # Profiling utilities
    "profile_performance",
    "timed_section",
    "benchmark",
    "get_monitor",
    # Core classes and modules
    "multi_layer_network",
    "random_generators",
]
