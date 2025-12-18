"""Operator registry for DSL v2.

This module provides a registry for user-defined DSL operators that can be
registered via decorators and used in DSL queries. This extends the existing
measure registry to support arbitrary operators.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class DSLOperator:
    """Metadata for a registered DSL operator.

    Attributes:
        name: Operator name (normalized)
        func: Python callable implementing the operator
        description: Optional human-readable description
        category: Optional category (e.g., "centrality", "dynamics", "io")
    """
    name: str
    func: Callable[..., Any]
    description: Optional[str] = None
    category: Optional[str] = None


class OperatorRegistry:
    """Registry for DSL operators.

    Provides registration, lookup, and introspection for user-defined
    DSL operators. Operators receive a DSLExecutionContext as their first
    argument, followed by any keyword arguments from the DSL.
    """

    def __init__(self):
        self._operators: Dict[str, DSLOperator] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: Optional[str] = None,
        category: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """Register a DSL operator.

        Args:
            name: Operator name (will be normalized)
            func: Python callable implementing the operator
            description: Optional description
            category: Optional category for organization
            overwrite: If True, allow replacing existing operators

        Raises:
            ValueError: If operator already exists and overwrite=False
        """
        # Normalize name: lowercase, strip whitespace
        normalized_name = name.lower().strip()

        if normalized_name in self._operators and not overwrite:
            raise ValueError(
                f"Operator '{normalized_name}' is already registered. "
                f"Use overwrite=True to replace it."
            )

        self._operators[normalized_name] = DSLOperator(
            name=normalized_name,
            func=func,
            description=description,
            category=category,
        )

    def get(self, name: str) -> Optional[DSLOperator]:
        """Get a registered operator by name.

        Args:
            name: Operator name (will be normalized)

        Returns:
            DSLOperator instance or None if not found
        """
        normalized_name = name.lower().strip()
        return self._operators.get(normalized_name)

    def has(self, name: str) -> bool:
        """Check if an operator is registered.

        Args:
            name: Operator name (will be normalized)

        Returns:
            True if operator exists
        """
        normalized_name = name.lower().strip()
        return normalized_name in self._operators

    def list_operators(self) -> Dict[str, DSLOperator]:
        """List all registered operators.

        Returns:
            Dictionary mapping operator names to DSLOperator instances
        """
        return dict(self._operators)

    def unregister(self, name: str) -> None:
        """Unregister an operator.

        Primarily useful for testing and cleanup.

        Args:
            name: Operator name (will be normalized)
        """
        normalized_name = name.lower().strip()
        self._operators.pop(normalized_name, None)


# Global operator registry instance
operator_registry = OperatorRegistry()


def register_operator(
    name: str,
    func: Optional[Callable[..., Any]] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    overwrite: bool = False,
) -> Callable[..., Any]:
    """Register a DSL operator with the global registry.

    This is a convenience function that delegates to operator_registry.register().

    Args:
        name: Operator name (will be normalized)
        func: Python callable implementing the operator
        description: Optional description
        category: Optional category for organization
        overwrite: If True, allow replacing existing operators
    """
    if func is None:
        # Decorator usage: @register_operator("name")
        def _decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            operator_registry.register(name, f, description, category, overwrite)
            return f

        return _decorator

    # Direct usage: register_operator("name", func)
    operator_registry.register(name, func, description, category, overwrite)
    return func


def get_operator(name: str) -> Optional[DSLOperator]:
    """Get a registered operator by name from the global registry.

    This is a convenience function that delegates to operator_registry.get().

    Args:
        name: Operator name (will be normalized)

    Returns:
        DSLOperator instance or None if not found
    """
    return operator_registry.get(name)


def list_operators() -> Dict[str, DSLOperator]:
    """List all registered operators from the global registry.

    This is a convenience function that delegates to operator_registry.list_operators().

    Returns:
        Dictionary mapping operator names to DSLOperator instances
    """
    return operator_registry.list_operators()


def unregister_operator(name: str) -> None:
    """Unregister an operator from the global registry.

    This is a convenience function that delegates to operator_registry.unregister().
    Primarily useful for testing and cleanup.

    Args:
        name: Operator name (will be normalized)
    """
    operator_registry.unregister(name)
