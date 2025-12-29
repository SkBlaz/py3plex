"""
Routing algorithms for multiplex networks.

This module provides routing algorithms that preserve layer semantics
and support explicit layer-switching costs.
"""

from .multiplex_paths import multiplex_shortest_path

__all__ = ["multiplex_shortest_path"]
