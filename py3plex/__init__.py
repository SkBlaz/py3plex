"""
Py3plex - A Python library for multilayer network analysis and visualization.

This package provides tools for constructing, analyzing, and visualizing
heterogeneous and multilayer networks.

Main Classes:
    multi_layer_network: Core class for creating and analyzing multilayer networks

Key Features:
    - Dict-based API for adding nodes and edges
    - NetworkX interoperability
    - Multiple I/O formats (edgelist, GML, GraphML, etc.)
    - Visualization for multilayer layouts
    - Community detection and centrality analysis
    - Random walk and embedding generation

Quick Start:
    >>> import py3plex as p3
    >>> net = p3.multi_layer_network(network_type='multilayer')
    >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
    >>> net.add_edges([{'source': 'A', 'target': 'B', 
    ...                 'source_type': 'layer1', 'target_type': 'layer1'}])
    >>> print(net)

For detailed documentation, see: https://py3plex.readthedocs.io
"""

# Version information
__version__ = "0.95a"
__api_version__ = "0.95a"

from py3plex.core.multinet import multi_layer_network
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

__all__ = [
    # Version info
    "__version__",
    "__api_version__",
    # Core classes
    "multi_layer_network",
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
]
