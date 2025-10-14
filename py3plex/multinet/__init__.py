"""
Multinet module for multilayer network operations.

This module provides optimized implementations for multilayer network
aggregation, supra-adjacency matrix construction, and related operations.
"""

from .aggregation import aggregate_layers

__all__ = ["aggregate_layers"]
