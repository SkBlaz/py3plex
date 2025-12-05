"""
Backend system for py3plex.

This module provides a pluggable backend architecture that allows py3plex to use
different multilayer network libraries as its underlying representation. Currently
supported backends:

- **networkx** (default): Uses NetworkX MultiGraph/MultiDiGraph for network storage.
  This is the current default and provides broad compatibility with existing py3plex
  code and the NetworkX ecosystem.

- **pymnet** (optional): Uses the pymnet library for native multilayer network
  representation. This backend leverages pymnet's specialized multilayer data
  structures and may provide better performance for certain multilayer-specific
  operations.

Usage:
    >>> from py3plex.backends import get_backend, set_default_backend, list_backends
    >>>
    >>> # List available backends
    >>> list_backends()
    ['networkx', 'pymnet']
    >>>
    >>> # Get the current default backend
    >>> backend = get_backend()
    >>> print(backend.name)
    'networkx'
    >>>
    >>> # Set a different default backend
    >>> set_default_backend('pymnet')  # doctest: +SKIP

    >>> # Or specify backend when creating a network
    >>> from py3plex import multi_layer_network
    >>> net = multi_layer_network(backend='pymnet')  # doctest: +SKIP

Backend API:
    All backends implement the BaseBackend abstract class, which provides a consistent
    interface for:
    - Creating graphs (directed/undirected, multi-edge support)
    - Adding/removing nodes and edges
    - Iterating over nodes and edges
    - Computing basic graph properties
    - Converting between backends
"""

from py3plex.backends.base import (
    BaseBackend,
    BackendNotAvailableError,
    BackendRegistry,
)
from py3plex.backends.networkx_backend import NetworkXBackend

# Global backend registry
_registry = BackendRegistry()

# Register NetworkX backend (always available)
_registry.register("networkx", NetworkXBackend)

# Try to register pymnet backend if the library is actually available
try:
    import pymnet  # noqa: F401
    from py3plex.backends.pymnet_backend import PymnetBackend
    _registry.register("pymnet", PymnetBackend)
except ImportError:
    pass  # pymnet not installed


def get_backend(name: str = None) -> BaseBackend:
    """Get a backend by name.

    Args:
        name: Name of the backend. If None, returns the default backend.

    Returns:
        Backend instance.

    Raises:
        BackendNotAvailableError: If the requested backend is not available.

    Examples:
        >>> backend = get_backend()  # Get default backend
        >>> print(backend.name)
        'networkx'
        >>> backend = get_backend('networkx')  # Get specific backend
    """
    return _registry.get(name)


def set_default_backend(name: str) -> None:
    """Set the default backend.

    Args:
        name: Name of the backend to set as default.

    Raises:
        BackendNotAvailableError: If the backend is not available.

    Examples:
        >>> set_default_backend('networkx')
        >>> backend = get_backend()
        >>> print(backend.name)
        'networkx'
    """
    _registry.set_default(name)


def list_backends() -> list:
    """List all registered backends.

    Returns:
        List of backend names.

    Examples:
        >>> backends = list_backends()
        >>> 'networkx' in backends
        True
    """
    return _registry.list_backends()


def is_backend_available(name: str) -> bool:
    """Check if a backend is available.

    Args:
        name: Name of the backend.

    Returns:
        True if the backend is available, False otherwise.

    Examples:
        >>> is_backend_available('networkx')
        True
    """
    return _registry.is_available(name)


__all__ = [
    "BaseBackend",
    "BackendNotAvailableError",
    "BackendRegistry",
    "NetworkXBackend",
    "get_backend",
    "set_default_backend",
    "list_backends",
    "is_backend_available",
]
