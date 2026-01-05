"""Backend dispatch for semiring operations.

Provides abstraction layer for different execution backends:
- Graph backend (default): operates on edge lists
- Matrix backend (placeholder): future support for matrix operations
"""

from typing import Any, Dict, List, Literal, Tuple
from py3plex.exceptions import Py3plexException

from .semiring import Semiring
from .lift import WeightLiftSpec
from .paths import sssp, PathResult
from .closure import closure


BackendType = Literal["graph", "matrix"]


class GraphBackend:
    """Default graph-based backend for semiring operations."""
    
    name: str = "graph"
    
    @staticmethod
    def sssp(
        nodes: List[Any],
        edges: List[Tuple[Any, Any, Dict[str, Any]]],
        source: Any,
        semiring: Semiring,
        lift_spec: WeightLiftSpec,
        **kwargs,
    ) -> PathResult:
        """Single-source shortest path."""
        return sssp(nodes, edges, source, semiring, lift_spec, **kwargs)
    
    @staticmethod
    def closure(
        nodes: List[Any],
        edges: List[Tuple[Any, Any, Dict[str, Any]]],
        semiring: Semiring,
        lift_spec: WeightLiftSpec,
        **kwargs,
    ) -> Dict[Tuple[Any, Any], Any]:
        """Transitive closure."""
        return closure(nodes, edges, semiring, lift_spec, **kwargs)


class MatrixBackend:
    """Placeholder for future matrix-based backend.
    
    Would use numpy/scipy for dense matrix operations.
    Requires optional dependencies.
    """
    
    name: str = "matrix"
    
    @staticmethod
    def sssp(*args, **kwargs):
        raise Py3plexException(
            "Matrix backend not yet implemented. "
            "Use backend='graph' (default)."
        )
    
    @staticmethod
    def closure(*args, **kwargs):
        raise Py3plexException(
            "Matrix backend not yet implemented. "
            "Use backend='graph' (default)."
        )


# Backend registry
_BACKENDS: Dict[str, Any] = {
    "graph": GraphBackend,
    "matrix": MatrixBackend,
}


def get_backend(name: BackendType) -> Any:
    """Get backend by name.
    
    Args:
        name: Backend identifier ("graph" or "matrix")
        
    Returns:
        Backend class
        
    Raises:
        Py3plexException: If backend not found
    """
    if name not in _BACKENDS:
        available = ", ".join(_BACKENDS.keys())
        raise Py3plexException(
            f"Unknown backend: '{name}'. Available: {available}"
        )
    return _BACKENDS[name]


def list_backends() -> List[str]:
    """List available backends.
    
    Returns:
        List of backend names
    """
    return sorted(_BACKENDS.keys())
