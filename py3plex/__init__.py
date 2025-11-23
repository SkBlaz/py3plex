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
    - **Plugin system for extensibility**

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
__version__ = "0.96"
__api_version__ = "0.96"

from py3plex.core.multinet import multi_layer_network
from py3plex.core.types import (
    Color,
    ColorList,
    EdgeDict,
    EdgeTuple,
    LayerId,
    LayoutDict,
    LayerGraph,
    NetworkData,
    Node,
    NodeDict,
    Position,
    Weight,
)
from py3plex.dsl import (
    DSLExecutionError,
    DSLSyntaxError,
    execute_query,
    format_result,
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer,
)
from py3plex.exceptions import (
    AlgorithmError,
    CentralityComputationError,
    CommunityDetectionError,
    ConversionError,
    DecompositionError,
    EmbeddingError,
    ExternalToolError,
    IncompatibleNetworkError,
    InvalidEdgeError,
    InvalidLayerError,
    InvalidNodeError,
    NetworkConstructionError,
    ParsingError,
    Py3plexException,
    Py3plexFormatError,
    Py3plexIOError,
    Py3plexLayoutError,
    Py3plexMatrixError,
    VisualizationError,
)
from py3plex.profiling import (
    benchmark,
    get_monitor,
    profile_performance,
    timed_section,
)

# Plugin system - import for easy access
from py3plex.plugins import (
    BasePlugin,
    CentralityPlugin,
    CommunityPlugin,
    LayoutPlugin,
    MetricPlugin,
    PluginRegistry,
    discover_plugins,
)

__all__ = [
    # Version info
    "__version__",
    "__api_version__",
    # Core classes
    "multi_layer_network",
    # Type aliases
    "Node",
    "LayerId",
    "Weight",
    "EdgeTuple",
    "EdgeDict",
    "NodeDict",
    "LayerGraph",
    "NetworkData",
    "Position",
    "LayoutDict",
    "Color",
    "ColorList",
    # DSL functions
    "execute_query",
    "format_result",
    "select_nodes_by_layer",
    "select_high_degree_nodes",
    "compute_centrality_for_layer",
    "DSLSyntaxError",
    "DSLExecutionError",
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
    "ExternalToolError",
    "Py3plexIOError",
    "Py3plexFormatError",
    "Py3plexLayoutError",
    "Py3plexMatrixError",
    # Profiling utilities
    "profile_performance",
    "timed_section",
    "benchmark",
    "get_monitor",
    # Plugin system
    "BasePlugin",
    "CentralityPlugin",
    "CommunityPlugin",
    "LayoutPlugin",
    "MetricPlugin",
    "PluginRegistry",
    "discover_plugins",
]
