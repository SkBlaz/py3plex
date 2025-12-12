"""Builder API for Pattern Matching.

This module provides a fluent builder API for constructing pattern queries.
The builders produce PatternGraph IR objects that can be compiled and executed.

Example:
    >>> pq = (
    ...     Q.pattern()
    ...      .node("a").where(layer="social", degree__gt=3)
    ...      .node("b").where(layer="social")
    ...      .edge("a", "b", directed=False).where(weight__gt=0.2)
    ...      .returning("a", "b")
    ... )
    >>> matches = pq.execute(network)
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .ir import (
    PatternNode,
    PatternEdge,
    PatternGraph,
    LayerConstraint,
    EdgeLayerConstraint,
    Predicate,
)
from .compiler import compile_pattern
from .engine import match_pattern
from .result import PatternQueryResult
from ..errors import DslSyntaxError


# Comparator suffix mapping (same as in builder.py)
COMPARATOR_MAP = {
    "gt": ">",
    "ge": ">=",
    "gte": ">=",
    "lt": "<",
    "le": "<=",
    "lte": "<=",
    "eq": "=",
    "ne": "!=",
    "neq": "!=",
}


class PatternNodeBuilder:
    """Builder for configuring a pattern node variable.
    
    This builder is returned by PatternQueryBuilder.node() and provides
    chainable methods for specifying node predicates and constraints.
    
    Methods that don't return self will return the parent QueryBuilder,
    allowing for seamless chaining back to the main pattern builder.
    """
    
    def __init__(self, parent: "PatternQueryBuilder", var: str, labels: Optional[Union[str, List[str]]] = None):
        """Initialize node builder.
        
        Args:
            parent: Parent PatternQueryBuilder
            var: Variable name
            labels: Optional labels for the node
        """
        self._parent = parent
        self._var = var
        self._labels: Optional[Set[str]] = None
        if labels:
            if isinstance(labels, str):
                self._labels = {labels}
            else:
                self._labels = set(labels)
        self._predicates: List[Predicate] = []
        self._layer_constraint: Optional[LayerConstraint] = None
    
    # Delegate to parent for chaining
    def __getattr__(self, name):
        """Delegate attribute access to parent PatternQueryBuilder."""
        return getattr(self._parent, name)
    
    def where(self, **kwargs) -> "PatternQueryBuilder":
        """Add predicates to the node.
        
        Supports the same predicate syntax as Q.nodes().where():
            - layer="social" → layer constraint
            - degree__gt=5 → degree > 5
            - any_attribute__op=value
        
        Args:
            **kwargs: Predicate specifications
            
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        for key, value in kwargs.items():
            if key == "layer":
                # Special handling for layer constraint
                self._layer_constraint = LayerConstraint.one(value)
            elif "__" in key:
                # Parse comparison: attr__op=value
                parts = key.rsplit("__", 1)
                attr = parts[0]
                suffix = parts[1]
                
                if suffix in COMPARATOR_MAP:
                    op = COMPARATOR_MAP[suffix]
                    self._predicates.append(Predicate(attr=attr, op=op, value=value))
                else:
                    raise DslSyntaxError(f"Unknown comparator suffix: {suffix}")
            else:
                # Direct equality: attr=value
                self._predicates.append(Predicate(attr=key, op="=", value=value))
        
        # Add node to pattern graph
        node = PatternNode(
            var=self._var,
            labels=self._labels,
            predicates=self._predicates,
            layer_constraint=self._layer_constraint,
        )
        self._parent._pattern.add_node(node)
        
        return self._parent
    
    def in_layers(self, layers: Union[str, List[str]]) -> "PatternQueryBuilder":
        """Specify layer constraint for the node.
        
        Args:
            layers: Single layer name, list of layers, or "*" for wildcard
            
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        if layers == "*":
            self._layer_constraint = LayerConstraint.wildcard()
        elif isinstance(layers, str):
            self._layer_constraint = LayerConstraint.one(layers)
        else:
            self._layer_constraint = LayerConstraint.set_of(set(layers))
        
        # Update node in pattern graph
        node = PatternNode(
            var=self._var,
            labels=self._labels,
            predicates=self._predicates,
            layer_constraint=self._layer_constraint,
        )
        self._parent._pattern.add_node(node)
        
        return self._parent
    
    def label(self, *labels: str) -> "PatternNodeBuilder":
        """Add labels to the node.
        
        Args:
            *labels: Label names
            
        Returns:
            Self for chaining
        """
        if self._labels is None:
            self._labels = set()
        self._labels.update(labels)
        return self


class PatternEdgeBuilder:
    """Builder for configuring a pattern edge.
    
    This builder is returned by PatternQueryBuilder.edge() and provides
    chainable methods for specifying edge predicates and constraints.
    
    Methods that don't return self will return the parent QueryBuilder,
    allowing for seamless chaining back to the main pattern builder.
    """
    
    def __init__(self, parent: "PatternQueryBuilder", src: str, dst: str, 
                 directed: bool = False, etype: Optional[str] = None):
        """Initialize edge builder.
        
        Args:
            parent: Parent PatternQueryBuilder
            src: Source variable name
            dst: Destination variable name
            directed: Whether the edge is directed
            etype: Optional edge type
        """
        self._parent = parent
        self._src = src
        self._dst = dst
        self._directed = directed
        self._etype = etype
        self._predicates: List[Predicate] = []
        self._layer_constraint: Optional[EdgeLayerConstraint] = None
    
    # Delegate to parent for chaining
    def __getattr__(self, name):
        """Delegate attribute access to parent PatternQueryBuilder."""
        return getattr(self._parent, name)
    
    def where(self, **kwargs) -> "PatternQueryBuilder":
        """Add predicates to the edge.
        
        Args:
            **kwargs: Predicate specifications
            
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        for key, value in kwargs.items():
            if "__" in key:
                # Parse comparison: attr__op=value
                parts = key.rsplit("__", 1)
                attr = parts[0]
                suffix = parts[1]
                
                if suffix in COMPARATOR_MAP:
                    op = COMPARATOR_MAP[suffix]
                    self._predicates.append(Predicate(attr=attr, op=op, value=value))
                else:
                    raise DslSyntaxError(f"Unknown comparator suffix: {suffix}")
            else:
                # Direct equality: attr=value
                self._predicates.append(Predicate(attr=key, op="=", value=value))
        
        # Update the last edge in the pattern with predicates
        if self._parent._pattern.edges:
            last_edge = self._parent._pattern.edges[-1]
            if last_edge.src == self._src and last_edge.dst == self._dst:
                # Update the existing edge with predicates
                last_edge.predicates.extend(self._predicates)
                last_edge.layer_constraint = self._layer_constraint
        
        return self._parent
    
    def within_layer(self, layer: str) -> "PatternQueryBuilder":
        """Constrain edge to be within a single layer.
        
        Args:
            layer: Layer name
            
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        self._layer_constraint = EdgeLayerConstraint.within(layer)
        
        # Update the last edge in the pattern
        if self._parent._pattern.edges:
            last_edge = self._parent._pattern.edges[-1]
            if last_edge.src == self._src and last_edge.dst == self._dst:
                last_edge.layer_constraint = self._layer_constraint
        
        return self._parent
    
    def between_layers(self, src_layer: str, dst_layer: str) -> "PatternQueryBuilder":
        """Constrain edge to be between two specific layers.
        
        Args:
            src_layer: Source layer name
            dst_layer: Destination layer name
            
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        self._layer_constraint = EdgeLayerConstraint.between(src_layer, dst_layer)
        
        # Update the last edge in the pattern
        if self._parent._pattern.edges:
            last_edge = self._parent._pattern.edges[-1]
            if last_edge.src == self._src and last_edge.dst == self._dst:
                last_edge.layer_constraint = self._layer_constraint
        
        return self._parent
    
    def any_layer(self) -> "PatternQueryBuilder":
        """Allow edge to be in any layer.
        
        Returns:
            Parent PatternQueryBuilder for chaining
        """
        self._layer_constraint = EdgeLayerConstraint.any_layer()
        
        # Update the last edge in the pattern
        if self._parent._pattern.edges:
            last_edge = self._parent._pattern.edges[-1]
            if last_edge.src == self._src and last_edge.dst == self._dst:
                last_edge.layer_constraint = self._layer_constraint
        
        return self._parent


class PatternQueryBuilder:
    """Main builder for pattern queries.
    
    Provides a fluent API for constructing pattern queries. The builder
    accumulates pattern elements (nodes, edges, constraints) and produces
    a PatternGraph IR object that can be compiled and executed.
    
    Example:
        >>> pq = (
        ...     Q.pattern()
        ...      .node("a").where(degree__gt=3)
        ...      .node("b")
        ...      .edge("a", "b", directed=False)
        ...      .returning("a", "b")
        ... )
        >>> matches = pq.execute(network)
    """
    
    def __init__(self):
        """Initialize pattern query builder."""
        self._pattern = PatternGraph()
        self._limit: Optional[int] = None
        self._order_by: Optional[Tuple[str, bool]] = None  # (key, desc)
    
    def node(self, var: str, labels: Optional[Union[str, List[str]]] = None) -> PatternNodeBuilder:
        """Add a node variable to the pattern.
        
        Args:
            var: Variable name (e.g., "a", "b")
            labels: Optional semantic labels
            
        Returns:
            PatternNodeBuilder for configuring the node
        """
        # Auto-add node if no predicates specified
        node_builder = PatternNodeBuilder(self, var, labels)
        # Add empty node immediately so builder chain works
        node = PatternNode(var=var, labels=node_builder._labels)
        self._pattern.add_node(node)
        return node_builder
    
    def edge(self, src: str, dst: str, directed: bool = False, 
             etype: Optional[str] = None) -> PatternEdgeBuilder:
        """Add an edge between two node variables.
        
        Args:
            src: Source variable name
            dst: Destination variable name
            directed: Whether the edge is directed
            etype: Optional edge type
            
        Returns:
            PatternEdgeBuilder for configuring the edge
        """
        edge_builder = PatternEdgeBuilder(self, src, dst, directed, etype)
        # Add empty edge immediately so builder chain works
        edge = PatternEdge(src=src, dst=dst, directed=directed, etype=etype)
        self._pattern.add_edge(edge)
        return edge_builder
    
    def path(self, vars: Union[List[str], Tuple[str, ...]], directed: bool = False,
             etype: Optional[str] = None, length: Optional[int] = None) -> "PatternQueryBuilder":
        """Add a path pattern.
        
        Creates edges between consecutive variables in the list.
        For example, path(["a", "b", "c"]) creates edges a-b and b-c.
        
        Args:
            vars: List of variable names representing the path
            directed: Whether edges are directed
            etype: Optional edge type for all edges
            length: Optional length constraint (currently ignored, for future use)
            
        Returns:
            Self for chaining
        """
        if len(vars) < 2:
            raise DslSyntaxError("Path must have at least 2 variables")
        
        # Create edges between consecutive variables
        for i in range(len(vars) - 1):
            edge = PatternEdge(
                src=vars[i],
                dst=vars[i + 1],
                directed=directed,
                etype=etype,
            )
            self._pattern.add_edge(edge)
        
        return self
    
    def triangle(self, a: str, b: str, c: str, directed: bool = False) -> "PatternQueryBuilder":
        """Add a triangle motif.
        
        Creates edges a-b, b-c, and c-a.
        
        Args:
            a: First variable name
            b: Second variable name
            c: Third variable name
            directed: Whether edges are directed
            
        Returns:
            Self for chaining
        """
        edges = [
            PatternEdge(src=a, dst=b, directed=directed),
            PatternEdge(src=b, dst=c, directed=directed),
            PatternEdge(src=c, dst=a, directed=directed),
        ]
        for edge in edges:
            self._pattern.add_edge(edge)
        
        return self
    
    def constraint(self, expr: str) -> "PatternQueryBuilder":
        """Add a global constraint.
        
        Currently supports:
            - "a != b" for all-different constraints
            - "all_distinct([a, b, c])" for multi-variable all-different
        
        Args:
            expr: Constraint expression
            
        Returns:
            Self for chaining
        """
        self._pattern.add_constraint(expr)
        return self
    
    def returning(self, *vars: str) -> "PatternQueryBuilder":
        """Specify which variables to return in results.
        
        Args:
            *vars: Variable names to return
            
        Returns:
            Self for chaining
        """
        self._pattern.return_vars = list(vars)
        return self
    
    def limit(self, n: int) -> "PatternQueryBuilder":
        """Limit the number of matches.
        
        Args:
            n: Maximum number of matches
            
        Returns:
            Self for chaining
        """
        self._limit = n
        return self
    
    def order_by(self, key: str, desc: bool = False) -> "PatternQueryBuilder":
        """Order matches by a computed attribute (future enhancement).
        
        Args:
            key: Attribute key for ordering
            desc: Whether to sort descending
            
        Returns:
            Self for chaining
        """
        self._order_by = (key, desc)
        return self
    
    def explain(self) -> Dict[str, Any]:
        """Generate and return the compilation plan.
        
        Returns:
            Dictionary with compilation plan details
        """
        plan = compile_pattern(self._pattern)
        return plan.to_dict()
    
    def execute(self, network: Any, backend: str = "native", 
                max_matches: Optional[int] = None, timeout: Optional[float] = None) -> PatternQueryResult:
        """Execute the pattern query on a network.
        
        Args:
            network: Multilayer network object
            backend: Execution backend (currently only "native" supported)
            max_matches: Maximum number of matches (overrides .limit())
            timeout: Optional timeout in seconds
            
        Returns:
            PatternQueryResult with matches
        """
        if backend != "native":
            raise ValueError(f"Unsupported backend: {backend}. Only 'native' is currently supported.")
        
        # Use max_matches if provided, otherwise use limit
        limit = max_matches if max_matches is not None else self._limit
        
        # Compile the pattern
        plan = compile_pattern(self._pattern)
        
        # Execute the pattern
        matches = match_pattern(network, self._pattern, plan, limit=limit, timeout=timeout)
        
        # Create result object
        return PatternQueryResult(
            pattern=self._pattern,
            matches=matches,
            meta={
                "num_matches": len(matches),
                "limit": limit,
            }
        )
