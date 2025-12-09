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

from typing import Any, Dict, List, Optional, Union

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
        
        Returns:
            Self for chaining
            
        Example:
            >>> Q.nodes().per_layer().top_k(5, "betweenness_centrality")
        """
        return self.group_by("layer")
    
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
                - "at_least": Keep items that appear in at least k groups (requires k parameter)
                - "exact": Keep items that appear in exactly k groups (requires k parameter)
                - "fraction": Keep items that appear in at least p fraction (0-1) of groups (requires p parameter)
            k: Threshold for "at_least" or "exact" modes
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
            
            >>> # Nodes in top-10 in at least 70% of layers (0.7 fraction)
            >>> Q.nodes().per_layer().top_k(10, "degree").coverage(mode="fraction", p=0.7)
        """
        allowed_modes = {"all", "any", "at_least", "exact", "fraction"}
        if mode not in allowed_modes:
            raise ValueError(
                f"Unknown coverage mode: {mode}. "
                f"Allowed modes: {', '.join(sorted(allowed_modes))}"
            )
        
        if mode in {"at_least", "exact"} and k is None:
            raise ValueError(f"coverage(mode='{mode}') requires k parameter")
        
        if mode == "fraction" and p is None:
            raise ValueError(f"coverage(mode='fraction') requires p parameter")
        
        if p is not None and (p < 0 or p > 1):
            raise ValueError(f"coverage fraction p must be in range [0, 1], got {p}")
        
        # Validate that grouping is set up
        if not self._select.group_by:
            raise ValueError(
                "coverage() requires grouping. Call .group_by() or .per_layer() first."
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
