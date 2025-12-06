"""Operator registry for DSL v2 plugin system.

This module provides a centralized registry for user-defined and built-in
DSL operators, allowing users to extend the DSL with custom functions.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class DSLOperator:
    """Metadata for a DSL operator.
    
    Attributes:
        name: Operator name used in DSL scripts
        func: Python callable that implements the operator
        description: Optional human-readable description
        category: Optional category (e.g., "centrality", "dynamics", "io")
    """
    name: str
    func: Callable[..., Any]
    description: Optional[str] = None
    category: Optional[str] = None


class OperatorRegistry:
    """Registry for DSL operators.
    
    Allows registration of operator functions and retrieval by name.
    Supports user-defined operators via decorator or direct registration.
    """
    
    def __init__(self) -> None:
        self._operators: Dict[str, DSLOperator] = {}
    
    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: Optional[str] = None,
        category: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """Register an operator function.
        
        Args:
            name: Operator name (will be normalized to lowercase)
            func: The operator function
            description: Optional description
            category: Optional category for grouping
            overwrite: If True, allow overwriting existing operators
            
        Raises:
            ValueError: If operator already exists and overwrite=False
        """
        normalized_name = name.lower().strip()
        
        if normalized_name in self._operators and not overwrite:
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
        self._operators[normalized_name] = operator
    
    def get(self, name: str) -> Optional[DSLOperator]:
        """Get an operator by name.
        
        Args:
            name: Operator name (case-insensitive)
            
        Returns:
            DSLOperator if found, None otherwise
        """
        normalized_name = name.lower().strip()
        return self._operators.get(normalized_name)
    
    def has(self, name: str) -> bool:
        """Check if an operator is registered.
        
        Args:
            name: Operator name (case-insensitive)
            
        Returns:
            True if operator exists
        """
        normalized_name = name.lower().strip()
        return normalized_name in self._operators
    
    def list_operators(self, category: Optional[str] = None) -> Dict[str, DSLOperator]:
        """List all registered operators.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary mapping operator names to DSLOperator objects
        """
        if category is None:
            return self._operators.copy()
        
        return {
            name: op
            for name, op in self._operators.items()
            if op.category == category
        }
    
    def unregister(self, name: str) -> bool:
        """Unregister an operator (useful for tests).
        
        Args:
            name: Operator name (case-insensitive)
            
        Returns:
            True if operator was removed, False if not found
        """
        normalized_name = name.lower().strip()
        if normalized_name in self._operators:
            del self._operators[normalized_name]
            return True
        return False


# Global operator registry
operator_registry = OperatorRegistry()


def register_operator(
    name: str,
    func: Callable[..., Any],
    description: Optional[str] = None,
    category: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    """Register an operator in the global registry.
    
    This is a convenience function that wraps operator_registry.register().
    
    Args:
        name: Operator name
        func: The operator function
        description: Optional description
        category: Optional category
        overwrite: If True, allow overwriting existing operators
    """
    operator_registry.register(name, func, description, category, overwrite)


def get_operator(name: str) -> Optional[DSLOperator]:
    """Get an operator from the global registry.
    
    Args:
        name: Operator name
        
    Returns:
        DSLOperator if found, None otherwise
    """
    return operator_registry.get(name)


def list_operators(category: Optional[str] = None) -> Dict[str, DSLOperator]:
    """List all operators in the global registry.
    
    Args:
        category: Optional category filter
        
    Returns:
        Dictionary of operator names to DSLOperator objects
    """
    return operator_registry.list_operators(category)


def describe_operator(name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about an operator.
    
    Args:
        name: Operator name
        
    Returns:
        Dictionary with operator details, or None if not found
    """
    op = operator_registry.get(name)
    if op is None:
        return None
    
    return {
        "name": op.name,
        "function": op.func.__name__,
        "description": op.description or op.func.__doc__ or "No description available",
        "category": op.category or "uncategorized",
    }
