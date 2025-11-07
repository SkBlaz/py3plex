"""
Schema definitions for multilayer graphs using dataclasses.

This module provides dataclass representations of multilayer graph components
with built-in validation and serialization support.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Hashable, List, Set, Tuple

from .exceptions import ReferentialIntegrityError, SchemaValidationError


def _is_json_serializable(obj: Any) -> bool:
    """
    Check if an object is JSON-serializable.

    Args:
        obj: Object to check

    Returns:
        True if the object can be serialized to JSON
    """
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


@dataclass
class Node:
    """
    Represents a node in a multilayer network.

    Attributes:
        id: Unique identifier for the node
        attributes: Dictionary of node attributes (must be JSON-serializable)
    """

    id: Hashable
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate node after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate the node.

        Raises:
            SchemaValidationError: If validation fails
        """
        # Validate that all attributes are JSON-serializable
        for key, value in self.attributes.items():
            if not _is_json_serializable(value):
                raise SchemaValidationError(
                    f"Node attribute '{key}' with value {value} is not JSON-serializable"
                )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary.

        Returns:
            Dictionary representation of the node
        """
        return {"id": self.id, "attributes": self.attributes.copy()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """
        Create node from dictionary.

        Args:
            data: Dictionary containing node data

        Returns:
            Node instance
        """
        return cls(id=data["id"], attributes=data.get("attributes", {}))


@dataclass
class Layer:
    """
    Represents a layer in a multilayer network.

    Attributes:
        id: Unique identifier for the layer
        attributes: Dictionary of layer attributes (must be JSON-serializable)
    """

    id: Hashable
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate layer after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate the layer.

        Raises:
            SchemaValidationError: If validation fails
        """
        # Validate that all attributes are JSON-serializable
        for key, value in self.attributes.items():
            if not _is_json_serializable(value):
                raise SchemaValidationError(
                    f"Layer attribute '{key}' with value {value} is not JSON-serializable"
                )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert layer to dictionary.

        Returns:
            Dictionary representation of the layer
        """
        return {"id": self.id, "attributes": self.attributes.copy()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layer":
        """
        Create layer from dictionary.

        Args:
            data: Dictionary containing layer data

        Returns:
            Layer instance
        """
        return cls(id=data["id"], attributes=data.get("attributes", {}))


@dataclass
class Edge:
    """
    Represents an edge in a multilayer network.

    Attributes:
        src: Source node ID
        dst: Destination node ID
        src_layer: Source layer ID
        dst_layer: Destination layer ID
        key: Optional edge key for multigraphs (default: 0)
        attributes: Dictionary of edge attributes (must be JSON-serializable)
    """

    src: Hashable
    dst: Hashable
    src_layer: Hashable
    dst_layer: Hashable
    key: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate edge after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate the edge.

        Raises:
            SchemaValidationError: If validation fails
        """
        # Validate that all attributes are JSON-serializable
        for attr_key, value in self.attributes.items():
            if not _is_json_serializable(value):
                raise SchemaValidationError(
                    f"Edge attribute '{attr_key}' with value {value} is not JSON-serializable"
                )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert edge to dictionary.

        Returns:
            Dictionary representation of the edge
        """
        return {
            "src": self.src,
            "dst": self.dst,
            "src_layer": self.src_layer,
            "dst_layer": self.dst_layer,
            "key": self.key,
            "attributes": self.attributes.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """
        Create edge from dictionary.

        Args:
            data: Dictionary containing edge data

        Returns:
            Edge instance
        """
        return cls(
            src=data["src"],
            dst=data["dst"],
            src_layer=data["src_layer"],
            dst_layer=data["dst_layer"],
            key=data.get("key", 0),
            attributes=data.get("attributes", {}),
        )

    def edge_tuple(self) -> Tuple[Hashable, Hashable, Hashable, Hashable, int]:
        """
        Return edge as a tuple for uniqueness checking.

        Returns:
            Tuple of (src, dst, src_layer, dst_layer, key)
        """
        return (self.src, self.dst, self.src_layer, self.dst_layer, self.key)


@dataclass
class MultiLayerGraph:
    """
    Represents a complete multilayer graph.

    Attributes:
        nodes: Dictionary mapping node IDs to Node objects
        layers: Dictionary mapping layer IDs to Layer objects
        edges: List of Edge objects
        directed: Whether the graph is directed
        attributes: Dictionary of graph-level attributes
    """

    nodes: Dict[Hashable, Node] = field(default_factory=dict)
    layers: Dict[Hashable, Layer] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    directed: bool = True
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate graph after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate the entire graph structure.

        Raises:
            SchemaValidationError: If validation fails
            ReferentialIntegrityError: If referential integrity is violated
        """
        # Validate graph attributes are JSON-serializable
        for key, value in self.attributes.items():
            if not _is_json_serializable(value):
                raise SchemaValidationError(
                    f"Graph attribute '{key}' with value {value} is not JSON-serializable"
                )

        # Check referential integrity: all edge nodes must exist in nodes
        for edge in self.edges:
            if edge.src not in self.nodes:
                raise ReferentialIntegrityError(
                    f"Edge references non-existent source node: {edge.src}"
                )
            if edge.dst not in self.nodes:
                raise ReferentialIntegrityError(
                    f"Edge references non-existent destination node: {edge.dst}"
                )

        # Check referential integrity: all edge layers must exist in layers
        for edge in self.edges:
            if edge.src_layer not in self.layers:
                raise ReferentialIntegrityError(
                    f"Edge references non-existent source layer: {edge.src_layer}"
                )
            if edge.dst_layer not in self.layers:
                raise ReferentialIntegrityError(
                    f"Edge references non-existent destination layer: {edge.dst_layer}"
                )

        # Check uniqueness of edges: (src, dst, src_layer, dst_layer, key) must be unique
        edge_tuples: Set[Tuple[Hashable, Hashable, Hashable, Hashable, int]] = set()
        for edge in self.edges:
            edge_tuple = edge.edge_tuple()
            if edge_tuple in edge_tuples:
                raise SchemaValidationError(
                    f"Duplicate edge found: {edge_tuple}. "
                    f"Edges must be unique by (src, dst, src_layer, dst_layer, key)."
                )
            edge_tuples.add(edge_tuple)

    def add_node(self, node: Node):
        """
        Add a node to the graph.

        Args:
            node: Node to add

        Raises:
            SchemaValidationError: If node ID already exists
        """
        if node.id in self.nodes:
            raise SchemaValidationError(f"Node with ID {node.id} already exists")
        self.nodes[node.id] = node

    def add_layer(self, layer: Layer):
        """
        Add a layer to the graph.

        Args:
            layer: Layer to add

        Raises:
            SchemaValidationError: If layer ID already exists
        """
        if layer.id in self.layers:
            raise SchemaValidationError(f"Layer with ID {layer.id} already exists")
        self.layers[layer.id] = layer

    def add_edge(self, edge: Edge):
        """
        Add an edge to the graph.

        Args:
            edge: Edge to add

        Raises:
            ReferentialIntegrityError: If edge references non-existent nodes or layers
            SchemaValidationError: If edge is duplicate
        """
        # Check referential integrity
        if edge.src not in self.nodes:
            raise ReferentialIntegrityError(
                f"Edge references non-existent source node: {edge.src}"
            )
        if edge.dst not in self.nodes:
            raise ReferentialIntegrityError(
                f"Edge references non-existent destination node: {edge.dst}"
            )
        if edge.src_layer not in self.layers:
            raise ReferentialIntegrityError(
                f"Edge references non-existent source layer: {edge.src_layer}"
            )
        if edge.dst_layer not in self.layers:
            raise ReferentialIntegrityError(
                f"Edge references non-existent destination layer: {edge.dst_layer}"
            )

        # Check uniqueness
        edge_tuple = edge.edge_tuple()
        for existing_edge in self.edges:
            if existing_edge.edge_tuple() == edge_tuple:
                raise SchemaValidationError(
                    f"Duplicate edge: {edge_tuple}. "
                    f"Edges must be unique by (src, dst, src_layer, dst_layer, key)."
                )

        self.edges.append(edge)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert graph to dictionary.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "layers": [layer.to_dict() for layer in self.layers.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "directed": self.directed,
            "attributes": self.attributes.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiLayerGraph":
        """
        Create graph from dictionary.

        Args:
            data: Dictionary containing graph data

        Returns:
            MultiLayerGraph instance
        """
        # Parse nodes
        nodes = {}
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            nodes[node.id] = node

        # Parse layers
        layers = {}
        for layer_data in data.get("layers", []):
            layer = Layer.from_dict(layer_data)
            layers[layer.id] = layer

        # Parse edges
        edges = [Edge.from_dict(edge_data) for edge_data in data.get("edges", [])]

        # Create graph
        return cls(
            nodes=nodes,
            layers=layers,
            edges=edges,
            directed=data.get("directed", True),
            attributes=data.get("attributes", {}),
        )
