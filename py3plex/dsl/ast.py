"""AST (Abstract Syntax Tree) definitions for DSL v2.

This module defines the core data structures that represent parsed DSL queries.
All query frontends (string DSL, builder API, dplyr-style) compile to these
AST nodes, which are then executed by the same engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Set
import json
import copy


class Target(Enum):
    """Query target - what to select from the network."""

    NODES = "nodes"
    EDGES = "edges"
    COMMUNITIES = "communities"


class ExportTarget(Enum):
    """Export target for query results."""

    PANDAS = "pandas"
    NETWORKX = "networkx"
    ARROW = "arrow"


@dataclass
class ExportSpec:
    """Specification for exporting query results to a file.

    Used to declaratively export results as part of the DSL pipeline.

    Attributes:
        path: Output file path
        fmt: Format type ('csv', 'json', 'tsv', etc.)
        columns: Optional list of columns to include/order
        options: Additional format-specific options (e.g., delimiter, orient)

    Example:
        ExportSpec(path='results.csv', fmt='csv', columns=['node', 'score'])
        ExportSpec(path='output.json', fmt='json', options={'orient': 'records'})
    """

    path: str
    fmt: str = "csv"
    columns: Optional[List[str]] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParamRef:
    """Reference to a query parameter.

    Parameters are placeholders in queries that are bound at execution time.

    Attributes:
        name: Parameter name (e.g., "k" for :k in DSL)
        type_hint: Optional type hint for validation
    """

    name: str
    type_hint: Optional[str] = None

    def __repr__(self) -> str:
        return f":{self.name}"


@dataclass
class LayerTerm:
    """A single layer reference in a layer expression.

    Attributes:
        name: Layer name (e.g., "social", "work")
    """

    name: str


@dataclass
class LayerExpr:
    """Layer expression with optional algebra operations.

    Supports:
        - Union: LAYER("a") + LAYER("b")
        - Difference: LAYER("a") - LAYER("b")
        - Intersection: LAYER("a") & LAYER("b")

    Attributes:
        terms: List of layer terms
        ops: List of operators between terms ('+', '-', '&')
    """

    terms: List[LayerTerm] = field(default_factory=list)
    ops: List[str] = field(default_factory=list)

    def get_layer_names(self) -> List[str]:
        """Get all layer names referenced in this expression."""
        return [term.name for term in self.terms]


# Value type for comparisons and function arguments
Value = Union[str, float, int, ParamRef]


@dataclass
class Comparison:
    """A comparison expression.

    Attributes:
        left: Attribute name (e.g., "degree", "layer")
        op: Comparison operator ('>', '>=', '<', '<=', '=', '!=')
        right: Value to compare against
    """

    left: str
    op: str
    right: Value


@dataclass
class FunctionCall:
    """A function call in a condition.

    Attributes:
        name: Function name (e.g., "reachable_from")
        args: List of arguments
    """

    name: str
    args: List[Value] = field(default_factory=list)


@dataclass
class SpecialPredicate:
    """Special multilayer predicates.

    Supported kinds:
        - 'intralayer': Edges within the same layer
        - 'interlayer': Edges between specific layers
        - 'motif': Motif pattern matching
        - 'reachable_from': Cross-layer reachability

    Attributes:
        kind: Predicate type
        params: Additional parameters for the predicate
    """

    kind: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionAtom:
    """A single atomic condition.

    Exactly one of comparison, function, or special should be non-None.

    Attributes:
        comparison: Simple comparison (e.g., degree > 5)
        function: Function call (e.g., reachable_from("Alice"))
        special: Special predicate (e.g., intralayer)
    """

    comparison: Optional[Comparison] = None
    function: Optional[FunctionCall] = None
    special: Optional[SpecialPredicate] = None

    @property
    def is_comparison(self) -> bool:
        return self.comparison is not None

    @property
    def is_function(self) -> bool:
        return self.function is not None

    @property
    def is_special(self) -> bool:
        return self.special is not None


@dataclass
class ConditionExpr:
    """Compound condition expression.

    Represents conditions joined by logical operators (AND, OR).

    Attributes:
        atoms: List of condition atoms
        ops: List of logical operators ('AND', 'OR') between atoms
    """

    atoms: List[ConditionAtom] = field(default_factory=list)
    ops: List[str] = field(default_factory=list)


@dataclass
class UQConfig:
    """Query-scoped uncertainty quantification configuration.

    This dataclass stores uncertainty estimation settings at the query level,
    providing defaults for all metrics computed in the query unless explicitly
    overridden on a per-metric basis.

    Attributes:
        method: Uncertainty estimation method ('bootstrap', 'perturbation', 'seed', 
                'null_model', 'stratified_perturbation')
        n_samples: Number of samples for uncertainty estimation
        ci: Confidence interval level (e.g., 0.95 for 95% CI)
        seed: Random seed for reproducibility
        mode: UQ execution mode ('summarize_only', 'propagate')
              - 'summarize_only': Current behavior, UQ computed per metric
              - 'propagate': Execute entire query per replicate, combine results
        keep_samples: Whether to keep raw samples in UQValue (None = auto)
        reduce: Reduction method ('empirical', 'gaussian')
                - 'empirical': Store full sample statistics
                - 'gaussian': Reduce to mean + std Gaussian approximation
        kwargs: Additional method-specific parameters (e.g., bootstrap_unit, bootstrap_mode,
                strata, bins for stratified_perturbation)

    Example:
        >>> uq = UQConfig(method="perturbation", n_samples=100, ci=0.95, seed=42)
        >>> uq = UQConfig(method="bootstrap", n_samples=200, ci=0.95,
        ...               kwargs={"bootstrap_unit": "edges", "bootstrap_mode": "resample"})
        >>> uq = UQConfig(method="stratified_perturbation", n_samples=100, ci=0.95, seed=42,
        ...               kwargs={"strata": ["degree", "layer"], "bins": {"degree": 5}})
        >>> uq = UQConfig(method="perturbation", n_samples=50, ci=0.95, seed=42,
        ...               mode="propagate", keep_samples=True, reduce="empirical")
    """

    method: Optional[str] = None
    n_samples: Optional[int] = None
    ci: Optional[float] = None
    seed: Optional[int] = None
    mode: str = "summarize_only"  # New: 'summarize_only' or 'propagate'
    keep_samples: Optional[bool] = None  # New: Whether to keep raw samples
    reduce: str = "empirical"  # New: 'empirical' or 'gaussian'
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApproximationSpec:
    """Specification for approximate computation of a measure.
    
    This allows fast, approximate versions of expensive centrality algorithms.
    
    Attributes:
        enabled: Whether approximation is enabled
        method: Approximation method name (e.g., "sampling", "landmarks", "power_iteration")
        params: Method-specific parameters (e.g., n_samples, n_landmarks, tol, max_iter, seed)
        diagnostics: Whether to compute per-node diagnostic information (e.g., stderr)
    """
    
    enabled: bool = False
    method: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    diagnostics: bool = False


@dataclass
class ComputeItem:
    """A measure to compute.

    Attributes:
        name: Measure name (e.g., 'betweenness_centrality')
        alias: Optional alias for the result (e.g., 'bc')
        uncertainty: Whether to compute uncertainty for this measure
        method: Uncertainty estimation method (e.g., 'bootstrap', 'perturbation', 'null_model')
        n_samples: Number of samples for uncertainty estimation
        ci: Confidence interval level (e.g., 0.95 for 95% CI)
        bootstrap_unit: What to resample for bootstrap: "edges", "nodes", or "layers"
        bootstrap_mode: Resampling mode: "resample" or "permute"
        n_null: Number of null model replicates
        null_model: Null model type: "degree_preserving", "erdos_renyi", "configuration"
        random_state: Random seed for reproducibility
        approx: Optional approximation specification for fast approximate computation
    """

    name: str
    alias: Optional[str] = None
    uncertainty: bool = False
    method: Optional[str] = None
    n_samples: Optional[int] = None
    ci: Optional[float] = None
    bootstrap_unit: Optional[str] = None
    bootstrap_mode: Optional[str] = None
    n_null: Optional[int] = None
    null_model: Optional[str] = None
    random_state: Optional[int] = None
    approx: Optional["ApproximationSpec"] = None

    @property
    def result_name(self) -> str:
        """Get the name to use in results (alias or original name)."""
        return self.alias if self.alias else self.name


@dataclass
class OrderItem:
    """Ordering specification.

    Attributes:
        key: Attribute or computed value to order by
        desc: True for descending order, False for ascending
    """

    key: str
    desc: bool = False


@dataclass
class TemporalContext:
    """Temporal context for time-based queries.

    This represents temporal constraints on a query, specified via AT or DURING clauses.

    Attributes:
        kind: Type of temporal constraint ("at" for point-in-time, "during" for interval)
        t0: Start time for interval queries (None for point-in-time)
        t1: End time for interval queries (None for point-in-time)
        range_name: Optional named range reference (e.g., "Q1_2023")

    Examples:
        >>> # Point-in-time: AT 1234567890
        >>> TemporalContext(kind="at", t0=1234567890.0, t1=1234567890.0)

        >>> # Time range: DURING [100, 200]
        >>> TemporalContext(kind="during", t0=100.0, t1=200.0)

        >>> # Named range: DURING RANGE "Q1_2023"
        >>> TemporalContext(kind="during", range_name="Q1_2023")
    """

    kind: str  # "at" or "during"
    t0: Optional[float] = None
    t1: Optional[float] = None
    range_name: Optional[str] = None


@dataclass
class WindowSpec:
    """Specification for sliding window iteration over temporal networks.

    This enables queries that operate over time windows, useful for
    streaming algorithms and temporal analysis.

    Attributes:
        window_size: Size of each time window (numeric or duration string)
        step: Step size between windows (defaults to window_size for non-overlapping)
        start: Optional start time for windowing
        end: Optional end time for windowing
        aggregation: How to aggregate results across windows ("list", "concat", "avg", etc.)

    Examples:
        >>> # Non-overlapping windows of size 100
        >>> WindowSpec(window_size=100.0)

        >>> # Overlapping windows: size 100, step 50
        >>> WindowSpec(window_size=100.0, step=50.0)

        >>> # Duration string (parsed later)
        >>> WindowSpec(window_size="7d", step="1d")
    """

    window_size: Union[float, str]
    step: Optional[Union[float, str]] = None
    start: Optional[float] = None
    end: Optional[float] = None
    aggregation: str = "list"  # "list", "concat", "avg", "sum", etc.


@dataclass
class ExplainSpec:
    """Specification for attaching explanations to query results.

    Explanations provide additional context for each result row (typically nodes),
    such as community membership, top neighbors, layer footprint, and attribution.

    Attributes:
        include: List of explanation blocks to compute (e.g., ["community", "top_neighbors", "attribution"])
        exclude: List of explanation blocks to exclude from defaults
        neighbors_top: Maximum number of neighbors to include in top_neighbors
        neighbors_cfg: Configuration for neighbor selection (metric, scope, direction)
        community_cfg: Configuration for community explanations
        layer_footprint_cfg: Configuration for layer footprint explanations
        attribution_cfg: Configuration for attribution explanations (Shapley values)
        cache: Whether to cache intermediate computations (default: True)
        as_columns: Store explanations as top-level columns (default: True)
        prefix: Optional prefix for explanation column names (default: "")

    Examples:
        >>> # Basic usage with defaults
        >>> ExplainSpec(include=["community", "top_neighbors"])

        >>> # Custom neighbor count
        >>> ExplainSpec(include=["top_neighbors"], neighbors_top=5)

        >>> # With attribution
        >>> ExplainSpec(
        ...     include=["attribution"],
        ...     attribution_cfg={"metric": "pagerank", "levels": ["layer"], "seed": 42}
        ... )
    """

    include: List[str] = field(
        default_factory=lambda: ["community", "top_neighbors", "layer_footprint"]
    )
    exclude: List[str] = field(default_factory=list)
    neighbors_top: int = 10
    neighbors_cfg: Dict[str, Any] = field(default_factory=dict)
    community_cfg: Dict[str, Any] = field(default_factory=dict)
    layer_footprint_cfg: Dict[str, Any] = field(default_factory=dict)
    attribution_cfg: Dict[str, Any] = field(default_factory=dict)
    cache: bool = True
    as_columns: bool = True
    prefix: str = ""


@dataclass
class CounterfactualSpec:
    """Specification for counterfactual robustness analysis.

    This represents a request to execute a query under controlled structural
    interventions to test the sensitivity of analytical conclusions.

    Attributes:
        intervention_type: Type of intervention ("remove_edges", "rewire", etc.)
        intervention_params: Parameters for the intervention
        repeats: Number of counterfactual runs
        seed: Random seed for reproducibility
        targets: Optional target specification for the intervention

    Examples:
        >>> # Quick robustness check with edge removal
        >>> CounterfactualSpec(
        ...     intervention_type="remove_edges",
        ...     intervention_params={"proportion": 0.05, "mode": "random"},
        ...     repeats=30,
        ...     seed=42
        ... )

        >>> # Degree-preserving rewiring
        >>> CounterfactualSpec(
        ...     intervention_type="rewire_degree_preserving",
        ...     intervention_params={"n_swaps": 100},
        ...     repeats=50,
        ...     seed=42
        ... )
    """

    intervention_type: str
    intervention_params: Dict[str, Any] = field(default_factory=dict)
    repeats: int = 30
    seed: Optional[int] = None
    targets: Optional[Any] = None


@dataclass
class SensitivitySpec:
    """Specification for query sensitivity analysis.

    Sensitivity analysis tests robustness of query conclusions (rankings, sets,
    communities) under controlled perturbations. This is DISTINCT from UQ:

    - UQ: Estimates uncertainty of METRIC VALUES (mean, std, CI)
    - Sensitivity: Assesses stability of CONCLUSIONS under perturbations

    Attributes:
        perturb: Perturbation method ('edge_drop', 'degree_preserving_rewire')
        grid: Perturbation strength grid (e.g., [0.0, 0.05, 0.1, 0.15, 0.2])
        n_samples: Number of samples per grid point for averaging
        seed: Random seed for reproducibility
        metrics: Stability metrics to compute (e.g., ['jaccard_at_k(20)', 'kendall_tau'])
        scope: Analysis scope ('global', 'per_node', 'per_layer')
        kwargs: Additional perturbation-specific parameters

    Example:
        SensitivitySpec(
            perturb='edge_drop',
            grid=[0.0, 0.05, 0.1, 0.15, 0.2],
            n_samples=30,
            seed=42,
            metrics=['jaccard_at_k(20)', 'kendall_tau'],
            scope='global'
        )
    """

    perturb: str
    grid: List[float]
    n_samples: int = 30
    seed: Optional[int] = None
    metrics: List[str] = field(default_factory=lambda: ["kendall_tau"])
    scope: str = "global"
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "perturb": self.perturb,
            "grid": self.grid,
            "n_samples": self.n_samples,
            "seed": self.seed,
            "metrics": self.metrics,
            "scope": self.scope,
            "kwargs": self.kwargs,
        }


@dataclass
class ContractSpec:
    """Specification for robustness contract (certification-grade).
    
    This represents a contract that ensures query conclusions are stable
    under perturbations. Unlike counterfactual analysis, contracts have:
    - Typed failure modes
    - Automatic predicate selection
    - Repair mechanisms
    - Deterministic reproducibility guarantees
    
    Attributes:
        contract: Robustness contract object from py3plex.contracts
    
    Examples:
        >>> from py3plex.contracts import Robustness
        >>> ContractSpec(contract=Robustness())
        >>> ContractSpec(contract=Robustness(n_samples=100, p_max=0.2))
    """
    contract: Any  # Robustness from py3plex.contracts


@dataclass
class AutoCommunityConfig:
    """Configuration for automatic community detection.
    
    Used by Q.communities().auto() and Q.nodes().community_auto() to specify
    parameters for automatic community detection algorithm selection.
    
    Attributes:
        enabled: Whether auto community detection is enabled
        kind: Type of query - "communities" (assignment table) or "nodes_join" (annotate nodes)
        seed: Random seed for reproducibility
        fast: Use fast mode with smaller parameter grids
        params: Additional parameters passed to auto_select_community
    """
    enabled: bool = False
    kind: str = "communities"  # "communities" or "nodes_join"
    seed: Optional[int] = None
    fast: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JoinNode:
    """A join operation between two query results.

    Represents a relational join between two query pipelines. Joins are
    row-wise relational joins, not graph merges.

    Attributes:
        left: Left query (SelectStmt or JoinNode)
        right: Right query (SelectStmt or JoinNode)
        on: Tuple of column names to join on
        how: Join type ('inner', 'left', 'right', 'outer', 'semi', 'anti')
        suffixes: Tuple of suffixes for name collisions (left_suffix, right_suffix)

    Example:
        >>> # Join nodes with communities
        >>> JoinNode(
        ...     left=SelectStmt(target=Target.NODES, ...),
        ...     right=SelectStmt(target=Target.COMMUNITIES, ...),
        ...     on=("node", "layer"),
        ...     how="left",
        ...     suffixes=("", "_comm")
        ... )
    """

    left: Union["SelectStmt", "JoinNode"]
    right: Union["SelectStmt", "JoinNode"]
    on: Tuple[str, ...]
    how: str = "inner"  # 'inner', 'left', 'right', 'outer', 'semi', 'anti'
    suffixes: Tuple[str, str] = ("", "_r")

    def requires_fields(self) -> set:
        """Get fields required by this join (join keys)."""
        return set(self.on)

    def provides_fields(self, left_fields: set, right_fields: set) -> set:
        """Get fields provided by this join.

        Args:
            left_fields: Fields from left query
            right_fields: Fields from right query

        Returns:
            Set of field names after join
        """
        if self.how in ("semi", "anti"):
            # Semi/anti joins only return left columns
            return left_fields

        # Determine which fields need suffixing
        collision_fields = left_fields & right_fields
        result_fields = set()

        # Add left fields
        for field in left_fields:
            if field in collision_fields and field not in self.on:
                result_fields.add(f"{field}{self.suffixes[0]}")
            else:
                result_fields.add(field)

        # Add right fields (except for join keys)
        for field in right_fields:
            if field in self.on:
                continue  # Join keys not duplicated
            if field in collision_fields:
                result_fields.add(f"{field}{self.suffixes[1]}")
            else:
                result_fields.add(field)

        return result_fields


@dataclass
class SelectStmt:
    """A SELECT statement.

    Attributes:
        target: What to select (nodes or edges)
        layer_expr: Optional layer expression for filtering
        where: Optional WHERE conditions
        compute: List of measures to compute
        order_by: List of ordering specifications
        limit: Optional limit on results
        export: Optional export target (for result format conversion)
        file_export: Optional file export specification (for writing to files)
        temporal_context: Optional temporal context for time-based queries
        window_spec: Optional window specification for sliding window analysis
        group_by: List of attribute names to group by (e.g., ["layer"])
        limit_per_group: Optional per-group limit for top-k filtering
        coverage_mode: Coverage filtering mode ("all", "any", "at_least", "exact", "fraction")
        coverage_k: Threshold for "at_least" or "exact" coverage modes
        coverage_p: Fraction threshold for "fraction" coverage mode
        coverage_group: Group attribute for coverage (defaults to primary grouping)
        coverage_id_field: Field to use for coverage identity (default: "id")
        select_cols: Optional list of columns to keep (for select() operation)
        drop_cols: Optional list of columns to drop (for drop() operation)
        rename_map: Optional mapping of old column names to new names
        summarize_aggs: Optional dict of name -> aggregation expression for summarize()
        distinct_cols: Optional list of columns for distinct operation
        rank_specs: Optional list of (attr, method) tuples for rank_by()
        zscore_attrs: Optional list of attributes to compute z-scores for
        post_filters: Optional list of filter specifications to apply after computation
        aggregate_specs: Optional dict of name -> aggregation spec for aggregate()
        mutate_specs: Optional dict of name -> transformation spec for mutate()
        autocompute: Whether to automatically compute missing metrics (default: True)
        uq_config: Optional query-scoped uncertainty quantification configuration
        counterfactual_spec: Optional counterfactual robustness specification
    """

    target: Target
    layer_expr: Optional[LayerExpr] = None
    layer_set: Optional[Any] = None  # LayerSet type (Any to avoid circular import)
    where: Optional[ConditionExpr] = None
    compute: List[ComputeItem] = field(default_factory=list)
    order_by: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None
    export: Optional[ExportTarget] = None
    file_export: Optional["ExportSpec"] = None
    temporal_context: Optional["TemporalContext"] = None
    window_spec: Optional["WindowSpec"] = None
    group_by: List[str] = field(default_factory=list)
    limit_per_group: Optional[int] = None
    coverage_mode: Optional[str] = None
    coverage_k: Optional[int] = None
    coverage_p: Optional[float] = None
    coverage_group: Optional[str] = None
    coverage_id_field: str = "id"
    select_cols: Optional[List[str]] = None
    drop_cols: Optional[List[str]] = None
    rename_map: Optional[Dict[str, str]] = None
    summarize_aggs: Optional[Dict[str, str]] = None
    distinct_cols: Optional[List[str]] = None
    rank_specs: Optional[List[Tuple[str, str]]] = None
    zscore_attrs: Optional[List[str]] = None
    post_filters: Optional[List[Dict[str, Any]]] = None
    aggregate_specs: Optional[Dict[str, Any]] = None
    mutate_specs: Optional[Dict[str, Any]] = None
    autocompute: bool = True
    uq_config: Optional["UQConfig"] = None
    explain_spec: Optional["ExplainSpec"] = None
    counterfactual_spec: Optional["CounterfactualSpec"] = None
    sensitivity_spec: Optional["SensitivitySpec"] = None
    contract_spec: Optional["ContractSpec"] = None
    auto_community_config: Optional["AutoCommunityConfig"] = None


@dataclass
class Query:
    """Top-level query representation.

    Attributes:
        explain: If True, return execution plan instead of results
        select: The SELECT statement
        dsl_version: DSL version for compatibility
    """

    explain: bool
    select: SelectStmt
    dsl_version: str = "2.0"


@dataclass
class PlanStep:
    """A step in the execution plan.

    Attributes:
        description: Human-readable description of the step
        estimated_complexity: Estimated time complexity (e.g., "O(|V|)")
    """

    description: str
    estimated_complexity: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Execution plan for EXPLAIN queries.

    Attributes:
        steps: List of execution steps
        warnings: List of performance or correctness warnings
    """

    steps: List[PlanStep] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ==============================================================================
# DSL Extensions: Multilayer Comparison (Part A)
# ==============================================================================


@dataclass
class CompareStmt:
    """COMPARE statement for network comparison.

    DSL Example:
        COMPARE NETWORK baseline, intervention
        USING multiplex_jaccard
        ON LAYER("offline") + LAYER("online")
        MEASURE global_distance
        TO pandas

    Attributes:
        network_a: Name/key for first network
        network_b: Name/key for second network
        metric_name: Comparison metric (e.g., "multiplex_jaccard")
        layer_expr: Optional layer expression for filtering
        measures: List of measure types (e.g., ["global_distance", "layerwise_distance"])
        export_target: Optional export format
    """

    network_a: str
    network_b: str
    metric_name: str
    layer_expr: Optional[LayerExpr] = None
    measures: List[str] = field(default_factory=list)
    export_target: Optional[str] = None


# ==============================================================================
# DSL Extensions: Null Models & Randomization (Part B)
# ==============================================================================


@dataclass
class NullModelStmt:
    """NULLMODEL statement for generating randomized networks.

    DSL Example:
        NULLMODEL configuration
        ON LAYER("social") + LAYER("work")
        WITH preserve_degree=True, preserve_layer_sizes=True
        SAMPLES 100
        SEED 42

    Attributes:
        model_type: Type of null model (e.g., "configuration", "erdos_renyi", "layer_shuffle")
        layer_expr: Optional layer expression for filtering
        params: Model parameters
        num_samples: Number of samples to generate
        seed: Optional random seed
        export_target: Optional export format
    """

    model_type: str
    layer_expr: Optional[LayerExpr] = None
    params: Dict[str, Any] = field(default_factory=dict)
    num_samples: int = 1
    seed: Optional[int] = None
    export_target: Optional[str] = None


# ==============================================================================
# DSL Extensions: Path Queries & Flow (Part C)
# ==============================================================================


@dataclass
class PathStmt:
    """PATH statement for path queries and flow analysis.

    DSL Example:
        PATH SHORTEST FROM "Alice" TO "Bob"
        ON LAYER("social") + LAYER("work")
        CROSSING LAYERS
        LIMIT 10

    Attributes:
        path_type: Type of path query ("shortest", "all", "random_walk", "flow")
        source: Source node identifier
        target: Optional target node identifier
        layer_expr: Optional layer expression for filtering
        cross_layer: Whether to allow cross-layer paths
        params: Additional parameters (e.g., max_length, teleport probability)
        limit: Optional limit on results
        export_target: Optional export format
    """

    path_type: str
    source: Union[str, ParamRef]
    target: Optional[Union[str, ParamRef]] = None
    layer_expr: Optional[LayerExpr] = None
    cross_layer: bool = False
    params: Dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = None
    export_target: Optional[str] = None


# ==============================================================================
# Extended Query: Top-level query with multiple statement types
# ==============================================================================


# ==============================================================================
# DSL Extensions: Dynamics & Trajectories (Part D)
# ==============================================================================


@dataclass
class DynamicsStmt:
    """DYNAMICS statement for declarative process simulation.

    DSL Example:
        DYNAMICS SIS WITH beta=0.3, mu=0.1
        ON LAYER("contacts") + LAYER("travel")
        SEED FROM nodes WHERE degree > 10
        PARAMETERS PER LAYER contacts: {beta=0.4}, travel: {beta=0.2}
        RUN FOR 100 STEPS, 10 REPLICATES
        TRACK prevalence, incidence

    Attributes:
        process_name: Name of the process (e.g., "SIS", "SIR", "RANDOM_WALK")
        params: Global process parameters (e.g., {"beta": 0.3, "mu": 0.1})
        layer_expr: Optional layer expression for filtering
        seed_query: Optional SELECT query for seeding initial conditions
        seed_fraction: Optional fraction for random seeding (e.g., 0.01 for 1%)
        layer_params: Optional per-layer parameter overrides
        steps: Number of simulation steps
        replicates: Number of independent runs
        track: List of measures to track (e.g., ["prevalence", "incidence"])
        seed: Optional random seed for reproducibility
        export_target: Optional export format
    """

    process_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    layer_expr: Optional[LayerExpr] = None
    seed_query: Optional[SelectStmt] = None
    seed_fraction: Optional[float] = None
    layer_params: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    steps: int = 100
    replicates: int = 1
    track: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    export_target: Optional[str] = None


@dataclass
class TrajectoriesStmt:
    """TRAJECTORIES statement for querying simulation results.

    DSL Example:
        TRAJECTORIES FROM process_result
        WHERE replicate = 5
        AT time = 50
        MEASURE peak_time, final_state
        ORDER BY node_id
        LIMIT 100

    Attributes:
        process_ref: Reference to a dynamics process or result
        where: Optional WHERE conditions on trajectories
        temporal_context: Optional temporal filtering (at specific time, during range)
        measures: List of trajectory measures to compute
        order_by: List of ordering specifications
        limit: Optional limit on results
        export_target: Optional export format
    """

    process_ref: str
    where: Optional[ConditionExpr] = None
    temporal_context: Optional[TemporalContext] = None
    measures: List[str] = field(default_factory=list)
    order_by: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None
    export_target: Optional[str] = None


@dataclass
class ExtendedQuery:
    """Extended query supporting multiple statement types.

    This extends the basic Query to support COMPARE, NULLMODEL, PATH, DYNAMICS,
    and TRAJECTORIES statements in addition to SELECT statements.

    Attributes:
        kind: Query type ("select", "compare", "nullmodel", "path", "dynamics", "trajectories", "semiring")
        explain: If True, return execution plan instead of results
        select: SELECT statement (if kind == "select")
        compare: COMPARE statement (if kind == "compare")
        nullmodel: NULLMODEL statement (if kind == "nullmodel")
        path: PATH statement (if kind == "path")
        dynamics: DYNAMICS statement (if kind == "dynamics")
        trajectories: TRAJECTORIES statement (if kind == "trajectories")
        semiring: SEMIRING statement (if kind == "semiring")
        dsl_version: DSL version for compatibility
    """

    kind: str
    explain: bool = False
    select: Optional[SelectStmt] = None
    compare: Optional[CompareStmt] = None
    nullmodel: Optional[NullModelStmt] = None
    path: Optional[PathStmt] = None
    dynamics: Optional[DynamicsStmt] = None
    trajectories: Optional[TrajectoriesStmt] = None
    semiring: Optional["SemiringStmt"] = None
    dsl_version: str = "2.0"


# ==============================================================================
# Semiring Algebra AST Nodes
# ==============================================================================


@dataclass
class SemiringSpecNode:
    """Semiring specification for algebra operations.

    Supports:
    - Single semiring: name or per_layer dict
    - Combined semirings: product or lexicographic combination

    Attributes:
        name: Semiring name (e.g., "min_plus", "boolean", "max_times")
        per_layer: Optional dict mapping layer -> semiring name
        combine_strategy: How to combine per-layer semirings ("product", "lexicographic")
    """

    name: Optional[str] = None
    per_layer: Optional[Dict[str, str]] = None
    combine_strategy: Optional[str] = None


@dataclass
class WeightLiftSpecNode:
    """Weight lifting specification for edge attribute extraction.

    Attributes:
        attr: Edge attribute name (e.g., "weight", "cost")
        transform: Optional transformation ("log", custom callable reference)
        default: Default value if attribute missing
        on_missing: Behavior on missing attribute ("default", "fail", "drop")
    """

    attr: Optional[str] = None
    transform: Optional[str] = None
    default: Any = 1.0
    on_missing: str = "default"


@dataclass
class CrossingLayersSpec:
    """Specification for cross-layer edge handling.

    Attributes:
        mode: Crossing mode ("allowed", "forbidden", "penalty")
        penalty: Optional penalty value (for "penalty" mode)
    """

    mode: str = "allowed"
    penalty: Optional[float] = None


@dataclass
class SemiringPathStmt:
    """SEMIRING PATH statement for path queries using semiring algebra.

    DSL Example:
        S.paths()
         .from_node("Alice")
         .to_node("Bob")
         .semiring("min_plus")
         .lift(attr="weight", default=1.0)
         .from_layers(L["social"] + L["work"])
         .crossing_layers(mode="allowed")
         .max_hops(5)
         .k_best(3)
         .witness(True)
         .backend("graph")

    Attributes:
        source: Source node identifier
        target: Optional target node identifier
        semiring_spec: Semiring specification
        lift_spec: Weight lifting specification
        layer_expr: Optional layer expression for filtering
        crossing_layers: Cross-layer edge handling
        max_hops: Optional maximum path length
        k_best: Optional number of best paths to find
        witness: Whether to track path witnesses
        backend: Backend selection ("graph", "matrix")
        uq_config: Optional uncertainty quantification config
    """

    source: Union[str, ParamRef]
    target: Optional[Union[str, ParamRef]] = None
    semiring_spec: SemiringSpecNode = field(
        default_factory=lambda: SemiringSpecNode(name="min_plus")
    )
    lift_spec: WeightLiftSpecNode = field(default_factory=WeightLiftSpecNode)
    layer_expr: Optional[LayerExpr] = None
    crossing_layers: CrossingLayersSpec = field(default_factory=CrossingLayersSpec)
    max_hops: Optional[int] = None
    k_best: Optional[int] = None
    witness: bool = False
    backend: str = "graph"
    uq_config: Optional[UQConfig] = None


@dataclass
class SemiringClosureStmt:
    """SEMIRING CLOSURE statement for transitive closure.

    DSL Example:
        S.closure()
         .semiring("boolean")
         .lift(attr="weight")
         .from_layers(L["social"])
         .backend("graph")

    Attributes:
        semiring_spec: Semiring specification
        lift_spec: Weight lifting specification
        layer_expr: Optional layer expression
        crossing_layers: Cross-layer edge handling
        method: Closure method ("auto", "floyd_warshall", "iterative")
        backend: Backend selection
        output_format: Output format ("sparse", "dense")
    """

    semiring_spec: SemiringSpecNode = field(
        default_factory=lambda: SemiringSpecNode(name="boolean")
    )
    lift_spec: WeightLiftSpecNode = field(default_factory=WeightLiftSpecNode)
    layer_expr: Optional[LayerExpr] = None
    crossing_layers: CrossingLayersSpec = field(default_factory=CrossingLayersSpec)
    method: str = "auto"
    backend: str = "graph"
    output_format: str = "sparse"


@dataclass
class SemiringFixedPointStmt:
    """SEMIRING FIXED_POINT statement for iterative computation.

    DSL Example:
        S.fixed_point()
         .operator("closure")
         .semiring("boolean")
         .max_iters(100)
         .tol(1e-6)

    Attributes:
        operator: Operator to iterate ("closure", custom)
        semiring_spec: Semiring specification
        lift_spec: Weight lifting specification
        layer_expr: Optional layer expression
        max_iters: Maximum iterations
        tol: Optional tolerance for convergence
    """

    operator: str = "closure"
    semiring_spec: SemiringSpecNode = field(
        default_factory=lambda: SemiringSpecNode(name="boolean")
    )
    lift_spec: WeightLiftSpecNode = field(default_factory=WeightLiftSpecNode)
    layer_expr: Optional[LayerExpr] = None
    max_iters: int = 100
    tol: Optional[float] = None


@dataclass
class SemiringStmt:
    """Top-level SEMIRING statement (union of path/closure/fixed_point).

    Attributes:
        operation: Operation type ("paths", "closure", "fixed_point")
        paths: Path statement (if operation == "paths")
        closure: Closure statement (if operation == "closure")
        fixed_point: Fixed-point statement (if operation == "fixed_point")
    """

    operation: str
    paths: Optional[SemiringPathStmt] = None
    closure: Optional[SemiringClosureStmt] = None
    fixed_point: Optional[SemiringFixedPointStmt] = None


# ==============================================================================
# Benchmark AST Nodes
# ==============================================================================


@dataclass
class BenchmarkAlgorithmSpec:
    """Specification for an algorithm in a benchmark.

    Supports:
    - Single config: ("leiden", {"gamma": 1.0})
    - Grid search: ("leiden", {"grid": {"gamma": [0.8, 1.0, 1.2]}})
    - AutoCommunity: ("autocommunity", {"mode": "pareto"})

    Attributes:
        algorithm: Algorithm name
        params: Parameters or grid specification
        config_id: Optional stable hash of configuration
    """

    algorithm: str
    params: Dict[str, Any] = field(default_factory=dict)
    config_id: Optional[str] = None


@dataclass
class BenchmarkProtocol:
    """Protocol specification for benchmark execution.

    Defines how algorithms should be evaluated: repeats, seeds, UQ, budgets.

    Attributes:
        repeat: Number of repeats per (dataset, layer) pair
        seed: Base seed for reproducibility
        uq_config: Optional UQ configuration
        budget_limit_ms: Optional time budget per unit
        budget_limit_evals: Optional eval budget per unit
        budget_per: Budgeting unit ("dataset", "repeat")
        n_jobs: Parallel jobs
    """

    repeat: int = 1
    seed: Optional[int] = None
    uq_config: Optional[UQConfig] = None
    budget_limit_ms: Optional[float] = None
    budget_limit_evals: Optional[int] = None
    budget_per: str = "repeat"
    n_jobs: int = 1


@dataclass
class BenchmarkNode:
    """AST node for benchmarking queries.

    Represents a benchmark comparing algorithms on datasets with a protocol.

    DSL Example:
        B.community()
         .on(dataset)
         .layers(L["social"])
         .algorithms(
             ("louvain", {"grid": {"resolution": [0.8, 1.0, 1.2]}}),
             ("autocommunity", {"mode": "pareto"}),
         )
         .metrics("modularity", "runtime_ms")
         .repeat(5, seed=42)
         .budget(runtime_ms=10_000)
         .select("wins")
         .execute()

    Attributes:
        benchmark_type: Type of benchmark ("community")
        datasets: Dataset specifications (name, network, or dict)
        layer_expr: Optional layer expression
        algorithm_specs: List of algorithm specifications
        metrics: List of metric names
        protocol: Execution protocol (repeats, seeds, budgets)
        selection_mode: How to select winners ("wins", "pareto", weighted)
        selection_weights: Optional weights for weighted selection
        return_trace: Whether to include AutoCommunity traces
        provenance: Provenance metadata
    """

    benchmark_type: str
    datasets: Any
    layer_expr: Optional[LayerExpr] = None
    algorithm_specs: List[BenchmarkAlgorithmSpec] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    protocol: BenchmarkProtocol = field(default_factory=BenchmarkProtocol)
    selection_mode: str = "wins"
    selection_weights: Optional[Dict[str, float]] = None
    return_trace: bool = True
    provenance: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# Benchmark AST Nodes
# ==============================================================================


@dataclass
class BenchmarkAlgorithmSpec:
    """Specification for an algorithm in a benchmark."""

    algorithm: str
    params: Dict[str, Any] = field(default_factory=dict)
    config_id: Optional[str] = None


@dataclass
class BenchmarkProtocol:
    """Protocol specification for benchmark execution."""

    repeat: int = 1
    seed: Optional[int] = None
    uq_config: Optional[UQConfig] = None
    budget_limit_ms: Optional[float] = None
    budget_limit_evals: Optional[int] = None
    budget_per: str = "repeat"
    n_jobs: int = 1


@dataclass
class BenchmarkNode:
    """AST node for benchmarking queries."""

    benchmark_type: str
    datasets: Any
    layer_expr: Optional[LayerExpr] = None
    algorithm_specs: List[BenchmarkAlgorithmSpec] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    protocol: BenchmarkProtocol = field(default_factory=BenchmarkProtocol)
    selection_mode: str = "wins"
    selection_weights: Optional[Dict[str, float]] = None
    return_trace: bool = True
    provenance: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# AST Canonicalization & Roundtrip Support
# ==============================================================================
# 
# This section implements the canonical AST representation that guarantees:
# 
#     canonical_ast(q.to_ast()) == canonical_ast(Q.from_ast(q.to_ast()).to_ast())
# 
# Two ASTs are considered equivalent if they have the same:
# - Target (nodes, edges, communities)
# - Layer algebra result (after resolution)
# - Filters (modulo commutative AND operations)
# - Computations (ignoring ordering where semantics are unaffected)
# - Grouping/aggregation semantics
# - UQ configuration (excluding volatile state)
# - Null model/dynamics/comparison semantics
#
# Canonicalization normalizes:
# - Commutative operations (sorts AND filters, layer unions, compute lists)
# - Default parameters (makes implicit explicit)
# - Numeric precision (stable float representation)
# - Field aliases (normalizes to canonical names)
# 
# Canonicalization preserves:
# - Semantic intent
# - Non-commutative operations
# - Provenance-relevant configuration (seeds, UQ params)
# ==============================================================================


def _normalize_float(value: float, precision: int = 10) -> float:
    """Normalize float to stable precision for canonical comparison.
    
    Args:
        value: Float value to normalize
        precision: Number of decimal places to retain
        
    Returns:
        Normalized float value
    """
    return round(value, precision)


def _sort_atoms_by_repr(atoms: List[ConditionAtom]) -> List[ConditionAtom]:
    """Sort condition atoms by their repr for canonical ordering.
    
    This enables stable ordering of commutative AND operations.
    
    Args:
        atoms: List of condition atoms
        
    Returns:
        Sorted list of atoms (by repr)
    """
    return sorted(atoms, key=lambda a: repr(a))


def _sort_compute_items(items: List[ComputeItem]) -> List[ComputeItem]:
    """Sort compute items by name for canonical ordering.
    
    Args:
        items: List of compute items
        
    Returns:
        Sorted list (by name)
    """
    return sorted(items, key=lambda c: c.name)


def _canonicalize_value(value: Value) -> Value:
    """Canonicalize a value (string, float, int, or ParamRef).
    
    Args:
        value: Value to canonicalize
        
    Returns:
        Canonicalized value
    """
    if isinstance(value, float):
        return _normalize_float(value)
    return value


def _canonicalize_comparison(comp: Comparison) -> Comparison:
    """Canonicalize a Comparison node.
    
    Args:
        comp: Comparison to canonicalize
        
    Returns:
        Canonicalized Comparison
    """
    return Comparison(
        left=comp.left,
        op=comp.op,
        right=_canonicalize_value(comp.right)
    )


def _canonicalize_condition_atom(atom: ConditionAtom) -> ConditionAtom:
    """Canonicalize a ConditionAtom node.
    
    Args:
        atom: Atom to canonicalize
        
    Returns:
        Canonicalized ConditionAtom
    """
    if atom.comparison:
        return ConditionAtom(comparison=_canonicalize_comparison(atom.comparison))
    if atom.function:
        return ConditionAtom(function=atom.function)
    if atom.special:
        return ConditionAtom(special=atom.special)
    return atom


def _canonicalize_condition_expr(cond: Optional[ConditionExpr]) -> Optional[ConditionExpr]:
    """Canonicalize a ConditionExpr by sorting commutative atoms.
    
    For AND operations, atoms are commutative and can be reordered.
    For mixed AND/OR, we preserve the original structure to maintain semantics.
    
    Args:
        cond: Condition expression to canonicalize
        
    Returns:
        Canonicalized ConditionExpr or None
    """
    if cond is None:
        return None
    
    # Canonicalize each atom
    canonical_atoms = [_canonicalize_condition_atom(atom) for atom in cond.atoms]
    
    # If all operations are AND (commutative), sort the atoms
    all_and = all(op == "AND" for op in cond.ops)
    if all_and:
        canonical_atoms = _sort_atoms_by_repr(canonical_atoms)
    
    return ConditionExpr(atoms=canonical_atoms, ops=list(cond.ops))


def _canonicalize_compute_item(item: ComputeItem) -> ComputeItem:
    """Canonicalize a ComputeItem by normalizing its parameters.
    
    Args:
        item: ComputeItem to canonicalize
        
    Returns:
        Canonicalized ComputeItem
    """
    return ComputeItem(
        name=item.name,
        alias=item.alias,
        uncertainty=item.uncertainty,
        method=item.method,
        n_samples=item.n_samples,
        ci=_normalize_float(item.ci) if item.ci is not None else None,
        bootstrap_unit=item.bootstrap_unit,
        bootstrap_mode=item.bootstrap_mode,
        n_null=item.n_null,
        null_model=item.null_model,
        random_state=item.random_state,
    )


def _canonicalize_uq_config(uq: Optional[UQConfig]) -> Optional[UQConfig]:
    """Canonicalize UQConfig by normalizing numeric values.
    
    Args:
        uq: UQConfig to canonicalize
        
    Returns:
        Canonicalized UQConfig or None
    """
    if uq is None:
        return None
    
    return UQConfig(
        method=uq.method,
        n_samples=uq.n_samples,
        ci=_normalize_float(uq.ci) if uq.ci is not None else None,
        seed=uq.seed,
        kwargs=dict(uq.kwargs),
    )


def _canonicalize_select_stmt(select: SelectStmt) -> SelectStmt:
    """Canonicalize a SelectStmt.
    
    This normalizes all sub-components while preserving semantic intent.
    
    Args:
        select: SelectStmt to canonicalize
        
    Returns:
        Canonicalized SelectStmt
    """
    # Sort compute items for stable ordering (computes are order-independent)
    canonical_compute = _sort_compute_items([_canonicalize_compute_item(c) for c in select.compute])
    
    # Canonicalize WHERE conditions
    canonical_where = _canonicalize_condition_expr(select.where)
    
    # Canonicalize UQ config
    canonical_uq = _canonicalize_uq_config(select.uq_config)
    
    # Create canonicalized SelectStmt
    return SelectStmt(
        target=select.target,
        layer_expr=select.layer_expr,
        layer_set=select.layer_set,
        where=canonical_where,
        compute=canonical_compute,
        order_by=list(select.order_by),  # Order matters for ORDER BY
        limit=select.limit,
        export=select.export,
        file_export=select.file_export,
        temporal_context=select.temporal_context,
        window_spec=select.window_spec,
        group_by=sorted(select.group_by) if select.group_by else [],  # Sort group_by for stability
        limit_per_group=select.limit_per_group,
        coverage_mode=select.coverage_mode,
        coverage_k=select.coverage_k,
        coverage_p=_normalize_float(select.coverage_p) if select.coverage_p is not None else None,
        coverage_group=select.coverage_group,
        coverage_id_field=select.coverage_id_field,
        select_cols=sorted(select.select_cols) if select.select_cols else None,
        drop_cols=sorted(select.drop_cols) if select.drop_cols else None,
        rename_map=dict(select.rename_map) if select.rename_map else None,
        summarize_aggs=dict(select.summarize_aggs) if select.summarize_aggs else None,
        distinct_cols=sorted(select.distinct_cols) if select.distinct_cols else None,
        rank_specs=list(select.rank_specs) if select.rank_specs else None,
        zscore_attrs=sorted(select.zscore_attrs) if select.zscore_attrs else None,
        post_filters=list(select.post_filters) if select.post_filters else None,
        aggregate_specs=dict(select.aggregate_specs) if select.aggregate_specs else None,
        mutate_specs=dict(select.mutate_specs) if select.mutate_specs else None,
        autocompute=select.autocompute,
        uq_config=canonical_uq,
        explain_spec=select.explain_spec,
        counterfactual_spec=select.counterfactual_spec,
        sensitivity_spec=select.sensitivity_spec,
        contract_spec=select.contract_spec,
        auto_community_config=select.auto_community_config,
    )


def canonicalize_ast(query: Query) -> Query:
    """Canonicalize an AST for stable comparison and hashing.
    
    The canonical form:
    - Sorts commutative operations (AND filters, compute lists)
    - Normalizes numeric precision
    - Preserves semantic intent and non-commutative operations
    
    This is the single source of truth for AST equivalence.
    
    Args:
        query: Query AST to canonicalize
        
    Returns:
        Canonicalized Query AST (deep copy)
        
    Example:
        >>> ast1 = Q.nodes().where(degree__gt=5.0001).compute("degree", "betweenness").to_ast()
        >>> ast2 = Q.nodes().where(degree__gt=5.0002).compute("betweenness", "degree").to_ast()
        >>> canonical_ast1 = canonicalize_ast(ast1)
        >>> canonical_ast2 = canonicalize_ast(ast2)
        >>> # canonical_ast1 == canonical_ast2 (up to float precision)
    """
    return Query(
        explain=query.explain,
        select=_canonicalize_select_stmt(query.select),
        dsl_version=query.dsl_version,
    )


def ast_equals(ast1: Query, ast2: Query) -> bool:
    """Check if two ASTs are semantically equivalent.
    
    Uses canonical comparison: canonicalize both ASTs and compare.
    
    Args:
        ast1: First AST
        ast2: Second AST
        
    Returns:
        True if ASTs are equivalent, False otherwise
        
    Example:
        >>> ast1 = Q.nodes().compute("degree", "betweenness").to_ast()
        >>> ast2 = Q.nodes().compute("betweenness", "degree").to_ast()
        >>> ast_equals(ast1, ast2)  # True (compute order doesn't matter)
    """
    canonical1 = canonicalize_ast(ast1)
    canonical2 = canonicalize_ast(ast2)
    return canonical1 == canonical2


def ast_diff(ast1: Query, ast2: Query) -> Dict[str, Any]:
    """Compute semantic difference between two ASTs.
    
    Returns a structured diff showing what differs between canonical forms.
    
    Args:
        ast1: First AST
        ast2: Second AST
        
    Returns:
        Dictionary with diff information:
        - 'equal': True if ASTs are equivalent
        - 'target_diff': Difference in target (if any)
        - 'layer_diff': Difference in layers (if any)
        - 'where_diff': Difference in conditions (if any)
        - 'compute_diff': Difference in computations (if any)
        - 'other_diffs': List of other differences
        
    Example:
        >>> ast1 = Q.nodes().where(degree__gt=5).to_ast()
        >>> ast2 = Q.nodes().where(degree__gt=10).to_ast()
        >>> diff = ast_diff(ast1, ast2)
        >>> diff['where_diff']  # Shows difference in WHERE clause
    """
    canonical1 = canonicalize_ast(ast1)
    canonical2 = canonicalize_ast(ast2)
    
    if canonical1 == canonical2:
        return {'equal': True}
    
    diff_result = {'equal': False}
    
    # Compare targets
    if canonical1.select.target != canonical2.select.target:
        diff_result['target_diff'] = {
            'ast1': canonical1.select.target,
            'ast2': canonical2.select.target,
        }
    
    # Compare layers
    if canonical1.select.layer_expr != canonical2.select.layer_expr:
        diff_result['layer_diff'] = {
            'ast1': canonical1.select.layer_expr,
            'ast2': canonical2.select.layer_expr,
        }
    
    # Compare WHERE conditions
    if canonical1.select.where != canonical2.select.where:
        diff_result['where_diff'] = {
            'ast1': repr(canonical1.select.where),
            'ast2': repr(canonical2.select.where),
        }
    
    # Compare compute items
    if canonical1.select.compute != canonical2.select.compute:
        diff_result['compute_diff'] = {
            'ast1': [c.name for c in canonical1.select.compute],
            'ast2': [c.name for c in canonical2.select.compute],
        }
    
    # Collect other differences
    other_diffs = []
    if canonical1.select.order_by != canonical2.select.order_by:
        other_diffs.append('order_by')
    if canonical1.select.limit != canonical2.select.limit:
        other_diffs.append('limit')
    if canonical1.select.group_by != canonical2.select.group_by:
        other_diffs.append('group_by')
    if canonical1.select.uq_config != canonical2.select.uq_config:
        other_diffs.append('uq_config')
    
    if other_diffs:
        diff_result['other_diffs'] = other_diffs
    
    return diff_result


def ast_to_json(query: Query, canonical: bool = True) -> str:
    """Serialize AST to JSON.
    
    Args:
        query: Query AST to serialize
        canonical: If True, canonicalize before serialization
        
    Returns:
        JSON string representation
        
    Example:
        >>> ast = Q.nodes().where(degree__gt=5).to_ast()
        >>> json_str = ast_to_json(ast)
        >>> # Can be deserialized with ast_from_json()
    """
    if canonical:
        query = canonicalize_ast(query)
    
    def _serialize(obj):
        """Convert dataclass to dict recursively."""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [_serialize(item) for item in obj]
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        if hasattr(obj, '__dataclass_fields__'):
            # Dataclass
            result = {'__type__': obj.__class__.__name__}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                result[field_name] = _serialize(value)
            return result
        if isinstance(obj, Enum):
            return {'__enum__': obj.__class__.__name__, 'value': obj.value}
        # Fallback
        return str(obj)
    
    data = _serialize(query)
    data['__schema_version__'] = '2.0'
    return json.dumps(data, indent=2, sort_keys=True)


def ast_from_json(json_str: str) -> Query:
    """Deserialize AST from JSON.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Query AST
        
    Raises:
        ValueError: If JSON is invalid or schema version is incompatible
        
    Example:
        >>> ast = Q.nodes().where(degree__gt=5).to_ast()
        >>> json_str = ast_to_json(ast)
        >>> reconstructed = ast_from_json(json_str)
        >>> ast_equals(ast, reconstructed)  # True
    """
    data = json.loads(json_str)
    
    # Check schema version
    schema_version = data.get('__schema_version__')
    if schema_version != '2.0':
        raise ValueError(f"Incompatible schema version: {schema_version} (expected 2.0)")
    
    # Remove schema version marker
    data.pop('__schema_version__', None)
    
    def _deserialize(obj, target_type=None):
        """Convert dict back to dataclass recursively."""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, list):
            return [_deserialize(item) for item in obj]
        if isinstance(obj, dict):
            if '__enum__' in obj:
                # Reconstruct enum
                enum_name = obj['__enum__']
                enum_value = obj['value']
                # Find enum class
                if enum_name == 'Target':
                    return Target(enum_value)
                if enum_name == 'ExportTarget':
                    return ExportTarget(enum_value)
                # Add more enums as needed
                return enum_value
            if '__type__' in obj:
                # Reconstruct dataclass
                type_name = obj['__type__']
                obj_data = {k: v for k, v in obj.items() if k != '__type__'}
                
                # Find dataclass type
                type_map = {
                    'Query': Query,
                    'SelectStmt': SelectStmt,
                    'LayerExpr': LayerExpr,
                    'LayerTerm': LayerTerm,
                    'ConditionExpr': ConditionExpr,
                    'ConditionAtom': ConditionAtom,
                    'Comparison': Comparison,
                    'FunctionCall': FunctionCall,
                    'SpecialPredicate': SpecialPredicate,
                    'ComputeItem': ComputeItem,
                    'OrderItem': OrderItem,
                    'ParamRef': ParamRef,
                    'UQConfig': UQConfig,
                    'TemporalContext': TemporalContext,
                    'WindowSpec': WindowSpec,
                    'ExportSpec': ExportSpec,
                    'ExplainSpec': ExplainSpec,
                    'SensitivitySpec': SensitivitySpec,
                    'CounterfactualSpec': CounterfactualSpec,
                    'ContractSpec': ContractSpec,
                    'AutoCommunityConfig': AutoCommunityConfig,
                }
                
                target_class = type_map.get(type_name)
                if target_class is None:
                    raise ValueError(f"Unknown type: {type_name}")
                
                # Recursively deserialize fields
                deserialized_data = {}
                for field_name, field_value in obj_data.items():
                    deserialized_data[field_name] = _deserialize(field_value)
                
                return target_class(**deserialized_data)
            # Regular dict
            return {k: _deserialize(v) for k, v in obj.items()}
        return obj
    
    return _deserialize(data)
