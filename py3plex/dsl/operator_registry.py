"""Operator registry for extensible DSL operators.

This module provides a pluggable operator system that allows users to define
custom DSL operators in Python and register them for use in DSL scripts.

Example:
    >>> from py3plex.dsl import dsl_operator
    >>> 
    >>> @dsl_operator("layer_resilience")
    >>> def layer_resilience_op(context, alpha: float = 0.1):
    ...     # Access network, layers, nodes via context
    ...     return 42.0
    >>> 
    >>> # Then use in DSL:
    >>> # COMPUTE layer_resilience(alpha=0.2)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class DSLOperator:
    """Metadata for a DSL operator.
    
    Attributes:
        name: Operator name (normalized to lowercase)
        func: Python callable implementing the operator
        description: Optional human-readable description
        category: Optional category (e.g., "centrality", "dynamics", "io")
    """
    name: str
    func: Callable[..., Any]
    description: Optional[str] = None
    category: Optional[str] = None


@dataclass
class DSLExecutionContext:
    """Execution context passed to DSL operators.
    
    Provides operators with access to the network, selected layers/nodes,
    and execution parameters.
    
    Attributes:
        graph: The multilayer network being queried
        current_layers: Currently selected layers (None = all)
        current_nodes: Currently selected nodes (None = all)
        params: Global execution parameters (e.g., random seed)
        metadata: Additional execution metadata
    """
    graph: Any
    current_layers: Optional[list[str]] = None
    current_nodes: Optional[list[Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Global operator registry
_OPERATOR_REGISTRY: Dict[str, DSLOperator] = {}


def register_operator(
    name: str,
    func: Callable[..., Any],
    description: Optional[str] = None,
    category: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    """Register a DSL operator.
    
    Args:
        name: Operator name (will be normalized to lowercase)
        func: Python callable implementing the operator
        description: Optional description
        category: Optional category for grouping
        overwrite: If True, allow overwriting existing operators
        
    Raises:
        ValueError: If operator already exists and overwrite=False
        
    Example:
        >>> def my_op(context, k=5):
        ...     return len(context.current_nodes or [])
        >>> register_operator("my_op", my_op, category="stats")
    """
    normalized_name = name.lower().strip()
    
    if not overwrite and normalized_name in _OPERATOR_REGISTRY:
        raise ValueError(
            f"Operator '{normalized_name}' is already registered. "
            f"Use overwrite=True to replace it."
        )
    
    operator = DSLOperator(
        name=normalized_name,
        func=func,
        description=description or func.__doc__,
        category=category,
    )
    
    _OPERATOR_REGISTRY[normalized_name] = operator


def get_operator(name: str) -> Optional[DSLOperator]:
    """Get a DSL operator by name.
    
    Args:
        name: Operator name (case-insensitive)
        
    Returns:
        DSLOperator if found, None otherwise
        
    Example:
        >>> op = get_operator("layer_resilience")
        >>> if op:
        ...     result = op.func(context, alpha=0.2)
    """
    normalized_name = name.lower().strip()
    return _OPERATOR_REGISTRY.get(normalized_name)


def list_operators(category: Optional[str] = None) -> Dict[str, DSLOperator]:
    """List all registered operators.
    
    Args:
        category: If provided, filter by category
        
    Returns:
        Dict mapping operator names to DSLOperator objects
        
    Example:
        >>> ops = list_operators(category="centrality")
        >>> for name, op in ops.items():
        ...     print(f"{name}: {op.description}")
    """
    if category is None:
        return _OPERATOR_REGISTRY.copy()
    
    return {
        name: op
        for name, op in _OPERATOR_REGISTRY.items()
        if op.category == category
    }


def unregister_operator(name: str) -> bool:
    """Unregister a DSL operator.
    
    Useful for cleanup in tests.
    
    Args:
        name: Operator name
        
    Returns:
        True if operator was found and removed, False otherwise
        
    Example:
        >>> unregister_operator("test_op")
    """
    normalized_name = name.lower().strip()
    if normalized_name in _OPERATOR_REGISTRY:
        del _OPERATOR_REGISTRY[normalized_name]
        return True
    return False


def describe_operator(name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about an operator.
    
    Args:
        name: Operator name
        
    Returns:
        Dict with operator details, or None if not found
        
    Example:
        >>> info = describe_operator("betweenness_centrality")
        >>> print(info["description"])
    """
    op = get_operator(name)
    if op is None:
        return None
    
    import inspect
    
    # Get function signature
    try:
        sig = inspect.signature(op.func)
        params = {
            param_name: {
                "default": (
                    param.default
                    if param.default != inspect.Parameter.empty
                    else None
                ),
                "annotation": (
                    str(param.annotation)
                    if param.annotation != inspect.Parameter.empty
                    else None
                ),
            }
            for param_name, param in sig.parameters.items()
            if param_name != "context"  # Skip context parameter
        }
    except Exception:
        params = {}
    
    return {
        "name": op.name,
        "description": op.description,
        "category": op.category,
        "parameters": params,
        "function": op.func,
    }
