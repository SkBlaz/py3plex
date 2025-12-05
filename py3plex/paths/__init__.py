"""Path queries and flow analysis for multilayer networks.

This module provides functionality for finding paths and analyzing flow
in multilayer networks.

Example Usage:
    >>> from py3plex.paths import find_paths, shortest_path
    >>> 
    >>> result = find_paths(network, source="Alice", target="Bob", path_type="shortest")
    >>> print(result.paths)
"""

from .algorithms import (
    shortest_path,
    all_paths,
    random_walk,
    multilayer_flow,
    PathRegistry,
    path_registry,
)
from .result import PathResult
from .executor import find_paths, execute_path_stmt

__all__ = [
    "find_paths",
    "execute_path_stmt",
    "shortest_path",
    "all_paths",
    "random_walk",
    "multilayer_flow",
    "PathResult",
    "PathRegistry",
    "path_registry",
]
