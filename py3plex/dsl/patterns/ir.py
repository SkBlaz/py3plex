"""Intermediate Representation (IR) for Pattern Matching.

This module defines the core data structures that represent pattern queries.
The IR is designed to be stable, easy to compile, and easy to execute.

Pattern IR types:
    - PatternNode: Represents a node variable with predicates and layer constraints
    - PatternEdge: Represents an edge between two node variables
    - PatternGraph: Represents a complete pattern with nodes, edges, and constraints
    - MatchRow: Represents a single match result (variable bindings)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


@dataclass
class Predicate:
    """A predicate for filtering nodes or edges.
    
    Attributes:
        attr: Attribute name (e.g., "degree", "weight")
        op: Comparison operator (">", ">=", "<", "<=", "=", "!=")
        value: Value to compare against
    """
    attr: str
    op: str
    value: Any
    
    def __repr__(self) -> str:
        return f"Predicate({self.attr} {self.op} {self.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "attr": self.attr,
            "op": self.op,
            "value": self.value,
        }


@dataclass
class LayerConstraint:
    """Layer constraint for a node.
    
    Attributes:
        kind: Type of constraint ("one", "set", "wildcard", "predicate")
        value: Layer name, set of layer names, or predicate function
    """
    kind: str  # "one", "set", "wildcard", "predicate"
    value: Optional[Union[str, Set[str], Callable]] = None
    
    @staticmethod
    def one(layer: str) -> "LayerConstraint":
        """Create constraint for a specific layer."""
        return LayerConstraint(kind="one", value=layer)
    
    @staticmethod
    def set_of(layers: Set[str]) -> "LayerConstraint":
        """Create constraint for a set of layers."""
        return LayerConstraint(kind="set", value=layers)
    
    @staticmethod
    def wildcard() -> "LayerConstraint":
        """Create wildcard constraint (any layer)."""
        return LayerConstraint(kind="wildcard", value=None)
    
    def matches(self, layer: str) -> bool:
        """Check if a layer satisfies this constraint."""
        if self.kind == "wildcard":
            return True
        elif self.kind == "one":
            return layer == self.value
        elif self.kind == "set":
            return layer in self.value
        elif self.kind == "predicate":
            return self.value(layer) if callable(self.value) else False
        return False
    
    def __repr__(self) -> str:
        if self.kind == "wildcard":
            return "LayerConstraint(*)"
        elif self.kind == "one":
            return f"LayerConstraint({self.value})"
        elif self.kind == "set":
            return f"LayerConstraint({{{', '.join(sorted(self.value))}}})"
        return f"LayerConstraint({self.kind})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        if self.kind == "wildcard":
            return {"kind": "wildcard"}
        elif self.kind == "one":
            return {"kind": "one", "value": self.value}
        elif self.kind == "set":
            return {"kind": "set", "value": sorted(list(self.value))}
        return {"kind": self.kind}


@dataclass
class EdgeLayerConstraint:
    """Layer constraint for an edge.
    
    Attributes:
        kind: Type of constraint ("within", "between", "any")
        src_layer: Source layer constraint (for "between")
        dst_layer: Destination layer constraint (for "between")
        layer: Layer constraint (for "within")
    """
    kind: str  # "within", "between", "any"
    src_layer: Optional[str] = None
    dst_layer: Optional[str] = None
    layer: Optional[str] = None
    
    @staticmethod
    def within(layer: str) -> "EdgeLayerConstraint":
        """Create constraint for edges within a single layer."""
        return EdgeLayerConstraint(kind="within", layer=layer)
    
    @staticmethod
    def between(src_layer: str, dst_layer: str) -> "EdgeLayerConstraint":
        """Create constraint for edges between two layers."""
        return EdgeLayerConstraint(kind="between", src_layer=src_layer, dst_layer=dst_layer)
    
    @staticmethod
    def any_layer() -> "EdgeLayerConstraint":
        """Create constraint that accepts any edge."""
        return EdgeLayerConstraint(kind="any")
    
    def matches(self, src_layer: str, dst_layer: str) -> bool:
        """Check if an edge satisfies this constraint."""
        if self.kind == "any":
            return True
        elif self.kind == "within":
            return src_layer == dst_layer == self.layer
        elif self.kind == "between":
            return src_layer == self.src_layer and dst_layer == self.dst_layer
        return False
    
    def __repr__(self) -> str:
        if self.kind == "any":
            return "EdgeLayerConstraint(any)"
        elif self.kind == "within":
            return f"EdgeLayerConstraint(within={self.layer})"
        elif self.kind == "between":
            return f"EdgeLayerConstraint(between={self.src_layer}→{self.dst_layer})"
        return f"EdgeLayerConstraint({self.kind})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"kind": self.kind}
        if self.kind == "within":
            result["layer"] = self.layer
        elif self.kind == "between":
            result["src_layer"] = self.src_layer
            result["dst_layer"] = self.dst_layer
        return result


@dataclass
class PatternNode:
    """Represents a node variable in a pattern.
    
    Attributes:
        var: Variable name (e.g., "a", "b")
        labels: Optional semantic labels (metadata only in v1)
        predicates: List of predicates for filtering
        layer_constraint: Optional layer constraint
    """
    var: str
    labels: Optional[Set[str]] = None
    predicates: List[Predicate] = field(default_factory=list)
    layer_constraint: Optional[LayerConstraint] = None
    
    def __repr__(self) -> str:
        parts = [f"var={self.var}"]
        if self.labels:
            parts.append(f"labels={{{', '.join(sorted(self.labels))}}}")
        if self.predicates:
            parts.append(f"predicates={len(self.predicates)}")
        if self.layer_constraint:
            parts.append(f"layer={self.layer_constraint}")
        return f"PatternNode({', '.join(parts)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {"var": self.var}
        if self.labels:
            result["labels"] = sorted(list(self.labels))
        if self.predicates:
            result["predicates"] = [p.to_dict() for p in self.predicates]
        if self.layer_constraint:
            result["layer_constraint"] = self.layer_constraint.to_dict()
        return result


@dataclass
class PatternEdge:
    """Represents an edge between two node variables in a pattern.
    
    Attributes:
        src: Source variable name
        dst: Destination variable name
        directed: Whether the edge is directed
        etype: Optional edge type/relation
        predicates: List of predicates for filtering
        layer_constraint: Optional layer constraint
    """
    src: str
    dst: str
    directed: bool = False
    etype: Optional[str] = None
    predicates: List[Predicate] = field(default_factory=list)
    layer_constraint: Optional[EdgeLayerConstraint] = None
    
    def __repr__(self) -> str:
        arrow = "→" if self.directed else "↔"
        parts = [f"{self.src}{arrow}{self.dst}"]
        if self.etype:
            parts.append(f"type={self.etype}")
        if self.predicates:
            parts.append(f"predicates={len(self.predicates)}")
        if self.layer_constraint:
            parts.append(f"layer={self.layer_constraint}")
        return f"PatternEdge({', '.join(parts)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "src": self.src,
            "dst": self.dst,
            "directed": self.directed,
        }
        if self.etype:
            result["etype"] = self.etype
        if self.predicates:
            result["predicates"] = [p.to_dict() for p in self.predicates]
        if self.layer_constraint:
            result["layer_constraint"] = self.layer_constraint.to_dict()
        return result


@dataclass
class PatternGraph:
    """Represents a complete pattern query.
    
    Attributes:
        nodes: Dictionary mapping variable names to PatternNode objects
        edges: List of PatternEdge objects
        constraints: List of global constraints (e.g., all-different)
        return_vars: List of variables to return (defaults to all)
    """
    nodes: Dict[str, PatternNode] = field(default_factory=dict)
    edges: List[PatternEdge] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    return_vars: Optional[List[str]] = None
    
    def add_node(self, node: PatternNode) -> None:
        """Add a node to the pattern."""
        if node.var in self.nodes:
            # Merge predicates if node already exists
            existing = self.nodes[node.var]
            existing.predicates.extend(node.predicates)
            if node.labels:
                if existing.labels is None:
                    existing.labels = set()
                existing.labels.update(node.labels)
            if node.layer_constraint and not existing.layer_constraint:
                existing.layer_constraint = node.layer_constraint
        else:
            self.nodes[node.var] = node
    
    def add_edge(self, edge: PatternEdge) -> None:
        """Add an edge to the pattern."""
        self.edges.append(edge)
        # Auto-create nodes if they don't exist
        if edge.src not in self.nodes:
            self.nodes[edge.src] = PatternNode(var=edge.src)
        if edge.dst not in self.nodes:
            self.nodes[edge.dst] = PatternNode(var=edge.dst)
    
    def add_constraint(self, constraint: str) -> None:
        """Add a global constraint."""
        self.constraints.append(constraint)
    
    def get_return_vars(self) -> List[str]:
        """Get the list of variables to return."""
        if self.return_vars is not None:
            return self.return_vars
        # Default: return all variables
        return sorted(self.nodes.keys())
    
    def __repr__(self) -> str:
        parts = [
            f"nodes={len(self.nodes)}",
            f"edges={len(self.edges)}",
        ]
        if self.constraints:
            parts.append(f"constraints={len(self.constraints)}")
        if self.return_vars:
            parts.append(f"return={self.return_vars}")
        return f"PatternGraph({', '.join(parts)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "nodes": {var: node.to_dict() for var, node in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }
        if self.constraints:
            result["constraints"] = self.constraints
        if self.return_vars:
            result["return_vars"] = self.return_vars
        return result


@dataclass
class MatchRow:
    """Represents a single match result.
    
    Attributes:
        bindings: Dictionary mapping variable names to node IDs
        edge_bindings: Optional dictionary mapping edge vars to edge tuples
    """
    bindings: Dict[str, Any] = field(default_factory=dict)
    edge_bindings: Optional[Dict[str, Tuple[Any, Any]]] = None
    
    def __getitem__(self, var: str) -> Any:
        """Get the binding for a variable."""
        return self.bindings[var]
    
    def __setitem__(self, var: str, value: Any) -> None:
        """Set the binding for a variable."""
        self.bindings[var] = value
    
    def __contains__(self, var: str) -> bool:
        """Check if a variable is bound."""
        return var in self.bindings
    
    def __repr__(self) -> str:
        items = [f"{k}={v}" for k, v in sorted(self.bindings.items())]
        return f"MatchRow({', '.join(items)})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = dict(self.bindings)
        if self.edge_bindings:
            result["_edges"] = self.edge_bindings
        return result
