"""Type system for DSL static analysis.

This module defines the type system used for type checking DSL expressions.
"""

from enum import Enum
from typing import Dict, Any, Optional


class AttrType(Enum):
    """Attribute type for static analysis."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LAYER_REF = "layer_ref"
    NODE_REF = "node_ref"
    EDGE_REF = "edge_ref"
    UNKNOWN = "unknown"
    
    def is_comparable(self, other: 'AttrType') -> bool:
        """Check if this type can be compared with another type."""
        # Same types are always comparable
        if self == other:
            return True
        
        # Unknown is compatible with everything (for now)
        if self == AttrType.UNKNOWN or other == AttrType.UNKNOWN:
            return True
        
        return False
    
    def supports_operator(self, op: str) -> bool:
        """Check if this type supports a given operator."""
        if op in ("=", "!="):
            # Equality works for all types
            return True
        
        if op in (">", "<", ">=", "<="):
            # Ordering only works for numeric and datetime
            return self in (AttrType.NUMERIC, AttrType.DATETIME, AttrType.UNKNOWN)
        
        if op in ("+", "-", "*", "/"):
            # Arithmetic only works for numeric
            return self in (AttrType.NUMERIC, AttrType.UNKNOWN)
        
        return False


class TypeEnvironment:
    """Type environment for DSL queries.
    
    Tracks types of attributes, computed values, and other entities
    in a query context.
    """
    
    def __init__(self):
        """Initialize empty type environment."""
        self.attribute_types: Dict[str, AttrType] = {}
        self.computed_types: Dict[str, AttrType] = {}
        self.layer_refs: set = set()
    
    def set_attribute_type(self, name: str, attr_type: AttrType):
        """Set the type of an attribute."""
        self.attribute_types[name] = attr_type
    
    def get_attribute_type(self, name: str) -> AttrType:
        """Get the type of an attribute."""
        return self.attribute_types.get(name, AttrType.UNKNOWN)
    
    def set_computed_type(self, name: str, attr_type: AttrType):
        """Set the type of a computed value."""
        self.computed_types[name] = attr_type
    
    def get_computed_type(self, name: str) -> AttrType:
        """Get the type of a computed value."""
        return self.computed_types.get(name, AttrType.UNKNOWN)
    
    def add_layer(self, layer: str):
        """Add a layer reference."""
        self.layer_refs.add(layer)
    
    def has_layer(self, layer: str) -> bool:
        """Check if a layer is known."""
        return layer in self.layer_refs
