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
    Save a multi_layer_network to Arrow format.
    
    This is a convenience function that handles conversion to MultiLayerGraph
    and delegates to the Arrow writer.
    
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
        # Assume it's a multi_layer_network, convert it
        from .multinet_bridge import multinet_to_multilayergraph
        graph = multinet_to_multilayergraph(network)
    
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
