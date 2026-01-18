# py3plex AI Agent Documentation

> **Mission**: Make this single markdown file fully self-sufficient for an LLM agent to design correct, reproducible, performant py3plex pipelines end-to-end (discover → decide → build → validate → export) without guessing or hallucinating APIs.

**What this document is**:
- An operational playbook (not just API docs)
- A decision guide (when to use what)
- A set of known-good pipeline blueprints ("Golden Paths")
- A reproducibility + performance policy manual

**Version**: py3plex 1.1.2 | DSL v2.1 | Python 3.8+

---

## Table of Contents

1. [Quick Start: Golden Paths](#quick-start-golden-paths)
2. [DSL v2 (Q / UQ / L) — Complete Reference](#dsl-v2-q-uq-l--complete-reference)
3. [Decision Guide: Which API When?](#decision-guide-which-api-when)
4. [Legacy DSL (String-Based)](#legacy-dsl-string-based)
5. [Dplyr-Style Operations](#dplyr-style-operations)
6. [Pipeline API (Sklearn-Style)](#pipeline-api-sklearn-style)
7. [I/O and Data Loading](#io-and-data-loading)
8. [Dynamics Simulations](#dynamics-simulations)
9. [Uncertainty Quantification](#uncertainty-quantification)
10. [Temporal Networks](#temporal-networks)
11. [Null Models and Statistical Testing](#null-models-and-statistical-testing)
12. [Counterexample Generation](#counterexample-generation)
13. [Claim Learning (Hypothesis Discovery)](#claim-learning-hypothesis-discovery)
14. [Semiring Algebra (Paths, Closure, Fixed-Point)](#semiring-algebra-paths-closure-fixed-point)
15. [Community Detection and Queries](#community-detection-and-queries)
16. [Pattern Matching (Cypher-like)](#pattern-matching-cypher-like)
17. [Network Comparison and Diff](#network-comparison-and-diff)
18. [CLI Tool](#cli-tool)
19. [Plugin System](#plugin-system)
20. [Configuration and Profiling](#configuration-and-profiling)
21. [Exception Hierarchy](#exception-hierarchy)
22. [Query Planner and Optimization](#query-planner-and-optimization)
23. [Performance Guidelines](#performance-guidelines)
24. [Reproducibility Policy](#reproducibility-policy)
25. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
26. [Testing Strategy](#testing-strategy)
27. [File Locations](#file-locations)

---

## Quick Start: Golden Paths

### Path 1: Network Analysis from CSV

```python
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Load network
net = multinet.multi_layer_network(directed=False)
net.load_network("network.csv", input_type="edgelist")

# Query: Top hubs in each layer
result = (
    Q.nodes()
     .from_layers(L["*"])  # All layers
     .compute("degree", "betweenness_centrality")
     .per_layer()
       .top_k(10, "degree")
     .end_grouping()
     .execute(net)
)

# Export
df = result.to_pandas()
df.to_csv("hubs.csv", index=False)
```

### Path 2: Uncertainty-Aware Centrality

```python
from py3plex.dsl import Q, L, UQ

# Compute with uncertainty
result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .compute("pagerank", "betweenness_centrality")
     .uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
     .execute(net)
)

# Get confidence intervals
df = result.to_pandas(expand_uncertainty=True)
print(df[["node", "pagerank", "pagerank_ci95_low", "pagerank_ci95_high"]])
```

### Path 3: Temporal Network Analysis

```python
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.dsl import Q

# Create temporal network
tnet = TemporalMultiLayerNetwork()
tnet.add_edge('A', 'B', layer='social', t_start=100.0, t_end=200.0)
# ... add more edges

# Query specific time window
result = (
    Q.edges()
     .during(100.0, 150.0)
     .from_layers(L["social"])
     .execute(tnet)
)
```

### Path 4: Dynamics Simulation

```python
from py3plex.dsl import Q, L

# Run SIS epidemic
sim = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .on_layers(L["contacts"])
     .seed_infections(0.01)  # 1% initial infections
     .run(steps=100, replicates=10)
     .execute(net)
)

# Extract peak time
trajectories = sim.trajectories
peak_time = trajectories['infected'].idxmax()
```

### Path 5: Hypothesis Testing with Counterexamples

```python
from py3plex.dsl import Q

# Learn claims from data
claims = (
    Q.learn_claims()
     .from_metrics(["degree", "pagerank", "betweenness_centrality"])
     .min_support(0.9)
     .min_coverage(0.05)
     .seed(42)
     .execute(net)
)

# Test each claim for counterexamples
for claim in claims[:5]:
    cex = claim.counterexample(net, seed=42)
    if cex:
        print(f" {claim.claim_string}: counterexample found")
    else:
        print(f" {claim.claim_string}: no counterexample (support={claim.support:.3f})")
```

---

## DSL v2 — Formal Specification

This section provides a normative, implementation-faithful specification of DSL v2. All behavior is specified using RFC 2119 keywords (MUST, MUST NOT, SHOULD, MAY).

---

### 1. DSL v2 Design Goals (Normative)

DSL v2 MUST satisfy the following design requirements:

1. **Lazy Evaluation**: All builder methods MUST return builder objects without executing queries. Only `.execute(network)` MAY trigger execution.

2. **Composability**: Builder methods MUST return `self` (or compatible builder type) to enable method chaining.

3. **Type Safety**: All builder methods MUST accept type-hinted parameters. Implementations SHOULD validate types at runtime.

4. **Determinism**: Identical queries with identical parameters and networks MUST produce identical results when `seed` is specified.

5. **Multilayer Native**: All constructs MUST support multilayer networks without explicit flattening.

6. **AST-Based**: All frontends (builder API, string DSL) MUST compile to the same AST representation defined in `py3plex.dsl.ast`.

7. **Error Reporting**: All errors MUST use the exception hierarchy in `py3plex.dsl.errors` with actionable messages.

8. **Backward Compatibility**: DSL v2 MUST NOT break existing DSL v1 (string-based) queries.

---

### 2. Core Abstractions

#### 2.1 Query Builder (`QueryBuilder`)

**Location**: `py3plex.dsl.builder.QueryBuilder`

**Lifecycle**:
1. **Construction**: Created via factory methods (`Q.nodes()`, `Q.edges()`, `Q.communities()`)
2. **Configuration**: Modified via chainable methods (`.where()`, `.compute()`, etc.)
3. **Compilation**: Converted to AST via `.to_ast()` (explicit) or `.execute()` (implicit)
4. **Execution**: Executed via `.execute(network, **params)` → returns `QueryResult`

**Mutability**: Builder objects are MUTABLE. Each method call modifies the internal `_select` AST node and returns `self`.

**Immutability Guarantee**: Calling `.to_ast()` MUST create a deep copy of the internal AST to prevent external mutation.

**Serialization**: Builders MUST be serializable via `.to_ast()` followed by AST serialization.

#### 2.2 Abstract Syntax Tree (AST)

**Location**: `py3plex.dsl.ast`

**Purpose**: Canonical representation of all DSL queries, independent of frontend syntax.

**Top-Level Nodes**:
- `Query`: Root query node (contains `SelectStmt` or `explain=True` flag)
- `SelectStmt`: SELECT query (target, layers, conditions, computations, ordering, limits, grouping, etc.)
- `CompareStmt`: Network comparison query
- `NullModelStmt`: Null model generation query
- `PathStmt`: Path finding query
- `DynamicsStmt`: Dynamics simulation query
- `TrajectoriesStmt`: Trajectory sampling query
- `SemiringPathStmt`: Semiring path algebra query
- `SemiringClosureStmt`: Semiring closure query

**Immutability**: All AST nodes MUST be dataclasses with `frozen=False` (to allow field assignment during the construction phase). However, implementations MUST treat AST nodes as immutable after construction is complete - no fields should be modified after a node is returned from a builder method. This is a convention-based immutability pattern where the dataclass is technically mutable but mutation is only allowed during the building process.

**Serialization**: All AST nodes MUST support JSON serialization via `dataclasses.asdict()` with custom handling for:
- `ParamRef` → `{"__type__": "ParamRef", "name": "...", "type_hint": "..."}`
- `LayerSet` → `{"__type__": "LayerSet", "expr": "..."}`

#### 2.3 Query Result (`QueryResult`)

**Location**: `py3plex.dsl.result.QueryResult`

**Attributes**:
- `target`: `str` - "nodes" or "edges"
- `items`: `List[Any]` - List of node/edge identifiers
- `attributes`: `Dict[str, Union[List[Any], Dict[Any, Any]]]` - Computed attributes (column → values)
- `meta`: `Dict[str, Any]` - Execution metadata (provenance, grouping, etc.)
- `computed_metrics`: `Set[str]` - Set of metrics computed during execution
- `sensitivity_result`: `Optional[SensitivityResult]` - Sensitivity analysis results if requested

**Export Methods**:
- `to_pandas(expand_uncertainty=False, ci_level=0.95, expand_explanations=False)` → `pd.DataFrame`
- `to_networkx()` → `nx.Graph` or `nx.MultiGraph`
- `to_arrow()` → `pa.Table`
- `to_json()` → `str` (JSON string)
- `to_csv(path, **kwargs)` → `None` (writes to file)

**Provenance Methods**:
- `provenance` → `Optional[Dict[str, Any]]` - Get provenance dictionary
- `is_replayable` → `bool` - Check if result has replayable provenance
- `replay(strict=True)` → `QueryResult` - Replay query from provenance

**Grouping Methods**:
- `group_summary()` → `pd.DataFrame` - Summary of groups (when grouping is active)

**Immutability**: QueryResult objects are IMMUTABLE after construction. All export methods MUST NOT modify the result.

#### 2.4 Layer Set (`LayerSet`)

**Location**: `py3plex.dsl.layers.LayerSet`

**Purpose**: First-class abstraction for layer selection with set-theoretic operations.

**Lifecycle**:
1. **Construction**: Created via `LayerSet("name")` or `LayerSet.parse("expr")`
2. **Composition**: Combined via operators (`|`, `&`, `-`, `~`)
3. **Resolution**: Resolved to concrete layer names via `.resolve(network)` → `Set[str]`

**Immutability**: LayerSet objects are IMMUTABLE. All operators return new LayerSet instances.

**Operations**:
- `self | other` - Union (returns layers in either set)
- `self & other` - Intersection (returns layers in both sets)
- `self - other` - Difference (returns layers in self but not other)
- `~self` - Complement (returns all layers except those in self)

**Special Layer Names**:
- `"*"` - All layers in the network
- Named groups: Defined via `LayerSet.define_group("name", LayerSet(...))`

**Resolution Semantics**:
- MUST resolve layer names at execution time (late binding)
- MUST raise `UnknownLayerError` if any referenced layer does not exist (when `strict=True`)
- MAY warn if a layer expression resolves to empty set (when `warn_empty=True`)

**String Parsing**:
- `LayerSet.parse("* - coupling")` - Parse from expression string
- Syntax: `term (op term)*` where `op` is `|`, `&`, or `-`
- Parentheses for precedence: `"(a | b) & c"`
- Complement prefix: `"~a"` (all except a)

---

### 3. Builder Objects — Complete API Contract

#### 3.1 Q — Query Factory (Namespace)

**Import**: `from py3plex.dsl import Q`

**Factory Methods**:

##### `Q.nodes(autocompute=True) → QueryBuilder`

Create a node query builder.

**Parameters**:
- `autocompute` (bool, default=`True`): If `True`, automatically compute missing metrics referenced in `.where()`, `.order_by()`, `.top_k()`. If `False`, raise `DslMissingMetricError` if a metric is referenced but not computed.

**Returns**: `QueryBuilder` with `target=Target.NODES`

**Semantics**: MUST create a builder that queries nodes from the network. Nodes MUST be uniquely identified by `(node_id, layer)` tuple in multilayer networks.

**Example**:
```python
Q.nodes()  # All nodes, autocompute enabled
Q.nodes(autocompute=False)  # Autocompute disabled
```

##### `Q.edges(autocompute=True) → QueryBuilder`

Create an edge query builder.

**Parameters**:
- `autocompute` (bool, default=`True`): Same as `Q.nodes()`

**Returns**: `QueryBuilder` with `target=Target.EDGES`

**Semantics**: MUST create a builder that queries edges from the network. Edges MUST be uniquely identified by `(source, target, source_layer, target_layer)` tuple.

**Example**:
```python
Q.edges()  # All edges
Q.edges(autocompute=False)
```

##### `Q.communities(partition="default", autocompute=True) → CommunityQueryBuilder`

Create a community query builder.

**Parameters**:
- `partition` (str, default=`"default"`): Name of the partition to query
- `autocompute` (bool, default=`True`): Same as `Q.nodes()`

**Returns**: `CommunityQueryBuilder` (extends `QueryBuilder`)

**Semantics**: MUST create a builder that queries communities from a pre-computed partition. If partition does not exist, MUST raise `DslExecutionError` at execution time.

**Example**:
```python
Q.communities()  # Default partition
Q.communities(partition="leiden_gamma_1.2")
```

**Global Configuration**:

##### `Q.uncertainty`

Global uncertainty quantification configuration (namespace).

**Attributes**:
- `enabled` (bool): Global UQ toggle (default: `False`)
- `defaults` (dict): Default UQ parameters for all queries

**Methods**:
- `Q.uncertainty.defaults(**kwargs)` - Set global UQ defaults
- `Q.uncertainty.enable()` - Enable UQ globally
- `Q.uncertainty.disable()` - Disable UQ globally

**Priority Order** (highest to lowest):
1. Per-metric parameters in `.compute(..., uncertainty=True, n_samples=100)`
2. Query-level UQ config from `.uq(method="bootstrap", n_samples=50)`
3. Global `Q.uncertainty.defaults`
4. Hardcoded defaults in `py3plex.uncertainty`

**Example**:
```python
Q.uncertainty.defaults(method="bootstrap", n_samples=100, ci=0.95)
Q.uncertainty.enable()
```

#### 3.2 QueryBuilder — Chainable Builder

**Location**: `py3plex.dsl.builder.QueryBuilder`

**Constructor**: MUST NOT be called directly. Use `Q.nodes()`, `Q.edges()`, or `Q.communities()`.

**All Methods MUST**:
- Return `self` (or compatible builder type) for chaining
- Not execute the query (lazy evaluation)
- Modify the internal `_select` AST node in place

##### `.from_layers(layer_expr) → QueryBuilder`

Filter query to specific layers using layer algebra.

**Parameters**:
- `layer_expr` (Union[LayerExprBuilder, LayerSet]): Layer expression

**Semantics**:
- MUST restrict query to nodes/edges in specified layers
- For nodes: `(node_id, layer)` tuples where `layer` is in the resolved layer set
- For edges: `(src, dst, src_layer, dst_layer)` tuples where `src_layer` and `dst_layer` are in the resolved layer set
- Layer expression MUST be resolved at execution time

**Compatibility**:
- MUST support legacy `LayerExprBuilder` (from `L["a"] + L["b"]`)
- MUST support new `LayerSet` (from `L["* - coupling"]`)

**Example**:
```python
.from_layers(L["social"] + L["work"])  # Union (legacy)
.from_layers(L["* - coupling"])  # Difference (new)
.from_layers(LayerSet("social") | LayerSet("work"))  # Union (new)
```

##### `.where(*exprs, **conditions) → QueryBuilder`

Add filtering conditions.

**Parameters**:
- `*exprs` (BooleanExpression): Boolean expressions from `F` (e.g., `F.degree > 5`)
- `**conditions` (keyword arguments): Condition specifications using suffixes

**Condition Syntax**:

1. **Equality**: `attr=value` → `attr = value`
2. **Comparison**: `attr__gt=value` → `attr > value`
   - Suffixes: `__gt` (>), `__gte` (>=), `__lt` (<), `__lte` (<=), `__eq` (=), `__ne` (!=)
3. **Special Predicates**:
   - `intralayer=True` → Edges within same layer
   - `interlayer=("layer1", "layer2")` → Edges between specific layers
4. **Temporal**: `t__between=(t_start, t_end)` → Time range filter
   - Also: `t__gte=t`, `t__lte=t`, `t__gt=t`, `t__lt=t`

**Operator Precedence** (for F expressions):
1. Comparison operators (`<`, `>`, `<=`, `>=`, `==`, `!=`)
2. NOT (`~`)
3. AND (`&`)
4. OR (`|`)

**Semantics**:
- Multiple conditions are combined with AND
- MUST filter items (nodes/edges) matching ALL conditions
- MUST support comparison on computed metrics (if autocompute enabled) or existing attributes
- MUST raise `UnknownAttributeError` if attribute does not exist and cannot be autocomputed

**Example**:
```python
.where(degree__gt=5, layer="social")  # AND semantics
.where(F.degree > 5)  # Expression syntax
.where((F.degree > 5) & (F.layer == "social"))  # Complex expression
.where(intralayer=True)  # Special predicate
.where(t__between=(100, 200))  # Temporal filter
```

**Error Conditions**:
- If `autocompute=False` and filtering on uncomputed metric → `DslMissingMetricError`
- If attribute does not exist → `UnknownAttributeError` with suggestions

##### `.compute(*measures, alias=None, aliases=None, uncertainty=None, **uq_params) → QueryBuilder`

Compute metrics on nodes/edges.

**Parameters**:
- `*measures` (str): Metric names to compute (e.g., "degree", "betweenness_centrality")
- `alias` (str, optional): Alias for single measure
- `aliases` (Dict[str, str], optional): Dictionary mapping measures to aliases
- `uncertainty` (bool, optional): Enable UQ for these metrics (default: inherits from query-level or global)
- `**uq_params`: UQ parameters (method, n_samples, ci, bootstrap_unit, bootstrap_mode, n_null, null_model, random_state)

**UQ Parameters**:
- `method` (str): "bootstrap", "perturbation", "seed", "null_model", "stratified_perturbation"
- `n_samples` (int): Number of samples (default: from uq_config or 50)
- `ci` (float): Confidence interval level (default: 0.95)
- `bootstrap_unit` (str): "edges", "nodes", or "layers"
- `bootstrap_mode` (str): "resample" or "permute"
- `n_null` (int): Number of null model replicates
- `null_model` (str): "degree_preserving", "erdos_renyi", "configuration"
- `random_state` (int): Random seed

**Semantics**:
- MUST compute specified metrics for all items in the current result set
- MUST store results in `attributes` dictionary of QueryResult
- MAY compute metrics lazily (deferred until needed by `.where()`, `.order_by()`, etc.)
- MUST use measure_registry to look up metric implementations

**Metric Types**:
1. **Centrality**: degree, betweenness_centrality, closeness_centrality, eigenvector_centrality, pagerank
2. **Clustering**: clustering, triangles
3. **Community**: community_id, community_size (requires partition)
4. **Custom**: User-defined via `@dsl_operator`

**UQ Behavior**:
- If `uncertainty=True`, results MUST be dictionaries with keys: `mean`, `std`, `quantiles`, `certainty`
- If `uncertainty=False` or `None` (and not enabled globally), results MUST be scalars
- Quantiles MUST include at minimum: 0.025, 0.05, 0.5, 0.95, 0.975 for ci=0.95

**Example**:
```python
.compute("degree", "betweenness_centrality")  # Multiple metrics
.compute("degree", alias="deg")  # With alias
.compute("degree", uncertainty=True, method="bootstrap", n_samples=100)  # With UQ
```

##### `.order_by(key, desc=False) → QueryBuilder`

Order results by attribute.

**Parameters**:
- `key` (str): Attribute name to order by
- `desc` (bool, default=False): If True, descending order; if False, ascending

**Semantics**:
- MUST sort items by specified attribute
- MUST support ordering by computed metrics
- For UQ metrics with uncertainty, MUST order by `mean` value
- MUST preserve stable sort order (items with equal keys maintain relative order)

**Example**:
```python
.order_by("degree", desc=True)  # Descending
.order_by("betweenness_centrality")  # Ascending
```

##### `.limit(n) → QueryBuilder`

Limit results to top n items.

**Parameters**:
- `n` (int): Maximum number of items to return

**Semantics**:
- MUST return at most `n` items
- MUST apply AFTER ordering (if `.order_by()` was called)
- MUST apply AFTER filtering (if `.where()` was called)
- If n <= 0, MUST return empty result

**Example**:
```python
.limit(20)  # Top 20 items
```

##### `.top_k(k, key) → QueryBuilder`

Keep top-k items by attribute value.

**Parameters**:
- `k` (int): Number of items to keep
- `key` (str): Attribute to rank by

**Semantics**:
- MUST keep top `k` items ranked by `key` (descending order)
- If grouping is active (`.per_layer()` or `.per_layer_pair()`), MUST apply per group
- MUST support UQ metrics (ranks by `mean` value)

**Difference from `.limit()`**:
- `.limit(n)` applies globally after all operations
- `.top_k(k, key)` can apply per group when grouping is active

**Example**:
```python
.top_k(10, "degree")  # Global top-10
.per_layer().top_k(5, "betweenness")  # Top-5 per layer
```

##### `.per_layer() → QueryBuilder`

Enable per-layer grouping for nodes.

**Semantics**:
- MUST group nodes by their layer
- Operations after `.per_layer()` MUST apply independently per layer
- MUST enable `.aggregate()` and `.coverage()` operations
- Grouping MUST remain active until `.end_grouping()` is called (implicit at execution if not called)

**Supported Operations in Grouping Context**:
- `.top_k(k, key)` - Top-k per layer
- `.where()` - Filter within each layer
- `.aggregate()` - Compute per-layer statistics
- `.coverage()` - Cross-layer filtering

**Example**:
```python
.per_layer().top_k(10, "degree")  # Top-10 nodes per layer
```

##### `.per_layer_pair() → QueryBuilder`

Enable per-layer-pair grouping for edges.

**Semantics**:
- MUST group edges by (source_layer, target_layer) tuple
- MUST only be valid for edge queries (raises error for node queries)
- Operations after `.per_layer_pair()` MUST apply independently per layer pair
- Grouping MUST remain active until `.end_grouping()` is called

**Example**:
```python
Q.edges().per_layer_pair().top_k(5, "weight")  # Top-5 edges per layer pair
```

##### `.end_grouping() → QueryBuilder`

Explicitly end grouping context.

**Semantics**:
- MUST flatten grouped results back to single collection
- MUST be called before `.coverage()` to enable cross-group filtering
- If not called explicitly, MUST be applied implicitly at execution time

**Example**:
```python
.per_layer().top_k(10, "degree").end_grouping().coverage(mode="all")
```

##### `.coverage(mode="all", k=None) → QueryBuilder`

Filter items by cross-group coverage.

**Parameters**:
- `mode` (str): Coverage mode - "all", "any", or "k"
- `k` (int, optional): Required for mode="k" - minimum number of groups

**Preconditions**:
- MUST be called after grouping context has ended (after `.end_grouping()` or before `.per_layer()`)
- MUST raise `GroupingError` if called within active grouping context

**Semantics**:
- **mode="all"**: Keep items present in ALL groups
- **mode="any"**: Keep items present in ANY group (no-op, all items pass)
- **mode="k"**: Keep items present in at least `k` groups
- For nodes: Compare by node_id (ignore layer)
- For edges: Compare by (source, target) tuple (ignore layers)

**Example**:
```python
# Nodes in all layers
.per_layer().top_k(10, "degree").end_grouping().coverage(mode="all")

# Edges in at least 2 layer pairs
Q.edges().per_layer_pair().top_k(5, "weight").end_grouping().coverage(mode="k", k=2)
```

##### `.aggregate(**aggregations) → QueryBuilder`

Compute per-group aggregations.

**Parameters**:
- `**aggregations` (str): Aggregation specifications in format `alias="func(column)"`

**Preconditions**:
- MUST be called within active grouping context (after `.per_layer()` or `.per_layer_pair()`)
- MUST raise `GroupingError` if called outside grouping context

**Supported Functions**:
- `mean(col)` - Mean value
- `sum(col)` - Sum
- `count(col)` or `count()` - Count of items
- `min(col)` - Minimum
- `max(col)` - Maximum
- `std(col)` - Standard deviation
- `median(col)` - Median

**Semantics**:
- MUST compute aggregation per group
- Result MUST have one row per group
- MUST support aggregating UQ metrics (aggregates the `mean` field)

**Example**:
```python
.per_layer().aggregate(avg_degree="mean(degree)", node_count="count()")
```

##### `.uq(method="perturbation", n_samples=50, ci=0.95, seed=None, **kwargs) → QueryBuilder`

Set query-level uncertainty quantification configuration.

**Parameters**:
- `method` (str or UQConfig or None): UQ method name, UQConfig instance, or None to disable
- `n_samples` (int, default=50): Number of samples
- `ci` (float, default=0.95): Confidence interval level
- `seed` (int, optional): Random seed
- `**kwargs`: Method-specific parameters

**Semantics**:
- MUST apply UQ defaults to all `.compute()` calls in this query
- Per-metric parameters in `.compute()` MUST override query-level UQ
- If `method=None`, MUST disable query-level UQ

**Priority** (highest to lowest):
1. Per-metric parameters in `.compute(uncertainty=True, n_samples=200)`
2. Query-level config from `.uq()`
3. Global `Q.uncertainty.defaults`

**Example**:
```python
.uq(method="bootstrap", n_samples=100, ci=0.95, bootstrap_unit="edges")
.uq(UQ.fast())  # Use preset
.uq(method=None)  # Disable
```

##### `.at(time) → QueryBuilder`

Query network at specific time point (temporal networks).

**Parameters**:
- `time` (float): Timestamp

**Semantics**:
- MUST filter to edges/nodes active at specified time
- MUST work with `TemporalMultiLayerNetwork` instances
- Temporal context MUST be set in AST as `TemporalContext(kind="at", t0=time, t1=time)`

**Example**:
```python
Q.edges().at(150.0).execute(temporal_net)
```

##### `.during(t_start, t_end) → QueryBuilder`

Query network during time interval (temporal networks).

**Parameters**:
- `t_start` (float): Start time (inclusive)
- `t_end` (float): End time (inclusive)

**Semantics**:
- MUST filter to edges/nodes active during [t_start, t_end]
- MUST work with `TemporalMultiLayerNetwork` instances
- Temporal context MUST be set in AST as `TemporalContext(kind="during", t0=t_start, t1=t_end)`

**Example**:
```python
Q.edges().during(100.0, 200.0).execute(temporal_net)
```

##### `.window(size, step=None, start=None, end=None, aggregation="list") → QueryBuilder`

Iterate over sliding time windows (temporal networks).

**Parameters**:
- `size` (float or str): Window size
- `step` (float or str, optional): Step size (default: size, non-overlapping)
- `start` (float, optional): Start time
- `end` (float, optional): End time
- `aggregation` (str, default="list"): How to aggregate results across windows

**Semantics**:
- MUST generate non-overlapping windows if `step=None` or `step=size`
- MUST generate overlapping windows if `step < size`
- Result MUST include window metadata in `meta["windows"]`

**Example**:
```python
.window(size=100.0, step=50.0)  # Overlapping windows
.window(size="7d", step="1d")  # Duration strings (if supported)
```

##### `.community(method="leiden", gamma=1.0, omega=1.0, random_state=None, partition_name="default", **kwargs) → QueryBuilder`

Run community detection and attach partition.

**Parameters**:
- `method` (str, default="leiden"): Algorithm name
- `gamma` (float or dict, default=1.0): Resolution parameter
- `omega` (float or array, default=1.0): Interlayer coupling strength
- `random_state` (int, optional): Random seed (default: 0)
- `partition_name` (str, default="default"): Partition name
- `**kwargs`: Algorithm-specific parameters

**Supported Algorithms**:
- `"leiden"` - Multilayer Leiden (production-ready with UQ)
- `"louvain"` - Multilayer Louvain
- `"infomap"` - Infomap (if available)
- `"label_propagation_supra"` - Supra-graph label propagation
- `"label_propagation_consensus"` - Consensus label propagation

**Semantics**:
- MUST run community detection on the network
- MUST attach results to network under `partition_name`
- Results MUST be accessible via `Q.communities(partition=partition_name)`
- When combined with `.uq()`, MUST enable probabilistic community detection

**Example**:
```python
.community(method="leiden", gamma=1.2, random_state=42)
.community(method="leiden").uq(method="ensemble", n_samples=50)  # With UQ
```

##### `.sensitivity(perturb, grid=None, n_samples=30, metrics=None, **kwargs) → QueryBuilder`

Enable sensitivity analysis for query conclusions.

**Parameters**:
- `perturb` (str): Perturbation method ("edge_drop", "degree_preserving_rewire")
- `grid` (List[float], optional): Perturbation strength grid (default: [0.0, 0.05, 0.1, 0.15, 0.2])
- `n_samples` (int, default=30): Samples per grid point
- `metrics` (List[str], optional): Stability metrics (default: ["kendall_tau"])
- `**kwargs`: Perturbation-specific parameters

**Semantics**:
- MUST test stability of query CONCLUSIONS (rankings, sets, communities), NOT metric values
- Result MUST include `sensitivity_result` with stability curves
- DISTINCT from `.uq()` which estimates uncertainty of metric VALUES

**Stability Metrics**:
- `"kendall_tau"` - Ranking correlation
- `"jaccard_at_k(k)"` - Set overlap at top-k
- `"nmi"` - Normalized mutual information (for communities)

**Example**:
```python
.sensitivity(perturb="edge_drop", grid=[0.0, 0.05, 0.1], n_samples=30)
```

##### `.explain(neighbors_top=None, include=None, **config) → QueryBuilder or ExplainQuery`

Attach explanations to results OR get execution plan.

**Two Modes**:

1. **Execution Plan Mode** (no arguments): Returns `ExplainQuery` showing execution plan
2. **Explanations Mode** (with arguments): Attaches explanations to each result row

**Parameters** (Explanations Mode):
- `neighbors_top` (int, default=10): Max neighbors to include
- `include` (List[str], optional): Explanation blocks (default: ["community", "top_neighbors", "layer_footprint"])
- `exclude` (List[str], optional): Blocks to exclude
- `neighbors` (dict, optional): Neighbor config (metric, scope, direction)
- `cache` (bool, default=True): Cache lookups
- `as_columns` (bool, default=True): Store as top-level columns
- `prefix` (str, default=""): Column name prefix

**Explanation Blocks**:
- `"community"` - Community membership and size
- `"top_neighbors"` - Top neighbors by weight/degree
- `"layer_footprint"` - Layers where node/edge appears

**Example**:
```python
.explain()  # Execution plan
.explain(neighbors_top=5, include=["top_neighbors"])  # With explanations
```

##### `.to_ast() → Query`

Convert builder to AST.

**Returns**: `Query` AST node

**Semantics**:
- MUST create deep copy of internal AST to prevent mutation
- MUST NOT execute the query
- Result MUST be serializable to JSON

**Example**:
```python
ast = Q.nodes().where(degree__gt=5).to_ast()
```

##### `.execute(network, progress=True, **params) → QueryResult`

Execute query on network.

**Parameters**:
- `network` (Any): Multilayer network object
- `progress` (bool, default=True): Enable progress logging
- `**params` (Any): Parameter bindings for `ParamRef` placeholders

**Returns**: `QueryResult`

**Semantics**:
- MUST compile builder to AST
- MUST bind all `ParamRef` parameters using `**params`
- MUST execute query using `execute_ast(network, query, params)`
- MUST raise `ParameterMissingError` if any parameter is missing
- MUST return `QueryResult` with items, attributes, and metadata

**Example**:
```python
result = Q.nodes().where(degree__gt=Param.int("k")).execute(net, k=5)
result = Q.nodes().execute(net, progress=False)  # Disable logging
```

---

#### 3.3 L — Layer Expression Factory

**Import**: `from py3plex.dsl import L`

**Syntax**:
- `L["name"]` → LayerExprBuilder or LayerSet (single layer)
- `L["name1", "name2"]` → LayerExprBuilder (union)
- `L["* - coupling"]` → LayerSet (parsed expression)

**Semantics**:
- MUST support both legacy (LayerExprBuilder) and new (LayerSet) backends
- MUST detect expressions with operators and use LayerSet
- MUST use LayerExprBuilder for simple names (backward compatibility)

**Example**:
```python
L["social"]  # Single layer
L["social", "work"]  # Union (legacy)
L["* - coupling"]  # Expression (new)
```

---

#### 3.4 Param — Parameter Reference Factory

**Import**: `from py3plex.dsl import Param`

**Factory Methods**:
- `Param.int(name)` → ParamRef with type hint "int"
- `Param.float(name)` → ParamRef with type hint "float"
- `Param.str(name)` → ParamRef with type hint "str"

**Semantics**:
- MUST create `ParamRef` AST nodes as placeholders
- Parameters MUST be bound at execution time via `.execute(**params)`
- Type hints MAY be used for validation (implementation-defined)

**Example**:
```python
.where(degree__gt=Param.int("threshold"))
.execute(net, threshold=5)
```

---

#### 3.5 UQ — Uncertainty Quantification Presets

**Import**: `from py3plex.dsl import UQ`

**Preset Methods**:
- `UQ.fast(seed=None)` → UQConfig with n_samples=20
- `UQ.standard(seed=None)` → UQConfig with n_samples=100
- `UQ.publication(seed=None)` → UQConfig with n_samples=500
- `UQ.off()` → None (disable UQ)

**Semantics**:
- MUST return `UQConfig` instances ready for use in `.uq()`
- MUST set reasonable defaults for method, ci, and other parameters

**Example**:
```python
.uq(UQ.fast())  # Quick UQ with 20 samples
.uq(UQ.publication(seed=42))  # Publication-quality with 500 samples
```

---

#### 3.6 F — Field Expression Builder

**Import**: `from py3plex.dsl import F`

**Syntax**:
- `F.attr` → FieldExpression for attribute
- `F.attr > value` → BooleanExpression (comparison)
- `(F.attr > 5) & (F.layer == "social")` → Complex BooleanExpression

**Supported Operators**:
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `&` (AND), `|` (OR), `~` (NOT)

**Precedence** (highest to lowest):
1. Comparison operators
2. NOT (`~`)
3. AND (`&`)
4. OR (`|`)

**Semantics**:
- MUST create `ConditionExpr` AST nodes compatible with `.where()`
- Logical operators MUST follow Python's bitwise operator precedence

**Example**:
```python
.where(F.degree > 5)
.where((F.degree > 5) & (F.layer == "social"))
.where((F.degree > 10) | (F.clustering < 0.5))
```

---

#### 3.7 C — Comparison Builder Factory

**Import**: `from py3plex.dsl import C`

**Factory Method**:
- `C.compare(net1_name, net2_name)` → CompareBuilder

**Semantics**:
- MUST create comparison query builder for two networks
- Networks MUST be provided as dict to `.execute({name1: net1, name2: net2})`

**Example**:
```python
C.compare("baseline", "treatment").using("multiplex_jaccard").execute(networks)
```

---

#### 3.8 N — Null Model Builder Factory

**Import**: `from py3plex.dsl import N`

**Factory Methods**:
- `N.configuration()` → NullModelBuilder (configuration model)
- `N.erdos_renyi()` → NullModelBuilder (Erdős-Rényi model)
- `N.degree_preserving()` → NullModelBuilder (degree-preserving rewiring)

**Semantics**:
- MUST generate null model instances
- MUST support `.samples(n)` to specify number of replicates
- MUST support `.seed(s)` for reproducibility

**Example**:
```python
N.configuration().samples(100).seed(42).execute(net)
```

---

#### 3.9 P — Path Builder Factory

**Import**: `from py3plex.dsl import P`

**Factory Methods**:
- `P.shortest(source, target)` → PathBuilder (shortest paths)
- `P.random_walk(start, steps)` → PathBuilder (random walks)

**Semantics**:
- MUST find paths in multilayer networks
- MUST support `.crossing_layers()` for interlayer paths

**Example**:
```python
P.shortest("Alice", "Bob").crossing_layers().execute(net)
```

---

#### 3.10 D — Dynamics Builder Factory

**Import**: `from py3plex.dsl import D` (if available)

**Factory Methods**:
- `D.simulate(model)` → DynamicsBuilder

**Semantics**:
- MUST simulate network dynamics (SIR, SIS, etc.)
- MUST support `.steps(n)` for number of timesteps

**Example**:
```python
from py3plex.dynamics import SIRModel
D.simulate(SIRModel(beta=0.3, gamma=0.1)).steps(100).execute(net)
```

---

### 4. Query Grammar (Formal + Executable)

#### 4.1 BNF Grammar

```bnf
<query> ::= <select_stmt> | <explain_stmt> | <compare_stmt> | <null_model_stmt> | <path_stmt> | <dynamics_stmt>

<select_stmt> ::= "SELECT" <target> [ <from_clause> ] [ <where_clause> ] [ <compute_clause> ] [ <order_clause> ] [ <limit_clause> ] [ <export_clause> ]

<target> ::= "nodes" | "edges" | "communities"

<from_clause> ::= "FROM" <layer_expr>

<layer_expr> ::= <layer_term> [ <layer_op> <layer_term> ]*
<layer_term> ::= "LAYER" "(" <string> ")" | "*"
<layer_op> ::= "+" | "-" | "&"

<where_clause> ::= "WHERE" <condition_expr>

<condition_expr> ::= <condition_atom> [ <logical_op> <condition_atom> ]*
<condition_atom> ::= <comparison> | <special_predicate> | <function_call>
<comparison> ::= <attribute> <comp_op> <value>
<comp_op> ::= ">" | "<" | ">=" | "<=" | "=" | "!="
<special_predicate> ::= "intralayer" | "interlayer" "(" <string> "," <string> ")"
<logical_op> ::= "AND" | "OR"

<compute_clause> ::= "COMPUTE" <compute_item> [ "," <compute_item> ]*
<compute_item> ::= <measure_name> [ "AS" <alias> ]

<order_clause> ::= "ORDER" "BY" <attribute> [ "DESC" | "ASC" ]

<limit_clause> ::= "LIMIT" <integer>

<export_clause> ::= "TO" <export_target>
<export_target> ::= "pandas" | "networkx" | "arrow" | "json"

<attribute> ::= <identifier>
<value> ::= <string> | <number> | <param_ref>
<param_ref> ::= ":" <identifier>
```

#### 4.2 Operator Precedence

**Layer Algebra** (evaluated left-to-right, no precedence):
1. `LAYER("a") + LAYER("b") - LAYER("c")` → `((a + b) - c)`

**Logical Operators** (in WHERE clause):
1. AND (higher precedence)
2. OR (lower precedence)
3. Use parentheses for explicit grouping

**F Expressions** (Python builder):
1. Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
2. NOT: `~`
3. AND: `&`
4. OR: `|`

---

### 5. Layer Algebra (Formal Semantics)

#### 5.1 Operations

Let `L` be the set of all layers in a network, and `S, T ⊆ L` be layer sets.

**Union** (`S | T` or `S + T`):
```
S ∪ T = {l | l ∈ S ∨ l ∈ T}
```

**Intersection** (`S & T`):
```
S ∩ T = {l | l ∈ S ∧ l ∈ T}
```

**Difference** (`S - T`):
```
S \ T = {l | l ∈ S ∧ l ∉ T}
```

**Complement** (`~S`):
```
L \ S = {l | l ∈ L ∧ l ∉ S}
```

#### 5.2 Special Cases

**Wildcard** (`*`):
```
* = L (all layers in the network)
```

**Empty Set**:
```
∅ (no layers; results in empty query)
```

#### 5.3 Evaluation Order

Layer expressions MUST be evaluated left-to-right without operator precedence:
```
L["a"] + L["b"] - L["c"]  →  ((L["a"] + L["b"]) - L["c"])
```

Use parentheses for different grouping:
```
LayerSet.parse("a + (b - c)")  →  (a + (b - c))
```

---

### 6. Filtering Semantics

#### 6.1 Attribute Access

Attributes MUST be resolved in the following order:
1. **Computed metrics**: Metrics added via `.compute()`
2. **Intrinsic attributes**: Node/edge attributes (e.g., "weight", "label")
3. **Structural properties**: "degree", "layer", "source_layer", "target_layer"
4. **Autocomputed metrics**: If `autocompute=True` and attribute is a known measure

#### 6.2 Comparison Semantics

**Numeric Comparisons**:
- `attr > value`: `attr_value > value`
- `attr >= value`: `attr_value >= value`
- `attr < value`: `attr_value < value`
- `attr <= value`: `attr_value <= value`

**Equality**:
- `attr == value`: Exact equality (for strings, case-sensitive)
- `attr != value`: Inequality

**Null Handling**:
- If `attr` is `None` or missing, comparison MUST return `False` (except for `!= None` which returns `True`)

#### 6.3 Logical Operators

**AND**:
```
result = item1 AND item2
Keep item if it satisfies BOTH conditions
```

**OR**:
```
result = item1 OR item2
Keep item if it satisfies EITHER condition
```

**NOT** (F expressions only):
```
result = ~(item)
Keep item if it does NOT satisfy condition
```

---

### 7. Compute Semantics

#### 7.1 Metric Computation

Metrics MUST be computed using the following process:

1. **Lookup**: Check `measure_registry` for metric implementation
2. **Execution**: Call metric function with network and current items
3. **Storage**: Store results in `attributes` dictionary
4. **Aliasing**: If alias provided, store under alias name instead of original name

#### 7.2 Autocompute Behavior

When `autocompute=True`:
1. If metric is referenced in `.where()`, `.order_by()`, or `.top_k()` but not computed
2. AND metric exists in `measure_registry` or `CENTRALITY_ALIASES`
3. THEN automatically compute metric before applying operation
4. ELSE raise `DslMissingMetricError`

When `autocompute=False`:
- Any reference to uncomputed metric MUST raise `DslMissingMetricError`

#### 7.3 Uncertainty Quantification

When UQ is enabled for a metric:

1. **Sampling**: Generate `n_samples` network replicates using specified method
2. **Computation**: Compute metric on each replicate
3. **Aggregation**: Compute mean, std, and quantiles across samples
4. **Result Format**:
   ```python
   {
       "mean": float,
       "std": float,
       "quantiles": {0.025: float, 0.05: float, 0.5: float, 0.95: float, 0.975: float},
       "certainty": float  # Confidence measure (0-1), see section 10.1 for calculation
   }
   ```

---

### 8. Grouping & Coverage (Critical)

#### 8.1 Grouping Lifecycle

**States**:
1. **No Grouping** (initial state): Operations apply globally
2. **Active Grouping**: After `.per_layer()` or `.per_layer_pair()`, operations apply per group
3. **Ended Grouping**: After `.end_grouping()` (explicit) or before `.coverage()`, groups are flattened

**State Transitions**:
```
No Grouping → [.per_layer()] → Active Grouping
Active Grouping → [.end_grouping()] → Ended Grouping
Ended Grouping → [.coverage()] → No Grouping
```

#### 8.2 `.per_layer()` Semantics

**For Nodes**:
- Group by `layer` attribute
- Each group contains nodes from exactly one layer
- Groups MUST be disjoint

**For Edges**:
- Group by `(source_layer, target_layer)` tuple
- Intralayer edges: `source_layer == target_layer`
- Interlayer edges: `source_layer != target_layer`

**Metadata**:
- Result MUST include `meta["grouping"]` with group information
- Format:
  ```python
  {
      "mode": "per_layer",
      "groups": ["layer1", "layer2", ...],
      "counts": {"layer1": 10, "layer2": 15, ...}
  }
  ```

#### 8.3 `.per_layer_pair()` Semantics

**For Edges Only**:
- Group by `(source_layer, target_layer)` tuple
- Each group represents edges between specific layer pair

**Metadata**:
- Result MUST include `meta["grouping"]` with group information
- Format:
  ```python
  {
      "mode": "per_layer_pair",
      "groups": [("layer1", "layer2"), ("layer1", "layer1"), ...],
      "counts": {("layer1", "layer2"): 5, ("layer1", "layer1"): 10, ...}
  }
  ```

#### 8.4 `.coverage()` Semantics

**Preconditions**:
- MUST NOT be in active grouping state
- MUST be called after `.end_grouping()` or before any grouping

**mode="all"** (Intersection):
- Keep items present in ALL groups
- For nodes: Compare by `node_id` (ignore layer)
- For edges: Compare by `(source, target)` tuple (ignore layers)
- Formula: `result = ∩ all_groups`

**mode="any"** (Union):
- Keep items present in ANY group
- Effectively a no-op (all items pass)
- Formula: `result = ∪ all_groups`

**mode="k"** (K-coverage):
- Keep items present in at least `k` groups
- MUST specify `k` parameter
- Formula: `result = {item | count(groups containing item) >= k}`

**Example**:
```python
# Find nodes in all three layers
result = (Q.nodes()
    .from_layers(L["social"] + L["work"] + L["hobby"])
    .per_layer()
    .top_k(10, "degree")
    .end_grouping()
    .coverage(mode="all")
    .execute(net))
```

---

### 9. Aggregations & Statistics

#### 9.1 Aggregate Functions

**Supported Functions**:
- `count()` or `count(col)`: Count of items (or non-null values in column)
- `mean(col)`: Arithmetic mean
- `sum(col)`: Sum of values
- `min(col)`: Minimum value
- `max(col)`: Maximum value
- `std(col)`: Standard deviation
- `median(col)`: Median value

#### 9.2 Aggregation Semantics

**Preconditions**:
- MUST be in active grouping state

**Execution**:
1. For each group, apply aggregation function to specified column
2. Result MUST have one row per group
3. Group identifier MUST be included in result

**UQ Handling**:
- If column contains UQ results (dicts with `mean`, `std`, etc.), MUST aggregate the `mean` field

**Example**:
```python
.per_layer().aggregate(
    avg_degree="mean(degree)",
    max_betweenness="max(betweenness_centrality)",
    node_count="count()"
)
```

---

### 10. Uncertainty Quantification (First-Class Type)

#### 10.1 UQ Result Format

All UQ results MUST be dictionaries with the following structure:
```python
{
    "mean": float,          # Point estimate
    "std": float,           # Standard deviation
    "quantiles": {          # Quantile dictionary
        0.025: float,
        0.05: float,
        0.5: float,         # Median
        0.95: float,
        0.975: float
    },
    "certainty": float      # Confidence measure (0-1), implementation-defined
                            # Suggested: 1.0 for deterministic
                            # For UQ: 1.0 - min(1.0, std/max(abs(mean), epsilon))
                            # where epsilon prevents division by zero (e.g., 1e-10)
}
```

#### 10.2 UQ Methods

**bootstrap**:
- Resample or permute network elements
- Parameters: 
  - `bootstrap_unit` ("edges", "nodes", "layers"): What to sample/permute
  - `bootstrap_mode`:
    - `"resample"`: Sample with replacement (standard bootstrap) - creates replicates by randomly sampling elements, allowing duplicates
    - `"permute"`: Permutation test without replacement - shuffles assignments (e.g., node-layer assignments) while preserving network structure

**Note**: "resample" mode generates bootstrap samples for confidence intervals, while "permute" mode is used for null hypothesis testing by randomizing assignments.

**perturbation**:
- Add Gaussian noise to edge weights
- Parameters: `noise_std` (standard deviation of noise)

**seed**:
- Run algorithm multiple times with different random seeds
- Parameters: `n_samples` (number of runs)

**null_model**:
- Compare against null model ensemble
- Parameters: `null_model` ("degree_preserving", "erdos_renyi", "configuration"), `n_null` (number of null networks)

**stratified_perturbation**:
- Stratified resampling by node/edge attributes
- Parameters: `strata` (list of attributes), `bins` (dict of binning specs)

#### 10.3 UQ Priority Order

1. **Per-metric parameters** in `.compute(uncertainty=True, n_samples=100)`
2. **Query-level config** from `.uq(method="bootstrap", n_samples=50)`
3. **Global defaults** from `Q.uncertainty.defaults(n_samples=100)`
4. **Hardcoded defaults** in `py3plex.uncertainty` (n_samples=50, ci=0.95, method="perturbation")

#### 10.4 UQ in DataFrame Export

When calling `to_pandas(expand_uncertainty=True, ci_level=0.95)`:
- Each UQ column MUST expand to multiple columns:
  - `{col}`: Point estimate (mean)
  - `{col}_std`: Standard deviation
  - `{col}_ci{pct}_low`: Lower CI bound (e.g., `degree_ci95_low`)
  - `{col}_ci{pct}_high`: Upper CI bound
  - `{col}_ci{pct}_width`: CI width

---

### 11. Temporal Semantics

#### 11.1 Temporal Network Requirements

Temporal queries MUST work with `TemporalMultiLayerNetwork` instances that support:
- `.get_snapshot(time)`: Get network state at specific time
- `.get_edges_in_range(t_start, t_end)`: Get edges active in time range

#### 11.2 `.at(time)` Semantics

**Behavior**:
- Filter network to snapshot at `time`
- MUST use `get_snapshot(time)` method
- Result MUST include only edges/nodes active at specified time

#### 11.3 `.during(t_start, t_end)` Semantics

**Behavior**:
- Filter network to time range [t_start, t_end] (inclusive)
- MUST use `get_edges_in_range(t_start, t_end)` method
- Result MUST include all edges/nodes active anytime during interval

#### 11.4 `.window(size, step)` Semantics

**Behavior**:
- Iterate over sliding time windows
- Window `i` spans `[start + i*step, start + i*step + size]`
- Execute query independently for each window
- Aggregate results according to `aggregation` parameter

**Aggregation Modes**:
- `"list"`: Return list of QueryResult objects (one per window)
- `"concat"`: Concatenate all results into single QueryResult
- `"avg"`: Average numeric attributes across windows

---

### 12. Result Model (QueryResult)

#### 12.1 Core Attributes

**target** (str):
- MUST be "nodes" or "edges"
- Indicates what the query selected

**items** (List[Any]):
- For nodes: List of `(node_id, layer)` tuples
- For edges: List of `(source, target, source_layer, target_layer)` tuples
- Order MUST match the order of attribute values

**attributes** (Dict[str, Union[List[Any], Dict[Any, Any]]]):
- Mapping from attribute name to values
- Values MUST be either:
  - List (one value per item, same order as `items`)
  - Dict (mapping item to value)
- UQ results MUST be dicts with structure specified in section 10.1

**meta** (Dict[str, Any]):
- Execution metadata
- MUST include:
  - `"query_ast"`: Serialized AST (if provenance enabled)
  - `"execution_time"`: Time in seconds
  - `"grouping"`: Grouping metadata (if grouping was used)
  - `"provenance"`: Provenance dictionary (if provenance enabled)
  - `"computed_metrics"`: Set of metrics computed during execution

**computed_metrics** (Set[str]):
- Set of metric names computed during execution
- Includes both explicit (via `.compute()`) and autocomputed metrics

**sensitivity_result** (Optional[SensitivityResult]):
- Sensitivity analysis results (if `.sensitivity()` was used)
- Contains stability curves and metrics

#### 12.2 Export Methods

##### `to_pandas(expand_uncertainty=False, ci_level=0.95, expand_explanations=False) → pd.DataFrame`

**Parameters**:
- `expand_uncertainty` (bool, default=False): Expand UQ results to multiple columns
- `ci_level` (float, default=0.95): Confidence interval level for expansion
- `expand_explanations` (bool, default=False): Expand explanation dicts to columns

**Behavior**:
- MUST create DataFrame with one row per item
- For nodes: Index MUST be `(node_id, layer)` tuple
- For edges: Index MUST be `(source, target, source_layer, target_layer)` tuple
- If `expand_uncertainty=True`, MUST expand UQ columns as specified in section 10.4
- If `expand_explanations=True`, MUST expand explanation dicts (e.g., `top_neighbors`) to JSON strings

##### `to_networkx() → nx.Graph or nx.MultiGraph`

**Behavior**:
- MUST convert result to NetworkX graph
- For node queries: Return graph with selected nodes and their attributes
- For edge queries: Return graph with selected edges and their attributes
- MUST use MultiGraph if multiple layers or parallel edges exist

##### `to_arrow() → pa.Table`

**Behavior**:
- MUST convert result to Apache Arrow table
- Column types MUST be inferred from attribute types
- UQ results MUST be stored as struct columns

##### `to_json() → str`

**Behavior**:
- MUST serialize result to JSON string
- Format:
  ```json
  {
      "target": "nodes",
      "items": [...],
      "attributes": {...},
      "meta": {...}
  }
  ```

##### `to_csv(path, **kwargs)`

**Behavior**:
- MUST write result to CSV file at `path`
- MUST use `to_pandas().to_csv(path, **kwargs)` internally

#### 12.3 Provenance Methods

##### `provenance → Optional[Dict[str, Any]]`

**Returns**: Provenance dictionary from `meta["provenance"]` if available

##### `is_replayable → bool`

**Returns**: True if result has replayable provenance

**Requirements for Replayability**:
- Provenance mode MUST be "replayable"
- AST MUST be serialized
- Network snapshot MUST be captured

##### `replay(strict=True) → QueryResult`

**Behavior**:
- MUST reconstruct network and query from provenance
- MUST re-execute query
- Result MUST match original result (if deterministic)
- If `strict=True`, MUST enforce version compatibility

#### 12.4 Grouping Methods

##### `group_summary() → pd.DataFrame`

**Behavior**:
- MUST return summary DataFrame when grouping was used
- Columns: group identifier, item count, aggregated statistics
- MUST raise error if no grouping was used

---

### 13. Provenance & Reproducibility

#### 13.1 Provenance Modes

**Disabled** (default):
- No provenance captured
- Minimal metadata in `meta`

**Replayable**:
- Full AST serialization
- Network snapshot capture
- Parameter bindings
- Random seeds
- Version information

#### 13.2 Provenance Capture

To enable replayable provenance:
```python
from py3plex.provenance import enable_provenance
enable_provenance(mode="replayable", capture_network=True)
```

**Captured Information**:
- Query AST (serialized)
- Parameter bindings
- Network structure (snapshot or delta)
- Random seeds
- Library versions (py3plex, networkx, numpy)
- Execution environment (Python version, platform)

#### 13.3 Replay Process

1. **Deserialize**: Load provenance from result
2. **Reconstruct Network**: Rebuild network from snapshot
3. **Reconstruct Query**: Deserialize AST
4. **Bind Parameters**: Apply saved parameter bindings
5. **Execute**: Run query with same seeds
6. **Compare**: Verify result matches original

---

### 14. Error Model (Complete Hierarchy)

#### 14.1 Base Error

**`DslError(message, query=None, line=None, column=None)`**
- Base class for all DSL errors
- Attributes:
  - `message` (str): Error message
  - `query` (str, optional): Query string that caused error
  - `line` (int, optional): Line number in query
  - `column` (int, optional): Column number in query
- Methods:
  - `format_message()`: Format error with context

#### 14.2 Syntax Errors

**`DslSyntaxError`** (extends `DslError`):
- Raised when query syntax is invalid
- Example: `"SELECT nodes FROMM LAYER("social")"` (typo in FROM)

#### 14.3 Execution Errors

**`DslExecutionError`** (extends `DslError`):
- Raised when query execution fails
- Example: Network does not support required operations

#### 14.4 Semantic Errors

**`UnknownAttributeError(attribute, known_attributes=None)`**:
- Raised when referencing unknown attribute
- Includes suggestions via Levenshtein distance
- Example: `"degree_centraliity"` → suggests `"degree_centrality"`

**`UnknownMeasureError(measure, known_measures=None)`**:
- Raised when computing unknown measure
- Includes suggestions
- Example: `"betweeness"` → suggests `"betweenness_centrality"`

**`UnknownLayerError(layer, known_layers=None)`**:
- Raised when referencing unknown layer
- Includes suggestions
- Example: `"socail"` → suggests `"social"`

**`ParameterMissingError(parameter, provided_params=None)`**:
- Raised when required parameter is not provided
- Lists provided parameters
- Example: `.execute(net)` when query has `Param.int("k")` → suggests providing `k=...`

**`TypeMismatchError(attribute, expected_type, actual_type)`**:
- Raised when attribute has wrong type
- Example: `degree__gt="five"` when degree is numeric

**`GroupingError(message)`**:
- Raised when grouping operations are used incorrectly
- Example: Calling `.coverage()` within active grouping context

**`DslMissingMetricError(metric, required_by=None, autocompute_enabled=True)`**:
- Raised when metric is missing and cannot be autocomputed
- Example: `.where(custom_metric__gt=5)` when `custom_metric` is not computed and not autocomputable

#### 14.5 Error Handling Best Practices

**For Agent Implementations**:
1. MUST catch `DslError` and subclasses
2. SHOULD extract suggestions from error attributes
3. SHOULD display formatted error messages to user
4. MAY attempt automatic correction for simple typos

**Example**:
```python
try:
    result = Q.nodes().where(degree_centraliity__gt=0.5).execute(net)
except UnknownAttributeError as e:
    print(f"Error: {e}")
    if e.suggestion:
        print(f"Did you mean '{e.suggestion}'?")
    # Try again with corrected name
    result = Q.nodes().where(**{e.suggestion + "__gt": 0.5}).execute(net)
```

---

### 15. Legacy Compatibility Rules

#### 15.1 String DSL (Legacy)

**Format**:
```sql
SELECT nodes
FROM LAYER("social") + LAYER("work")
WHERE intralayer AND degree > 5
COMPUTE betweenness_centrality AS bc
ORDER BY bc DESC
LIMIT 20
TO pandas
```

**Compatibility**:
- MUST compile to same AST as builder API
- MUST support all legacy keywords (`FROM`, `WHERE`, `COMPUTE`, `ORDER BY`, `LIMIT`, `TO`)
- MUST support legacy layer syntax (`LAYER("name") + LAYER("name")`)

**Import**:
```python
from py3plex.dsl_legacy import execute_query
result = execute_query(network, query_string)
```

#### 15.2 Migration Path

**From Legacy DSL to Builder API**:
```python
# Legacy
execute_query(net, 'SELECT nodes WHERE degree > 5 COMPUTE betweenness_centrality')

# Builder API (equivalent)
Q.nodes().where(degree__gt=5).compute("betweenness_centrality").execute(net)
```

---

### 16. Minimal Canonical Examples

Each example demonstrates ONE concept unambiguously.

#### 16.1 Basic Node Query with Filtering

```python
from py3plex.dsl import Q, L

# Find high-degree nodes in social layer
result = (
    Q.nodes()
    .from_layers(L["social"])
    .where(degree__gt=5)
    .execute(network)
)

# Result: QueryResult with nodes from "social" layer where degree > 5
# items: [('Alice', 'social'), ('Bob', 'social'), ...]
# attributes: {'degree': [6, 8, ...]}
```

#### 16.2 Computing Metrics with Uncertainty

```python
from py3plex.dsl import Q

# Compute betweenness with bootstrap uncertainty
result = (
    Q.nodes()
    .compute(
        "betweenness_centrality",
        uncertainty=True,
        method="bootstrap",
        n_samples=100,
        ci=0.95,
        bootstrap_unit="edges"
    )
    .execute(network)
)

# Result: Each node has UQ result dict
# attributes: {
#     'betweenness_centrality': {
#         ('Alice', 'social'): {'mean': 0.15, 'std': 0.02, 'quantiles': {...}},
#         ...
#     }
# }

# Export to DataFrame with expanded columns
df = result.to_pandas(expand_uncertainty=True, ci_level=0.95)
# Columns: node, layer, betweenness_centrality, betweenness_centrality_std,
#          betweenness_centrality_ci95_low, betweenness_centrality_ci95_high,
#          betweenness_centrality_ci95_width
```

#### 16.3 Per-Layer Grouping with Top-K

```python
from py3plex.dsl import Q, L

# Find top-5 nodes per layer by degree
result = (
    Q.nodes()
    .from_layers(L["social"] + L["work"] + L["hobby"])
    .per_layer()              # Enable grouping
    .compute("degree")
    .top_k(5, "degree")       # Top-5 per layer (not global)
    .execute(network)
)

# Result: 15 nodes total (5 from each layer)
# meta['grouping']: {
#     'mode': 'per_layer',
#     'groups': ['social', 'work', 'hobby'],
#     'counts': {'social': 5, 'work': 5, 'hobby': 5}
# }
```

#### 16.4 Coverage Filtering (Cross-Layer)

```python
from py3plex.dsl import Q, L

# Find nodes present in ALL three layers (after selecting top-10 per layer)
result = (
    Q.nodes()
    .from_layers(L["social"] + L["work"] + L["hobby"])
    .per_layer()
    .compute("degree")
    .top_k(10, "degree")
    .end_grouping()            # Exit grouping context
    .coverage(mode="all")      # Keep nodes in all groups
    .execute(network)
)

# Result: Nodes that appear in top-10 of ALL three layers
# Compares by node_id (ignores layer)
```

#### 16.5 Aggregation with Grouping

```python
from py3plex.dsl import Q

# Compute per-layer statistics
result = (
    Q.nodes()
    .per_layer()
    .compute("degree", "betweenness_centrality")
    .aggregate(
        avg_degree="mean(degree)",
        max_betweenness="max(betweenness_centrality)",
        node_count="count()"
    )
    .execute(network)
)

# Result: One row per layer with aggregated stats
# items: ['social', 'work', 'hobby']
# attributes: {
#     'avg_degree': [5.2, 4.8, 3.5],
#     'max_betweenness': [0.45, 0.38, 0.22],
#     'node_count': [100, 80, 60]
# }
```

#### 16.6 Temporal Query

```python
from py3plex.dsl import Q

# Query edges active during time window
result = (
    Q.edges()
    .during(100.0, 200.0)
    .where(weight__gt=0.5)
    .execute(temporal_network)
)

# Result: Edges active anytime in [100, 200] with weight > 0.5
```

#### 16.7 Parameterized Query

```python
from py3plex.dsl import Q, Param

# Create reusable query with parameters
query = (
    Q.nodes()
    .where(degree__gt=Param.int("min_degree"))
    .compute("betweenness_centrality")
    .order_by("betweenness_centrality", desc=True)
    .limit(Param.int("top_n"))
)

# Execute with different parameter values
result1 = query.execute(network, min_degree=5, top_n=20)
result2 = query.execute(network, min_degree=10, top_n=10)

# Results have different items based on parameters
```

---

### 17. DSL v2 Specification Compliance Checklist

For implementations and agents:

**Core Abstractions**:
- [ ] QueryBuilder is mutable and chainable
- [ ] `.to_ast()` creates deep copy
- [ ] `.execute()` returns QueryResult
- [ ] QueryResult is immutable
- [ ] LayerSet supports all operators (|, &, -, ~)
- [ ] LayerSet resolves at execution time

**Builder Methods**:
- [ ] All methods return `self` (except `.execute()` and `.to_ast()`)
- [ ] `.where()` supports both kwargs and F expressions
- [ ] `.compute()` supports UQ parameters
- [ ] `.per_layer()` enables grouping for nodes
- [ ] `.per_layer_pair()` enables grouping for edges
- [ ] `.coverage()` requires ended grouping context
- [ ] `.aggregate()` requires active grouping context

**Filtering**:
- [ ] Comparison suffixes (__gt, __gte, __lt, __lte, __eq, __ne) work correctly
- [ ] Special predicates (intralayer, interlayer) work
- [ ] Temporal filters (t__between, t__gte, etc.) work
- [ ] Unknown attributes raise UnknownAttributeError with suggestions
- [ ] autocompute=False raises DslMissingMetricError for uncomputed metrics

**Grouping & Coverage**:
- [ ] `.per_layer()` groups nodes by layer
- [ ] `.per_layer_pair()` groups edges by (src_layer, dst_layer)
- [ ] Operations in grouping context apply per group
- [ ] `.coverage(mode="all")` keeps items in all groups
- [ ] `.coverage(mode="k", k=2)` keeps items in ≥2 groups
- [ ] `.aggregate()` computes per-group statistics

**Uncertainty Quantification**:
- [ ] UQ results have correct format (mean, std, quantiles, certainty)
- [ ] UQ priority order: per-metric > query-level > global > defaults
- [ ] `.to_pandas(expand_uncertainty=True)` expands UQ columns correctly
- [ ] Bootstrap, perturbation, seed, and null_model methods work

**Temporal**:
- [ ] `.at(time)` filters to snapshot
- [ ] `.during(t_start, t_end)` filters to time range
- [ ] `.window(size, step)` iterates over windows

**Export**:
- [ ] `.to_pandas()` creates correct DataFrame
- [ ] `.to_networkx()` creates correct graph
- [ ] `.to_arrow()` creates correct table
- [ ] `.to_json()` serializes correctly
- [ ] `.to_csv(path)` writes to file

**Error Handling**:
- [ ] All errors extend DslError
- [ ] UnknownAttributeError includes suggestions
- [ ] UnknownMeasureError includes suggestions
- [ ] UnknownLayerError includes suggestions
- [ ] ParameterMissingError lists provided params
- [ ] GroupingError provides actionable message

**Provenance**:
- [ ] Provenance mode can be set to "replayable"
- [ ] `.is_replayable` checks for replayable provenance
- [ ] `.replay()` reconstructs and re-executes query

**Legacy Compatibility**:
- [ ] String DSL compiles to same AST as builder API
- [ ] Legacy layer syntax (LAYER("name") + LAYER("name")) works
- [ ] execute_query() function works with legacy strings

---

## Decision Guide: Which API When?

### Use DSL v2 (Q builder) when:
-  You need type-safe, IDE-autocomplete experience
-  Complex queries with grouping, aggregation, coverage
-  Uncertainty quantification required
-  Temporal network queries
-  Integration with other DSL features (dynamics, counterexamples)
-  Building reusable, parameterized queries
-  You're new to py3plex (most ergonomic API)

### Use Legacy DSL (string-based) when:
-  Quick one-off queries in notebooks
-  You prefer SQL-like syntax
-  Simple filtering and centrality computation
-  Backward compatibility with old scripts
-  Teaching/documentation (familiar SQL syntax)

### Use Dplyr-Style API when:
-  You're familiar with R's dplyr or pandas
-  Interactive data exploration in notebooks
-  Simple transformations (filter, mutate, arrange, select)
-  Converting results to DataFrames for analysis
-  NOT for complex multilayer-specific operations (use Q builder instead)

### Use Pipeline API when:
-  Sklearn-style workflow orchestration
-  Reproducible multi-step analysis pipelines
-  Caching intermediate results
-  Config-driven workflows from YAML/JSON
-  Research workflows requiring provenance

### Use CLI when:
-  Shell scripts and automation
-  Quick network statistics without Python
-  File format conversion
-  CI/CD integration

### Decision Tree: Computing Centrality

```
Need uncertainty quantification?
├─ YES → Use Q.nodes().compute(...).uq(...)
└─ NO
   ├─ Complex filtering (multilayer-specific)?
   │  └─ YES → Use Q.nodes().from_layers(L[...]).where(...).compute(...)
   └─ Simple layer filtering?
      ├─ YES → Use execute_query("SELECT nodes WHERE layer='X' COMPUTE ...")
      └─ NO (single-layer or all layers)
         └─ Use networkx directly: nx.betweenness_centrality(net.core_network)
```

### Decision Tree: Network Analysis Workflow

```
Start with network file (CSV, edgelist, etc.)
├─ Load: net.load_network("file.csv", input_type="edgelist")
├─ Explore structure: net.get_layers(), len(net.get_nodes()), len(net.get_edges())
├─ Query:
│  ├─ Descriptive stats → Q.nodes().per_layer().aggregate(...)
│  ├─ Top nodes → Q.nodes().per_layer().top_k(...)
│  └─ Specific patterns → Q.edges().where(intralayer=True).per_layer_pair().aggregate(...)
├─ Analysis:
│  ├─ Centrality with uncertainty → Q.nodes().compute(...).uq(...)
│  ├─ Community detection → from py3plex.algorithms.community_detection import louvain; louvain(net)
│  └─ Dynamics → Q.dynamics("SIS", ...).run(...).execute(net)
└─ Export: result.to_pandas().to_csv("output.csv")
```

---

## Legacy DSL (String-Based)

For backward compatibility, py3plex supports SQL-like string queries.

### Syntax

```
SELECT target WHERE conditions COMPUTE measures
```

### Core Function

```python
from py3plex.dsl import execute_query, format_result

result = execute_query(network, 'SELECT nodes WHERE degree > 5')
print(format_result(result))
```

### Examples

```python
# Select by layer
execute_query(net, 'SELECT nodes WHERE layer="social"')

# Filter by degree
execute_query(net, 'SELECT nodes WHERE degree > 2')

# Combine filters
execute_query(net, 'SELECT nodes WHERE layer="social" AND degree > 2')

# Compute centrality
execute_query(net, 'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality')

# Multiple measures
execute_query(net, 'SELECT nodes WHERE degree > 2 COMPUTE degree_centrality closeness_centrality')
```

### Supported Operators

- Comparisons: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `AND`, `OR`, `NOT`
- Measures: degree, degree_centrality, betweenness_centrality, closeness_centrality, eigenvector_centrality, pagerank, clustering

### Result Structure (Dictionary)

```python
{
    'query': str,           # Original query string
    'target': str,          # 'nodes' or 'edges'
    'nodes': list,          # List of (node_id, layer) tuples
    'count': int,           # Number of items
    'computed': {           # Present if COMPUTE used
        'measure_name': {
            (node_id, layer): float,
            ...
        }
    },
    'meta': {               # Metadata including provenance
        'provenance': {...}
    }
}
```

### Convenience Functions

```python
from py3plex.dsl import (
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer
)

# Get nodes in layer
nodes = select_nodes_by_layer(net, 'social')

# Get high-degree nodes
high_deg = select_high_degree_nodes(net, min_degree=3)

# Compute centrality for layer
centrality = compute_centrality_for_layer(net, 'transport', 'degree_centrality')
```

### Limitations

-  No grouping or aggregation
-  No uncertainty quantification
-  No temporal queries
-  Limited edge queries
-  No layer algebra
- → **Use DSL v2 for these features**

---

## Dplyr-Style Operations

**NOTE**: As of v1.1.0, dplyr methods are integrated into DSL v2 builder (`Q.nodes()`, `Q.edges()`). The standalone `graph_ops` module remains for backward compatibility.

### Integrated DSL v2 Dplyr Methods

All dplyr-style methods work directly in the Q builder:

```python
from py3plex.dsl import Q, L

result = (
    Q.nodes()
     .from_layers(L["ppi"])
     .compute("degree")
     .filter(degree__gt=1)               # Dplyr-style filter
     .mutate(norm_deg=lambda r: r["degree"] / 3)
     .arrange("-degree")
     .head(10)
     .execute(net)
)

df = result.to_pandas()
```

### Available Dplyr Methods in DSL Builder

**Filtering**:
- `.filter(...)` - Alias for `.where()`
- `.filter_expr("degree > 5 and layer == 'social'")` - String expression filtering

**Sampling and Slicing**:
- `.head(n)` - First n items
- `.tail(n)` - Last n items
- `.sample(n, seed)` - Random sample
- `.slice(start, end)` - Array slicing
- `.first()` - First item only
- `.last()` - Last item only

**Transformation**:
- `.mutate(**transformations)` - Add/modify columns with lambdas
- `.select(*columns)` - Keep only specified columns
- `.rename(**mapping)` - Rename columns
- `.drop(*columns)` - Drop columns

**Ordering**:
- `.arrange(*columns, desc)` - Sort (alias for `.order_by()`)
- `.order_by(*keys, desc)` - Sort by keys

**Aggregation**:
- `.aggregate(**aggregations)` - Per-group statistics
- `.summarize(**aggregations)` - Alias for `.aggregate()`

**Misc**:
- `.collect()` - No-op for API compatibility
- `.pluck(field)` - Extract single column

### Standalone graph_ops (Backward Compatibility)

```python
from py3plex.graph_ops import nodes, edges

# Node operations
df = (
    nodes(net, layers=["ppi"])
    .filter(lambda n: n["degree"] > 1)
    .mutate(normalized_degree=lambda n: n["degree"] / 4)
    .arrange("degree", reverse=True)
    .head(3)
    .to_pandas()
)

# Group by and summarise
df = (
    nodes(net)
    .group_by("layer")
    .summarise(
        avg_degree=("degree", np.mean),
        max_degree=("degree", max),
        n_nodes=("id", len)
    )
    .to_pandas()
)
```

**Recommendation**: Use integrated DSL v2 methods for new code. Use standalone `graph_ops` only for legacy scripts.

---

## Pipeline API (Sklearn-Style)

py3plex provides sklearn-style pipelines for composable, reproducible workflows.

### Core Concepts

```python
from py3plex.pipeline import Pipeline, Step

# Define pipeline
pipeline = Pipeline([
    ("load", LoadStep(path="network.csv", input_type="edgelist")),
    ("stats", ComputeStatsStep(measures=["degree", "betweenness"])),
    ("filter", FilterStep(condition="degree > 5")),
    ("export", ExportStep(path="output.csv", format="csv"))
])

# Run pipeline
result = pipeline.fit(network)
```

### Built-in Steps

**I/O Steps**:
- `LoadStep` - Load network from file
- `ExportStep` - Export results to file

**Transformation Steps**:
- `ComputeStatsStep` - Compute centrality measures
- `FilterStep` - Filter nodes/edges
- `AggregateStep` - Per-layer aggregation

**Analysis Steps**:
- `CommunityDetectionStep` - Run community detection
- `CentralityStep` - Compute centrality with options
- `DynamicsStep` - Run dynamics simulation

**Custom Steps**:
```python
from py3plex.pipeline import BaseStep

class CustomStep(BaseStep):
    def __init__(self, param=1.0):
        self.param = param

    def fit(self, network, context=None):
        # Your logic here
        return result
```

### Config-Driven Workflows

```yaml
# workflow.yaml
pipeline:
  - step: load
    path: network.csv
    input_type: edgelist

  - step: compute_stats
    measures:
      - degree
      - betweenness_centrality

  - step: filter
    condition: "degree > 5"

  - step: export
    path: output.csv
    format: csv
```

```python
from py3plex.workflows import load_workflow, run_workflow

workflow = load_workflow("workflow.yaml")
result = run_workflow(workflow, network)
```

### Provenance

Pipelines track full provenance:

```python
result = pipeline.fit(network)
prov = result.meta['provenance']

# Pipeline execution trace
for step in prov['steps']:
    print(f"{step['name']}: {step['duration_ms']}ms")
```

---

## I/O and Data Loading

### Multi_layer_network Construction

```python
from py3plex.core import multinet

# Create empty network
net = multinet.multi_layer_network(directed=False)

# Add nodes (plural)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
])

# Add edges (plural)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
])
```

**CRITICAL API PATTERNS**:
- Use `add_nodes([...])` and `add_edges([...])` (plural) - singular forms don't exist
- Edge dict format: `{'source': ..., 'target': ..., 'source_type': ..., 'target_type': ...}`
- Node dict format: `{'source': ..., 'type': ...}`

### Load from File

```python
# Edgelist format (CSV)
net.load_network("network.csv", input_type="edgelist")

# GraphML
net.load_network("network.graphml", input_type="graphml")

# GML
net.load_network("network.gml", input_type="gml")

# JSON
net.load_network("network.json", input_type="json")

# Apache Arrow (high-performance)
from py3plex.io import load_from_arrow
net = load_from_arrow("network.arrow")
```

### Export to File

```python
# JSON
net.to_json("output.json")

# CSV (via query result)
result = Q.nodes().compute("degree").execute(net)
result.to_pandas().to_csv("output.csv", index=False)

# Arrow
from py3plex.io import save_to_arrow
save_to_arrow(result, "output.arrow")
```

### Built-in Datasets

```python
from py3plex.datasets import (
    load_aarhus_cs,
    load_imdb,
    load_example_multilayer,
    make_random_multilayer,
)

# Load real dataset
net = load_aarhus_cs()

# Generate random multilayer network
net = make_random_multilayer(
    n_nodes=100,
    n_layers=3,
    p_intra=0.1,
    p_inter=0.01,
    seed=42
)
```

---

## Dynamics Simulations

py3plex supports epidemic-style dynamics on multilayer networks.

### Built-in Processes

**SIS (Susceptible-Infected-Susceptible)**:
```python
sim = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .on_layers(L["contacts"])
     .seed_infections(0.01)  # 1% initial
     .run(steps=100, replicates=10)
     .execute(net)
)
```

**SIR (Susceptible-Infected-Recovered)**:
```python
sim = (
    Q.dynamics("SIR", beta=0.3, gamma=0.1)
     .on_layers(L["social"] + L["work"])
     .seed_infections(nodes=[('Alice', 'social')])
     .run(steps=200, replicates=5)
     .execute(net)
)
```

**SEIR (Susceptible-Exposed-Infected-Recovered)**:
```python
sim = (
    Q.dynamics("SEIR", beta=0.3, sigma=0.2, gamma=0.1)
     .on_layers(L["*"])
     .seed_infections(0.05)
     .run(steps=150, replicates=20)
     .execute(net)
)
```

**Random Walk**:
```python
sim = (
    Q.dynamics("RANDOM_WALK", restart_prob=0.15)
     .on_layers(L["social"])
     .starting_nodes([('Alice', 'social')])
     .run(steps=100, replicates=50)
     .execute(net)
)
```

### DynamicsBuilder Reference

#### Methods

##### .on_layers(layer_expr) → DynamicsBuilder

Specify layers for simulation.

**Args**: layer_expr from `L[...]`

##### .seed_infections(fraction=None, nodes=None) → DynamicsBuilder

Initialize infections.

**Args**:
- `fraction` (float): Fraction of nodes to infect randomly (e.g., 0.01 for 1%)
- `nodes` (list): Specific nodes to infect (list of (node, layer) tuples)

##### .starting_nodes(nodes) → DynamicsBuilder

Set starting nodes for random walk.

**Args**: `nodes` - List of (node, layer) tuples

##### .run(steps, replicates, track="all") → DynamicsBuilder

Configure simulation execution.

**Args**:
- `steps` (int): Number of simulation steps
- `replicates` (int): Number of independent runs
- `track` (str): What to track - "all", "infected", "peak_time", etc.

##### .execute(network) → DynamicsResult

Run simulation and return results.

**Returns**: DynamicsResult with trajectories, statistics, provenance

### DynamicsResult

```python
# Access trajectories
sim.trajectories  # DataFrame with columns: step, replicate, susceptible, infected, recovered

# Summary statistics
print(sim.mean_peak_time)
print(sim.mean_final_infected)

# Per-replicate data
for rep in range(sim.n_replicates):
    traj = sim.trajectories[sim.trajectories['replicate'] == rep]
    # Analyze individual trajectory
```

### Custom Dynamics (Advanced)

```python
def custom_process(node, state, neighbors, params):
    """Custom dynamics process.

    Args:
        node: Current node (tuple: (id, layer))
        state: Current state dict
        neighbors: List of neighbor nodes
        params: Process parameters

    Returns:
        new_state: Updated state for node
    """
    # Your logic here
    return new_state

sim = (
    Q.dynamics("CUSTOM", process_func=custom_process, alpha=0.5)
     .on_layers(L["*"])
     .run(steps=100, replicates=10)
     .execute(net)
)
```

---

## Uncertainty Quantification

### Overview

Uncertainty Quantification (UQ) in py3plex provides confidence intervals, stability metrics, and distributional information for network analysis results. UQ is integrated into DSL v2 and is essential for robust, reproducible research.

### Correctness Guarantees

**Determinism**:
- All UQ methods are **fully deterministic** when seeded ✅
- Same `seed` parameter produces **identical confidence intervals** across runs (verified in tests)
- Bootstrap, perturbation, and null model methods all respect `seed`

**Monotonicity**:
- **CI stability**: Larger `n_samples` → more stable confidence intervals
- **Coverage guarantee**: Confidence intervals use standard bootstrap percentile method
- **Finiteness**: All CI bounds are finite (no NaN/inf), verified in tests ✅

**Special cases**:
- **Deterministic algorithms with seed**: `std = 0`, CI width = 0 (verified) ✅
- **Empty groups**: Handled gracefully with explicit error messages (no silent failures)
- **Single-node groups**: UQ still computes, but CI may be degenerate

**Reproducibility**:
```python
# ✅ Guaranteed to produce identical CIs
result1 = Q.nodes().compute("betweenness").uq(seed=42, n_samples=100).execute(net)
result2 = Q.nodes().compute("betweenness").uq(seed=42, n_samples=100).execute(net)

# Extract CIs
df1 = result1.to_pandas(expand_uncertainty=True)
df2 = result2.to_pandas(expand_uncertainty=True)
assert df1.equals(df2)  # ✅ Identical
```

py3plex provides first-class uncertainty quantification for network metrics.

### Methods

**Bootstrap Resampling**:
```python
result = (
    Q.nodes()
     .compute("pagerank", "betweenness_centrality")
     .uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
     .execute(net)
)
```

**Perturbation**:
```python
result = (
    Q.nodes()
     .compute("degree", "clustering")
     .uq(method="perturbation", n_samples=50, noise_level=0.1, seed=42)
     .execute(net)
)
```

**Stratified Perturbation** (NEW - Variance-Reduced):
```python
# Auto-select stratification dimensions
result = (
    Q.nodes()
     .compute("betweenness_centrality")
     .uq(method="stratified_perturbation", n_samples=100, edge_drop_p=0.1, seed=42)
     .execute(net)
)

# Explicit stratification by degree with custom bins
result = (
    Q.nodes()
     .compute("pagerank")
     .uq(
         method="stratified_perturbation",
         n_samples=100,
         strata=["degree"],
         bins={"degree": 5},
         edge_drop_p=0.05,
         seed=42
     )
     .execute(net)
)

# Composite stratification (degree + layer)
result = (
    Q.nodes()
     .compute("clustering")
     .uq(
         method="stratified_perturbation",
         n_samples=100,
         strata=["degree", "layer"],
         bins={"degree": 5},
         edge_drop_p=0.1,
         seed=42
     )
     .execute(net)
)

# Edge stratification (layer_pair for edge metrics)
result = (
    Q.edges()
     .compute("edge_betweenness_centrality")
     .uq(
         method="stratified_perturbation",
         n_samples=100,
         strata=["layer_pair"],
         edge_drop_p=0.1,
         seed=42
     )
     .execute(net)
)
```

**Multi-seed (Deterministic Metrics)**:
```python
result = (
    Q.nodes()
     .compute("louvain_community")
     .uq(method="seed", n_samples=20, seed=42)
     .execute(net)
)
```

### Stratified Perturbation Features

**Variance Reduction**: Stratified resampling preserves key network structure (degree distribution, layer densities, edge weight distribution) during perturbation, reducing estimator variance without increasing sample count.

**Stratification Dimensions**:
- `degree`: Node degree quantiles (default for node queries)
- `layer`: Per-layer grouping
- `layer_pair`: Source-destination layer pairs (default for edge queries)
- `weight`: Edge weight quantiles

**Auto-Selection**: If `strata` is omitted or `None`, py3plex automatically selects appropriate dimensions based on query type.

**Deterministic**: Same seed → identical results across runs and parallel executions (uses `numpy.random.SeedSequence`).

**Metadata**: Results include stratification info in `result.meta["stratification"]` and `result.meta["n_strata"]`.

**Fallback**: If stratification is infeasible (e.g., network too small, no meaningful strata), automatically falls back to regular perturbation.

### Bootstrap Units

```python
# Resample edges
.uq(method="bootstrap", bootstrap_unit="edges", n_samples=100)

# Resample nodes
.uq(method="bootstrap", bootstrap_unit="nodes", n_samples=100)

# Resample layers (entire layers)
.uq(method="bootstrap", bootstrap_unit="layers", n_samples=50)
```

### Bootstrap Modes

```python
# Resample with replacement
.uq(method="bootstrap", bootstrap_mode="resample", n_samples=100)

# Permutation (shuffle labels)
.uq(method="bootstrap", bootstrap_mode="permute", n_samples=100)
```

### Result Expansion

```python
result = Q.nodes().compute("pagerank").uq(method="bootstrap", n_samples=100, ci=0.95, seed=42).execute(net)

df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, pagerank_mean, pagerank_std, pagerank_ci95_low, pagerank_ci95_high
```

### Null Model Comparison

```python
from py3plex.nullmodels import configuration_model

# Generate null model
null_net = configuration_model(net, seed=42)

# Compute metric on observed and null
observed = Q.nodes().compute("betweenness").execute(net)
null_result = Q.nodes().compute("betweenness").execute(null_net)

# Compare distributions
import scipy.stats as stats
z_score = (observed.attributes['betweenness'] - null_result.attributes['betweenness'].mean()) / null_result.attributes['betweenness'].std()
```

### Global UQ Defaults

```python
from py3plex.dsl import UQ

# Set defaults
UQ.defaults(method="bootstrap", n_samples=100, ci=0.95, seed=42, bootstrap_unit="edges")

# Now all queries with uncertainty=True use these
Q.nodes().compute("pagerank", uncertainty=True).execute(net)
```



### 9.2 Partition UQ (Community Detection) — **NEW in v1.1**

**Goal**: Quantify uncertainty in community partitions, not just numeric scores.

Answers: (1) How stable is the partition? (2) Which nodes are ambiguous? (3) Which pairs reliably co-cluster? (4) What is consensus?

#### Basic Usage

```python
from py3plex.dsl import Q
from py3plex.uncertainty.noise_models import EdgeDrop

result = (
    Q.nodes()
     .community(method="leiden", gamma=1.2, random_state=42)
     .uq(
        method="perturbation",
        noise_model=EdgeDrop(p=0.1),
        n_samples=100,
        seed=42
     )
     .execute(net)
)

df = result.to_pandas()
print(df[["node", "community_id", "community_entropy", "community_confidence"]])
print(result.meta["uq"]["stability"])  # VI, NMI, etc.
```

#### UQ Methods

**Seed** (fastest): `.uq(method="seed", n_samples=50, seed=42)` - Algorithm stochasticity
**Perturbation** (most informative): `.uq(method="perturbation", noise_model=EdgeDrop(p=0.1), n_samples=100)` - Network robustness
**Noise Models**: `EdgeDrop(p)`, `WeightNoise(dist, sigma)`, `LayerDrop(p)`

#### Storage Modes

- `store="none"`: Only summary stats (minimal memory)
- `store="sketch"`: Sparse co-assignment matrix (default)
- `store="samples"`: Full samples (only for small networks)

#### Output

**Attributes per node**: `community_id`, `community_entropy`, `community_confidence`
**Metadata**: `result.meta["uq"]["stability"]` (VI, NMI, mean_entropy, boundary_nodes)
**PartitionUQ object**: `result.meta["partition_uq"]` (consensus, co-assignment, node summaries)

#### Interpreting Results

- **Stable**: VI < 0.2, NMI > 0.9, mean_confidence > 0.85
- **Moderate**: VI < 0.5, NMI > 0.8, mean_confidence > 0.7
- **Unstable**: VI > 0.5 or NMI < 0.7 → Tune γ or refine data

**Node Entropy**: Low (<0.5) = consistent, High (>1.0) = ambiguous
**Confidence**: High (>0.8) = clear, Low (<0.6) = boundary node


### When to Use Which UQ Method

**Use `stratified_perturbation` when**:
- You want **lower variance** estimates without increasing sample count
- Network has **heterogeneous structure** (varying degrees, multiple layers, weighted edges)
- You need **production-quality** confidence intervals with fewer samples
- Computing metrics is expensive and you want to minimize runs
- Network structure should be preserved during uncertainty estimation

**Use `perturbation` when**:
- You want simple, general-purpose uncertainty estimation
- Network is small or homogeneous
- Stratification overhead is not worthwhile
- You want the most straightforward approach

**Use `bootstrap` when**:
- You need to test **sampling variability**
- You want to understand effect of data collection biases
- You're performing hypothesis testing via resampling

**Use `seed` when**:
- The metric itself is stochastic (e.g., community detection)
- You want to quantify algorithmic randomness
- Network structure should **not** be perturbed


### Agent Guidelines for UQ

**When building pipelines**:
1. Default to `stratified_perturbation` for production-quality UQ with minimal cost
2. Use `n_samples=100` for stratified (equivalent to `n_samples=200+` for regular perturbation)
3. Always specify `seed` for reproducibility
4. Let auto-selection choose stratification dimensions unless you have domain knowledge

**Example Decision Tree**:
```python
# High-stakes analysis requiring tight CIs → stratified_perturbation
Q.nodes().compute("pagerank").uq(method="stratified_perturbation", n_samples=100, seed=42).execute(net)

# Quick exploratory analysis → perturbation
Q.nodes().compute("degree").uq(method="perturbation", n_samples=50, edge_drop_p=0.1, seed=42).execute(net)

# Stochastic algorithm (Leiden) → seed
Q.nodes().community(method="leiden").uq(method="seed", n_samples=50, seed=42).execute(net)

# Testing data robustness → bootstrap
Q.nodes().compute("betweenness").uq(method="bootstrap", bootstrap_unit="edges", n_samples=100, seed=42).execute(net)
```


### Sensitivity Analysis

**PSEUDOCODE** (Feature planned):
```python
sensitivity = (
    Q.sensitivity()
     .on_metric("pagerank")
     .perturb_edges(fraction=0.1, n_trials=50)
     .measure_ranking_stability()
     .execute(net)
)

print(f"Ranking correlation: {sensitivity.kendall_tau_mean}")
```

---

## Temporal Networks

py3plex supports time-stamped edges and temporal queries.

### TemporalMultiLayerNetwork

```python
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

# Create temporal network
tnet = TemporalMultiLayerNetwork()

# Add edges with time attributes
tnet.add_edge('A', 'B', layer='social', t_start=100.0, t_end=200.0)
tnet.add_edge('B', 'C', layer='social', t=150.0)  # Point-in-time
tnet.add_edge('C', 'D', layer='work', t_start=120.0, t_end=180.0)
```

### Temporal Queries

**Snapshot at time t**:
```python
result = Q.edges().at(150.0).execute(tnet)
```

**Time range**:
```python
result = Q.edges().during(100.0, 200.0).execute(tnet)
```

**Before/After**:
```python
result = Q.edges().before(150.0).execute(tnet)
result = Q.edges().after(100.0).execute(tnet)
```

**Sliding Windows**:
```python
result = (
    Q.edges()
     .window(size=100.0, stride=50.0)  # 100-unit windows, 50-unit stride
     .per_window()
     .aggregate(edge_count="count()", avg_weight="mean(weight)")
     .execute(tnet)
)
```

### Temporal Snapshots

```python
# Get snapshot as static network
snapshot = tnet.get_snapshot(time_range=(100.0, 150.0))

# Query snapshot
result = Q.nodes().compute("degree").execute(snapshot)
```

### Temporal Aggregation

```python
# Count edges per time window per layer
result = (
    Q.edges()
     .window(size=50.0, stride=50.0)
     .per_layer_pair()
     .aggregate(
         edge_count="count()",
         active_nodes="count_unique(source)"
     )
     .execute(tnet)
)
```

---

## Null Models and Statistical Testing

py3plex provides null model generators for hypothesis testing.

### Configuration Model

```python
from py3plex.nullmodels import configuration_model

# Generate degree-preserving null model
null_net = configuration_model(net, seed=42)

# Multiple replicates
null_nets = [configuration_model(net, seed=i) for i in range(100)]
```

**Properties**:
- Preserves degree sequence
- Randomizes edge placement
- Preserves layer structure

### Erdős-Rényi Model

```python
from py3plex.nullmodels import erdos_renyi_multilayer

null_net = erdos_renyi_multilayer(
    n_nodes=100,
    n_layers=3,
    p=0.1,  # Edge probability
    seed=42
)
```

### Random Graph with Layer Structure

```python
from py3plex.nullmodels import random_multilayer

null_net = random_multilayer(
    n_nodes=100,
    layers=['social', 'work', 'family'],
    p_intra=0.15,  # Intra-layer edge prob
    p_inter=0.01,  # Inter-layer edge prob
    seed=42
)
```

### Statistical Testing Pattern

```python
# Compute observed statistic
observed_stat = Q.nodes().compute("betweenness").execute(net).attributes['betweenness'].mean()

# Generate null distribution
null_stats = []
for i in range(100):
    null_net = configuration_model(net, seed=i)
    null_stat = Q.nodes().compute("betweenness").execute(null_net).attributes['betweenness'].mean()
    null_stats.append(null_stat)

# p-value
p_value = sum(ns >= observed_stat for ns in null_stats) / len(null_stats)
print(f"p-value: {p_value}")
```

### Null Model Builder (DSL Extension)

```python
from py3plex.dsl import N

# Generate null models via DSL
null_models = (
    N.configuration()
     .samples(100)
     .seed(42)
     .preserve_layers(True)
     .execute(net)
)

# Use for testing
for null_net in null_models:
    # Analyze null network
    pass
```

---

## Counterexample Generation

Find violations of network invariants with minimal witness subgraphs.

### Basic Usage

```python
from py3plex.dsl import Q

cex = (
    Q.counterexample()
     .claim("degree__ge(k) -> pagerank__rank_le(r)")
     .params(k=10, r=50)
     .seed(42)
     .execute(net)
)

if cex:
    print(cex.explain())
    witness = cex.subgraph  # Minimal subgraph demonstrating violation
```

### Claim Language

**Format**: `antecedent -> consequent`

**Value-based predicates**:
- `degree__ge(k)` - degree >= k
- `degree__gt(k)` - degree > k
- `pagerank__lt(x)` - pagerank < x
- `betweenness_centrality__ge(x)` - betweenness >= x

**Rank-based predicates**:
- `pagerank__rank_gt(r)` - pagerank rank > r (lower rank)
- `pagerank__rank_le(r)` - pagerank rank <= r (higher or equal rank)

**Comparators**: `gt`, `ge`, `gte`, `lt`, `le`, `lte`, `eq`, `ne`

### Examples

```python
# High degree doesn't guarantee high PageRank
cex = Q.counterexample().claim("degree__ge(10) -> pagerank__rank_le(50)").params(k=10, r=50).seed(42).execute(net)

# High betweenness doesn't guarantee low rank
cex = Q.counterexample().claim("betweenness_centrality__ge(0.1) -> pagerank__rank_gt(100)").params(x=0.1, r=100).seed(42).execute(net)
```

### Counterexample Object

**Attributes**:
- `cex.subgraph` - Witness network (multi_layer_network)
- `cex.violation` - Violation details (node, metrics, margins)
- `cex.witness_nodes` - Set of (node, layer) tuples
- `cex.witness_edges` - Set of edge tuples
- `cex.minimization` - Minimization report (is_minimal, tests_used, strategy)
- `cex.meta['provenance']` - Full provenance

**Methods**:
- `cex.explain()` - Human-readable explanation
- `cex.to_dict()` - JSON-serializable representation

### Configuration

```python
cex = (
    Q.counterexample()
     .claim("degree__ge(k) -> pagerank__rank_le(r)")
     .params(k=10, r=50)
     .seed(42)
     .find_minimal(True)  # Enable minimization (default: True)
     .budget(max_tests=200, max_witness_size=500)
     .layers(L["social"] + L["work"])  # Restrict search to specific layers
     .execute(net)
)
```

### Integration with Query Results

```python
result = Q.nodes().compute("degree", "pagerank").execute(net)

cex = result.counterexample(
    claim="degree__ge(k) -> pagerank__rank_le(r)",
    params={"k": 10, "r": 50},
    seed=42
)
```

### Error Handling

```python
from py3plex.counterexamples.claim_lang import ClaimParseError
from py3plex.counterexamples.engine import CounterexampleNotFound

try:
    cex = Q.counterexample().claim("invalid syntax").execute(net)
except ClaimParseError as e:
    print(f"Invalid claim: {e}")

try:
    cex = Q.counterexample().claim("degree__ge(k) -> pagerank__rank_le(r)").params(k=100, r=1).execute(net)
except CounterexampleNotFound:
    print("No violation found - claim holds for this network")
```

---

## Claim Learning (Hypothesis Discovery)

Automatically discover plausible, interpretable claims from network data.

### Basic Usage

```python
from py3plex.dsl import Q

claims = (
    Q.learn_claims()
     .from_metrics(["degree", "pagerank", "betweenness_centrality"])
     .min_support(0.9)      # At least 90% support
     .min_coverage(0.05)    # At least 5% of nodes
     .max_claims(20)        # Return top 20
     .seed(42)              # Deterministic
     .execute(net)
)

for claim in claims:
    print(f"{claim.claim_string}")
    print(f"  Support: {claim.support:.3f}, Coverage: {claim.coverage:.3f}")
```

### Advanced Configuration

```python
claims = (
    Q.learn_claims()
     .from_metrics(["degree", "strength", "pagerank", "betweenness"])
     .cheap_metrics(["degree", "strength"])      # Use for antecedents
     .target_metrics(["pagerank", "betweenness"]) # Use for consequents
     .layers(L["social"] + L["work"])             # Learn for specific layers
     .min_support(0.85)
     .min_coverage(0.1)
     .max_antecedents(1)  # MVP: only 1 antecedent term supported
     .seed(42)
     .execute(net)
)
```

### Claim Object

**Attributes**:
- `claim_string` - DSL-compatible claim (e.g., "degree__gte(10.0) -> pagerank__rank_lte(50)")
- `antecedent` - Antecedent predicate
- `consequent` - Consequent predicate
- `support` - Statistical support (0.0-1.0)
- `coverage` - Coverage (0.0-1.0)
- `score` - ClaimScore with detailed statistics
- `meta['provenance']` - Full provenance

**Methods**:
- `claim.counterexample(net, **kwargs)` - Find counterexample
- `claim.to_dict()` - JSON-serializable

### Integration with Counterexamples

```python
# Learn claims
claims = Q.learn_claims().from_metrics(["degree", "pagerank"]).min_support(0.8).execute(net)

# Test each claim
for claim in claims:
    cex = claim.counterexample(net, seed=42)
    if cex:
        print(f" {claim.claim_string}: falsified")
    else:
        print(f" {claim.claim_string}: holds (support={claim.support:.3f})")
```

### Interpretation Warning

**Claims are hypotheses, not truths.**

- Support < 1.0 means exceptions exist
- High support ≠ causation
- Claims are inductive (summarize observed patterns)
- Always validate on held-out data or additional networks
- Document provenance for audit trails

**Best Practices**:
1. Use min_support >= 0.9 for reliable claims
2. Use min_coverage >= 0.05 to avoid overfitting
3. Always set seed for reproducibility
4. Test with counterexample engine
5. Validate on multiple networks

---


## Semiring Algebra (Paths, Closure, Fixed-Point)

**Formal Definitions (Verbatim from Specification)**

**Definition (Semiring).**
A semiring is a tuple (K, ⊕, ⊗, 0, 1) where K is a set and ⊕, ⊗ are binary operations on K such that:
1) (K, ⊕, 0) is a commutative monoid: ⊕ is associative and commutative, and 0 is the identity (a ⊕ 0 = a).
2) (K, ⊗, 1) is a monoid: ⊗ is associative and 1 is the identity (a ⊗ 1 = 1 ⊗ a = a).
3) ⊗ distributes over ⊕: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c), and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a).
4) 0 is absorbing for ⊗: 0 ⊗ a = a ⊗ 0 = 0.

**Note**: Some useful semirings relax commutativity of ⊕; this library supports both "strict" and "relaxed" modes.

**Definition (Lift).**
Given an edge e, lift : Edge → K maps edge attributes into semiring space.

**Definition (Path algebra).**
For a walk w = (e1, e2, ..., ek), its semiring weight is: W(w) = lift(e1) ⊗ lift(e2) ⊗ ... ⊗ lift(ek).

**Definition (Closure).**
A* = I ⊕ A ⊕ A^2 ⊕ A^3 ⊕ ... where I[u,u]=1 and I[u,v]=0 for u≠v.

### Package Structure

- **py3plex/semiring/core.py** - SemiringSpec dataclass with bounded validation
- **py3plex/semiring/registry.py** - Registry with built-in semirings
- **py3plex/semiring/types.py** - Type definitions (EdgeView, LiftFn, PathResult)
- **py3plex/semiring/engine.py** - Path and closure algorithms
- **py3plex/semiring/pareto.py** - Multiobjective Pareto frontier support
- **py3plex/dsl/builder.py** - S builder (lines 3869-4255)
- **py3plex/dsl/executor_semiring.py** - Execution logic

### Built-in Semirings

1. **min_plus** - Shortest paths (K=ℝ∪{∞}, ⊕=min, ⊗=+, 0=∞, 1=0)
2. **boolean** - Reachability (K={False,True}, ⊕=or, ⊗=and, 0=False, 1=True)
3. **max_times** - Most reliable paths (K=[0,1], ⊕=max, ⊗=×, 0=0, 1=1)
4. **tropical_lex** - Lexicographic (K=(cost, switches), ⊕=lex-min, ⊗=component-add)

### S — Semiring Builder

```python
from py3plex.dsl import S, L

# Shortest paths (min_plus)
result = (
    S.paths()
     .from_node("Alice")
     .to_node("Bob")                    # Optional: omit for all-pairs
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .from_layers(L["social"] + L["work"])
     .max_hops(10)                      # Required for non-idempotent semirings without leq
     .witness(True)                     # Request path witnesses
     .algorithm("auto")                 # auto|dijkstra|bellman_ford
     .execute(net)
)

# Boolean reachability
result = (
    S.paths()
     .from_node("Alice")
     .semiring("boolean")
     .lift(attr=None, default=True)     # All edges contribute True
     .execute(net)
)

# All-pairs closure
result = (
    S.closure()
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .max_hops(10)                      # Required for large networks
     .execute(net)
)

# Custom semiring
from py3plex.semiring import SemiringSpec, register_semiring
import math

custom = SemiringSpec(
    name="my_semiring",
    zero=math.inf,
    one=0.0,
    plus=lambda a, b: min(a, b),
    times=lambda a, b: a + b,
    strict=True,
    is_idempotent_plus=True,
    examples=(0.0, 1.0, 2.0, math.inf),
)
register_semiring(custom, overwrite=True)

result = S.paths().from_node('A').semiring('my_semiring').execute(net)
```

### Key Methods

**S.paths()** - Create semiring path query:
- `.from_node(source)` - Required: source node
- `.to_node(target)` - Optional: target node (omit for all nodes)
- `.semiring(name)` - Semiring name or spec
- `.lift(attr="weight", default=1.0)` - Edge weight extraction
- `.from_layers(L[...])` - Layer filter
- `.max_hops(n)` - Maximum path length (required for non-idempotent without leq)
- `.witness(True)` - Request path witnesses
- `.algorithm("auto"|"dijkstra"|"bellman_ford")` - Algorithm selection
- `.execute(net)` - Execute query

**S.closure()** - Create closure query:
- `.semiring(name)` - Semiring name
- `.lift(attr="weight", default=1.0)` - Edge weight extraction
- `.from_layers(L[...])` - Layer filter
- `.max_hops(n)` - Required for large networks (default threshold: 100 nodes)
- `.execute(net)` - Execute query

### Critical Implementation Notes

**max_hops Requirement**:
- Non-idempotent semirings WITHOUT `leq` ordering REQUIRE explicit `max_hops`
- If omitted, error is raised with actionable message
- If non-idempotent WITH `leq` ordering but no `max_hops`: warning issued, safe default used
- Closure on networks > 100 nodes requires `max_hops` unless size_threshold increased

**Algorithm Selection (auto mode)**:
- Uses Dijkstra for: min_plus OR (idempotent_plus AND leq exists)
- Falls back to Bellman-Ford otherwise
- Explicit override with `.algorithm("dijkstra"|"bellman_ford")`

**Determinism**:
- All operations deterministic with fixed random seeds
- Registry ordering: alphabetical (stable)
- Pareto frontier: deterministic ordering via stable sort

**Provenance**:
- `result.meta['provenance']['algebra']['semiring']['name']` - Semiring used
- `result.meta['provenance']['algorithm']` - Algorithm selected
- `result.meta['provenance']['relaxations']` - Iteration count
- `result.meta['provenance']['performance']['total_ms']` - Timing

### Common Pitfalls

1. **Forgetting max_hops for non-idempotent semirings**: Will raise SemiringExecutionError
2. **Large closure without max_hops**: Network > 100 nodes requires explicit bound
3. **Assuming all semirings use Dijkstra**: Only works for monotone ordered semirings
4. **Path witnesses without .witness(True)**: Path reconstruction requires explicit request

### File Locations

- Core: `py3plex/semiring/{core,registry,types,engine,pareto}.py`
- DSL: `py3plex/dsl/{builder,executor_semiring}.py` (S builder)
- Tests: `tests/test_semiring_*.py` (verification, negative cases, etc.)
- Examples: `examples/network_analysis/semiring_{paths,boolean,tropical_lex,pareto}.py`
- Docs: `docfiles/user_guide/dsl.rst` (Semiring Algebra section)

---

## Community Detection and Queries

### Basic Community Detection

```python
from py3plex.dsl import Q

# Run Leiden algorithm
result = (
    Q.nodes()
     .community(method="leiden", gamma=1.2, random_state=42)
     .execute(network)
)

# With UQ for stability
result = (
    Q.nodes()
     .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
     .uq(method="ensemble", n_samples=50, seed=42)
     .execute(network)
)
print(f"Consensus partition: {result.meta['consensus_partition']}")
print(f"Score CI: {result.meta['score_ci']}")
```

### AutoCommunity: Automatic Algorithm Selection

**Purpose**: Automatically select the best community detection algorithm based on multi-metric evaluation and a "most wins" decision engine.

**How it works**:
1. Detects available algorithms (Leiden, Louvain, etc.) and metrics (modularity, coverage, stability, etc.)
2. Runs candidate algorithms with parameter grids
3. Evaluates on multiple quality metrics (bucketed by category)
4. Selects winner using pairwise "most wins" logic with bucket caps
5. Optionally uses UQ to gate wins by statistical significance

**Functional API**:
```python
from py3plex.algorithms.community_detection import auto_select_community

# Basic auto-selection
result = auto_select_community(network, fast=True, seed=42)

# Access results
print(result.explain())              # Why this algorithm won
print(result.leaderboard)            # Rankings of all candidates
net.assign_partition(result.partition)

# With UQ for stability-aware selection
result = auto_select_community(
    network,
    uq=True,
    uq_n_samples=50,
    uq_method="seed",
    seed=42
)
```

**DSL API**:
```python
from py3plex.dsl import Q

# Auto-select via DSL
result = Q.communities().auto_select(fast=True, seed=42).execute(network)
print(result.explain())
print(result.leaderboard)

# With UQ
result = (
    Q.communities()
     .auto_select(fast=True, seed=42)
     .uq(method="seed", n_samples=50, seed=42)
     .execute(network)
)
```

**Result Object** (`AutoCommunityResult`):
- `result.partition`: Winning partition
- `result.algorithm`: Algorithm name and parameters
- `result.leaderboard`: DataFrame with all candidates ranked by wins
- `result.explain(n=5)`: Natural language explanation of why the winner won
- `result.provenance`: Full detection and selection metadata
- `result.to_dict()`: Serializable dictionary

**Key Parameters**:
- `fast=True`: Use smaller parameter grids (default)
- `max_candidates=10`: Maximum number of algorithms to evaluate
- `seed=0`: Master random seed for deterministic results
- `uq=False`: Enable uncertainty quantification (stability metrics)
- `uq_method="seed"`: UQ method (seed, perturbation, bootstrap)
- `uq_n_samples=10`: Number of UQ samples

**Selection Logic**:
- **Pairwise wins**: Each metric compares all pairs of contestants (winner gets 1, loser gets 0, ties get 0.5 each)
- **Bucket caps**: Prevents any single metric category from dominating (e.g., max 30 points from "objective" metrics)
- **Tie-breaking**: (1) Total wins, (2) Stability wins, (3) Lower runtime, (4) Lexicographic by ID
- **UQ gating** (optional): Wins only count if statistically significant under perturbation

**Metric Buckets**:
- `objective`: Modularity, objective scores (cap: 30)
- `structure`: Coverage, cut ratio, density, **replica_consistency** (cap: 30)
- `sanity`: Singleton fraction, size entropy, community count deviation, **layer_entropy** (cap: 30)
- `stability`: Node entropy, VI, NMI from UQ (cap: 30, requires `uq=True`)
- `runtime`: Execution time (cap: 10)
- `predictive`: Reserved for future use (cap: 30)

**Multilayer Quality Metrics (Guardrails)**:

Two multilayer-specific metrics serve as guardrails against degenerate partitions:

1. **replica_consistency** (bucket: structure, weight: 0.15):
   - Measures whether replicas of the same node across layers are assigned to the same community
   - Range: [0, 1], where 1.0 = perfect coherence, 0.0 = random
   - Formula: For each node v, compute pairwise agreement of community labels across layers
   - Label-permutation invariant (compares labels within-node only)
   - Typical ranges: >0.8 = excellent, 0.5-0.8 = good, <0.5 = poor

2. **layer_entropy** (bucket: sanity, weight: 0.07):
   - Measures the balance of community sizes within each layer, averaged across layers
   - Range: [0.1, 0.9] (clipped to prevent extreme values)
   - Formula: Normalized Shannon entropy of community sizes per layer, then averaged
   - Clipping prevents giant clusters (H→0) or extreme fragmentation from dominating
   - Typical ranges: >0.7 = well-balanced, 0.3-0.7 = normal, <0.3 = degenerate

**When to use**:
- Exploring new datasets without prior knowledge of best algorithm
- Want statistically-backed algorithm selection
- Need reproducible algorithm choice with provenance
- Comparing algorithms fairly across multiple quality dimensions

---

### Successive Halving: Efficient Algorithm Racing

**Purpose**: Efficiently race multiple community detection algorithms using increasing computational budgets with progressive elimination. This is a first-class strategy for AutoCommunity that reduces computational cost while maintaining selection quality.

**How it works**:
1. Start with all candidate algorithms
2. Evaluate each on a small budget (e.g., max_iter=5, uq_samples=10)
3. Compute utilities (UQ-aware) and eliminate worst performers
4. Increase budget and repeat with survivors
5. Return winner when one algorithm remains

**Key advantages**:
- **Efficiency**: Quickly eliminates poor algorithms with minimal computation
- **UQ-aware**: Utilities computed from distributions, not point estimates
- **Deterministic**: Fully reproducible with seed control (including parallel execution)
- **Provenance-rich**: Complete racing history with per-round budgets and metrics
- **Configurable**: Customizable budgets, utility functions, and elimination strategies

**Builder API**:
```python
from py3plex.algorithms.community_detection import AutoCommunity

# Basic Successive Halving
result = (
    AutoCommunity()
      .candidates("louvain", "leiden", "label_propagation")
      .metrics("modularity", "coverage")
      .strategy("successive_halving", eta=3, rounds=2)
      .seed(42)
      .execute(network)
)

# Access racing history
history = result.provenance["racing_history"]
print(f"Rounds: {len(history['rounds'])}")
print(f"Winner: {history['winner_algo_id']}")
print(f"Total runtime: {history['total_runtime_ms']:.2f} ms")

# Inspect elimination progression
for i, round_rec in enumerate(history["rounds"]):
    print(f"Round {i}: {len(round_rec['algorithms'])} algorithms")
    print(f"  Survivors: {round_rec['survivors']}")
    print(f"  Eliminated: {round_rec['eliminated']}")
```

**Configuration Parameters**:
```python
# Custom budget schedule
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity", "coverage")
      .strategy(
          "successive_halving",
          eta=3,                  # Elimination factor (keep top 1/3 each round)
          rounds=3,               # Number of rounds (None = auto-compute)
          budget0={               # Initial budget
              "max_iter": 10,
              "n_restarts": 1,
              "uq_samples": 15,
          },
          budget_growth=3.0,      # Budget growth factor per round
          utility_method="mean_minus_std",  # Utility function
          utility_lambda=1.0,     # Lambda for mean_minus_std
          tie_mode="keep_more",   # Tie handling ("keep_more" or "underdetermined")
          metric_weights={        # Custom metric weights
              "modularity": 0.6,
              "coverage": 0.4,
          },
      )
      .seed(42)
      .execute(network)
)
```

**BudgetSpec Structure**:
- `max_iter`: Maximum iterations (for iterative algorithms)
- `n_restarts`: Number of random restarts
- `resolution_trials`: Number of resolution parameter trials
- `time_limit_s`: Time limit in seconds (optional)
- `uq_samples`: Number of samples for UQ evaluation
- `n_jobs`: Parallelism (algorithms ignore unsupported parameters)

**Utility Methods**:
1. **mean_minus_std** (default): `U = mean(score) - lambda * std(score)`
   - Balances expected performance with risk
   - Higher lambda = more conservative (prefer consistent algorithms)
   
2. **expected_regret**: `U = -E[max(scores) - score]`
   - Minimizes expected loss relative to best algorithm
   
3. **prob_near_best**: `U = P(score >= max - eps)`
   - Probability of being close to best (eps = 0.01 default)

**Metric Aggregation**:
- Multiple metrics → single scalar via weighted sum
- Normalization: robust min-max per round (configurable)
- Default weights: equal across metrics
- Missing metrics: handled gracefully with warnings

**Provenance Metadata**:
```python
prov = result.provenance

# Always present
assert prov["engine"] == "autocommunity_successive_halving"
assert "py3plex_version" in prov
assert "timestamp_utc" in prov
assert "seed" in prov
assert "strategy" == "successive_halving"

# Racing-specific
history = prov["racing_history"]
assert "rounds" in history          # List of round records
assert "winner_algo_id" in history  # Winning algorithm
assert "finalists" in history       # List (multiple if underdetermined)
assert "status" in history          # "ok", "underdetermined", "error"
assert "total_runtime_ms" in history

# Each round record contains:
round0 = history["rounds"][0]
assert "round" in round0           # Round index
assert "budget" in round0          # BudgetSpec as dict
assert "algorithms" in round0      # Algorithms run this round
assert "metrics" in round0         # Metrics DataFrame
assert "utilities" in round0       # Utility per algorithm
assert "survivors" in round0       # Survivors to next round
assert "eliminated" in round0      # Eliminated this round
```

**Determinism Guarantees**:
```python
# Same seed → identical results (deterministic)
result1 = AutoCommunity().candidates(...).strategy("successive_halving").seed(42).execute(net)
result2 = AutoCommunity().candidates(...).strategy("successive_halving").seed(42).execute(net)
assert result1.selected == result2.selected
assert result1.provenance["racing_history"] == result2.provenance["racing_history"]

# Parallel invariance (not yet implemented for n_jobs>1)
# Future: n_jobs=1 and n_jobs=4 will produce identical results
```

**Underdetermined Handling**:
```python
# If top-2 utilities are too close (tie)
result = AutoCommunity().strategy("successive_halving", tie_mode="underdetermined").execute(net)

if result.provenance["racing_history"]["status"] == "underdetermined":
    finalists = result.provenance["racing_history"]["finalists"]
    print(f"No clear winner. Finalists: {finalists}")
    # result.selected is arbitrary choice from finalists
```

**When to use Successive Halving vs Default Pareto**:
- **Use SH when**:
  - Large number of candidate algorithms (>5)
  - Computational budget is limited
  - Want efficient early elimination
  - Clear metric preferences (weighted)
  
- **Use Pareto when**:
  - Small number of candidates (<5)
  - Multi-objective optimization without clear weights
  - Want consensus from non-dominated set
  - Null model calibration is critical

**Performance**:
- Conservative default budgets: fast exploration in early rounds
- Budget growth: 3x per round by default (configurable)
- Budget caps: prevent explosion (max_iter: 1000, uq_samples: 200, etc.)
- Early stopping: enabled by default (stop when 1 survivor)

**Best Practices**:
1. Start with small budget0 (max_iter=5, uq_samples=10)
2. Use eta=3 for aggressive elimination, eta=2 for conservative
3. Enable UQ with uq_samples in budget for stability-aware selection
4. Set seed for reproducibility
5. Inspect racing_history to understand selection rationale
6. Use metric_weights to encode domain knowledge
7. Check status for "underdetermined" to detect ties

**Advanced: Direct Racer Usage**:
```python
from py3plex.algorithms.community_detection.successive_halving import (
    SuccessiveHalvingRacer,
    SuccessiveHalvingConfig,
)
from py3plex.algorithms.community_detection.budget import BudgetSpec

# Configure racer directly
config = SuccessiveHalvingConfig(
    eta=3,
    rounds=3,
    budget0=BudgetSpec(max_iter=5, uq_samples=10),
    utility_method="mean_minus_std",
    normalize_metrics=True,
)

racer = SuccessiveHalvingRacer(config, seed=42)

# Run race
history = racer.race(
    network=network,
    algorithm_ids=["louvain", "leiden", "label_propagation"],
    metric_names=["modularity", "coverage"],
    n_jobs=1,
)

# Inspect results
print(f"Winner: {history.winner_algo_id}")
print(f"Status: {history.status}")
```

**Golden Path: AutoCommunity with Successive Halving**:
```python
# 1. Load network
net = multinet.multi_layer_network(directed=False)
net.load_network("network.csv", input_type="edgelist")

# 2. Run Successive Halving
result = (
    AutoCommunity()
      .candidates("louvain", "leiden", "label_propagation")
      .metrics("modularity", "coverage", "stability")
      .uq(method="seed", n_samples=20)  # Enable UQ
      .strategy("successive_halving", eta=3, rounds=2)
      .seed(42)
      .execute(net)
)

# 3. Access winner and history
print(f"Winner: {result.selected}")
print(f"Communities: {result.community_stats.n_communities}")

# 4. Export results
df = result.to_pandas()
df.to_csv("communities.csv", index=False)

# 5. Save provenance
import json
with open("provenance.json", "w") as f:
    json.dump(result.provenance, f, indent=2)
```

**Invariants**:
- Budget must be monotone-increasing across rounds
- Determinism: same seed → same winner → same elimination order
- Provenance completeness: all rounds, budgets, utilities tracked
- No API sprawl: clean integration with existing AutoCommunity

---

### Community Quality Metrics

### AutoCommunity Meta-Algorithm (v2.0) — **NEW Design**

**Purpose**: Multi-objective, uncertainty-aware, null-model-calibrated meta-algorithm for principled community detection in multilayer networks.

**Key Design Principles**:
1. **No single scalar objective** - Uses multi-objective evaluation with Pareto dominance
2. **Uncertainty is first-class** - Node-level confidence, entropy, and stability
3. **Null-model calibration mandatory** - Statistical significance via Z-scores
4. **Multilayer-native** - Preserves layer semantics in metrics and stability
5. **Reproducible and inspectable** - Full provenance and regime diagnostics

**Builder API**:
```python
from py3plex.algorithms.community_detection import AutoCommunity

# Full pipeline with all features
result = (
    AutoCommunity()
      .candidates("louvain", "leiden", "infomap")
      .metrics("modularity", "stability", "coverage", "entropy")
      .uq(method="perturbation", n_samples=50)
      .null_model(type="configuration", samples=50)
      .pareto()
      .seed(42)
      .execute(network)
)

# Access results
print(result.explain())                    # Selection rationale
print(result.pareto_front)                 # Non-dominated algorithms
print(result.consensus_partition)          # Final partition
print(result.community_stats.node_confidence)  # Node-level confidence
```

**Minimal Configuration**:
```python
# Simplest usage (uses defaults)
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity", "coverage")
      .seed(42)
      .execute(network)
)
```

**Result Object** (`AutoCommunityResult`):
- `result.algorithms_tested`: List of all algorithms evaluated
- `result.pareto_front`: Non-dominated algorithms (Pareto optimal)
- `result.selected`: ID of selected algorithm or "consensus"
- `result.consensus_partition`: Final partition (dict: (node, layer) -> community_id)
- `result.community_stats`: Structured statistics with uncertainty
  - `n_communities`: Number of communities
  - `community_sizes`: List of community sizes
  - `coverage`: Fraction of nodes in non-singleton communities
  - `orphan_nodes`: List of singleton community nodes
  - `node_confidence`: Per-node confidence scores (dict)
  - `node_entropy`: Per-node uncertainty scores (dict)
  - `stability_score`: Overall partition stability
- `result.evaluation_matrix`: DataFrame with all metrics for all algorithms
- `result.null_model_results`: Null model Z-scores (if enabled)
- `result.graph_regime`: Network regime features
- `result.provenance`: Full configuration and seed information

**Evaluation Axes** (Built-in Metrics):
| Metric | Description | Direction |
|--------|-------------|-----------|
| `modularity` | Layer-aware multilayer modularity | Maximize |
| `stability` | Node assignment stability under perturbation | Maximize |
| `coverage` | Fraction of nodes in non-singleton communities | Maximize |
| `entropy` | Node-level assignment uncertainty (mean) | Minimize |
| `mdl` | Minimum description length (if available) | Minimize |

**Pareto Selection Logic**:
- Algorithm A **dominates** B if: A ≥ B on all objectives AND A > B on at least one
- **Pareto front**: Set of all non-dominated algorithms
- If multiple non-dominated → **Consensus partition** computed via co-assignment
- If single non-dominated → That algorithm is selected

**Consensus Communities** (When Multiple Are Non-Dominated):
```python
# Consensus is automatically computed when len(pareto_front) > 1
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity", "stability", "coverage")
      .uq(method="perturbation", n_samples=30)
      .execute(network)
)

if result.selected == "consensus":
    print("Multiple algorithms were non-dominated!")
    print(f"Algorithms in consensus: {result.pareto_front}")

    # Identify core vs. peripheral nodes
    confidence = result.community_stats.node_confidence
    core_nodes = {node for node, conf in confidence.items() if conf > 0.8}
    print(f"Core nodes (high confidence): {len(core_nodes)}")

    # Check node-level entropy
    entropy = result.community_stats.node_entropy
    uncertain_nodes = {node for node, ent in entropy.items() if ent > 1.0}
    print(f"Uncertain nodes: {len(uncertain_nodes)}")
```

**Null Model Calibration**:
```python
# Compare to null models to ensure significance
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity", "coverage")
      .null_model(type="configuration", samples=50)
      .seed(42)
      .execute(network)
)

# Check Z-scores
if result.null_model_results:
    z_scores = result.null_model_results['z_scores']
    for algo_id, z_score in z_scores.items():
        print(f"{algo_id}: Z={z_score:.2f}")
        if z_score > 3.0:
            print("  → Highly significant (p < 0.001)")
        elif z_score > 2.0:
            print("  → Significant (p < 0.05)")
        else:
            print("  → Weak signal (may be filtered)")
```

**Graph Regime Diagnostics**:
```python
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity")
      .execute(network)
)

# Check what type of network this is
regime = result.graph_regime
print(f"Degree heterogeneity: {regime.get('degree_heterogeneity', 0):.3f}")
print(f"Layer density variance: {regime.get('layer_density_variance', 0):.3f}")
print(f"Inter-layer coupling: {regime.get('coupling_strength', 0):.3f}")

# High degree heterogeneity → Scale-free network
# High coupling strength → Strongly multiplex network
```

**Export and Serialization**:
```python
# Export to DataFrame
df = result.to_pandas()
# Columns: node, layer, community, confidence, entropy, margin

# Export to dictionary (JSON-serializable)
result_dict = result.to_dict()

# Save provenance
import json
with open("community_provenance.json", "w") as f:
    json.dump({
        'provenance': result.provenance,
        'graph_regime': result.graph_regime,
        'null_results': result.null_model_results,
    }, f, indent=2)
```

**DSL Integration** (Planned):
```python
from py3plex.dsl import Q

# Query communities with confidence filtering
result = (
    Q.communities()
     .auto()
     .confidence__gt(0.9)  # Only high-confidence assignments
     .execute(network)
)

# Combine with other DSL operations
result = (
    Q.nodes()
     .community_auto()
     .where(community_size__gt=10)  # Large communities only
     .compute("pagerank")
     .execute(network)
)
```

**Anti-Patterns to Avoid**:
-  Using single metric (e.g., only modularity) → Use multi-objective
-  Ignoring uncertainty → Always use `.uq()` for stability
-  No null calibration → Use `.null_model()` for significance
-  Treating all nodes equally → Check `node_confidence` for reliability
-  Ignoring orphan nodes → Examine `community_stats.orphan_nodes`

**When to Use AutoCommunity Meta-Algorithm**:
- Need principled selection across competing quality objectives
- Want statistical confidence in community assignments
- Need to distinguish real structure from noise (null models)
- Working with multilayer networks where layer semantics matter
- Require full provenance and reproducibility
- Need to identify core vs. peripheral community members

**Comparison: Old vs. New AutoCommunity**:
| Feature | Old (auto_select) | New (AutoCommunity) |
|---------|-------------------|---------------------|
| Objective | Single scalar (most wins) | Multi-objective (Pareto) |
| Uncertainty | Optional, metric-level | First-class, node-level |
| Null models | Not integrated | Mandatory calibration |
| Selection | Weighted sum | Pareto dominance |
| Consensus | Not available | Automatic when needed |
| Provenance | Partial | Complete with regime |
| Node confidence | No | Yes (with UQ) |
| Multilayer semantics | Partial | Full (layer-aware metrics) |

**Backward Compatibility**:
The original `auto_select_community()` function is still available for backward compatibility, but the new `AutoCommunity` class is recommended for all new code.

```python
# Old API (still works)
from py3plex.algorithms.community_detection import auto_select_community
result = auto_select_community(network, fast=True, seed=42)

# New API (recommended)
from py3plex.algorithms.community_detection import AutoCommunity
result = (
    AutoCommunity()
      .candidates("louvain", "leiden")
      .metrics("modularity", "stability")
      .seed(42)
      .execute(network)
)
```

**Notes**:
- Returns `AutoCommunityResult` instead of regular `QueryResult`
- Detected algorithms depend on what's installed in py3plex
- Deterministic with fixed `seed`
- Defaults are fast and safe (small grids, 10 candidates)
- UQ adds stability metrics but increases runtime

### Community Queries

### Detect Communities

```python
from py3plex.algorithms.community_detection import louvain, leiden, label_propagation

# Louvain
communities = louvain(net, resolution=1.0, seed=42)

# Leiden (higher quality)
communities = leiden(net, resolution=1.0, seed=42)

# Label propagation (fast)
communities = label_propagation(net, seed=42)
```

### Query Communities

```python
from py3plex.dsl import Q

# Detect first
communities = louvain(net, seed=42)

# Query large communities
result = (
    Q.communities()
     .where(size__gt=10)
     .compute("conductance", "modularity_contribution")
     .execute(net)
)

# Get members of large communities
result = (
    Q.communities()
     .where(size__gt=10)
     .members()  # Switch to node query
     .compute("degree", "betweenness")
     .execute(net)
)
```

---

## Pattern Matching (Cypher-like)

**PSEUDOCODE** - Feature is implemented but simplified here.

```python
from py3plex.dsl.patterns import PatternQueryBuilder

# Find triangles
pattern = (
    PatternQueryBuilder()
     .node("a", layer="social")
     .edge("a", "b")
     .edge("b", "c")
     .edge("c", "a")
     .return_nodes("a", "b", "c")
)

matches = pattern.execute(net)
for match in matches:
    print(f"Triangle: {match['a']} - {match['b']} - {match['c']}")
```

---

## Network Comparison and Diff

```python
from py3plex.dsl import C

comparison = (
    C.compare("baseline", "treatment")
     .using("multiplex_jaccard")
     .by_layer()
     .execute({"baseline": net1, "treatment": net2})
)

print(f"Jaccard similarity: {comparison.similarity}")
print(f"Layer-wise: {comparison.by_layer}")
```

---

## CLI Tool

py3plex provides a full-featured CLI for shell scripts and automation.

### Basic Commands

```bash
# Get help
py3plex --help

# Create random network
py3plex create --nodes 100 --layers 3 --p-intra 0.1 --p-inter 0.01 --output network.edgelist

# Compute statistics
py3plex stats network.edgelist --output stats.csv

# Query network
py3plex query network.edgelist --query "SELECT nodes WHERE degree > 5" --output filtered.csv

# Convert format
py3plex convert network.edgelist --output network.graphml --format graphml
```

### Advanced Features

```bash
# Community detection
py3plex communities network.edgelist --algorithm louvain --output communities.csv

# Centrality with uncertainty
py3plex centrality network.edgelist --metric pagerank --uq bootstrap --n-samples 100 --output centrality.csv
```

---

## Plugin System

Extend py3plex with custom operators.

### Register Custom Operator

```python
from py3plex.dsl import dsl_operator, DSLExecutionContext

@dsl_operator("my_metric", description="Custom metric", category="centrality")
def my_custom_metric(context: DSLExecutionContext, alpha: float = 0.5):
    """Compute custom metric with parameter alpha."""
    graph = context.graph
    layers = context.current_layers

    # Your computation here
    result = {}
    for node in graph.nodes():
        result[node] = compute_value(node, alpha)

    return result

# Use in DSL
result = Q.nodes().compute("my_metric", alpha=0.8).execute(net)
```

### Query Registered Operators

```python
from py3plex.dsl import list_operators, describe_operator

# List all operators
operators = list_operators()

# Get operator details
info = describe_operator("my_metric")
print(info["description"])
```

---

## Configuration and Profiling

### Configuration

```python
from py3plex import config

# Get configuration
print(config.get("default_directed"))

# Set configuration (if mutable)
# config.set("default_directed", False)  # Most configs are constants
```

### Profiling

```python
from py3plex.profiling import profile_performance, timed_section

@profile_performance
def my_analysis(network):
    result = Q.nodes().compute("betweenness").execute(network)
    return result

# Timed sections
with timed_section("community_detection"):
    communities = louvain(net)
```

---

## Exception Hierarchy

Always use domain-specific exceptions:

```python
from py3plex.exceptions import (
    Py3plexException,           # Base exception
    Py3plexIOError,             # I/O errors
    NetworkConstructionError,   # Network construction failures
    ParsingError,               # Input parsing failures
)

# DSL exceptions
from py3plex.dsl import (
    DslError,                   # Base DSL error
    DslSyntaxError,             # Syntax errors
    DslExecutionError,          # Execution errors
    UnknownAttributeError,      # Unknown attribute referenced
    UnknownMeasureError,        # Unknown measure
    UnknownLayerError,          # Unknown layer
    ParameterMissingError,      # Parameter binding error
    TypeMismatchError,          # Type mismatch
    GroupingError,              # Grouping configuration error
)
```

**Best Practice**:
```python
from py3plex.exceptions import Py3plexIOError

try:
    net.load_network("file.csv")
except Py3plexIOError as e:
    print(f"Failed to load network: {e}")
```

**Don't use generic exceptions for domain errors**:
-  `FileNotFoundError` →  `Py3plexIOError`
-  `ValueError` →  `NetworkConstructionError`

---

## Query Planner and Optimization

### Overview

The DSL v2 query planner is an internal optimization layer that sits between AST compilation and execution. It automatically:

1. **Reorders stages** to reduce execution cost (filter early, compute late)
2. **Pushes down computations** to compute only measures needed downstream
3. **Caches expensive results** keyed by stable identifiers + provenance
4. **Provides execution plans** via `explain_plan()` for debugging and optimization
5. **Ensures determinism** - same network + AST + params + seed → same plan and results

**Key Property**: The planner is **semantically transparent** - planned and unplanned execution produce identical results.

### Usage

#### Basic Usage (Automatic)

The planner runs automatically on all DSL v2 queries. No code changes needed:

```python
from py3plex.dsl import Q

# Planner runs automatically
result = Q.nodes().compute("degree", "betweenness").where(degree__gt=5).execute(net)
```

#### Viewing Execution Plans

Use `explain_plan=True` to see how the planner optimized your query:

```python
# Get plan in result metadata
result = (
    Q.nodes()
     .compute("degree", "betweenness")
     .where(degree__gt=5)
     .order_by("betweenness", desc=True)
     .limit(10)
     .execute(net, explain_plan=True)
)

# Inspect plan
plan = result.meta["plan"]
print(f"Plan hash: {plan['plan_hash']}")
print(f"Stages: {[s['name'] for s in plan['planned_stage_order']]}")
print(f"Rewrites: {plan['rewrite_summary']}")
print(f"Total cost: {plan['total_estimated_cost']}")
```

**Typical output**:
```
Plan hash: a3f8c2e1b9d4...
Stages: ['get_nodes', 'filter_layers', 'filter_where', 'compute', 'order_by', 'limit']
Rewrites: ['Moved layer filtering early', 'Moved WHERE filter before compute']
Total cost: 73
```

#### Configuring the Planner

Use `.planner()` to customize planner behavior:

```python
# Minimal compute policy: only compute measures actually used
result = (
    Q.nodes()
     .compute("degree", "betweenness", "closeness")  # 3 measures requested
     .where(degree__gt=5)                             # Only degree used in WHERE
     .planner(compute_policy="minimal")               # Only degree computed!
     .execute(net)
)

# Disable caching for one-off queries
result = (
    Q.nodes()
     .compute("betweenness")
     .planner(enable_cache=False)
     .execute(net)
)

# Or pass config to execute()
result = Q.nodes().compute("degree").execute(
    net, 
    planner={"compute_policy": "minimal", "enable_cache": True}
)
```

### Compute Policies

The planner supports three compute policies:

| Policy | Behavior | Use When |
|--------|----------|----------|
| `explicit` | Compute all user-requested measures + measures needed for semantics (ORDER BY, WHERE) | Default - balances performance and explicitness |
| `minimal` | Compute only measures actually used downstream (ignores unused user-requested computes) | Performance-critical queries where you over-specified computes |
| `all` | Compute everything requested regardless of usage | Debugging or when you want all measures exported |

**Example**:
```python
# User requests 3 measures but only uses degree
q = Q.nodes().compute("degree", "betweenness", "closeness").where(degree__gt=5)

# explicit (default): computes all 3
q.execute(net, planner={"compute_policy": "explicit"})

# minimal: computes only degree (used in WHERE)
q.execute(net, planner={"compute_policy": "minimal"})

# all: computes all 3 (same as explicit in this case)
q.execute(net, planner={"compute_policy": "all"})
```

### Caching

The planner caches expensive computations (primarily centrality measures) with deterministic keys:

**Cache Key = hash(network_fingerprint + AST_hash + params + seed + UQ_config)**

**Cache behavior**:
- **First execution**: Computes and stores in cache (MISS)
- **Second execution** (same network, query, params): Retrieves from cache (HIT)
- **Different params/seed**: New cache entry (MISS)

**Checking cache statistics**:
```python
from py3plex.dsl import get_cache_statistics, clear_cache

# Execute query twice
result1 = Q.nodes().compute("betweenness").execute(net)
result2 = Q.nodes().compute("betweenness").execute(net)

# Check stats
stats = get_cache_statistics()
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Clear cache if needed
clear_cache()
```

**Cache is automatically invalidated when**:
- Network structure changes (different node/edge/layer counts)
- Query AST changes
- Parameters change
- Random seed changes
- UQ configuration changes

### Optimization Rules

The planner applies these optimization rules **safely** (never changes semantics):

1. **Layer filtering early**: `.from_layers()` always executes immediately after GetItems
2. **WHERE before compute**: Filters on intrinsic fields (layer, type, id) move before compute
3. **WHERE after compute**: Filters on computed fields (degree, betweenness) stay after compute
4. **Compute delayed**: Computation delayed until after filters (reduce item set first)
5. **ORDER BY after compute**: Sorting happens after measures are computed
6. **LIMIT after sort**: Limit applied after ordering (or after filters if no ordering)

**Example reordering**:
```python
# Original query order
q = Q.nodes().compute("degree").from_layers(L["social"]).where(layer="social")

# Planner reorders to:
# 1. GetItems (get_nodes)
# 2. FilterLayers (from_layers) ← moved early
# 3. FilterWhere (layer="social") ← moved before compute (intrinsic field)
# 4. Compute (degree)

# Result: fewer nodes to compute degree for!
```

### Error Handling

The planner detects and reports dependency errors with **actionable hints**:

```python
# Error: WHERE references computed field without computing it
q = Q.nodes().where(betweenness_centrality__gt=0.1)  # No .compute()

# Raises DslExecutionError with hint:
# "Field 'betweenness_centrality' referenced in WHERE clause but not computed.
#  Add .compute('betweenness_centrality') before the WHERE clause."
```

```python
# Error: ORDER BY references uncomputed field
q = Q.nodes().order_by("pagerank")  # No .compute()

# Raises DslExecutionError with hint:
# "Field 'pagerank' required by order_by but not computed.
#  Add .compute('pagerank') before the operation that requires it."
```

### Provenance Integration

When the planner is used, it adds metadata to `result.meta["provenance"]`:

```python
result = Q.nodes().compute("degree").execute(net)

prov = result.meta["provenance"]
# prov["query"]["plan_hash"] - hash of planned stages
# prov["backend"]["cache"] - cache hit/miss statistics  
# prov["performance"]["plan_ms"] - time spent planning
```

**Full provenance structure**:
```json
{
  "query": {
    "target": "nodes",
    "ast_hash": "a3f8c2e1...",
    "plan_hash": "b7d4a9f2...",  // NEW
    "params": {}
  },
  "backend": {
    "graph_backend": "networkx",
    "cache": {  // NEW
      "hits": 2,
      "misses": 1
    }
  },
  "performance": {
    "total_ms": 145.3,
    "plan_ms": 0.8,  // NEW
    "temporal_context": 0.1
  }
}
```

### Determinism Guarantees

The planner is **fully deterministic**:

**Same input → Same plan → Same results**

Where "same input" means:
- Same network structure (node/edge/layer counts + topology)
- Same AST (query structure)
- Same bound parameters
- Same random seed (if randomness used)
- Same UQ configuration (if UQ enabled)

**Implications**:
- Plans are reproducible across runs
- Cache hits are deterministic
- Reordering is deterministic (no random tie-breaking)
- Plan hashes are stable

**Example**:
```python
# First execution
plan1 = plan_query(Q.nodes().compute("degree").to_ast(), net)

# Second execution (identical query + network)
plan2 = plan_query(Q.nodes().compute("degree").to_ast(), net)

# Plans are identical
assert plan1.plan_hash == plan2.plan_hash
assert [s.stage_type for s in plan1.planned_stages] == [s.stage_type for s in plan2.planned_stages]
```

### Advanced: Direct Planner API

For advanced use cases, access the planner directly:

```python
from py3plex.dsl import plan_query, QueryPlanner

# Plan a query
q = Q.nodes().compute("degree", "betweenness").where(degree__gt=5)
plan = plan_query(q.to_ast(), network)

# Inspect plan structure
print(f"Stages: {len(plan.planned_stages)}")
print(f"Required measures: {plan.required_measures}")
print(f"Rewrite summary: {plan.plan_meta['rewrite_summary']}")

# Custom planner with specific config
planner = QueryPlanner({"compute_policy": "minimal", "enable_cache": False})
plan = planner.plan(q.to_ast(), network, params={})
```

### Performance Impact

**Planning overhead**: < 1ms for typical queries (measured via `provenance.performance.plan_ms`)

**Expected speedups**:
- **Layer filtering early**: 2-10x fewer nodes to process downstream
- **WHERE before compute**: 2-5x faster (avoid computing on filtered nodes)
- **Compute pushdown**: 1.5-3x faster (avoid unused expensive measures)
- **Caching**: 10-100x faster on second run (for expensive centralities)

**Example**:
```python
# Without planner (manual optimization)
result = Q.nodes().from_layers(L["social"]).compute("betweenness").execute(net)
# Time: 5.2s

# With planner (automatic optimization)
result = Q.nodes().compute("betweenness").from_layers(L["social"]).execute(net)
# Time: 5.2s (planner reorders automatically)
# Plan: ['get_nodes', 'filter_layers' ← moved early, 'compute']
```

---

## Performance Guidelines

### Network Size Recommendations

| Network Size | Recommended Actions |
|--------------|---------------------|
| < 1,000 nodes | All operations fast, no special considerations |
| 1,000-10,000 nodes | Disable autocompute for repeated queries, use layer filtering |
| 10,000-100,000 nodes | Avoid betweenness/closeness, use sampling, enable progress logging |
| > 100,000 nodes | Use NetworkX backend optimizations, consider graph-tool for centrality |

### Metric Complexity

| Metric | Time Complexity | Space | Notes |
|--------|----------------|-------|-------|
| degree | O(m) | O(1) | Very fast |
| pagerank | O(m * k) | O(n) | k iterations, usually fast |
| betweenness | O(n * m) | O(n²) | Expensive for large graphs |
| closeness | O(n * m) | O(n²) | Expensive for large graphs |
| clustering | O(n * d²) | O(1) | d = avg degree |

**Optimization Tips**:
1. **Filter early**: Use `.where()` before `.compute()` to reduce node set
2. **Layer filtering**: Use `.from_layers()` to work on subnetworks
3. **Disable autocompute**: If metrics are pre-computed, set `autocompute=False`
4. **Batch computations**: Compute multiple metrics in one `.compute()` call
5. **UQ sampling**: Start with n_samples=10 for development
6. **Progress logging**: Use `progress=True` for long-running queries

---

## Reproducibility Policy

### Determinism Guarantees

py3plex guarantees deterministic results when:
1. **Seed is set**: All randomized operations accept `seed` parameter
2. **Same network**: Identical input network structure
3. **Same version**: py3plex version and dependencies unchanged
4. **Same parameters**: All parameters (including hyperparameters) identical

### Provenance

Every query execution records provenance for reproducibility and verification:

```python
result = Q.nodes().compute("pagerank").execute(net)

prov = result.meta['provenance']

# Key provenance fields
print(prov['engine'])             # "dsl_v2_executor"
print(prov['py3plex_version'])    # "1.1.2"
print(prov['timestamp_utc'])      # ISO8601 timestamp
print(prov['network_fingerprint']) # Node/edge counts, layers
print(prov['query']['ast_hash'])  # Stable hash of query AST
print(prov['randomness']['seed']) # Random seed if used
print(prov['performance']['total_ms']) # Execution time
```

**Correctness verification**:
- **AST hash stability**: Identical queries produce identical AST hashes ✅ (tested)
- **Reproducibility expectations**: Same AST hash + seed + network → same results ✅
- **Provenance presence**: All DSL v2 results include provenance metadata ✅ (verified in tests)

**Usage in verification**:
```python
# Verify AST stability
q1 = Q.nodes().compute("degree")
q2 = Q.nodes().compute("degree")
assert q1.to_ast() == q2.to_ast()  # ✅ Structurally identical

# Verify reproducibility via provenance
result1 = q1.execute(net)
result2 = q2.execute(net)
assert result1.meta['provenance']['query']['ast_hash'] == result2.meta['provenance']['query']['ast_hash']
```

### Reproducibility Checklist

- [ ] Set `seed` parameter for all randomized operations
- [ ] Document `py3plex.__version__` in code/paper
- [ ] Save provenance metadata: `result.meta['provenance']`
- [ ] Archive network data with checksums
- [ ] Document Python and dependency versions
- [ ] Use parameterized queries with Param.ref() for reusability

---

## Verification & Correctness Guarantees

### Overview

py3plex employs **metamorphic testing**, **differential testing**, and **certificate-based verification** to provide strong correctness guarantees without relying on brittle golden outputs. This approach verifies that algorithms satisfy key invariants and properties rather than comparing against pre-computed results.

**Philosophy**: Correctness is established through:
1. **Metamorphic relations**: Transformations that should preserve properties
2. **Certificates/witnesses**: Independent validation of algorithm outputs
3. **Cross-implementation agreement**: Comparing equivalent operations across APIs
4. **Determinism enforcement**: All stochastic algorithms are seedable and reproducible

**Current Coverage** (as of v1.1.2):
- ✅ Centrality measures: Metamorphic invariance tests
- ✅ Community detection: Certificate-based validation
- ✅ DSL v2: Provenance and metadata checks
- ⚠️ Null models: Partial coverage (degree sequence preservation)
- ⚠️ Path algorithms: Basic tests (not yet comprehensive)
- ⚠️ Dynamics simulations: Determinism tests (not yet metamorphic)

### Metamorphic Testing

Metamorphic testing verifies that algorithms satisfy invariants under controlled transformations. py3plex tests the following metamorphic relations:

#### Supported Transformations

All transformations are deterministic and preserve specific properties:

| Transformation | What it preserves | Test fixture |
|----------------|-------------------|--------------|
| **Node relabeling** | Topology, degree distribution, all centrality value multisets | `relabel_nodes(net, mapping)` |
| **Layer permutation** | Network structure, intralayer/interlayer patterns | `permute_layers(net, perm)` |
| **Edge order shuffle** | All edges, all graph properties (tests insertion order independence) | `shuffle_edge_order(net, seed=42)` |
| **Weight scaling** | Topology, relative weight ordering, shortest path routes | `scale_weights(net, factor=2.0)` |
| **Isolated node addition** | Connected component structure, existing edges | `add_isolated_nodes(net, nodes, layer=0)` |
| **Edge perturbation** | Stability envelope (used for testing robustness) | `perturb_edges(net, drop_prob=0.1, seed=42)` |

#### Verified Invariants

**Centrality measures** (17 tests):
- **Relabel invariance**: Node naming doesn't affect centrality distributions
  - Degree centrality ✅
  - Betweenness centrality ✅
  - PageRank ✅
  - Closeness centrality ✅
- **Layer permutation invariance**: Layer ordering doesn't affect results ✅
- **Edge order invariance**: Edge insertion order doesn't matter ✅
- **Finiteness**: All values are finite (no NaN/inf) ✅
- **PageRank normalization**: Values sum to ≈1.0 within 1e-6 tolerance ✅

**Community detection** (7 certificate tests):
- **Partition validity**: Every node assigned exactly once ✅
- **No empty communities**: All communities have at least one member ✅
- **Modularity certificate**: Recomputed modularity matches and is within bounds [-0.5, 1.0] ✅
- **Determinism**: Same seed produces identical partitions ✅
- **Expected structure**: Known structures (e.g., two cliques with bridge) produce reasonable community counts ✅
- **Relabel equivalence**: Relabeling produces same partition structure (same modularity) ✅

**DSL v2**:
- **Provenance presence**: All results include provenance metadata ✅
- **AST stability**: Identical queries produce identical AST representations ✅

### Certificate-Based Verification

Certificates are independent witnesses that validate algorithm outputs without trusting the algorithm itself.

#### Community Detection Certificates

```python
from py3plex.algorithms.community_detection import louvain_multilayer, multilayer_modularity

# Run algorithm
partition = louvain_multilayer(net, random_state=42)

# Certificate 1: Partition covers all nodes
nodes = set(net.get_nodes())
assert set(partition.keys()) == nodes

# Certificate 2: No empty communities
community_sizes = {}
for node, comm in partition.items():
    community_sizes[comm] = community_sizes.get(comm, 0) + 1
assert all(size > 0 for size in community_sizes.values())

# Certificate 3: Recompute modularity
Q = multilayer_modularity(net, partition)
assert -0.5 <= Q <= 1.0  # Theoretical bounds
assert math.isfinite(Q)   # Must be finite
```

#### PageRank Certificates

```python
# Run PageRank
centrality = net.monoplex_nx_wrapper("pagerank")

# Certificate 1: Non-negativity
assert all(v >= 0 for v in centrality.values())

# Certificate 2: Normalization
total = sum(centrality.values())
assert abs(total - 1.0) < 1e-6

# Certificate 3: Finiteness
assert all(math.isfinite(v) for v in centrality.values())
```

#### Null Model Certificates

Null models must preserve specified constraints. Verification checks that constraints are actually preserved:

```python
from py3plex.nullmodels import configuration_model

# Generate null model
null_net = configuration_model(net, seed=42)

# Certificate 1: Degree sequence preserved (per layer)
for layer in net.get_layers():
    original_degrees = sorted([net.degree(n, layer) for n in net.get_nodes(layer)])
    null_degrees = sorted([null_net.degree(n, layer) for n in null_net.get_nodes(layer)])
    assert original_degrees == null_degrees

# Certificate 2: Layer count preserved
assert len(net.get_layers()) == len(null_net.get_layers())

# Certificate 3: Node count preserved (per layer)
for layer in net.get_layers():
    assert len(net.get_nodes(layer)) == len(null_net.get_nodes(layer))
```

### Differential Testing

Differential testing compares equivalent operations across different implementations to detect semantic drift.

#### DSL v2 vs Legacy DSL

**Note**: Legacy DSL has limited functionality, so many comparisons are not feasible. Current tests:

```python
from py3plex.dsl import Q, execute_query

# Node selection (both DSLs)
legacy_result = execute_query(net, "SELECT nodes")
v2_result = Q.nodes().execute(net)
# Should select same nodes ✅ (tested where feasible)

# Computed measures (when supported)
legacy_result = execute_query(net, "SELECT nodes COMPUTE degree")
v2_result = Q.nodes().compute("degree").execute(net)
# Should produce same degree values ✅
```

**Skipped tests**: 9 differential tests are skipped because legacy DSL doesn't support:
- Layer filtering with `FROM` clause (inconsistent syntax)
- Degree filtering with `WHERE degree > N`
- Betweenness/PageRank computation
- Edge selection with `intralayer=True`
- Ordering with `ORDER BY`

**DSL v2 advantages verified**:
- ✅ Richer provenance metadata
- ✅ Stable AST representation
- ✅ Type safety and IDE autocomplete
- ✅ Chainable builder API

#### py3plex vs NetworkX (planned)

For single-layer projections, centrality measures should agree with NetworkX:
- Degree centrality (not yet implemented)
- Betweenness centrality (not yet implemented)
- Closeness centrality (not yet implemented)
- PageRank (not yet implemented)

**Status**: Not yet implemented. Future work will add differential tests comparing py3plex monoplex projections with NetworkX on identical graphs.

### Determinism and Reproducibility

**Guarantee**: All stochastic algorithms are fully deterministic when seeded.

```python
# Community detection with seed
partition1 = louvain_multilayer(net, random_state=42)
partition2 = louvain_multilayer(net, random_state=42)
assert partition1 == partition2  # ✅ Identical

# Uncertainty quantification with seed
result1 = Q.nodes().compute("betweenness").uq(method="bootstrap", n_samples=100, seed=42).execute(net)
result2 = Q.nodes().compute("betweenness").uq(method="bootstrap", n_samples=100, seed=42).execute(net)
# Confidence intervals should be identical ✅

# Null model generation with seed
null1 = configuration_model(net, seed=123)
null2 = configuration_model(net, seed=123)
# Should produce identical null networks ✅
```

**Verification**: Tests check that `seed=N` produces identical results across multiple runs.

### Test Fixtures

All verification tests use **canonical small graphs** for deterministic, fast testing:

```python
from tests.fixtures import (
    tiny_two_layer,          # 4 nodes, 2 layers, 4 edges
    small_three_layer,       # 5 nodes, 3 layers, 5 edges
    two_cliques_bridge,      # 6 nodes, 1 layer, K3-bridge-K3 (known community structure)
    path_graph_multilayer,   # Parameterized path graphs replicated across layers
)

# All fixtures return multi_layer_network instances
net = tiny_two_layer()
```

**Properties**:
- Small enough for fast testing (< 10 nodes typically)
- Diverse enough to cover edge cases
- Well-documented with known structural properties
- Deterministic (no randomness in construction)

### Current Limitations

**What is NOT yet covered**:
- ❌ Path algorithms: Only basic tests, no comprehensive metamorphic tests
- ❌ Null models: Certificate tests not yet comprehensive
- ❌ Dynamics simulations: Determinism tested, but not metamorphic properties
- ❌ Temporal network algorithms: No verification tests yet
- ❌ Graph operations (graph_ops): No differential tests vs DSL v2
- ❌ CLI vs Python API: No differential tests
- ❌ py3plex vs NetworkX: No cross-implementation comparison tests

**What is partially covered**:
- ⚠️ DSL v2 vs Legacy DSL: 9 tests skipped due to legacy DSL limitations
- ⚠️ Community detection: Strong certificate tests, but stability envelope tests not yet comprehensive

**Roadmap**:
1. Add path algorithm metamorphic tests (weight scaling preserves argmin path)
2. Add comprehensive null model certificate tests
3. Add py3plex vs NetworkX differential tests for single-layer operations
4. Add CLI vs Python API smoke tests
5. Add temporal algorithm verification tests
6. Expand community detection stability envelope tests

### Best Practices

**For developers**:
1. **Add metamorphic tests** for new algorithms (test invariants, not golden outputs)
2. **Add certificate validators** for algorithm outputs (independent verification)
3. **Use canonical fixtures** (`tests/fixtures/`) for deterministic testing
4. **Enforce determinism** with `seed` parameters and test reproducibility
5. **Update this section** when adding new verification tests (keep it factual)

**For users**:
1. **Trust the verified invariants**: If an algorithm passes metamorphic tests, its invariants hold
2. **Check certificates**: Recompute modularity, check PageRank normalization, etc.
3. **Use seeds**: Always set `seed` for reproducible research
4. **Report violations**: If you find an invariant violation, file an issue with a minimal repro

---

## Common Pitfalls and Solutions

### 1. NetworkX MultiGraph Limitations

**Problem**: `clustering()` doesn't support MultiGraph

**Solution**: Convert to simple graph first

```python
import networkx as nx

# Wrong
# clustering = nx.clustering(net.core_network)

# Correct
simple_graph = nx.Graph(net.core_network)
clustering = nx.clustering(simple_graph)
```

---

### 2. Forward References in Type Hints

**Problem**: Type hints for classes defined later cause NameError

**Solution**: Use string type hints

```python
# Correct
def method(self) -> "ClassName":
    return ClassName()
```

---

### 3. Forgetting .execute()

**Problem**: Query builder returned instead of results

**Solution**: Always end with `.execute(network)`

```python
# Wrong - returns QueryBuilder
result = Q.nodes().where(degree__gt=5)

# Correct - returns QueryResult
result = Q.nodes().where(degree__gt=5).execute(network)
```

---

### 4. Empty Layer Expressions

**Problem**: Layer algebra that matches no layers → empty result

**Solution**: Check layer names or use `L["*"]` to see all layers

```python
# Check available layers first
print(net.get_layers())

# Or use wildcard
Q.nodes().from_layers(L["*"]).execute(net)
```

---

### 5. Temporal Edge Attributes

**Problem**: Mixing `t` with `t_start`/`t_end`

**Solution**: Stick to one convention (prefer interval form)

```python
# Consistent - interval form
tnet.add_edge('A', 'B', layer='social', t_start=100.0, t_end=200.0)
tnet.add_edge('C', 'D', layer='social', t_start=120.0, t_end=180.0)

# Also valid - point-in-time (but don't mix)
tnet.add_edge('A', 'B', layer='social', t=150.0)
```

---

### 6. Coverage Without Grouping

**Problem**: `.coverage()` called without `.per_layer()`

**Solution**: Always group before coverage

```python
# Wrong
# Q.nodes().top_k(5).coverage(mode="all").execute(net)

# Correct
Q.nodes().per_layer().top_k(5).end_grouping().coverage(mode="all").execute(net)
```

---

### 7. Aggregate vs Compute Confusion

**Problem**: Using `.aggregate()` when `.compute()` is needed

**Solution**: Remember the distinction

```python
# Compute - per item (node/edge)
Q.nodes().compute("degree").execute(net)  # Each node gets a degree value

# Aggregate - per group
Q.nodes().per_layer().aggregate(avg_degree="mean(degree)").execute(net)  # One value per layer
```

---

### 8. UQ Seed Omission

**Problem**: Non-reproducible uncertainty results

**Solution**: Always set seed

```python
# Wrong - non-reproducible
Q.nodes().compute("pagerank").uq(method="bootstrap", n_samples=100).execute(net)

# Correct - reproducible
Q.nodes().compute("pagerank").uq(method="bootstrap", n_samples=100, seed=42).execute(net)
```

---

## Testing Strategy

### Test Organization

- **Unit Tests**: Fast tests in `tests/test_*.py`
- **Property Tests**: Hypothesis-based, marked `@pytest.mark.property`
- **Integration Tests**: Multi-component, marked `@pytest.mark.integration`
- **Slow Tests**: Marked `@pytest.mark.slow` - skip during development

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_dsl_v2.py

# With coverage
pytest tests/ --cov=py3plex

# Skip slow tests
pytest tests/ -m "not slow"

# Only property tests
pytest tests/ -m property

# Targeted test
pytest tests/test_dsl_v2.py::test_query_builder_basic
```

### Test Markers

- `@pytest.mark.property` - Property-based (Hypothesis)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.unit` - Fast unit tests

---

## File Locations

### Core Modules

- `py3plex/core/multinet.py` - Main multi_layer_network class
- `py3plex/core/temporal_multinet.py` - Temporal networks
- `py3plex/dsl/` - DSL v2 (builder API, AST, executor)
- `py3plex/dsl_legacy.py` - Legacy string-based DSL
- `py3plex/graph_ops.py` - Dplyr-style chainable API
- `py3plex/pipeline.py` - Sklearn-style pipeline
- `py3plex/workflows.py` - Config-driven workflows
- `py3plex_mcp/` - MCP server for AI agent integration

### MCP Server

- `py3plex_mcp/server.py` - FastMCP server implementation
- `py3plex_mcp/registry.py` - In-memory network handle storage
- `py3plex_mcp/schemas.py` - Response schema utilities
- `py3plex_mcp/errors.py` - Typed error handling
- `py3plex_mcp/safe_paths.py` - Path validation and safety

### DSL v2 Internals

- `py3plex/dsl/__init__.py` - Public API exports
- `py3plex/dsl/builder.py` - Q, L, UQ, Param builders (4600+ lines)
- `py3plex/dsl/ast.py` - AST node definitions
- `py3plex/dsl/executor.py` - Query execution engine
- `py3plex/dsl/result.py` - QueryResult class
- `py3plex/dsl/layers.py` - Layer algebra (LayerSet)
- `py3plex/dsl/expressions.py` - F field expressions
- `py3plex/dsl/errors.py` - DSL-specific exceptions

### Advanced Features

- `py3plex/dynamics/` - Dynamics simulations
- `py3plex/uncertainty/` - Uncertainty quantification
- `py3plex/temporal_utils.py` - Temporal utilities
- `py3plex/nullmodels/` - Null model implementations
- `py3plex/counterexamples/` - Counterexample engine
- `py3plex/claims/` - Claim learning
- `py3plex/algebra/` - Semiring algebra

### Algorithms

- `py3plex/algorithms/centrality/` - Centrality measures
- `py3plex/algorithms/community_detection/` - Community detection
- `py3plex/algorithms/temporal/` - Temporal algorithms

### I/O and Data

- `py3plex/io/` - I/O handlers
- `py3plex/datasets/` - Built-in datasets

### Utilities

- `py3plex/cli.py` - CLI entry point
- `py3plex/config.py` - Configuration constants
- `py3plex/exceptions.py` - Exception hierarchy
- `py3plex/validation.py` - Input validation
- `py3plex/profiling.py` - Performance profiling

### Documentation

- `AGENTS.md` - AI agent documentation (this file)
- `README.md` - Quick start
- `docfiles/` - Documentation source
- `examples/` - 170+ example scripts

### Tests

- `tests/test_dsl_v2.py` - DSL v2 tests
- `tests/test_dsl_extensions.py` - DSL extensions
- `tests/test_graph_ops.py` - Dplyr-style tests
- `tests/test_pipeline.py` - Pipeline tests
- `tests/test_dynamics.py` - Dynamics tests
- `tests/test_uncertainty.py` - UQ tests
- `tests/test_temporal.py` - Temporal tests
- `tests/test_counterexamples.py` - Counterexample tests
- `tests/test_claim_learning.py` - Claim learning tests

---

## API-Specific Patterns (CRITICAL)

### Multi_layer_network API

**Node and Edge Addition**:
- Use `add_nodes([...])` and `add_edges([...])` (**plural**)
- Singular forms don't exist
- Edge dict: `{'source': ..., 'target': ..., 'source_type': ..., 'target_type': ...}`
- Node dict: `{'source': ..., 'type': ...}`

```python
# Correct
net.add_edges([{'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}])

# Wrong - singular form doesn't exist
# net.add_edge('A', 'B', 'layer1', 'layer1')
```

### DSL Architecture

- **DSL v2**: Modern builder API (preferred) - use Q, L, UQ
- **Legacy DSL**: String-based (backward compat) - use execute_query()
- Canonical layer selection: `FROM layer="name"` or `.from_layers(L["name"])`
- Backward compat: `WHERE layer="name"`

### Error Handling

Always use domain-specific exceptions:

```python
from py3plex.exceptions import Py3plexIOError, Py3plexException

# For I/O
raise Py3plexIOError(f"Failed to read: {path}")

# For general errors
raise Py3plexException("Invalid configuration")
```

---

## Version Information

```python
import py3plex

print(py3plex.__version__)  # "1.1.2"
```

**Version History**:
- **1.1.2** (Current): Removed redundant documentation files
- **1.1.1**: Documentation updates and AutoCommunity examples
- **1.1.0**: DSL v2, Dynamics, UQ, Temporal, Null models, Counterexamples, Claim learning
- **1.0.0**: Initial stable release
- **0.96**: Pre-release

---

## References

- **README.md**: Quick start and flagship example
- **AGENTS.md**: Comprehensive AI agent documentation (this file)
- **docfiles/**: Detailed documentation
- **examples/**: 170+ working examples
- **pyproject.toml**: Dependencies and build config
- **Technical Book**: `docs/py3plex_book.pdf` (106 pages)

---

## Contributing Guidelines

When adding features:

1. **Type Hints**: Add for all public functions
2. **Docstrings**: Use Google-style
3. **Tests**: Add to `tests/` directory
4. **Documentation**: Update AGENTS.md
5. **Backward Compatibility**: Never break without deprecation
6. **Domain Exceptions**: Use exceptions from `py3plex.exceptions`
7. **Dependencies**: Check with gh-advisory-database before adding

**Code Style**:
```bash
black py3plex/
ruff check py3plex/
mypy py3plex/  # Requires Python 3.9+
```

---

## Summary: DSL v2 Mental Model

**1. Builder Lifecycle**
```
Q.nodes() → configure (.where, .compute, etc.) → .execute(net) → QueryResult
  lazy         lazy                                 eager          rich object
```

**2. Grouping Pattern**
```
.per_layer() → .top_k(k) → .end_grouping() → .coverage(mode) → .execute()
  group         per-group     marker           cross-group        run
```

**3. Compute vs Aggregate**
```
.compute("degree")  # Per-item metric (each node/edge)
.aggregate(avg_degree="mean(degree)")  # Per-group statistic
```

**4. Layer Algebra**
```
L["a"] + L["b"]  # Union
L["a"] - L["b"]  # Difference
L["a"] & L["b"]  # Intersection
L["*"]           # All layers
```

**5. Uncertainty**
```
.uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
→ Adds _mean, _std, _ci95_low, _ci95_high columns
```

**6. Error Handling**
```
UnknownLayerError      # Bad layer name
UnknownAttributeError  # Bad attribute name
GroupingError          # Grouping misconfiguration
ParameterMissingError  # Param binding failed
```

**7. Performance**
- Filter early with `.where()`
- Use `.from_layers()` to reduce network size
- Disable autocompute if metrics pre-computed
- Start UQ with small n_samples (10-20) for development

**8. Reproducibility**
- Always set `seed` for randomized operations
- Save `result.meta['provenance']`
- Document py3plex version

---

## MCP Integration (Model Context Protocol)

py3plex provides a production-ready MCP server that exposes py3plex functionality as tools and resources for AI coding assistants like Claude, Gemini, and Codex.

**Key Features**:
- **DSL v2 Support**: Modern builder API with type hints and IDE autocomplete
- **Backward Compatible**: Legacy string-based DSL still supported
- **7 Tools**: Load networks, run queries, detect communities, export results, and more
- **3 Resources**: Complete documentation, DSL reference, and tool schemas
- **Security-First**: Safe file access, automatic output directory, structured errors

**Requirements**: Python 3.10 or higher (due to MCP SDK dependency)

**Note**: The base py3plex package supports Python 3.8+. Only the optional MCP feature requires Python 3.10+.

### Installation

```bash
# Install with MCP support (requires Python 3.10+)
pip install py3plex[mcp]

# Or using uv
uv pip install py3plex[mcp]
```

### Starting the Server

```bash
# Start MCP server (stdio transport)
py3plex-mcp
```

The server runs in stdio mode, communicating via standard input/output following the MCP protocol.

### Available Tools

The MCP server exposes 7 tools:

#### 1. py3plex.load_network

Load a network from file and store in registry.

**Parameters**:
- `path` (str, required): File or directory path
- `input_type` (str, default: "multiedgelist"): Input format
- `directed` (bool, default: False): Whether network is directed
- `layer_separator` (str, optional): Layer separator character

**Returns**:
- `net_id`: Network handle (8-character UUID)
- `source`: Source path
- `stats`: Node count, edge count, layer count, layers preview

**Example**:
```json
{
  "path": "/data/network.csv",
  "input_type": "multiedgelist",
  "directed": false
}
```

#### 2. py3plex.stats

Get network statistics.

**Parameters**:
- `net_id` (str, required): Network handle

**Returns**:
- Network statistics (nodes, edges, layers)

#### 3. py3plex.run_query

Execute DSL query on network. **Supports both legacy (string-based) and DSL v2 (builder-based) queries.**

**Parameters**:
- `net_id` (str, required): Network handle
- `query` (str, required): DSL query string
  - Legacy DSL: SQL-like syntax (e.g., `"SELECT nodes WHERE degree > 5 COMPUTE pagerank"`)
  - DSL v2: Python builder expression (e.g., `"Q.nodes().where(degree__gt=5).compute('pagerank').limit(20)"`)
- `limit` (int, default: 200): Maximum items to return
- `use_v2` (bool, default: False): Use DSL v2 builder API (evaluates Python expression)

**Returns**:
- Query results with truncation info
- `dsl_version`: "legacy" or "v2" indicating which DSL was used

**Example (Legacy DSL)**:
```json
{
  "net_id": "abc12345",
  "query": "SELECT nodes WHERE degree > 5 COMPUTE pagerank",
  "limit": 200,
  "use_v2": false
}
```

**Example (DSL v2 - Recommended)**:
```json
{
  "net_id": "abc12345",
  "query": "Q.nodes().where(degree__gt=5).compute('pagerank').order_by('pagerank', desc=True).limit(20)",
  "limit": 200,
  "use_v2": true
}
```

**DSL v2 Features**:
- **Chainable builder API**: `Q.nodes().where(...).compute(...).limit(...)`
- **Django-style lookups**: `degree__gt`, `degree__between`, `layer__in`
- **Layer algebra**: `L["social"] + L["work"]` (union), `L["social"] - L["work"]` (difference)
- **Grouping**: `.per_layer()` or `.per_layer_pair()`
- **Type hints and IDE support**

**DSL v2 Common Patterns**:
```python
# Filter by layer and degree
"Q.nodes().where(layer='social', degree__gt=5).compute('pagerank')"

# Multiple layers with union
"Q.nodes().from_layers(L['social'] + L['work']).compute('degree')"

# Range filtering
"Q.nodes().where(degree__between=(5, 15)).compute('betweenness_centrality')"

# Edge queries
"Q.edges().where(interlayer=True).limit(100)"

# Grouped by layer
"Q.nodes().per_layer().compute('degree')"
```

#### 4. py3plex.community_detect

Detect communities in network.

**Parameters**:
- `net_id` (str, required): Network handle
- `algorithm` (str, default: "louvain"): Algorithm (louvain, leiden, label_propagation)
- `layer_mode` (str, default: "aggregate"): Layer handling mode
- `params` (dict, optional): Algorithm parameters (e.g., `{"seed": 42}`)

**Returns**:
- Community assignments and quality metrics

#### 5. py3plex.export

Export data to file.

**Parameters**:
- `data` (dict, required): Data to export
- `out_dir` (str, optional): Output directory (default: `~/.py3plex_mcp/out`)
- `format` (str, default: "json"): Output format (json or csv)
- `filename` (str, optional): Filename (auto-generated if not provided)

**Returns**:
- Written file paths

#### 6. py3plex.close

Close network handle and free memory.

**Parameters**:
- `net_id` (str, required): Network handle

#### 7. py3plex.list_handles

List all network handles.

**Returns**:
- List of network handles with metadata

### Available Resources

The MCP server exposes 3 resources:

#### py3plex://agents

Returns the complete AGENTS.md documentation.

#### py3plex://help/dsl

Returns DSL reference guide with syntax and examples.

#### py3plex://help/tools

Returns tool list with schemas and usage examples.

### Client Configuration

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "py3plex": {
      "command": "py3plex-mcp"
    }
  }
}
```

**Location**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

#### Gemini CLI

```bash
# Using stdio transport
gemini --mcp py3plex-mcp
```

#### Codex CLI

```bash
# Configure MCP server
codex config add-server py3plex py3plex-mcp
```

### Security Model

The MCP server implements security-first defaults:

**File Access**:
- **Read**: Only explicitly provided paths allowed
- **No globbing**: Patterns like `*.csv` are rejected
- **Forbidden paths**: System locations (`/etc`, `/sys`, `/proc`, etc.) are blocked
- **Write**: Only to safe output directory (default: `~/.py3plex_mcp/out`)

**Output Directory**:
- Default: `~/.py3plex_mcp/out`
- Created automatically if it doesn't exist
- Files are never overwritten (auto-suffix added)

**Network Registry**:
- In-memory only (no persistent state)
- Networks are isolated by unique handles
- Memory is freed on close or server shutdown

### Example Workflows

#### Load → Analyze → Export

```python
# 1. Load network
response = py3plex.load_network(
    path="/data/social_network.csv",
    input_type="multiedgelist"
)
net_id = response["net_id"]

# 2. Get statistics
stats = py3plex.stats(net_id=net_id)

# 3. Run query
result = py3plex.run_query(
    net_id=net_id,
    query="SELECT nodes WHERE degree > 10 COMPUTE pagerank",
    limit=100
)

# 4. Export results
py3plex.export(
    data=result,
    format="csv",
    filename="high_degree_nodes.csv"
)

# 5. Clean up
py3plex.close(net_id=net_id)
```

#### Community Detection

```python
# 1. Load network
response = py3plex.load_network(path="/data/network.csv")
net_id = response["net_id"]

# 2. Detect communities
communities = py3plex.community_detect(
    net_id=net_id,
    algorithm="louvain",
    params={"seed": 42}
)

# 3. Export communities
py3plex.export(
    data=communities,
    format="json",
    filename="communities.json"
)
```

### Error Handling

All tools return structured error responses:

```json
{
  "ok": false,
  "error": {
    "type": "NetworkNotFoundError",
    "message": "Network 'xyz' not found",
    "hint": "Use py3plex.list_handles to see available networks"
  },
  "meta": {
    "tool": "py3plex.stats",
    "timestamp": 1673456789.123
  }
}
```

**Common Error Types**:
- `NetworkNotFoundError`: Network handle not found
- `UnsupportedFormatError`: Unknown input format
- `QueryParseError`: DSL query parsing failed
- `UnsupportedAlgorithmError`: Unknown algorithm
- `PathAccessError`: Path access denied

### Response Format

All successful tool responses include:

```json
{
  "meta": {
    "ok": true,
    "tool": "tool_name",
    "version": {
      "py3plex": "1.1.2",
      "mcp_server": "1.0.0"
    },
    "timestamp": 1673456789.123,
    "truncated": false
  },
  // ... tool-specific data
}
```

### Truncation

Query results are automatically truncated to prevent overwhelming responses:

- Default limit: 200 items
- Configurable via `limit` parameter
- Metadata includes `truncated`, `total_count`, and `limit` when applicable

### Testing

```bash
# Run MCP server tests
pytest tests/test_mcp_server.py -v

# Test installation
pip install -e ".[mcp]"
py3plex-mcp --help
```

### Troubleshooting

**"Python 3.10 or higher required"**:
The MCP SDK requires Python 3.10+. Either:
- Upgrade to Python 3.10 or higher, OR
- Use the base py3plex package without MCP (supports Python 3.8+)

**"MCP SDK not installed"**:
```bash
pip install py3plex[mcp]
```

**"Network not found"**:
Use `py3plex.list_handles` to see active networks.

**"Path access denied"**:
Ensure the path exists and is not in a forbidden system location.

**Server not responding**:
Check that the server is running and stdio transport is properly configured.

---

**End of py3plex AI Agent Documentation**

**Last Updated**: 2026-01-15 (for py3plex v1.1.2 + MCP v1.0.0)


---

## SBM (Stochastic Block Model) — Model-Based Community Detection

### Overview

**Stochastic Block Model (SBM)** is a generative, model-based approach to community detection, integrated with AutoCommunity, Successive Halving, and UQ frameworks.

**Key Features:**
- Automatic model selection (number of communities K)
- Degree-corrected variant (DC-SBM) as default
- Principled statistical inference
- Compatible with BudgetSpec and Successive Halving
- Full UQ support

### Algorithm Variants

**Standard SBM:**
```
P(A_ij = 1 | z_i, z_j) = θ_{z_i z_j}
```

**DC-SBM (Degree-Corrected, recommended):**
```
P(A_ij = 1 | z_i, z_j) = θ_i θ_j ω_{z_i z_j}
```

DC-SBM accounts for degree heterogeneity, making it more realistic for real-world networks.

### When to Use SBM

**Use SBM when:**
- You need automatic model selection (K selection via MDL/BIC)
- Network has heterogeneous degree distribution
- You want principled statistical inference
- UQ is critical

**Use Louvain/Leiden when:**
- Network is very large (>10K nodes)
- Speed is critical
- You already know the number of communities

**Rule of thumb:** SBM is a "model-based" method vs. Louvain/Leiden's "objective-based" approach. SBM has higher computational cost but provides automatic K selection and better statistical foundations.

### Basic Usage (with AutoCommunity)

```python
from py3plex.algorithms.community_detection import AutoCommunity
from py3plex.core import multinet

net = multinet.multi_layer_network(directed=False)
net.load_network("network.csv", input_type="edgelist")

# Include SBM as candidate
result = (
    AutoCommunity()
      .candidates("louvain", "dc_sbm")
      .metrics("modularity", "sbm_log_likelihood")
      .seed(42)
      .execute(net)
)

print(f"Selected: {result.selected}")
print(f"Communities: {result.community_stats.n_communities}")
```

### Direct Runner Usage

```python
from py3plex.algorithms.community_detection.runner import run_community_algorithm
from py3plex.algorithms.community_detection.budget import BudgetSpec

# Define budget
budget = BudgetSpec(
    max_iter=100,      # EM iterations
    n_restarts=5,      # Random initializations
    uq_samples=None    # No UQ (single run)
)

# Run DC-SBM
result = run_community_algorithm(
    algorithm_id="dc_sbm",
    network=net,
    budget=budget,
    seed=42,
    K_range=[2, 3, 4, 5, 6, 7, 8]  # Model selection range
)

# Access results
partition = result.partition
K_selected = result.meta["K_selected"]
log_likelihood = result.meta["log_likelihood"]
mdl = result.meta["mdl"]  # Lower is better
```

### Budget Mapping

SBM respects BudgetSpec parameters:

| BudgetSpec Parameter | SBM Interpretation |
|----------------------|-------------------|
| `max_iter` | EM iterations (default: 500) |
| `n_restarts` | Random initializations (default: 5) |
| `uq_samples` | Bootstrap samples (default: None) |
| `time_limit_s` | Not yet implemented |
| `K_range` (kwarg) | Model selection range (default: [2..8]) |

**Example:**
```python
budget = BudgetSpec(max_iter=50, n_restarts=2, uq_samples=20)
# → SBM runs 50 EM iterations, 2 restarts, 20 bootstrap samples for UQ
```

### Model Selection

SBM automatically selects K using **Minimum Description Length (MDL)**:

```python
result = run_community_algorithm(
    algorithm_id="dc_sbm",
    network=net,
    budget=BudgetSpec(max_iter=100, n_restarts=3),
    seed=42,
    K_range=[2, 3, 4, 5, 6, 7, 8]
)

print(f"Selected K: {result.meta['K_selected']}")
print(f"MDL: {result.meta['mdl']:.2f}")  # Lower = better
```

**Criteria available:**
- **ELBO** (Evidence Lower Bound) — Maximize
- **MDL/BIC** (Minimum Description Length) — Minimize (default)
- **ICL** (Integrated Classification Likelihood) — Minimize

### UQ Integration

Enable UQ via `uq_samples`:

```python
budget_uq = BudgetSpec(max_iter=50, n_restarts=2, uq_samples=20)

result = run_community_algorithm(
    algorithm_id="dc_sbm",
    network=net,
    budget=budget_uq,
    seed=42,
    K_range=[2, 3, 4, 5]
)

# Access uncertainty
ll_mean = result.meta["log_likelihood"]
ll_std = result.meta["log_likelihood_std"]
print(f"Log-likelihood: {ll_mean:.2f} ± {ll_std:.2f}")
```

**UQ modes supported:**
1. **Bootstrap restarts:** Different random initializations (via `uq_samples`)
2. **Edge perturbation:** Refit on perturbed graphs (future)

### Successive Halving with SBM

SBM is SH-compatible with automatic budget scaling:

```python
result = (
    AutoCommunity()
      .candidates("louvain", "leiden", "dc_sbm")
      .metrics("modularity", "sbm_log_likelihood")
      .strategy(
          "successive_halving",
          eta=3,
          budget0={"max_iter": 10, "n_restarts": 1},
          utility_method="mean_minus_std"
      )
      .seed(42)
      .execute(net)
)
```

**Budget progression example (eta=3):**
- **Round 0:** `max_iter=10, n_restarts=1, K_range=[2,3,4]`
- **Round 1:** `max_iter=30, n_restarts=3, K_range=[2,3,4,5,6]`
- **Round 2:** `max_iter=90, n_restarts=9, K_range=[2,3,4,5,6,7,8]`

**Note:** SBM has higher computational cost per round than Louvain/Leiden, so SH is especially valuable for early elimination.

### Multilayer Support

SBM supports **shared-membership multilayer networks**:

```python
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'A', 'target': 'C', 'source_type': 'work', 'target_type': 'work'},
])

result = run_community_algorithm(
    algorithm_id="dc_sbm",
    network=net,
    budget=BudgetSpec(max_iter=100, n_restarts=3),
    seed=42,
    K_range=[2, 3, 4]
)
```

**Constraints:**
- All layers must be **node-aligned** (same nodes across layers)
- One latent assignment per node (shared across layers)
- Separate block affinity matrices per layer

### SBM Metrics

SBM provides specialized metrics for AutoCommunity:

| Metric | Direction | Description |
|--------|-----------|-------------|
| `sbm_log_likelihood` | Maximize | Model log-likelihood (higher = better fit) |
| `sbm_mdl` | Minimize | Minimum Description Length / BIC |
| `sbm_n_blocks` | None | Number of blocks selected by model |

**Usage:**
```python
result = (
    AutoCommunity()
      .candidates("dc_sbm", "louvain")
      .metrics("modularity", "sbm_log_likelihood", "sbm_mdl")
      .seed(42)
      .execute(net)
)
```

**Note:** SBM metrics return `None` for non-SBM algorithms.

### Determinism

SBM is fully deterministic under fixed seed:

```python
result1 = run_community_algorithm("dc_sbm", net, budget, seed=42)
result2 = run_community_algorithm("dc_sbm", net, budget, seed=42)

# Same partition, same K, same log-likelihood
assert result1.meta["K_selected"] == result2.meta["K_selected"]
assert abs(result1.meta["log_likelihood"] - result2.meta["log_likelihood"]) < 1e-6
```

**Seeding strategy:**
- Main seed spawns per-restart seeds deterministically
- UQ samples use deterministic seed spawning
- Multiple runs with same seed produce identical results

### Performance Guidelines

| Network Size | Recommended Budget |
|--------------|-------------------|
| Small (<100 nodes) | `BudgetSpec(max_iter=200, n_restarts=10)` |
| Medium (100-1K nodes) | `BudgetSpec(max_iter=100, n_restarts=5)` |
| Large (1K-10K nodes) | `BudgetSpec(max_iter=50, n_restarts=2)` |
| Very Large (>10K nodes) | Use Louvain/Leiden instead |

**Tips:**
- Start with small K_range (e.g., [2, 3, 4, 5]) for faster convergence
- Use Successive Halving to eliminate SBM early if underperforming
- Disable UQ for initial exploration (`uq_samples=None`)

### Metadata Schema

SBM results include:

```python
result.meta = {
    "model_type": "dc_sbm",              # or "sbm"
    "K_selected": 3,                     # Selected number of blocks
    "log_likelihood": -1234.56,          # ELBO (higher = better)
    "mdl": 2500.12,                      # MDL/BIC (lower = better)
    "converged": True,                   # Whether EM converged
    "n_iter": 45,                        # Number of EM iterations
    "uq_enabled": False,                 # Whether UQ was run
    "n_samples": None,                   # UQ samples (if enabled)
    "log_likelihood_std": None,          # Std dev of LL (if UQ enabled)
    "mdl_std": None,                     # Std dev of MDL (if UQ enabled)
}
```

### Common Pitfalls

1. **Node alignment:** Multilayer networks must have all nodes in all layers
   - **Fix:** Ensure all layers share the same node set

2. **Large K_range on big networks:** Exponential cost
   - **Fix:** Use conservative K_range (e.g., [2, 3, 4, 5])

3. **Comparing SBM metrics to non-SBM algorithms:** Apples to oranges
   - **Fix:** Use shared metrics like `modularity` or `coverage` for cross-algorithm comparison

4. **Insufficient restarts:** SBM can get stuck in local optima
   - **Fix:** Use `n_restarts >= 3` for reliable results

### References

- **Standard SBM:** Holland et al. (1983)
- **Degree-Corrected SBM:** Karrer & Newman (2011)
- **Variational inference:** Gopalan & Blei (2013)
- **Multilayer SBM:** Stanley et al. (2016)

