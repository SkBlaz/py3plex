"""
Pymnet backend for py3plex.

This backend uses the pymnet library as the underlying representation for
multilayer networks. Pymnet provides specialized data structures optimized
for multilayer network analysis.

Note:
    This backend requires the pymnet library to be installed:
    pip install pymnet

References:
    - pymnet: https://github.com/mnets/pymnet
    - Kivelä et al. (2014): Multilayer networks
"""

from typing import Any, Iterator, List, Optional, Tuple

# Try to import pymnet
try:
    import pymnet
    PYMNET_AVAILABLE = True
except ImportError:
    PYMNET_AVAILABLE = False
    pymnet = None

import networkx as nx

from py3plex.backends.base import BaseBackend


class PymnetBackend(BaseBackend):
    """Pymnet-based backend for multilayer networks.

    This backend leverages pymnet's native multilayer network representation,
    which can provide better performance and more natural semantics for
    certain multilayer-specific operations.

    The pymnet library models multilayer networks with explicit layer and
    aspect dimensions, making it particularly suitable for multiplex networks
    and networks with regular layer structure.

    Attributes:
        name: "pymnet"
        version: The installed pymnet version.

    Note:
        Pymnet must be installed to use this backend:
        pip install pymnet

    Examples:
        >>> from py3plex.backends import get_backend, is_backend_available
        >>> if is_backend_available('pymnet'):  # doctest: +SKIP
        ...     backend = get_backend('pymnet')
        ...     g = backend.create_graph(directed=False)
        ...     backend.add_node(g, ('A', 'layer1'))
        ...     backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
    """

    def __init__(self):
        """Initialize the pymnet backend.

        Raises:
            ImportError: If pymnet is not installed.
        """
        if not PYMNET_AVAILABLE:
            raise ImportError(
                "pymnet is required for this backend. "
                "Install it with: pip install pymnet"
            )

    @property
    def name(self) -> str:
        """Return backend name."""
        return "pymnet"

    @property
    def version(self) -> str:
        """Return pymnet version."""
        if PYMNET_AVAILABLE:
            try:
                return pymnet.__version__
            except AttributeError:
                return "unknown"
        return "not installed"

    def create_graph(self, directed: bool = True) -> Any:
        """Create a new empty pymnet MultiplexNetwork.

        Args:
            directed: Whether the graph should be directed.

        Returns:
            A new pymnet MultiplexNetwork or MultilayerNetwork.

        Note:
            Pymnet uses MultiplexNetwork for most multilayer use cases.
            The directed parameter affects edge symmetry behavior.
        """
        # pymnet uses fullyInterconnected=True by default for multiplex networks
        # We create a MultiplexNetwork with one aspect (layers)
        return pymnet.MultiplexNetwork(
            couplings="none",  # No automatic coupling edges
            directed=directed,
            fullyInterconnected=False  # Don't auto-create inter-layer edges
        )

    def add_node(
        self,
        graph: Any,
        node: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add a node to the graph.

        Args:
            graph: Pymnet MultiplexNetwork.
            node: Node as (node_id, layer_id) tuple.
            **attrs: Additional node attributes (stored separately).
        """
        node_id, layer_id = node
        # In pymnet, adding an edge implicitly adds nodes
        # We use a special method to ensure the node exists
        graph.add_node(node_id, layer=layer_id)

    def add_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any],
        **attrs: Any
    ) -> None:
        """Add an edge to the graph.

        Args:
            graph: Pymnet MultiplexNetwork.
            source: Source node as (node_id, layer_id) tuple.
            target: Target node as (node_id, layer_id) tuple.
            **attrs: Additional edge attributes (e.g., weight).
        """
        src_node, src_layer = source
        tgt_node, tgt_layer = target

        # Get weight if specified
        weight = attrs.get('weight', 1.0)

        # Add edge based on whether it's intra-layer or inter-layer
        if src_layer == tgt_layer:
            # Intra-layer edge
            graph[src_node, tgt_node, src_layer] = weight
        else:
            # Inter-layer edge (coupling)
            # In pymnet, this requires the network to support inter-layer edges
            graph[src_node, src_layer][tgt_node, tgt_layer] = weight

    def remove_node(self, graph: Any, node: Tuple[Any, Any]) -> None:
        """Remove a node from the graph.

        Args:
            graph: Pymnet MultiplexNetwork.
            node: Node as (node_id, layer_id) tuple.

        Note:
            Pymnet's MultiplexNetwork doesn't support direct node removal.
            This method attempts to remove the node by clearing its edges,
            but the node may still appear in the network structure.
            For complete removal, consider recreating the network without
            the unwanted nodes.
        """
        node_id, layer_id = node
        # Pymnet doesn't have a direct remove_node for node-layer pairs
        # We attempt to clear edges connected to this node in the layer
        try:
            # Try to access the layer's adjacency structure
            if hasattr(graph, 'A') and layer_id in graph.get_layers():
                layer_graph = graph.A[layer_id]
                if hasattr(layer_graph, '__delitem__') and node_id in layer_graph:
                    del layer_graph[node_id]
        except (KeyError, IndexError, AttributeError, TypeError):
            # Node doesn't exist or pymnet structure doesn't support this operation
            pass

    def remove_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> None:
        """Remove an edge from the graph.

        Args:
            graph: Pymnet MultiplexNetwork.
            source: Source node.
            target: Target node.
        """
        src_node, src_layer = source
        tgt_node, tgt_layer = target

        if src_layer == tgt_layer:
            try:
                del graph[src_node, tgt_node, src_layer]
            except (KeyError, IndexError):
                pass
        else:
            try:
                del graph[src_node, src_layer][tgt_node, tgt_layer]
            except (KeyError, IndexError):
                pass

    def has_node(self, graph: Any, node: Tuple[Any, Any]) -> bool:
        """Check if a node exists.

        Args:
            graph: Pymnet MultiplexNetwork.
            node: Node as (node_id, layer_id) tuple.

        Returns:
            True if node exists.
        """
        node_id, layer_id = node
        try:
            return (layer_id in graph.get_layers() and
                    node_id in graph.A[layer_id])
        except (KeyError, IndexError, AttributeError):
            return False

    def has_edge(
        self,
        graph: Any,
        source: Tuple[Any, Any],
        target: Tuple[Any, Any]
    ) -> bool:
        """Check if an edge exists.

        Args:
            graph: Pymnet MultiplexNetwork.
            source: Source node.
            target: Target node.

        Returns:
            True if edge exists.
        """
        src_node, src_layer = source
        tgt_node, tgt_layer = target

        try:
            if src_layer == tgt_layer:
                return graph[src_node, tgt_node, src_layer] != 0
            else:
                return graph[src_node, src_layer][tgt_node, tgt_layer] != 0
        except (KeyError, IndexError):
            return False

    def nodes(self, graph: Any, data: bool = False) -> Iterator:
        """Iterate over nodes.

        Args:
            graph: Pymnet MultiplexNetwork.
            data: If True, yield (node, attr_dict) tuples.

        Yields:
            Nodes as (node_id, layer_id) tuples.
        """
        try:
            for layer in graph.get_layers():
                for node in graph.A[layer]:
                    node_tuple = (node, layer)
                    if data:
                        # Pymnet doesn't store node attributes in the same way
                        yield (node_tuple, {})
                    else:
                        yield node_tuple
        except (AttributeError, KeyError):
            return

    def edges(self, graph: Any, data: bool = False) -> Iterator:
        """Iterate over edges.

        Args:
            graph: Pymnet MultiplexNetwork.
            data: If True, yield (source, target, attr_dict) tuples.

        Yields:
            Edges as tuples.
        """
        seen = set()
        try:
            for layer in graph.get_layers():
                for node1 in graph.A[layer]:
                    for node2 in graph.A[layer][node1]:
                        weight = graph[node1, node2, layer]
                        if weight != 0:
                            source = (node1, layer)
                            target = (node2, layer)
                            edge_key = (source, target)
                            if edge_key not in seen:
                                seen.add(edge_key)
                                if data:
                                    yield (source, target, {'weight': weight})
                                else:
                                    yield (source, target)
        except (AttributeError, KeyError):
            return

    def number_of_nodes(self, graph: Any) -> int:
        """Return number of nodes.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            Number of node-layer pairs.
        """
        count = 0
        try:
            for layer in graph.get_layers():
                count += len(list(graph.A[layer]))
        except (AttributeError, KeyError):
            pass
        return count

    def number_of_edges(self, graph: Any) -> int:
        """Return number of edges.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            Number of edges.
        """
        return sum(1 for _ in self.edges(graph))

    def get_layers(self, graph: Any) -> List[Any]:
        """Get unique layer identifiers.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            Sorted list of layer identifiers.
        """
        try:
            return sorted(graph.get_layers())
        except (AttributeError, TypeError):
            return []

    def subgraph(
        self,
        graph: Any,
        nodes: Optional[List[Tuple[Any, Any]]] = None,
        layers: Optional[List[Any]] = None
    ) -> Any:
        """Extract a subgraph.

        Args:
            graph: Pymnet MultiplexNetwork.
            nodes: List of nodes to include.
            layers: List of layers to include.

        Returns:
            A new pymnet MultiplexNetwork containing the subgraph.
        """
        # Create new graph with same properties
        new_graph = self.create_graph(directed=graph.directed)

        # Determine which nodes to include
        if nodes is not None:
            node_set = set(nodes)
        elif layers is not None:
            layer_set = set(layers)
            node_set = set()
            for n in self.nodes(graph):
                if n[1] in layer_set:
                    node_set.add(n)
        else:
            node_set = set(self.nodes(graph))

        # Add nodes
        for node in node_set:
            self.add_node(new_graph, node)

        # Add edges between included nodes
        for source, target, data in self.edges(graph, data=True):
            if source in node_set and target in node_set:
                self.add_edge(new_graph, source, target, **data)

        return new_graph

    def copy(self, graph: Any) -> Any:
        """Create a copy of the graph.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            A copy of the graph.
        """
        # Create new graph with same properties
        new_graph = self.create_graph(directed=graph.directed)

        # Copy all nodes and edges
        for node in self.nodes(graph):
            self.add_node(new_graph, node)

        for source, target, data in self.edges(graph, data=True):
            self.add_edge(new_graph, source, target, **data)

        return new_graph

    def to_networkx(self, graph: Any) -> nx.Graph:
        """Convert to NetworkX graph.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            A NetworkX MultiGraph or MultiDiGraph.
        """
        if graph.directed:
            nx_graph = nx.MultiDiGraph()
        else:
            nx_graph = nx.MultiGraph()

        # Add nodes
        for node in self.nodes(graph):
            nx_graph.add_node(node)

        # Add edges
        for source, target, data in self.edges(graph, data=True):
            nx_graph.add_edge(source, target, **data)

        return nx_graph

    def from_networkx(self, nx_graph: nx.Graph, directed: bool = None) -> Any:
        """Create from NetworkX graph.

        Args:
            nx_graph: NetworkX graph.
            directed: Whether result should be directed.

        Returns:
            A new pymnet MultiplexNetwork.
        """
        if directed is None:
            directed = nx_graph.is_directed()

        new_graph = self.create_graph(directed=directed)

        # Add nodes
        for node in nx_graph.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                self.add_node(new_graph, node)

        # Add edges
        for source, target, data in nx_graph.edges(data=True):
            if (isinstance(source, tuple) and len(source) >= 2 and
                isinstance(target, tuple) and len(target) >= 2):
                self.add_edge(new_graph, source, target, **data)

        return new_graph

    def is_directed(self, graph: Any) -> bool:
        """Check if graph is directed.

        Args:
            graph: Pymnet MultiplexNetwork.

        Returns:
            True if directed.
        """
        try:
            return graph.directed
        except AttributeError:
            return True
