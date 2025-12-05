"""
NetworkX backend for py3plex.

This backend uses NetworkX MultiGraph/MultiDiGraph as the underlying
representation for multilayer networks. This is the default backend and
provides broad compatibility with the existing py3plex codebase and
the NetworkX ecosystem.
"""

from typing import Any, Iterator, List, Optional, Tuple

import networkx as nx

from py3plex.backends.base import BaseBackend


class NetworkXBackend(BaseBackend):
    """NetworkX-based backend for multilayer networks.

    This backend stores multilayer networks using NetworkX's MultiGraph or
    MultiDiGraph classes. Nodes are represented as (node_id, layer_id) tuples,
    which allows the same node to exist in multiple layers.

    Attributes:
        name: "networkx"
        version: The installed NetworkX version.

    Examples:
        >>> backend = NetworkXBackend()
        >>> g = backend.create_graph(directed=False)
        >>> backend.add_node(g, ('A', 'layer1'), weight=1.0)
        >>> backend.add_node(g, ('B', 'layer1'), weight=2.0)
        >>> backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'), weight=0.5)
        >>> backend.number_of_nodes(g)
        2
        >>> backend.number_of_edges(g)
        1
    """

    @property
    def name(self) -> str:
        """Return backend name."""
        return "networkx"

    @property
    def version(self) -> str:
        """Return NetworkX version."""
        return nx.__version__

    def create_graph(self, directed: bool = True) -> nx.Graph:
        """Create a new empty NetworkX graph.

        Args:
            directed: Whether the graph should be directed.

        Returns:
            A new NetworkX MultiGraph or MultiDiGraph.
        """
        if directed:
            return nx.MultiDiGraph()
        else:
            return nx.MultiGraph()

    def add_node(
        self,
        graph: nx.Graph,
        node: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add a node to the graph.

        Args:
            graph: NetworkX graph.
            node: Node as (node_id, layer_id) tuple.
            **attrs: Additional node attributes.
        """
        graph.add_node(node, **attrs)

    def add_edge(
        self,
        graph: nx.Graph,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add an edge to the graph.

        Args:
            graph: NetworkX graph.
            source: Source node as (node_id, layer_id) tuple.
            target: Target node as (node_id, layer_id) tuple.
            **attrs: Additional edge attributes.
        """
        graph.add_edge(source, target, **attrs)

    def remove_node(self, graph: nx.Graph, node: Tuple[Any, Any]) -> None:
        """Remove a node from the graph.

        Args:
            graph: NetworkX graph.
            node: Node as (node_id, layer_id) tuple.
        """
        graph.remove_node(node)

    def remove_edge(
        self,
        graph: nx.Graph,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> None:
        """Remove an edge from the graph.

        Args:
            graph: NetworkX graph.
            source: Source node.
            target: Target node.
        """
        graph.remove_edge(source, target)

    def has_node(self, graph: nx.Graph, node: Tuple[Any, Any]) -> bool:
        """Check if a node exists.

        Args:
            graph: NetworkX graph.
            node: Node as (node_id, layer_id) tuple.

        Returns:
            True if node exists.
        """
        return graph.has_node(node)

    def has_edge(
        self,
        graph: nx.Graph,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> bool:
        """Check if an edge exists.

        Args:
            graph: NetworkX graph.
            source: Source node.
            target: Target node.

        Returns:
            True if edge exists.
        """
        return graph.has_edge(source, target)

    def nodes(self, graph: nx.Graph, data: bool = False) -> Iterator:
        """Iterate over nodes.

        Args:
            graph: NetworkX graph.
            data: If True, yield (node, attr_dict) tuples.

        Yields:
            Nodes or (node, attr_dict) tuples.
        """
        return iter(graph.nodes(data=data))

    def edges(self, graph: nx.Graph, data: bool = False) -> Iterator:
        """Iterate over edges.

        Args:
            graph: NetworkX graph.
            data: If True, yield (source, target, attr_dict) tuples.

        Yields:
            Edges or (source, target, attr_dict) tuples.
        """
        return iter(graph.edges(data=data))

    def number_of_nodes(self, graph: nx.Graph) -> int:
        """Return number of nodes.

        Args:
            graph: NetworkX graph.

        Returns:
            Number of nodes.
        """
        return graph.number_of_nodes()

    def number_of_edges(self, graph: nx.Graph) -> int:
        """Return number of edges.

        Args:
            graph: NetworkX graph.

        Returns:
            Number of edges.
        """
        return graph.number_of_edges()

    def get_layers(self, graph: nx.Graph) -> List[Any]:
        """Get unique layer identifiers.

        Args:
            graph: NetworkX graph.

        Returns:
            Sorted list of layer identifiers.
        """
        layers = set()
        for node in graph.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                layers.add(node[1])
        return sorted(layers)

    def subgraph(
        self,
        graph: nx.Graph,
        nodes: Optional[List[Tuple[Any, Any]]] = None,
        layers: Optional[List[Any]] = None
    ) -> nx.Graph:
        """Extract a subgraph.

        Args:
            graph: NetworkX graph.
            nodes: List of nodes to include.
            layers: List of layers to include.

        Returns:
            A new NetworkX graph containing the subgraph.
        """
        # Determine which nodes to include
        if nodes is not None:
            node_set = set(nodes)
        elif layers is not None:
            layer_set = set(layers)
            node_set = {
                n for n in graph.nodes()
                if isinstance(n, tuple) and len(n) >= 2 and n[1] in layer_set
            }
        else:
            node_set = set(graph.nodes())

        return graph.subgraph(node_set).copy()

    def copy(self, graph: nx.Graph) -> nx.Graph:
        """Create a copy of the graph.

        Args:
            graph: NetworkX graph.

        Returns:
            A copy of the graph.
        """
        return graph.copy()

    def to_networkx(self, graph: nx.Graph) -> nx.Graph:
        """Convert to NetworkX (identity for this backend).

        Args:
            graph: NetworkX graph.

        Returns:
            The same graph (or a copy).
        """
        return graph.copy()

    def from_networkx(self, nx_graph: nx.Graph, directed: bool = None) -> nx.Graph:
        """Create from NetworkX graph.

        Args:
            nx_graph: NetworkX graph.
            directed: Whether result should be directed.

        Returns:
            A copy of the input graph.
        """
        if directed is None:
            directed = nx_graph.is_directed()

        if directed and not nx_graph.is_directed():
            return nx_graph.to_directed()
        elif not directed and nx_graph.is_directed():
            return nx_graph.to_undirected()
        else:
            return nx_graph.copy()

    def neighbors(self, graph: nx.Graph, node: Tuple[Any, Any]) -> Iterator:
        """Get neighbors of a node.

        Args:
            graph: NetworkX graph.
            node: Node as (node_id, layer_id) tuple.

        Yields:
            Neighbor nodes.
        """
        return iter(graph.neighbors(node))

    def degree(self, graph: nx.Graph, node: Tuple[Any, Any]) -> int:
        """Get node degree.

        Args:
            graph: NetworkX graph.
            node: Node as (node_id, layer_id) tuple.

        Returns:
            Node degree.
        """
        return graph.degree(node)

    def is_directed(self, graph: nx.Graph) -> bool:
        """Check if graph is directed.

        Args:
            graph: NetworkX graph.

        Returns:
            True if directed.
        """
        return graph.is_directed()
