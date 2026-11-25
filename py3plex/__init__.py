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
from ._version import __version__

__api_version__ = __version__

from importlib import import_module as _import_module


_EXPORT_MODULES = {
    "py3plex.core.multinet": (
        "multi_layer_network",
    ),
    "py3plex.core.types": (
        "Color",
        "ColorList",
        "EdgeDict",
        "EdgeTuple",
        "LayerId",
        "LayoutDict",
        "LayerGraph",
        "NetworkData",
        "Node",
        "NodeDict",
        "Position",
        "Weight",
    ),
    "py3plex.dsl": (
        "DSLExecutionError",
        "DSLSyntaxError",
        "execute_query",
        "format_result",
        "select_nodes_by_layer",
        "select_high_degree_nodes",
        "compute_centrality_for_layer",
    ),
    "py3plex.graph_ops": (
        "nodes",
        "edges",
        "NodeFrame",
        "EdgeFrame",
        "GroupedNodeFrame",
        "GroupedEdgeFrame",
    ),
    "py3plex.exceptions": (
        "AlgorithmError",
        "CentralityComputationError",
        "CommunityDetectionError",
        "ConversionError",
        "DecompositionError",
        "EmbeddingError",
        "ExternalToolError",
        "IncompatibleNetworkError",
        "InvalidEdgeError",
        "InvalidLayerError",
        "InvalidNodeError",
        "NetworkConstructionError",
        "ParsingError",
        "Py3plexException",
        "Py3plexFormatError",
        "Py3plexIOError",
        "Py3plexLayoutError",
        "Py3plexMatrixError",
        "VisualizationError",
    ),
    "py3plex.errors": (
        "ErrorMessage",
        "Note",
        "Severity",
        "SourceContext",
        "Span",
        "Suggestion",
        "find_similar",
        "format_exception",
    ),
    "py3plex.profiling": (
        "benchmark",
        "get_monitor",
        "profile_performance",
        "timed_section",
    ),
    "py3plex.plugins": (
        "BasePlugin",
        "CentralityPlugin",
        "CommunityPlugin",
        "LayoutPlugin",
        "MetricPlugin",
        "PluginRegistry",
        "discover_plugins",
    ),
    "py3plex.pipeline": (
        "Pipeline",
        "PipelineStep",
        "LoadStep",
        "AggregateLayers",
        "LeidenMultilayer",
        "LouvainCommunity",
        "ComputeStats",
        "FilterNodes",
        "SaveNetwork",
        "NodeEmbedding",
    ),
    "py3plex.workflows": (
        "WorkflowConfig",
        "WorkflowRunner",
        "run_workflow",
    ),
    "py3plex.datasets": (
        "get_data_dir",
        "list_datasets",
        "load_aarhus_cs",
        "load_synthetic_multilayer",
        "make_clique_multiplex",
        "make_random_multilayer",
        "make_random_multiplex",
        "make_social_network",
    ),
    "py3plex.dynamics": (
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
    ),
    "py3plex.runtime.capabilities": (
        "capabilities",
        "capabilities_flat",
        "capabilities_fingerprint",
    ),
    "py3plex.uncertainty": (
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
    ),
    "py3plex.agent": (
        "load_network_from_path",
        "top_hubs_by_layer",
        "uncertainty_centrality",
        "community_detection_with_uq",
        "temporal_slice",
        "reproducible_export_bundle",
        "compare_networks",
        "summarize_result",
    ),
}
_EXPORTS = {name: module for module, names in _EXPORT_MODULES.items() for name in names}
# Public submodules previously exposed as a side effect of eager imports.
_SUBMODULES = frozenset(
    "agent algorithms config core datasets diagnostics dsl dsl_legacy dynamics "
    "embeddings errors exceptions graph_ops logging_config meta ml pipeline plugins "
    "profiling requirements robustness runtime selection uncertainty utils "
    "visualization workflows".split()
)


def __getattr__(name):
    if name in _EXPORTS:
        value = getattr(_import_module(_EXPORTS[name]), name)
    elif name in _SUBMODULES:
        value = _import_module(f"{__name__}.{name}")
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | _EXPORTS.keys() | _SUBMODULES)


def save_to_arrow(network, path, **kwargs):
    """Lazy top-level alias for :func:`py3plex.io.save_to_arrow`."""
    from py3plex.io import save_to_arrow as _save_to_arrow

    return _save_to_arrow(network, path, **kwargs)


def load_from_arrow(path, as_multinet=True, **kwargs):
    """Lazy top-level alias for :func:`py3plex.io.load_from_arrow`."""
    from py3plex.io import load_from_arrow as _load_from_arrow

    return _load_from_arrow(path, as_multinet=as_multinet, **kwargs)


def save_network_to_parquet(network, path, **kwargs):
    """Lazy top-level alias for :func:`py3plex.io.save_network_to_parquet`."""
    from py3plex.io import save_network_to_parquet as _save_network_to_parquet

    return _save_network_to_parquet(network, path, **kwargs)


def load_network_from_parquet(path, **kwargs):
    """Lazy top-level alias for :func:`py3plex.io.load_network_from_parquet`."""
    from py3plex.io import load_network_from_parquet as _load_network_from_parquet

    return _load_network_from_parquet(path, **kwargs)

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
    "NodeEmbedding",
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
    # Config module
    "config",
    # I/O convenience functions
    "save_to_arrow",
    "load_from_arrow",
    "save_network_to_parquet",
    "load_network_from_parquet",
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
    # Runtime capability discovery
    "capabilities",
    "capabilities_flat",
    "capabilities_fingerprint",
    # Agent-facing stable API
    "load_network_from_path",
    "top_hubs_by_layer",
    "uncertainty_centrality",
    "community_detection_with_uq",
    "temporal_slice",
    "reproducible_export_bundle",
    "compare_networks",
    "summarize_result",
]
