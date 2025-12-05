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


# ==============================================================================
# Builder API for DSL Extensions
# ==============================================================================


class CompareBuilder:
    """Builder for COMPARE statements.
    
    Example:
        >>> from py3plex.dsl import C, L
        >>> 
        >>> result = (
        ...     C.compare("baseline", "intervention")
        ...      .using("multiplex_jaccard")
        ...      .on_layers(L["social"] + L["work"])
        ...      .measure("global_distance", "layerwise_distance")
        ...      .execute(networks)
        ... )
    """
    
    def __init__(self, network_a: str, network_b: str):
        """Initialize builder with two network names."""
        from .ast import CompareStmt
        self._stmt = CompareStmt(
            network_a=network_a,
            network_b=network_b,
            metric_name="multiplex_jaccard",
        )
    
    def using(self, metric: str) -> "CompareBuilder":
        """Set the comparison metric.
        
        Args:
            metric: Metric name (e.g., "multiplex_jaccard")
            
        Returns:
            Self for chaining
        """
        self._stmt.metric_name = metric
        return self
    
    def on_layers(self, layer_expr: LayerExprBuilder) -> "CompareBuilder":
        """Filter by layers using layer algebra.
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])
            
        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self
    
    def measure(self, *measures: str) -> "CompareBuilder":
        """Specify which measures to compute.
        
        Args:
            *measures: Measure names (e.g., "global_distance", "layerwise_distance")
            
        Returns:
            Self for chaining
        """
        self._stmt.measures.extend(measures)
        return self
    
    def to(self, target: str) -> "CompareBuilder":
        """Set export target.
        
        Args:
            target: Export format ('pandas', 'json')
            
        Returns:
            Self for chaining
        """
        self._stmt.export_target = target
        return self
    
    def execute(self, networks: Dict[str, Any]) -> "ComparisonResult":
        """Execute the comparison.
        
        Args:
            networks: Dictionary mapping network names to network objects
            
        Returns:
            ComparisonResult with comparison results
        """
        from py3plex.comparison import execute_compare_stmt
        return execute_compare_stmt(networks, self._stmt)
    
    def to_ast(self) -> "CompareStmt":
        """Export as AST CompareStmt object."""
        return self._stmt
    
    def __repr__(self) -> str:
        return f"CompareBuilder('{self._stmt.network_a}' vs '{self._stmt.network_b}')"


class C:
    """Compare factory for creating CompareBuilder instances.
    
    Example:
        >>> C.compare("baseline", "intervention").using("multiplex_jaccard")
    """
    
    @staticmethod
    def compare(network_a: str, network_b: str) -> CompareBuilder:
        """Create a comparison builder for two networks."""
        return CompareBuilder(network_a, network_b)


class NullModelBuilder:
    """Builder for NULLMODEL statements.
    
    Example:
        >>> from py3plex.dsl import N, L
        >>> 
        >>> result = (
        ...     N.model("configuration")
        ...      .on_layers(L["social"])
        ...      .with_params(preserve_degree=True)
        ...      .samples(100)
        ...      .seed(42)
        ...      .execute(network)
        ... )
    """
    
    def __init__(self, model_type: str):
        """Initialize builder with model type."""
        from .ast import NullModelStmt
        self._stmt = NullModelStmt(model_type=model_type)
    
    def on_layers(self, layer_expr: LayerExprBuilder) -> "NullModelBuilder":
        """Filter by layers using layer algebra.
        
        Args:
            layer_expr: Layer expression
            
        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self
    
    def with_params(self, **params) -> "NullModelBuilder":
        """Set model parameters.
        
        Args:
            **params: Model parameters
            
        Returns:
            Self for chaining
        """
        self._stmt.params.update(params)
        return self
    
    def samples(self, n: int) -> "NullModelBuilder":
        """Set number of samples to generate.
        
        Args:
            n: Number of samples
            
        Returns:
            Self for chaining
        """
        self._stmt.num_samples = n
        return self
    
    def seed(self, seed: int) -> "NullModelBuilder":
        """Set random seed.
        
        Args:
            seed: Random seed
            
        Returns:
            Self for chaining
        """
        self._stmt.seed = seed
        return self
    
    def to(self, target: str) -> "NullModelBuilder":
        """Set export target.
        
        Args:
            target: Export format
            
        Returns:
            Self for chaining
        """
        self._stmt.export_target = target
        return self
    
    def execute(self, network: Any) -> "NullModelResult":
        """Execute null model generation.
        
        Args:
            network: Multilayer network
            
        Returns:
            NullModelResult with generated samples
        """
        from py3plex.nullmodels import execute_nullmodel_stmt
        return execute_nullmodel_stmt(network, self._stmt)
    
    def to_ast(self) -> "NullModelStmt":
        """Export as AST NullModelStmt object."""
        return self._stmt
    
    def __repr__(self) -> str:
        return f"NullModelBuilder(model='{self._stmt.model_type}')"


class N:
    """NullModel factory for creating NullModelBuilder instances.
    
    Example:
        >>> N.model("configuration").samples(100).seed(42)
    """
    
    @staticmethod
    def model(model_type: str) -> NullModelBuilder:
        """Create a null model builder."""
        return NullModelBuilder(model_type)
    
    @staticmethod
    def configuration() -> NullModelBuilder:
        """Create a configuration model builder."""
        return NullModelBuilder("configuration")
    
    @staticmethod
    def erdos_renyi() -> NullModelBuilder:
        """Create an Erdős-Rényi model builder."""
        return NullModelBuilder("erdos_renyi")
    
    @staticmethod
    def layer_shuffle() -> NullModelBuilder:
        """Create a layer shuffle model builder."""
        return NullModelBuilder("layer_shuffle")
    
    @staticmethod
    def edge_swap() -> NullModelBuilder:
        """Create an edge swap model builder."""
        return NullModelBuilder("edge_swap")


class PathBuilder:
    """Builder for PATH statements.
    
    Example:
        >>> from py3plex.dsl import P, L
        >>> 
        >>> result = (
        ...     P.shortest("Alice", "Bob")
        ...      .on_layers(L["social"] + L["work"])
        ...      .crossing_layers()
        ...      .execute(network)
        ... )
    """
    
    def __init__(self, path_type: str, source: Any, target: Optional[Any] = None):
        """Initialize builder with path type and endpoints."""
        from .ast import PathStmt
        self._stmt = PathStmt(
            path_type=path_type,
            source=source,
            target=target,
        )
    
    def on_layers(self, layer_expr: LayerExprBuilder) -> "PathBuilder":
        """Filter by layers using layer algebra.
        
        Args:
            layer_expr: Layer expression
            
        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self
    
    def crossing_layers(self, allow: bool = True) -> "PathBuilder":
        """Allow or disallow cross-layer paths.
        
        Args:
            allow: Whether to allow cross-layer paths
            
        Returns:
            Self for chaining
        """
        self._stmt.cross_layer = allow
        return self
    
    def with_params(self, **params) -> "PathBuilder":
        """Set additional parameters.
        
        Args:
            **params: Additional parameters
            
        Returns:
            Self for chaining
        """
        self._stmt.params.update(params)
        return self
    
    def limit(self, n: int) -> "PathBuilder":
        """Limit number of results.
        
        Args:
            n: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self._stmt.limit = n
        return self
    
    def to(self, target: str) -> "PathBuilder":
        """Set export target.
        
        Args:
            target: Export format
            
        Returns:
            Self for chaining
        """
        self._stmt.export_target = target
        return self
    
    def execute(self, network: Any) -> "PathResult":
        """Execute path query.
        
        Args:
            network: Multilayer network
            
        Returns:
            PathResult with found paths
        """
        from py3plex.paths import execute_path_stmt
        return execute_path_stmt(network, self._stmt)
    
    def to_ast(self) -> "PathStmt":
        """Export as AST PathStmt object."""
        return self._stmt
    
    def __repr__(self) -> str:
        target_str = f" -> {self._stmt.target}" if self._stmt.target else ""
        return f"PathBuilder({self._stmt.path_type}: {self._stmt.source}{target_str})"


class P:
    """Path factory for creating PathBuilder instances.
    
    Example:
        >>> P.shortest("Alice", "Bob").crossing_layers()
        >>> P.random_walk("Alice").with_params(steps=100, teleport=0.1)
    """
    
    @staticmethod
    def shortest(source: Any, target: Any) -> PathBuilder:
        """Create a shortest path query builder."""
        return PathBuilder("shortest", source, target)
    
    @staticmethod
    def all_paths(source: Any, target: Any) -> PathBuilder:
        """Create an all-paths query builder."""
        return PathBuilder("all", source, target)
    
    @staticmethod
    def random_walk(source: Any) -> PathBuilder:
        """Create a random walk query builder."""
        return PathBuilder("random_walk", source)
    
    @staticmethod
    def flow(source: Any, target: Any) -> PathBuilder:
        """Create a flow analysis query builder."""
        return PathBuilder("flow", source, target)
