"""AST (Abstract Syntax Tree) definitions for DSL v2.

This module defines the core data structures that represent parsed DSL queries.
All query frontends (string DSL, builder API, dplyr-style) compile to these
AST nodes, which are then executed by the same engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class Target(Enum):
    """Query target - what to select from the network."""
    NODES = "nodes"
    EDGES = "edges"


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
        method: Uncertainty estimation method ('bootstrap', 'perturbation', 'seed', 'null_model')
        n_samples: Number of samples for uncertainty estimation
        ci: Confidence interval level (e.g., 0.95 for 95% CI)
        seed: Random seed for reproducibility
        kwargs: Additional method-specific parameters (e.g., bootstrap_unit, bootstrap_mode)
    
    Example:
        >>> uq = UQConfig(method="perturbation", n_samples=100, ci=0.95, seed=42)
        >>> uq = UQConfig(method="bootstrap", n_samples=200, ci=0.95, 
        ...               kwargs={"bootstrap_unit": "edges", "bootstrap_mode": "resample"})
    """
    method: Optional[str] = None
    n_samples: Optional[int] = None
    ci: Optional[float] = None
    seed: Optional[int] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)


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
    """
    target: Target
    layer_expr: Optional[LayerExpr] = None
    layer_set: Optional[Any] = None  # LayerSet type (Any to avoid circular import)
    where: Optional[ConditionExpr] = None
    compute: List[ComputeItem] = field(default_factory=list)
    order_by: List[OrderItem] = field(default_factory=list)
    limit: Optional[int] = None
    export: Optional[ExportTarget] = None
    file_export: Optional['ExportSpec'] = None
    temporal_context: Optional['TemporalContext'] = None
    window_spec: Optional['WindowSpec'] = None
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
    uq_config: Optional['UQConfig'] = None


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
        kind: Query type ("select", "compare", "nullmodel", "path", "dynamics", "trajectories")
        explain: If True, return execution plan instead of results
        select: SELECT statement (if kind == "select")
        compare: COMPARE statement (if kind == "compare")
        nullmodel: NULLMODEL statement (if kind == "nullmodel")
        path: PATH statement (if kind == "path")
        dynamics: DYNAMICS statement (if kind == "dynamics")
        trajectories: TRAJECTORIES statement (if kind == "trajectories")
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
    dsl_version: str = "2.0"
