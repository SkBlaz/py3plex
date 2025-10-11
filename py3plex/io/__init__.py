"""
I/O module for py3plex multilayer networks.

This module provides a comprehensive I/O system for multilayer graphs with:
- Schema validation and dataclass representations
- Multiple file format support (JSON, CSV, GraphML, GEXF, HDF5)
- Library converters (NetworkX, igraph, graph-tool)
- Streaming support for large graphs
- Deterministic serialization
"""

from .api import read, register_reader, register_writer, supported_formats, write
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
    # Exceptions
    "SchemaValidationError",
    "ReferentialIntegrityError",
    "FormatUnsupportedError",
]
