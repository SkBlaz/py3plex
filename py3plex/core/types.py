"""
Type aliases for py3plex core data structures.

This module defines common type aliases used throughout the library for
better type safety and documentation.
"""

from typing import Any, Dict, Hashable, List, Tuple, Union

# Basic node and layer identifiers
Node = Hashable  # Any hashable object can be a node identifier
LayerId = Hashable  # Any hashable object can be a layer identifier
Weight = float  # Edge weight

# Edge representations
# EdgeTuple format: (node1, layer1, node2, layer2, weight)
EdgeTuple = Tuple[Node, LayerId, Node, LayerId, Weight]

# EdgeDict format: dictionary with source, target, type information
EdgeDict = Dict[str, Any]

# NodeDict format: dictionary with source and type information
NodeDict = Dict[str, Any]

# Network data structures
LayerGraph = Any  # NetworkX graph object (avoiding circular import)
NetworkData = Dict[str, Any]  # Generic network data dictionary

# Position/coordinate types
Position = Tuple[float, float]  # 2D position (x, y)
LayoutDict = Dict[Node, Position]  # Node to position mapping

# Color types
Color = Union[str, Tuple[float, float, float], Tuple[float, float, float, float]]
ColorList = List[Color]

__all__ = [
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
