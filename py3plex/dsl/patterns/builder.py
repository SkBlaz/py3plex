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

from ..errors import DslSyntaxError
from .compiler import compile_pattern
from .engine import match_pattern
from .ir import (
    EdgeLayerConstraint,
    LayerConstraint,
    PatternEdge,
    PatternGraph,
    PatternNode,
    Predicate,
)
from .result import PatternQueryResult


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
    """Builder for configuring a pattern node variable."""

    def __init__(self, parent: "PatternQueryBuilder", var: str, labels: Optional[Union[str, List[str]]] = None):
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

    def __getattr__(self, name):
        return getattr(self._parent, name)

    def where(self, **kwargs) -> "PatternQueryBuilder":
        """Add predicates to the node."""
        for key, value in kwargs.items():
            if key == "layer":
                self._layer_constraint = LayerConstraint.one(value)
            elif "__" in key:
                attr, suffix = key.rsplit("__", 1)
                if suffix in COMPARATOR_MAP:
                    self._predicates.append(
                        Predicate(attr=attr, op=COMPARATOR_MAP[suffix], value=value)
                    )
                else:
                    raise DslSyntaxError(f"Unknown comparator suffix: {suffix}")
            else:
                self._predicates.append(Predicate(attr=key, op="=", value=value))

        node = PatternNode(
            var=self._var,
            labels=self._labels,
            predicates=self._predicates,
            layer_constraint=self._layer_constraint,
        )
        self._parent._pattern.add_node(node)
        return self._parent

    def in_layers(self, layers: Union[str, List[str]]) -> "PatternQueryBuilder":
        """Specify layer constraint for the node."""
        if layers == "*":
            self._layer_constraint = LayerConstraint.wildcard()
        elif isinstance(layers, str):
            self._layer_constraint = LayerConstraint.one(layers)
        else:
            self._layer_constraint = LayerConstraint.set_of(set(layers))

        node = PatternNode(
            var=self._var,
            labels=self._labels,
            predicates=self._predicates,
            layer_constraint=self._layer_constraint,
        )
        self._parent._pattern.add_node(node)
        return self._parent

    def label(self, *labels: str) -> "PatternNodeBuilder":
        """Add labels to the node."""
        if self._labels is None:
            self._labels = set()
        self._labels.update(labels)
        return self


class PatternEdgeBuilder:
    """Builder for configuring a pattern edge."""

    def __init__(self, parent: "PatternQueryBuilder", edge: PatternEdge):
        self._parent = parent
        self._edge = edge

    def __getattr__(self, name):
        return getattr(self._parent, name)

    def _require_edge(self) -> PatternEdge:
        if self._edge is None:
            raise DslSyntaxError("Pattern edge builder is not attached to an edge.")
        return self._edge

    def where(self, **kwargs) -> "PatternQueryBuilder":
        """Add predicates to the edge."""
        edge = self._require_edge()
        for key, value in kwargs.items():
            if "__" in key:
                attr, suffix = key.rsplit("__", 1)
                if suffix in COMPARATOR_MAP:
                    edge.predicates.append(
                        Predicate(attr=attr, op=COMPARATOR_MAP[suffix], value=value)
                    )
                else:
                    raise DslSyntaxError(f"Unknown comparator suffix: {suffix}")
            else:
                edge.predicates.append(Predicate(attr=key, op="=", value=value))
        return self._parent

    def within_layer(self, layer: str) -> "PatternQueryBuilder":
        """Constrain edge to be within a single layer."""
        edge = self._require_edge()
        edge.layer_constraint = EdgeLayerConstraint.within(layer)
        return self._parent

    def between_layers(self, src_layer: str, dst_layer: str) -> "PatternQueryBuilder":
        """Constrain edge to be between two specific layers."""
        edge = self._require_edge()
        edge.layer_constraint = EdgeLayerConstraint.between(src_layer, dst_layer)
        return self._parent

    def any_layer(self) -> "PatternQueryBuilder":
        """Allow edge to be in any layer."""
        edge = self._require_edge()
        edge.layer_constraint = EdgeLayerConstraint.any_layer()
        return self._parent


class PatternQueryBuilder:
    """Main builder for pattern queries."""

    def __init__(self):
        self._pattern = PatternGraph()
        self._limit: Optional[int] = None
        self._order_by: Optional[Tuple[str, bool]] = None

    def node(self, var: str, labels: Optional[Union[str, List[str]]] = None) -> PatternNodeBuilder:
        """Add a node variable to the pattern."""
        node_builder = PatternNodeBuilder(self, var, labels)
        self._pattern.add_node(PatternNode(var=var, labels=node_builder._labels))
        return node_builder

    def edge(
        self,
        src: str,
        dst: str,
        directed: bool = False,
        etype: Optional[str] = None,
    ) -> PatternEdgeBuilder:
        """Add an edge between two node variables."""
        edge = PatternEdge(src=src, dst=dst, directed=directed, etype=etype)
        self._pattern.add_edge(edge)
        return PatternEdgeBuilder(self, edge)

    def path(
        self,
        vars: Union[List[str], Tuple[str, ...]],
        directed: bool = False,
        etype: Optional[str] = None,
        length: Optional[int] = None,
    ) -> "PatternQueryBuilder":
        """Add a path pattern."""
        if len(vars) < 2:
            raise DslSyntaxError("Path must have at least 2 variables")

        for index in range(len(vars) - 1):
            self._pattern.add_edge(
                PatternEdge(
                    src=vars[index],
                    dst=vars[index + 1],
                    directed=directed,
                    etype=etype,
                )
            )
        return self

    def triangle(self, a: str, b: str, c: str, directed: bool = False) -> "PatternQueryBuilder":
        """Add a triangle motif."""
        for edge in (
            PatternEdge(src=a, dst=b, directed=directed),
            PatternEdge(src=b, dst=c, directed=directed),
            PatternEdge(src=c, dst=a, directed=directed),
        ):
            self._pattern.add_edge(edge)
        return self

    def constraint(self, expr: str) -> "PatternQueryBuilder":
        """Add a global constraint.

        Supported forms:
            - "a != b"
            - "all_distinct(a, b, c)"
        """
        self._pattern.add_constraint(expr)
        return self

    def returning(self, *vars: str) -> "PatternQueryBuilder":
        """Specify which variables to return in results."""
        self._pattern.return_vars = list(vars)
        return self

    def limit(self, n: int) -> "PatternQueryBuilder":
        """Limit the number of matches."""
        self._limit = n
        return self

    def order_by(self, key: str, desc: bool = False) -> "PatternQueryBuilder":
        """Order matches by a computed attribute (future enhancement)."""
        self._order_by = (key, desc)
        return self

    def explain(self) -> Dict[str, Any]:
        """Generate and return the compilation plan."""
        plan = compile_pattern(self._pattern, network=None)
        return plan.to_dict()

    def execute(
        self,
        network: Any,
        backend: str = "native",
        max_matches: Optional[int] = None,
        timeout: Optional[float] = None,
        injective: bool = True,
    ) -> PatternQueryResult:
        """Execute the pattern query on a network."""
        if backend != "native":
            raise ValueError(
                f"Unsupported backend: {backend}. Only 'native' is currently supported."
            )

        limit = max_matches if max_matches is not None else self._limit
        plan = compile_pattern(self._pattern, network=network, injective=injective)
        matches = match_pattern(network, self._pattern, plan, limit=limit, timeout=timeout)

        return PatternQueryResult(
            pattern=self._pattern,
            matches=matches,
            meta={
                "num_matches": len(matches),
                "limit": limit,
                "injective": injective,
            },
        )
