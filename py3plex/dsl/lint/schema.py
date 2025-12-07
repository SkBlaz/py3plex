"""Schema provider for DSL linting.

Defines interfaces and implementations for querying network schema information.
"""

from typing import Protocol, Optional, List, Set, Dict, Any
from .types import AttrType


class EntityRef:
    """Reference to an entity (node/edge) in the schema."""
    
    def __init__(self, entity_type: str, layer: Optional[str] = None, attribute: Optional[str] = None):
        """Initialize entity reference.
        
        Args:
            entity_type: "node" or "edge"
            layer: Optional layer name
            attribute: Optional attribute name
        """
        self.entity_type = entity_type
        self.layer = layer
        self.attribute = attribute


class SchemaProvider(Protocol):
    """Protocol for schema providers.
    
    Schema providers allow the linter to query information about
    available layers, node/edge types, and attributes in a network.
    """
    
    def list_layers(self) -> List[str]:
        """Get list of all layers in the network."""
        ...
    
    def list_node_types(self, layer: Optional[str] = None) -> List[str]:
        """Get list of node types, optionally filtered by layer."""
        ...
    
    def list_edge_types(self, layer: Optional[str] = None) -> List[str]:
        """Get list of edge types, optionally filtered by layer."""
        ...
    
    def get_attribute_type(self, entity_ref: EntityRef, attr: str) -> Optional[AttrType]:
        """Get the type of an attribute for a given entity.
        
        Args:
            entity_ref: Reference to the entity (node/edge + layer)
            attr: Attribute name
            
        Returns:
            Attribute type or None if unknown
        """
        ...
    
    def get_node_count(self, layer: Optional[str] = None) -> int:
        """Get approximate node count, optionally for a specific layer."""
        ...
    
    def get_edge_count(self, layer: Optional[str] = None) -> int:
        """Get approximate edge count, optionally for a specific layer."""
        ...


class NetworkSchemaProvider:
    """Schema provider backed by a py3plex multilayer network."""
    
    def __init__(self, network: Any):
        """Initialize from a multilayer network.
        
        Args:
            network: py3plex multi_layer_network instance
        """
        self.network = network
        self._cached_layers: Optional[Set[str]] = None
        self._cached_node_attributes: Optional[Dict[str, Set[str]]] = None
        self._cached_edge_attributes: Optional[Dict[str, Set[str]]] = None
    
    def list_layers(self) -> List[str]:
        """Get list of all layers."""
        if self._cached_layers is None:
            self._cached_layers = set()
            
            # Extract layers from nodes
            if hasattr(self.network, 'core_network') and self.network.core_network:
                for node in self.network.core_network.nodes():
                    if isinstance(node, tuple) and len(node) >= 2:
                        self._cached_layers.add(node[1])
        
        return sorted(self._cached_layers) if self._cached_layers else []
    
    def list_node_types(self, layer: Optional[str] = None) -> List[str]:
        """Get list of node types."""
        # For now, return empty list - could be extended to analyze node attributes
        return []
    
    def list_edge_types(self, layer: Optional[str] = None) -> List[str]:
        """Get list of edge types."""
        # For now, return empty list - could be extended to analyze edge attributes
        return []
    
    def get_attribute_type(self, entity_ref: EntityRef, attr: str) -> Optional[AttrType]:
        """Get attribute type by sampling nodes/edges."""
        if not hasattr(self.network, 'core_network') or not self.network.core_network:
            return None
        
        G = self.network.core_network
        
        # Special built-in attributes
        if attr == "degree":
            return AttrType.NUMERIC
        if attr == "layer":
            return AttrType.CATEGORICAL
        
        # Sample nodes/edges to infer type
        if entity_ref.entity_type == "node":
            # Sample a few nodes to check attribute type
            for node in list(G.nodes())[:10]:
                if node in G and attr in G.nodes[node]:
                    value = G.nodes[node][attr]
                    return self._infer_type(value)
        elif entity_ref.entity_type == "edge":
            # Sample a few edges to check attribute type
            for edge in list(G.edges())[:10]:
                if G.has_edge(*edge) and attr in G.edges[edge]:
                    value = G.edges[edge][attr]
                    return self._infer_type(value)
        
        return None
    
    def _infer_type(self, value: Any) -> AttrType:
        """Infer attribute type from a value."""
        if isinstance(value, bool):
            return AttrType.BOOLEAN
        if isinstance(value, (int, float)):
            return AttrType.NUMERIC
        if isinstance(value, str):
            return AttrType.CATEGORICAL
        return AttrType.UNKNOWN
    
    def get_node_count(self, layer: Optional[str] = None) -> int:
        """Get node count."""
        if not hasattr(self.network, 'core_network') or not self.network.core_network:
            return 0
        
        if layer is None:
            return self.network.core_network.number_of_nodes()
        
        # Count nodes in specific layer
        count = 0
        for node in self.network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer:
                count += 1
        return count
    
    def get_edge_count(self, layer: Optional[str] = None) -> int:
        """Get edge count."""
        if not hasattr(self.network, 'core_network') or not self.network.core_network:
            return 0
        
        if layer is None:
            return self.network.core_network.number_of_edges()
        
        # Count edges in specific layer (intralayer edges)
        count = 0
        for edge in self.network.core_network.edges():
            if len(edge) >= 2:
                src, dst = edge[0], edge[1]
                if isinstance(src, tuple) and isinstance(dst, tuple):
                    if len(src) >= 2 and len(dst) >= 2:
                        if src[1] == layer and dst[1] == layer:
                            count += 1
        return count
