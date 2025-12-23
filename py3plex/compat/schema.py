"""
Schema validation and inference for graph conversion.

This module provides schema validation to ensure type safety and
compatibility checking before conversion.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .exceptions import SchemaError
from .ir import GraphIR


@dataclass
class GraphSchema:
    """
    Schema specification for graph data.
    
    This describes the structure and types of a graph for compatibility checking.
    
    Attributes:
        directed: Whether the graph is directed
        multi: Whether the graph supports parallel edges
        node_id_type: Type of node identifiers (e.g., "int", "str", "mixed")
        edge_id_required: Whether edge IDs must be present
        node_attr_types: Mapping of node attribute names to types
        edge_attr_types: Mapping of edge attribute names to types
        unsafe_types: List of attribute types that may not serialize cleanly
        has_layers: Whether the graph has multilayer structure
        layer_count: Number of layers (None if not multilayer)
    """
    
    directed: bool = False
    multi: bool = False
    node_id_type: str = "mixed"
    edge_id_required: bool = False
    node_attr_types: Dict[str, str] = field(default_factory=dict)
    edge_attr_types: Dict[str, str] = field(default_factory=dict)
    unsafe_types: List[str] = field(default_factory=list)
    has_layers: bool = False
    layer_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return {
            "directed": self.directed,
            "multi": self.multi,
            "node_id_type": self.node_id_type,
            "edge_id_required": self.edge_id_required,
            "node_attr_types": self.node_attr_types,
            "edge_attr_types": self.edge_attr_types,
            "unsafe_types": self.unsafe_types,
            "has_layers": self.has_layers,
            "layer_count": self.layer_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphSchema":
        """Create schema from dictionary."""
        return cls(**data)


def infer_schema(ir: GraphIR) -> GraphSchema:
    """
    Infer schema from GraphIR.
    
    Analyzes the IR to determine types and characteristics for
    compatibility checking.
    
    Args:
        ir: GraphIR to analyze
    
    Returns:
        GraphSchema describing the IR
    """
    # Infer node ID type
    node_id_types = set()
    for node_id in ir.nodes.node_id:
        node_id_types.add(_get_type_name(node_id))
    
    if len(node_id_types) == 1:
        node_id_type = node_id_types.pop()
    else:
        node_id_type = "mixed"
    
    # Infer node attribute types
    node_attr_types = {}
    if ir.nodes.attrs is not None:
        for col in ir.nodes.attrs.columns:
            dtype = ir.nodes.attrs[col].dtype
            node_attr_types[col] = _pandas_dtype_to_name(dtype)
    
    # Infer edge attribute types
    edge_attr_types = {}
    if ir.edges.attrs is not None:
        for col in ir.edges.attrs.columns:
            dtype = ir.edges.attrs[col].dtype
            edge_attr_types[col] = _pandas_dtype_to_name(dtype)
    
    # Detect unsafe types
    unsafe_types = []
    for attr_type in set(node_attr_types.values()) | set(edge_attr_types.values()):
        if attr_type in ("object", "complex", "datetime", "timedelta"):
            unsafe_types.append(attr_type)
    
    # Check for multilayer structure
    has_layers = ir.meta.layers is not None and len(ir.meta.layers) > 0
    layer_count = len(ir.meta.layers) if ir.meta.layers else None
    
    return GraphSchema(
        directed=ir.meta.directed,
        multi=ir.meta.multi,
        node_id_type=node_id_type,
        edge_id_required=ir.meta.multi,  # Required for multigraphs
        node_attr_types=node_attr_types,
        edge_attr_types=edge_attr_types,
        unsafe_types=unsafe_types,
        has_layers=has_layers,
        layer_count=layer_count,
    )


@dataclass
class ValidationReport:
    """
    Report from schema validation.
    
    Attributes:
        valid: Whether validation passed
        errors: List of validation error messages
        warnings: List of validation warning messages
    """
    
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        """ValidationReport is truthy if valid."""
        return self.valid
    
    def __str__(self) -> str:
        """String representation of validation report."""
        if self.valid:
            msg = "Validation passed"
            if self.warnings:
                msg += f" with {len(self.warnings)} warning(s)"
        else:
            msg = f"Validation failed with {len(self.errors)} error(s)"
        
        parts = [msg]
        
        if self.errors:
            parts.append("\nErrors:")
            for err in self.errors:
                parts.append(f"  - {err}")
        
        if self.warnings:
            parts.append("\nWarnings:")
            for warn in self.warnings:
                parts.append(f"  - {warn}")
        
        return "".join(parts)


def validate_against_schema(ir: GraphIR, schema: GraphSchema) -> ValidationReport:
    """
    Validate GraphIR against a schema.
    
    Checks that the IR conforms to the expected schema specification.
    
    Args:
        ir: GraphIR to validate
        schema: Expected schema
    
    Returns:
        ValidationReport with validation results
    """
    errors = []
    warnings = []
    
    # Check directed/undirected
    if ir.meta.directed != schema.directed:
        errors.append(
            f"Directedness mismatch: IR is {'directed' if ir.meta.directed else 'undirected'}, "
            f"schema expects {'directed' if schema.directed else 'undirected'}"
        )
    
    # Check multigraph
    if ir.meta.multi != schema.multi:
        errors.append(
            f"Multigraph mismatch: IR is {'multigraph' if ir.meta.multi else 'simple'}, "
            f"schema expects {'multigraph' if schema.multi else 'simple'}"
        )
    
    # Check node ID types
    actual_node_id_type = _infer_node_id_type(ir)
    if schema.node_id_type != "mixed" and actual_node_id_type != schema.node_id_type:
        warnings.append(
            f"Node ID type mismatch: actual is {actual_node_id_type}, "
            f"schema expects {schema.node_id_type}"
        )
    
    # Check edge ID requirement
    if schema.edge_id_required:
        if not ir.edges.edge_id:
            errors.append("Schema requires edge IDs, but none are present")
    
    # Check node attributes
    if ir.nodes.attrs is not None:
        for col in ir.nodes.attrs.columns:
            if col in schema.node_attr_types:
                actual_type = _pandas_dtype_to_name(ir.nodes.attrs[col].dtype)
                expected_type = schema.node_attr_types[col]
                if actual_type != expected_type:
                    warnings.append(
                        f"Node attribute '{col}' type mismatch: "
                        f"actual is {actual_type}, expected {expected_type}"
                    )
    
    # Check edge attributes
    if ir.edges.attrs is not None:
        for col in ir.edges.attrs.columns:
            if col in schema.edge_attr_types:
                actual_type = _pandas_dtype_to_name(ir.edges.attrs[col].dtype)
                expected_type = schema.edge_attr_types[col]
                if actual_type != expected_type:
                    warnings.append(
                        f"Edge attribute '{col}' type mismatch: "
                        f"actual is {actual_type}, expected {expected_type}"
                    )
    
    # Check multilayer structure
    actual_has_layers = ir.meta.layers is not None and len(ir.meta.layers) > 0
    if actual_has_layers != schema.has_layers:
        if schema.has_layers:
            errors.append("Schema expects multilayer structure, but IR has none")
        else:
            warnings.append("IR has multilayer structure, but schema doesn't expect it")
    
    if schema.layer_count is not None:
        actual_layer_count = len(ir.meta.layers) if ir.meta.layers else 0
        if actual_layer_count != schema.layer_count:
            warnings.append(
                f"Layer count mismatch: actual is {actual_layer_count}, "
                f"expected {schema.layer_count}"
            )
    
    valid = len(errors) == 0
    return ValidationReport(valid=valid, errors=errors, warnings=warnings)


def _get_type_name(obj: Any) -> str:
    """Get a simple type name for an object."""
    if isinstance(obj, bool):
        return "bool"
    elif isinstance(obj, int):
        return "int"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, str):
        return "str"
    elif isinstance(obj, tuple):
        return "tuple"
    elif isinstance(obj, list):
        return "list"
    else:
        return "object"


def _pandas_dtype_to_name(dtype) -> str:
    """Convert pandas dtype to a simple type name."""
    dtype_str = str(dtype)
    
    if "int" in dtype_str:
        return "int"
    elif "float" in dtype_str:
        return "float"
    elif "bool" in dtype_str:
        return "bool"
    elif "datetime" in dtype_str:
        return "datetime"
    elif "timedelta" in dtype_str:
        return "timedelta"
    elif "complex" in dtype_str:
        return "complex"
    elif dtype_str == "object":
        return "object"
    else:
        return "unknown"


def _infer_node_id_type(ir: GraphIR) -> str:
    """Infer the predominant node ID type."""
    node_id_types = set()
    for node_id in ir.nodes.node_id:
        node_id_types.add(_get_type_name(node_id))
    
    if len(node_id_types) == 1:
        return node_id_types.pop()
    else:
        return "mixed"
