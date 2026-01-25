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
import pandas as pd
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Tuple
import numpy as np

if TYPE_CHECKING:
    from .layers import LayerSet
    from py3plex.counterfactual.spec import InterventionSpec
    from py3plex.counterfactual.result import CounterfactualResult, RobustnessReport

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
    ApproximationSpec,
    OrderItem,
    ParamRef,
    ExecutionPlan,
    TemporalContext,
    WindowSpec,
    UQConfig,
    CounterfactualSpec,
    SensitivitySpec,
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
    ResamplingStrategy.STRATIFIED_PERTURBATION: "stratified_perturbation",
    # Jackknife currently maps to seed-style multi-run execution until dedicated support lands
    ResamplingStrategy.JACKKNIFE: "seed",
}
_METHOD_TO_RESAMPLING = {v: k for k, v in _RESAMPLING_TO_METHOD.items()}


# Default approximation methods for each measure
_DEFAULT_APPROX_METHODS = {
    "betweenness_centrality": "sampling",
    "betweenness": "sampling",
    "closeness_centrality": "landmarks",
    "closeness": "landmarks",
    "pagerank": "power_iteration",
}


def _get_default_approx_method(measure_name: str) -> str:
    """Get default approximation method for a measure.
    
    Args:
        measure_name: Measure name
        
    Returns:
        Default approximation method name
        
    Raises:
        ValueError: If measure doesn't have a default approximation method
    """
    method = _DEFAULT_APPROX_METHODS.get(measure_name)
    if method is None:
        raise ValueError(
            f"No default approximation method for measure '{measure_name}'. "
            f"Supported measures: {', '.join(_DEFAULT_APPROX_METHODS.keys())}. "
            f"Either specify approx_method explicitly or use a supported measure."
        )
    return method


def _validate_approx_params(measure_name: str, approx_method: str, params: Dict[str, Any]) -> None:
    """Validate approximation parameters for a method.
    
    Args:
        measure_name: Measure name
        approx_method: Approximation method
        params: Method parameters to validate
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Check method is supported for this measure
    if approx_method not in ["sampling", "landmarks", "power_iteration"]:
        raise ValueError(
            f"Unknown approximation method '{approx_method}'. "
            f"Supported: sampling, landmarks, power_iteration"
        )
    
    # Validate parameter ranges
    if "n_samples" in params:
        if not isinstance(params["n_samples"], int) or params["n_samples"] <= 0:
            raise ValueError(f"n_samples must be a positive integer, got {params['n_samples']}")
    
    if "sample_fraction" in params:
        frac = params["sample_fraction"]
        if not isinstance(frac, (int, float)) or not (0 < frac <= 1):
            raise ValueError(f"sample_fraction must be in (0, 1], got {frac}")
    
    if "n_landmarks" in params:
        if not isinstance(params["n_landmarks"], int) or params["n_landmarks"] <= 0:
            raise ValueError(f"n_landmarks must be a positive integer, got {params['n_landmarks']}")
    
    if "tol" in params:
        if not isinstance(params["tol"], (int, float)) or params["tol"] <= 0:
            raise ValueError(f"tol must be positive, got {params['tol']}")
    
    if "max_iter" in params:
        if not isinstance(params["max_iter"], int) or params["max_iter"] <= 0:
            raise ValueError(f"max_iter must be a positive integer, got {params['max_iter']}")
    
    # Check for irrelevant params (warn or error)
    # For now, we'll be lenient and just ignore them, but could add warnings
    relevant_params = {
        "sampling": {"n_samples", "seed", "normalized", "weight"},
        "landmarks": {"n_landmarks", "seed", "weight"},
        "power_iteration": {"tol", "max_iter", "alpha", "personalization"},
    }
    
    if approx_method in relevant_params:
        for param in params:
            if param not in relevant_params[approx_method]:
                # For now, just silently ignore (could add warning later)
                pass


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
        - layer="social" -> Comparison("layer", "=", "social")
        - degree__gt=5 -> Comparison("degree", ">", 5)
        - intralayer=True -> SpecialPredicate("intralayer", {})
        - interlayer=("social","work") -> SpecialPredicate("interlayer", {...})
        - t__between=(100, 200) -> SpecialPredicate("temporal_range", {...})
        - t__gte=100 -> Comparison("t", ">=", 100)

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
                    atoms.append(
                        ConditionAtom(
                            special=SpecialPredicate(
                                kind="temporal_range",
                                params={"t_start": value[0], "t_end": value[1]},
                            )
                        )
                    )
                else:
                    raise ValueError("t__between requires a tuple of (t_start, t_end)")
            elif suffix in COMPARATOR_MAP:
                cmp = Comparison(
                    left=attr, op=COMPARATOR_MAP[suffix], right=_wrap_value(value)
                )
                atoms.append(ConditionAtom(comparison=cmp))
            else:
                raise ValueError(f"Unknown comparison suffix: {suffix}")

        elif key == "intralayer":
            if value:
                atoms.append(
                    ConditionAtom(
                        special=SpecialPredicate(kind="intralayer", params={})
                    )
                )

        elif key == "interlayer":
            if value is True:
                # interlayer=True means any inter-layer edge
                atoms.append(
                    ConditionAtom(
                        special=SpecialPredicate(
                            kind="interlayer", params={}
                        )
                    )
                )
            elif isinstance(value, tuple) and len(value) == 2:
                src, dst = value
                atoms.append(
                    ConditionAtom(
                        special=SpecialPredicate(
                            kind="interlayer", params={"src": src, "dst": dst}
                        )
                    )
                )
            else:
                raise ValueError(
                    "interlayer requires True or a tuple of (src_layer, dst_layer)"
                )

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
        - L["social"] -> single layer (backward compatible)
        - L["social", "work"] -> union of layers (backward compatible)
        - L["* - coupling"] -> string expression with algebra (NEW)
        - L["(ppi | gene) & disease"] -> complex expression (NEW)

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

    def from_layers(
        self, layer_expr: Union[LayerExprBuilder, "LayerSet"]
    ) -> "QueryBuilder":
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
            if hasattr(self._select, "layer_set"):
                self._select.layer_set = None

        return self

    def where(self, *args, **kwargs) -> "QueryBuilder":
        """Add WHERE conditions.

        Supports two styles:

        1. Keyword arguments:
            - layer="social" -> equality
            - degree__gt=5 -> comparison (gt, ge, lt, le, eq, ne)
            - intralayer=True -> intralayer predicate
            - interlayer=("social","work") -> interlayer predicate

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

    def compute(
        self,
        *measures: str,
        alias: Optional[str] = None,
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
        random_state: Optional[int] = None,
        approx: Optional[bool] = None,
        approx_method: Optional[str] = None,
        approx_diagnostics: bool = False,
        # Approximation-specific parameters (collected via **kwargs)
        **kwargs
    ) -> "QueryBuilder":
        """Add measures to compute with optional uncertainty estimation and/or approximation.

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
            approx: Whether to use fast approximate computation (default: False)
            approx_method: Approximation method name ("sampling", "landmarks", "power_iteration")
                If approx=True and approx_method=None, defaults are:
                - betweenness_centrality -> "sampling"
                - closeness_centrality -> "landmarks"
                - pagerank -> "power_iteration"
            approx_diagnostics: Whether to compute per-node diagnostic info (e.g., stderr)
            **kwargs: Additional approximation parameters (e.g., n_samples, n_landmarks, tol, max_iter, seed)

        Returns:
            Self for chaining

        Example:
            >>> # Without uncertainty or approximation
            >>> Q.nodes().compute("degree", "betweenness_centrality")

            >>> # With uncertainty using explicit parameters
            >>> Q.nodes().compute(
            ...     "degree", "betweenness_centrality",
            ...     uncertainty=True,
            ...     method="bootstrap",
            ...     n_samples=500,
            ...     ci=0.95
            ... )

            >>> # With approximation
            >>> Q.nodes().compute(
            ...     "betweenness_centrality",
            ...     approx=True,
            ...     approx_method="sampling",
            ...     n_samples=512,
            ...     seed=42
            ... )

            >>> # With both UQ and approximation
            >>> Q.nodes().compute(
            ...     "betweenness_centrality",
            ...     approx=True,
            ...     n_samples=256,
            ...     seed=42
            ... ).uq(method="bootstrap", n_samples=50, seed=42).execute(net)
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
                uncertainty_flag = bool(
                    Q.uncertainty.get("enabled", False)
                    or cfg.mode == UncertaintyMode.ON
                )
        else:
            uncertainty_flag = bool(uncertainty)

        # Get defaults from query-level uq_config, Q.uncertainty, or context
        # Priority: explicit params > query uq_config > Q.uncertainty > global context
        if uncertainty_flag:
            # Apply defaults for unspecified parameters
            if method is None:
                # Check query-level config first
                if (
                    self._select.uq_config is not None
                    and self._select.uq_config.method is not None
                ):
                    method = self._select.uq_config.method
                else:
                    method = Q.uncertainty.get("method")
                if method is None:
                    method = _RESAMPLING_TO_METHOD.get(cfg.default_resampling)
                if method is None:
                    method = "bootstrap"

            if n_samples is None and n_boot is None:
                # Check query-level config first
                if (
                    self._select.uq_config is not None
                    and self._select.uq_config.n_samples is not None
                ):
                    n_samples = self._select.uq_config.n_samples
                else:
                    n_samples = Q.uncertainty.get("n_boot", cfg.default_n_runs)
            # n_boot takes precedence over n_samples for clarity
            if n_boot is not None:
                n_samples = n_boot
            if ci is None:
                # Check query-level config first
                if (
                    self._select.uq_config is not None
                    and self._select.uq_config.ci is not None
                ):
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
                if (
                    self._select.uq_config is not None
                    and self._select.uq_config.seed is not None
                ):
                    random_state = self._select.uq_config.seed
                else:
                    random_state = Q.uncertainty.get("random_state")

        # Handle approximation parameters
        approx_spec = None
        if approx:
            # Extract approximation-specific params from kwargs
            approx_params = {}
            
            # Collect known approximation parameters
            for param_name in ["n_samples", "n_landmarks", "tol", "max_iter", "alpha", 
                               "seed", "normalized", "weight", "personalization", "sample_fraction"]:
                if param_name in kwargs:
                    approx_params[param_name] = kwargs[param_name]
            
            # Determine approximation method for each measure
            # We'll validate and create ApproximationSpec per measure in the loop below
            pass
        
        items: List[ComputeItem] = []

        if aliases:
            for name, al in aliases.items():
                # Build approximation spec for this measure
                measure_approx_spec = None
                if approx:
                    method_for_measure = approx_method or _get_default_approx_method(name)
                    _validate_approx_params(name, method_for_measure, approx_params)
                    measure_approx_spec = ApproximationSpec(
                        enabled=True,
                        method=method_for_measure,
                        params=dict(approx_params),  # Copy to avoid mutation
                        diagnostics=approx_diagnostics
                    )
                
                items.append(
                    ComputeItem(
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
                        approx=measure_approx_spec,
                    )
                )
        elif alias and len(measures) == 1:
            # Build approximation spec for this measure
            measure_approx_spec = None
            if approx:
                method_for_measure = approx_method or _get_default_approx_method(measures[0])
                _validate_approx_params(measures[0], method_for_measure, approx_params)
                measure_approx_spec = ApproximationSpec(
                    enabled=True,
                    method=method_for_measure,
                    params=dict(approx_params),
                    diagnostics=approx_diagnostics
                )
            
            items.append(
                ComputeItem(
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
                    approx=measure_approx_spec,
                )
            )
        else:
            for m in measures:
                # Build approximation spec for this measure
                measure_approx_spec = None
                if approx:
                    method_for_measure = approx_method or _get_default_approx_method(m)
                    _validate_approx_params(m, method_for_measure, approx_params)
                    measure_approx_spec = ApproximationSpec(
                        enabled=True,
                        method=method_for_measure,
                        params=dict(approx_params),
                        diagnostics=approx_diagnostics
                    )
                
                items.append(
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
                        approx=measure_approx_spec,
                    )
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

    def name(self, query_name: str) -> "QueryBuilder":
        """Assign a name to this query for provenance tracking.
        
        Named queries are easier to debug and their names appear in:
        - Provenance metadata
        - Debug output
        - Explanations
        - Algebra operation tracking
        
        Args:
            query_name: Descriptive name for this query
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Name subqueries for better tracking
            >>> hubs = Q.nodes().where(degree__gt=5).name("high_degree_hubs")
            >>> stable = Q.nodes().uq(method="bootstrap", n_samples=100).name("stable_nodes")
            >>> 
            >>> # Compose named queries
            >>> robust_hubs = hubs & stable
            >>> robust_hubs = robust_hubs.name("robust_hubs")
            >>> 
            >>> # Execute and check provenance
            >>> result = robust_hubs.execute(network)
            >>> print(result.meta.get('query_name'))  # "robust_hubs"
            >>> print(result.meta.get('algebra_op'))   # Shows operand names
        """
        if not hasattr(self._select, '_query_name'):
            self._select._query_name = query_name
        else:
            self._select._query_name = query_name
        return self

    def resolve(
        self, 
        identity: Optional[str] = None,
        conflicts: Optional[str] = None
    ) -> "QueryBuilder":
        """Configure resolution strategies for algebra operations.
        
        This method sets strategies for handling ambiguities when combining
        queries or results through algebraic operators.
        
        Args:
            identity: Identity strategy for multilayer comparisons
                - "by_id": Compare nodes by ID only (ignore layer)
                - "by_replica": Compare by (node_id, layer) tuple
            conflicts: Conflict resolution strategy for attributes
                - "error": Raise error on conflicts (default)
                - "prefer_left": Use value from left operand
                - "prefer_right": Use value from right operand
                - "mean": Average numeric values
                - "max": Take maximum value
                - "min": Take minimum value
                - "keep_both": Store both with namespaced keys
                
        Returns:
            Self for chaining
            
        Example:
            >>> # Specify identity for multilayer algebra
            >>> q1 = Q.nodes().from_layers(L["social"]).resolve(identity="by_id")
            >>> q2 = Q.nodes().from_layers(L["work"]).resolve(identity="by_id")
            >>> union = q1 | q2  # Merges by node ID
            >>> 
            >>> # Handle attribute conflicts
            >>> q1 = Q.nodes().compute("degree")
            >>> q2 = Q.nodes().compute("pagerank")
            >>> combined = (q1 & q2).resolve(conflicts="mean")
            >>> 
            >>> # Set both strategies
            >>> query = (
            ...     Q.nodes()
            ...      .compute("degree")
            ...      .resolve(identity="by_replica", conflicts="prefer_left")
            ... )
        """
        if identity is not None:
            # Store in metadata for use during algebra
            if not hasattr(self._select, '_resolution_config'):
                self._select._resolution_config = {}
            self._select._resolution_config['identity'] = identity
            
        if conflicts is not None:
            if not hasattr(self._select, '_resolution_config'):
                self._select._resolution_config = {}
            self._select._resolution_config['conflicts'] = conflicts
            
        return self

    def uq(
        self,
        method: Optional[str] = None,
        n_samples: Optional[int] = None,
        ci: Optional[float] = None,
        seed: Optional[int] = None,
        mode: str = "summarize_only",
        keep_samples: Optional[bool] = None,
        reduce: str = "empirical",
        **kwargs,
    ) -> "QueryBuilder":
        """Set query-scoped uncertainty quantification configuration.

        This method establishes uncertainty defaults for all metrics computed
        in this query, unless overridden on a per-metric basis in compute().
        
        When parameters are None, they will be resolved from:
        - Global defaults (set via set_global_uq_defaults())
        - Library defaults (perturbation, n_samples=50, ci=0.95)

        Args:
            method: Uncertainty estimation method ('bootstrap', 'perturbation', 'seed', 'null_model')
                   If None, uses global or library default.
            n_samples: Number of samples for uncertainty estimation
                      If None, uses global or library default (50).
            ci: Confidence interval level (e.g., 0.95 for 95% CI)
               If None, uses global or library default (0.95).
            seed: Random seed for reproducibility (default: None)
            mode: UQ execution mode (default: 'summarize_only')
                 - 'summarize_only': Current behavior, UQ computed per metric
                 - 'propagate': Execute entire query per replicate, combine results
            keep_samples: Whether to keep raw samples in results (default: None = auto)
                         Auto defaults to True for propagate mode, False for summarize_only
            reduce: Reduction method (default: 'empirical')
                   - 'empirical': Store full sample statistics
                   - 'gaussian': Reduce to mean + std Gaussian approximation
            **kwargs: Additional method-specific parameters (e.g., bootstrap_unit='edges',
                     bootstrap_mode='resample', null_model='configuration')

        Returns:
            Self for chaining

        Example:
            >>> # Set uncertainty with explicit parameters (summarize_only)
            >>> (Q.nodes()
            ...   .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)
            ...   .compute("betweenness_centrality")
            ...   .where(betweenness_centrality__mean__gt=0.1)
            ...   .execute(net))

            >>> # Use propagate mode for end-to-end uncertainty
            >>> (Q.nodes()
            ...   .compute("pagerank")
            ...   .order_by("pagerank", desc=True)
            ...   .limit(3)
            ...   .uq(method="perturbation", n_samples=25, seed=42, mode="propagate")
            ...   .execute(net))

            >>> # Use global defaults
            >>> set_global_uq_defaults(method="bootstrap", n_samples=200, seed=42)
            >>> (Q.nodes()
            ...   .uq()  # Uses global defaults
            ...   .compute("degree")
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

        # If method=None explicitly, disable UQ (backward compatibility)
        if method is None:
            self._select.uq_config = None
            return self

        # Create UQConfig - None values will be resolved during execution
        # using the priority order: query > global > library
        self._select.uq_config = UQConfig(
            method=method,
            n_samples=n_samples,
            ci=ci,
            seed=seed,
            mode=mode,
            keep_samples=keep_samples,
            reduce=reduce,
            kwargs=kwargs,
        )
        return self

    def uncertainty(
        self,
        method: Optional[str] = "perturbation",
        n_samples: Optional[int] = 50,
        ci: Optional[float] = 0.95,
        seed: Optional[int] = None,
        **kwargs,
    ) -> "QueryBuilder":
        """Alias for uq() - set query-scoped uncertainty configuration.

        See uq() for full documentation.
        """
        return self.uq(method=method, n_samples=n_samples, ci=ci, seed=seed, **kwargs)

    def community(
        self,
        method: str = "leiden",
        gamma: Union[float, Dict[Any, float]] = 1.0,
        omega: Union[float, np.ndarray] = 1.0,
        n_iterations: int = 2,
        random_state: Optional[int] = None,
        partition_name: str = "default",
        **kwargs,
    ) -> "QueryBuilder":
        """Run community detection and attach partition to network.
        
        This operator runs community detection on the network and attaches the
        resulting partition so it can be queried or used in subsequent operations.
        
        Supported algorithms:
            - "leiden": Multilayer Leiden algorithm (production-ready with UQ)
            - "louvain": Multilayer Louvain algorithm
            - "infomap": Infomap (if available)
            - "label_propagation_supra": Supra-graph label propagation (hard labels)
            - "label_propagation_consensus": Multiplex consensus label propagation (hard labels)
            
        For Leiden specifically, use in combination with .uq() for uncertainty
        quantification. Label propagation algorithms support deterministic execution
        with random_state for reproducibility.
        
        Args:
            method: Community detection algorithm (default: "leiden")
            gamma: Resolution parameter(s). Higher -> more communities. (default: 1.0)
                   Not used for label_propagation algorithms.
            omega: Interlayer coupling strength. Higher -> stronger coupling. (default: 1.0)
                   For label_propagation_supra: weight of identity links between layers.
                   Not used for label_propagation_consensus.
            n_iterations: Number of iterations for iterative methods (default: 2)
                         For label_propagation_supra: maps to max_iter (default: 100)
                         For label_propagation_consensus: maps to max_iter (default: 25)
            random_state: Random seed for reproducibility. If None, uses 0. (default: None)
            partition_name: Name to assign to this partition (default: "default")
            **kwargs: Additional algorithm-specific parameters:
                     - projection: "none" or "majority" (label_propagation_supra only)
                     - inner_max_iter: int (label_propagation_consensus only, default: 50)
                     - max_iter: int (override default iterations for label propagation)
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Basic Leiden community detection
            >>> result = (
            ...     Q.nodes()
            ...      .community(method="leiden", gamma=1.2, random_state=42)
            ...      .execute(network)
            ... )
            >>>
            >>> # Supra-graph label propagation with layer coupling
            >>> result = (
            ...     Q.nodes()
            ...      .community(method="label_propagation_supra", omega=0.7, 
            ...                projection="none", random_state=42)
            ...      .execute(network)
            ... )
            >>>
            >>> # Consensus label propagation (node-level)
            >>> result = (
            ...     Q.nodes()
            ...      .community(method="label_propagation_consensus", 
            ...                max_iter=25, inner_max_iter=50, random_state=42)
            ...      .execute(network)
            ... )
            >>>
            >>> # Leiden with uncertainty quantification
            >>> result = (
            ...     Q.nodes()
            ...      .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
            ...      .uq(method="ensemble", n_samples=50, seed=42)
            ...      .execute(network)
            ... )
            >>> print(f"Consensus partition: {result.meta['consensus_partition']}")
            >>> print(f"Score CI: {result.meta['score_ci']}")
            >>>
            >>> # Query communities after detection
            >>> result = (
            ...     Q.nodes()
            ...      .community(method="leiden", partition_name="my_leiden")
            ...      .execute(network)
            ... )
            >>> communities = Q.communities(partition="my_leiden").execute(network)
            
        Notes:
            - Results are attached to the network under partition_name
            - Combining with .uq() enables probabilistic community detection
            - Default random_state=None becomes 0 for determinism
            - For large networks, consider tuning omega and gamma for performance
            - Label propagation algorithms use hard labels with random tie-breaking
        """
        # Store community detection config in select statement
        if not hasattr(self._select, 'community_config'):
            self._select.community_config = {}
        
        self._select.community_config = {
            'method': method,
            'gamma': gamma,
            'omega': omega,
            'n_iterations': n_iterations,
            'random_state': random_state if random_state is not None else 0,
            'partition_name': partition_name,
            **kwargs
        }
        
        return self

    def sensitivity(
        self,
        perturb: str,
        grid: Optional[List[float]] = None,
        n_samples: int = 30,
        seed: Optional[int] = None,
        metrics: Optional[List[str]] = None,
        scope: str = "global",
        **kwargs,
    ) -> "QueryBuilder":
        """Set query-scoped sensitivity analysis configuration.

        Sensitivity analysis tests the robustness of query CONCLUSIONS (rankings,
        sets, communities) under controlled perturbations. This is DISTINCT from
        uncertainty quantification (.uq()):

        - UQ (.uq()): Estimates uncertainty of metric VALUES (mean, std, CI)
        - Sensitivity (.sensitivity()): Assesses stability of CONCLUSIONS

        The sensitivity analysis runs the query on multiple perturbed versions
        of the network and measures how much the conclusions change using
        stability metrics like Jaccard@k and Kendall-τ.

        Args:
            perturb: Perturbation method:
                    - 'edge_drop': Randomly drop edges
                    - 'degree_preserving_rewire': Rewire while preserving degrees
            grid: Perturbation strength grid (default: [0.0, 0.05, 0.1, 0.15, 0.2])
                 Interpretation depends on perturbation method (e.g., fraction of edges)
            n_samples: Number of samples per grid point for averaging (default: 30)
            seed: Random seed for reproducibility (default: None)
            metrics: Stability metrics to compute (default: ['kendall_tau'])
                    Options: 'jaccard_at_k(k)', 'kendall_tau', 'variation_of_information'
            scope: Analysis scope (default: 'global')
                  - 'global': Overall stability curves
                  - 'per_node': Node-level influence scores
                  - 'per_layer': Layer-level influence scores
            **kwargs: Additional perturbation-specific parameters:
                     - layer_aware: Whether to preserve layer structure (default: True)
                     - max_attempts: Max rewiring attempts (for rewiring methods)

        Returns:
            Self for chaining

        Examples:
            >>> # Sensitivity of top-k centrality rankings to edge removal
            >>> result = (
            ...     Q.nodes()
            ...      .compute("betweenness_centrality")
            ...      .order_by("-betweenness_centrality")
            ...      .limit(20)
            ...      .sensitivity(
            ...          perturb="edge_drop",
            ...          grid=[0.0, 0.05, 0.1, 0.15, 0.2],
            ...          n_samples=30,
            ...          metrics=["jaccard_at_k(20)", "kendall_tau"],
            ...          seed=42
            ...      )
            ...      .execute(network)
            ... )
            >>>
            >>> # Access stability curves
            >>> print(result.sensitivity_curves)
            >>>
            >>> # Export to pandas
            >>> df = result.to_pandas(expand_sensitivity=True)

            >>> # Community detection robustness
            >>> result = (
            ...     Q.communities()
            ...      .detect("louvain")
            ...      .sensitivity(
            ...          perturb="degree_preserving_rewire",
            ...          grid=[0.0, 0.1, 0.2, 0.3],
            ...          metrics=["variation_of_information"],
            ...          seed=42
            ...      )
            ...      .execute(network)
            ... )

        Notes:
            - Sensitivity results include stability curves (metric vs perturbation)
            - Unlike UQ, sensitivity does NOT report mean/std/CI for values
            - Sensitivity analyzes how CONCLUSIONS change, not value uncertainty
            - Results can identify tipping points where conclusions collapse
            - Per-node/per-layer scope provides local influence attribution
        """
        # Default grid if not provided
        if grid is None:
            grid = [0.0, 0.05, 0.1, 0.15, 0.2]

        # Default metrics if not provided
        if metrics is None:
            metrics = ["kendall_tau"]

        # Create sensitivity spec
        self._select.sensitivity_spec = SensitivitySpec(
            perturb=perturb,
            grid=grid,
            n_samples=n_samples,
            seed=seed,
            metrics=metrics,
            scope=scope,
            kwargs=kwargs,
        )

        return self

    def contract(self, contract: "Robustness") -> "QueryBuilder":
        """Attach a robustness contract to the query (certification-grade).
        
        Contracts ensure that query conclusions are stable under structural
        perturbations. This is distinct from uncertainty quantification:
        - UQ quantifies uncertainty of estimates (error bars)
        - Contracts certify robustness of conclusions (stable/unstable)
        
        Contracts provide:
        - **Typed failure modes**: Clear classification of why a contract might fail
        - **Auto-inference**: Sensible defaults for perturbation, predicates, samples
        - **Repair mechanisms**: Stable cores, tiers, stable nodes
        - **Determinism**: Default seed=0 ensures reproducibility
        - **Provenance**: Full replay capability
        
        Args:
            contract: Robustness contract object from py3plex.contracts
            
        Returns:
            Self for chaining
            
        Examples:
            >>> from py3plex.contracts import Robustness
            >>> 
            >>> # Minimal usage - all defaults
            >>> result = (Q.nodes()
            ...           .compute("pagerank")
            ...           .top_k(20, "pagerank")
            ...           .contract(Robustness())
            ...           .execute(net))
            >>> 
            >>> if result.contract_ok:
            ...     print("Top-20 PageRank is stable!")
            ... else:
            ...     print(f"Contract failed: {result.failure_mode}")
            ...     print("Stable core:", result.stable_core)
            >>> 
            >>> # Override defaults
            >>> result = (Q.nodes()
            ...           .compute("degree")
            ...           .top_k(10, "degree")
            ...           .contract(Robustness(n_samples=100, p_max=0.2))
            ...           .execute(net))
            >>> 
            >>> # Ranking stability
            >>> result = (Q.nodes()
            ...           .compute("betweenness_centrality")
            ...           .order_by("betweenness_centrality", desc=True)
            ...           .contract(Robustness())
            ...           .execute(net))
            >>> 
            >>> # Community stability
            >>> result = (Q.nodes()
            ...           .community()
            ...           .contract(Robustness())
            ...           .execute(net))
        
        Note:
            Only one contract per query is supported. Calling .contract() multiple
            times will replace the previous contract.
        """
        from .ast import ContractSpec
        
        self._select.contract_spec = ContractSpec(contract=contract)
        return self

    def community_auto(
        self,
        seed: Optional[int] = None,
        fast: bool = True,
        **kwargs
    ) -> "QueryBuilder":
        """Automatically detect communities and join annotations to nodes.
        
        Extends the node query with community assignment annotations:
        - community: Community assignment
        - confidence: Assignment confidence (0-1)
        - entropy: Assignment entropy (uncertainty measure)
        - margin: Margin between top two community assignments
        - community_size: Size of the assigned community
        - layer: Layer name (nullable for single-layer networks)
        
        These annotations can be filtered with .where() like any other attribute.
        
        Args:
            seed: Random seed for reproducibility (default: None)
            fast: Use fast mode with smaller parameter grids (default: True)
            **kwargs: Additional parameters passed to auto_select_community
        
        Returns:
            Self for chaining (execute() will run auto detection and join)
        
        Examples:
            >>> # Basic usage
            >>> result = (
            ...     Q.nodes()
            ...      .community_auto(seed=42)
            ...      .execute(network)
            ... )
            >>> df = result.to_pandas()
            >>> print(df[['node', 'community', 'confidence', 'community_size']])
            >>> 
            >>> # With filtering and computation
            >>> result = (
            ...     Q.nodes()
            ...      .community_auto(seed=42, fast=True)
            ...      .where(community_size__gt=10, confidence__gt=0.8)
            ...      .compute("pagerank")
            ...      .execute(network)
            ... )
        
        Notes:
            - Caching: Auto community detection runs once per execute() call
            - Filtering: All annotation fields support predicate filters
            - Computation: Can chain .compute() after community_auto()
        """
        from .ast import AutoCommunityConfig
        
        # Create auto community config
        config = AutoCommunityConfig(
            enabled=True,
            kind="nodes_join",
            seed=seed,
            fast=fast,
            params=kwargs,
        )
        
        self._select.auto_community_config = config
        
        return self
    
    def explain(
        self,
        neighbors_top: Optional[int] = None,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        neighbors: Optional[Dict[str, Any]] = None,
        community: Optional[Dict[str, Any]] = None,
        layer_footprint: Optional[Dict[str, Any]] = None,
        attribution: Optional[Dict[str, Any]] = None,
        cache: bool = True,
        as_columns: bool = True,
        prefix: str = "",
        include_community: Optional[bool] = None,
    ) -> Union["QueryBuilder", ExplainQuery]:
        """Attach explanations to results OR get execution plan.

        **Two modes:**

        1. **Execution Plan Mode** (no arguments):
           Returns an ExplainQuery that shows the execution plan when executed.
           This is like SQL EXPLAIN - it shows what the query will do.

        2. **Explanations Mode** (with arguments):
           Attaches explanations to each result row (typically nodes), such as:
           - Community membership and size
           - Top neighbors by weight/degree
           - Layer footprint (which layers the node appears in)
           - Attribution (Shapley value explanations for why items are ranked/scored highly)

        Args:
            neighbors_top: Maximum number of neighbors to include in top_neighbors (default: 10).
                         If None and no other args, returns execution plan (mode 1).
            include: List of explanation blocks to compute. If None, uses defaults:
                    ["community", "top_neighbors", "layer_footprint"]
                    To include attribution, explicitly add "attribution" to the list.
            exclude: List of explanation blocks to exclude from include list
            neighbors: Optional configuration for neighbor selection:
                      - "metric": "weight" or "degree" (default: "weight")
                      - "scope": "layer" (per-layer) or "global" (default: "layer")
                      - "direction": "out", "in", or "both" (default: "both")
            community: Optional configuration for community explanations (reserved)
            layer_footprint: Optional configuration for layer footprint (reserved)
            attribution: Optional configuration for attribution explanations (Shapley values):
                        - "metric": str (which metric to explain, auto-detected if None)
                        - "objective": "value" or "rank" (default: "value")
                        - "levels": ["layer", "edge"] (default: ["layer"])
                        - "method": "shapley", "shapley_mc", or "influence" (default: "shapley_mc")
                        - "seed": int (random seed for reproducibility)
                        - "n_permutations": int (Monte Carlo samples, default: 128)
                        - "max_edges": int (max candidate edges, default: 40)
                        - See AttributionConfig for full options
            cache: Whether to cache neighbor lookups (default: True)
            as_columns: Store explanations as top-level columns in result (default: True)
            prefix: Optional prefix for explanation column names (default: "")
            include_community: Optional shorthand to explicitly exclude community info (use False).
                             By default, community info is included automatically when available.
                             Set to False to exclude it. Setting to True is redundant (default behavior).

        Returns:
            QueryBuilder (self) for chaining when in explanations mode
            ExplainQuery when in execution plan mode

        Raises:
            ValueError: If include contains unknown explanation blocks
            ValueError: If neighbors_top < 1

        Examples:
            >>> # Execution plan mode (no arguments)
            >>> plan = Q.nodes().compute("degree").explain().execute(network)
            >>> print(plan.steps)

            >>> # Explanations mode with attribution
            >>> result = (
            ...     Q.nodes()
            ...      .compute("pagerank")
            ...      .order_by("-pagerank")
            ...      .limit(10)
            ...      .explain(
            ...          include=["attribution"],
            ...          attribution={"metric": "pagerank", "levels": ["layer"], "seed": 42}
            ...      )
            ...      .execute(network)
            ... )
            >>> df = result.to_pandas(expand_explanations=True)
            >>> # df now has attribution column with layer contributions

            >>> # Explicitly exclude community info if not needed
            >>> result = (
            ...     Q.nodes()
            ...      .compute("betweenness")
            ...      .explain(neighbors_top=5, include_community=False)
            ...      .execute(network)
            ... )
        """
        # Check if this is execution plan mode (no arguments provided)
        has_any_arg = any(
            [
                neighbors_top is not None,
                include is not None,
                exclude is not None,
                neighbors is not None,
                community is not None,
                layer_footprint is not None,
                attribution is not None,
                not cache,  # cache defaults to True, so False means it was set
                not as_columns,  # as_columns defaults to True, so False means it was set
                prefix != "",  # prefix defaults to "", so non-empty means it was set
                include_community is not None,  # New parameter
            ]
        )

        if not has_any_arg:
            # Execution plan mode - return ExplainQuery
            return ExplainQuery(self._select)

        # Explanations mode - continue with explanation logic
        from .ast import ExplainSpec

        # Set default for neighbors_top if not provided
        if neighbors_top is None:
            neighbors_top = 10

        # Determine final include list
        if include is None:
            final_include = ["community", "top_neighbors", "layer_footprint"]
        else:
            final_include = list(include)

        # Apply exclusions first
        if exclude:
            final_include = [b for b in final_include if b not in exclude]

        # Handle include_community shorthand (takes precedence over exclude)
        # This is processed after exclude so that include_community can override it
        if include_community is not None:
            if include_community:
                # Ensure community is in the include list (even if it was excluded)
                if "community" not in final_include:
                    final_include.append("community")
            else:
                # Ensure community is NOT in the include list
                final_include = [b for b in final_include if b != "community"]

        # Validate include list
        supported_blocks = {"community", "top_neighbors", "layer_footprint", "attribution"}
        unknown = set(final_include) - supported_blocks
        if unknown:
            raise ValueError(
                f"Unknown explanation blocks: {', '.join(sorted(unknown))}. "
                f"Supported blocks: {', '.join(sorted(supported_blocks))}"
            )

        # Validate neighbors_top
        if neighbors_top < 1:
            raise ValueError(f"neighbors_top must be >= 1, got {neighbors_top}")

        # Check if explain already called
        if self._select.explain_spec is not None:
            # Merge with existing spec (allow multiple calls)
            existing = self._select.explain_spec

            # Merge include lists (deduplicate)
            merged_include = list(dict.fromkeys(existing.include + final_include))

            # Later call overrides scalar values
            self._select.explain_spec = ExplainSpec(
                include=merged_include,
                exclude=list(set(existing.exclude) | set(exclude or [])),
                neighbors_top=neighbors_top,
                neighbors_cfg=neighbors or existing.neighbors_cfg,
                community_cfg=community or existing.community_cfg,
                layer_footprint_cfg=layer_footprint or existing.layer_footprint_cfg,
                attribution_cfg=attribution or existing.attribution_cfg,
                cache=cache,
                as_columns=as_columns,
                prefix=prefix,
            )
        else:
            # Create new spec
            self._select.explain_spec = ExplainSpec(
                include=final_include,
                exclude=exclude or [],
                neighbors_top=neighbors_top,
                neighbors_cfg=neighbors or {},
                community_cfg=community or {},
                layer_footprint_cfg=layer_footprint or {},
                attribution_cfg=attribution or {},
                cache=cache,
                as_columns=as_columns,
                prefix=prefix,
            )

        return self

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

    def summarise(self, **aggs: str) -> "QueryBuilder":
        """Aggregate grouped results using summary expressions.

        This method is used with grouping (e.g., per_layer(), per_layer_pair())
        to compute aggregate statistics per group.

        Args:
            **aggs: Named aggregation expressions:
                - count="n" - Count of items in group
                - mean_w="mean(weight)" - Mean of weight attribute
                - sum_w="sum(weight)" - Sum of weight attribute
                - n_layers="n_unique(layer)" - Count of unique layer values

        Returns:
            Self for chaining

        Example:
            >>> Q.edges().per_layer_pair().summarise(count="n", mean_w="mean(weight)").end_grouping()
        """
        if self._select.summarize_aggs is None:
            self._select.summarize_aggs = {}
        self._select.summarize_aggs.update(aggs)
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
            raise ValueError(
                f"coverage(mode='{mode}') requires k or threshold parameter"
            )

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
                '    Q.nodes().from_layers(L["*"])\n'
                '        .per_layer().top_k(5, "degree").end_grouping()\n'
                '        .coverage(mode="all")'
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
            - n() / count() : count of items
            - mean(attr) : mean value
            - median(attr) : median value
            - sum(attr) : sum of values
            - min(attr) : minimum value
            - max(attr) : maximum value
            - std(attr) : standard deviation
            - var(attr) : variance
            - quantile(attr, p) : p-th quantile (e.g., quantile(degree, 0.95))

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
            ...     median_degree="median(degree)",
            ...     q95_degree="quantile(degree, 0.95)",
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

    
# ═══════════════════════════════════════════════════════════════════════
    # Additional dplyr-style methods (merged from graph_ops.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════════════
    # Additional dplyr-style methods (merged from graph_ops.py)
    # ═══════════════════════════════════════════════════════════════════════
    
    def filter(self, *args, **kwargs) -> "QueryBuilder":
        """Filter results using a predicate (dplyr-style alias for where).
        
        This is an alias for the where() method, providing the traditional
        dplyr naming convention. Supports the same syntax as where():
        - Keyword arguments for simple conditions
        - Expression objects using F
        
        Args:
            *args: BooleanExpression objects from F
            **kwargs: Conditions as keyword arguments
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().filter(degree__gt=5)
            >>> Q.nodes().filter(F.degree > 5, layer="social")
        """
        return self.where(*args, **kwargs)
    
    def filter_expr(self, expr: str) -> "QueryBuilder":
        """Filter results using a string expression.
        
        Provides string-based filtering similar to pandas query() or
        graph_ops.NodeFrame.filter_expr(). Uses safe expression evaluation
        to prevent code injection.
        
        Args:
            expr: Expression string like "degree > 10 and layer == 'social'"
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree").filter_expr("degree > 10 and layer == 'ppi'")
            >>> Q.edges().filter_expr("weight > 0.5")
        
        Note:
            This method creates a post-processing filter that evaluates
            the expression on each result row. For better performance,
            use where() with keyword arguments when possible.
        """
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "expression",
            "expr": expr,
        })
        return self
    
    def head(self, n: int = 5) -> "QueryBuilder":
        """Keep only the first n results (dplyr-style).
        
        Equivalent to limit(n) but with more intuitive dplyr-style naming.
        
        Args:
            n: Number of results to keep (default: 5)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree").head(10)
            >>> Q.nodes().arrange("-degree").head(5)
        """
        return self.limit(n)
    
    def tail(self, n: int = 5) -> "QueryBuilder":
        """Keep only the last n results.
        
        Returns the last n results after all other operations are applied.
        Useful for finding the bottom-k items when combined with sorting.
        
        Args:
            n: Number of results to keep from the end (default: 5)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().compute("degree").arrange("degree").tail(5)  # 5 lowest degree nodes
        """
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "tail",
            "n": n,
        })
        return self
    
    def take(self, n: int = 5) -> "QueryBuilder":
        """Keep only the first n results (alias for head).
        
        SQL-style alias for head() method.
        
        Args:
            n: Number of results to keep (default: 5)
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().take(10)
        """
        return self.head(n)
    
    def sample(self, n: int = 5, seed: Optional[int] = None) -> "QueryBuilder":
        """Randomly sample n results.
        
        Randomly selects n items from the result set. Useful for
        quick exploration or testing on a subset of data.
        
        Args:
            n: Number of results to sample (default: 5)
            seed: Optional random seed for reproducibility
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().sample(10, seed=42)
            >>> Q.nodes().from_layers(L["social"]).sample(5)
        """
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "sample",
            "n": n,
            "seed": seed,
        })
        return self
    
    def slice(self, start: int, end: Optional[int] = None) -> "QueryBuilder":
        """Slice results from start to end index.
        
        Returns a slice of the result set using Python's slicing semantics.
        
        Args:
            start: Starting index (0-based, inclusive)
            end: Ending index (exclusive). If None, slices to the end.
            
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().slice(5, 15)  # rows 5-14
            >>> Q.nodes().slice(10)     # rows 10 to end
        """
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "slice",
            "start": start,
            "end": end,
        })
        return self
    
    def first(self) -> "QueryBuilder":
        """Return only the first result.
        
        Terminal-style operation that limits results to 1. 
        Note: This still returns a QueryBuilder for chaining with execute().
        
        Returns:
            Self for chaining
            
        Example:
            >>> result = Q.nodes().arrange("-degree").first().execute(net)
            >>> df = result.to_pandas()  # Will have at most 1 row
        """
        return self.limit(1)
    
    def last(self) -> "QueryBuilder":
        """Return only the last result.
        
        Returns the last result after all other operations are applied.
        
        Returns:
            Self for chaining
            
        Example:
            >>> result = Q.nodes().arrange("degree").last().execute(net)
        """
        if self._select.post_filters is None:
            self._select.post_filters = []
        
        self._select.post_filters.append({
            "type": "last",
        })
        return self
    
    def collect(self) -> "QueryBuilder":
        """Explicitly collect results (no-op for builder).
        
        This method exists for API compatibility with graph_ops.NodeFrame
        but is a no-op in the builder pattern since execute() handles
        collection. Included for completeness and to reduce cognitive load
        when switching between APIs.
        
        Returns:
            Self for chaining
            
        Example:
            >>> result = Q.nodes().filter(degree__gt=5).collect().execute(net)
        """
        # No-op in builder - execute() handles collection
        return self
    
    def pluck(self, field: str) -> "QueryBuilder":
        """Extract values for a single field/column.
        
        Convenience method that selects only one column. Equivalent to
        select(field) but with more intuitive naming for single-column extraction.
        
        Args:
            field: Field name to extract
            
        Returns:
            Self for chaining
            
        Example:
            >>> result = Q.nodes().compute("degree").pluck("degree").execute(net)
            >>> df = result.to_pandas()  # Will have only 'degree' column (plus id/layer)
        """
        return self.select(field)
    

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
            kind="at", t0=float(t), t1=float(t)
        )
        return self

    def during(
        self, t0: Optional[float] = None, t1: Optional[float] = None
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
        self._select.temporal_context = TemporalContext(kind="during", t0=t0, t1=t1)
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
            kind="during", t0=None, t1=float(t)
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
            kind="during", t0=float(t), t1=None
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
            raise ValueError(
                f"Unknown export target: {target}. Options: {list(target_map.keys())}"
            )
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

        self._select.post_filters.append(
            {
                "type": "community_predicate",
                "predicate": predicate,
            }
        )
        return self

    def aggregate(self, **aggregations) -> "QueryBuilder":
        """Aggregate columns with support for lambdas and builtin functions.

        This method computes aggregations over the result set. It supports:
        - Built-in aggregation functions: mean(), sum(), min(), max(), std(), var(), median(), quantile(attr, p), count()
        - Direct attribute references for last/first value
        - Lambda functions for custom aggregations

        The aggregations are computed after grouping if active, otherwise globally.

        Args:
            **aggregations: Named aggregations where:
                - Key is the output column name
                - Value is either:
                    * A string like "mean(degree)", "quantile(degree, 0.95)", or "sum(weight)"
                    * A string attribute name (gets the value directly)
                    * A lambda function receiving each item

        Returns:
            Self for chaining

        Example:
            >>> Q.nodes().per_layer().aggregate(
            ...     avg_degree="mean(degree)",
            ...     max_bc="max(betweenness_centrality)",
            ...     median_bc="median(betweenness_centrality)",
            ...     q95_degree="quantile(degree, 0.95)",
            ...     node_count="count()",
            ...     layer_name="layer"  # Direct attribute
            ... )

            >>> # With lambda
            >>> Q.nodes().aggregate(
            ...     community_size=lambda n: network.community_sizes[network.get_partition(n)]
            ... )

            >>> # Edge aggregations
            >>> Q.edges().per_layer_pair().aggregate(
            ...     avg_weight="mean(weight)",
            ...     total_edges="count()",
            ...     max_src_degree="max(src_degree)"
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

    def provenance(
        self,
        mode: str = "replayable",
        capture: str = "auto",
        max_bytes: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> "QueryBuilder":
        """Configure provenance tracking for this query.

        Enables replayable provenance that captures sufficient information
        to deterministically reproduce the query result.

        Args:
            mode: Provenance mode ("log" or "replayable"). Default: "replayable"
            capture: Network capture method:
                - "auto": Automatically decide based on network size
                - "fingerprint": Only capture metadata (node/edge counts)
                - "snapshot": Always capture full network snapshot
                - "delta": Capture delta from base (if available)
            max_bytes: Maximum bytes for inline snapshot (default: 10MB)
            seed: Base random seed for reproducibility (default: None)

        Returns:
            Self for chaining

        Example:
            >>> result = (Q.nodes()
            ...          .provenance(mode="replayable", capture="auto", seed=42)
            ...          .compute("degree")
            ...          .execute(net))
            >>> result.is_replayable  # True
            >>> result.replay()  # Deterministically reproduce the result
            >>> result.export_bundle("result.json.gz")  # Save for later
        """
        # Store provenance config in select statement
        if not hasattr(self._select, "provenance_config"):
            self._select.provenance_config = {}

        self._select.provenance_config = {
            "mode": mode,
            "capture": capture,
            "max_bytes": max_bytes,
            "seed": seed,
        }

        return self

    def reproducible(
        self, enabled: bool = True, capture: str = "auto", seed: Optional[int] = None
    ) -> "QueryBuilder":
        """Enable reproducible execution (sugar for provenance).

        Convenience method that sets up replayable provenance with
        a simpler interface.

        Args:
            enabled: Whether to enable reproducible mode
            capture: Network capture method (see provenance())
            seed: Base random seed

        Returns:
            Self for chaining

        Example:
            >>> result = Q.nodes().reproducible(True, seed=42).compute("degree").execute(net)
            >>> result.is_replayable  # True
        """
        if enabled:
            return self.provenance(mode="replayable", capture=capture, seed=seed)
        else:
            return self.provenance(mode="log", capture="fingerprint")

    def robustness_check(
        self,
        network: Any,
        strength: str = "medium",
        shake: str = "degree_safe",
        repeats: int = 30,
        seed: Optional[int] = None,
        targets: Optional[Any] = None,
        **params,
    ) -> "RobustnessReport":
        """Test robustness of query results to network perturbations.

        This is the PRIMARY interface for counterfactual analysis. It runs
        the query on the original network (baseline) and on multiple perturbed
        versions to test whether analytical conclusions remain stable.

        Args:
            network: Multilayer network to analyze
            strength: Perturbation strength - "light", "medium", or "heavy"
            shake: Perturbation strategy preset (default: "degree_safe")
                   Options: "quick", "degree_safe", "layer_safe", "weight_only", "targeted"
            repeats: Number of counterfactual runs (default: 30)
            seed: Random seed for reproducibility (default: None)
            targets: Optional target specification for targeted perturbations
            **params: Parameter bindings for the query

        Returns:
            RobustnessReport with human-friendly summary and analysis methods

        Example:
            >>> # Quick robustness check
            >>> report = (Q.nodes()
            ...           .compute("pagerank")
            ...           .robustness_check(net))
            >>> report.show()
            >>>
            >>> # Check top-k stability
            >>> stable = report.stable_top_k(k=10, threshold=0.8)
            >>> fragile = report.fragile(n=5)
        """
        from py3plex.counterfactual import get_preset
        from py3plex.counterfactual.engine import CounterfactualEngine

        # Get intervention spec from preset
        spec = get_preset(shake, strength=strength, targets=targets)

        # Create and run engine
        engine = CounterfactualEngine(
            network=network,
            query=self,
            spec=spec,
            repeats=repeats,
            seed=seed,
            streaming=False,
        )

        result = engine.run()
        return result.to_report()

    def try_strengths(
        self, network: Any, repeats: int = 30, seed: Optional[int] = None, **params
    ) -> pd.DataFrame:
        """Compare light/medium/heavy perturbation strengths.

        This convenience method runs robustness checks at three different
        perturbation strengths and returns a summary table for comparison.

        Args:
            network: Multilayer network to analyze
            repeats: Number of counterfactual runs per strength (default: 30)
            seed: Random seed for reproducibility (default: None)
            **params: Parameter bindings for the query

        Returns:
            DataFrame with summary statistics for each strength level

        Example:
            >>> # Compare strengths
            >>> summary = (Q.nodes()
            ...           .compute("betweenness_centrality")
            ...           .try_strengths(net))
            >>> print(summary)
        """
        import pandas as pd

        strengths = ["light", "medium", "heavy"]
        results = []

        for strength in strengths:
            report = self.robustness_check(
                network=network,
                strength=strength,
                shake="degree_safe",
                repeats=repeats,
                seed=seed,
                **params,
            )

            # Extract key statistics
            summary_df = report.to_pandas()

            # Compute aggregate statistics
            metric_cols = [c for c in summary_df.columns if c.endswith("_cv")]

            strength_summary = {"strength": strength}
            for col in metric_cols:
                metric_name = col.replace("_cv", "")
                strength_summary[f"{metric_name}_avg_cv"] = summary_df[col].mean()
                strength_summary[f"{metric_name}_max_cv"] = summary_df[col].max()

            results.append(strength_summary)

        return pd.DataFrame(results)

    def counterfactualize(
        self,
        network: Any,
        spec: "InterventionSpec",
        repeats: int = 100,
        seed: int = 42,
        **params,
    ) -> "CounterfactualResult":
        """Execute query under custom counterfactual intervention (ADVANCED).

        This is the advanced interface for counterfactual analysis, allowing
        full control over intervention specifications. Most users should use
        robustness_check() instead.

        Args:
            network: Multilayer network to analyze
            spec: Custom InterventionSpec (from py3plex.counterfactual.spec)
            repeats: Number of counterfactual runs (default: 100)
            seed: Random seed for reproducibility (default: 42)
            **params: Parameter bindings for the query

        Returns:
            CounterfactualResult with full details of baseline and counterfactuals

        Example:
            >>> from py3plex.counterfactual import RemoveEdgesSpec
            >>>
            >>> # Custom intervention
            >>> spec = RemoveEdgesSpec(proportion=0.1, mode="targeted")
            >>> result = (Q.nodes()
            ...           .compute("degree")
            ...           .counterfactualize(net, spec, repeats=100))
            >>>
            >>> # Convert to report for analysis
            >>> report = result.to_report()
            >>> report.show()
        """
        from py3plex.counterfactual.engine import CounterfactualEngine

        engine = CounterfactualEngine(
            network=network,
            query=self,
            spec=spec,
            repeats=repeats,
            seed=seed,
            streaming=False,
        )

        return engine.run()

    def join(
        self,
        right: Union["QueryBuilder", QueryResult],
        on: Union[str, List[str]],
        how: str = "inner",
        suffixes: Tuple[str, str] = ("", "_r"),
    ) -> "QueryBuilder":
        """Join this query with another query or result.

        Performs a relational join between two query results. Joins are row-wise
        relational joins, not graph merges. The join is lazy and will be executed
        when .execute() is called.

        Args:
            right: Right query (QueryBuilder or QueryResult to join with)
            on: Column name(s) to join on. Can be a single string or list of strings.
                All keys must exist in both left and right schemas.
            how: Join type. One of:
                - 'inner': Only rows with matching keys in both sides
                - 'left': All left rows, matching right rows (nulls for non-matches)
                - 'right': All right rows, matching left rows (nulls for non-matches)
                - 'outer': All rows from both sides (nulls for non-matches)
                - 'semi': Left rows that have a match in right (left columns only)
                - 'anti': Left rows that have NO match in right (left columns only)
            suffixes: Tuple of (left_suffix, right_suffix) for name collisions.
                Default: ("", "_r")

        Returns:
            JoinBuilder wrapping the join operation for further chaining

        Raises:
            ValueError: If join type is invalid
            InvalidJoinKeyError: If join keys don't exist in schemas (at execute time)

        Examples:
            >>> # Join nodes with communities
            >>> result = (
            ...     Q.nodes()
            ...      .compute("degree")
            ...      .join(
            ...          Q.communities(mode="leiden").members(),
            ...          on=["node", "layer"],
            ...          how="left",
            ...          suffixes=("", "_comm")
            ...      )
            ...      .where(degree__gt=3)
            ...      .execute(network)
            ... )

            >>> # Join with pre-computed result
            >>> communities = Q.communities().members().execute(network)
            >>> result = (
            ...     Q.nodes()
            ...      .compute("degree")
            ...      .join(communities, on=["node", "layer"], how="inner")
            ...      .execute(network)
            ... )

            >>> # Self-join (same query, different filters)
            >>> high_degree = Q.nodes().where(degree__gt=10)
            >>> high_bc = Q.nodes().compute("betweenness_centrality").where(betweenness_centrality__gt=0.1)
            >>> result = high_degree.join(high_bc, on=["node", "layer"], how="inner").execute(network)
        """
        from .ast import JoinNode

        # Validate join type
        valid_join_types = {"inner", "left", "right", "outer", "semi", "anti"}
        if how not in valid_join_types:
            raise ValueError(
                f"Invalid join type '{how}'. Must be one of: {', '.join(sorted(valid_join_types))}"
            )

        # Normalize on to tuple
        if isinstance(on, str):
            on_tuple = (on,)
        else:
            on_tuple = tuple(on)

        # Create JoinBuilder
        return JoinBuilder(
            left=self,
            right=right,
            on=on_tuple,
            how=how,
            suffixes=suffixes,
        )

    def to_program(self) -> "GraphProgram":
        """Convert query to a GraphProgram object without executing.
        
        This creates an immutable program object that can be:
        - Composed with other programs
        - Optimized with rewrite rules
        - Explained with cost estimates
        - Diffed against other programs
        - Cached for reproducibility
        - Executed later
        
        Returns:
            GraphProgram object
            
        Example:
            >>> from py3plex.dsl import Q, L
            >>> program = (Q.nodes()
            ...     .from_layers(L["social"])
            ...     .compute("degree", "betweenness_centrality")
            ...     .top_k(10, "degree")
            ...     .to_program())
            >>> 
            >>> # Inspect without executing
            >>> print(program.hash())
            >>> print(program.explain())
            >>>
            >>> # Optimize and execute
            >>> optimized = program.optimize(budget="10s")
            >>> result = optimized.execute(network)
        """
        from py3plex.dsl.program import GraphProgram
        ast = Query(explain=False, select=self._select)
        return GraphProgram.from_ast(ast)

    def hint(self) -> "QueryBuilder":
        """Display context-aware hints for next query-building steps.
        
        This non-invasive discoverability mechanism suggests relevant methods
        based on the current query state. It prints suggestions to stdout
        but does NOT modify query behavior or auto-execute anything.
        
        Suggestions adapt to:
        - Whether layers are selected
        - Whether filters are applied
        - Whether computations are added
        - Whether grouping is active
        - Whether UQ is enabled
        
        Returns:
            Self for chaining (unmodified)
            
        Example:
            >>> # After where() -> suggests compute(), per_layer(), uq()
            >>> Q.nodes().where(degree__gt=3).hint()
            
            >>> # After per_layer() -> suggests aggregate(), coverage()
            >>> Q.nodes().per_layer().hint()
            
            >>> # After compute() -> suggests order_by(), limit(), explain()
            >>> Q.nodes().compute("degree").hint()
        
        Note:
            This is purely informational. The query remains unchanged.
            Call .execute() when ready to run the query.
        """
        # Collect current query state
        has_layers = (self._select.layer_expr is not None or 
                      (hasattr(self._select, 'layer_set') and self._select.layer_set is not None))
        has_filters = self._select.where is not None
        has_compute = bool(self._select.compute)
        has_grouping = bool(self._select.group_by)
        has_uq = self._select.uq_config is not None
        has_ordering = bool(self._select.order_by)
        has_limit = self._select.limit is not None
        has_explain = self._select.explain_spec is not None
        is_coverage_filtered = (hasattr(self._select, 'coverage_mode') and 
                               self._select.coverage_mode is not None)
        
        print("\n" + "="*60)
        print("[HINT] Query Builder Hints")
        print("="*60)
        
        # Show current state
        print("\n[STATE] Current query state:")
        state_items = []
        if has_layers:
            state_items.append("✓ Layers selected")
        if has_filters:
            state_items.append("✓ Filters applied")
        if has_compute:
            metrics = [c.name for c in self._select.compute]
            state_items.append(f"✓ Computing: {', '.join(metrics)}")
        if has_grouping:
            group_keys = ', '.join(self._select.group_by)
            state_items.append(f"✓ Grouped by: {group_keys}")
        if has_uq:
            state_items.append("✓ Uncertainty enabled")
        if has_ordering:
            state_items.append("✓ Ordering specified")
        if has_limit:
            state_items.append(f"✓ Limited to {self._select.limit} results")
        if has_explain:
            state_items.append("✓ Explanations enabled")
        
        if state_items:
            for item in state_items:
                print(f"  {item}")
        else:
            print("  (empty query - start building!)")
        
        # Suggest next steps based on state
        print("\n[TIP] Suggested next steps:\n")
        
        suggestions = []
        
        # Layer selection suggestions
        if not has_layers:
            suggestions.append(
                "  -> .from_layers(L[\"social\"])  # Filter to specific layers\n"
                "    Example: L[\"social\"] + L[\"work\"] for multiple layers"
            )
        
        # Filter suggestions
        if not has_filters and not has_grouping:
            suggestions.append(
                "  -> .where(degree__gt=3)  # Filter nodes/edges by attributes\n"
                "    Example: .where(layer=\"social\", degree__gt=5)"
            )
        
        # Compute suggestions
        if not has_compute:
            suggestions.append(
                "  -> .compute(\"degree\", \"betweenness_centrality\")  # Compute metrics\n"
                "    Available: degree, betweenness_centrality, pagerank, clustering, ..."
            )
        
        # Grouping suggestions
        if not has_grouping and has_layers:
            suggestions.append(
                "  -> .per_layer()  # Group results by layer for per-layer analysis\n"
                "    Then use: .top_k(), .aggregate(), .coverage()"
            )
        
        if not has_grouping and self._select.target == Target.EDGES:
            suggestions.append(
                "  -> .per_layer_pair()  # Group edges by source-target layer pairs"
            )
        
        # UQ suggestions
        if has_compute and not has_uq:
            suggestions.append(
                "  -> .uq(method=\"bootstrap\", n_samples=100)  # Add uncertainty quantification\n"
                "    Methods: bootstrap, perturbation, seed, stratified_perturbation"
            )
        
        # Grouping-specific suggestions
        if has_grouping and not is_coverage_filtered:
            suggestions.append(
                "  -> .aggregate(\"mean\", \"std\")  # Aggregate metrics within groups"
            )
            suggestions.append(
                "  -> .coverage(mode=\"all\")  # Filter items present across groups\n"
                "    Modes: all, any, at_least, exact, fraction"
            )
            suggestions.append(
                "  -> .end_grouping()  # Return to ungrouped context"
            )
        
        # Ordering suggestions
        if has_compute and not has_ordering:
            suggestions.append(
                "  -> .order_by(\"-degree\")  # Sort results (use '-' for descending)\n"
                "    Example: .order_by(\"-betweenness_centrality\", \"node_id\")"
            )
        
        # Limiting suggestions
        if has_ordering and not has_limit:
            suggestions.append(
                "  -> .limit(10)  # Keep only top N results\n"
                "    Alias: .head(10) for dplyr-style syntax"
            )
        
        if has_grouping:
            suggestions.append(
                "  -> .top_k(10, \"degree\")  # Get top-k items per group"
            )
        
        # Explanation suggestions
        if has_compute and not has_explain:
            suggestions.append(
                "  -> .explain()  # Add explanatory context (community, neighbors, layers)\n"
                "    Options: neighbors_top=5, include_community=True"
            )
        
        # Always suggest execute
        suggestions.append(
            "  -> .execute(network)  # Execute the query and get results"
        )
        
        # Display suggestions
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
            if i < len(suggestions):
                print()
        
        print("\n" + "="*60)
        print("[TIP] Tip: Chain methods together for complex queries!")
        print("   Example: Q.nodes().where(...).compute(...).order_by(...).limit(...).execute(net)")
        print("="*60 + "\n")
        
        return self

    def execute(self, network: Any, progress: bool = True, explain_plan: bool = False, planner: Optional[Dict[str, Any]] = None, **params) -> QueryResult:
        """Execute the query.

        Args:
            network: Multilayer network object
            progress: If True, log progress messages during query execution (default: True)
            explain_plan: If True, populate result.meta["plan"] with execution plan (default: False)
            planner: Optional planner configuration dict (compute_policy, enable_cache, etc.)
            **params: Parameter bindings

        Returns:
            QueryResult with results and metadata
        """
        from .executor import execute_ast
        
        # Check if auto-detection is configured
        if hasattr(self, "_auto_detect_config"):
            config = self._auto_detect_config
            mode = config.get("mode")
            params_dict = config.get("params", {})
            write_attrs = config.get("write_attrs", {})
            
            # Import auto_select_community
            from py3plex.algorithms.community_detection import auto_select_community
            
            # Run auto-detection
            result = auto_select_community(network, mode=mode, **params_dict)
            
            # Assign partition to network
            network.assign_partition(result.partition)
            
            # Write additional attributes if community stats are available
            if hasattr(result, 'community_stats') and result.community_stats is not None:
                # Write community stability if available
                if hasattr(result.community_stats, 'node_confidence') and result.community_stats.node_confidence:
                    stability_attr = write_attrs.get("community_stability", "community_stability")
                    for (node, layer), conf in result.community_stats.node_confidence.items():
                        # Node is already a tuple (node, layer) in the partition
                        network.set_node_attribute((node, layer), stability_attr, conf)
            
            # Write community ID
            community_id_attr = write_attrs.get("community_id", "community_id")
            for (node, layer), comm_id in result.partition.items():
                # Node is already a tuple (node, layer) in the partition
                network.set_node_attribute((node, layer), community_id_attr, comm_id)

        ast = Query(explain=False, select=self._select)
        return execute_ast(network, ast, params=params, progress=progress, explain_plan=explain_plan, planner_config=planner)
    
    def explain_plan(self) -> "QueryBuilder":
        """Enable plan explanation in the next execute() call.
        
        When enabled, the execution plan will be included in result.meta["plan"]
        showing stage order, costs, and optimization rewrites.
        
        Returns:
            Self for chaining
            
        Example:
            >>> result = Q.nodes().compute("degree").explain_plan().execute(net)
            >>> print(result.meta["plan"]["rewrite_summary"])
        """
        # Store flag that will be passed to execute
        if not hasattr(self, "_explain_plan_flag"):
            self._explain_plan_flag = True
        return self
    
    def planner(self, compute_policy: str = "explicit", enable_cache: bool = True, **kwargs) -> "QueryBuilder":
        """Configure query planner behavior.
        
        Args:
            compute_policy: Compute policy - "explicit" (default), "minimal", or "all"
            enable_cache: Whether to enable result caching (default: True)
            **kwargs: Additional planner configuration
            
        Returns:
            Self for chaining
            
        Example:
            >>> # Use minimal compute policy to optimize performance
            >>> result = Q.nodes().compute("degree", "betweenness").where(degree__gt=5)\\
            ...     .planner(compute_policy="minimal").execute(net)
            
            >>> # Disable caching for one-off queries
            >>> result = Q.nodes().compute("degree")\\
            ...     .planner(enable_cache=False).execute(net)
        """
        if not hasattr(self, "_planner_config"):
            self._planner_config = {}
        
        self._planner_config["compute_policy"] = compute_policy
        self._planner_config["enable_cache"] = enable_cache
        self._planner_config.update(kwargs)
        
        return self

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

    def __getattr__(self, name: str):
        """Enable attribute sugar for predicate filters.
        
        This allows calling filter predicates as methods, e.g.:
            .confidence__gt(0.9) instead of .where(confidence__gt=0.9)
            .degree__lt(5) instead of .where(degree__lt=5)
        
        Args:
            name: Attribute name (should be in format: field__operator)
        
        Returns:
            A callable that applies the filter
        
        Raises:
            AttributeError: If name doesn't match the predicate pattern
        """
        # Check if this looks like a predicate (field__operator)
        if "__" in name:
            # Split into field and operator
            parts = name.rsplit("__", 1)
            if len(parts) == 2:
                field, operator = parts
                # Valid operators
                valid_ops = ["gt", "gte", "lt", "lte", "eq", "ne", "in", "contains"]
                if operator in valid_ops:
                    # Return a function that adds this as a where clause
                    def predicate_method(value):
                        return self.where(**{name: value})
                    return predicate_method
        
        # Not a predicate pattern, raise AttributeError as usual
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def name(self, query_name: str) -> "QueryBuilder":
        """Assign a name to this query for provenance tracking.
        
        Named queries appear in provenance metadata and explanations,
        making it easier to understand complex composed queries.
        
        Args:
            query_name: Descriptive name for this query
            
        Returns:
            Self for chaining
            
        Example:
            >>> hubs = Q.nodes().where(degree__gt=5).name("hubs")
            >>> stable = Q.nodes().uq().name("stable_nodes")
            >>> combined = hubs & stable
        """
        # Store name in metadata
        if not hasattr(self._select, 'metadata'):
            self._select.metadata = {}
        self._select.metadata['name'] = query_name
        return self
    
    def resolve(self, 
                identity: Optional[str] = None,
                conflicts: Optional[str] = None) -> "QueryBuilder":
        """Configure algebra resolution strategies for this query.
        
        This method sets strategies for:
        - Identity comparison (by_id vs by_replica)
        - Attribute conflict resolution
        
        Args:
            identity: Identity strategy - "by_id" or "by_replica"
            conflicts: Conflict resolution - "prefer_left", "prefer_right", 
                      "mean", "max", "min", "keep_both", "error"
                      
        Returns:
            Self for chaining
            
        Example:
            >>> q1 = Q.nodes().compute("degree")
            >>> q2 = Q.nodes().compute("pagerank")
            >>> combined = (q1 & q2).resolve(identity="by_id", conflicts="mean")
        """
        from .algebra import IdentityStrategy, ConflictResolution
        
        if not hasattr(self._select, 'metadata'):
            self._select.metadata = {}
        
        if identity is not None:
            try:
                strategy = IdentityStrategy(identity)
                self._select.metadata['identity_strategy'] = strategy
            except ValueError:
                raise ValueError(
                    f"Invalid identity strategy: {identity}. "
                    f"Must be 'by_id' or 'by_replica'"
                )
        
        if conflicts is not None:
            try:
                resolution = ConflictResolution(conflicts)
                self._select.metadata['conflict_resolution'] = resolution
            except ValueError:
                raise ValueError(
                    f"Invalid conflict resolution: {conflicts}. "
                    f"Valid options: prefer_left, prefer_right, mean, max, min, keep_both, error"
                )
        
        return self
    
    def __or__(self, other: "QueryBuilder") -> "QueryBuilder":
        """Union operator: q1 | q2
        
        Combines two queries, keeping items that appear in either query.
        For pre-compute queries (not yet executed), creates a logical OR composition.
        
        Args:
            other: Another QueryBuilder instance
            
        Returns:
            New QueryBuilder representing the union
            
        Raises:
            IncompatibleQueryError: If queries have different targets
            
        Example:
            >>> social_hubs = Q.nodes().from_layers(L["social"]).where(degree__gt=5)
            >>> work_hubs = Q.nodes().from_layers(L["work"]).where(degree__gt=5)
            >>> all_hubs = social_hubs | work_hubs
        """
        from .algebra import check_query_compatibility, AlgebraError
        from copy import deepcopy
        
        check_query_compatibility(self, other)
        
        # Create new builder with combined logic
        result = QueryBuilder(self._select.target, autocompute=self._select.autocompute)
        
        # Store algebra operation in metadata
        if not hasattr(result._select, 'metadata'):
            result._select.metadata = {}
        result._select.metadata['algebra_op'] = {
            'operation': 'union',
            'left': getattr(self._select, 'metadata', {}).get('name', 'unnamed_left'),
            'right': getattr(other._select, 'metadata', {}).get('name', 'unnamed_right'),
        }
        
        # For now, mark as algebra composition (execution will handle merging)
        result._select.metadata['is_algebra_composition'] = True
        result._select.metadata['algebra_operands'] = (deepcopy(self._select), deepcopy(other._select))
        
        return result
    
    def __and__(self, other: "QueryBuilder") -> "QueryBuilder":
        """Intersection operator: q1 & q2
        
        Combines two queries, keeping only items that appear in both queries.
        For pre-compute queries (not yet executed), creates a logical AND composition.
        
        Args:
            other: Another QueryBuilder instance
            
        Returns:
            New QueryBuilder representing the intersection
            
        Raises:
            IncompatibleQueryError: If queries have different targets
            
        Example:
            >>> high_degree = Q.nodes().where(degree__gt=5)
            >>> high_betweenness = Q.nodes().where(betweenness_centrality__gt=0.1)
            >>> hubs = high_degree & high_betweenness
        """
        from .algebra import check_query_compatibility
        from copy import deepcopy
        
        check_query_compatibility(self, other)
        
        result = QueryBuilder(self._select.target, autocompute=self._select.autocompute)
        
        if not hasattr(result._select, 'metadata'):
            result._select.metadata = {}
        result._select.metadata['algebra_op'] = {
            'operation': 'intersection',
            'left': getattr(self._select, 'metadata', {}).get('name', 'unnamed_left'),
            'right': getattr(other._select, 'metadata', {}).get('name', 'unnamed_right'),
        }
        
        result._select.metadata['is_algebra_composition'] = True
        result._select.metadata['algebra_operands'] = (deepcopy(self._select), deepcopy(other._select))
        
        return result
    
    def __sub__(self, other: "QueryBuilder") -> "QueryBuilder":
        """Difference operator: q1 - q2
        
        Keeps items from first query that are not in second query.
        For pre-compute queries (not yet executed), creates a logical difference.
        
        Args:
            other: Another QueryBuilder instance
            
        Returns:
            New QueryBuilder representing the difference
            
        Raises:
            IncompatibleQueryError: If queries have different targets
            
        Example:
            >>> all_nodes = Q.nodes()
            >>> outliers = Q.nodes().where(degree__gt=10)
            >>> normal_nodes = all_nodes - outliers
        """
        from .algebra import check_query_compatibility
        from copy import deepcopy
        
        check_query_compatibility(self, other)
        
        result = QueryBuilder(self._select.target, autocompute=self._select.autocompute)
        
        if not hasattr(result._select, 'metadata'):
            result._select.metadata = {}
        result._select.metadata['algebra_op'] = {
            'operation': 'difference',
            'left': getattr(self._select, 'metadata', {}).get('name', 'unnamed_left'),
            'right': getattr(other._select, 'metadata', {}).get('name', 'unnamed_right'),
        }
        
        result._select.metadata['is_algebra_composition'] = True
        result._select.metadata['algebra_operands'] = (deepcopy(self._select), deepcopy(other._select))
        
        return result
    
    def __xor__(self, other: "QueryBuilder") -> "QueryBuilder":
        """Symmetric difference operator: q1 ^ q2
        
        Keeps items that appear in exactly one of the queries (not both).
        For pre-compute queries (not yet executed), creates a logical XOR.
        
        Args:
            other: Another QueryBuilder instance
            
        Returns:
            New QueryBuilder representing the symmetric difference
            
        Raises:
            IncompatibleQueryError: If queries have different targets
            
        Example:
            >>> social_only = Q.nodes().from_layers(L["social"])
            >>> work_only = Q.nodes().from_layers(L["work"])
            >>> exclusive = social_only ^ work_only  # In one layer, not both
        """
        from .algebra import check_query_compatibility
        from copy import deepcopy
        
        check_query_compatibility(self, other)
        
        result = QueryBuilder(self._select.target, autocompute=self._select.autocompute)
        
        if not hasattr(result._select, 'metadata'):
            result._select.metadata = {}
        result._select.metadata['algebra_op'] = {
            'operation': 'symmetric_difference',
            'left': getattr(self._select, 'metadata', {}).get('name', 'unnamed_left'),
            'right': getattr(other._select, 'metadata', {}).get('name', 'unnamed_right'),
        }
        
        result._select.metadata['is_algebra_composition'] = True
        result._select.metadata['algebra_operands'] = (deepcopy(self._select), deepcopy(other._select))
        
        return result
    
    def __repr__(self) -> str:
        return f"QueryBuilder(target={self._select.target.value})"


class JoinBuilder:
    """Builder for join operations.

    This class wraps a JoinNode and provides a chainable interface for
    operations after a join. Join execution is deferred until .execute()
    is called.

    Do not instantiate directly - use QueryBuilder.join() or QueryResult.join().
    """

    def __init__(
        self,
        left: Union[QueryBuilder, QueryResult],
        right: Union[QueryBuilder, QueryResult],
        on: Tuple[str, ...],
        how: str,
        suffixes: Tuple[str, str],
    ):
        """Initialize JoinBuilder.

        Args:
            left: Left query or result
            right: Right query or result
            on: Tuple of join keys
            how: Join type
            suffixes: Suffix tuple for name collisions
        """
        from .ast import JoinNode

        self._left = left
        self._right = right
        self._on = on
        self._how = how
        self._suffixes = suffixes

        # Build JoinNode
        left_select = left._select if isinstance(left, QueryBuilder) else left._to_select_stmt()
        right_select = right._select if isinstance(right, QueryBuilder) else right._to_select_stmt()

        self._join_node = JoinNode(
            left=left_select,
            right=right_select,
            on=on,
            how=how,
            suffixes=suffixes,
        )

        # Post-join operations (where, compute, order_by, limit)
        self._where: Optional[ConditionExpr] = None
        self._compute: List[ComputeItem] = []
        self._order_by: List[OrderItem] = []
        self._limit: Optional[int] = None

    def where(self, **kwargs) -> "JoinBuilder":
        """Filter joined results.

        Args:
            **kwargs: Conditions (same as QueryBuilder.where)

        Returns:
            Self for chaining
        """
        condition = build_condition_from_kwargs(kwargs)
        if self._where is None:
            self._where = condition
        else:
            # Merge with AND
            self._where.atoms.extend(condition.atoms)
            if condition.atoms:
                self._where.ops.append("AND")
            self._where.ops.extend(condition.ops)
        return self

    def compute(self, *measures: str, **kwargs) -> "JoinBuilder":
        """Compute measures on joined results.

        Args:
            *measures: Measure names
            **kwargs: Additional compute options (alias, uncertainty, etc.)

        Returns:
            Self for chaining
        """
        # Extract kwargs for ComputeItem
        alias = kwargs.get("alias")
        aliases = kwargs.get("aliases")
        uncertainty = kwargs.get("uncertainty", False)
        method = kwargs.get("method")
        n_samples = kwargs.get("n_samples")

        if aliases:
            for name, al in aliases.items():
                self._compute.append(ComputeItem(
                    name=name,
                    alias=al,
                    uncertainty=uncertainty,
                    method=method,
                    n_samples=n_samples,
                ))
        elif alias and len(measures) == 1:
            self._compute.append(ComputeItem(
                name=measures[0],
                alias=alias,
                uncertainty=uncertainty,
                method=method,
                n_samples=n_samples,
            ))
        else:
            self._compute.extend(
                ComputeItem(
                    name=m,
                    uncertainty=uncertainty,
                    method=method,
                    n_samples=n_samples,
                ) for m in measures
            )
        return self

    def order_by(self, *keys: str, desc: bool = False) -> "JoinBuilder":
        """Order joined results.

        Args:
            *keys: Attribute names to order by
            desc: Default sort direction

        Returns:
            Self for chaining
        """
        for k in keys:
            if k.startswith("-"):
                self._order_by.append(OrderItem(key=k[1:], desc=True))
            else:
                self._order_by.append(OrderItem(key=k, desc=desc))
        return self

    def limit(self, n: int) -> "JoinBuilder":
        """Limit joined results.

        Args:
            n: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit = n
        return self

    def execute(self, network: Any, progress: bool = True, explain_plan: bool = False, planner: Optional[Dict[str, Any]] = None, **params) -> QueryResult:
        """Execute the join query.

        Args:
            network: Multilayer network object
            progress: If True, log progress messages
            explain_plan: If True, populate result.meta["plan"] with execution plan (default: False)
            planner: Optional planner configuration dict (compute_policy, enable_cache, etc.)
            **params: Parameter bindings

        Returns:
            QueryResult with joined data and provenance
        """
        from .executor import execute_join

        return execute_join(
            network=network,
            join_node=self._join_node,
            post_where=self._where,
            post_compute=self._compute,
            post_order_by=self._order_by,
            post_limit=self._limit,
            params=params,
            progress=progress,
            explain_plan=explain_plan,
            planner_config=planner,
        )

    def __repr__(self) -> str:
        return f"JoinBuilder(on={self._on}, how={self._how})"


class CommunityQueryBuilder(QueryBuilder):
    """Builder for community queries.

    Extends QueryBuilder with community-specific operations.
    Use Q.communities() to create.
    """

    def __init__(
        self,
        autocompute: bool = True,
        partition_name: str = "default",
        mode: Optional[str] = None,
        fast: Optional[bool] = None,
        uq: Optional[bool] = None,
        uq_n_samples: Optional[int] = None,
        uq_method: Optional[str] = None,
        seed: Optional[int] = None,
        write_attrs: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Initialize community query builder.

        Args:
            autocompute: Whether to automatically compute missing metrics (default: True)
            partition_name: Name of the partition to query (default: "default")
            mode: Auto-detection mode - "pareto" or "wins" (if provided, enables auto-detection)
            fast: Use fast mode with smaller grids/samples (default: True)
            uq: Enable uncertainty quantification (default: False)
            uq_n_samples: Number of UQ samples (default: 10)
            uq_method: UQ method - "seed", "perturbation", or "bootstrap" (default: "seed")
            seed: Master random seed for reproducibility
            write_attrs: Dict mapping attribute names to write (e.g., {"community_id": "community_id"})
            **kwargs: Additional parameters passed to auto_select_community
        """
        super().__init__(Target.COMMUNITIES, autocompute=autocompute)
        self._partition_name = partition_name
        # Store partition name in select for executor
        if not hasattr(self._select, "partition_name"):
            self._select.partition_name = partition_name
        
        # Store auto-detection parameters
        self._auto_detect_mode = mode
        self._auto_detect_params = {
            "fast": fast if fast is not None else True,
            "uq": uq if uq is not None else False,
            "uq_n_samples": uq_n_samples if uq_n_samples is not None else 10,
            "uq_method": uq_method if uq_method is not None else "seed",
            "seed": seed if seed is not None else 0,
            **kwargs
        }
        self._write_attrs = write_attrs or {}

    def from_partition(self, name: str) -> "CommunityQueryBuilder":
        """Select which partition to query.

        Args:
            name: Name of the partition (e.g., "louvain", "infomap", "default")

        Returns:
            Self for chaining

        Example:
            >>> Q.communities().from_partition("louvain")
        """
        self._partition_name = name
        self._select.partition_name = name
        return self
    
    def nodes(self) -> QueryBuilder:
        """Trigger community detection and return a node query builder.
        
        If auto-detection mode is configured (via mode parameter), this method
        will run auto_select_community, assign the results to the network,
        and return a QueryBuilder for nodes with community attributes.
        
        Returns:
            QueryBuilder for nodes with community attributes
            
        Example:
            >>> # Auto-detect communities and query nodes
            >>> result = (
            ...     Q.communities(mode="pareto", fast=False, uq=True, seed=42,
            ...                   write_attrs={"community_id": "community_id"})
            ...      .nodes()
            ...      .node_type("gene")
            ...      .where(degree__gt=3)
            ...      .execute(network)
            ... )
        """
        # Create a new node query builder
        node_builder = QueryBuilder(Target.NODES, autocompute=self._select.autocompute)
        
        # If auto-detection mode is configured, mark for execution
        if self._auto_detect_mode is not None:
            # Store auto-detection configuration in the node builder
            node_builder._auto_detect_config = {
                "mode": self._auto_detect_mode,
                "params": self._auto_detect_params,
                "write_attrs": self._write_attrs,
            }
        
        return node_builder

    def members(self) -> QueryBuilder:
        """Return nodes that are members of the selected communities.

        This bridges from communities to nodes, allowing you to query
        the members of filtered communities.

        Returns:
            NodeQueryBuilder for members

        Example:
            >>> # Get nodes in large communities
            >>> Q.communities().where(size__gt=10).members().compute("degree")
        """
        # Create a new node query builder
        node_builder = QueryBuilder(Target.NODES, autocompute=self._select.autocompute)

        # Mark that this is derived from a community query
        if not hasattr(node_builder._select, "_from_communities"):
            node_builder._select._from_communities = self._select

        return node_builder

    def boundary_edges(self) -> QueryBuilder:
        """Return edges that cross community boundaries.

        Returns edges where source and target are in different communities.

        Returns:
            EdgeQueryBuilder for boundary edges

        Example:
            >>> # Get inter-community edges for large communities
            >>> Q.communities().where(size__gt=10).boundary_edges()
        """
        # Create a new edge query builder
        edge_builder = QueryBuilder(Target.EDGES, autocompute=self._select.autocompute)

        # Mark that this is derived from a community query (boundary edges)
        if not hasattr(edge_builder._select, "_from_communities"):
            edge_builder._select._from_communities = self._select
            edge_builder._select._community_edge_type = "boundary"

        return edge_builder
    
    def auto_select(
        self,
        fast: bool = True,
        max_candidates: int = 10,
        seed: int = 0,
    ) -> "CommunityQueryBuilder":
        """Automatically select best community detection algorithm.
        
        Runs multiple community detection algorithms with parameter grids,
        evaluates them on multiple quality metrics (bucketed), and selects
        the winner using a "most wins" decision engine.
        
        Args:
            fast: Use fast mode with smaller parameter grids (default: True)
            max_candidates: Maximum number of algorithm candidates (default: 10)
            seed: Master random seed for reproducibility (default: 0)
        
        Returns:
            Self for chaining (execute() will run auto-selection)
        
        Examples:
            >>> # Basic auto-selection
            >>> result = Q.community().auto_select().execute(network)
            >>> print(result.explain())
            >>> network.assign_partition(result.partition)
            >>> 
            >>> # With UQ for stability
            >>> result = (
            ...     Q.community()
            ...      .auto_select(fast=True, seed=42)
            ...      .uq(method="seed", n_samples=50, seed=42)
            ...      .execute(network)
            ... )
            >>> print(result.explain())
            >>> print(result.leaderboard)
        
        Notes:
            - Combine with .uq() to enable uncertainty quantification
            - Returns AutoCommunityResult instead of regular QueryResult
            - The winning partition is automatically assigned to the network
        """
        # Mark that auto-selection is requested
        if not hasattr(self._select, "auto_select_config"):
            self._select.auto_select_config = {}
        
        self._select.auto_select_config = {
            "enabled": True,
            "fast": fast,
            "max_candidates": max_candidates,
            "seed": seed,
        }
        
        return self
    
    def auto(
        self,
        seed: Optional[int] = None,
        fast: bool = True,
        **kwargs
    ) -> "CommunityQueryBuilder":
        """Automatically detect communities using the AutoCommunity meta-algorithm.
        
        Returns an assignment table with columns:
        - node: Node identifier
        - layer: Layer name (nullable for single-layer networks)
        - community: Community assignment
        - confidence: Assignment confidence (0-1)
        - entropy: Assignment entropy (uncertainty measure)
        - margin: Margin between top two community assignments
        - community_size: Size of the assigned community
        
        Args:
            seed: Random seed for reproducibility (default: None)
            fast: Use fast mode with smaller parameter grids (default: True)
            **kwargs: Additional parameters passed to auto_select_community
        
        Returns:
            Self for chaining (execute() will run auto community detection)
        
        Examples:
            >>> # Basic usage
            >>> result = Q.communities().auto(seed=42).execute(network)
            >>> df = result.to_pandas()
            >>> print(df.columns)  # node, layer, community, confidence, entropy, margin, community_size
            >>> 
            >>> # With filtering
            >>> result = (
            ...     Q.communities()
            ...      .auto(seed=42, fast=True)
            ...      .where(confidence__gt=0.9, community_size__gt=10)
            ...      .execute(network)
            ... )
        
        Notes:
            - Caching: Auto community detection runs once per execute() call
            - UQ: Combine with .uq() to enable uncertainty quantification
            - Filtering: All assignment table columns support predicate filters
        """
        from .ast import AutoCommunityConfig
        
        # Apply deferred mode if set via select() before auto()
        if hasattr(self, '_deferred_mode'):
            kwargs['mode'] = self._deferred_mode
            delattr(self, '_deferred_mode')
        
        # Create auto community config
        config = AutoCommunityConfig(
            enabled=True,
            kind="communities",
            seed=seed,
            fast=fast,
            params=kwargs,
        )
        
        self._select.auto_community_config = config
        
        return self
    
    def execute(self, network: Any, progress: bool = True, **params):
        """Execute community query or auto-selection.
        
        Args:
            network: Multilayer network object
            progress: If True, log progress messages (default: True)
            **params: Parameter bindings
        
        Returns:
            AutoCommunityResult if auto_select was called, else QueryResult
        """
        # Check if auto-selection is requested
        auto_config = getattr(self._select, "auto_select_config", None)
        
        if auto_config and auto_config.get("enabled", False):
            # Run auto-selection
            from py3plex.algorithms.community_detection import auto_select_community
            
            # Check if UQ is enabled
            uq_config = getattr(self._select, "uq_config", None)
            uq_enabled = uq_config is not None
            
            if uq_enabled:
                uq_method = uq_config.uq_method or "seed"
                uq_n_samples = uq_config.n_samples or 10
            else:
                uq_method = "seed"
                uq_n_samples = 10
            
            result = auto_select_community(
                network=network,
                fast=auto_config.get("fast", True),
                max_candidates=auto_config.get("max_candidates", 10),
                uq=uq_enabled,
                uq_n_samples=uq_n_samples,
                uq_method=uq_method,
                seed=auto_config.get("seed", 0),
            )
            
            return result
        else:
            # Normal community query execution
            return super().execute(network, progress=progress, **params)


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
    def communities(
        autocompute: bool = True,
        partition: str = "default",
        mode: Optional[str] = None,
        fast: Optional[bool] = None,
        uq: Optional[bool] = None,
        uq_n_samples: Optional[int] = None,
        uq_method: Optional[str] = None,
        seed: Optional[int] = None,
        write_attrs: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> CommunityQueryBuilder:
        """Create a query builder for communities.

        Args:
            autocompute: Whether to automatically compute missing metrics (default: True)
            partition: Name of the partition to query (default: "default")
            mode: Auto-detection mode - "pareto" or "wins" (if provided, enables auto-detection)
            fast: Use fast mode with smaller grids/samples (default: True)
            uq: Enable uncertainty quantification (default: False)
            uq_n_samples: Number of UQ samples (default: 10)
            uq_method: UQ method - "seed", "perturbation", or "bootstrap" (default: "seed")
            seed: Master random seed for reproducibility
            write_attrs: Dict mapping attribute names to write (e.g., {"community_id": "community_id"})
            **kwargs: Additional parameters passed to auto_select_community

        Returns:
            CommunityQueryBuilder for communities

        Example:
            >>> # Query large communities
            >>> Q.communities().where(size__gt=10).compute("conductance")

            >>> # Query from a specific algorithm
            >>> Q.communities(partition="louvain").where(density_intra__gt=0.5)

            >>> # Get members of large communities
            >>> Q.communities().where(size__gt=10).members().compute("degree")
            
            >>> # Auto-detection with community assignment
            >>> Q.communities(mode="pareto", fast=False, uq=True, seed=42).nodes()
        """
        return CommunityQueryBuilder(
            autocompute=autocompute,
            partition_name=partition,
            mode=mode,
            fast=fast,
            uq=uq,
            uq_n_samples=uq_n_samples,
            uq_method=uq_method,
            seed=seed,
            write_attrs=write_attrs,
            **kwargs
        )

    @staticmethod
    def assert_subset(subset_query, superset_query, network=None, identity: str = "by_replica") -> bool:
        """Assert that one query result is a subset of another.
        
        This verification method checks algebraic subset relationships between queries.
        Can be used for:
        - Regression testing (ensuring query results remain consistent)
        - Monotonicity checks (verifying that filtering reduces results)
        - Scientific claims validation
        
        Args:
            subset_query: Query or QueryResult that should be subset
            superset_query: Query or QueryResult that should be superset
            network: Network to execute queries on (required if queries not executed)
            identity: Identity strategy - "by_id" or "by_replica" (default: "by_replica")
            
        Returns:
            True if subset_query ⊆ superset_query, False otherwise
            
        Raises:
            AssertionError: If subset condition is violated
            IncompatibleQueryError: If queries have incompatible targets
            
        Example:
            >>> # Verify that high-degree nodes are subset of all nodes
            >>> all_nodes = Q.nodes()
            >>> high_degree = Q.nodes().where(degree__gt=5)
            >>> Q.assert_subset(high_degree, all_nodes, network)
            True
            
            >>> # Regression test: ensure filtering doesn't add nodes
            >>> filtered = Q.nodes().where(layer="social")
            >>> unfiltered = Q.nodes()
            >>> assert Q.assert_subset(filtered, unfiltered, network)
        """
        from .algebra import check_query_compatibility, extract_item_identity, IdentityStrategy
        from .result import QueryResult
        
        # Execute queries if needed
        if not isinstance(subset_query, QueryResult):
            if network is None:
                raise ValueError("network parameter required when queries are not executed")
            subset_result = subset_query.execute(network)
        else:
            subset_result = subset_query
            
        if not isinstance(superset_query, QueryResult):
            if network is None:
                raise ValueError("network parameter required when queries are not executed")
            superset_result = superset_query.execute(network)
        else:
            superset_result = superset_query
        
        # Check compatibility
        if subset_result.target != superset_result.target:
            from .algebra import IncompatibleQueryError
            raise IncompatibleQueryError(
                f"Cannot compare queries with different targets: "
                f"{subset_result.target} vs {superset_result.target}"
            )
        
        # Get identity strategy
        try:
            strategy = IdentityStrategy(identity)
        except ValueError:
            raise ValueError(f"Invalid identity strategy: {identity}. Must be 'by_id' or 'by_replica'")
        
        # Extract identities
        subset_ids = {extract_item_identity(item, strategy) for item in subset_result.items}
        superset_ids = {extract_item_identity(item, strategy) for item in superset_result.items}
        
        # Check subset relationship
        is_subset = subset_ids.issubset(superset_ids)
        
        if not is_subset:
            missing = subset_ids - superset_ids
            raise AssertionError(
                f"Subset assertion failed: {len(missing)} items in subset_query are not in superset_query. "
                f"First few missing items: {list(missing)[:5]}"
            )
        
        return True

    @staticmethod
    def assert_nonempty(query, network=None, message: Optional[str] = None) -> bool:
        """Assert that a query returns non-empty results.
        
        This verification method ensures that queries produce at least one result.
        Useful for:
        - Validating that intersections are meaningful
        - Ensuring filters don't eliminate all items
        - Regression testing
        
        Args:
            query: Query or QueryResult to check
            network: Network to execute query on (required if query not executed)
            message: Custom error message
            
        Returns:
            True if query produces non-empty results
            
        Raises:
            AssertionError: If query returns empty results
            
        Example:
            >>> # Verify that intersection is meaningful
            >>> social = Q.nodes().from_layers(L["social"])
            >>> high_degree = Q.nodes().where(degree__gt=5)
            >>> intersection = social & high_degree
            >>> Q.assert_nonempty(intersection, network)
            True
            
            >>> # Ensure filters don't eliminate everything
            >>> filtered = Q.nodes().where(degree__gt=5, betweenness__gt=0.1)
            >>> assert Q.assert_nonempty(filtered, network)
        """
        from .result import QueryResult
        
        # Execute query if needed
        if not isinstance(query, QueryResult):
            if network is None:
                raise ValueError("network parameter required when query is not executed")
            result = query.execute(network)
        else:
            result = query
        
        is_nonempty = len(result.items) > 0
        
        if not is_nonempty:
            error_msg = message or "Query returned empty results"
            raise AssertionError(f"Non-empty assertion failed: {error_msg}")
        
        return True

    @staticmethod
    def assert_disjoint(query1, query2, network=None, identity: str = "by_replica") -> bool:
        """Assert that two queries have no overlapping results.
        
        This verification method checks that query results are disjoint (no shared items).
        Useful for validating partitioning and exclusive filtering.
        
        Args:
            query1: First query or QueryResult
            query2: Second query or QueryResult
            network: Network to execute queries on (required if queries not executed)
            identity: Identity strategy - "by_id" or "by_replica" (default: "by_replica")
            
        Returns:
            True if results are disjoint
            
        Raises:
            AssertionError: If results overlap
            IncompatibleQueryError: If queries have incompatible targets
            
        Example:
            >>> # Verify that layer filters are exclusive
            >>> social = Q.nodes().from_layers(L["social"])
            >>> work = Q.nodes().from_layers(L["work"])
            >>> Q.assert_disjoint(social, work, network, identity="by_replica")
            True
        """
        from .algebra import check_query_compatibility, extract_item_identity, IdentityStrategy
        from .result import QueryResult
        
        # Execute queries if needed
        if not isinstance(query1, QueryResult):
            if network is None:
                raise ValueError("network parameter required when queries are not executed")
            result1 = query1.execute(network)
        else:
            result1 = query1
            
        if not isinstance(query2, QueryResult):
            if network is None:
                raise ValueError("network parameter required when queries are not executed")
            result2 = query2.execute(network)
        else:
            result2 = query2
        
        # Check compatibility
        if result1.target != result2.target:
            from .algebra import IncompatibleQueryError
            raise IncompatibleQueryError(
                f"Cannot compare queries with different targets: "
                f"{result1.target} vs {result2.target}"
            )
        
        # Get identity strategy
        try:
            strategy = IdentityStrategy(identity)
        except ValueError:
            raise ValueError(f"Invalid identity strategy: {identity}. Must be 'by_id' or 'by_replica'")
        
        # Extract identities
        ids1 = {extract_item_identity(item, strategy) for item in result1.items}
        ids2 = {extract_item_identity(item, strategy) for item in result2.items}
        
        # Check disjoint
        overlap = ids1 & ids2
        
        if overlap:
            raise AssertionError(
                f"Disjoint assertion failed: {len(overlap)} items found in both queries. "
                f"First few overlapping items: {list(overlap)[:5]}"
            )
        
        return True

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
    def counterexample() -> "CounterexampleBuilder":
        """Create a counterexample query builder.
        
        Returns:
            CounterexampleBuilder for finding network counterexamples
            
        Example:
            >>> cex = (
            ...     Q.counterexample()
            ...      .claim("degree__ge(k) -> pagerank__rank_gt(r)")
            ...      .params(k=10, r=50)
            ...      .seed(42)
            ...      .execute(network)
            ... )
        """
        return CounterexampleBuilder()
    
    @staticmethod
    def learn_claims() -> "ClaimLearnerBuilder":
        """Create a claim learning query builder.
        
        Returns:
            ClaimLearnerBuilder for learning claims from network data
            
        Example:
            >>> claims = (
            ...     Q.learn_claims()
            ...      .from_metrics(["degree", "pagerank", "betweenness"])
            ...      .min_support(0.9)
            ...      .min_coverage(0.05)
            ...      .max_claims(20)
            ...      .seed(42)
            ...      .execute(network)
            ... )
        """
        return ClaimLearnerBuilder()

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

    @staticmethod
    def from_ast(query_ast: "Query") -> QueryBuilder:
        """Reconstruct a QueryBuilder from an AST.
        
        This is the inverse of QueryBuilder.to_ast(). It enables:
        - AST round-trip: builder → ast → builder → ast
        - Query replay from stored AST
        - AST-based query transformations
        
        Args:
            query_ast: Query AST to reconstruct from
            
        Returns:
            QueryBuilder that will produce an equivalent AST
            
        Raises:
            ValueError: If AST schema version is incompatible
            ValueError: If AST is invalid or incomplete
            TypeError: If required AST fields are missing
            
        Example:
            >>> # Round-trip a query
            >>> original = Q.nodes().where(degree__gt=5).compute("betweenness")
            >>> ast = original.to_ast()
            >>> reconstructed = Q.from_ast(ast)
            >>> # reconstructed produces equivalent AST
            >>> from py3plex.dsl.ast import ast_equals
            >>> ast_equals(original.to_ast(), reconstructed.to_ast())  # True
        """
        from .ast import Query, SelectStmt, Target
        
        # Validate AST
        if not isinstance(query_ast, Query):
            raise TypeError(f"Expected Query AST, got {type(query_ast)}")
        
        # Check schema version
        if query_ast.dsl_version != "2.0":
            raise ValueError(
                f"Incompatible DSL version: {query_ast.dsl_version} (expected 2.0)"
            )
        
        select = query_ast.select
        if not isinstance(select, SelectStmt):
            raise TypeError(f"Expected SelectStmt, got {type(select)}")
        
        # Create builder with target
        if select.target == Target.NODES:
            builder = Q.nodes(autocompute=select.autocompute)
        elif select.target == Target.EDGES:
            builder = Q.edges(autocompute=select.autocompute)
        elif select.target == Target.COMMUNITIES:
            builder = QueryBuilder(Target.COMMUNITIES, autocompute=select.autocompute)
        else:
            raise ValueError(f"Unknown target: {select.target}")
        
        # Reconstruct layer selection
        if select.layer_expr is not None:
            builder._select.layer_expr = select.layer_expr
        if select.layer_set is not None:
            builder._select.layer_set = select.layer_set
        
        # Reconstruct WHERE conditions
        if select.where is not None:
            builder._select.where = select.where
        
        # Reconstruct COMPUTE
        if select.compute:
            builder._select.compute = list(select.compute)
        
        # Reconstruct ORDER BY
        if select.order_by:
            builder._select.order_by = list(select.order_by)
        
        # Reconstruct LIMIT
        if select.limit is not None:
            builder._select.limit = select.limit
        
        # Reconstruct grouping
        if select.group_by:
            builder._select.group_by = list(select.group_by)
        
        # Reconstruct per-group limit
        if select.limit_per_group is not None:
            builder._select.limit_per_group = select.limit_per_group
        
        # Reconstruct coverage
        if select.coverage_mode is not None:
            builder._select.coverage_mode = select.coverage_mode
            builder._select.coverage_k = select.coverage_k
            builder._select.coverage_p = select.coverage_p
            builder._select.coverage_group = select.coverage_group
            builder._select.coverage_id_field = select.coverage_id_field
        
        # Reconstruct UQ config
        if select.uq_config is not None:
            builder._select.uq_config = select.uq_config
        
        # Reconstruct temporal context
        if select.temporal_context is not None:
            builder._select.temporal_context = select.temporal_context
        
        # Reconstruct window spec
        if select.window_spec is not None:
            builder._select.window_spec = select.window_spec
        
        # Reconstruct aggregations
        if select.aggregate_specs:
            builder._select.aggregate_specs = dict(select.aggregate_specs)
        
        # Reconstruct mutations
        if select.mutate_specs:
            builder._select.mutate_specs = dict(select.mutate_specs)
        
        # Reconstruct column operations
        if select.select_cols is not None:
            builder._select.select_cols = list(select.select_cols)
        if select.drop_cols is not None:
            builder._select.drop_cols = list(select.drop_cols)
        if select.rename_map:
            builder._select.rename_map = dict(select.rename_map)
        if select.distinct_cols is not None:
            builder._select.distinct_cols = list(select.distinct_cols)
        
        # Reconstruct advanced features
        if select.explain_spec is not None:
            builder._select.explain_spec = select.explain_spec
        if select.sensitivity_spec is not None:
            builder._select.sensitivity_spec = select.sensitivity_spec
        if select.counterfactual_spec is not None:
            builder._select.counterfactual_spec = select.counterfactual_spec
        if select.contract_spec is not None:
            builder._select.contract_spec = select.contract_spec
        if select.auto_community_config is not None:
            builder._select.auto_community_config = select.auto_community_config
        
        # Reconstruct export specs
        if select.export is not None:
            builder._select.export = select.export
        if select.file_export is not None:
            builder._select.file_export = select.file_export
        
        return builder

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
                n_runs = (
                    cls._defaults.get("n_samples")
                    or cls._defaults.get("n_boot")
                    or cfg.default_n_runs
                )
                resampling = _METHOD_TO_RESAMPLING.get(
                    cls._defaults.get("method"), cfg.default_resampling
                )
                set_uncertainty_config(
                    UncertaintyConfig(
                        mode=(
                            UncertaintyMode.ON
                            if cls._defaults.get("enabled")
                            else UncertaintyMode.OFF
                        ),
                        default_n_runs=int(n_runs),
                        default_resampling=resampling,
                    )
                )
            except Exception:
                # Keep DSL usable even if uncertainty package is partially available
                logging.getLogger(__name__).debug(
                    "Failed to sync uncertainty context", exc_info=True
                )


# ==============================================================================
# D Factory for Dynamics Simulations
# ==============================================================================


class D:
    """Dynamics simulation factory for DSL-level dynamics.

    This provides an alternative entry point to Q.dynamics() with a more
    simulation-oriented naming convention. Both Q.dynamics() and D.simulate()
    produce the same DynamicsBuilder instances.

    Example:
        >>> from py3plex.dsl import D, L
        >>> from py3plex.dynamics import SIRModel
        >>>
        >>> # Using model instance
        >>> sim = (
        ...     D.simulate(SIRModel(beta=0.3, gamma=0.1))
        ...      .on_layers(L["social"] + L["work"])
        ...      .seed_infections(fraction=0.01)
        ...      .steps(100)
        ...      .execute(network)
        ... )
        >>>
        >>> # Using model name
        >>> sim = (
        ...     D.simulate("SIS", beta=0.3, mu=0.1)
        ...      .on_layers(L["contacts"])
        ...      .seed_infections(0.01)
        ...      .run(steps=100, replicates=10)
        ...      .execute(network)
        ... )
    """

    @staticmethod
    def simulate(model_or_name: Union[str, Any], **params) -> "DynamicsBuilder":
        """Create a dynamics simulation builder.

        Args:
            model_or_name: Either a model name string (e.g., "SIS", "SIR")
                          or a model instance with parameters
            **params: Model parameters (only used if model_or_name is a string)

        Returns:
            DynamicsBuilder for configuring and running simulations

        Example:
            >>> # From model name
            >>> D.simulate("SIS", beta=0.3, mu=0.1).steps(100).execute(net)
            
            >>> # From model instance (if supported in future)
            >>> model = SIRModel(beta=0.3, gamma=0.1)
            >>> D.simulate(model).steps(200).execute(net)
        """
        if isinstance(model_or_name, str):
            # Model name provided
            return DynamicsBuilder(model_or_name, **params)
        else:
            # Model instance provided - extract name and params
            # For now, assume model has 'name' attribute and params as attributes
            if hasattr(model_or_name, 'name'):
                model_name = model_or_name.name
            else:
                # Fall back to class name
                model_name = model_or_name.__class__.__name__.replace('Model', '').upper()
            
            # Extract params from model instance
            model_params = {}
            if hasattr(model_or_name, '__dict__'):
                # Get all non-private attributes
                model_params = {k: v for k, v in model_or_name.__dict__.items() 
                               if not k.startswith('_')}
            
            # Merge with any provided params (provided params override)
            model_params.update(params)
            
            return DynamicsBuilder(model_name, **model_params)


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

    def seed(
        self, query_or_fraction: Union[float, "QueryBuilder"]
    ) -> "DynamicsBuilder":
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
        elif hasattr(query_or_fraction, "_select"):
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

    def parameters_per_layer(
        self, layer_params: Dict[str, Dict[str, Any]]
    ) -> "DynamicsBuilder":
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
        track: Optional[Union[str, List[str]]] = None,
        n_jobs: int = 1,
    ) -> "DynamicsBuilder":
        """Set execution parameters.

        Args:
            steps: Number of time steps to simulate
            replicates: Number of independent runs
            track: Measures to track ("all" or list of specific measures)
            n_jobs: Number of parallel jobs (1 = sequential, -1 = all cores).
                   Parallel execution is deterministic: same seed produces
                   identical results regardless of n_jobs value.

        Returns:
            Self for chaining

        Example:
            >>> # Sequential execution
            >>> builder.run(steps=100, replicates=20, n_jobs=1)
            
            >>> # Parallel execution (deterministic with same seed)
            >>> builder.run(steps=100, replicates=20, n_jobs=4)
        """
        self._stmt.steps = steps
        self._stmt.replicates = replicates
        
        # Store n_jobs for use by executor
        if not hasattr(self._stmt, 'n_jobs'):
            self._stmt.n_jobs = n_jobs
        else:
            self._stmt.n_jobs = n_jobs

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

    def seed_infections(
        self,
        fraction: Optional[float] = None,
        nodes: Optional[List[Tuple[Any, str]]] = None
    ) -> "DynamicsBuilder":
        """Set initial infections for epidemic models (convenience alias for .seed()).

        Args:
            fraction: Fraction of nodes to infect randomly (e.g., 0.01 for 1%)
            nodes: Specific nodes to infect as list of (node_id, layer) tuples

        Returns:
            Self for chaining

        Examples:
            >>> # Infect 1% randomly
            >>> builder.seed_infections(fraction=0.01)

            >>> # Infect specific nodes
            >>> builder.seed_infections(nodes=[('Alice', 'social'), ('Bob', 'work')])
        """
        if fraction is not None and nodes is not None:
            raise ValueError("Provide either 'fraction' or 'nodes', not both")
        
        if fraction is not None:
            self._stmt.seed_fraction = fraction
        elif nodes is not None:
            # Convert nodes list to a query-like structure
            # For now, store directly in seed_nodes (will handle in executor)
            if not hasattr(self._stmt, 'seed_nodes'):
                self._stmt.seed_nodes = nodes
            else:
                self._stmt.seed_nodes = nodes
        else:
            raise ValueError("Must provide either 'fraction' or 'nodes'")
        
        return self

    def starting_nodes(self, nodes: List[Tuple[Any, str]]) -> "DynamicsBuilder":
        """Set starting nodes for random walk dynamics.

        Args:
            nodes: List of (node_id, layer) tuples to start from

        Returns:
            Self for chaining

        Example:
            >>> builder.starting_nodes([('Alice', 'social'), ('Bob', 'work')])
        """
        # For random walk, starting nodes are similar to seed infections
        if not hasattr(self._stmt, 'seed_nodes'):
            self._stmt.seed_nodes = nodes
        else:
            self._stmt.seed_nodes = nodes
        return self

    def steps(self, n: int) -> "DynamicsBuilder":
        """Set number of simulation steps (convenience alias for .run(steps=n)).

        Args:
            n: Number of time steps

        Returns:
            Self for chaining

        Example:
            >>> builder.steps(100)
        """
        self._stmt.steps = n
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

    def uq(
        self, 
        ci_level: float = 0.95, 
        method: str = "dynamics_mc"
    ) -> "DynamicsBuilder":
        """Enable uncertainty quantification for dynamics results.
        
        Wraps per-replicate summary statistics with confidence intervals.
        
        Args:
            ci_level: Confidence interval level (default: 0.95 for 95% CI)
            method: UQ method (default: "dynamics_mc" for Monte Carlo across replicates)
        
        Returns:
            Self for chaining
        
        Example:
            >>> result = (
            ...     Q.dynamics("SIS", beta=0.3, mu=0.1)
            ...      .seed_infections(fraction=0.01)
            ...      .run(steps=100, replicates=50)
            ...      .uq(ci_level=0.95, method="dynamics_mc")
            ...      .execute(network)
            ... )
            >>> # Summary stats now include CI bounds:
            >>> result.mean_peak_time  # {'mean': 45.2, 'ci_low': 40.1, 'ci_high': 50.3}
        """
        # Store UQ configuration in statement for executor
        if not hasattr(self._stmt, 'uq_config'):
            self._stmt.uq_config = {}
        
        self._stmt.uq_config = {
            'ci_level': ci_level,
            'method': method,
        }
        
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
            kind="at", t0=float(t), t1=float(t)
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
            kind="during", t0=float(t0), t1=float(t1)
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


# ==============================================================================
# Semiring Algebra Builder (Part S: Semiring Operations)
# ==============================================================================


class SemiringPathBuilder:
    """Builder for SEMIRING PATH statements.

    Example:
        >>> from py3plex.dsl import S, L
        >>>
        >>> result = (
        ...     S.paths()
        ...      .from_node("Alice")
        ...      .to_node("Bob")
        ...      .semiring("min_plus")
        ...      .lift(attr="weight", default=1.0)
        ...      .from_layers(L["social"] + L["work"])
        ...      .crossing_layers(mode="allowed")
        ...      .max_hops(5)
        ...      .execute(network)
        ... )
    """

    def __init__(self):
        """Initialize builder."""
        from .ast import (
            SemiringPathStmt,
            SemiringSpecNode,
            WeightLiftSpecNode,
            CrossingLayersSpec,
        )

        self._stmt = SemiringPathStmt(
            source="",  # Must be set by from_node()
            semiring_spec=SemiringSpecNode(name="min_plus"),
            lift_spec=WeightLiftSpecNode(),
            crossing_layers=CrossingLayersSpec(),
        )

    def from_node(self, source: Union[str, ParamRef]) -> "SemiringPathBuilder":
        """Set source node.

        Args:
            source: Source node identifier or parameter reference

        Returns:
            Self for chaining
        """
        self._stmt.source = source
        return self

    def to_node(self, target: Union[str, ParamRef]) -> "SemiringPathBuilder":
        """Set target node (optional).

        Args:
            target: Target node identifier or parameter reference

        Returns:
            Self for chaining
        """
        self._stmt.target = target
        return self

    def semiring(
        self, name_or_spec: Union[str, Dict[str, str]]
    ) -> "SemiringPathBuilder":
        """Set semiring specification.

        Args:
            name_or_spec: Either a semiring name (e.g., "min_plus") or
                         a dict mapping layer names to semiring names

        Returns:
            Self for chaining
        """
        from .ast import SemiringSpecNode

        if isinstance(name_or_spec, str):
            self._stmt.semiring_spec = SemiringSpecNode(name=name_or_spec)
        elif isinstance(name_or_spec, dict):
            self._stmt.semiring_spec = SemiringSpecNode(per_layer=name_or_spec)
        return self

    def lift(
        self,
        attr: Optional[str] = None,
        transform: Optional[str] = None,
        default: Any = 1.0,
        on_missing: str = "default",
    ) -> "SemiringPathBuilder":
        """Set weight lifting specification.

        Args:
            attr: Edge attribute name
            transform: Optional transformation ("log")
            default: Default value if missing
            on_missing: Behavior on missing ("default", "fail", "drop")

        Returns:
            Self for chaining
        """
        from .ast import WeightLiftSpecNode

        self._stmt.lift_spec = WeightLiftSpecNode(
            attr=attr,
            transform=transform,
            default=default,
            on_missing=on_missing,
        )
        return self

    def from_layers(self, layer_expr: LayerExprBuilder) -> "SemiringPathBuilder":
        """Filter by layers using layer algebra.

        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])

        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self

    def crossing_layers(
        self,
        mode: str = "allowed",
        penalty: Optional[float] = None,
    ) -> "SemiringPathBuilder":
        """Set cross-layer edge handling.

        Args:
            mode: Crossing mode ("allowed", "forbidden", "penalty")
            penalty: Optional penalty value (for "penalty" mode)

        Returns:
            Self for chaining
        """
        from .ast import CrossingLayersSpec

        self._stmt.crossing_layers = CrossingLayersSpec(mode=mode, penalty=penalty)
        return self

    def max_hops(self, n: int) -> "SemiringPathBuilder":
        """Set maximum path length.

        Args:
            n: Maximum number of hops

        Returns:
            Self for chaining
        """
        self._stmt.max_hops = n
        return self

    def k_best(self, k: int) -> "SemiringPathBuilder":
        """Find k best paths.

        Args:
            k: Number of best paths to find

        Returns:
            Self for chaining
        """
        self._stmt.k_best = k
        return self

    def witness(self, enabled: bool = True) -> "SemiringPathBuilder":
        """Enable/disable witness tracking for path reconstruction.

        Args:
            enabled: Whether to track witnesses

        Returns:
            Self for chaining
        """
        self._stmt.witness = enabled
        return self

    def backend(self, name: str) -> "SemiringPathBuilder":
        """Set backend selection.

        Args:
            name: Backend name ("graph", "matrix")

        Returns:
            Self for chaining
        """
        self._stmt.backend = name
        return self

    def uq(
        self,
        mode: Optional[str] = None,
        samples: Optional[int] = None,
        method: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> "SemiringPathBuilder":
        """Enable uncertainty quantification.

        Args:
            mode: UQ mode ("bootstrap", "seed")
            samples: Number of samples
            method: Resampling method
            seed: Random seed
            **kwargs: Additional UQ parameters

        Returns:
            Self for chaining
        """
        from .ast import UQConfig

        self._stmt.uq_config = UQConfig(
            mode=mode or "bootstrap",
            samples=samples or 100,
            method=method or "bootstrap",
            seed=seed,
            params=kwargs,
        )
        return self

    def execute(self, network: Any, **params) -> "QueryResult":
        """Execute semiring path query.

        Args:
            network: Multilayer network
            **params: Parameter bindings

        Returns:
            QueryResult with path data
        """
        from .executor_semiring import execute_semiring_path_stmt

        return execute_semiring_path_stmt(network, self._stmt, params)

    def to_ast(self) -> "SemiringPathStmt":
        """Export as AST SemiringPathStmt object."""
        return self._stmt

    def __repr__(self) -> str:
        return f"SemiringPathBuilder(from={self._stmt.source}, to={self._stmt.target})"


class SemiringClosureBuilder:
    """Builder for SEMIRING CLOSURE statements.

    Example:
        >>> from py3plex.dsl import S, L
        >>>
        >>> result = (
        ...     S.closure()
        ...      .semiring("boolean")
        ...      .from_layers(L["social"])
        ...      .method("auto")
        ...      .execute(network)
        ... )
    """

    def __init__(self):
        """Initialize builder."""
        from .ast import (
            SemiringClosureStmt,
            SemiringSpecNode,
            WeightLiftSpecNode,
            CrossingLayersSpec,
        )

        self._stmt = SemiringClosureStmt(
            semiring_spec=SemiringSpecNode(name="boolean"),
            lift_spec=WeightLiftSpecNode(),
            crossing_layers=CrossingLayersSpec(),
        )

    def semiring(self, name: str) -> "SemiringClosureBuilder":
        """Set semiring.

        Args:
            name: Semiring name

        Returns:
            Self for chaining
        """
        from .ast import SemiringSpecNode

        self._stmt.semiring_spec = SemiringSpecNode(name=name)
        return self

    def lift(
        self,
        attr: Optional[str] = None,
        transform: Optional[str] = None,
        default: Any = 1.0,
        on_missing: str = "default",
    ) -> "SemiringClosureBuilder":
        """Set weight lifting specification.

        Args:
            attr: Edge attribute name
            transform: Optional transformation
            default: Default value
            on_missing: Behavior on missing

        Returns:
            Self for chaining
        """
        from .ast import WeightLiftSpecNode

        self._stmt.lift_spec = WeightLiftSpecNode(
            attr=attr,
            transform=transform,
            default=default,
            on_missing=on_missing,
        )
        return self

    def from_layers(self, layer_expr: LayerExprBuilder) -> "SemiringClosureBuilder":
        """Filter by layers.

        Args:
            layer_expr: Layer expression

        Returns:
            Self for chaining
        """
        self._stmt.layer_expr = layer_expr._to_ast()
        return self

    def method(self, name: str) -> "SemiringClosureBuilder":
        """Set closure method.

        Args:
            name: Method name ("auto", "floyd_warshall", "iterative")

        Returns:
            Self for chaining
        """
        self._stmt.method = name
        return self

    def backend(self, name: str) -> "SemiringClosureBuilder":
        """Set backend.

        Args:
            name: Backend name

        Returns:
            Self for chaining
        """
        self._stmt.backend = name
        return self

    def execute(self, network: Any, **params) -> "QueryResult":
        """Execute closure query.

        Args:
            network: Multilayer network
            **params: Parameter bindings

        Returns:
            QueryResult with closure data
        """
        from .executor_semiring import execute_semiring_closure_stmt

        return execute_semiring_closure_stmt(network, self._stmt, params)

    def to_ast(self) -> "SemiringClosureStmt":
        """Export as AST."""
        return self._stmt

    def __repr__(self) -> str:
        return f"SemiringClosureBuilder(semiring={self._stmt.semiring_spec.name})"


class S:
    """Semiring algebra factory for creating semiring builders.

    Example:
        >>> S.paths().from_node("A").to_node("B").semiring("min_plus")
        >>> S.closure().semiring("boolean").from_layers(L["social"])
    """

    @staticmethod
    def paths() -> SemiringPathBuilder:
        """Create a semiring path query builder."""
        return SemiringPathBuilder()

    @staticmethod
    def closure() -> SemiringClosureBuilder:
        """Create a semiring closure query builder."""
        return SemiringClosureBuilder()


# ============================================================================
# Counterexample Builder
# ============================================================================


class CounterexampleBuilder:
    """Builder for counterexample queries.
    
    Example:
        >>> from py3plex.dsl import Q
        >>> cex = (Q.counterexample()
        ...          .claim("degree__ge(k) -> pagerank__rank_gt(r)")
        ...          .params(k=10, r=50)
        ...          .seed(42)
        ...          .execute(net))
    """
    
    def __init__(self):
        """Initialize counterexample builder."""
        self._claim_str: Optional[str] = None
        self._params: Dict[str, Any] = {}
        self._layers: Optional[List[str]] = None
        self._seed: int = 42
        self._find_minimal: bool = True
        self._budget_max_tests: int = 200
        self._budget_max_witness_size: int = 500
        self._initial_radius: int = 2
    
    def claim(self, claim_str: str) -> "CounterexampleBuilder":
        """Set the claim to check.
        
        Args:
            claim_str: Claim string (e.g., "degree__ge(k) -> pagerank__rank_gt(r)")
            
        Returns:
            Self for chaining
        """
        self._claim_str = claim_str
        return self
    
    def params(self, **kwargs) -> "CounterexampleBuilder":
        """Set parameter bindings for the claim.
        
        Args:
            **kwargs: Parameter bindings (e.g., k=10, r=50)
            
        Returns:
            Self for chaining
        """
        self._params.update(kwargs)
        return self
    
    def layers(self, layer_expr: Any) -> "CounterexampleBuilder":
        """Set layers to consider.
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])
            
        Returns:
            Self for chaining
        """
        # Extract layer names from layer expression
        if hasattr(layer_expr, 'to_ast'):
            # LayerExprBuilder
            ast = layer_expr.to_ast()
            self._layers = self._extract_layer_names(ast)
        elif isinstance(layer_expr, list):
            self._layers = layer_expr
        else:
            self._layers = [str(layer_expr)]
        return self
    
    def seed(self, seed: int) -> "CounterexampleBuilder":
        """Set random seed for determinism.
        
        Args:
            seed: Random seed
            
        Returns:
            Self for chaining
        """
        self._seed = seed
        return self
    
    def find_minimal(self, minimal: bool = True) -> "CounterexampleBuilder":
        """Set whether to minimize witness.
        
        Args:
            minimal: Whether to find minimal witness
            
        Returns:
            Self for chaining
        """
        self._find_minimal = minimal
        return self
    
    def budget(self, max_tests: int = 200, max_witness_size: int = 500) -> "CounterexampleBuilder":
        """Set resource budgets.
        
        Args:
            max_tests: Maximum violation tests during minimization
            max_witness_size: Maximum witness size (nodes)
            
        Returns:
            Self for chaining
        """
        self._budget_max_tests = max_tests
        self._budget_max_witness_size = max_witness_size
        return self
    
    def initial_radius(self, radius: int) -> "CounterexampleBuilder":
        """Set initial ego subgraph radius.
        
        Args:
            radius: Ego subgraph radius (default: 2)
            
        Returns:
            Self for chaining
        """
        self._initial_radius = radius
        return self
    
    def execute(self, network: Any) -> Optional[Any]:
        """Execute counterexample search.
        
        Args:
            network: py3plex multi_layer_network object
            
        Returns:
            Counterexample object if found, None otherwise
            
        Raises:
            CounterexampleNotFound: If no violation exists
        """
        from py3plex.counterexamples import find_counterexample
        from py3plex.counterexamples.types import Budget
        
        if self._claim_str is None:
            raise ValueError("Claim must be set before executing")
        
        budget = Budget(
            max_tests=self._budget_max_tests,
            max_witness_size=self._budget_max_witness_size,
        )
        
        return find_counterexample(
            network=network,
            claim_str=self._claim_str,
            params=self._params,
            layers=self._layers,
            seed=self._seed,
            find_minimal=self._find_minimal,
            budget=budget,
            initial_radius=self._initial_radius,
        )
    
    def _extract_layer_names(self, layer_ast: Any) -> List[str]:
        """Extract layer names from layer AST."""
        from .ast import LayerExpr, LayerTerm
        
        names = []
        if isinstance(layer_ast, LayerExpr):
            for term in layer_ast.terms:
                names.extend(self._extract_layer_names(term))
        elif isinstance(layer_ast, LayerTerm):
            names.append(layer_ast.name)
        return names


# ==============================================================================
# Claim Learning Builder
# ==============================================================================


class ClaimLearnerBuilder:
    """Builder for claim learning queries.
    
    Example:
        >>> from py3plex.dsl import Q
        >>> claims = (Q.learn_claims()
        ...             .from_metrics(["degree", "pagerank"])
        ...             .min_support(0.9)
        ...             .min_coverage(0.05)
        ...             .seed(42)
        ...             .execute(net))
    """
    
    def __init__(self):
        """Initialize claim learner builder."""
        self._metrics: List[str] = []
        self._layers: Optional[List[str]] = None
        self._min_support: float = 0.9
        self._min_coverage: float = 0.05
        self._max_antecedents: int = 1
        self._max_claims: int = 20
        self._seed: int = 42
        self._cheap_metrics: Optional[List[str]] = None
        self._target_metrics: Optional[List[str]] = None
    
    def from_metrics(self, metrics: List[str]) -> "ClaimLearnerBuilder":
        """Set metrics to use for claim learning.
        
        Args:
            metrics: List of metric names (e.g., ["degree", "pagerank"])
            
        Returns:
            Self for chaining
        """
        self._metrics = metrics
        return self
    
    def layers(self, layer_expr: Any) -> "ClaimLearnerBuilder":
        """Set layers to consider.
        
        Args:
            layer_expr: Layer expression (e.g., L["social"] + L["work"])
            
        Returns:
            Self for chaining
        """
        # Extract layer names from layer expression
        if hasattr(layer_expr, '_to_ast'):
            # LayerExprBuilder
            ast = layer_expr._to_ast()
            self._layers = self._extract_layer_names(ast)
        elif isinstance(layer_expr, list):
            self._layers = layer_expr
        else:
            self._layers = [str(layer_expr)]
        return self
    
    def min_support(self, support: float) -> "ClaimLearnerBuilder":
        """Set minimum support threshold.
        
        Args:
            support: Minimum support (default: 0.9)
            
        Returns:
            Self for chaining
        """
        self._min_support = support
        return self
    
    def min_coverage(self, coverage: float) -> "ClaimLearnerBuilder":
        """Set minimum coverage threshold.
        
        Args:
            coverage: Minimum coverage (default: 0.05)
            
        Returns:
            Self for chaining
        """
        self._min_coverage = coverage
        return self
    
    def max_antecedents(self, n: int) -> "ClaimLearnerBuilder":
        """Set maximum antecedent terms.
        
        MVP: Only 1 is supported. Validation happens at execution.
        
        Args:
            n: Maximum antecedent terms (must be 1 in MVP)
            
        Returns:
            Self for chaining
        """
        self._max_antecedents = n
        return self
    
    def max_claims(self, n: int) -> "ClaimLearnerBuilder":
        """Set maximum claims to return.
        
        Args:
            n: Maximum claims (default: 20)
            
        Returns:
            Self for chaining
        """
        self._max_claims = n
        return self
    
    def seed(self, seed: int) -> "ClaimLearnerBuilder":
        """Set random seed for determinism.
        
        Args:
            seed: Random seed (default: 42)
            
        Returns:
            Self for chaining
        """
        self._seed = seed
        return self
    
    def cheap_metrics(self, metrics: List[str]) -> "ClaimLearnerBuilder":
        """Set which metrics to use for antecedents.
        
        Args:
            metrics: List of metric names for antecedents
            
        Returns:
            Self for chaining
        """
        self._cheap_metrics = metrics
        return self
    
    def target_metrics(self, metrics: List[str]) -> "ClaimLearnerBuilder":
        """Set which metrics to use for consequents.
        
        Args:
            metrics: List of metric names for consequents
            
        Returns:
            Self for chaining
        """
        self._target_metrics = metrics
        return self
    
    def autocompute(self, enabled: bool = True) -> "ClaimLearnerBuilder":
        """Set whether to autocompute missing metrics.
        
        Note: This is a placeholder for future functionality.
        Currently, all metrics specified are computed.
        
        Args:
            enabled: Whether to autocompute (default: True)
            
        Returns:
            Self for chaining
        """
        # Placeholder for future functionality
        return self
    
    def execute(self, network: Any) -> List[Any]:
        """Execute claim learning.
        
        Args:
            network: py3plex multi_layer_network object
            
        Returns:
            List of Claim objects, sorted by rank
            
        Raises:
            ClaimLearningError: If learning fails
        """
        from py3plex.claims.learner import learn_claims
        
        if not self._metrics:
            from py3plex.claims.learner import ClaimLearningError
            raise ClaimLearningError(
                "No metrics specified",
                suggestions=["Call .from_metrics([...]) before .execute()"],
            )
        
        return learn_claims(
            network=network,
            metrics=self._metrics,
            layers=self._layers,
            min_support=self._min_support,
            min_coverage=self._min_coverage,
            max_antecedents=self._max_antecedents,
            max_claims=self._max_claims,
            seed=self._seed,
            cheap_metrics=self._cheap_metrics,
            target_metrics=self._target_metrics,
        )
    
    def _extract_layer_names(self, layer_ast: Any) -> List[str]:
        """Extract layer names from layer AST."""
        from .ast import LayerExpr, LayerTerm
        
        names = []
        if isinstance(layer_ast, LayerExpr):
            for term in layer_ast.terms:
                names.extend(self._extract_layer_names(term))
        elif isinstance(layer_ast, LayerTerm):
            names.append(layer_ast.name)
        return names



# =============================================================================
# Approximation Helper Functions
# =============================================================================

def _get_default_approx_method(measure_name: str) -> str:
    """Get default approximation method for a measure.
    
    Args:
        measure_name: Name of the measure
        
    Returns:
        Default approximation method name
        
    Raises:
        DslExecutionError: If measure doesn't have a default approx method
    """
    from .errors import DslExecutionError
    
    defaults = {
        "betweenness_centrality": "sampling",
        "betweenness": "sampling",
        "closeness_centrality": "landmarks",
        "closeness": "landmarks",
        "pagerank": "power_iteration",
    }
    
    method = defaults.get(measure_name)
    if method is None:
        raise DslExecutionError(
            f"No default approximation method for measure '{measure_name}'. "
            f"Please specify approx_method explicitly. "
            f"Available measures with default approx: {list(defaults.keys())}"
        )
    return method


def _validate_approx_params(measure_name: str, method: str, params: Dict[str, Any]) -> None:
    """Validate approximation parameters for a measure and method.
    
    Args:
        measure_name: Name of the measure
        method: Approximation method
        params: Approximation parameters
        
    Raises:
        DslExecutionError: If parameters are invalid
    """
    from .errors import DslExecutionError
    
    # Validate common parameters
    if "n_samples" in params:
        if not isinstance(params["n_samples"], int) or params["n_samples"] <= 0:
            raise DslExecutionError(
                f"Parameter 'n_samples' must be a positive integer, got {params['n_samples']}"
            )
    
    if "n_landmarks" in params:
        if not isinstance(params["n_landmarks"], int) or params["n_landmarks"] <= 0:
            raise DslExecutionError(
                f"Parameter 'n_landmarks' must be a positive integer, got {params['n_landmarks']}"
            )
    
    if "tol" in params:
        if not isinstance(params["tol"], (int, float)) or params["tol"] <= 0:
            raise DslExecutionError(
                f"Parameter 'tol' must be a positive number, got {params['tol']}"
            )
    
    if "max_iter" in params:
        if not isinstance(params["max_iter"], int) or params["max_iter"] <= 0:
            raise DslExecutionError(
                f"Parameter 'max_iter' must be a positive integer, got {params['max_iter']}"
            )
    
    if "sample_fraction" in params:
        frac = params["sample_fraction"]
        if not isinstance(frac, (int, float)) or frac <= 0 or frac > 1:
            raise DslExecutionError(
                f"Parameter 'sample_fraction' must be in (0, 1], got {frac}"
            )
    
    # Validate method-specific parameters
    if method == "sampling":
        # Betweenness sampling
        if measure_name in ["betweenness_centrality", "betweenness"]:
            if "n_samples" not in params:
                # This is OK - will use default
                pass
    
    elif method == "landmarks":
        # Closeness landmarks
        if measure_name in ["closeness_centrality", "closeness"]:
            if "n_landmarks" not in params:
                # This is OK - will use default
                pass
    
    elif method == "power_iteration":
        # PageRank power iteration
        if measure_name == "pagerank":
            if "tol" not in params and "max_iter" not in params:
                # This is OK - will use defaults
                pass
