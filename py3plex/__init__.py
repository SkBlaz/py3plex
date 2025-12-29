"""
Py3plex - A Python library for multilayer network analysis and visualization.

This package provides tools for constructing, analyzing, and visualizing
heterogeneous and multilayer networks.

Main Classes:
    multi_layer_network: Core class for creating and analyzing multilayer networks

Key Features:
    - **SQL-like DSL for intuitive network queries**
    - **Dplyr-style chainable graph operations API**
    - **Built-in datasets** (similar to scikit-learn)
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
    
    # Load built-in datasets
    >>> net = p3.load_aarhus_cs()  # Social network dataset
    >>> net = p3.make_random_multilayer(n_nodes=50, n_layers=3)  # Synthetic
    
    # Use SQL-like DSL for queries
    >>> result = p3.execute_query(net, 'SELECT nodes WHERE layer="layer1"')
    >>> result = p3.execute_query(net, 'SELECT nodes WHERE degree > 1 COMPUTE betweenness_centrality')
    
    # Use dplyr-style chainable API
    >>> import numpy as np
    >>> from py3plex.graph_ops import nodes
    >>> df = (
    ...     nodes(net, layers=["layer1"])
    ...     .filter(lambda n: n["degree"] > 1)
    ...     .mutate(normalized_degree=lambda n: n["degree"] / 10)
    ...     .group_by("layer")
    ...     .summarise(avg_degree=("degree", np.mean))
    ...     .to_pandas()
    ... )

For detailed documentation, see: https://skblaz.github.io/py3plex/
"""

# Version information
__version__ = "1.1.0"
__api_version__ = "1.1.0"

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
from py3plex.graph_ops import (
    nodes,
    edges,
    NodeFrame,
    EdgeFrame,
    GroupedNodeFrame,
    GroupedEdgeFrame,
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
from py3plex.errors import (
    ErrorMessage,
    Note,
    Severity,
    SourceContext,
    Span,
    Suggestion,
    find_similar,
    format_exception,
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

# Pipeline system for composable workflows
from py3plex.pipeline import (
    Pipeline,
    PipelineStep,
    LoadStep,
    AggregateLayers,
    LeidenMultilayer,
    LouvainCommunity,
    ComputeStats,
    FilterNodes,
    SaveNetwork,
)

# Config-driven workflows
from py3plex.workflows import WorkflowConfig, WorkflowRunner, run_workflow

# Built-in datasets (similar to scikit-learn)
from py3plex.datasets import (
    get_data_dir,
    list_datasets,
    load_aarhus_cs,
    load_synthetic_multilayer,
    make_clique_multiplex,
    make_random_multilayer,
    make_random_multiplex,
    make_social_network,
)

# Dynamics module for simulating dynamical processes
from py3plex.dynamics import (
    D,
    SimulationBuilder,
    ProcessSpec,
    SIS,
    SIR,
    RandomWalk,
    SimulationResult,
    run_simulation,
    DynamicsError,
    UnknownProcessError,
    MissingInitialConditionError,
)

# Uncertainty module for first-class uncertainty estimation
from py3plex.uncertainty import (
    StatSeries,
    StatMatrix,
    CommunityStats,
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
    get_uncertainty_config,
    set_uncertainty_config,
    uncertainty_enabled,
    estimate_uncertainty,
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
    # Graph operations (dplyr-style chainable API)
    "nodes",
    "edges",
    "NodeFrame",
    "EdgeFrame",
    "GroupedNodeFrame",
    "GroupedEdgeFrame",
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
    # Error formatting (Rust-style error messages)
    "ErrorMessage",
    "Note",
    "Severity",
    "SourceContext",
    "Span",
    "Suggestion",
    "find_similar",
    "format_exception",
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
    # Pipeline system
    "Pipeline",
    "PipelineStep",
    "LoadStep",
    "AggregateLayers",
    "LeidenMultilayer",
    "LouvainCommunity",
    "ComputeStats",
    "FilterNodes",
    "SaveNetwork",
    # Workflows
    "WorkflowConfig",
    "WorkflowRunner",
    "run_workflow",
    # Built-in datasets
    "load_aarhus_cs",
    "load_synthetic_multilayer",
    "make_random_multilayer",
    "make_random_multiplex",
    "make_clique_multiplex",
    "make_social_network",
    "list_datasets",
    "get_data_dir",
    # Dynamics (simulation)
    "D",
    "SimulationBuilder",
    "ProcessSpec",
    "SIS",
    "SIR",
    "RandomWalk",
    "SimulationResult",
    "run_simulation",
    "DynamicsError",
    "UnknownProcessError",
    "MissingInitialConditionError",
    # Uncertainty (first-class uncertainty support)
    "StatSeries",
    "StatMatrix",
    "CommunityStats",
    "ResamplingStrategy",
    "UncertaintyMode",
    "UncertaintyConfig",
    "get_uncertainty_config",
    "set_uncertainty_config",
    "uncertainty_enabled",
    "estimate_uncertainty",
]
