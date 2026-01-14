# py3plex AI Agent Documentation

> **Mission**: Make this single markdown file fully self-sufficient for an LLM agent to design correct, reproducible, performant py3plex pipelines end-to-end (discover → decide → build → validate → export) without guessing or hallucinating APIs.

**What this document is**:
- An operational playbook (not just API docs)
- A decision guide (when to use what)
- A set of known-good pipeline blueprints ("Golden Paths")
- A reproducibility + performance policy manual

**Version**: py3plex 1.1.1 | DSL v2.1 | Python 3.8+

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
22. [Performance Guidelines](#performance-guidelines)
23. [Reproducibility Policy](#reproducibility-policy)
24. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
25. [Testing Strategy](#testing-strategy)
26. [File Locations](#file-locations)

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

## DSL v2 (Q / UQ / L) — Complete Reference

### Minimal Mental Model

**Core Concepts**:
1. **Builder Lifecycle**: Build → Execute → Result
   - `Q.nodes()` creates a builder (lazy)
   - `.where()`, `.compute()`, etc. configure the builder (still lazy)
   - `.execute(network)` runs the query (eager) → returns `QueryResult`

2. **Lazy vs Eager**:
   - All builder methods (`.where()`, `.compute()`, `.from_layers()`) are **lazy** - they just build an AST
   - Only `.execute(network)` is **eager** - it runs the query
   - You can call `.to_ast()` to see the query without executing it

3. **Grouping and Coverage**:
   - `.per_layer()` / `.per_layer_pair()` enable grouping
   - `.top_k(k, key)` keeps top-k items **per group**
   - `.coverage(mode="all")` filters cross-group: keep items in all/any/k groups
   - **Order matters**: grouping → operations → end_grouping → coverage

4. **Return Types**:
   - Builder methods → `QueryBuilder` (chainable)
   - `.execute(network)` → `QueryResult` (rich result object)
   - `QueryResult.to_pandas()` → pandas DataFrame
   - `QueryResult.to_networkx()` → NetworkX graph
   - `QueryResult.to_arrow()` → Apache Arrow table

5. **Compute vs Aggregate**:
   - `.compute("degree")` - compute metric **per item** (node/edge)
   - `.aggregate(avg_degree="mean(degree)")` - compute **per group** statistic
   - Aggregate requires grouping; compute does not

---

### Q — Query Builder Factory

**Import**: `from py3plex.dsl import Q`

#### Q.nodes(autocompute=True) → QueryBuilder

Create a node query builder.

**Args**:
- `autocompute` (bool, default=True): Auto-compute referenced metrics if missing

**Returns**: `QueryBuilder` for nodes

**Example**:
```python
Q.nodes().where(degree__gt=5).execute(net)
Q.nodes(autocompute=False).where(layer="social").execute(net)
```

**Failure modes**:
- If `autocompute=False` and you filter on a metric not yet computed, execution fails
- Use `.compute()` explicitly to avoid this

---

#### Q.edges(autocompute=True) → QueryBuilder

Create an edge query builder.

**Args**:
- `autocompute` (bool, default=True): Auto-compute referenced metrics if missing

**Returns**: `QueryBuilder` for edges

**Example**:
```python
Q.edges().where(weight__gt=1.0).execute(net)
Q.edges().per_layer_pair().aggregate(count="count()").execute(net)
```

**Failure modes**:
- Edge endpoint properties (src_degree, dst_degree) require autocompute or pre-computation

---

#### Q.communities(autocompute=True, partition="default") → CommunityQueryBuilder

Create a community query builder.

**Args**:
- `autocompute` (bool, default=True): Auto-compute metrics if missing
- `partition` (str, default="default"): Partition name to query

**Returns**: `CommunityQueryBuilder` (extends QueryBuilder)

**Example**:
```python
# Detect communities first
from py3plex.algorithms.community_detection import louvain
communities = louvain(net)

# Query communities
Q.communities().where(size__gt=10).compute("modularity").execute(net)
Q.communities(partition="louvain").where(conductance__lt=0.5).execute(net)
```

**Failure modes**:
- Community partition must exist before querying
- Use `detect_communities()` first or pass results to network

---

#### Q.dynamics(process_name, **params) → DynamicsBuilder

Create a dynamics simulation builder.

**Args**:
- `process_name` (str): Process type ("SIS", "SIR", "SEIR", "RANDOM_WALK", "CUSTOM")
- `**params`: Process-specific parameters (e.g., `beta=0.3`, `mu=0.1`)

**Returns**: `DynamicsBuilder`

**Example**:
```python
sim = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .on_layers(L["contacts"])
     .seed_infections(0.01)
     .run(steps=100, replicates=10)
     .execute(net)
)
```

**See**: [Dynamics Simulations](#dynamics-simulations) section for full reference

---

#### Q.trajectories(process_ref) → TrajectoriesBuilder

Create a trajectories query builder (query simulation results).

**Args**:
- `process_ref` (str): Reference to simulation result

**Returns**: `TrajectoriesBuilder`

**Example**:
```python
# After running a simulation
result = Q.trajectories("sim_1").at(50).measure("peak_time").execute(context)
```

---

#### Q.counterexample() → CounterexampleBuilder

Create a counterexample search builder.

**Returns**: `CounterexampleBuilder`

**Example**:
```python
cex = (
    Q.counterexample()
     .claim("degree__ge(k) -> pagerank__rank_le(r)")
     .params(k=10, r=50)
     .seed(42)
     .execute(net)
)
```

**See**: [Counterexample Generation](#counterexample-generation) section

---

#### Q.learn_claims() → ClaimLearnerBuilder

Create a claim learning builder (hypothesis discovery).

**Returns**: `ClaimLearnerBuilder`

**Example**:
```python
claims = (
    Q.learn_claims()
     .from_metrics(["degree", "pagerank", "betweenness_centrality"])
     .min_support(0.9)
     .min_coverage(0.05)
     .seed(42)
     .execute(net)
)
```

**See**: [Claim Learning](#claim-learning-hypothesis-discovery) section

---

### QueryBuilder — Main Query Builder

**Obtained from**: `Q.nodes()` or `Q.edges()`

All methods return `self` (QueryBuilder) for chaining unless otherwise noted.

---

#### .from_layers(layer_expr) → QueryBuilder

Filter by layers using layer algebra.

**Args**:
- `layer_expr`: LayerExprBuilder from `L[...]` or LayerSet

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().from_layers(L["social"])
Q.nodes().from_layers(L["social"] + L["work"])
Q.nodes().from_layers(L["* - coupling"])  # All except coupling
```

**Semantics**:
- Selects only nodes/edges in specified layers
- Layer algebra: `+` (union), `-` (difference), `&` (intersection)
- `L["*"]` means all layers

**Failure modes**:
- Unknown layer names are caught at execution (raises `UnknownLayerError`)
- Empty layer expression → empty result (not an error)

---

#### .where(*args, **kwargs) → QueryBuilder

Add WHERE conditions (filtering).

**Args**:
- `*args`: BooleanExpression objects from `F` (e.g., `F.degree > 5`)
- `**kwargs`: Conditions as keyword arguments

**Returns**: QueryBuilder (self)

**Keyword Syntax**:
- Simple equality: `layer="social"`
- Comparisons: `degree__gt=5`, `degree__gte=5`, `degree__lt=10`, `degree__lte=10`, `degree__eq=5`, `degree__ne=3`
- Special predicates:
  - `intralayer=True` - edges within same layer
  - `interlayer=("social", "work")` - edges between specific layers
  - `t__between=(100, 200)` - temporal range
  - `t__gte=100`, `t__lt=200` - temporal comparisons

**Expression Syntax** (using `F`):
```python
from py3plex.dsl import F

Q.nodes().where(F.degree > 5)
Q.nodes().where((F.degree > 5) & (F.layer == "social"))
Q.nodes().where((F.degree > 10) | (F.clustering < 0.5))
```

**Operators**: `>`, `>=`, `<`, `<=`, `==`, `!=`, `&` (and), `|` (or), `~` (not)

**Example**:
```python
# Keyword style
Q.nodes().where(layer="social", degree__gt=5)
Q.edges().where(weight__gte=1.0, intralayer=True)

# Expression style
Q.nodes().where(F.degree > 5, F.layer == "social")
Q.nodes().where((F.degree > 10) | (F.betweenness_centrality > 0.1))

# Mix both
Q.nodes().where(F.degree > 5, layer="social")
```

**Semantics**:
- Multiple conditions are combined with AND
- Conditions are evaluated lazily at execution time
- Autocompute metrics referenced in conditions (if autocompute=True)

**Failure modes**:
- Unknown attributes raise `UnknownAttributeError` at execution
- Type mismatches (e.g., `layer > 5`) raise `TypeMismatchError`
- If autocompute=False and metric not computed, execution fails

---

#### .compute(*measures, **options) → QueryBuilder

Compute metrics per item (node/edge).

**Args**:
- `*measures` (str): Metric names to compute
- `alias` (str, optional): Alias for single measure
- `aliases` (Dict[str, str], optional): Map measure→alias
- `uncertainty` (bool, optional): Enable uncertainty for these measures
- `method`, `n_samples`, `ci`, etc.: Uncertainty options (see UQ section)

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree")
Q.nodes().compute("degree", "betweenness_centrality", "pagerank")
Q.nodes().compute("degree", alias="node_degree")
Q.nodes().compute("betweenness_centrality", "pagerank",
                  aliases={"betweenness_centrality": "bc", "pagerank": "pr"})

# With uncertainty
Q.nodes().compute("pagerank", uncertainty=True, n_samples=100, ci=0.95, seed=42)
```

**Built-in Metrics** (nodes):
- `degree` - Node degree
- `degree_centrality` - Normalized degree centrality
- `betweenness_centrality` - Betweenness centrality
- `closeness_centrality` - Closeness centrality
- `eigenvector_centrality` - Eigenvector centrality
- `pagerank` - PageRank
- `clustering` - Clustering coefficient
- `strength` - Weighted degree (sum of edge weights)
- `layer_count` - Number of layers node appears in

**Built-in Metrics** (edges):
- `weight` - Edge weight (default: 1.0)
- `src_degree`, `dst_degree` - Endpoint degrees
- `edge_betweenness_centrality` - Edge betweenness

**Custom Metrics**: Use plugin system or `.mutate()` for derived metrics

**Semantics**:
- Computes metrics for **each item** (not aggregated)
- Results stored in QueryResult.attributes
- Multiple `.compute()` calls accumulate (don't replace)

**Failure modes**:
- Unknown measure names raise `UnknownMeasureError`
- Some measures require simple graphs (e.g., clustering) → auto-converted if needed
- Computationally expensive on large networks (>10k nodes)

---

#### .order_by(*keys, desc=False) → QueryBuilder

Sort results by one or more keys.

**Args**:
- `*keys` (str): Attribute names to sort by. Prefix with `-` for descending (e.g., `"-degree"`)
- `desc` (bool, default=False): Sort descending (applies to all keys if no `-` prefix)

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").order_by("degree")  # Ascending
Q.nodes().compute("degree").order_by("-degree")  # Descending
Q.nodes().compute("degree").order_by("degree", desc=True)  # Descending
Q.nodes().compute("degree", "layer").order_by("layer", "degree")  # Multi-key
Q.nodes().compute("degree", "pagerank").order_by("-pagerank", "-degree")  # Both desc
```

**Semantics**:
- Stable sort (preserves order of equal elements)
- Multi-key sort: primary key first, then secondary, etc.
- `-` prefix overrides `desc` parameter for that key

**Failure modes**:
- Unknown keys raise error at execution
- Keys must be in result (computed or intrinsic like "node", "layer")

---

#### .limit(n) → QueryBuilder

Limit result to first n items.

**Args**:
- `n` (int): Maximum number of items to return

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").order_by("-degree").limit(10)  # Top 10 by degree
```

**Semantics**:
- Applied **after** ordering
- Does not interact with grouping (see `.top_k()` for per-group limits)

---

#### .uq(method, n_samples, ci, seed, **options) → QueryBuilder

Enable uncertainty quantification for the query.

**Args**:
- `method` (str): "bootstrap", "perturbation", "seed"
- `n_samples` (int): Number of samples for UQ
- `ci` (float): Confidence interval level (e.g., 0.95 for 95%)
- `seed` (int): Random seed for reproducibility
- `**options`: Additional UQ options (bootstrap_unit, bootstrap_mode, etc.)

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("pagerank").uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
Q.nodes().compute("degree", "betweenness").uq(method="perturbation", n_samples=50, seed=123)
```

**Methods**:
- `"bootstrap"`: Resample edges/nodes/layers
- `"perturbation"`: Add noise to edge weights
- `"seed"`: Multi-run with different random seeds

**Semantics**:
- Computes metrics multiple times with resampling
- Returns mean, std, confidence intervals
- Use `.to_pandas(expand_uncertainty=True)` to get CI columns

**See**: [Uncertainty Quantification](#uncertainty-quantification) for detailed reference

**Failure modes**:
- Computationally expensive (n_samples × metric cost)
- Requires deterministic metrics (some algorithms use randomness)
- Seed must be set for reproducibility

---

#### .per_layer() → QueryBuilder

Group results by layer (for **node** queries).

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().per_layer().top_k(5, "degree")
```

**Semantics**:
- Shorthand for `.group_by("layer")`
- Enables per-layer operations (`.top_k()`, `.aggregate()`)
- **Only valid for node queries** (raises error for edges)

**After grouping, use**:
- `.top_k(k, key)` - top-k per layer
- `.aggregate(...)` - compute per-layer statistics
- `.end_grouping()` - marker for readability
- `.coverage(...)` - cross-layer filtering

**Failure modes**:
- Called on edge query → raises `DslExecutionError`
- Forgetting `.end_grouping()` before `.coverage()` → may be confusing but not an error

---

#### .per_layer_pair() → QueryBuilder

Group edge results by (src_layer, dst_layer) pair (for **edge** queries).

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.edges().per_layer_pair().aggregate(count="count()", avg_weight="mean(weight)")
```

**Semantics**:
- Shorthand for `.group_by("src_layer", "dst_layer")`
- Enables per-layer-pair operations
- **Only valid for edge queries** (raises error for nodes)

**Failure modes**:
- Called on node query → raises `DslExecutionError`

---

#### .top_k(k, key=None) → QueryBuilder

Keep top-k items per group.

**Args**:
- `k` (int): Number of items to keep per group
- `key` (str, optional): Attribute to sort by (descending). If None, uses existing order_by.

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().per_layer().top_k(5, "degree")
Q.nodes().per_layer().compute("betweenness").top_k(10, "betweenness_centrality")
```

**Semantics**:
- Requires prior grouping (`.per_layer()` or `.group_by()`)
- Keeps top-k **per group** (not global top-k)
- If key provided, implicitly sets `.order_by(f"-{key}")`

**Failure modes**:
- Called without grouping → raises `ValueError`
- Key must be in result (computed or intrinsic)

---

#### .end_grouping() → QueryBuilder

Marker for end of grouping configuration (readability).

**Returns**: QueryBuilder (self)

**Example**:
```python
(Q.nodes()
  .per_layer()
    .top_k(5, "degree")
  .end_grouping()
  .coverage(mode="all"))
```

**Semantics**:
- No execution effect (purely for API readability)
- Helps visually separate grouping operations from post-grouping operations

---

#### .coverage(mode, k=None, threshold=None, p=None) → QueryBuilder

Filter items based on cross-group coverage.

**Args**:
- `mode` (str): "all", "any", "at_least", "exact", "fraction"
- `k` (int, optional): Threshold for "at_least" or "exact" modes
- `threshold` (int, optional): Alias for `k`
- `p` (float, optional): Fraction threshold (0.0-1.0) for "fraction" mode

**Returns**: QueryBuilder (self)

**Modes**:
- `"all"`: Keep items in ALL groups
- `"any"`: Keep items in at least ONE group (default behavior, not usually needed)
- `"at_least"`: Keep items in at least k groups (requires `k` or `threshold`)
- `"exact"`: Keep items in exactly k groups (requires `k`)
- `"fraction"`: Keep items in at least p fraction of groups (requires `p`, e.g., p=0.67 for 67%)

**Example**:
```python
# Cross-layer hubs (top-5 degree in ALL layers)
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="all")

# Top-5 in at least 2 layers
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="at_least", k=2)

# Top-10 in at least 70% of layers
Q.nodes().per_layer().top_k(10, "degree").coverage(mode="fraction", p=0.7)
```

**Semantics**:
- Requires prior grouping
- Applied **after** per-group operations (`.top_k()`, `.aggregate()`)
- Filters final result to items meeting cross-group criteria

**Failure modes**:
- Called without grouping → raises `GroupingError`
- Invalid mode → raises `ValueError`
- Missing required parameters (k for "at_least", p for "fraction") → raises `ValueError`

---

#### .aggregate(**aggregations) → QueryBuilder

Compute per-group statistics.

**Args**:
- `**aggregations`: Map of `alias="function(attribute)"` pairs

**Returns**: QueryBuilder (self)

**Functions**:
- `count()` / `n()`: Count of items in group
- `mean(attr)`: Arithmetic mean
- `median(attr)`: Median value
- `sum(attr)`: Sum of values
- `min(attr)`, `max(attr)`: Minimum/maximum
- `std(attr)`, `var(attr)`: Standard deviation and variance
- `quantile(attr, p)`: p-th quantile (e.g., `quantile(degree, 0.95)`)

**Example**:
```python
# Per-layer statistics
Q.nodes().per_layer().aggregate(
    node_count="count()",
    avg_degree="mean(degree)",
    median_degree="median(degree)",
    q95_degree="quantile(degree, 0.95)"
)

# Per-layer-pair edge statistics
Q.edges().per_layer_pair().aggregate(
    edge_count="count()",
    avg_weight="mean(weight)",
    total_weight="sum(weight)"
)
```

**Semantics**:
- Requires prior grouping
- Returns **one row per group** (not per item)
- Result has group keys (layer, src_layer/dst_layer) + computed aggregates

**Failure modes**:
- Called without grouping → error
- Unknown aggregation functions → error
- Attribute not in result → error

---

#### .filter(*args, **kwargs) → QueryBuilder

Alias for `.where()` (dplyr-style naming).

**See**: `.where()` documentation above

---

#### .filter_expr(expr) → QueryBuilder

Filter using string expression.

**Args**:
- `expr` (str): Boolean expression string

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().filter_expr("degree > 5 and layer == 'social'")
Q.edges().filter_expr("weight >= 1.0 and intralayer")
```

**Semantics**:
- Parses expression and converts to condition AST
- Supports: `>`, `>=`, `<`, `<=`, `==`, `!=`, `and`, `or`, `not`

**Failure modes**:
- Invalid syntax → parse error
- Unknown attributes → error at execution

---

#### .head(n=5) → QueryBuilder

Keep first n results (dplyr-style).

**Args**:
- `n` (int, default=5): Number of items to keep

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").order_by("-degree").head(10)
```

**Semantics**:
- Alias for `.limit(n)`
- Applied after ordering

---

#### .tail(n=5) → QueryBuilder

Keep last n results (dplyr-style).

**Args**:
- `n` (int, default=5): Number of items to keep

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").order_by("degree").tail(10)  # 10 lowest degree
```

**Semantics**:
- Reverses order, takes first n, reverses again
- Applied after ordering

---

#### .sample(n=5, seed=None) → QueryBuilder

Random sample of n items (dplyr-style).

**Args**:
- `n` (int, default=5): Number of items to sample
- `seed` (int, optional): Random seed for reproducibility

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().sample(10, seed=42)  # Random 10 nodes, reproducible
```

**Semantics**:
- Random sampling without replacement
- Seed ensures reproducibility

**Failure modes**:
- If n > result size, returns all items (not an error)

---

#### .slice(start, end=None) → QueryBuilder

Array-style slicing (dplyr-style).

**Args**:
- `start` (int): Start index (inclusive, 0-based)
- `end` (int, optional): End index (exclusive). If None, goes to end.

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().slice(10, 20)  # Items 10-19
Q.nodes().slice(5, None)  # Items 5 to end
```

**Semantics**:
- Python-style slicing
- Applied after ordering

---

#### .mutate(**transformations) → QueryBuilder

Add or modify attributes using lambda functions (dplyr-style).

**Args**:
- `**transformations`: Map of `new_attr=lambda row: expression` pairs

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").mutate(
    norm_deg=lambda r: r["degree"] / 10,
    is_hub=lambda r: r["degree"] > 5
)
```

**Semantics**:
- Computes new attributes from existing ones
- Lambda receives row dict with all current attributes
- Can reference computed metrics

**Failure modes**:
- Lambda errors (e.g., KeyError for missing attr) propagate at execution

---

#### .select(*columns) → QueryBuilder

Keep only specified columns in result (dplyr-style).

**Args**:
- `*columns` (str): Column names to keep

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree", "pagerank").select("node", "layer", "degree")
```

**Semantics**:
- Projection operation (like SQL SELECT)
- Other columns are dropped from result

---

#### .rename(**mapping) → QueryBuilder

Rename columns (dplyr-style).

**Args**:
- `**mapping`: Map of `old_name="new_name"` pairs

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.nodes().compute("degree").rename(degree="node_degree", layer="layer_name")
```

---

#### .arrange(*columns, desc=False) → QueryBuilder

Alias for `.order_by()` (dplyr-style).

**See**: `.order_by()` documentation

---

#### .at(t) → QueryBuilder

Temporal snapshot at time t (temporal networks).

**Args**:
- `t` (float): Timestamp

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.edges().at(150.0).execute(temporal_net)
```

**Semantics**:
- Filters edges to those active at time t
- Requires `t_start`/`t_end` or `t` on edges

**See**: [Temporal Networks](#temporal-networks) section

---

#### .during(t_start, t_end) → QueryBuilder

Temporal range query [t_start, t_end] (temporal networks).

**Args**:
- `t_start` (float): Start time (inclusive)
- `t_end` (float): End time (inclusive)

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.edges().during(100.0, 200.0).execute(temporal_net)
```

**Semantics**:
- Filters edges to those active in interval
- Requires `t_start`/`t_end` or `t` on edges

---

#### .before(t) → QueryBuilder

Temporal query for edges before time t.

**Args**:
- `t` (float): Cutoff time

**Returns**: QueryBuilder (self)

---

#### .after(t) → QueryBuilder

Temporal query for edges after time t.

**Args**:
- `t` (float): Cutoff time

**Returns**: QueryBuilder (self)

---

#### .window(size, stride=None, ...) → QueryBuilder

Sliding window temporal query (temporal networks).

**Args**:
- `size` (float): Window size
- `stride` (float, optional): Stride (default: size, non-overlapping)
- Additional params: anchors, aggregation, etc.

**Returns**: QueryBuilder (self)

**Example**:
```python
Q.edges().window(size=100.0, stride=50.0).execute(temporal_net)
```

**See**: [Temporal Networks](#temporal-networks) section

---

#### .execute(network, progress=True, **params) → QueryResult

Execute the query and return results.

**Args**:
- `network`: multi_layer_network or TemporalMultiLayerNetwork instance
- `progress` (bool, default=True): Show progress logging
- `**params`: Parameter bindings (for Param.ref placeholders)

**Returns**: `QueryResult`

**Example**:
```python
result = Q.nodes().where(degree__gt=Param.int("k")).execute(net, k=5)
```

**Semantics**:
- **This is the only eager operation**
- Compiles query to AST, binds parameters, executes
- Returns rich QueryResult object

**Failure modes**:
- Network validation errors
- Unknown layers, attributes, measures
- Parameter binding errors (missing or type mismatch)

---

#### .to_ast() → Query

Export query as AST without executing.

**Returns**: AST Query object

**Example**:
```python
ast = Q.nodes().where(degree__gt=5).compute("pagerank").to_ast()
print(ast)  # Inspect AST structure
```

**Use cases**:
- Debugging query structure
- Serializing queries
- Static analysis

---

### QueryResult — Rich Result Object

**Obtained from**: `.execute(network)`

#### Attributes

- `result.target`: "nodes" or "edges"
- `result.items`: List of node/edge items (tuples)
- `result.attributes`: Dict of computed attributes (e.g., `{"degree": {...}}`)
- `result.meta`: Metadata dict (provenance, grouping, etc.)
- `result.count`: Number of items (same as `len(result)`)

#### Methods

##### .to_pandas(expand_uncertainty=False, expand_explanations=False) → DataFrame

Convert to pandas DataFrame.

**Args**:
- `expand_uncertainty` (bool): Expand UQ columns (_mean, _std, _ci95_low, _ci95_high)
- `expand_explanations` (bool): Expand explain() metadata into columns

**Returns**: pandas DataFrame

**Example**:
```python
df = result.to_pandas()
df = result.to_pandas(expand_uncertainty=True)
```

---

##### .to_networkx() → nx.Graph

Convert result to NetworkX graph.

**Returns**: NetworkX Graph or MultiGraph

---

##### .to_arrow() → pyarrow.Table

Convert to Apache Arrow table (for interop with other tools).

**Returns**: Apache Arrow Table

---

##### .to_dict() → dict

Convert to plain dictionary (backward compatible with legacy DSL).

**Returns**: Dictionary with keys: query, target, nodes/edges, count, computed, meta

---

##### .group_summary() → DataFrame

Get summary of grouped results (when grouping is used).

**Returns**: DataFrame with group keys and per-group statistics

**Example**:
```python
result = (Q.nodes()
           .per_layer()
           .aggregate(count="count()", avg_degree="mean(degree)")
           .execute(net))
df = result.group_summary()
```

---

##### .counterexample(claim, **kwargs) → Counterexample | None

Lazily find counterexample for a claim on this result's network.

**Args**:
- `claim` (str): Claim string (e.g., "degree__ge(k) -> pagerank__rank_le(r)")
- `**kwargs`: Passed to counterexample engine (params, seed, etc.)

**Returns**: Counterexample object or None

**Example**:
```python
result = Q.nodes().compute("degree", "pagerank").execute(net)
cex = result.counterexample("degree__ge(k) -> pagerank__rank_le(r)", k=10, r=50, seed=42)
```

**See**: [Counterexample Generation](#counterexample-generation)

---

### L — Layer Algebra Builder

**Import**: `from py3plex.dsl import L`

#### L["layer_name"] → LayerExprBuilder

Create a layer expression builder.

**Example**:
```python
L["social"]  # Single layer
L["social"] + L["work"]  # Union
L["social"] - L["bots"]  # Difference
L["social"] & L["work"]  # Intersection
L["*"]  # All layers
L["*"] - L["coupling"]  # All except coupling
```

**Operators**:
- `+`: Union of layers
- `-`: Difference (A - B = elements in A but not B)
- `&`: Intersection
- `L["*"]`: All layers (wildcard)

**Advanced Syntax** (LayerSet parsing):
```python
L["* - coupling"]  # String expression with operators
L["(ppi | gene) & disease"]  # Parentheses and pipe operator
```

**Semantics**:
- Builds AST for layer selection
- Resolved at execution time against network's layers
- Unknown layers → error at execution

**Failure modes**:
- Empty result (e.g., `L["social"] & L["work"]` on network without both) → empty query result, not error

---

#### L.define(name, layer_expr)

Define named layer group for reuse.

**Args**:
- `name` (str): Group name
- `layer_expr`: LayerExprBuilder or LayerSet

**Example**:
```python
bio = L["ppi"] | L["gene"] | L["disease"]
L.define("bio", bio)

# Later
Q.nodes().from_layers(L["bio"]).execute(net)
```

---

#### L.list_groups() → dict

List all defined layer groups.

**Returns**: Dictionary mapping group names to layer expressions

---

#### L.clear_groups()

Clear all defined layer groups.

---

### UQ — Uncertainty Quantification Factory

**Import**: `from py3plex.dsl import UQ`

UQ provides defaults for uncertainty quantification across queries.

#### UQ.defaults(method, n_samples, ci, seed, **options) → UncertaintyConfig

Set default UQ configuration.

**Args**:
- `method` (str): "bootstrap", "perturbation", "seed"
- `n_samples` (int): Number of samples
- `ci` (float): Confidence interval level (e.g., 0.95)
- `seed` (int): Random seed
- `**options`: bootstrap_unit, bootstrap_mode, etc.

**Returns**: UncertaintyConfig object

**Example**:
```python
UQ.defaults(method="bootstrap", n_samples=100, ci=0.95, seed=42)

# Now all queries with uncertainty=True use these defaults
Q.nodes().compute("pagerank", uncertainty=True).execute(net)
```

**See**: [Uncertainty Quantification](#uncertainty-quantification) for full reference

---

### Param — Parameter Placeholders

**Import**: `from py3plex.dsl import Param`

Param creates parameter placeholders for parameterized queries.

#### Param.int(name) → ParamRef

Integer parameter.

**Example**:
```python
q = Q.nodes().where(degree__gt=Param.int("k"))
result = q.execute(net, k=5)
```

---

#### Param.float(name) → ParamRef

Float parameter.

**Example**:
```python
q = Q.nodes().where(weight__gte=Param.float("threshold"))
result = q.execute(net, threshold=1.5)
```

---

#### Param.str(name) → ParamRef

String parameter.

**Example**:
```python
q = Q.nodes().where(layer=Param.str("target_layer"))
result = q.execute(net, target_layer="social")
```

---

#### Param.ref(name) → ParamRef

Untyped parameter reference.

**Example**:
```python
q = Q.nodes().where(degree__gt=Param.ref("threshold"))
result = q.execute(net, threshold=10)
```

---

### F — Field Expressions

**Import**: `from py3plex.dsl import F`

F provides a fluent API for building filter expressions.

#### F.field_name → FieldProxy

Access field for comparisons.

**Example**:
```python
F.degree > 5
F.degree >= 10
F.layer == "social"
F.weight != 1.0
(F.degree > 5) & (F.layer == "social")
(F.degree > 10) | (F.clustering < 0.5)
~(F.degree < 5)  # NOT
```

**Operators**:
- Comparison: `>`, `>=`, `<`, `<=`, `==`, `!=`
- Logical: `&` (and), `|` (or), `~` (not)

**Usage in `.where()`**:
```python
Q.nodes().where(F.degree > 5)
Q.nodes().where((F.degree > 5) & (F.layer == "social"))
```

---

### Common Patterns

#### Pattern 1: Top-k Hubs per Layer

```python
result = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree", "betweenness_centrality")
     .per_layer()
       .top_k(10, "degree")
     .end_grouping()
     .execute(net)
)
```

---

#### Pattern 2: Cross-Layer Hubs (All Layers)

```python
result = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
       .top_k(20, "degree")
     .end_grouping()
     .coverage(mode="all")  # Must be top-20 in ALL layers
     .execute(net)
)
```

---

#### Pattern 3: Aggregation per Layer

```python
result = (
    Q.nodes()
     .per_layer()
     .aggregate(
         node_count="count()",
         avg_degree="mean(degree)",
         q95_degree="quantile(degree, 0.95)"
     )
     .execute(net)
)

df = result.to_pandas()
# Columns: layer, node_count, avg_degree, q95_degree
```

---

#### Pattern 4: Filtered Aggregation

```python
result = (
    Q.nodes()
     .where(degree__gt=5)  # Filter first
     .per_layer()
     .aggregate(
         high_degree_count="count()",
         avg_bc="mean(betweenness_centrality)"
     )
     .execute(net)
)
```

---

#### Pattern 5: Temporal Snapshot with Grouping

```python
result = (
    Q.edges()
     .during(100.0, 200.0)
     .per_layer_pair()
     .aggregate(
         edge_count="count()",
         avg_weight="mean(weight)"
     )
     .execute(temporal_net)
)
```

---

#### Pattern 6: Uncertainty with Filtering

```python
result = (
    Q.nodes()
     .where(degree__gt=10)
     .compute("pagerank", "betweenness_centrality")
     .uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
     .order_by("-pagerank")
     .limit(20)
     .execute(net)
)

df = result.to_pandas(expand_uncertainty=True)
# Columns include: pagerank_mean, pagerank_std, pagerank_ci95_low, pagerank_ci95_high
```

---

### Failure Mode Reference

**Empty Results**:
- Layer expressions that match no layers → empty result (not error)
- Filters that match no items → empty result (not error)
- `SELECT nodes WHERE degree > 1000` on small network → empty result

**Execution Errors**:
- Unknown layer names → `UnknownLayerError`
- Unknown attributes → `UnknownAttributeError`
- Unknown measures → `UnknownMeasureError`
- Type mismatches (e.g., `layer > 5`) → `TypeMismatchError`
- Grouping errors (e.g., `.top_k()` without `.per_layer()`) → `GroupingError`

**Parameter Binding Errors**:
- Missing parameters → `ParameterMissingError`
- Type mismatches → binding errors at execution

**Autocompute Limitations**:
- If `autocompute=False` and metric referenced in filter not computed → error
- Circular dependencies in metrics → error (rare)

**Performance Issues**:
- Large networks (>10k nodes) with expensive metrics (betweenness, closeness) → slow
- UQ with many samples (>1000) → very slow
- Solution: Use smaller sample sizes, profile with `.meta['provenance']['performance']`

---

### Performance Tips

1. **Filter early**: Use `.where()` before `.compute()` to reduce computation
2. **Disable autocompute**: If you know metrics are pre-computed, use `autocompute=False`
3. **Use layer algebra**: `L["social"]` is faster than selecting all and filtering
4. **Batch computations**: Compute multiple metrics in one `.compute()` call
5. **UQ sampling**: Start with n_samples=10-20 for development, increase for production
6. **Temporal queries**: Use `.at()` or `.during()` to reduce edge set before other operations
7. **Grouping**: Use `.per_layer()` early to parallelize computations (future feature)

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

**Multi-seed (Deterministic Metrics)**:
```python
result = (
    Q.nodes()
     .compute("louvain_community")
     .uq(method="seed", n_samples=20, seed=42)
     .execute(net)
)
```

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


### 9.3 Compositional UQ (Aggregate/Summarize/Ranking) — **NEW in v1.1**

**Goal**: Propagate uncertainty through complete query pipelines, not just compute() operations.

Compositional UQ wraps the entire query execution with resampling, executing the query multiple times on resampled networks and aggregating results. This provides uncertainty for:
- Aggregate/summarize statistics (mean, median, quantiles)
- Ranking stability (order_by/limit operations)
- Coverage membership probability

#### Why Compositional UQ?

Traditional UQ only affects `.compute()` - it gives you uncertainty per node/edge but deterministic aggregates. Compositional UQ gives you uncertainty **for the aggregate itself**.

**Example**: "What is the average degree with confidence interval?"
- Traditional: Average of uncertain node degrees → single value
- Compositional: Uncertain average degree → mean ± std, with CI

#### Basic Usage: Aggregate with UQ

```python
from py3plex.dsl import Q

# Compute average degree with uncertainty
result = (
    Q.nodes()
     .compute("degree")
     .summarize(avg_degree="mean(degree)", median="median(degree)")
     .uq(method="seed", n_samples=50, seed=42)
     .execute(net)
)

# Extract results with uncertainty
df = result.to_pandas(expand_uncertainty=True)
print(df[["avg_degree", "avg_degree_std", "avg_degree_ci95_low", "avg_degree_ci95_high"]])
```

**Output attributes** have uncertainty structure:
```python
{
    "mean": 2.5,           # Mean across resamples
    "std": 0.3,            # Standard deviation
    "quantiles": {         # Confidence intervals
        0.025: 1.9,
        0.975: 3.1
    },
    "n_samples": 50
}
```

#### Per-Layer Aggregation with UQ

```python
result = (
    Q.nodes()
     .compute("degree")
     .per_layer()
     .aggregate(
         avg_degree="mean(degree)",
         node_count="count()",
         q95_degree="quantile(degree, 0.95)"
     )
     .uq(method="perturbation", n_samples=100, seed=42)
     .execute(net)
)

# Each layer gets uncertainty estimates
df = result.to_pandas(expand_uncertainty=True)
# Columns: layer, avg_degree, avg_degree_std, avg_degree_ci95_low, ...
```

#### Ranking Stability (Order_by with UQ)

Compositional UQ for ranking produces **rank stability metrics**:

```python
result = (
    Q.nodes()
     .compute("betweenness_centrality")
     .order_by("-betweenness_centrality")
     .limit(10)  # Top 10
     .uq(method="perturbation", n_samples=50, seed=42)
     .execute(net)
)

# Access rank stability
rank_stab = result.meta["rank_stability"]
print(f"Kendall tau: {rank_stab['kendall_tau_mean']:.3f}")

# Per-node rank uncertainty
for node in result.items[:5]:
    rank_mean = rank_stab["rank_means"][node]
    rank_std = rank_stab["rank_stds"][node]
    print(f"{node}: rank {rank_mean:.1f} ± {rank_std:.2f}")
```

**Stability Metrics**:
- `kendall_tau_mean`: Rank correlation across resamples (1.0 = perfect stability)
- `rank_means`: Mean rank per item
- `rank_stds`: Standard deviation of rank per item
- `rank_quantiles`: CI for ranks

**Interpreting rank stability**:
- Kendall tau > 0.8: Stable ranking
- Kendall tau 0.6-0.8: Moderate stability
- Kendall tau < 0.6: Unstable (sensitive to perturbations)

#### Coverage with UQ

Coverage membership becomes probabilistic:

```python
result = (
    Q.nodes()
     .compute("degree")
     .per_layer()
     .top_k(5, "degree")
     .coverage(mode="all")  # Cross-layer hubs
     .uq(method="perturbation", n_samples=100, seed=42)
     .execute(net)
)

# Access coverage stability
cov_stab = result.meta["coverage_stability"]
print(f"Stable members: {len(cov_stab['stable_members'])}")
print(f"Boundary members: {len(cov_stab['boundary_members'])}")

# Per-node inclusion probability
for node in result.items:
    prob = cov_stab["inclusion_probability"][node]
    print(f"{node}: {prob:.1%} inclusion")
```

**Coverage Metrics**:
- `inclusion_probability`: P(node in coverage set) across resamples
- `stable_members`: Nodes with P ≥ 0.8
- `boundary_members`: Nodes with 0.2 < P < 0.8

#### UQ Methods

Same as compute() UQ, but affects entire pipeline:
- `"seed"`: Multi-run with different random seeds (fastest, for stochastic algorithms)
- `"perturbation"`: Perturb network structure between runs (most informative)
- `"bootstrap"`: Resample edges/nodes with replacement

**Seed specification** is critical for reproducibility:
```python
# Deterministic: same seed → identical results
.uq(method="seed", n_samples=100, seed=42)
```

Internal: Uses `numpy.random.SeedSequence` to generate child seeds deterministically.

#### Metadata

Compositional UQ adds to `result.meta`:
```python
{
    "uq": {
        "type": "compositional",
        "method": "perturbation",
        "n_samples": 50,
        "seed": 42,
        "has_aggregate": True,
        "has_ordering": True,
        "has_coverage": False
    },
    "rank_stability": {...},      # If order_by used
    "coverage_stability": {...}   # If coverage used
}
```

#### When to Use Compositional vs Compute UQ

**Use Compositional UQ when**:
- You need uncertainty for **aggregate statistics** (mean, median, quantiles)
- You want **ranking stability** (which nodes are reliably in top-k?)
- You want **coverage membership probability**
- Your query has `.aggregate()`, `.summarize()`, `.order_by()`, or `.coverage()`

**Use Compute UQ when**:
- You only need **per-node/per-edge uncertainty**
- No aggregation or ranking involved
- Query is just `.compute()` → `.to_pandas()`

**Both work together**: Compositional UQ automatically wraps compute() operations.

#### Performance Notes

Compositional UQ runs the entire query `n_samples` times:
- Cost: O(n_samples × query_cost)
- Typical: 50-100 samples for dev, 300+ for publications
- Parallelization: Not yet implemented (future work)

**Tips**:
- Start with `n_samples=10` during development
- Use `method="seed"` for quick iterations (no network modification)
- Increase to 50-100 for reliable CI estimates
- Use 300+ for publication-quality results


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

Every query execution records provenance:

```python
result = Q.nodes().compute("pagerank").execute(net)

prov = result.meta['provenance']

# Key provenance fields
print(prov['engine'])             # "dsl_v2_executor"
print(prov['py3plex_version'])    # "1.1.1"
print(prov['timestamp_utc'])      # ISO8601 timestamp
print(prov['network_fingerprint']) # Node/edge counts, layers
print(prov['query']['ast_hash'])  # Stable hash of query AST
print(prov['randomness']['seed']) # Random seed if used
print(prov['performance']['total_ms']) # Execution time
```

### Reproducibility Checklist

- [ ] Set `seed` parameter for all randomized operations
- [ ] Document `py3plex.__version__` in code/paper
- [ ] Save provenance metadata: `result.meta['provenance']`
- [ ] Archive network data with checksums
- [ ] Document Python and dependency versions
- [ ] Use parameterized queries with Param.ref() for reusability

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

print(py3plex.__version__)  # "1.1.1"
```

**Version History**:
- **1.1.1** (Current): Documentation updates and AutoCommunity examples
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
      "py3plex": "1.1.1",
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

**Last Updated**: 2026-01-11 (for py3plex v1.1.1 + MCP v1.0.0)


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

