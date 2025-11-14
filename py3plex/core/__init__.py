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

Examples:
    >>> from py3plex.core import multi_layer_network
    >>> net = multi_layer_network(network_type='multilayer')
    >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
"""

from py3plex.core.multinet import multi_layer_network

__all__ = ["multi_layer_network"]
