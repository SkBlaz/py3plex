"""Operator registry for pluggable DSL operators.

This module provides a registry system for user-defined DSL operators,
allowing external functions to be registered and invoked via the DSL.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class DSLOperator:
    """Metadata for a DSL operator.
    
    Attributes:
        name: Operator name (normalized to lowercase)
        func: The callable implementing the operator
        description: Optional description of what the operator does
        category: Optional category (e.g., "centrality", "dynamics", "io")
    """
    name: str
    func: Callable[..., Any]
    description: Optional[str] = None
    category: Optional[str] = None


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
        func: The callable implementing the operator
        description: Optional description
        category: Optional category for organization
        overwrite: If True, allow overwriting existing operator
        
    Raises:
        ValueError: If operator already registered and overwrite=False
    """
    normalized_name = name.strip().lower()
    
    if normalized_name in _OPERATOR_REGISTRY and not overwrite:
        raise ValueError(
            f"Operator '{normalized_name}' is already registered. "
            f"Use overwrite=True to replace it."
        )
    
    operator = DSLOperator(
        name=normalized_name,
        func=func,
        description=description,
        category=category,
    )
    
    _OPERATOR_REGISTRY[normalized_name] = operator


def get_operator(name: str) -> Optional[DSLOperator]:
    """Get a DSL operator by name.
    
    Args:
        name: Operator name (case-insensitive)
        
    Returns:
        DSLOperator if found, None otherwise
    """
    normalized_name = name.strip().lower()
    return _OPERATOR_REGISTRY.get(normalized_name)


def has_operator(name: str) -> bool:
    """Check if an operator is registered.
    
    Args:
        name: Operator name (case-insensitive)
        
    Returns:
        True if operator exists
    """
    normalized_name = name.strip().lower()
    return normalized_name in _OPERATOR_REGISTRY


def list_operators() -> Dict[str, DSLOperator]:
    """List all registered operators.
    
    Returns:
        Dictionary mapping operator names to DSLOperator instances
    """
    return _OPERATOR_REGISTRY.copy()


def describe_operator(name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about an operator.
    
    Args:
        name: Operator name (case-insensitive)
        
    Returns:
        Dictionary with operator details or None if not found
    """
    operator = get_operator(name)
    if operator is None:
        return None
    
    return {
        "name": operator.name,
        "function": operator.func,
        "description": operator.description,
        "category": operator.category,
        "signature": str(operator.func.__annotations__) if hasattr(operator.func, '__annotations__') else None,
    }


def unregister_operator(name: str) -> bool:
    """Unregister a DSL operator.
    
    Useful for cleanup in tests.
    
    Args:
        name: Operator name (case-insensitive)
        
    Returns:
        True if operator was removed, False if not found
    """
    normalized_name = name.strip().lower()
    if normalized_name in _OPERATOR_REGISTRY:
        del _OPERATOR_REGISTRY[normalized_name]
        return True
    return False
