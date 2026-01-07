"""Type definitions for semiring algebra.

This module provides type aliases and data structures for semiring operations.
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from dataclasses import dataclass, field


# Type alias for edge lift functions
LiftFn = Callable[[Dict[str, Any]], Any]


class EdgeView(Protocol):
    """Protocol for edge-like objects in the network.
    
    An edge view provides access to edge attributes needed for semiring operations.
    """
    
    @property
    def source(self) -> Any:
        """Source node."""
        ...
    
    @property
    def target(self) -> Any:
        """Target node."""
        ...
    
    @property
    def attrs(self) -> Dict[str, Any]:
        """Edge attributes dictionary."""
        ...


@dataclass
class PathResult:
    """Result of a semiring path computation.
    
    Attributes:
        value: Semiring value (e.g., distance, boolean reachability)
        path: Optional path witness (list of nodes or edges)
        meta: Additional metadata (e.g., algorithm used, iterations)
    """
    value: Any
    path: Optional[List[Any]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
