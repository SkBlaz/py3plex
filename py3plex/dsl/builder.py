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
    >>> 
    >>> # Temporal queries
    >>> q = Q.edges().at(150.0).execute(network)  # Snapshot at t=150
    >>> q = Q.edges().during(100.0, 200.0).execute(network)  # Range [100, 200]
"""

import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .layers import LayerSet

from .ast import (
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    ExportSpec,
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
    TemporalContext,
    WindowSpec,
    UQConfig,
)
from .result import QueryResult

from py3plex.uncertainty import (
    get_uncertainty_config,
    set_uncertainty_config,
    UncertaintyConfig,
    UncertaintyMode,
    ResamplingStrategy,
)


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

_RESAMPLING_TO_METHOD = {
    ResamplingStrategy.BOOTSTRAP: "bootstrap",
    ResamplingStrategy.PERTURBATION: "perturbation",
    ResamplingStrategy.SEED: "seed",
    # Jackknife currently maps to seed-style multi-run execution until dedicated support lands
    ResamplingStrategy.JACKKNIFE: "seed",
}
_METHOD_TO_RESAMPLING = {v: k for k, v in _RESAMPLING_TO_METHOD.items()}


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
        - t__between=(100, 200) → SpecialPredicate("temporal_range", {...})
        - t__gte=100 → Comparison("t", ">=", 100)
    
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
            
            # Special handling for t__between
            if attr == "t" and suffix == "between":
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    atoms.append(ConditionAtom(
                        special=SpecialPredicate(
                            kind="temporal_range",
                            params={"t_start": value[0], "t_end": value[1]}
                        )
                    ))
                else:
                    raise ValueError("t__between requires a tuple of (t_start, t_end)")
            elif suffix in COMPARATOR_MAP:
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
    """Proxy for creating layer expressions via L["name"] syntax.
    
    Supports both simple layer names and advanced string expressions:
        - L["social"] → single layer (backward compatible)
        - L["social", "work"] → union of layers (backward compatible)
        - L["* - coupling"] → string expression with algebra (NEW)
        - L["(ppi | gene) & disease"] → complex expression (NEW)
    
    The proxy automatically detects whether to use the old LayerExprBuilder
    (for simple names) or the new LayerSet (for expressions with operators).
    """
    
    def __getitem__(self, name_or_names) -> Union[LayerExprBuilder, "LayerSet"]:
        """Create a layer expression builder for the given layer name(s).
        
        Supports:
        - Single layer: L["social"]
        - Multiple layers: L["social", "work"] (union)
        - String expressions: L["* - coupling"]
        - Complex expressions: L["(ppi | gene) & disease"]
        
        Returns:
            LayerExprBuilder for simple cases (backward compatibility)
            LayerSet for expressions with operators (new feature)
        """
        # Import LayerSet here to avoid circular dependency
        from .layers import LayerSet
        
        if isinstance(name_or_names, (tuple, list)):
            # Multiple layers - create union (backward compatible)
            if not name_or_names:
                raise ValueError("Cannot create layer expression with empty list")
            
            # Start with first layer
            result = LayerExprBuilder(name_or_names[0])
            
            # Add remaining layers with union operator
            for name in name_or_names[1:]:
                result = result + LayerExprBuilder(name)
            
            return result
        
        # Single name/expression
        name = name_or_names
        
        # Check if this is an expression string (contains operators)
        if isinstance(name, str) and self._is_expression(name):
            # Use new LayerSet with parsing
            return LayerSet.parse(name)
        else:
            # Use old LayerExprBuilder (backward compatible)
            return LayerExprBuilder(name)
    
    def _is_expression(self, text: str) -> bool:
        """Check if text contains layer algebra operators.
        
        Returns True if the text is a complex expression that needs parsing,
        False if it's a simple layer name.
        """
        # Check for operators (but not at start for complement)
        operators = ["|", "&", "+"]
        for op in operators:
            if op in text:
                return True
        
        # Check for difference operator (must not be part of identifier)
        # E.g., "layer-name" is valid, but "layer - name" is an expression
        if " - " in text or text.startswith("- ") or text.endswith(" -"):
            return True
        
        # Check for parentheses
        if "(" in text or ")" in text:
            return True
        
        # Check for complement
        if text.startswith("~"):
            return True
        
        return False
    
    @staticmethod
    def define(name: str, layer_expr: Union[LayerExprBuilder, "LayerSet"]) -> None:
        """Define a named layer group for reuse.
        
        Args:
            name: Group name
            layer_expr: LayerExprBuilder or LayerSet to associate with the name
            
        Example:
            >>> bio = L["ppi"] | L["gene"] | L["disease"]
            >>> L.define("bio", bio)
            >>> 
            >>> # Later use the group
            >>> result = Q.nodes().from_layers(L["bio"]).execute(net)
        """
        from .layers import LayerSet
        
        # Convert LayerExprBuilder to LayerSet if needed
        if isinstance(layer_expr, LayerExprBuilder):
            # Build a LayerSet from the LayerExprBuilder
            # This requires converting the AST format
            layer_set = _convert_expr_builder_to_layer_set(layer_expr)
        else:
            layer_set = layer_expr
        
        LayerSet.define_group(name, layer_set)
    
    @staticmethod
    def list_groups() -> Dict[str, Any]:
        """List all defined layer groups.
        
        Returns:
            Dictionary mapping group names to layer expressions
        """
        from .layers import LayerSet
        return LayerSet.list_groups()
    
    @staticmethod
    def clear_groups() -> None:
        """Clear all defined layer groups."""
        from .layers import LayerSet
        LayerSet.clear_groups()


def _convert_expr_builder_to_layer_set(builder: LayerExprBuilder) -> "LayerSet":
    """Convert LayerExprBuilder to LayerSet for group definition.
    
    Args:
        builder: LayerExprBuilder instance
        
    Returns:
        Equivalent LayerSet
    """
    from .layers import LayerSet
    
    # Start with first term
    if not builder.terms:
        raise ValueError("Empty LayerExprBuilder")
    
    result = LayerSet(builder.terms[0].name)
    
    # Apply operations
    for i, op in enumerate(builder.ops):
        next_term = LayerSet(builder.terms[i + 1].name)
        
        if op == "+":
            result = result | next_term
        elif op == "-":
            result = result - next_term
        elif op == "&":
            result = result & next_term
    
    return result


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
    
    def __init__(self, target: Target, autocompute: bool = True):
        """Initialize builder with target.
        
        Args:
            target: Query target (NODES or EDGES)
            autocompute: Whether to automatically compute missing metrics (default: True)
        """
        self._select = SelectStmt(target=target, autocompute=autocompute)
    
    def from_layers(self, layer_expr: Union[LayerExprBuilder, "LayerSet"]) -> "QueryBuilder":
        """Filter by layers using layer algebra.
        
        Supports both LayerExprBuilder (backward compatible) and LayerSet (new).
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"] or L["* - coupling"])
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Old style (still works)
            >>> Q.nodes().from_layers(L["social"] + L["work"])
            >>> 
            >>> # New style with string expressions
            >>> Q.nodes().from_layers(L["* - coupling"])
            >>> Q.nodes().from_layers(L["(ppi | gene) & disease"])
        """
        from .layers import LayerSet
        
        if isinstance(layer_expr, LayerSet):
            # Store LayerSet directly in a new field
            self._select.layer_set = layer_expr
            # Clear the old layer_expr to avoid conflicts
            self._select.layer_expr = None
        else:
            # LayerExprBuilder - use old path
            self._select.layer_expr = layer_expr._to_ast()
            # Clear layer_set
            if hasattr(self._select, 'layer_set'):
                self._select.layer_set = None
        
        return self
    
    def where(self, *args, **kwargs) -> "QueryBuilder":
        """Add WHERE conditions.
        
        Supports two styles:
        
        1. Keyword arguments:
            - layer="social" → equality
            - degree__gt=5 → comparison (gt, ge, lt, le, eq, ne)
            - intralayer=True → intralayer predicate
            - interlayer=("social","work") → interlayer predicate
        
        2. Expression objects (using F):
            - where(F.degree > 5)
            - where((F.degree > 5) & (F.layer == "social"))
            - where((F.degree > 10) | (F.clustering < 0.5))
        
        Can mix both styles:
            - where(F.degree > 5, layer="social")
        
        Args:
            *args: BooleanExpression objects from F
            **kwargs: Conditions as keyword arguments
            
        Returns:
            Self for chaining
        """
        # Import here to avoid circular dependency
        from .expressions import BooleanExpression
        
        # Process expression arguments
        for arg in args:
            if isinstance(arg, BooleanExpression):
                condition = arg.to_condition_expr()
                if self._select.where is None:
                    self._select.where = condition
                else:
                    # Merge conditions with AND
                    self._select.where.atoms.extend(condition.atoms)
                    if condition.atoms:  # Only add AND if there are atoms to add
                        self._select.where.ops.append("AND")
                    self._select.where.ops.extend(condition.ops)
            else:
                raise TypeError(
                    f"Positional arguments to where() must be BooleanExpression objects (from F), "
                    f"got {type(arg)}"
                )
        
        # Process keyword arguments
        if kwargs:
            condition = build_condition_from_kwargs(kwargs)
            if self._select.where is None:
                self._select.where = condition
            else:
                # Merge conditions with AND
                self._select.where.atoms.extend(condition.atoms)
                if condition.atoms:
                    self._select.where.ops.append("AND")
                self._select.where.ops.extend(condition.ops)
        
        return self
    
    def compute(self, *measures: str, alias: Optional[str] = None,
                aliases: Optional[Dict[str, str]] = None,
                uncertainty: Optional[bool] = None,
                method: Optional[str] = None,
                n_samples: Optional[int] = None,
                ci: Optional[float] = None,
                bootstrap_unit: Optional[str] = None,
                bootstrap_mode: Optional[str] = None,
                n_boot: Optional[int] = None,
                n_null: Optional[int] = None,
                null_model: Optional[str] = None,
                random_state: Optional[int] = None) -> "QueryBuilder":
        """Add measures to compute with optional uncertainty estimation.
        
        Args:
            *measures: Measure names to compute
            alias: Alias for single measure
            aliases: Dictionary mapping measure names to aliases
            uncertainty: Whether to compute uncertainty for these measures. If None,
                uses Q.uncertainty defaults or the global uncertainty context.
            method: Uncertainty estimation method ('bootstrap', 'perturbation', 'seed', 'null_model')
            n_samples: Number of samples for uncertainty estimation (default: from Q.uncertainty.defaults)
            ci: Confidence interval level (default: from Q.uncertainty.defaults)
            bootstrap_unit: What to resample - "edges", "nodes", or "layers" (default: from Q.uncertainty.defaults)
            bootstrap_mode: Resampling mode - "resample" or "permute" (default: from Q.uncertainty.defaults)
            n_boot: Alias for n_samples (for bootstrap)
            n_null: Number of null model replicates (default: from Q.uncertainty.defaults)
            null_model: Null model type - "degree_preserving", "erdos_renyi", "configuration" (default: from Q.uncertainty.defaults)
            random_state: Random seed for reproducibility (default: from Q.uncertainty.defaults)
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Without uncertainty
            >>> Q.nodes().compute("degree", "betweenness_centrality")
            
            >>> # With uncertainty using explicit parameters
            >>> Q.nodes().compute(
            ...     "degree", "betweenness_centrality",
            ...     uncertainty=True,
            ...     method="bootstrap",
            ...     n_samples=500,
            ...     ci=0.95
            ... )
            
            >>> # With uncertainty using global defaults
            >>> Q.uncertainty.defaults(n_boot=500, ci=0.95)
            >>> Q.nodes().compute("degree", uncertainty=True)
        """
        # Determine whether to compute uncertainty:
        # Priority order:
        # 1) explicit uncertainty argument wins
        # 2) query-level uq_config (from .uq() method)
        # 3) Q.uncertainty.enabled=True
        # 4) global uncertainty context set to ON
        cfg = get_uncertainty_config()
        if uncertainty is None:
            # Check for query-level UQ config first
            if self._select.uq_config is not None:
                uncertainty_flag = True
            else:
                uncertainty_flag = bool(Q.uncertainty.get("enabled", False) or cfg.mode == UncertaintyMode.ON)
        else:
            uncertainty_flag = bool(uncertainty)

        # Get defaults from query-level uq_config, Q.uncertainty, or context
        # Priority: explicit params > query uq_config > Q.uncertainty > global context
        if uncertainty_flag:
            # Apply defaults for unspecified parameters
            if method is None:
                # Check query-level config first
                if self._select.uq_config is not None and self._select.uq_config.method is not None:
                    method = self._select.uq_config.method
                else:
                    method = Q.uncertainty.get("method")
                if method is None:
                    method = _RESAMPLING_TO_METHOD.get(cfg.default_resampling)
                if method is None:
                    method = "bootstrap"

            if n_samples is None and n_boot is None:
                # Check query-level config first
                if self._select.uq_config is not None and self._select.uq_config.n_samples is not None:
                    n_samples = self._select.uq_config.n_samples
                else:
                    n_samples = Q.uncertainty.get("n_boot", cfg.default_n_runs)
            # n_boot takes precedence over n_samples for clarity
            if n_boot is not None:
                n_samples = n_boot
            if ci is None:
                # Check query-level config first
                if self._select.uq_config is not None and self._select.uq_config.ci is not None:
                    ci = self._select.uq_config.ci
                else:
                    ci = Q.uncertainty.get("ci", 0.95)
            if bootstrap_unit is None:
                # Check query-level config kwargs first
                if self._select.uq_config is not None:
                    bootstrap_unit = self._select.uq_config.kwargs.get("bootstrap_unit")
                if bootstrap_unit is None:
                    bootstrap_unit = Q.uncertainty.get("bootstrap_unit", "edges")
            if bootstrap_mode is None:
                # Check query-level config kwargs first
                if self._select.uq_config is not None:
                    bootstrap_mode = self._select.uq_config.kwargs.get("bootstrap_mode")
                if bootstrap_mode is None:
                    bootstrap_mode = Q.uncertainty.get("bootstrap_mode", "resample")
            if n_null is None:
                # Check query-level config kwargs first
                if self._select.uq_config is not None:
                    n_null = self._select.uq_config.kwargs.get("n_null")
                if n_null is None:
                    n_null = Q.uncertainty.get("n_null", 200)
            if null_model is None:
                # Check query-level config kwargs first
                if self._select.uq_config is not None:
                    null_model = self._select.uq_config.kwargs.get("null_model")
                if null_model is None:
                    null_model = Q.uncertainty.get("null_model", "degree_preserving")
            if random_state is None:
                # Check query-level config first (seed field)
                if self._select.uq_config is not None and self._select.uq_config.seed is not None:
                    random_state = self._select.uq_config.seed
                else:
                    random_state = Q.uncertainty.get("random_state")
        
        items: List[ComputeItem] = []
        
        if aliases:
            for name, al in aliases.items():
                items.append(ComputeItem(
                    name=name, 
                    alias=al,
                    uncertainty=uncertainty_flag,
                    method=method,
                    n_samples=n_samples,
                    ci=ci,
                    bootstrap_unit=bootstrap_unit,
                    bootstrap_mode=bootstrap_mode,
                    n_null=n_null,
                    null_model=null_model,
                    random_state=random_state,
                ))
        elif alias and len(measures) == 1:
            items.append(ComputeItem(
                name=measures[0], 
                alias=alias,
                uncertainty=uncertainty_flag,
                method=method,
                n_samples=n_samples,
                ci=ci,
                bootstrap_unit=bootstrap_unit,
                bootstrap_mode=bootstrap_mode,
                n_null=n_null,
                null_model=null_model,
                random_state=random_state,
            ))
        else:
            items.extend(
                ComputeItem(
                    name=m,
                    uncertainty=uncertainty_flag,
                    method=method,
                    n_samples=n_samples,
                    ci=ci,
                    bootstrap_unit=bootstrap_unit,
                    bootstrap_mode=bootstrap_mode,
                    n_null=n_null,
                    null_model=null_model,
                    random_state=random_state,
                ) for m in measures
            )
        
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
    
    def uq(self, method: Optional[str] = "perturbation", 
           n_samples: Optional[int] = 50, 
           ci: Optional[float] = 0.95, 
           seed: Optional[int] = None,
           **kwargs) -> "QueryBuilder":
        """Set query-scoped uncertainty quantification configuration.
        
        This method establishes uncertainty defaults for all metrics computed
        in this query, unless overridden on a per-metric basis in compute().
        
        Args:
            method: Uncertainty estimation method ('bootstrap', 'perturbation', 'seed', 'null_model')
                   Pass None to disable query-level uncertainty.
            n_samples: Number of samples for uncertainty estimation (default: 50)
            ci: Confidence interval level (default: 0.95 for 95% CI)
            seed: Random seed for reproducibility (default: None)
            **kwargs: Additional method-specific parameters (e.g., bootstrap_unit='edges',
                     bootstrap_mode='resample', null_model='configuration')
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Set uncertainty defaults for the query
            >>> (Q.nodes()
            ...   .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)
            ...   .compute("betweenness_centrality")
            ...   .where(betweenness_centrality__mean__gt=0.1)
            ...   .execute(net))
            
            >>> # Use UQ profile (see UQ class for presets)
            >>> (Q.nodes()
            ...   .uq(UQ.fast(seed=7))
            ...   .compute("degree")
            ...   .execute(net))
            
            >>> # Disable query-level uncertainty
            >>> Q.nodes().uq(method=None).compute("degree").execute(net)
        """
        # Handle UQConfig instance passed directly
        if isinstance(method, UQConfig):
            self._select.uq_config = method
            return self
        
        # Create UQConfig or clear it
        if method is None:
            self._select.uq_config = None
        else:
            self._select.uq_config = UQConfig(
                method=method,
                n_samples=n_samples,
                ci=ci,
                seed=seed,
                kwargs=kwargs
            )
        return self
    
    def uncertainty(self, method: Optional[str] = "perturbation", 
                    n_samples: Optional[int] = 50, 
                    ci: Optional[float] = 0.95, 
                    seed: Optional[int] = None,
                    **kwargs) -> "QueryBuilder":
        """Alias for uq() - set query-scoped uncertainty configuration.
        
        See uq() for full documentation.
        """
        return self.uq(method=method, n_samples=n_samples, ci=ci, seed=seed, **kwargs)
    
    def group_by(self, *fields: str) -> "QueryBuilder":
        """Group result items by given fields.
        
        This is the low-level grouping primitive used by per_layer().
        Once grouping is established, you can apply per-group operations like top_k().
        
        Args:
            *fields: Attribute names to group by (e.g., "layer")
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().group_by("layer").top_k(5, "degree")
        """
        self._select.group_by = list(fields)
        return self
    
    def per_layer(self) -> "QueryBuilder":
        """Group results by layer (sugar for group_by("layer")).
        
        This is the most common grouping operation for multilayer queries.
        After calling this, you can apply per-layer operations like top_k().
        
        Note: Only valid for node queries. For edge queries, use per_layer_pair().
        
        Returns:
            Self for chaining
            
        Raises:
            DslExecutionError: If called on an edge query
            
        Example:
            >>> Q.nodes().per_layer().top_k(5, "betweenness_centrality")
        """
        # Check that we're working with nodes
        if self._select.target == Target.EDGES:
            from .errors import DslExecutionError
            raise DslExecutionError(
                "per_layer() is defined only for node queries. "
                "For edge queries use per_layer_pair()."
            )
        return self.group_by("layer")
    
    def per_layer_pair(self) -> "QueryBuilder":
        """Group edge results by (src_layer, dst_layer) pair.
        
        This is the grouping operation for edge queries in multilayer networks.
        After calling this, you can apply per-layer-pair operations like top_k().
        
        Note: Only valid for edge queries. For node queries, use per_layer().
        
        Returns:
            Self for chaining
            
        Raises:
            DslExecutionError: If called on a node query
            
        Example:
            >>> Q.edges().per_layer_pair().top_k(5, "edge_betweenness_centrality")
        """
        # Check that we're working with edges
        if self._select.target == Target.NODES:
            from .errors import DslExecutionError
            raise DslExecutionError(
                "per_layer_pair() is defined only for edge queries. "
                "For node queries use per_layer()."
            )
        return self.group_by("src_layer", "dst_layer")
    
    def top_k(self, k: int, key: Optional[str] = None) -> "QueryBuilder":
        """Keep the top-k items per group, ordered by the given key.
        
        Requires that group_by() or per_layer() has been called first.
        
        Args:
            k: Number of items to keep per group
            key: Attribute/measure to sort by (descending). If None, uses existing order_by.
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If called without prior grouping
            
        Example:
            >>> Q.nodes().per_layer().top_k(5, "betweenness_centrality")
        """
        # Validate that grouping has been set up
        if not self._select.group_by:
            raise ValueError(
                "top_k() requires grouping. Call .group_by() or .per_layer() first."
            )
        
        # If a key is provided, configure order_by accordingly (descending)
        if key is not None:
            # Clear existing order_by and set new one
            self._select.order_by.clear()
            self.order_by(f"-{key}")
        
        # Store the per-group limit
        self._select.limit_per_group = int(k)
        return self
    
    def end_grouping(self) -> "QueryBuilder":
        """Marker for the end of grouping configuration.
        
        This is purely for API readability and has no effect on execution.
        It helps visually separate grouping operations from post-grouping operations.
        
        Returns:
            Self for chaining
            
        Example:
            >>> (Q.nodes()
            ...   .per_layer()
            ...     .top_k(5, "degree")
            ...   .end_grouping()
            ...   .coverage(mode="all"))
        """
        return self
    
    def coverage(
        self,
        mode: str = "all",
        k: Optional[int] = None,
        threshold: Optional[int] = None,
        p: Optional[float] = None,
        group: Optional[str] = None,
        id_field: str = "id",
    ) -> "QueryBuilder":
        """Configure coverage filtering across groups.
        
        Coverage determines which items appear in the final result based on
        how many groups they appear in after grouping and top_k filtering.
        
        Args:
            mode: Coverage mode:
                - "all": Keep items that appear in ALL groups
                - "any": Keep items that appear in AT LEAST ONE group
                - "at_least": Keep items that appear in at least k groups (requires k/threshold parameter)
                - "exact": Keep items that appear in exactly k groups (requires k/threshold parameter)
                - "fraction": Keep items that appear in at least p fraction (0-1) of groups (requires p parameter)
            k: Threshold for "at_least" or "exact" modes
            threshold: Alias for k parameter
            p: Fraction threshold (0.0-1.0) for "fraction" mode. E.g., p=0.67 means at least 67% of groups
            group: Group attribute for coverage (defaults to primary grouping context)
            id_field: Field to use for identity matching (default: "id" for nodes)
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If mode is invalid or required parameters are missing
            ValueError: If called without prior grouping
            
        Example:
            >>> # Nodes that are top-5 hubs in ALL layers
            >>> Q.nodes().per_layer().top_k(5, "betweenness").coverage(mode="all")
            
            >>> # Nodes that are top-5 in at least 2 layers
            >>> Q.nodes().per_layer().top_k(5, "degree").coverage(mode="at_least", k=2)
            >>> # Or equivalently:
            >>> Q.nodes().per_layer().top_k(5, "degree").coverage(mode="at_least", threshold=2)
            
            >>> # Nodes in top-10 in at least 70% of layers (0.7 fraction)
            >>> Q.nodes().per_layer().top_k(10, "degree").coverage(mode="fraction", p=0.7)
        """
        # Handle threshold as alias for k
        if threshold is not None and k is None:
            k = threshold
        elif threshold is not None and k is not None:
            raise ValueError("Cannot specify both k and threshold parameters")
        
        allowed_modes = {"all", "any", "at_least", "exact", "fraction"}
        if mode not in allowed_modes:
            raise ValueError(
                f"Unknown coverage mode: {mode}. "
                f"Allowed modes: {', '.join(sorted(allowed_modes))}"
            )
        
        if mode in {"at_least", "exact"} and k is None:
            raise ValueError(f"coverage(mode='{mode}') requires k or threshold parameter")
        
        if mode == "fraction" and p is None:
            raise ValueError(f"coverage(mode='fraction') requires p parameter")
        
        if p is not None and (p < 0 or p > 1):
            raise ValueError(f"coverage fraction p must be in range [0, 1], got {p}")
        
        # Validate that grouping is set up
        if not self._select.group_by:
            from .errors import GroupingError
            raise GroupingError(
                "coverage() requires an active grouping (e.g. per_layer(), group_by('layer')). "
                "No grouping is currently active.\n"
                "Example:\n"
                "    Q.nodes().from_layers(L[\"*\"])\n"
                "        .per_layer().top_k(5, \"degree\").end_grouping()\n"
                "        .coverage(mode=\"all\")"
            )
        
        self._select.coverage_mode = mode
        self._select.coverage_k = k
        self._select.coverage_p = p
        self._select.coverage_group = group
        self._select.coverage_id_field = id_field
        return self
    
    def per_community(self) -> "QueryBuilder":
        """Group results by community (sugar for group_by("community")).
        
        Similar to per_layer(), but groups by community attribute.
        Useful after community detection has been run and community
        assignments are stored in node attributes.
        
        Returns:
            Self for chaining
            
        Example:
            >>> # Find top nodes per community
            >>> Q.nodes().per_community().top_k(5, "betweenness_centrality")
        """
        return self.group_by("community")
    
    def select(self, *columns: str) -> "QueryBuilder":
        """Keep only specified columns in the result.
        
        This operation filters the output columns, keeping only the ones specified.
        Useful for reducing result size and focusing on specific attributes.
        
        Args:
            *columns: Column names to keep in the result
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree", "betweenness_centrality").select("id", "degree")
        """
        self._select.select_cols = list(columns)
        return self
    
    def drop(self, *columns: str) -> "QueryBuilder":
        """Remove specified columns from the result.
        
        This operation filters out the specified columns from the output.
        Complementary to select() - use drop() when it's easier to specify
        what to remove rather than what to keep.
        
        Args:
            *columns: Column names to remove from the result
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree", "betweenness", "closeness").drop("closeness")
        """
        self._select.drop_cols = list(columns)
        return self
    
    def rename(self, **mapping: str) -> "QueryBuilder":
        """Rename columns in the result.
        
        Provide keyword arguments where the key is the new name and the
        value is the old name to rename.
        
        Args:
            **mapping: Mapping from new names to old names (new=old)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree", "betweenness_centrality").rename(
            ...     deg="degree", bc="betweenness_centrality"
            ... )
        """
        if self._select.rename_map is None:
            self._select.rename_map = {}
        self._select.rename_map.update(mapping)
        return self
    
    def summarize(self, **aggregations: str) -> "QueryBuilder":
        """Aggregate over the current grouping context.
        
        Computes summary statistics per group when grouping is active,
        or globally if no grouping is set. Aggregation expressions are
        strings like "mean(degree)", "max(degree)", "n()".
        
        Supported aggregations:
            - n() : count of items
            - mean(attr) : mean value
            - sum(attr) : sum of values
            - min(attr) : minimum value
            - max(attr) : maximum value
            - std(attr) : standard deviation
            - var(attr) : variance
        
        Args:
            **aggregations: Named aggregations (name=expression)
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If aggregation expression is invalid
            
        Example:
            >>> Q.nodes().from_layers(L["*"]).compute("degree").per_layer().summarize(
            ...     mean_degree="mean(degree)",
            ...     max_degree="max(degree)",
            ...     n="n()"
            ... )
        """
        if self._select.summarize_aggs is None:
            self._select.summarize_aggs = {}
        self._select.summarize_aggs.update(aggregations)
        return self
    
    def arrange(self, *columns: str, desc: bool = False) -> "QueryBuilder":
        """Sort results by specified columns (dplyr-style alias for order_by).
        
        This is a convenience method that provides dplyr-style syntax.
        Columns can be prefixed with "-" to indicate descending order.
        
        Args:
            *columns: Column names to sort by (prefix with "-" for descending)
            desc: Default sort direction (only used if column has no prefix)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree").arrange("degree")  # ascending
            >>> Q.nodes().compute("degree").arrange("-degree")  # descending
            >>> Q.nodes().compute("degree", "betweenness").arrange("degree", "-betweenness")
        """
        return self.order_by(*columns, desc=desc)
    
    def distinct(self, *columns: str) -> "QueryBuilder":
        """Return unique rows based on specified columns.
        
        If columns are specified, deduplicates based on those columns only.
        If no columns are specified, deduplicates based on all columns.
        
        Args:
            *columns: Optional column names to use for uniqueness check
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Unique (node, layer) pairs
            >>> Q.nodes().distinct()
            
            >>> # Unique communities per layer
            >>> Q.nodes().distinct("community", "layer")
        """
        self._select.distinct_cols = list(columns) if columns else []
        return self
    
    def centrality(self, *metrics: str, **aliases: str) -> "QueryBuilder":
        """Compute centrality metrics (convenience wrapper for compute).
        
        This is a domain-specific convenience method for computing
        common centrality measures. It's equivalent to calling compute()
        with the metric names.
        
        Supported metrics:
            - degree
            - betweenness (or betweenness_centrality)
            - closeness (or closeness_centrality)
            - eigenvector (or eigenvector_centrality)
            - pagerank
            - clustering (or clustering_coefficient)
        
        Args:
            *metrics: Centrality metric names
            **aliases: Optional aliases for metrics (alias=metric_name)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().centrality("degree", "betweenness", "pagerank")
            >>> Q.nodes().centrality("degree", bc="betweenness_centrality")
        """
        # First add metrics without aliases
        for metric in metrics:
            self._select.compute.append(ComputeItem(name=metric))
        
        # Then add metrics with aliases
        for alias, metric in aliases.items():
            self._select.compute.append(ComputeItem(name=metric, alias=alias))
        
        return self
    
    def rank_by(self, attr: str, method: str = "dense") -> "QueryBuilder":
        """Add rank column based on specified attribute.
        
        Computes ranks within the current grouping context. If grouping
        is active, ranks are computed per group. Otherwise, ranks are global.
        
        The rank column will be named "{attr}_rank".
        
        Args:
            attr: Attribute to rank by
            method: Ranking method - "dense", "min", "max", "average", "first"
                   (follows pandas.Series.rank semantics)
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Global ranking
            >>> Q.nodes().compute("degree").rank_by("degree")
            
            >>> # Per-layer ranking
            >>> Q.nodes().compute("degree").per_layer().rank_by("degree", "dense")
        """
        if self._select.rank_specs is None:
            self._select.rank_specs = []
        self._select.rank_specs.append((attr, method))
        return self
    
    def zscore(self, *attrs: str) -> "QueryBuilder":
        """Compute z-scores for specified attributes.
        
        For each attribute, computes the z-score (standardized value)
        within the current grouping context. If grouping is active,
        z-scores are computed per group. Otherwise, they are global.
        
        Creates new columns named "{attr}_zscore".
        
        Args:
            *attrs: Attribute names to compute z-scores for
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Global z-scores
            >>> Q.nodes().compute("degree", "betweenness").zscore("degree", "betweenness")
            
            >>> # Per-layer z-scores
            >>> Q.nodes().compute("degree").per_layer().zscore("degree")
        """
        if self._select.zscore_attrs is None:
            self._select.zscore_attrs = []
        self._select.zscore_attrs.extend(attrs)
        return self
    
    def at(self, t: float) -> "QueryBuilder":
        """Add temporal snapshot constraint (AT clause).
        
        Filters edges to only those active at a specific point in time.
        For point-in-time edges (with 't' attribute), includes edges where t_edge == t.
        For interval edges (with 't_start', 't_end'), includes edges where t is in [t_start, t_end].
        
        Args:
            t: Timestamp for snapshot
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Snapshot at specific time
            >>> Q.edges().at(150.0).execute(network)
        """
        self._select.temporal_context = TemporalContext(
            kind="at",
            t0=float(t),
            t1=float(t)
        )
        return self
    
    def during(
        self,
        t0: Optional[float] = None,
        t1: Optional[float] = None
    ) -> "QueryBuilder":
        """Add temporal range constraint (DURING clause).
        
        Filters edges to only those active during a time range [t0, t1].
        For point-in-time edges, includes edges where t is in [t0, t1].
        For interval edges, includes edges where the interval overlaps [t0, t1].
        
        Args:
            t0: Start of time range (None means -infinity)
            t1: End of time range (None means +infinity)
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Time range query
            >>> Q.edges().during(100.0, 200.0).execute(network)
            
            >>> # Open-ended ranges
            >>> Q.edges().during(100.0, None).execute(network)  # From 100 onwards
            >>> Q.edges().during(None, 200.0).execute(network)  # Up to 200
        """
        self._select.temporal_context = TemporalContext(
            kind="during",
            t0=t0,
            t1=t1
        )
        return self
    
    def before(self, t: float) -> "QueryBuilder":
        """Add temporal constraint for edges/nodes before a specific time.
        
        Convenience method equivalent to `.during(None, t)`.
        Filters to only include edges/nodes active before (and at) time t.
        
        Args:
            t: Upper bound timestamp (inclusive)
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Get all edges before time 100
            >>> Q.edges().before(100.0).execute(network)
            
            >>> # Nodes active before 2024-01-01
            >>> Q.nodes().before(1704067200.0).execute(network)
        """
        self._select.temporal_context = TemporalContext(
            kind="during",
            t0=None,
            t1=float(t)
        )
        return self
    
    def after(self, t: float) -> "QueryBuilder":
        """Add temporal constraint for edges/nodes after a specific time.
        
        Convenience method equivalent to `.during(t, None)`.
        Filters to only include edges/nodes active after (and at) time t.
        
        Args:
            t: Lower bound timestamp (inclusive)
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Get all edges after time 100
            >>> Q.edges().after(100.0).execute(network)
            
            >>> # Nodes active after 2024-01-01
            >>> Q.nodes().after(1704067200.0).execute(network)
        """
        self._select.temporal_context = TemporalContext(
            kind="during",
            t0=float(t),
            t1=None
        )
        return self
    
    def window(
        self,
        window_size: Union[float, str],
        step: Optional[Union[float, str]] = None,
        start: Optional[float] = None,
        end: Optional[float] = None,
        aggregation: str = "list",
    ) -> "QueryBuilder":
        """Add sliding window specification for temporal analysis.
        
        Enables queries that operate over sliding time windows, useful for
        streaming algorithms and temporal pattern analysis.
        
        Args:
            window_size: Size of each window. Can be:
                        - Numeric: treated as timestamp units
                        - String: duration like "7d", "1h", "30m"
            step: Step size between windows (defaults to window_size for non-overlapping).
                 Same format as window_size.
            start: Optional start time for windowing (defaults to network's first timestamp)
            end: Optional end time for windowing (defaults to network's last timestamp)
            aggregation: How to aggregate results across windows:
                        - "list": Return list of per-window results
                        - "concat": Concatenate DataFrames
                        - "avg": Average numeric columns
                        
        Returns:
            Self for chaining
            
        Examples:
            >>> # Non-overlapping windows of size 100
            >>> Q.nodes().compute("degree").window(100.0).execute(tnet)
            
            >>> # Overlapping windows: size 100, step 50
            >>> Q.nodes().compute("degree").window(100.0, step=50.0).execute(tnet)
            
            >>> # Duration strings (for datetime timestamps)
            >>> Q.edges().window("7d", step="1d").execute(tnet)
            
        Note:
            Window queries require a TemporalMultiLayerNetwork instance.
            For regular multi_layer_network, an error will be raised.
        """
        self._select.window_spec = WindowSpec(
            window_size=window_size,
            step=step,
            start=start,
            end=end,
            aggregation=aggregation,
        )
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
    
    def export(
        self,
        path: str,
        fmt: str = "csv",
        columns: Optional[List[str]] = None,
        **options,
    ) -> "QueryBuilder":
        """Attach a file export specification to the query.
        
        This adds a side-effect to write query results to a file when executed.
        The query will still return the QueryResult as normal.
        
        Args:
            path: Output file path (string)
            fmt: Format type ('csv', 'json', 'tsv')
            columns: Optional list of column names to include/order
            **options: Format-specific options (e.g., delimiter=';', orient='records')
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If format is not supported
            
        Example:
            >>> q = (
            ...     Q.nodes()
            ...      .compute("degree")
            ...      .export("results.csv", fmt="csv", columns=["node", "degree"])
            ... )
        """
        # Validate format early
        supported_formats = {"csv", "json", "tsv"}
        fmt_lower = fmt.lower()
        if fmt_lower not in supported_formats:
            raise ValueError(
                f"Unsupported export format: '{fmt}'. "
                f"Supported formats: {', '.join(sorted(supported_formats))}"
            )
        
        self._select.file_export = ExportSpec(
            path=path,
            fmt=fmt_lower,
            columns=columns,
            options=options,
        )
        return self
    
    def export_csv(
        self,
        path: str,
        columns: Optional[List[str]] = None,
        delimiter: str = ",",
        **options,
    ) -> "QueryBuilder":
        """Export query results to CSV file.
        
        Convenience wrapper around .export() for CSV format.
        
        Args:
            path: Output CSV file path
            columns: Optional list of columns to include/order
            delimiter: CSV delimiter (default: ',')
            **options: Additional CSV-specific options
            
        Returns:
            Self for chaining
        """
        options["delimiter"] = delimiter
        return self.export(path, fmt="csv", columns=columns, **options)
    
    def export_json(
        self,
        path: str,
        columns: Optional[List[str]] = None,
        orient: str = "records",
        **options,
    ) -> "QueryBuilder":
        """Export query results to JSON file.
        
        Convenience wrapper around .export() for JSON format.
        
        Args:
            path: Output JSON file path
            columns: Optional list of columns to include/order
            orient: JSON orientation ('records', 'split', 'index', 'columns', 'values')
            **options: Additional JSON-specific options
            
        Returns:
            Self for chaining
        """
        options["orient"] = orient
        return self.export(path, fmt="json", columns=columns, **options)
    
    def node_type(self, node_type: str) -> "QueryBuilder":
        """Filter nodes by node_type attribute.
        
        This is a convenience method that adds a WHERE condition filtering
        by the "node_type" attribute. Equivalent to .where(node_type=node_type).
        
        Args:
            node_type: Node type to filter by (e.g., "gene", "protein", "drug")
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().node_type("gene").compute("degree")
        """
        return self.where(node_type=node_type)
    
    def has_community(self, predicate) -> "QueryBuilder":
        """Filter nodes based on a community-related predicate.
        
        This method filters nodes based on their community membership or
        community-related attributes. The predicate can be:
        - A callable: Called with each node tuple, should return bool
        - A value: Direct equality check against "community" attribute
        
        Args:
            predicate: Either a callable(node_tuple) -> bool or a value to match
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Filter by community ID
            >>> Q.nodes().has_community(3)
            
            >>> # Filter by custom predicate
            >>> Q.nodes().has_community(
            ...     lambda n: network.get_node_attribute(n, "disease_enriched") is True
            ... )
        """
        # Store the predicate for later execution
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "community_predicate",
            "predicate": predicate,
        })
        return self
    
    def aggregate(self, **aggregations) -> "QueryBuilder":
        """Aggregate columns with support for lambdas and builtin functions.
        
        This method computes aggregations over the result set. It supports:
        - Built-in aggregation functions: mean(), sum(), min(), max(), std(), count()
        - Direct attribute references for last/first value
        - Lambda functions for custom aggregations
        
        The aggregations are computed after grouping if active, otherwise globally.
        
        Args:
            **aggregations: Named aggregations where:
                - Key is the output column name
                - Value is either:
                    * A string like "mean(degree)" or "sum(weight)"
                    * A string attribute name (gets the value directly)
                    * A lambda function receiving each item
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().per_layer().aggregate(
            ...     avg_degree="mean(degree)",
            ...     max_bc="max(betweenness_centrality)",
            ...     node_count="count()",
            ...     layer_name="layer"  # Direct attribute
            ... )
            
            >>> # With lambda
            >>> Q.nodes().aggregate(
            ...     community_size=lambda n: network.community_sizes[network.get_partition(n)]
            ... )
        """
        if self._select.aggregate_specs is None:
            self._select.aggregate_specs = {}
        
        self._select.aggregate_specs.update(aggregations)
        return self
    
    def mutate(self, **transformations) -> "QueryBuilder":
        """Add or transform columns using expressions or lambda functions.
        
        This method creates new columns or modifies existing ones by applying
        transformations to each row. It corresponds to dplyr::mutate and is
        applied row-by-row (not aggregated like summarize/aggregate).
        
        Transformations can be:
        - String expressions referencing existing attributes
        - Lambda functions that receive a dict with item attributes
        - Simple values (applied to all rows)
        
        Args:
            **transformations: Named transformations where:
                - Key is the output column name
                - Value is either:
                    * A lambda function receiving dict of item attributes
                    * A string expression (e.g., "degree * 2")
                    * A simple value (applied to all rows)
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Create new columns from existing attributes
            >>> Q.nodes().compute("degree", "clustering").mutate(
            ...     normalized_degree=lambda row: row.get("degree", 0) / 10.0,
            ...     log_degree=lambda row: np.log1p(row.get("degree", 0)),
            ...     score=lambda row: row.get("degree", 0) * row.get("clustering", 0)
            ... )
            
            >>> # Simple transformations
            >>> Q.nodes().mutate(
            ...     category="hub",  # Constant value
            ...     doubled_degree=lambda row: row.get("degree", 0) * 2
            ... )
        """
        if self._select.mutate_specs is None:
            self._select.mutate_specs = {}
        
        self._select.mutate_specs.update(transformations)
        return self
    
    def sort(self, by: str, descending: bool = False) -> "QueryBuilder":
        """Sort results by a column (convenience alias for order_by).
        
        This provides a more intuitive API matching common data analysis
        patterns (e.g., pandas DataFrame.sort_values).
        
        Args:
            by: Column name to sort by
            descending: If True, sort in descending order (default: False)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree").sort(by="degree", descending=True)
        """
        if descending:
            return self.order_by(f"-{by}")
        else:
            return self.order_by(by)
    
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
        >>> Q.nodes(autocompute=False).where(degree__gt=5)  # Disable autocompute
        >>> Q.dynamics("SIS", beta=0.3).run(steps=100)  # Dynamics simulation
        >>> Q.trajectories("sim_result").at(50)  # Query trajectories
    """
    
    @staticmethod
    def nodes(autocompute: bool = True) -> QueryBuilder:
        """Create a query builder for nodes.
        
        Args:
            autocompute: Whether to automatically compute missing metrics (default: True)
            
        Returns:
            QueryBuilder for nodes
        """
        return QueryBuilder(Target.NODES, autocompute=autocompute)
    
    @staticmethod
    def edges(autocompute: bool = True) -> QueryBuilder:
        """Create a query builder for edges.
        
        Args:
            autocompute: Whether to automatically compute missing metrics (default: True)
            
        Returns:
            QueryBuilder for edges
        """
        return QueryBuilder(Target.EDGES, autocompute=autocompute)
    
    @staticmethod
    def dynamics(process_name: str, **params) -> "DynamicsBuilder":
        """Create a dynamics simulation builder.
        
        Args:
            process_name: Name of the process (e.g., "SIS", "SIR", "RANDOM_WALK")
            **params: Process parameters (e.g., beta=0.3, mu=0.1)
            
        Returns:
            DynamicsBuilder for configuring and running simulations
            
        Example:
            >>> sim = (
            ...     Q.dynamics("SIS", beta=0.3, mu=0.1)
            ...      .on_layers(L["contacts"])
            ...      .seed(0.01)
            ...      .run(steps=100, replicates=10, track="all")
            ...      .execute(network)
            ... )
        """
        return DynamicsBuilder(process_name, **params)
    
    @staticmethod
    def trajectories(process_ref: str) -> "TrajectoriesBuilder":
        """Create a trajectories query builder.
        
        Args:
            process_ref: Reference to a simulation result or process name
            
        Returns:
            TrajectoriesBuilder for querying simulation outputs
            
        Example:
            >>> result = (
            ...     Q.trajectories("sim_result")
            ...      .at(50)
            ...      .measure("peak_time", "final_state")
            ...      .execute(context)
            ... )
        """
        return TrajectoriesBuilder(process_ref)
    
    @staticmethod
    def pattern() -> "PatternQueryBuilder":
        """Create a pattern matching query builder.
        
        Returns:
            PatternQueryBuilder for constructing pattern queries
            
        Example:
            >>> pq = (
            ...     Q.pattern()
            ...      .node("a").where(layer="social", degree__gt=3)
            ...      .node("b").where(layer="social")
            ...      .edge("a", "b", directed=False).where(weight__gt=0.2)
            ...      .returning("a", "b")
            ... )
            >>> matches = pq.execute(network)
            >>> df = matches.to_pandas()
        """
        from .patterns.builder import PatternQueryBuilder
        return PatternQueryBuilder()
    
    # Nested class for uncertainty defaults
    class uncertainty:
        """Global defaults for uncertainty estimation.
        
        This class provides a way to configure default parameters for
        uncertainty estimation that will be used when uncertainty=True
        is passed to compute() but specific parameters are omitted.
        
        Example:
            >>> from py3plex.dsl import Q
            >>> 
            >>> # Set global defaults
            >>> Q.uncertainty.defaults(
            ...     enabled=True,
            ...     n_boot=200,
            ...     ci=0.95,
            ...     bootstrap_unit="edges",
            ...     bootstrap_mode="resample",
            ...     random_state=42
            ... )
            >>> 
            >>> # Now compute() will use these defaults
            >>> Q.nodes().compute("degree", uncertainty=True).execute(net)
            
            >>> # Reset to defaults
            >>> Q.uncertainty.reset()
        """
        
        _defaults: Dict[str, Any] = {
            "enabled": False,
            "n_boot": 50,
            "n_samples": 50,
            "ci": 0.95,
            "bootstrap_unit": "edges",
            "bootstrap_mode": "resample",
            "method": "bootstrap",
            "random_state": None,
            "n_null": 200,
            "null_model": "degree_preserving",
        }
        
        @classmethod
        def defaults(cls, **kwargs) -> None:
            """Set global defaults for uncertainty estimation.
            
            Args:
                enabled: Whether uncertainty is enabled by default (default: False)
                n_boot: Number of bootstrap replicates (default: 50)
                n_samples: Alias for n_boot (default: 50)
                ci: Confidence interval level (default: 0.95)
                bootstrap_unit: What to resample - "edges", "nodes", or "layers" (default: "edges")
                bootstrap_mode: Resampling mode - "resample" or "permute" (default: "resample")
                method: Uncertainty estimation method - "bootstrap", "perturbation", "seed" (default: "bootstrap")
                random_state: Random seed for reproducibility (default: None)
                n_null: Number of null model replicates (default: 200)
                null_model: Null model type - "degree_preserving", "erdos_renyi", "configuration" (default: "degree_preserving")
            
            Example:
                >>> Q.uncertainty.defaults(
                ...     enabled=True,
                ...     n_boot=500,
                ...     ci=0.95,
                ...     bootstrap_unit="edges"
                ... )
            """
            for key, value in kwargs.items():
                if key not in cls._defaults:
                    raise ValueError(
                        f"Unknown uncertainty parameter: {key}. "
                        f"Valid parameters: {list(cls._defaults.keys())}"
                    )
                cls._defaults[key] = value
            cls._sync_context()
        
        @classmethod
        def reset(cls) -> None:
            """Reset all defaults to their initial values."""
            cls._defaults = {
                "enabled": False,
                "n_boot": 50,
                "n_samples": 50,
                "ci": 0.95,
                "bootstrap_unit": "edges",
                "bootstrap_mode": "resample",
                "method": "bootstrap",
                "random_state": None,
                "n_null": 200,
                "null_model": "degree_preserving",
            }
            cls._sync_context()
        
        @classmethod
        def get(cls, key: str, default: Any = None) -> Any:
            """Get a default value.
            
            Args:
                key: Parameter name
                default: Value to return if key not found
                
            Returns:
                Default value for the parameter
            """
            return cls._defaults.get(key, default)
        
        @classmethod
        def get_all(cls) -> Dict[str, Any]:
            """Get all current defaults as a dictionary.
            
            Returns:
                Dictionary of all default values
            """
            return cls._defaults.copy()

        @classmethod
        def _sync_context(cls) -> None:
            """Push defaults into the shared uncertainty context."""
            try:
                cfg = get_uncertainty_config()
                n_runs = cls._defaults.get("n_samples") or cls._defaults.get("n_boot") or cfg.default_n_runs
                resampling = _METHOD_TO_RESAMPLING.get(cls._defaults.get("method"), cfg.default_resampling)
                set_uncertainty_config(
                    UncertaintyConfig(
                        mode=UncertaintyMode.ON if cls._defaults.get("enabled") else UncertaintyMode.OFF,
                        default_n_runs=int(n_runs),
                        default_resampling=resampling,
                    )
                )
            except Exception:
                # Keep DSL usable even if uncertainty package is partially available
                logging.getLogger(__name__).debug("Failed to sync uncertainty context", exc_info=True)


# ==============================================================================
# UQ Profiles for One-Liner Ergonomics
# ==============================================================================


class UQ:
    """Uncertainty quantification profiles for ergonomic one-liners.
    
    This class provides convenient presets for common uncertainty estimation
    scenarios. Each profile returns a UQConfig that can be passed to .uq().
    
    Example:
        >>> from py3plex.dsl import Q, UQ
        >>> 
        >>> # Fast exploratory analysis
        >>> Q.nodes().uq(UQ.fast(seed=42)).compute("degree").execute(net)
        >>> 
        >>> # Default balanced settings
        >>> Q.nodes().uq(UQ.default()).compute("betweenness_centrality").execute(net)
        >>> 
        >>> # Publication-quality with more samples
        >>> Q.nodes().uq(UQ.paper(seed=123)).compute("closeness").execute(net)
    """
    
    @staticmethod
    def fast(seed: Optional[int] = None) -> UQConfig:
        """Fast exploratory profile with minimal samples.
        
        Settings: perturbation, n=25, ci=0.95
        
        Use this for quick exploratory analysis when speed matters more
        than precision.
        
        Args:
            seed: Random seed for reproducibility (default: None)
            
        Returns:
            UQConfig with fast settings
            
        Example:
            >>> Q.nodes().uq(UQ.fast(seed=0)).compute("degree").execute(net)
        """
        return UQConfig(method="perturbation", n_samples=25, ci=0.95, seed=seed)
    
    @staticmethod
    def default(seed: Optional[int] = None) -> UQConfig:
        """Default balanced profile.
        
        Settings: perturbation, n=50, ci=0.95
        
        Use this for general-purpose uncertainty estimation with reasonable
        computational cost.
        
        Args:
            seed: Random seed for reproducibility (default: None)
            
        Returns:
            UQConfig with default settings
            
        Example:
            >>> Q.nodes().uq(UQ.default()).compute("betweenness_centrality").execute(net)
        """
        return UQConfig(method="perturbation", n_samples=50, ci=0.95, seed=seed)
    
    @staticmethod
    def paper(seed: Optional[int] = None) -> UQConfig:
        """Publication-quality profile with thorough sampling.
        
        Settings: bootstrap, n=300, ci=0.95
        
        Use this for publication-quality results where precision is critical
        and computational cost is acceptable.
        
        Args:
            seed: Random seed for reproducibility (default: None)
            
        Returns:
            UQConfig with publication-quality settings
            
        Example:
            >>> Q.nodes().uq(UQ.paper(seed=123)).compute("closeness").execute(net)
        """
        return UQConfig(method="bootstrap", n_samples=300, ci=0.95, seed=seed)


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


# ==============================================================================
# Dynamics Builder (Part D: Dynamics Integration)
# ==============================================================================


class DynamicsBuilder:
    """Builder for DYNAMICS statements.
    
    Example:
        >>> from py3plex.dsl import Q, L
        >>> 
        >>> result = (
        ...     Q.dynamics("SIS", beta=0.3, mu=0.1)
        ...      .on_layers(L["contacts"] + L["travel"])
        ...      .seed(Q.nodes().where(degree__gt=10))
        ...      .parameters_per_layer({
        ...          "contacts": {"beta": 0.4},
        ...          "travel": {"beta": 0.2}
        ...      })
        ...      .run(steps=100, replicates=10)
        ...      .execute(network)
        ... )
    """
    
    def __init__(self, process_name: str, **params):
        """Initialize builder with process name and parameters."""
        from .ast import DynamicsStmt
        self._stmt = DynamicsStmt(
            process_name=process_name,
            params=params,
        )
    
    def on_layers(self, layer_expr: LayerExprBuilder) -> "DynamicsBuilder":
        """Filter by layers using layer algebra.
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])
            
        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self
    
    def seed(self, query_or_fraction: Union[float, "QueryBuilder"]) -> "DynamicsBuilder":
        """Set initial seeding for the dynamics.
        
        Args:
            query_or_fraction: Either a fraction (e.g., 0.01 for 1%) or a QueryBuilder
                              for selecting specific nodes to seed
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Seed 1% randomly
            >>> builder.seed(0.01)
            
            >>> # Seed high-degree nodes
            >>> builder.seed(Q.nodes().where(degree__gt=10))
        """
        if isinstance(query_or_fraction, float):
            self._stmt.seed_fraction = query_or_fraction
        elif hasattr(query_or_fraction, '_select'):
            # It's a QueryBuilder
            self._stmt.seed_query = query_or_fraction._select
        else:
            raise TypeError("seed() requires a float fraction or QueryBuilder")
        return self
    
    def with_states(self, **state_mapping) -> "DynamicsBuilder":
        """Explicitly define state labels (optional).
        
        Args:
            **state_mapping: State labels (e.g., S="susceptible", I="infected")
            
        Returns:
            Self for chaining
            
        Note:
            This is optional metadata and doesn't affect execution, but helps
            with documentation and trajectory queries.
        """
        # Store in params for now (could be separate field in future)
        if "state_labels" not in self._stmt.params:
            self._stmt.params["state_labels"] = {}
        self._stmt.params["state_labels"].update(state_mapping)
        return self
    
    def parameters_per_layer(self, layer_params: Dict[str, Dict[str, Any]]) -> "DynamicsBuilder":
        """Set per-layer parameter overrides.
        
        Args:
            layer_params: Dictionary mapping layer names to parameter dictionaries
            
        Returns:
            Self for chaining
            
        Example:
            >>> builder.parameters_per_layer({
            ...     "contacts": {"beta": 0.3},
            ...     "travel": {"beta": 0.1}
            ... })
        """
        self._stmt.layer_params = layer_params
        return self
    
    def run(
        self,
        steps: int = 100,
        replicates: int = 1,
        track: Optional[Union[str, List[str]]] = None
    ) -> "DynamicsBuilder":
        """Set execution parameters.
        
        Args:
            steps: Number of time steps to simulate
            replicates: Number of independent runs
            track: Measures to track ("all" or list of specific measures)
            
        Returns:
            Self for chaining
        """
        self._stmt.steps = steps
        self._stmt.replicates = replicates
        
        if track is not None:
            if isinstance(track, str):
                if track == "all":
                    # Will be expanded by executor based on process type
                    self._stmt.track = ["all"]
                else:
                    self._stmt.track = [track]
            else:
                self._stmt.track = list(track)
        
        return self
    
    def random_seed(self, seed: int) -> "DynamicsBuilder":
        """Set random seed for reproducibility.
        
        Args:
            seed: Random seed
            
        Returns:
            Self for chaining
        """
        self._stmt.seed = seed
        return self
    
    def to(self, target: str) -> "DynamicsBuilder":
        """Set export target.
        
        Args:
            target: Export format
            
        Returns:
            Self for chaining
        """
        self._stmt.export_target = target
        return self
    
    def execute(self, network: Any) -> Any:
        """Execute dynamics simulation.
        
        Args:
            network: Multilayer network
            
        Returns:
            DynamicsResult with simulation outputs
        """
        from py3plex.dsl.executor import execute_dynamics_stmt
        return execute_dynamics_stmt(network, self._stmt)
    
    def to_ast(self) -> "DynamicsStmt":
        """Export as AST DynamicsStmt object."""
        return self._stmt
    
    def __repr__(self) -> str:
        return f"DynamicsBuilder({self._stmt.process_name}, steps={self._stmt.steps})"


class TrajectoriesBuilder:
    """Builder for TRAJECTORIES statements.
    
    Example:
        >>> from py3plex.dsl import Q
        >>> 
        >>> result = (
        ...     Q.trajectories("sim_result")
        ...      .where(replicate=5)
        ...      .at(50)
        ...      .measure("peak_time", "final_state")
        ...      .order_by("node_id")
        ...      .limit(100)
        ...      .execute()
        ... )
    """
    
    def __init__(self, process_ref: str):
        """Initialize builder with process reference."""
        from .ast import TrajectoriesStmt
        self._stmt = TrajectoriesStmt(process_ref=process_ref)
    
    def where(self, **kwargs) -> "TrajectoriesBuilder":
        """Add WHERE conditions on trajectories.
        
        Args:
            **kwargs: Conditions (e.g., replicate=5, node="Alice")
            
        Returns:
            Self for chaining
        """
        self._stmt.where = build_condition_from_kwargs(kwargs)
        return self
    
    def at(self, t: float) -> "TrajectoriesBuilder":
        """Filter to specific time point.
        
        Args:
            t: Timestamp
            
        Returns:
            Self for chaining
        """
        self._stmt.temporal_context = TemporalContext(
            kind="at",
            t0=float(t),
            t1=float(t)
        )
        return self
    
    def during(self, t0: float, t1: float) -> "TrajectoriesBuilder":
        """Filter to time range.
        
        Args:
            t0: Start time
            t1: End time
            
        Returns:
            Self for chaining
        """
        self._stmt.temporal_context = TemporalContext(
            kind="during",
            t0=float(t0),
            t1=float(t1)
        )
        return self
    
    def measure(self, *measures: str) -> "TrajectoriesBuilder":
        """Add trajectory measures to compute.
        
        Args:
            *measures: Measure names
            
        Returns:
            Self for chaining
        """
        self._stmt.measures.extend(measures)
        return self
    
    def order_by(self, key: str, desc: bool = False) -> "TrajectoriesBuilder":
        """Add ordering specification.
        
        Args:
            key: Attribute to order by
            desc: If True, descending order
            
        Returns:
            Self for chaining
        """
        from .ast import OrderItem
        self._stmt.order_by.append(OrderItem(key=key, desc=desc))
        return self
    
    def limit(self, n: int) -> "TrajectoriesBuilder":
        """Limit number of results.
        
        Args:
            n: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self._stmt.limit = n
        return self
    
    def to(self, target: str) -> "TrajectoriesBuilder":
        """Set export target.
        
        Args:
            target: Export format
            
        Returns:
            Self for chaining
        """
        self._stmt.export_target = target
        return self
    
    def execute(self, context: Optional[Any] = None) -> Any:
        """Execute trajectory query.
        
        Args:
            context: Optional context containing simulation results
            
        Returns:
            QueryResult with trajectory data
        """
        from py3plex.dsl.executor import execute_trajectories_stmt
        return execute_trajectories_stmt(self._stmt, context)
    
    def to_ast(self) -> "TrajectoriesStmt":
        """Export as AST TrajectoriesStmt object."""
        return self._stmt
    
    def __repr__(self) -> str:
        return f"TrajectoriesBuilder({self._stmt.process_ref})"
