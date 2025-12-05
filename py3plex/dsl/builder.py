"""Python Builder API for DSL v2.

This module provides a chainable, type-hinted builder API for constructing
DSL queries. The builder API maps directly to the AST nodes.

Example:
    >>> from py3plex.dsl import Q, L, Param
    >>> 
    >>> q = (
    ...     Q.nodes()
    ...      .from_layers(L["social"] + L["work"])
    ...      .where(intralayer=True, degree__gt=Param.int("k"))
    ...      .compute("betweenness_centrality", alias="bc")
    ...      .order_by("bc", desc=True)
    ...      .limit(20)
    ... )
    >>> 
    >>> result = q.execute(network, k=5)
"""

from typing import Any, Dict, List, Optional, Union

from .ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    ExecutionPlan,
)
from .result import QueryResult


# Comparator suffix mapping
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


def _wrap_value(v: Any) -> Union[str, float, int, ParamRef]:
    """Wrap a value for use in comparisons."""
    if isinstance(v, ParamRef):
        return v
    if isinstance(v, (int, float, str)):
        return v
    raise TypeError(f"Unsupported value type for condition: {type(v)}")


def build_condition_from_kwargs(kwargs: Dict[str, Any]) -> ConditionExpr:
    """Build ConditionExpr from keyword arguments.
    
    Supported patterns:
        - layer="social" → Comparison("layer", "=", "social")
        - degree__gt=5 → Comparison("degree", ">", 5)
        - intralayer=True → SpecialPredicate("intralayer", {})
        - interlayer=("social","work") → SpecialPredicate("interlayer", {...})
    
    Args:
        kwargs: Keyword arguments representing conditions
        
    Returns:
        ConditionExpr with parsed conditions
    """
    atoms: List[ConditionAtom] = []
    ops: List[str] = []
    
    for i, (key, value) in enumerate(kwargs.items()):
        if "__" in key:
            # Handle comparison suffix: degree__gt=5
            parts = key.rsplit("__", 1)
            attr = parts[0]
            suffix = parts[1]
            
            if suffix in COMPARATOR_MAP:
                cmp = Comparison(left=attr, op=COMPARATOR_MAP[suffix], right=_wrap_value(value))
                atoms.append(ConditionAtom(comparison=cmp))
            else:
                raise ValueError(f"Unknown comparison suffix: {suffix}")
        
        elif key == "intralayer":
            if value:
                atoms.append(ConditionAtom(
                    special=SpecialPredicate(kind="intralayer", params={})
                ))
        
        elif key == "interlayer":
            if isinstance(value, tuple) and len(value) == 2:
                src, dst = value
                atoms.append(ConditionAtom(
                    special=SpecialPredicate(
                        kind="interlayer",
                        params={"src": src, "dst": dst}
                    )
                ))
            else:
                raise ValueError("interlayer requires a tuple of (src_layer, dst_layer)")
        
        else:
            # Simple equality: layer="social"
            cmp = Comparison(left=key, op="=", right=_wrap_value(value))
            atoms.append(ConditionAtom(comparison=cmp))
        
        # Add AND between conditions
        if i > 0:
            ops.append("AND")
    
    return ConditionExpr(atoms=atoms, ops=ops)


class LayerExprBuilder:
    """Builder for layer expressions.
    
    Supports layer algebra:
        - Union: L["social"] + L["work"]
        - Difference: L["social"] - L["bots"]
        - Intersection: L["social"] & L["work"]
    """
    
    def __init__(self, term: str):
        """Initialize with a layer name."""
        self.terms = [LayerTerm(term)]
        self.ops: List[str] = []
    
    def __add__(self, other: "LayerExprBuilder") -> "LayerExprBuilder":
        """Union of layers: L["a"] + L["b"]"""
        result = LayerExprBuilder.__new__(LayerExprBuilder)
        result.terms = self.terms + other.terms
        result.ops = self.ops + ["+"] + other.ops
        return result
    
    def __sub__(self, other: "LayerExprBuilder") -> "LayerExprBuilder":
        """Difference of layers: L["a"] - L["b"]"""
        result = LayerExprBuilder.__new__(LayerExprBuilder)
        result.terms = self.terms + other.terms
        result.ops = self.ops + ["-"] + other.ops
        return result
    
    def __and__(self, other: "LayerExprBuilder") -> "LayerExprBuilder":
        """Intersection of layers: L["a"] & L["b"]"""
        result = LayerExprBuilder.__new__(LayerExprBuilder)
        result.terms = self.terms + other.terms
        result.ops = self.ops + ["&"] + other.ops
        return result
    
    def _to_ast(self) -> LayerExpr:
        """Convert to AST LayerExpr."""
        return LayerExpr(terms=self.terms, ops=self.ops)
    
    def __repr__(self) -> str:
        names = [t.name for t in self.terms]
        if not self.ops:
            return f"L[{names[0]!r}]"
        
        parts = [f"LAYER({names[0]!r})"]
        for op, name in zip(self.ops, names[1:]):
            parts.append(f" {op} LAYER({name!r})")
        return "".join(parts)


class LayerProxy:
    """Proxy for creating layer expressions via L["name"] syntax."""
    
    def __getitem__(self, name: str) -> LayerExprBuilder:
        """Create a layer expression builder for the given layer name."""
        return LayerExprBuilder(name)


# Global layer proxy
L = LayerProxy()


class Param:
    """Factory for parameter references.
    
    Parameters are placeholders in queries that are bound at execution time.
    
    Example:
        >>> q = Q.nodes().where(degree__gt=Param.int("k"))
        >>> result = q.execute(network, k=5)
    """
    
    @staticmethod
    def int(name: str) -> ParamRef:
        """Create an integer parameter reference."""
        return ParamRef(name=name, type_hint="int")
    
    @staticmethod
    def float(name: str) -> ParamRef:
        """Create a float parameter reference."""
        return ParamRef(name=name, type_hint="float")
    
    @staticmethod
    def str(name: str) -> ParamRef:
        """Create a string parameter reference."""
        return ParamRef(name=name, type_hint="str")
    
    @staticmethod
    def ref(name: str) -> ParamRef:
        """Create a parameter reference without type hint."""
        return ParamRef(name=name)


class ExplainQuery:
    """Wrapper for EXPLAIN queries that returns execution plans."""
    
    def __init__(self, select: SelectStmt):
        self._select = select
    
    def execute(self, network: Any, **params) -> ExecutionPlan:
        """Execute EXPLAIN query and return execution plan.
        
        Args:
            network: Multilayer network object
            **params: Parameter bindings
            
        Returns:
            ExecutionPlan with steps and warnings
        """
        from .executor import execute_ast
        
        ast = Query(explain=True, select=self._select)
        return execute_ast(network, ast, params=params)
    
    def to_ast(self) -> Query:
        """Export as AST Query object."""
        return Query(explain=True, select=self._select)


class QueryBuilder:
    """Chainable query builder.
    
    Use Q.nodes() or Q.edges() to create a builder, then chain methods
    to construct the query.
    """
    
    def __init__(self, target: Target):
        """Initialize builder with target."""
        self._select = SelectStmt(target=target)
    
    def from_layers(self, layer_expr: LayerExprBuilder) -> "QueryBuilder":
        """Filter by layers using layer algebra.
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])
            
        Returns:
            Self for chaining
        """
        self._select.layer_expr = layer_expr._to_ast()
        return self
    
    def where(self, **kwargs) -> "QueryBuilder":
        """Add WHERE conditions.
        
        Supports:
            - layer="social" → equality
            - degree__gt=5 → comparison (gt, ge, lt, le, eq, ne)
            - intralayer=True → intralayer predicate
            - interlayer=("social","work") → interlayer predicate
        
        Args:
            **kwargs: Conditions as keyword arguments
            
        Returns:
            Self for chaining
        """
        if kwargs:
            condition = build_condition_from_kwargs(kwargs)
            if self._select.where is None:
                self._select.where = condition
            else:
                # Merge conditions with AND
                self._select.where.atoms.extend(condition.atoms)
                self._select.where.ops.append("AND")
                self._select.where.ops.extend(condition.ops)
        return self
    
    def compute(self, *measures: str, alias: Optional[str] = None,
                aliases: Optional[Dict[str, str]] = None) -> "QueryBuilder":
        """Add measures to compute.
        
        Args:
            *measures: Measure names to compute
            alias: Alias for single measure
            aliases: Dictionary mapping measure names to aliases
            
        Returns:
            Self for chaining
        """
        items: List[ComputeItem] = []
        
        if aliases:
            for name, al in aliases.items():
                items.append(ComputeItem(name=name, alias=al))
        elif alias and len(measures) == 1:
            items.append(ComputeItem(name=measures[0], alias=alias))
        else:
            items.extend(ComputeItem(name=m) for m in measures)
        
        self._select.compute.extend(items)
        return self
    
    def order_by(self, *keys: str, desc: bool = False) -> "QueryBuilder":
        """Add ORDER BY clause.
        
        Args:
            *keys: Attribute names to order by (prefix with "-" for descending)
            desc: Default sort direction
            
        Returns:
            Self for chaining
        """
        for k in keys:
            if k.startswith("-"):
                self._select.order_by.append(OrderItem(key=k[1:], desc=True))
            else:
                self._select.order_by.append(OrderItem(key=k, desc=desc))
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Limit number of results.
        
        Args:
            n: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self._select.limit = n
        return self
    
    def to(self, target: str) -> "QueryBuilder":
        """Set export target.
        
        Args:
            target: Export format ('pandas', 'networkx', 'arrow')
            
        Returns:
            Self for chaining
        """
        target_map = {
            "pandas": ExportTarget.PANDAS,
            "networkx": ExportTarget.NETWORKX,
            "arrow": ExportTarget.ARROW,
        }
        if target.lower() not in target_map:
            raise ValueError(f"Unknown export target: {target}. Options: {list(target_map.keys())}")
        self._select.export = target_map[target.lower()]
        return self
    
    def explain(self) -> ExplainQuery:
        """Create EXPLAIN query for execution plan.
        
        Returns:
            ExplainQuery that can be executed to get the plan
        """
        return ExplainQuery(self._select)
    
    def execute(self, network: Any, **params) -> QueryResult:
        """Execute the query.
        
        Args:
            network: Multilayer network object
            **params: Parameter bindings
            
        Returns:
            QueryResult with results and metadata
        """
        from .executor import execute_ast
        
        ast = Query(explain=False, select=self._select)
        return execute_ast(network, ast, params=params)
    
    def to_ast(self) -> Query:
        """Export as AST Query object.
        
        Returns:
            Query AST node
        """
        return Query(explain=False, select=self._select)
    
    def to_dsl(self) -> str:
        """Export as DSL string.
        
        Returns:
            DSL query string
        """
        from .serializer import ast_to_dsl
        return ast_to_dsl(self.to_ast())
    
    def __repr__(self) -> str:
        return f"QueryBuilder(target={self._select.target.value})"


class Q:
    """Query factory for creating QueryBuilder instances.
    
    Example:
        >>> Q.nodes().where(layer="social").compute("degree")
        >>> Q.edges().where(intralayer=True)
    """
    
    @staticmethod
    def nodes() -> QueryBuilder:
        """Create a query builder for nodes."""
        return QueryBuilder(Target.NODES)
    
    @staticmethod
    def edges() -> QueryBuilder:
        """Create a query builder for edges."""
        return QueryBuilder(Target.EDGES)
