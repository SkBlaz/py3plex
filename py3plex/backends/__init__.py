"""
Backend system for py3plex (Experimental).

This module provides low-level utilities for working with different multilayer
network libraries. It is primarily designed for **interoperability and conversion**
between py3plex and other multilayer network libraries like pymnet.

.. warning::
    This is an experimental feature. The backend system provides basic graph
    operations but does NOT have full feature parity with py3plex's
    ``multi_layer_network`` class. For full py3plex functionality, continue
    using the standard ``multi_layer_network`` API.

Currently supported backends:

- **networkx** (default): Uses NetworkX MultiGraph/MultiDiGraph for network storage.
  This provides a thin wrapper around NetworkX for basic operations.

- **pymnet** (optional): Uses the pymnet library for native multilayer network
  representation. Useful for converting py3plex networks to pymnet format for
  use with pymnet's specialized analysis functions.

Primary Use Cases:
    1. **Convert py3plex networks to pymnet** for specialized analysis
    2. **Import pymnet networks into py3plex** for visualization
    3. **Low-level graph operations** when working directly with graph structures

Usage:
    >>> from py3plex.backends import get_backend, list_backends
    >>>
    >>> # List available backends
    >>> list_backends()
    ['networkx']
    >>>
    >>> # Get a backend for low-level operations
    >>> backend = get_backend()
    >>> print(backend.name)
    'networkx'

    >>> # Convert a py3plex network to pymnet (if installed)
    >>> from py3plex.backends import to_pymnet, from_pymnet  # doctest: +SKIP
    >>> pymnet_net = to_pymnet(my_py3plex_network)  # doctest: +SKIP
    >>> # ... use pymnet functions ...
    >>> py3plex_net = from_pymnet(pymnet_net)  # doctest: +SKIP

Note:
    For standard multilayer network analysis, use ``py3plex.multi_layer_network``
    directly. This backend system is for advanced users who need interoperability
    with other libraries.
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


def to_pymnet(network):
    """Convert a py3plex multi_layer_network to a pymnet MultiplexNetwork.

    This function provides interoperability between py3plex and pymnet,
    allowing you to use pymnet's specialized analysis functions on
    py3plex networks.

    Args:
        network: A py3plex multi_layer_network instance.

    Returns:
        A pymnet MultiplexNetwork with the same nodes and edges.

    Raises:
        BackendNotAvailableError: If pymnet is not installed.

    Examples:
        >>> from py3plex import multi_layer_network
        >>> from py3plex.backends import to_pymnet  # doctest: +SKIP
        >>>
        >>> net = multi_layer_network()
        >>> net.add_edges([
        ...     {'source': 'A', 'target': 'B',
        ...      'source_type': 'layer1', 'target_type': 'layer1'}
        ... ])  # doctest: +SKIP
        >>> pymnet_net = to_pymnet(net)  # doctest: +SKIP
    """
    if not is_backend_available("pymnet"):
        raise BackendNotAvailableError("pymnet", list_backends())

    pymnet_backend = get_backend("pymnet")

    # Get the NetworkX graph from py3plex
    if hasattr(network, 'core_network') and network.core_network is not None:
        nx_graph = network.core_network
    elif hasattr(network, 'to_networkx'):
        nx_graph = network.to_networkx()
    else:
        raise TypeError("Expected a py3plex multi_layer_network instance")

    # Convert to pymnet format
    directed = nx_graph.is_directed() if hasattr(nx_graph, 'is_directed') else True
    return pymnet_backend.from_networkx(nx_graph, directed=directed)


def from_pymnet(pymnet_network, network_type="multilayer", directed=None):
    """Convert a pymnet MultiplexNetwork to a py3plex multi_layer_network.

    This function allows you to import pymnet networks into py3plex
    for visualization or further analysis with py3plex functions.

    Args:
        pymnet_network: A pymnet MultiplexNetwork instance.
        network_type: Type of py3plex network ('multilayer' or 'multiplex').
        directed: Whether the network is directed. If None, inferred from pymnet.

    Returns:
        A py3plex multi_layer_network instance.

    Raises:
        BackendNotAvailableError: If pymnet is not installed.

    Examples:
        >>> from py3plex.backends import from_pymnet  # doctest: +SKIP
        >>> import pymnet  # doctest: +SKIP
        >>>
        >>> # Create a pymnet network
        >>> pn = pymnet.MultiplexNetwork(couplings='none')  # doctest: +SKIP
        >>> pn['A', 'B', 'layer1'] = 1  # doctest: +SKIP
        >>>
        >>> # Convert to py3plex
        >>> net = from_pymnet(pn)  # doctest: +SKIP
        >>> net.basic_stats()  # doctest: +SKIP
    """
    if not is_backend_available("pymnet"):
        raise BackendNotAvailableError("pymnet", list_backends())

    # Import here to avoid circular imports
    from py3plex.core.multinet import multi_layer_network

    pymnet_backend = get_backend("pymnet")

    # Convert pymnet to NetworkX
    nx_graph = pymnet_backend.to_networkx(pymnet_network)

    # Determine directedness
    if directed is None:
        directed = pymnet_backend.is_directed(pymnet_network)

    # Create py3plex network
    net = multi_layer_network(network_type=network_type, directed=directed, verbose=False)
    net.core_network = nx_graph

    return net


__all__ = [
    "BaseBackend",
    "BackendNotAvailableError",
    "BackendRegistry",
    "NetworkXBackend",
    "get_backend",
    "set_default_backend",
    "list_backends",
    "is_backend_available",
    "to_pymnet",
    "from_pymnet",
]
