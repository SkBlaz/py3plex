"""
Core data structures and utilities for multilayer networks.

This module provides the fundamental building blocks for working with
multilayer networks, including the multi_layer_network class and related
parsers and converters.

Classes:
    multi_layer_network: Main class for creating and manipulating multilayer networks

Submodules:
    multinet: Core network data structure implementation
    parsers: I/O parsers for various network formats
    converters: Format conversion utilities
    nx_compat: NetworkX compatibility layer
    types: Type aliases for network components

Examples:
    >>> from py3plex.core import multi_layer_network
    >>> net = multi_layer_network(network_type='multilayer')
    >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
"""

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
# Import datasets module for convenience
from py3plex import datasets

__all__ = [
    "multi_layer_network",
    "datasets",
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
]
