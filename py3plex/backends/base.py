"""
Base classes and registry for the backend system.

This module defines the abstract base class that all backends must implement,
as well as the registry system for managing available backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type


class BackendNotAvailableError(Exception):
    """Raised when a requested backend is not available."""

    def __init__(self, name: str, available: List[str]):
        self.name = name
        self.available = available
        super().__init__(
            f"Backend '{name}' is not available. "
            f"Available backends: {', '.join(available)}"
        )


class BaseBackend(ABC):
    """Abstract base class for multilayer network backends.

    All backends must implement this interface to provide a consistent API
    for network operations. The interface is designed to be minimal but
    sufficient for py3plex's core functionality.

    Attributes:
        name: Human-readable name of the backend.
        version: Version string of the underlying library.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this backend."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of the underlying library."""
        pass

    @abstractmethod
    def create_graph(self, directed: bool = True) -> Any:
        """Create a new empty graph.

        Args:
            directed: Whether the graph should be directed.

        Returns:
            A new graph object suitable for multilayer network representation.
        """
        pass

    @abstractmethod
    def add_node(
        self,
        graph: Any,
        node: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add a node to the graph.

        Args:
            graph: The graph object.
            node: Node as (node_id, layer_id) tuple.
            **attrs: Additional node attributes.
        """
        pass

    @abstractmethod
    def add_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add an edge to the graph.

        Args:
            graph: The graph object.
            source: Source node as (node_id, layer_id) tuple.
            target: Target node as (node_id, layer_id) tuple.
            **attrs: Additional edge attributes (e.g., weight, type).
        """
        pass

    @abstractmethod
    def remove_node(self, graph: Any, node: Tuple[Any, Any]) -> None:
        """Remove a node from the graph.

        Args:
            graph: The graph object.
            node: Node as (node_id, layer_id) tuple.
        """
        pass

    @abstractmethod
    def remove_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> None:
        """Remove an edge from the graph.

        Args:
            graph: The graph object.
            source: Source node as (node_id, layer_id) tuple.
            target: Target node as (node_id, layer_id) tuple.
        """
        pass

    @abstractmethod
    def has_node(self, graph: Any, node: Tuple[Any, Any]) -> bool:
        """Check if a node exists in the graph.

        Args:
            graph: The graph object.
            node: Node as (node_id, layer_id) tuple.

        Returns:
            True if node exists, False otherwise.
        """
        pass

    @abstractmethod
    def has_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> bool:
        """Check if an edge exists in the graph.

        Args:
            graph: The graph object.
            source: Source node as (node_id, layer_id) tuple.
            target: Target node as (node_id, layer_id) tuple.

        Returns:
            True if edge exists, False otherwise.
        """
        pass

    @abstractmethod
    def nodes(self, graph: Any, data: bool = False) -> Iterator:
        """Iterate over nodes in the graph.

        Args:
            graph: The graph object.
            data: If True, yield (node, attr_dict) tuples.

        Yields:
            Nodes or (node, attr_dict) tuples.
        """
        pass

    @abstractmethod
    def edges(self, graph: Any, data: bool = False) -> Iterator:
        """Iterate over edges in the graph.

        Args:
            graph: The graph object.
            data: If True, yield (source, target, attr_dict) tuples.

        Yields:
            Edges or (source, target, attr_dict) tuples.
        """
        pass

    @abstractmethod
    def number_of_nodes(self, graph: Any) -> int:
        """Return the number of nodes in the graph.

        Args:
            graph: The graph object.

        Returns:
            Number of nodes.
        """
        pass

    @abstractmethod
    def number_of_edges(self, graph: Any) -> int:
        """Return the number of edges in the graph.

        Args:
            graph: The graph object.

        Returns:
            Number of edges.
        """
        pass

    @abstractmethod
    def get_layers(self, graph: Any) -> List[Any]:
        """Get list of unique layer identifiers.

        Args:
            graph: The graph object.

        Returns:
            Sorted list of layer identifiers.
        """
        pass

    @abstractmethod
    def subgraph(
        self,
        graph: Any,
        nodes: Optional[List[Tuple[Any, Any]]] = None,
        layers: Optional[List[Any]] = None
    ) -> Any:
        """Extract a subgraph.

        Args:
            graph: The graph object.
            nodes: List of nodes to include. If None, include all nodes.
            layers: List of layers to include. If None, include all layers.

        Returns:
            A new graph object containing only the specified nodes/layers.
        """
        pass

    @abstractmethod
    def copy(self, graph: Any) -> Any:
        """Create a copy of the graph.

        Args:
            graph: The graph object.

        Returns:
            A new graph object that is a copy of the original.
        """
        pass

    @abstractmethod
    def to_networkx(self, graph: Any) -> Any:
        """Convert the graph to a NetworkX graph.

        This is useful for interoperability with NetworkX-based algorithms.

        Args:
            graph: The graph object.

        Returns:
            A NetworkX MultiGraph or MultiDiGraph.
        """
        pass

    @abstractmethod
    def from_networkx(self, nx_graph: Any, directed: bool = None) -> Any:
        """Create a graph from a NetworkX graph.

        Args:
            nx_graph: A NetworkX graph.
            directed: Whether the result should be directed. If None,
                      infer from the input graph.

        Returns:
            A new graph object in this backend's format.
        """
        pass

    def neighbors(self, graph: Any, node: Tuple[Any, Any]) -> Iterator:
        """Get neighbors of a node.

        Args:
            graph: The graph object.
            node: Node as (node_id, layer_id) tuple.

        Yields:
            Neighbor nodes.
        """
        # Default implementation - backends may override for efficiency
        # For undirected graphs, we need to check both directions
        seen = set()
        for source, target in self.edges(graph):
            if source == node and target not in seen:
                seen.add(target)
                yield target
            elif target == node and source not in seen:
                # For undirected graphs, the node could be either source or target
                seen.add(source)
                yield source

    def degree(self, graph: Any, node: Tuple[Any, Any]) -> int:
        """Get the degree of a node.

        Args:
            graph: The graph object.
            node: Node as (node_id, layer_id) tuple.

        Returns:
            Node degree.
        """
        # Default implementation - backends may override for efficiency
        return sum(1 for _ in self.neighbors(graph, node))

    def is_directed(self, graph: Any) -> bool:
        """Check if the graph is directed.

        Args:
            graph: The graph object.

        Returns:
            True if directed, False otherwise.
        """
        # Default implementation - backends should override
        return True


class BackendRegistry:
    """Registry for managing available backends.

    This class maintains a mapping of backend names to backend classes and
    handles the default backend selection.
    """

    def __init__(self):
        self._backends: Dict[str, Type[BaseBackend]] = {}
        self._instances: Dict[str, BaseBackend] = {}
        self._default: str = "networkx"

    def register(self, name: str, backend_class: Type[BaseBackend]) -> None:
        """Register a backend.

        Args:
            name: Name for the backend.
            backend_class: Backend class (must be subclass of BaseBackend).
        """
        if not issubclass(backend_class, BaseBackend):
            raise TypeError(
                f"Backend class must be a subclass of BaseBackend, "
                f"got {backend_class}"
            )
        self._backends[name] = backend_class

    def get(self, name: str = None) -> BaseBackend:
        """Get a backend instance by name.

        Args:
            name: Name of the backend. If None, returns the default.

        Returns:
            Backend instance.

        Raises:
            BackendNotAvailableError: If the backend is not registered.
        """
        if name is None:
            name = self._default

        if name not in self._backends:
            raise BackendNotAvailableError(name, list(self._backends.keys()))

        # Cache instances
        if name not in self._instances:
            self._instances[name] = self._backends[name]()

        return self._instances[name]

    def set_default(self, name: str) -> None:
        """Set the default backend.

        Args:
            name: Name of the backend to set as default.

        Raises:
            BackendNotAvailableError: If the backend is not registered.
        """
        if name not in self._backends:
            raise BackendNotAvailableError(name, list(self._backends.keys()))
        self._default = name

    def list_backends(self) -> List[str]:
        """List all registered backend names.

        Returns:
            List of backend names.
        """
        return list(self._backends.keys())

    def is_available(self, name: str) -> bool:
        """Check if a backend is available.

        Args:
            name: Name of the backend.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._backends

    @property
    def default(self) -> str:
        """Get the name of the default backend."""
        return self._default
