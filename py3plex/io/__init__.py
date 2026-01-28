"""
I/O module for py3plex multilayer networks.

This module provides a comprehensive I/O system for multilayer graphs with:
- Schema validation and dataclass representations
- Multiple file format support (JSON, CSV, GraphML, GEXF, HDF5, Arrow, Parquet)
- Library converters (NetworkX, igraph, graph-tool)
- Streaming support for large graphs
- Deterministic serialization
- Bridge to multi_layer_network class
"""

from pathlib import Path
from typing import Union

from .api import read, register_reader, register_writer, supported_formats, write
from .converters import from_igraph, from_networkx, to_igraph, to_networkx
from .exceptions import (
    FormatUnsupportedError,
    ReferentialIntegrityError,
    SchemaValidationError,
)
from .schema import Edge, Layer, MultiLayerGraph, Node

__all__ = [
    # Schema classes
    "MultiLayerGraph",
    "Node",
    "Layer",
    "Edge",
    # API functions
    "read",
    "write",
    "register_reader",
    "register_writer",
    "supported_formats",
    # Convenience functions for multi_layer_network
    "save_to_arrow",
    "load_from_arrow",
    "save_network_to_parquet",
    "load_network_from_parquet",
    # Converters
    "to_networkx",
    "from_networkx",
    "to_igraph",
    "from_igraph",
    # Exceptions
    "SchemaValidationError",
    "ReferentialIntegrityError",
    "FormatUnsupportedError",
]


def save_to_arrow(network, path: Union[str, Path], **kwargs) -> None:
    """
    Save a multi_layer_network to Arrow format with zero-loss preservation.
    
    This function saves the network with rich metadata including:
    - Schema version and library version
    - Network type (multilayer/multiplex) and directedness
    - Attribute type manifest for proper reconstruction
    - JSON-encoded column tracking for complex attributes
    
    Args:
        network: multi_layer_network instance or MultiLayerGraph instance
        path: Output file path (will use .arrow extension)
        **kwargs: Additional arguments passed to Arrow writer
        
    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.io import save_to_arrow
        >>> net = multinet.multi_layer_network()
        >>> # ... build network ...
        >>> save_to_arrow(net, "network.arrow")
    """
    # Check if it's already a MultiLayerGraph
    if isinstance(network, MultiLayerGraph):
        graph = network
    else:
        # Assume it's a multi_layer_network, convert with metadata
        from .multinet_bridge import multinet_to_multilayergraph_with_metadata
        graph, metadata = multinet_to_multilayergraph_with_metadata(network)
        
        # Store metadata in graph attributes for now
        # Later we'll enhance Arrow format to store this properly
        if not hasattr(graph, 'attributes') or graph.attributes is None:
            graph.attributes = {}
        graph.attributes['__p3x_metadata'] = metadata
    
    # Write using the Arrow writer
    write(graph, path, format='arrow', **kwargs)


def load_from_arrow(path: Union[str, Path], as_multinet: bool = True, **kwargs):
    """
    Load a network from Arrow format.
    
    Args:
        path: Input file path
        as_multinet: If True (default), return multi_layer_network instance.
                     If False, return MultiLayerGraph instance.
        **kwargs: Additional arguments passed to Arrow reader
        
    Returns:
        multi_layer_network or MultiLayerGraph instance depending on as_multinet
        
    Example:
        >>> from py3plex.io import load_from_arrow
        >>> net = load_from_arrow("network.arrow")
        >>> # Returns multi_layer_network by default
        >>> 
        >>> graph = load_from_arrow("network.arrow", as_multinet=False)
        >>> # Returns MultiLayerGraph
    """
    # Read using Arrow reader
    graph = read(path, format='arrow', **kwargs)
    
    if as_multinet:
        # Convert to multi_layer_network
        from .multinet_bridge import multilayergraph_to_multinet
        return multilayergraph_to_multinet(graph)
    else:
        return graph


def save_network_to_parquet(network, path: Union[str, Path], **kwargs) -> None:
    """
    Save a multi_layer_network to Parquet directory format.
    
    Creates a directory with:
    - nodes.parquet: Node table with (node, layer) and attributes
    - edges.parquet: Edge table with (source, target, source_layer, target_layer) and attributes
    - metadata.json: Network metadata (network_type, directed, coupling, schema version)
    
    This format ensures zero-loss roundtrip with atomic writes.
    
    Args:
        network: multi_layer_network instance
        path: Output directory path
        **kwargs: Additional arguments (currently unused)
        
    Raises:
        Py3plexIOError: If pyarrow not available or write fails
        
    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.io import save_network_to_parquet
        >>> net = multinet.multi_layer_network()
        >>> # ... build network ...
        >>> save_network_to_parquet(net, "network_dir")
    """
    try:
        from .parquet_format import save_network_to_parquet as _save
        _save(network, path)
    except ImportError:
        from py3plex.exceptions import Py3plexIOError
        raise Py3plexIOError(
            "PyArrow is required for Parquet support. "
            "Install it with: pip install pyarrow"
        )


def load_network_from_parquet(path: Union[str, Path], **kwargs):
    """
    Load a multi_layer_network from Parquet directory format.
    
    Reads:
    - nodes.parquet: Node table
    - edges.parquet: Edge table
    - metadata.json: Network metadata
    
    Args:
        path: Input directory path
        **kwargs: Additional arguments (currently unused)
        
    Returns:
        multi_layer_network instance
        
    Raises:
        Py3plexIOError: If directory not found, files missing, or read fails
        
    Example:
        >>> from py3plex.io import load_network_from_parquet
        >>> net = load_network_from_parquet("network_dir")
    """
    try:
        from .parquet_format import load_network_from_parquet as _load
        return _load(path)
    except ImportError:
        from py3plex.exceptions import Py3plexIOError
        raise Py3plexIOError(
            "PyArrow is required for Parquet support. "
            "Install it with: pip install pyarrow"
        )

