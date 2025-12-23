"""
Cross-compatibility conversion layer for py3plex.

This module provides lossless conversion between py3plex multilayer networks
and common graph ecosystems (NetworkX, igraph, PyTorch Geometric, DGL, etc.).

Key features:
- Lossless roundtrip conversions preserving structure, semantics, and attributes
- Intermediate Representation (IR) for consistent converter implementation
- Schema validation and compatibility checking
- Sidecar bundle format for preserving data in lossy target formats
- Strict and compatibility modes for conversion

Main components:
- GraphIR: Intermediate representation for graph data
- convert(): High-level conversion entry point
- Sidecar bundles: Lossless preservation for lossy targets
"""

from .convert import convert
from .equality import ir_diff, ir_equals
from .exceptions import CompatibilityError, SchemaError
from .ir import EdgeTable, GraphIR, GraphMeta, NodeTable, from_ir, to_ir
from .schema import GraphSchema, infer_schema, validate_against_schema

__all__ = [
    # IR components
    "GraphIR",
    "NodeTable",
    "EdgeTable",
    "GraphMeta",
    "to_ir",
    "from_ir",
    # Schema
    "GraphSchema",
    "infer_schema",
    "validate_against_schema",
    # Conversion
    "convert",
    # Equality
    "ir_equals",
    "ir_diff",
    # Exceptions
    "CompatibilityError",
    "SchemaError",
]
