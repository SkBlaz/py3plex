# py3plex AI Agent Documentation

> **Mission**: Make this single markdown file fully self-sufficient for an LLM agent to design correct, reproducible, performant py3plex pipelines end-to-end (discover -> decide -> build -> validate -> export) without guessing or hallucinating APIs.

**What this document is**:
- An operational playbook (not just API docs)
- A decision guide (when to use what)
- A set of known-good pipeline blueprints ("Golden Paths")
- A reproducibility + performance policy manual

**Version**: py3plex 1.1.4 | DSL v2.1 | Python 3.8+

** New to py3plex?** 
- **5 minutes**: See [dsl_patterns_quick_reference.py](examples/getting_started/dsl_patterns_quick_reference.py) for 7 copy-paste patterns
- **15 minutes**: Jump to [Quick Start: Golden Paths](#quick-start-golden-paths) for 5 high-value patterns that cover common workflows
- **Deep dive**: Continue reading this comprehensive guide

---

## Table of Contents

1. [Quick Start: Golden Paths](#quick-start-golden-paths)
2. [NEW: Ergonomics Features (v1.1+)](#new-ergonomics-features-v11)
3. [DSL v2 (Q / UQ / L) — Complete Reference](#dsl-v2-q-uq-l--complete-reference)
4. [Decision Guide: Which API When?](#decision-guide-which-api-when)
5. [Legacy DSL (String-Based)](#legacy-dsl-string-based)
6. [Dplyr-Style Operations](#dplyr-style-operations)
7. [Pipeline API (Sklearn-Style)](#pipeline-api-sklearn-style)
8. [I/O and Data Loading](#io-and-data-loading)
9. [Network Type Conversions](#network-type-conversions)
10. [Dynamics Simulations](#dynamics-simulations)
11. [Uncertainty Quantification](#uncertainty-quantification)
12. [Temporal Networks](#temporal-networks)
13. [Null Models and Statistical Testing](#null-models-and-statistical-testing)
14. [Counterexample Generation](#counterexample-generation)
15. [Claim Learning (Hypothesis Discovery)](#claim-learning-hypothesis-discovery)
16. [Semiring Algebra (Paths, Closure, Fixed-Point)](#semiring-algebra-paths-closure-fixed-point)
17. [Community Detection and Queries](#community-detection-and-queries)
18. [Pattern Matching (Cypher-like)](#pattern-matching-cypher-like)
19. [Network Comparison and Diff](#network-comparison-and-diff)
20. [CLI Tool](#cli-tool)
21. [Plugin System](#plugin-system)
22. [Configuration and Profiling](#configuration-and-profiling)
23. [Diagnostic System and Error Reporting](#diagnostic-system-and-error-reporting)
24. [Exception Hierarchy](#exception-hierarchy)
25. [Query Planner and Optimization](#query-planner-and-optimization)
26. [Performance Guidelines](#performance-guidelines)
27. [Reproducibility Policy](#reproducibility-policy)
28. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
29. [Multilayer Semantics Guide](#multilayer-semantics-guide)
30. [Testing Strategy](#testing-strategy)
31. [File Locations](#file-locations)

---

## NEW: Ergonomics Features (v1.1+)

py3plex v1.1+ includes systematic ergonomics improvements to reduce user friction and cognitive load. These features are designed for both humans and LLM agents.

### Interactive Query Building: `.hint()`

**What it does**: Provides context-aware suggestions for next query-building steps.

```python
from py3plex.dsl import Q, L

# Start building
q = Q.nodes().from_layers(L["social"])

# Get hints
q.hint()
# Outputs:
# [HINT] Query Builder Hints
# ==========================================
# [STATE] Current query state:
#    Layers selected
#
# [TIP] Suggested next steps:
# 1. -> .where(degree__gt=3)  # Filter nodes by attributes
# 2. -> .compute("degree", "betweenness_centrality")  # Compute metrics
# 3. -> .per_layer()  # Group results by layer
# ...

# Continue building based on hints
q = q.compute("degree").hint()  # Get new suggestions
```

**Key features**:
- Non-invasive (only displays info, doesn't modify query)
- Context-aware (suggestions adapt to query state)
- Chainable (returns self for chaining)
- Educational (includes examples and method signatures)

**When to use**: During interactive development, learning the API, or when unsure what methods are available next.

**LLM agent guidance**: Call `.hint()` when:
- Building complex queries and unsure of next steps
- Learning new DSL features
- Debugging query construction issues

**Validation status**:
- Execution and chaining behavior are covered by `tests/test_agents_ergonomics_features.py`
- Exact hint text and formatting may evolve between versions; rely on API behavior, not exact output text

### Enhanced QueryResult Introspection

**What it does**: QueryResult objects now have rich `__repr__` showing full context.

```python
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .per_layer()
     .uq(method="bootstrap", n_samples=100)
     .execute(network)
)

print(result)
# Outputs:
# QueryResult(
#   target='nodes'
#   count=42
#   attributes=['degree', 'betweenness_centrality']
#   computed=['degree', 'betweenness_centrality']
#   grouping='per_layer' (3 groups)
#   uncertainty='bootstrap'
#   provenance='replayable'
#   replayable=True
# )
```

**What to inspect**:
- `target`: 'nodes', 'edges', or 'communities'
- `count`: Number of items returned
- `attributes`: Available computed attributes
- `computed`: Explicitly computed metrics
- `grouping`: If grouped, shows type and count
- `uncertainty`: UQ method if enabled
- `provenance`: Provenance mode
- `replayable`: Whether query can be replayed

**LLM agent guidance**: ALWAYS inspect QueryResult before calling `.to_pandas()`:
```python
# [CORRECT] Good: Inspect first
print(result)
print(f"Got {result.count} {result.target}")
if result.meta.get("has_uncertainty"):
    df = result.to_pandas(expand_uncertainty=True)
else:
    df = result.to_pandas()

# [ERROR] Bad: Immediate conversion without inspection
df = result.to_pandas()  # May miss important context
```

### Pedagogical Error Messages

**What it does**: DSL errors now include:
1. What the user likely intended
2. Why the operation failed
3. 1-2 corrected query examples
4. Common pitfall notes

**Example**:
```python
try:
    Q.nodes().execute(net).where(degree__gt=3)  # Execute too early
except DslSyntaxError as e:
    print(e)
# Outputs:
# DslSyntaxError: Cannot call .where() on QueryResult
#
# [INTENT] You probably wanted to: Filter before executing
#
# [ERROR] Why this failed: .execute() returns a QueryResult object,
#    which is immutable. Query building methods like .where()
#    must be called before .execute().
#
# [CORRECT] Corrected examples:
#   1. Q.nodes().where(degree__gt=3).execute(net)
#   2. result = Q.nodes().execute(net); df = result.to_pandas().query("degree > 3")
```

**LLM agent guidance**: When you encounter a DSL error:
1. Read the ENTIRE error message (don't stop at first line)
2. Apply the suggested fix from "Corrected examples"
3. Learn the pitfall to avoid repeating the mistake
4. If examples don't work, consult documentation sections mentioned in error

### Performance and Semantic Warnings

**What it does**: Non-blocking warnings for expensive operations and multilayer semantic issues.

**Performance warnings**:
```python
# Expensive centrality on large graphs
result = Q.nodes().compute("betweenness_centrality").execute(net)
# [WARNING]  Performance Warning: EXPENSIVE operation
#    Computing 'betweenness_centrality' on ~10,000 node replicas
#    Estimated time: seconds to minutes
#
# [TIP] Faster alternatives:
#   1. Compute per-layer: .per_layer().compute('betweenness_centrality')
#   2. Filter to specific layers: .from_layers(L['social']).compute(...)
#   3. Sample nodes: .where(...).compute(...)

# High UQ samples
result = Q.nodes().compute("degree").uq(n_samples=1000).execute(net)
# [WARNING]  Performance Warning: HIGH UQ cost
#    Computing 'degree' with n_samples=1000 on 5000 nodes
#    Computational cost: ~5,000,000 evaluations
```

**Multilayer semantic warnings**:
```python
# Node replica confusion
result = Q.nodes().execute(multilayer_net)
# [WARNING]  Multilayer Semantic Warning: Node replica vs physical node
#    Q.nodes() returns node REPLICAS (node + layer pairs)
#    Physical node 'Alice' appears as ('Alice', 'social'), ('Alice', 'work'), etc.

# Degree ambiguity
result = Q.nodes().compute("degree").execute(multilayer_net)
# [WARNING]  Multilayer Semantic Warning: Degree ambiguity
#    'degree' can mean: intra-layer, inter-layer, or aggregate
#    By default, py3plex computes AGGREGATE degree

# Global community detection
result = Q.nodes().community(method="leiden").execute(multilayer_net)
# [WARNING]  Multilayer Semantic Warning: Global community detection
#    Running 'leiden' on 5-layer network globally
#    Communities will span multiple layers simultaneously
```

**Suppressing warnings**:
```python
from py3plex.dsl.warnings import suppress_warnings

# Suppress specific warning types
with suppress_warnings("expensive_centrality"):
    result = Q.nodes().compute("betweenness_centrality").execute(net)

# Suppress multiple types
with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
    result = Q.nodes().compute("degree").execute(net)
```

**LLM agent guidance**:
- **Development mode**: Let warnings guide you to better query patterns
- **Production mode**: Suppress warnings only when semantics are clearly understood
- **React to warnings**: Warnings are actionable — apply suggested alternatives when applicable
- **Don't ignore**: Warnings indicate potential correctness or performance issues

**Validation status**:
- Warning suppression behavior (`suppress_warnings`) is tested in `tests/test_agents_ergonomics_features.py`
- Warning triggering thresholds and exact warning text are implementation details and may vary across releases

### Multilayer Semantics Mental Model

**Core concepts LLM agents must understand**:

**1. Node Replicas vs Physical Nodes**:
- Physical node: A unique entity (e.g., "Alice")
- Node replica: (physical_node, layer) pair (e.g., ("Alice", "social"))
- Most operations return **replicas**, not physical nodes
- To get physical nodes: `set(n[0] for n in result.items)`

**2. Degree Meanings**:
- Intra-layer degree: Edges within same layer
- Inter-layer degree: Edges to other layers
- Aggregate degree: Total (intra + inter) — **default in py3plex**

**3. Coverage Semantics**:
- `mode="all"`: Intersection (strict — keeps items in ALL groups)
- `mode="any"`: Union (permissive — keeps items in ANY group)
- `mode="at_least", k=N`: Items in at least N groups
- `mode="fraction", p=0.X`: Items in at least X% of groups

**4. Global vs Per-Layer**:
- **Global operations**: Treat network as unified structure
- **Per-layer operations**: Independent analysis per layer
- Use `.per_layer()` when layer structure matters

**LLM agent decision rules**:

```python
# IF: User asks about "nodes" in multilayer network
# THEN: Clarify if they mean replicas or physical nodes
# Default to replicas (standard py3plex semantics)

# IF: User asks to compute "degree"
# THEN: Clarify if they mean intra-layer, aggregate, or per-layer
# Default to aggregate, but warn if ambiguous

# IF: User asks for "top-k hubs"
# THEN: Ask if they want:
#   - Top-k globally (aggregate metrics)
#   - Top-k per layer (.per_layer().top_k())
#   - Top-k across layers (.per_layer().top_k().coverage())

# IF: Network has >1 layer and user doesn't specify layer scope
# THEN: Issue semantic warning or ask for clarification
```

### Guided Quickstart Recipes

**Purpose**: Task-oriented minimal recipes demonstrating best practices.

**Recipe 1: Find Hubs Across Layers**
```python
result = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree", "betweenness_centrality")
     .per_layer()
       .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="at_least", k=2)  # In ≥2 layers
     .order_by("-degree")
     .execute(net)
)
```

**Recipe 2: Community Detection with UQ**
```python
result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
     .uq(method="ensemble", n_samples=50, seed=42)
     .execute(net)
)
```

**Recipe 3: Reproducible Results**
```python
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .uq(method="bootstrap", n_samples=100, seed=42)
     .provenance(mode="replayable", capture="snapshot")
     .execute(net)
)
result.export_bundle("analysis.bundle.json.gz", compress=True)
```

**LLM agent guidance**: When user asks "how do I...", search these recipes first and then validate in the current environment.

---

## Quick Start: Golden Paths

**Validation status**:
- Path 1 and Path 2 are exercised in `tests/test_agents_golden_paths.py`
- Path 3, Path 4, and Path 5 are advanced workflows and may require optional modules or setup in the current environment

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

**See Also**:
- **RST Documentation**: `docfiles/user_guide/dsl.rst` - Quick start guide, cheat sheet, and basic examples
- **Examples**: `examples/network_analysis/example_dsl_builder_api.py` - Comprehensive working examples
- **Legacy DSL**: See [Legacy DSL (String-Based)](#legacy-dsl-string-based) section below

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
4. **Execution**: Executed via `.execute(network, **params)` -> returns `QueryResult`

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
- `ParamRef` -> `{"__type__": "ParamRef", "name": "...", "type_hint": "..."}`
- `LayerSet` -> `{"__type__": "LayerSet", "expr": "..."}`

#### 2.3 Query Result (`QueryResult`)

**Location**: `py3plex.dsl.result.QueryResult`

**Attributes**:
- `target`: `str` - "nodes" or "edges"
- `items`: `List[Any]` - List of node/edge identifiers
- `attributes`: `Dict[str, Union[List[Any], Dict[Any, Any]]]` - Computed attributes (column -> values)
- `meta`: `Dict[str, Any]` - Execution metadata (provenance, grouping, etc.)
- `computed_metrics`: `Set[str]` - Set of metrics computed during execution
- `sensitivity_result`: `Optional[SensitivityResult]` - Sensitivity analysis results if requested

**Export Methods**:
- `to_pandas(expand_uncertainty=False, expand_explanations=False)` -> `pd.DataFrame`
- `to_networkx()` -> `nx.Graph` or `nx.MultiGraph`
- `to_arrow()` -> `pa.Table`
- `to_json()` -> `str` (JSON string)
- `to_csv(path, **kwargs)` -> `None` (writes to file)

**Provenance Methods**:
- `provenance` -> `Optional[Dict[str, Any]]` - Get provenance dictionary
- `is_replayable` -> `bool` - Check if result has replayable provenance
- `replay(strict=True)` -> `QueryResult` - Replay query from provenance

**Grouping Methods**:
- `group_summary()` -> `pd.DataFrame` - Summary of groups (when grouping is active)

**Immutability**: QueryResult objects are IMMUTABLE after construction. All export methods MUST NOT modify the result.

#### 2.4 Layer Set (`LayerSet`)

**Location**: `py3plex.dsl.layers.LayerSet`

**Purpose**: First-class abstraction for layer selection with set-theoretic operations.

**Lifecycle**:
1. **Construction**: Created via `LayerSet("name")` or `LayerSet.parse("expr")`
2. **Composition**: Combined via operators (`|`, `&`, `-`, `~`)
3. **Resolution**: Resolved to concrete layer names via `.resolve(network)` -> `Set[str]`

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

##### `Q.nodes(autocompute=True) -> QueryBuilder`

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

##### `Q.edges(autocompute=True) -> QueryBuilder`

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

##### `Q.communities(partition="default", autocompute=True) -> CommunityQueryBuilder`

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

##### `.from_layers(layer_expr) -> QueryBuilder`

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

##### `.where(*exprs, **conditions) -> QueryBuilder`

Add filtering conditions.

**Parameters**:
- `*exprs` (BooleanExpression): Boolean expressions from `F` (e.g., `F.degree > 5`)
- `**conditions` (keyword arguments): Condition specifications using suffixes

**Condition Syntax**:

1. **Equality**: `attr=value` -> `attr = value`
2. **Comparison**: `attr__gt=value` -> `attr > value`
   - Suffixes: `__gt` (>), `__gte` (>=), `__lt` (<), `__lte` (<=), `__eq` (=), `__ne` (!=)
3. **Special Predicates**:
   - `intralayer=True` -> Edges within same layer
   - `interlayer=("layer1", "layer2")` -> Edges between specific layers
4. **Temporal**: `t__between=(t_start, t_end)` -> Time range filter
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
- If `autocompute=False` and filtering on uncomputed metric -> `DslMissingMetricError`
- If attribute does not exist -> `UnknownAttributeError` with suggestions

##### `.compute(*measures, alias=None, aliases=None, uncertainty=None, approx=None, approx_method=None, approx_diagnostics=False, **kwargs) -> QueryBuilder`

Compute metrics on nodes/edges with optional approximation for large networks.

**Parameters**:
- `*measures` (str): Metric names to compute (e.g., "degree", "betweenness_centrality")
- `alias` (str, optional): Alias for single measure
- `aliases` (Dict[str, str], optional): Dictionary mapping measures to aliases
- `uncertainty` (bool, optional): Enable UQ for these metrics (default: inherits from query-level or global)
- `approx` (bool, optional): Enable fast approximation (default: False)
- `approx_method` (str, optional): Approximation method (auto-inferred if not specified)
- `approx_diagnostics` (bool, optional): Enable per-node diagnostics (default: False)
- `**kwargs`: UQ parameters OR approximation parameters depending on context

**UQ Parameters** (when `uncertainty=True`):
- `method` (str): "bootstrap", "perturbation", "seed", "null_model", "stratified_perturbation"
- `n_samples` (int): Number of samples (default: from uq_config or 50)
- `ci` (float): Confidence interval level (default: 0.95)
- `bootstrap_unit` (str): "edges", "nodes", or "layers"
- `bootstrap_mode` (str): "resample" or "permute"
- `n_null` (int): Number of null model replicates
- `null_model` (str): "degree_preserving", "erdos_renyi", "configuration"
- `random_state` (int): Random seed

**Approximation Parameters** (when `approx=True`):
- `n_samples` (int): Number of samples for sampling-based methods (betweenness)
- `n_landmarks` (int): Number of landmarks for landmark-based methods (closeness)
- `tol` (float): Convergence tolerance for iterative methods (pagerank)
- `max_iter` (int): Maximum iterations for iterative methods (pagerank)
- `seed` (int): Random seed for determinism

**Default Approximation Methods**:
- `betweenness_centrality` → `"sampling"` (sampling-based Brandes algorithm)
- `closeness_centrality` → `"landmarks"` (landmark-based distance sampling)
- `pagerank` → `"power_iteration"` (power iteration with convergence tracking)

**Semantics**:
- MUST compute specified metrics for all items in the current result set
- MUST store results in `attributes` dictionary of QueryResult
- MAY compute metrics lazily (deferred until needed by `.where()`, `.order_by()`, etc.)
- MUST use measure_registry to look up metric implementations
- When `approx=True`, MUST set `fast_path=True` in provenance

**Metric Types**:
1. **Centrality**: degree, betweenness_centrality, closeness_centrality, eigenvector_centrality, pagerank
2. **Clustering**: clustering, triangles
3. **Community**: community_id, community_size (requires partition)
4. **Custom**: User-defined via `@dsl_operator`

**UQ Behavior**:
- If `uncertainty=True`, results MUST be dictionaries with keys: `mean`, `std`, `quantiles`, `certainty`
- If `uncertainty=False` or `None` (and not enabled globally), results MUST be scalars
- Quantiles MUST include at minimum: 0.025, 0.05, 0.5, 0.95, 0.975 for ci=0.95

**Approximation Behavior**:
- If `approx=True`, MUST use approximate algorithm from registry
- MUST record approximation metadata in `result.meta["approximation"]`
- MUST set `result.meta["provenance"]["backend"]["fast_path"] = True`
- Approximation is deterministic when `seed` is specified

**Example**:
```python
# Exact computation
.compute("degree", "betweenness_centrality")

# With alias
.compute("degree", alias="deg")

# With UQ
.compute("degree", uncertainty=True, method="bootstrap", n_samples=100)

# With approximation (NEW in v1.1)
.compute("betweenness_centrality", approx=True, n_samples=512, seed=42)
.compute("closeness_centrality", approx=True, n_landmarks=64, seed=42)
.compute("pagerank", approx=True, tol=1e-6, max_iter=100)

# UQ + approximation (composition)
.compute("betweenness_centrality", approx=True, uncertainty=True, n_samples=100, seed=42)
```

##### `.order_by(key, desc=False) -> QueryBuilder`

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

##### `.limit(n) -> QueryBuilder`

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

##### `.top_k(k, key) -> QueryBuilder`

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

##### `.per_layer() -> QueryBuilder`

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

##### `.per_layer_pair() -> QueryBuilder`

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

##### `.end_grouping() -> QueryBuilder`

Explicitly end grouping context.

**Semantics**:
- MUST flatten grouped results back to single collection
- MUST be called before `.coverage()` to enable cross-group filtering
- If not called explicitly, MUST be applied implicitly at execution time

**Example**:
```python
.per_layer().top_k(10, "degree").end_grouping().coverage(mode="all")
```

##### `.coverage(mode="all", k=None) -> QueryBuilder`

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

##### `.aggregate(**aggregations) -> QueryBuilder`

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

##### `.uq(method="perturbation", n_samples=50, ci=0.95, seed=None, **kwargs) -> QueryBuilder`

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

##### `.at(time) -> QueryBuilder`

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

##### `.during(t_start, t_end) -> QueryBuilder`

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

##### `.window(size, step=None, start=None, end=None, aggregation="list") -> QueryBuilder`

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

##### `.community(method="leiden", gamma=1.0, omega=1.0, random_state=None, partition_name="default", **kwargs) -> QueryBuilder`

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

##### `.sensitivity(perturb, grid=None, n_samples=30, metrics=None, **kwargs) -> QueryBuilder`

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

##### `.explain(neighbors_top=None, include=None, **config) -> QueryBuilder or ExplainQuery`

Attach explanations to results OR get execution plan.

**Two Modes**:

1. **Execution Plan Mode** (no arguments): Returns `ExplainQuery` showing execution plan
2. **Explanations Mode** (with arguments): Attaches explanations to each result row

**Parameters** (Explanations Mode):
- `neighbors_top` (int, default=10): Max neighbors to include
- `include` (List[str], optional): Explanation blocks (default: ["community", "top_neighbors", "layer_footprint"])
- `exclude` (List[str], optional): Blocks to exclude
- `neighbors` (dict, optional): Neighbor config (metric, scope, direction)
- `attribution` (dict, optional): Attribution configuration (see Attribution Block below)
- `cache` (bool, default=True): Cache lookups
- `as_columns` (bool, default=True): Store as top-level columns
- `prefix` (str, default=""): Column name prefix

**Explanation Blocks**:
- `"community"` - Community membership and size
- `"top_neighbors"` - Top neighbors by weight/degree
- `"layer_footprint"` - Layers where node/edge appears
- `"attribution"` - Shapley-based attribution explanations (see below)

**Example**:
```python
.explain()  # Execution plan
.explain(neighbors_top=5, include=["top_neighbors"])  # With explanations
.explain(include=["attribution"], attribution={"metric": "degree", "seed": 42})  # With attribution
```

##### Attribution Block

The `"attribution"` explanation block provides Shapley-based explanations for metric values or rankings using game-theoretic attribution methods.

**Purpose**: Answers "Why is this node/edge ranked highly?" by decomposing contributions across layers and/or edges.

**Configuration** (via `attribution` parameter dict):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | str \| None | Auto-infer | Which computed metric to explain. Required if multiple metrics computed. |
| `objective` | "value" \| "rank" | "value" | Explain metric value or ranking position. |
| `levels` | List["layer", "edge"] | ["layer"] | Attribution levels to compute. |
| `method` | "shapley" \| "shapley_mc" \| "influence" | "shapley_mc" | Computation method. |
| `feature_space` | "layers" \| "layer_pairs" \| "coupling_types" | "layers" | Layer feature representation. |
| `n_permutations` | int | 128 | MC Shapley sample count (≥16). |
| `max_exact_features` | int | 8 | Switch from exact to MC at this threshold. |
| `seed` | int \| None | None | Random seed for determinism (recommended). |
| `edge_scope` | "incident" \| "ego_k_hop" \| "shortest_path_sample" \| "global_top_m" | "incident" | Edge candidate selection strategy. |
| `k_hop` | int | 2 | Ego network radius (for ego_k_hop). |
| `max_edges` | int | 40 | Maximum candidate edges. |
| `top_k_layers` | int | 10 | Top layer contributions to return. |
| `top_k_edges` | int | 20 | Top edge contributions to return. |
| `include_negative` | bool | True | Include negative contributions. |
| `cache` | bool | True | Cache subset computations. |
| `uq` | "off" \| "propagate" \| "summarize_only" | "off" | UQ integration mode. |
| `ci_level` | float | 0.95 | Confidence interval level for UQ. |

**Output Structure** (JSON-serializable dict):
```python
{
    "metric": "pagerank",
    "objective": "value",
    "utility_def": None,  # or "margin_to_cutoff(k=10)" for rank
    "levels": ["layer", "edge"],
    "method": "shapley_mc",
    "seed": 42,
    "n_permutations": 128,
    "feature_space": "layers",
    "full_value": 0.1186,
    "baseline_value": 0.0500,
    "delta": 0.0686,
    "residual": 1e-12,
    "layer_contrib": [
        {"layer": "social", "phi": 0.0401},
        {"layer": "work", "phi": 0.0285}
    ],
    "edge_contrib": [
        {"edge": ["Alice", "Bob", "social", "social"], "phi": 0.0102},
        # ...
    ],
    "warnings": [],
    "cache_hit_rate": 0.73
}
```

**Examples**:

```python
# Layer attribution for PageRank
result = (
    Q.nodes()
     .compute("pagerank")
     .explain(
         include=["attribution"],
         attribution={
             "metric": "pagerank",
             "levels": ["layer"],
             "method": "shapley",
             "seed": 42
         }
     )
     .execute(net)
)

# Edge attribution for betweenness with rank objective
result = (
    Q.nodes()
     .compute("betweenness_centrality")
     .order_by("-betweenness_centrality")
     .limit(10)
     .explain(
         include=["attribution"],
         attribution={
             "objective": "rank",
             "levels": ["edge"],
             "edge_scope": "ego_k_hop",
             "k_hop": 2,
             "max_edges": 40,
             "n_permutations": 128,
             "seed": 42
         }
     )
     .execute(net)
)

# With UQ propagation
result = (
    Q.nodes()
     .uq(method="perturbation", n_samples=30, seed=42)
     .compute("pagerank")
     .explain(
         include=["attribution"],
         attribution={
             "metric": "pagerank",
             "uq": "propagate",
             "levels": ["layer"],
             "seed": 42
         }
     )
     .execute(net)
)
```

**Determinism**:
- Setting `seed` ensures reproducible attribution results
- Same seed produces identical Shapley values across runs
- Different seeds produce statistically different but valid attributions
- Results are independent of parallel execution settings (n_jobs)

**Performance Considerations**:
- **Exact Shapley**: Only feasible for ≤ `max_exact_features` layers (default 8)
- **Monte Carlo Shapley**: Scales to larger feature sets via sampling
- **Edge Attribution**: Bounded by `max_edges` to prevent exponential blowup
- **Caching**: Enabled by default to reuse subset computations

**UQ Integration**:
- `uq="off"`: No UQ (default), deterministic scalar Shapley values
- `uq="propagate"`: Compute attribution per UQ replicate, aggregate mean/std/CI
- `uq="summarize_only"`: Compute once on base network, wrap in UQ-like structure

**Caveats**:
- Requires at least one computed metric
- If multiple metrics computed, must specify `metric` parameter
- Edge attribution is more expensive than layer attribution
- Always set `seed` for reproducible research

**Export Compatibility**:
Attribution data is serialized to JSON strings when using:
```python
df = result.to_pandas(expand_explanations=True)
# df["attribution"] contains JSON-serialized attribution dicts
```

##### `.to_ast() -> Query`

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

##### `.execute(network, progress=True, **params) -> QueryResult`

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
- `L["name"]` -> LayerExprBuilder or LayerSet (single layer)
- `L["name1", "name2"]` -> LayerExprBuilder (union)
- `L["* - coupling"]` -> LayerSet (parsed expression)

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
- `Param.int(name)` -> ParamRef with type hint "int"
- `Param.float(name)` -> ParamRef with type hint "float"
- `Param.str(name)` -> ParamRef with type hint "str"

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
- `UQ.fast(seed=None)` -> UQConfig with n_samples=20
- `UQ.standard(seed=None)` -> UQConfig with n_samples=100
- `UQ.publication(seed=None)` -> UQConfig with n_samples=500
- `UQ.off()` -> None (disable UQ)

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
- `F.attr` -> FieldExpression for attribute
- `F.attr > value` -> BooleanExpression (comparison)
- `(F.attr > 5) & (F.layer == "social")` -> Complex BooleanExpression

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
- `C.compare(net1_name, net2_name)` -> CompareBuilder

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
- `N.configuration()` -> NullModelBuilder (configuration model)
- `N.erdos_renyi()` -> NullModelBuilder (Erdős-Rényi model)
- `N.degree_preserving()` -> NullModelBuilder (degree-preserving rewiring)

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
- `P.shortest(source, target)` -> PathBuilder (shortest paths)
- `P.random_walk(start, steps)` -> PathBuilder (random walks)

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
- `D.simulate(model)` -> DynamicsBuilder

**Semantics**:
- MUST simulate network dynamics (SIR, SIS, etc.)
- MUST support `.steps(n)` for number of timesteps

**Example**:
```python
from py3plex.dynamics import SIRModel
D.simulate(SIRModel(beta=0.3, gamma=0.1)).steps(100).execute(net)
```

---

#### 3.11 M — Meta-Analysis Builder Factory

**Import**: `from py3plex.dsl import M`

**Factory Methods**:
- `M.meta(name: Optional[str] = None)` -> MetaBuilder

**Purpose**: Perform meta-analytic pooling of network statistics across multiple networks with support for fixed-effect and random-effects models (DerSimonian–Laird baseline).

**Execution Contract (NON-NEGOTIABLE)**:
- `.on_networks(...)` MUST be called exactly once
- `.run(...)` MUST be called exactly once
- `.execute()` without both MUST raise `MetaAnalysisError`
- Re-calling `.on_networks()` or `.run()` overwrites previous values but MUST emit a provenance warning
- Default model is `random` unless `.model("fixed")` is specified

**Chainable Methods**:
- `.on_networks(networks)` - Set networks (dict, list, or generator)
- `.with_network_meta(meta_dict)` - Add network-level metadata
- `.run(query, effect, se=None, group_by=None)` - Execute query and extract effects
- `.model(type)` - Set model type: "fixed" or "random" (default: "random")
- `.subgroup(by)` - Enable subgroup meta-analysis
- `.meta_regress(formula)` - Enable meta-regression (v1 constrained)
- `.allow_unweighted(bool)` - Allow unweighted pooling if SE unavailable
- `.seed(int)` - Set seed for missing query seeds (respects explicit query seeds)
- `.ci_level(float)` - Set confidence interval level (default: 0.95)
- `.preserve_order(bool)` - Preserve dict insertion order (default: False, sorts by key)
- `.execute()` - Execute meta-analysis and return MetaResult

**Statistical Models**:

**Fixed-Effect (Inverse Variance)**:
```
w_i = 1 / se_i²
pooled_effect = Σ(w_i * y_i) / Σ(w_i)
pooled_se = sqrt(1 / Σ(w_i))
```

**Random-Effects (DerSimonian–Laird)**:
```
Q = Σ(w_i * (y_i − pooled_fixed)²)
τ² = max(0, (Q − df) / C)  where C = Σ(w_i) − Σ(w_i²) / Σ(w_i)
w_i* = 1 / (se_i² + τ²)
pooled_effect = Σ(w_i* * y_i) / Σ(w_i*)
```

**Heterogeneity Metrics**:
- **Q**: Cochran's Q statistic (test for heterogeneity)
- **τ²**: Between-study variance (tau-squared)
- **I²**: Percentage of total variation due to heterogeneity: `max(0, (Q − df) / Q) × 100%`
- **H**: Ratio of Q to its degrees of freedom: `sqrt(Q / df)`

**SE Resolution Priority** (STRICT ORDER):
1. Explicit `se="column_name"` if column exists
2. Expression `se="se(effect_col)"` if variance available
3. Auto-infer from `.uq()` if `provenance.randomness.n_samples` is not None
4. Error unless `.allow_unweighted(True)` is set (uses sample SD)

**Example 1: Network-Level Meta-Analysis**:
```python
from py3plex.dsl import Q, M

# Compute average degree across multiple networks
meta = (
    M.meta("avg_degree_meta")
     .on_networks({"net1": net1, "net2": net2, "net3": net3})
     .run(
         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
         effect="avg_degree",
     )
     .model("random")
     .execute()
)

# Access results
df = meta.to_pandas()  # Pooled effects table
network_df = meta.network_table()  # Per-network effects
print(f"Pooled effect: {df['pooled_effect'].iloc[0]:.3f} ± {df['pooled_se'].iloc[0]:.3f}")
print(f"I²: {df['I2'].iloc[0]:.1f}%")
```

**Example 2: Node-Level Effects (Shared Node IDs)**:
```python
from py3plex.dsl import Q, M, UQ

# Pool PageRank across treatment conditions (shared gene IDs)
meta = (
    M.meta("pagerank_gene_meta")
     .on_networks({"ctrl": netA, "trt1": netB, "trt2": netC})
     .run(
         Q.nodes()
          .node_type("gene")
          .uq(UQ.standard(seed=42))
          .compute("pagerank")
          .select("node", "pagerank", "pagerank_std"),
         effect="pagerank",
         se="pagerank_std",
         group_by=["node"],
     )
     .model("fixed")
     .execute()
)

# Results: one pooled effect per gene across networks
```

**Example 3: Subgroup Meta-Analysis**:
```python
# Subgroup analysis by treatment condition
meta = (
    M.meta()
     .on_networks({"a": net1, "b": net2, "c": net3})
     .with_network_meta({
         "a": {"condition": "ctrl"},
         "b": {"condition": "trt"},
         "c": {"condition": "trt"},
     })
     .run(
         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
         effect="avg_degree",
     )
     .subgroup(by="condition")
     .model("random")
     .execute()
)

# Results include both per-subgroup and overall pooled effects
```

**Example 4: Meta-Regression (v1 Constrained)**:
```python
# Network-level effects with covariates
meta = (
    M.meta()
     .on_networks(nets)
     .with_network_meta(meta_tbl)  # Must include covariates
     .run(
         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
         effect="avg_degree",
     )
     .meta_regress(formula="avg_degree ~ node_count + edge_count")
     .model("random")
     .execute()
)

# Regression coefficients in meta.meta_provenance["meta_regression"]
```

**MetaResult Object**:
```python
result = meta.execute()

# Access pooled effects
result.to_pandas()  # Tidy DataFrame with pooled results

# Access per-network effects
result.network_table()  # DataFrame with network-level effects and weights

# Access provenance
result.meta_provenance  # Complete aggregated provenance dict

# Serialize to JSON
result.to_dict()  # JSON-serializable dictionary
```

**Provenance Aggregation**:

Meta-analysis aggregates provenance from all networks:
```python
{
    "engine": "dsl_v2_meta",
    "py3plex_version": "...",
    "timestamp_utc": "...",
    "networks": [
        {
            "name": "net1",
            "network_fingerprint": {"node_count": ..., "edge_count": ..., "layers": ...},
            "query_ast_hash": "...",
            "randomness": {...},
            "performance": {...},
            "warnings": [...]
        },
        # ... per network
    ],
    "meta_model": {
        "type": "fixed|random",
        "tau2_estimator": "DL",
        "k": 3,
        "unweighted": false  # Only present if unweighted pooling used
    }
}
```

**Determinism Guarantees**:
- Same networks + same query + same seeds → identical results
- Network order is stable (sorted by key unless `.preserve_order(True)`)
- All provenance is JSON-serializable
- Explicit query seeds are always honored
- Meta-level `.seed()` fills missing seeds only

**Error Handling**:
- `MetaAnalysisError` for all meta-analysis-specific errors
- Actionable hints included in all error messages
- Examples:
  - Missing effect column
  - Missing SE without `.allow_unweighted(True)`
  - `group_by` mismatch across networks
  - Missing network metadata for subgroup/regression

**Edge Cases**:
- **k=1 (single network)**: Pooled effect = y₁, SE = se₁, τ² = NaN, Q = NaN, I² = NaN
- **All effects equal**: τ² = 0, I² = 0 (no heterogeneity)
- **C ≤ 0 in DL estimation**: τ² = 0 with provenance warning
- **Empty group_by groups**: Returned with `k_warning=True`

**Limitations (v1)**:
- Meta-regression: Numeric covariates only, no interactions
- Tau² estimator: Only "DL" supported (REML, SJ raise `NotImplementedError`)
- Categorical predictors: Must be pre-encoded

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
1. `LAYER("a") + LAYER("b") - LAYER("c")` -> `((a + b) - c)`

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
L["a"] + L["b"] - L["c"]  ->  ((L["a"] + L["b"]) - L["c"])
```

Use parentheses for different grouping:
```
LayerSet.parse("a + (b - c)")  ->  (a + (b - c))
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
No Grouping -> [.per_layer()] -> Active Grouping
Active Grouping -> [.end_grouping()] -> Ended Grouping
Ended Grouping -> [.coverage()] -> No Grouping
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

When calling `to_pandas(expand_uncertainty=True)`:
- Each UQ column MUST expand to multiple columns:
  - `{col}`: Point estimate (mean)
  - `{col}_std`: Standard deviation
  - `{col}_ci{pct}_low`: Lower CI bound (e.g., `degree_ci95_low`)
  - `{col}_ci{pct}_high`: Upper CI bound
  - `{col}_ci{pct}_width`: CI width

#### 10.5 UQ Algebraic Laws (Formal Specification)

**Status**: Implemented in `py3plex.dsl.uq_algebra` (v1.1.3+)

All UQ operations in py3plex are governed by formal algebraic laws that ensure mathematical correctness, composability, and reproducibility. UQ outputs are treated as first-class algebraic objects, and all operations combining, transforming, or aggregating UQ results MUST obey explicit laws. Any violation raises a hard error (fail-fast policy).

##### 10.5.1 UQValue Object Model

All UQ results are represented as `UQValue` objects with the following structure:

```python
from py3plex.dsl.uq_algebra import UQValue, DistributionType, ProvenanceInfo

# Create a UQValue
value = UQValue(
    distribution_type=DistributionType.GAUSSIAN,  # EMPIRICAL, GAUSSIAN, or DEGENERATE
    mean=10.0,                    # Point estimate
    std=2.0,                      # Standard deviation
    quantiles={0.025: 6.08, 0.975: 13.92},  # Quantile dictionary
    samples=None,                 # Optional: raw samples (for EMPIRICAL)
    support={"layer": "social"},  # Optional: support domain (grouping context)
    provenance=ProvenanceInfo(    # Provenance information
        method="bootstrap",
        n_samples=100,
        seed=42,
        bootstrap_unit="edges",
        bootstrap_mode="resample"
    ),
    effective_count=1.0,          # Number of original observations represented
)
```

**Distribution Types**:
- `EMPIRICAL`: Distribution from bootstrap/resampling samples (has raw samples)
- `GAUSSIAN`: Parametric Gaussian approximation (mean + std)
- `DEGENERATE`: Single-value distribution (std=0, deterministic)

**Provenance Fields**:
- `method`: UQ method used (bootstrap, perturbation, seed, null_model, etc.)
- `n_samples`: Number of samples/replicates
- `seed`: Random seed used (None if not applicable)
- `null_model`: Null model type (if method is null_model)
- `bootstrap_unit`: Bootstrap unit (if method is bootstrap)
- `bootstrap_mode`: Bootstrap mode (if method is bootstrap)
- `extra`: Additional method-specific parameters

**Serialization**:
```python
# Convert to canonical UQ format
data = value.to_dict()
# {
#     "mean": 10.0,
#     "value": 10.0,  # Alias for compatibility
#     "std": 2.0,
#     "quantiles": {0.025: 6.08, 0.975: 13.92},
#     "ci_low": 6.08,
#     "ci_high": 13.92,
#     "certainty": 0.8,
#     "method": "bootstrap",
#     "n_samples": 100,
#     "seed": 42,
#     ...
# }

# Reconstruct from dict
reconstructed = UQValue.from_dict(data)
```

##### 10.5.2 Algebraic Laws (Complete List)

All UQ aggregation operations MUST respect the following laws:

**[IDENTITY]**
- **Law**: Aggregating a single UQValue MUST return the same UQValue
- **Enforced**: [CORRECT] `UQAlgebra.aggregate_mean([value])` returns `value`
- **Violation**: Raises `UQIdentityViolation`
- **Special case**: Zero-weight aggregation is forbidden (raises error)

**[IDEMPOTENCE]**
- **Law**: Aggregating identical UQValues with identical provenance MUST NOT change distribution
- **Enforced**: [CORRECT] Structural hash used to detect identical values; std preserved
- **Violation**: Raises `UQIdempotenceViolation`
- **Implementation**: If all values have same structural hash, preserve original std

**[ASSOCIATIVITY]**
- **Law**: `(A ⊕ B) ⊕ C == A ⊕ (B ⊕ C)` for mean (std may vary slightly due to variance propagation)
- **Enforced**: [CORRECT] Uses `effective_count` weighting to ensure mean associativity
- **Violation**: Raises `UQAssociativityViolation` if mean differs beyond tolerance
- **Tolerance**: 1e-6 for mean, 1e-5 for std
- **Note**: Std may differ by aggregation path due to variance propagation formula

**[COMMUTATIVITY]**
- **Law**: `A ⊕ B == B ⊕ A` (order-independent aggregation)
- **Enforced**: [CORRECT] Aggregation uses symmetric weighting by effective counts
- **Violation**: Raises `UQCommutativityViolation`
- **Tolerance**: 1e-9

**[MONOTONICITY]**
- **Law**: Increasing sample count MUST NOT increase uncertainty (variance inflation forbidden)
- **Enforced**: [CORRECT] Post-aggregation check validates result std ≤ max(input stds) * tolerance
- **Violation**: Raises `UQMonotonicityViolation`
- **Rationale**: More evidence should not reduce confidence

**[DISTRIBUTION CLOSURE]**
- **Law**: Operation between two UQValues MUST result in a valid UQValue
- **Enforced**: [CORRECT] All aggregation operations return `UQValue` instances
- **Violation**: Raises `UQClosureViolation`
- **Mixed types**: EMPIRICAL + GAUSSIAN -> EMPIRICAL; GAUSSIAN + DEGENERATE -> GAUSSIAN

**[DEGENERACY CONSISTENCY]**
- **Law**: Degenerate distributions (std=0) act as neutral elements
- **Enforced**: [CORRECT] DEGENERATE + DEGENERATE -> DEGENERATE; DEGENERATE + non-DEGENERATE preserves uncertainty
- **Violation**: Raises `UQDegeneracyViolation`
- **Special case**: Deterministic values (method="deterministic") can mix with any provenance

**[GROUPING INVARIANCE]**
- **Law**: Algebraic laws MUST hold within and across grouping contexts
- **Enforced**: [CORRECT] per_layer aggregation equivalent to explicit layer-wise aggregation
- **Violation**: Raises `UQGroupingViolation`
- **Implementation**: Support field tracks grouping context; operations check compatibility

**[NULL-MODEL DOMINANCE]**
- **Law**: Aggregation involving null-model UQ MUST reflect increased uncertainty
- **Enforced**: [CORRECT] Null-model variance propagates correctly
- **Violation**: Raises `UQDominanceViolation`
- **Rationale**: Null-model UQ represents baseline uncertainty that cannot be reduced

**[SEED DETERMINISM]**
- **Law**: Same operands + same seeds -> identical result
- **Enforced**: [CORRECT] Seed recorded in provenance; aggregation with same seeds produces identical output
- **Violation**: Raises `UQDeterminismViolation`
- **Note**: Aggregation of multiple values invalidates single seed (provenance.seed becomes None)

##### 10.5.3 Forbidden Operations

The following operations are **FORBIDDEN** and will raise typed errors:

1. **Aggregating UQValues with incompatible support domains**
   - Error: `UQIncompatibleSupport`
   - Example: Mixing `support={"layer": "social"}` and `support={"layer": "work"}`
   - Fix: Ensure all values have compatible or None support

2. **Mixing incompatible provenance without reconciliation**
   - Error: `UQIncompatibleProvenance`
   - Example: Mixing `method="bootstrap"` with `method="null_model"` (unless one is deterministic)
   - Fix: Use same UQ method for values to be aggregated

3. **Silent distribution coercion**
   - Error: `UQSilentCoercion`
   - Example: Implicitly converting EMPIRICAL to GAUSSIAN
   - Fix: Use explicit conversion with documented rationale

4. **Scalar math on UQValues outside algebra definitions**
   - Error: `UQScalarOperation`
   - Example: `uqvalue + 5.0` (not supported)
   - Fix: Use `UQAlgebra.aggregate_mean([uqvalue, UQValue.degenerate(5.0)])`

##### 10.5.4 Usage Examples

**Basic Aggregation**:
```python
from py3plex.dsl.uq_algebra import UQValue, UQAlgebra, DistributionType, ProvenanceInfo

# Create UQValues
v1 = UQValue(
    distribution_type=DistributionType.GAUSSIAN,
    mean=10.0,
    std=2.0,
    quantiles={0.025: 6.08, 0.975: 13.92},
    provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=42),
)
v2 = UQValue(
    distribution_type=DistributionType.GAUSSIAN,
    mean=15.0,
    std=3.0,
    quantiles={0.025: 9.15, 0.975: 20.85},
    provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=43),
)

# Aggregate (mean is weighted by effective_count)
result = UQAlgebra.aggregate_mean([v1, v2])
print(f"Mean: {result.mean}, Std: {result.std}")
# Mean: 12.5, Std: 1.803 (variance propagation)
```

**Weighted Aggregation**:
```python
# Custom weights
result = UQAlgebra.aggregate_mean([v1, v2], weights=[0.3, 0.7])
print(f"Mean: {result.mean}")
# Mean: 13.5 (0.3*10 + 0.7*15)
```

**Checking Algebraic Laws**:
```python
# Check commutativity
UQAlgebra.check_commutativity(v1, v2, tolerance=1e-9)
# No exception -> law holds

# Check associativity
v3 = UQValue(
    distribution_type=DistributionType.GAUSSIAN,
    mean=20.0,
    std=4.0,
    quantiles={},
    provenance=ProvenanceInfo(method="bootstrap", n_samples=100),
)
UQAlgebra.check_associativity(v1, v2, v3, tolerance=1e-6)
# No exception -> law holds
```

**Mixing Degenerate and Non-Degenerate**:
```python
degenerate = UQValue.degenerate(value=5.0, method="deterministic")
non_degenerate = UQValue(
    distribution_type=DistributionType.GAUSSIAN,
    mean=10.0,
    std=2.0,
    quantiles={},
    provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
)

# Deterministic values can mix with any method
result = UQAlgebra.aggregate_mean([degenerate, non_degenerate])
print(f"Result is degenerate: {result.is_degenerate()}")
# False (uncertainty preserved from non-degenerate)
```

**Converting to/from Canonical Format**:
```python
# From canonical UQ dict
uq_dict = {
    "mean": 10.0,
    "std": 2.0,
    "quantiles": {0.025: 6.0, 0.975: 14.0},
    "method": "bootstrap",
    "n_samples": 100,
}
value = UQValue.from_dict(uq_dict)

# To canonical UQ dict
canonical = value.to_dict()
# Compatible with existing DSL v2 UQ format
```

##### 10.5.5 Guarantees vs Non-Guarantees

**What py3plex GUARANTEES**:
- [CORRECT] All algebraic laws are enforced via runtime checks
- [CORRECT] Violations raise typed, informative errors (fail-fast)
- [CORRECT] UQValue objects are validated on construction
- [CORRECT] Provenance is tracked and recorded for all operations
- [CORRECT] Seed determinism (same seeds -> identical results)
- [CORRECT] Distribution closure (operations always produce valid UQValues)
- [CORRECT] Mean is always associative and commutative
- [CORRECT] Idempotence for identical values

**What py3plex DOES NOT GUARANTEE**:
- [ERROR] Exact std associativity (variance propagation path-dependent)
- [ERROR] Std preservation under aggregation (reduces by variance formula unless identical)
- [ERROR] Backward compatibility with UQValues created before v1.1.3
- [ERROR] Numeric exactness beyond 1e-9 tolerance (floating point limitations)

##### 10.5.6 Fail-Fast Policy

All algebra violations raise **typed exceptions** with actionable error messages:

```python
try:
    UQAlgebra.aggregate_mean([])
except UQIdentityViolation as e:
    print(f"Identity violation: {e}")
    # "Identity law violation: Cannot aggregate empty list of UQValues"

try:
    incompatible1 = UQValue(..., support={"layer": "social"})
    incompatible2 = UQValue(..., support={"layer": "work"})
    UQAlgebra.aggregate_mean([incompatible1, incompatible2])
except UQIncompatibleSupport as e:
    print(f"Support incompatibility: {e}")
    # "Cannot aggregate UQValues with incompatible support: ..."

try:
    bootstrap_value = UQValue(..., provenance=ProvenanceInfo(method="bootstrap"))
    null_model_value = UQValue(..., provenance=ProvenanceInfo(method="null_model"))
    UQAlgebra.aggregate_mean([bootstrap_value, null_model_value])
except UQIncompatibleProvenance as e:
    print(f"Provenance incompatibility: {e}")
    # "Cannot aggregate UQValues with incompatible provenance: ..."
```

##### 10.5.7 Testing Strategy

UQ algebra is verified via:

**Property-Based Tests** (Hypothesis):
- Random UQValues generated with fixed seeds
- Laws checked for all combinations
- Counterexamples saved for regression

**Differential Tests**:
- Same aggregation via different code paths -> identical results
- Direct vs split-aggregate equivalence

**Metamorphic Tests**:
- Splitting then aggregating equals direct aggregation
- Reordering operands preserves results
- Scaling all values scales mean proportionally

**Regression Tests**:
- Known-good UQ algebra outcomes stored as fixtures
- Checked on every commit

**Test Coverage**:
- 32 tests in `tests/test_uq_algebra.py`
- All algebraic laws covered
- All error conditions covered
- Property tests with 50+ random examples each

##### 10.5.8 Implementation Notes

**Location**: `py3plex/dsl/uq_algebra.py`

**Key Classes**:
- `UQValue`: First-class UQ object
- `DistributionType`: Enum (EMPIRICAL, GAUSSIAN, DEGENERATE)
- `ProvenanceInfo`: Immutable provenance tracking
- `UQAlgebra`: Static methods for aggregation and law checking

**Key Functions**:
- `UQAlgebra.aggregate_mean(values, weights=None)`: Primary aggregation operation
- `UQAlgebra.check_associativity(a, b, c, tolerance)`: Verify associativity law
- `UQAlgebra.check_commutativity(a, b, tolerance)`: Verify commutativity law
- `convert_to_uqvalue(data)`: Convert dict/scalar/UQValue to UQValue

**Integration Points**:
- DSL v2 executor uses UQValue internally (planned)
- Existing UQ resolution in `uq_resolution.py` (planned integration)
- Compositional UQ in `compositional_uq.py` (planned integration)

**Backward Compatibility**:
- Existing dict-based UQ format still supported via `to_dict()` / `from_dict()`
- New code should use UQValue directly for algebra guarantees

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

##### `to_pandas(expand_uncertainty=False, expand_explanations=False) -> pd.DataFrame`

**Parameters**:
- `expand_uncertainty` (bool, default=False): Expand UQ results to multiple columns
- `expand_explanations` (bool, default=False): Expand explanation dicts to columns

**Behavior**:
- MUST create DataFrame with one row per item
- For nodes: Index MUST be `(node_id, layer)` tuple
- For edges: Index MUST be `(source, target, source_layer, target_layer)` tuple
- If `expand_uncertainty=True`, MUST expand UQ columns as specified in section 10.4
- If `expand_explanations=True`, MUST expand explanation dicts to JSON strings:
  - `top_neighbors`: JSON-serialized neighbor list
  - `layer_footprint`: JSON-serialized layer presence info
  - `attribution`: JSON-serialized attribution results (see Attribution Block section)

##### `to_networkx() -> nx.Graph or nx.MultiGraph`

**Behavior**:
- MUST convert result to NetworkX graph
- For node queries: Return graph with selected nodes and their attributes
- For edge queries: Return graph with selected edges and their attributes
- MUST use MultiGraph if multiple layers or parallel edges exist

##### `to_arrow() -> pa.Table`

**Behavior**:
- MUST convert result to Apache Arrow table
- Column types MUST be inferred from attribute types
- UQ results MUST be stored as struct columns

##### `to_json() -> str`

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

##### `provenance -> Optional[Dict[str, Any]]`

**Returns**: Provenance dictionary from `meta["provenance"]` if available

##### `is_replayable -> bool`

**Returns**: True if result has replayable provenance

**Requirements for Replayability**:
- Provenance mode MUST be "replayable"
- AST MUST be serialized
- Network snapshot MUST be captured

##### `replay(strict=True) -> QueryResult`

**Behavior**:
- MUST reconstruct network and query from provenance
- MUST re-execute query
- Result MUST match original result (if deterministic)
- If `strict=True`, MUST enforce version compatibility

#### 12.4 Grouping Methods

##### `group_summary() -> pd.DataFrame`

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

#### 13.4 Network Mutation Versioning (`network_version`)

Every `multi_layer_network` instance carries a **monotonic mutation counter** called
`network_version` that increments by exactly 1 on every public structural change.

**Semantics**:
- Starts at `0` for a freshly constructed empty object.
- Incremented by exactly **1** per top-level public mutation call, regardless of how
  many internal graph operations that call performs.
- Read-only property: `net.network_version -> int`.
- Wrapper methods that delegate internally use a `_suspend_version_bump` guard to
  prevent double-counting.

**Mutation triggers** (each increments the counter by 1):
- `add_nodes()`
- `add_edges()`
- `remove_nodes()`
- `remove_edges()`
- `load_network()` (exactly once per call, after the file is fully parsed)

**Non-mutating methods** (counter unchanged):
- `get_nodes()`, `get_edges()`, `get_layers()`, and all read-only query methods.

**Provenance integration**:
`ProvenanceBuilder.set_network(net)` automatically reads `net.network_version` (via
`getattr`) and stores it as `provenance["network_version"]`.  This makes it
straightforward to tie a query result back to the exact structural state of the network
at execution time.

```python
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl.provenance import ProvenanceBuilder

net = multi_layer_network(directed=False)
assert net.network_version == 0          # fresh object

net.add_nodes([{"source": "A", "type": "social"}])
assert net.network_version == 1

net.add_edges([
    {"source": "A", "target": "B", "source_type": "social", "target_type": "social"}
])
assert net.network_version == 2          # one bump for add_edges

# Provenance captures the current version
builder = ProvenanceBuilder(engine="my_engine")
builder.set_network(net)
prov = builder.build()
assert prov["network_version"] == 2
```

**Cache invalidation**:
Downstream caches (e.g., centrality fast-path) MAY use the tuple
`(network_version, ast_hash, params)` as a cache key.  Because `network_version`
changes on every structural mutation, stale cache entries are never silently reused.

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
- Example: `"degree_centraliity"` -> suggests `"degree_centrality"`

**`UnknownMeasureError(measure, known_measures=None)`**:
- Raised when computing unknown measure
- Includes suggestions
- Example: `"betweeness"` -> suggests `"betweenness_centrality"`

**`UnknownLayerError(layer, known_layers=None)`**:
- Raised when referencing unknown layer
- Includes suggestions
- Example: `"socail"` -> suggests `"social"`

**`ParameterMissingError(parameter, provided_params=None)`**:
- Raised when required parameter is not provided
- Lists provided parameters
- Example: `.execute(net)` when query has `Param.int("k")` -> suggests providing `k=...`

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
df = result.to_pandas(expand_uncertainty=True)
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
├─ YES -> Use Q.nodes().compute(...).uq(...)
└─ NO
   ├─ Complex filtering (multilayer-specific)?
   │  └─ YES -> Use Q.nodes().from_layers(L[...]).where(...).compute(...)
   └─ Simple layer filtering?
      ├─ YES -> Use execute_query("SELECT nodes WHERE layer='X' COMPUTE ...")
      └─ NO (single-layer or all layers)
         └─ Use networkx directly: nx.betweenness_centrality(net.core_network)
```

### Decision Tree: Network Analysis Workflow

```
Start with network file (CSV, edgelist, etc.)
├─ Load: net.load_network("file.csv", input_type="edgelist")
├─ Explore structure: net.get_layers(), len(net.get_nodes()), len(net.get_edges())
├─ Query:
│  ├─ Descriptive stats -> Q.nodes().per_layer().aggregate(...)
│  ├─ Top nodes -> Q.nodes().per_layer().top_k(...)
│  └─ Specific patterns -> Q.edges().where(intralayer=True).per_layer_pair().aggregate(...)
├─ Analysis:
│  ├─ Centrality with uncertainty -> Q.nodes().compute(...).uq(...)
│  ├─ Community detection -> from py3plex.algorithms.community_detection import louvain; louvain(net)
│  └─ Dynamics -> Q.dynamics("SIS", ...).run(...).execute(net)
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
- -> **Use DSL v2 for these features**

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

### Network Type Conversions

py3plex supports conversions between different network types: multilayer, multiplex, and single-layer (monoplex).

#### Multilayer vs Multiplex Networks

**Multilayer Networks**:
- General case: Each layer can have a different set of nodes
- Edges can connect any nodes within or across layers
- No automatic coupling edges
- Best for heterogeneous networks (e.g., author-paper-venue)

**Multiplex Networks**:
- Special case: All layers share the same node set (strict replica model)
- Automatic coupling edges between same node across layers
- Best for same entities with multiple relationship types (e.g., social networks with friend/colleague/family layers)

#### Convert Multilayer → Multiplex

Use `to_multiplex()` to convert a multilayer network to multiplex by aligning node sets across layers.

```python
from py3plex.core import multinet

# Create multilayer with partial node overlap
net = multinet.multi_layer_network(network_type='multilayer', directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'friends'},
    {'source': 'Bob', 'type': 'friends'},
    {'source': 'Alice', 'type': 'colleagues'},
    {'source': 'Charlie', 'type': 'colleagues'},
])

# Convert using intersection method (only nodes in ALL layers)
multiplex_strict = net.to_multiplex(method='intersection')
# Result: Only 'Alice' remains (present in both layers)

# Convert using union method (add missing nodes to each layer)
multiplex_complete = net.to_multiplex(method='union')
# Result: All nodes (Alice, Bob, Charlie) now in both layers
```

**Methods**:
- `'intersection'`: Keep only nodes present in ALL layers (strict multiplex)
- `'union'`: Add missing nodes to all layers (lenient multiplex)

**Automatic Coupling**:
After conversion, coupling edges are automatically created between each node and its counterparts in other layers (bidirectional, `type='coupling'`, weight=coupling_weight).

#### Convert Multiplex → Multilayer

Use `to_multilayer()` to convert a multiplex network to multilayer, relaxing the strict replica constraint.

```python
# Create multiplex network
multiplex = multinet.multi_layer_network(network_type='multiplex', directed=False)
multiplex.add_nodes([
    {'source': 'Alice', 'type': 'friends'},
    {'source': 'Alice', 'type': 'colleagues'},
])
multiplex._couple_all_edges()  # Creates coupling edges

# Convert to multilayer, removing coupling edges
multilayer = multiplex.to_multilayer(remove_coupling=True)
# Result: Multilayer network without automatic coupling

# Convert preserving coupling edges as regular inter-layer edges
multilayer_with_coupling = multiplex.to_multilayer(remove_coupling=False)
# Result: Coupling edges preserved as regular edges
```

**Parameters**:
- `remove_coupling=True` (default): Remove automatic coupling edges
- `remove_coupling=False`: Keep coupling edges as regular inter-layer edges

#### Flatten to Single-Layer Graph

Use `flatten_to_monoplex()` to aggregate all layers into a single NetworkX graph.

```python
# Create multilayer network
net = multinet.multi_layer_network(network_type='multilayer', directed=False)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'friends', 'target_type': 'friends', 'weight': 2},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'colleagues', 'target_type': 'colleagues', 'weight': 3},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'friends', 'target_type': 'friends'},
])

# Method 1: Count edge occurrences
flat_count = net.flatten_to_monoplex(method='count')
# Alice-Bob edge: weight=2 (appears in 2 layers)

# Method 2: Sum weights across layers
flat_sum = net.flatten_to_monoplex(method='union')
# Alice-Bob edge: weight=5 (2+3 from two layers)

# Method 3: Keep first occurrence only
flat_first = net.flatten_to_monoplex(method='first')
# Alice-Bob edge: weight=2 (from first layer encountered)
```

**Methods**:
- `'count'`: Count number of times each edge appears across layers
- `'union'`: Sum edge weights across layers (default)
- `'first'`: Keep weight from first occurrence

**Key Behaviors**:
- Node IDs extracted from `(node_id, layer)` tuples → single nodes
- Only intra-layer edges aggregated (inter-layer edges excluded)
- Returns standard NetworkX Graph or DiGraph
- Edge attributes from first occurrence preserved

#### Roundtrip Conversions

```python
# Multilayer → Multiplex → Multilayer
original = multinet.multi_layer_network(network_type='multilayer')
# ... add nodes present in all layers ...
multiplex = original.to_multiplex(method='intersection')
restored = multiplex.to_multilayer(remove_coupling=True)
# Node sets and edges preserved (coupling excluded)

# Multiplex → Multilayer → Multiplex
original_multiplex = multinet.multi_layer_network(network_type='multiplex')
# ... add nodes ...
multilayer = original_multiplex.to_multilayer(remove_coupling=True)
back_to_multiplex = multilayer.to_multiplex(method='intersection')
# Nodes preserved, coupling recreated
```

**Warning**: Flattening to monoplex loses layer information and cannot be reversed.

#### Use Cases

**When to use `to_multiplex()`**:
- Algorithm requires strict replica model (e.g., multiplex centrality)
- Need automatic coupling between layers
- Want to ensure all layers have same nodes

**When to use `to_multilayer()`**:
- Need flexibility in node sets per layer
- Want to remove automatic coupling constraint
- Converting from external multiplex format

**When to use `flatten_to_monoplex()`**:
- Need single-layer graph for standard NetworkX algorithms
- Want to aggregate information across layers
- Comparing multilayer network to monoplex baseline

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

##### .on_layers(layer_expr) -> DynamicsBuilder

Specify layers for simulation.

**Args**: layer_expr from `L[...]`

##### .seed_infections(fraction=None, nodes=None) -> DynamicsBuilder

Initialize infections.

**Args**:
- `fraction` (float): Fraction of nodes to infect randomly (e.g., 0.01 for 1%)
- `nodes` (list): Specific nodes to infect (list of (node, layer) tuples)

##### .starting_nodes(nodes) -> DynamicsBuilder

Set starting nodes for random walk.

**Args**: `nodes` - List of (node, layer) tuples

##### .run(steps, replicates, track="all") -> DynamicsBuilder

Configure simulation execution.

**Args**:
- `steps` (int): Number of simulation steps
- `replicates` (int): Number of independent runs
- `track` (str): What to track - "all", "infected", "peak_time", etc.

##### .execute(network) -> DynamicsResult

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

## Query Selection Fast Path (Filter Fast Path)

### Overview

**New in v1.1.3:** py3plex includes a **selection-only** fast path that accelerates common WHERE filters by pre-building a compact index over the network and applying filters via simple integer comparisons, bypassing the full condition-evaluation pipeline.

> **Important:** This fast path accelerates **item selection** (nodes / edges) only.
> It does **not** approximate centrality metrics.  It is completely separate from
> the approximate-centrality compute fast path described in the next section.

### When the Fast Path Fires

The fast path is activated when **all** of the following hold:

1. `config.DSL_FAST_PATH_ENABLED = True` (default).
2. The query contains **only** supported predicate shapes (see below).
3. No grouping, aggregation, ordering, limit, UQ, community detection, temporal
   context, sensitivity, explain, or compute steps are present.

If any unsupported pattern is detected, the module returns `None` and the
**baseline executor runs unchanged** — results are always correct.

### Supported Predicate Shapes

**Node queries** (`Q.nodes()`):
- Layer filters: `.from_layers(L["X"])` or `WHERE layer="X"`
- Degree thresholds: `degree__gt`, `degree__ge`, `degree__lt`, `degree__le`, `degree__eq`
- Only **AND** combinations of the above.
- **Not supported:** NOT, OR, nested expressions, function calls.

**Edge queries** (`Q.edges()`):
- `src_degree__gt/ge/lt/le/eq`
- `dst_degree__gt/ge/lt/le/eq`
- Optional `source_layer == X AND target_layer == Y`
- Only **AND** combinations.
- **Not supported:** NOT, OR.

### Provenance Flag

Every DSL v2 execution records:

```python
result.meta["provenance"]["backend"]["fast_path"] = True   # fast path used
result.meta["provenance"]["backend"]["fast_path"] = False  # baseline used
```

When the fast path fires it also sets:

```python
result.meta["provenance"]["backend"]["fast_path_plan"] = "FastPlan(target=nodes, ...)"
```

If the fast path raises an unexpected exception it falls back to the baseline
executor and appends `"fast_path_failed_fallback"` to
`result.meta["provenance"]["warnings"]`.

### Config Flag

```python
# py3plex/config.py
DSL_FAST_PATH_ENABLED: bool = True   # set to False to always use baseline
```

Pass `planner={"enable_cache": False}` or temporarily set
`config.DSL_FAST_PATH_ENABLED = False` to force the baseline for benchmarking.

### Module Location

`py3plex/dsl/fastpath.py` — public symbols:

| Symbol | Purpose |
|--------|---------|
| `FastPlan` | Dataclass describing a fast-path eligible query |
| `FastIndex` | Pre-built index over the network |
| `match_fastpath(select_stmt)` | Returns `FastPlan` or `None` |
| `build_fast_index(net, plan)` | Builds the index lazily |
| `fast_select_nodes(plan, idx)` | Returns filtered node list |
| `fast_select_edges(plan, idx)` | Returns filtered edge list |

### Distinction from Compute Fast Path

| Feature | Selection fast path | Compute fast path (approx centrality) |
|---------|--------------------|-----------------------------------------|
| Controls | Item selection (WHERE) | Centrality metric computation |
| Trigger | `config.DSL_FAST_PATH_ENABLED` | `approx=True` in `.compute()` |
| Provenance flag | `backend.fast_path` | `backend.fast_path` |
| Safe fallback | Yes — returns None, baseline runs | Raises on bad params |
| Affects metric values | **No** | **Yes** (approximation) |

---

## Approximate Centrality Algorithms (Compute Fast Path)

### Overview

**New in v1.1:** py3plex provides fast approximate centrality algorithms as first-class citizens for large networks (>1000 nodes). Approximations integrate seamlessly with DSL v2, AST/provenance, UQ, and multilayer semantics.

**Key Features:**
- **10-100x speedup** for betweenness and closeness on large networks
- **Deterministic**: Same seed produces identical results
- **Integrated**: Works with `.from_layers()`, `.per_layer()`, and `.uq()`
- **Provenance**: Full parameter tracking with `fast_path=True` flag

### Supported Algorithms

| Measure | Default Method | Typical Speedup | Parameters |
|---------|---------------|-----------------|------------|
| `betweenness_centrality` | `sampling` | 10-100x | `n_samples`, `seed` |
| `closeness_centrality` | `landmarks` | 10-50x | `n_landmarks`, `seed` |
| `pagerank` | `power_iteration` | 2-10x | `tol`, `max_iter` |

### DSL v2 API

**Basic usage:**

```python
from py3plex.dsl import Q

# Approximate betweenness (sampling-based)
result = Q.nodes().compute(
    "betweenness_centrality",
    approx=True,
    n_samples=512,
    seed=42
).execute(net)

# Approximate closeness (landmark-based)
result = Q.nodes().compute(
    "closeness_centrality",
    approx=True,
    n_landmarks=64,
    seed=42
).execute(net)

# Approximate PageRank (power iteration)
result = Q.nodes().compute(
    "pagerank",
    approx=True,
    tol=1e-6,
    max_iter=100
).execute(net)
```

**With explicit method:**

```python
result = Q.nodes().compute(
    "betweenness_centrality",
    approx=True,
    approx_method="sampling",  # Explicit method
    n_samples=512,
    seed=42
).execute(net)
```

### Legacy String DSL API

**Bare APPROXIMATE keyword (uses defaults):**

```python
from py3plex.dsl_legacy import execute_query

result = execute_query(net, 'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE')
```

**With parameters:**

```python
result = execute_query(net,
    'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE(method="sampling", n_samples=512, seed=42)'
)
```

### Multilayer Integration

Approximations work seamlessly with multilayer queries:

```python
# Layer filtering
result = Q.nodes().from_layers(L["social"]).compute(
    "betweenness_centrality",
    approx=True,
    n_samples=256,
    seed=42
).execute(net)

# Per-layer grouping
result = Q.nodes().per_layer().compute(
    "betweenness_centrality",
    approx=True,
    n_samples=128,
    seed=42
).execute(net)
```

### UQ Integration

Approximations compose with uncertainty quantification:

```python
# UQ + approximation
result = Q.nodes().compute(
    "betweenness_centrality",
    approx=True,
    uncertainty=True,
    n_samples=100,  # UQ samples
    seed=42
).execute(net)
```

**Note**: When combining UQ with approximation:
- `n_samples` in `.compute()` refers to UQ replicates
- Approximation parameters (like sampling count) are set via approx-specific kwargs
- Seed is shared across UQ and approximation for full determinism

### Provenance Metadata

All approximation executions record detailed metadata:

```python
result = Q.nodes().compute(
    "betweenness_centrality",
    approx=True,
    n_samples=512,
    seed=42
).execute(net)

# Check fast_path flag
assert result.meta["provenance"]["backend"]["fast_path"] is True

# Check approximation details
approx_meta = result.meta["approximation"]
print(approx_meta)
# {
#     "enabled": True,
#     "measures": [{
#         "measure": "betweenness_centrality",
#         "algorithm": "sampling_betweenness_centrality",
#         "method": "sampling",
#         "parameters": {"seed": 42},
#         "diagnostics_enabled": False
#     }],
#     "fast_path": True
# }
```

### Accuracy Guidelines

**Betweenness (sampling):**
- `n_samples=100`: ~20% relative error
- `n_samples=512`: ~10% relative error
- `n_samples=2048`: ~5% relative error

**Closeness (landmarks):**
- `n_landmarks=10`: Coarse approximation
- `n_landmarks=50`: ~15% relative error
- `n_landmarks=100`: ~10% relative error

**PageRank (power iteration):**
- `tol=1e-4`: Fast, ~1% error
- `tol=1e-6`: Standard, ~0.1% error
- `tol=1e-8`: High precision, ~0.01% error

### When to Use Approximation

**Use approximation when:**
- Network has >1000 nodes
- Exact computation takes >1 minute
- Exploratory analysis where approximate rankings are sufficient
- Production pipelines requiring predictable execution time
- Multiple runs needed for sensitivity analysis

**Use exact computation when:**
- Network has <500 nodes (exact is fast enough)
- Precise values required for critical decisions
- Publishing results requiring exact centrality values

### Error Handling

Invalid parameters raise typed errors:

```python
from py3plex.dsl.uq_resolution import UQResolutionError

try:
    Q.nodes().compute("betweenness_centrality", approx=True, n_samples=0).execute(net)
except UQResolutionError as e:
    print(e)  # "n_samples must be positive, got 0"
```

Invalid methods fall back gracefully with warnings logged.

### Algorithm Details

**Sampling-based Betweenness:**
- Algorithm: Brandes with source sampling
- Complexity: O(m × n_samples) vs O(nm) exact
- Unbiased estimator converging to exact value

**Landmark-based Closeness:**
- Algorithm: Distance sampling from random landmarks
- Complexity: O(m × n_landmarks) vs O(nm) exact
- Component-aware for undirected graphs

**Power Iteration PageRank:**
- Algorithm: Power iteration with L1 convergence
- Complexity: O(m × max_iter) vs O(nm) for some exact methods
- Deterministic (no randomness)

### LLM Agent Guidance

**Decision rules for agents:**

```
IF user asks to compute centrality on large network (>1000 nodes)
THEN suggest approximation:
  Q.nodes().compute("betweenness_centrality", approx=True, n_samples=512, seed=42)

IF user needs deterministic results
THEN always specify seed:
  approx=True, seed=42

IF user combines with UQ
THEN clarify parameter semantics:
  - n_samples in .compute() = UQ replicates
  - approx params = algorithm parameters
```

**Common patterns:**

```python
# Exploratory analysis (fast)
Q.nodes().compute("betweenness_centrality", approx=True, n_samples=128, seed=42)

# Production (balanced accuracy/speed)
Q.nodes().compute("betweenness_centrality", approx=True, n_samples=512, seed=42)

# High accuracy (near-exact)
Q.nodes().compute("betweenness_centrality", approx=True, n_samples=2048, seed=42)

# With UQ
Q.nodes().compute("betweenness_centrality", approx=True, uncertainty=True, n_samples=50, seed=42)
```

---

## Uncertainty Quantification

### Overview

Uncertainty Quantification (UQ) in py3plex provides confidence intervals, stability metrics, and distributional information for network analysis results. UQ is integrated into DSL v2 and is essential for robust, reproducible research.

**UQ Compliance Philosophy**: py3plex UQ is designed to be **deterministic**, **fail-fast**, and **fully verifiable**. All UQ configurations are materialized before execution, validated against a canonical schema, and tracked in provenance.

### UQ Resolution Order

UQ configuration follows a strict **priority order** to ensure deterministic, predictable behavior:

1. **Metric-level** (highest priority): Parameters specified in `.compute()` call
2. **Query-level**: Parameters specified in `.uq()` call
3. **Global defaults**: Set via `set_global_uq_defaults()`
4. **Library defaults**: Built-in defaults

**Example**:
```python
from py3plex.dsl import Q, set_global_uq_defaults

# Set global defaults
set_global_uq_defaults(method="bootstrap", n_samples=100, seed=42)

# Query-level overrides global for this query
result = (
    Q.nodes()
     .uq(method="perturbation", n_samples=50)  # Overrides global method and n_samples
     .compute("degree")  # Uses query-level config
     .compute("betweenness", n_samples=200)  # Metric-level overrides query-level n_samples
     .execute(net)
)

# Final resolution:
# - degree: method="perturbation", n_samples=50, seed=42 (query + global)
# - betweenness: method="perturbation", n_samples=200, seed=42 (metric + query + global)
```

**Resolution Guarantees**:
- [CORRECT] Exactly one UQ config per metric after resolution
- [CORRECT] Conflicting configs at same priority level raise `UQResolutionError`
- [CORRECT] Resolved config is fully materialized before execution
- [CORRECT] No implicit or silent defaults applied at execution time
- [CORRECT] Provenance tracks source of each parameter (metric/query/global/library)

### Canonical UQ Schema

All UQ-enabled results conform to a **single canonical schema**. This ensures consistency across all UQ methods, contexts, and export formats.

**Required Fields**:
```python
{
    "value": float,        # or "mean" - the point estimate
    "std": float,          # standard deviation
    "ci_low": float,       # lower confidence interval bound
    "ci_high": float,      # upper confidence interval bound
    "quantiles": dict,     # {quantile: value} mapping
    "n_samples": int,      # number of samples used
    "method": str,         # UQ method used
    "seed": int,           # random seed (if applicable)
}
```

**Optional Fields** (method-specific):
```python
{
    # Bootstrap-specific
    "bootstrap_unit": str,     # "edges", "nodes", or "layers"
    "bootstrap_mode": str,     # "resample" or "permute"
    
    # Null model-specific
    "null_model": str,         # "degree_preserving", "erdos_renyi", "configuration"
    "mean_null": float,        # null model mean
    "zscore": float,           # z-score
    "pvalue": float,           # p-value
    
    # Legacy
    "certainty": float,        # certainty metric (deprecated, maintained for compatibility)
}
```

**Schema Validation**:
- [CORRECT] All UQ results are validated before being returned
- [CORRECT] Invalid schemas raise `UQSchemaValidationError` with detailed diagnostics
- [CORRECT] Deterministic metrics (std=0) allowed with `allow_degenerate=True`

**Example - Accessing UQ Results**:
```python
result = (
    Q.nodes()
     .compute("degree")
     .uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)
     .execute(net)
)

# Access UQ information
degree_uq = result.attributes["degree"]
for node, uq_dict in degree_uq.items():
    print(f"Node {node}:")
    print(f"  Value: {uq_dict['value']}")
    print(f"  Std: {uq_dict['std']}")
    print(f"  95% CI: [{uq_dict['ci_low']}, {uq_dict['ci_high']}]")
    print(f"  Method: {uq_dict['method']}")
    print(f"  Seed: {uq_dict['seed']}")
```

### UQ Execution Modes

py3plex DSL v2 supports two execution modes for uncertainty quantification:

#### Mode 1: summarize_only (DEFAULT)

**Behavior**: Compute metrics with UQ, then apply downstream operations (where, order_by, limit) on the summarized (mean) values.

**Use when**:
- You want traditional UQ on metric values
- Downstream operations should use point estimates
- You're interested in metric uncertainty, not selection uncertainty

**Example**:
```python
result = (
    Q.nodes()
     .compute("pagerank")
     .order_by("pagerank", desc=True)
     .limit(10)
     .uq(method="bootstrap", n_samples=50, seed=42, mode="summarize_only")
     .execute(net)
)

# Result: Top 10 nodes by MEAN pagerank
# Each pagerank value is a UQ dict with mean, std, CI
```

#### Mode 2: propagate (NEW)

**Behavior**: Execute the entire query end-to-end per replicate (bootstrap/perturbation/seed), then aggregate replicate results to measure **selection uncertainty**.

**Use when**:
- You want to know which nodes/edges are stable in rankings
- You need to quantify selection uncertainty (e.g., "is this node reliably in the top-10?")
- Downstream operations (where, limit, top_k) should be uncertainty-aware

**Extra Outputs**:
- **p_present**: Fraction of replicates where item appears in result
- **p_selected**: Fraction where item is in final selected set (when limit/top_k used)
- **rank_uq**: UQ over ranks (when ordering + selection used)

**Example**:
```python
result = (
    Q.nodes()
     .compute("pagerank")
     .order_by("pagerank", desc=True)
     .limit(3)
     .uq(method="perturbation", n_samples=25, seed=42, mode="propagate")
     .execute(net)
)

df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, p_present, p_selected, rank_uq, pagerank (with _mean, _std, _ci95_low, etc.)
# p_selected shows how often each node was in top-3 across replicates
```

**Mode Comparison**:

| Feature | summarize_only | propagate |
|---------|---------------|-----------|
| Metric UQ |  (mean, std, CI) |  (mean, std, CI) |
| Selection UQ |  |  (p_present, p_selected) |
| Rank UQ |  |  (rank_uq) |
| Computational cost | Lower | Higher (n_samples × query) |
| Use for | Metric uncertainty | Selection stability |

### Extended .uq() Signature

```python
.uq(
    method="perturbation",    # UQ method
    n_samples=50,             # Number of samples/replicates
    ci=0.95,                  # Confidence interval level
    seed=None,                # Random seed for determinism
    mode="summarize_only",    # NEW: "summarize_only" | "propagate"
    keep_samples=None,        # NEW: bool | None (default: True for propagate)
    reduce="empirical",       # NEW: "empirical" | "gaussian"
    **kwargs                  # Method-specific parameters
)
```

**New Parameters**:

- **mode**: Execution mode
  - `"summarize_only"` (default): Traditional UQ on metrics
  - `"propagate"`: End-to-end replicate execution for selection UQ

- **keep_samples**: Whether to retain raw samples
  - `None` (default): Auto-decide (True for propagate, False for summarize_only)
  - `True`: Keep samples (enables empirical reduction)
  - `False`: Discard samples (use Gaussian approximation)

- **reduce**: Reduction method for aggregating replicate results
  - `"empirical"` (default): Use empirical quantiles from samples
  - `"gaussian"`: Assume Gaussian, use mean ± z*std

**Performance Note**: `mode="propagate"` with `reduce="gaussian"` and `keep_samples=False` saves memory for large n_samples.

### Correctness Guarantees

**Determinism**:
- All UQ methods are **fully deterministic** when seeded [CORRECT]
- Same `seed` parameter produces **identical confidence intervals** across runs (verified in tests)
- Bootstrap, perturbation, and null model methods all respect `seed`

**Monotonicity**:
- **CI stability**: Larger `n_samples` -> more stable confidence intervals
- **Coverage guarantee**: Confidence intervals use standard bootstrap percentile method
- **Finiteness**: All CI bounds are finite (no NaN/inf), verified in tests [CORRECT]

**Special cases**:
- **Deterministic algorithms with seed**: `std = 0`, CI width = 0 (verified) [CORRECT]
- **Empty groups**: Handled gracefully with explicit error messages (no silent failures)
- **Single-node groups**: UQ still computes, but CI may be degenerate

**Reproducibility**:
```python
# [CORRECT] Guaranteed to produce identical CIs
result1 = Q.nodes().compute("betweenness").uq(seed=42, n_samples=100).execute(net)
result2 = Q.nodes().compute("betweenness").uq(seed=42, n_samples=100).execute(net)

# Extract CIs
df1 = result1.to_pandas(expand_uncertainty=True)
df2 = result2.to_pandas(expand_uncertainty=True)
assert df1.equals(df2)  # [CORRECT] Identical
```

### Semantic Consistency

UQ semantics are **identical** across all contexts:

**[CORRECT] Consistent Across**:
- Node queries, edge queries, graph-level metrics
- Per-layer and per-layer-pair groupings
- Temporal queries (snapshots, windows)
- All supported UQ methods (bootstrap, perturbation, seed, null_model)

**Example - Grouping Preserves Semantics**:
```python
# Global UQ
result_global = (
    Q.nodes()
     .compute("degree")
     .uq(method="bootstrap", n_samples=100, seed=42)
     .execute(net)
)

# Per-layer UQ (same semantics, grouped results)
result_grouped = (
    Q.nodes()
     .compute("degree")
     .uq(method="bootstrap", n_samples=100, seed=42)
     .per_layer()
     .end_grouping()
     .execute(net)
)

# Same seed + same method -> same distributions per node
# Grouping only affects result organization, not UQ semantics
```

py3plex provides first-class uncertainty quantification for network metrics.

### UQ Modes: Summarize vs. Propagate

**New in v1.1+**: py3plex DSL v2 supports two UQ execution modes that control how uncertainty propagates through query operations.

#### Mode: `summarize_only` (DEFAULT)

**Behavior**: Compute metrics multiple times, then summarize. Downstream operators (filtering, ordering, selection) operate on **mean values**.

**Use when**:
- You want traditional UQ on metric values only
- Query structure is deterministic (no selection/ordering based on uncertain values)
- Backward compatibility with existing queries

**Example**:
```python
result = (
    Q.nodes()
     .compute("pagerank")
     .order_by("pagerank", desc=True)
     .limit(10)
     .uq(method="bootstrap", n_samples=50, seed=42, mode="summarize_only")
     .execute(net)
)

# Ordering uses mean pagerank values
# Top 10 nodes are deterministic under fixed seed
df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, pagerank_mean, pagerank_std, pagerank_ci95_low, pagerank_ci95_high
```

#### Mode: `propagate` (NEW)

**Behavior**: Execute the **entire query end-to-end per replicate** (bootstrap/perturbation/seed/etc.), then reduce replicate results into a single UQ-aware QueryResult.

**What changes per replicate**:
- Network structure (bootstrap resampling, edge perturbation)
- Metric values (computed on perturbed networks)
- **Query results**: which items pass filters, ordering, selection

**Additional outputs in `propagate` mode**:
- **`p_present`**: Fraction of replicates where an item appears in the result set
- **`p_selected`**: Fraction of replicates where an item is in the final selection (when `.limit()` or `.top_k()` used)
- **`rank_uq`** (optional): Uncertainty over rank positions when selection is used

**Use when**:
- Selection/ordering depends on uncertain metric values
- You need to quantify **selection stability** ("is this node reliably in top-10?")
- You want to identify **borderline cases** (0 < p_selected < 1)

**Example**:
```python
result = (
    Q.nodes()
     .compute("pagerank")
     .order_by("pagerank", desc=True)
     .limit(10)
     .uq(method="perturbation", n_samples=50, seed=42, mode="propagate")
     .execute(net)
)

# Each replicate:
#   1. Perturb network
#   2. Compute pagerank on perturbed network
#   3. Order by perturbed pagerank
#   4. Select top 10
# Then aggregate across replicates

df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, pagerank_mean, pagerank_std, pagerank_ci95_low, pagerank_ci95_high,
#          p_present, p_selected, rank_uq_mean, rank_uq_std, ...

# Identify borderline nodes (sometimes in top-10, sometimes not)
borderline = df[(df['p_selected'] > 0) & (df['p_selected'] < 1)]
print(f"Borderline nodes: {len(borderline)}")
```

#### `.uq()` Parameter Reference

**Updated signature (v1.1+)**:
```python
.uq(
    method="perturbation",     # UQ method: "bootstrap", "perturbation", "seed", "null_model"
    n_samples=50,              # Number of replicates
    ci=0.95,                   # Confidence interval level
    seed=None,                 # Random seed for determinism
    mode="summarize_only",     # NEW: "summarize_only" | "propagate"
    keep_samples=None,         # NEW: Store raw samples (default: True if propagate, False otherwise)
    reduce="empirical",        # NEW: "empirical" (use quantiles) | "gaussian" (parametric)
    **kwargs                   # Method-specific parameters
)
```

**New Parameters**:

**`mode`** (str, default: `"summarize_only"`):
- `"summarize_only"`: Traditional UQ on metric values; downstream ops use means
- `"propagate"`: Execute full query per replicate; quantify selection uncertainty

**`keep_samples`** (bool | None, default: `None`):
- `None`: Auto-decide (True for propagate, False for summarize_only)
- `True`: Store raw samples for each metric (memory-intensive)
- `False`: Discard samples after computing statistics

**`reduce`** (str, default: `"empirical"`):
- `"empirical"`: Use empirical quantiles from samples (non-parametric)
- `"gaussian"`: Fit Gaussian and use parametric CI (memory-efficient, assumes normality)

**Performance Notes**:
- **Propagate mode cost**: O(n_samples × query_cost)
- Use `reduce="gaussian"` with large n_samples to save memory
- Start with n_samples=20-30 for exploration, increase for publication
- Always set `seed` for reproducibility

**Compatibility Rules**:
- `mode` is **query-level only** (cannot be set per-metric)
- In `mode="propagate"`, per-metric UQ methods must be unset or equal to query method
- Mixing propagate mode with per-metric UQ raises `UQIncompatibleConfiguration`

#### Provenance for Propagate Mode

When `mode="propagate"`, provenance includes replicate plan summary:

```python
result.meta["provenance"]["uq"] = {
    "enabled": True,
    "method": "perturbation",
    "n_samples": 50,
    "ci": 0.95,
    "seed": 42,
    "mode": "propagate",
    "keep_samples": True,
    "reduce": "empirical",
    "plan": {
        "n_replicates": 50,
        "replicate_type": "perturbed_network",
        "deterministic": True,
        "seed_spawn_method": "splitmix64"
    }
}

result.meta["uq_propagation"] = {
    "n_samples": 50,
    "mode": "propagate",
    "selection": {
        "has_topk": False,
        "has_limit": True,
        "key": "pagerank",
        "k": 10
    },
    "p_present_column": "p_present",
    "p_selected_column": "p_selected"
}
```

### Supported UQ Methods

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

**Deterministic**: Same seed -> identical results across runs and parallel executions (uses `numpy.random.SeedSequence`).

**Metadata**: Results include stratification info in `result.meta["stratification"]` and `result.meta["n_strata"]`.

**Fallback**: If stratification is infeasible (e.g., network too small, no meaningful strata), automatically falls back to regular perturbation.

### Provenance and Traceability

Every UQ execution is fully auditable through provenance metadata:

**Provenance Contains**:
```python
{
    "method": "bootstrap",             # UQ method used
    "n_samples": 100,                  # Number of samples
    "seed": 42,                        # Random seed (if set)
    "ci": 0.95,                        # Confidence interval level
    "bootstrap_unit": "edges",         # Method-specific params
    "resolution": {                    # Source of each parameter
        "method": "query_level",
        "n_samples": "metric_level",
        "seed": "global_default",
        "ci": "library_default"
    },
    "timestamp": "2024-01-18T15:19:03Z",
    "aggregation_level": "per_node"   # or "per_layer", "per_layer_pair", etc.
}
```

**Accessing Provenance**:
```python
result = Q.nodes().compute("degree").uq(method="bootstrap", seed=42).execute(net)

# Access provenance
prov = result.meta["provenance"]
print(f"UQ method: {prov['randomness']['method']}")
print(f"Seed: {prov['randomness']['seed']}")
print(f"Samples: {prov['randomness']['n_samples']}")
```

**Provenance Guarantees**:
- [CORRECT] Machine-readable and serializable (JSON-compatible)
- [CORRECT] Comparable across runs (same structure, deterministic ordering)
- [CORRECT] Includes resolution source for each parameter (metric/query/global/library)
- [CORRECT] Results cannot be returned if UQ requested but provenance incomplete

### Fail-Fast Error Handling

py3plex UQ uses **explicit, fail-fast error handling** with no silent fallbacks:

**Error Types**:

1. **`UQResolutionError`** - Configuration issues
   ```python
   # Invalid method
   Q.nodes().compute("degree").uq(method="invalid_method")
   # -> UQResolutionError: Invalid UQ method 'invalid_method'. Valid methods: bootstrap, perturbation, ...
   
   # Missing required parameter
   Q.nodes().compute("degree").uq(method="null_model")  # Missing null_model param
   # -> UQResolutionError: null_model method requires 'null_model' parameter
   ```

2. **`UQSchemaValidationError`** - Result schema violations
   ```python
   # Internal error: metric implementation returns incomplete UQ result
   # -> UQSchemaValidationError: UQ result for 'degree' missing required fields: std, ci_low
   ```

3. **`UQUnsupportedError`** - Unsupported contexts
   ```python
   # UQ on edge queries (not yet fully supported)
   Q.edges().compute("edge_betweenness").uq(method="bootstrap")
   # -> UQUnsupportedError: UQ for edge queries not yet fully supported
   ```

**No Silent Fallbacks**:
- [ERROR] No default values silently applied
- [ERROR] No warnings without errors
- [ERROR] No graceful degradation to deterministic
- [CORRECT] Every configuration issue raises a descriptive error
- [CORRECT] Errors include location in DSL chain and fix suggestions

**Example - Helpful Error Messages**:
```python
try:
    Q.nodes().compute("degree").uq(n_samples=0).execute(net)
except UQResolutionError as e:
    print(e)
    # -> n_samples must be positive, got 0
    #   At: .uq() call in query chain
    #   Fix: Set n_samples to a positive integer (e.g., n_samples=50)
```

### Supported and Unsupported Contexts

**[CORRECT] Fully Supported**:
- Node queries with centrality metrics (degree, betweenness, closeness, pagerank, etc.)
- Bootstrap resampling (edges, nodes, layers)
- Perturbation and stratified perturbation
- Null model comparisons
- Per-layer and per-layer-pair groupings
- Temporal snapshots and windows

**[WARNING] Partial Support**:
- Edge queries (bootstrap only, other methods in development)
- Community detection (via separate ensemble API)

**[ERROR] Not Supported** (raises `UQUnsupportedError`):
- Graph-level aggregations (use per-node UQ then aggregate)
- Motif queries (deterministic only)

### Export and Serialization

All exports **preserve full UQ information by default**:

**Pandas Export**:
```python
result = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=100, seed=42).execute(net)

# Expanded format (deterministic column names)
df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, degree_mean, degree_std, degree_ci95_low, degree_ci95_high

# Compact format (UQ dicts in cells)
df_compact = result.to_pandas(expand_uncertainty=False)
# Columns: node, layer, degree (dict with UQ info)
```

**JSON Export**:
```python
# Full UQ metadata preserved
result.to_json("result.json")
# {
#   "nodes": [...],
#   "attributes": {"degree": {"node1": {"mean": 5.0, "std": 0.5, ...}}},
#   "meta": {"provenance": {"randomness": {...}}}
# }
```

**NetworkX Attributes**:
```python
# UQ info attached as node attributes
G = result.to_networkx(attach_attributes=True)
# G.nodes["node1"]["degree"] = {"mean": 5.0, "std": 0.5, ...}
```

**Lossy Exports** (require explicit opt-in):
```python
# Drop uncertainty info (not yet implemented - will require explicit flag)
# df = result.to_pandas(drop_uncertainty=True)  # Future API
# -> Records loss in provenance
```

### Supported UQ Methods

**1. Bootstrap Resampling**

Bootstrap estimates uncertainty by resampling network elements (edges, nodes, or layers) with replacement.

```python
# Bootstrap with edge resampling (default)
result = (
    Q.nodes()
     .compute("pagerank", "betweenness_centrality")
     .uq(method="bootstrap", n_samples=100, ci=0.95, seed=42, bootstrap_unit="edges")
     .execute(net)
)

# Bootstrap with node resampling
result = (
    Q.nodes()
     .compute("clustering")
     .uq(method="bootstrap", n_samples=100, bootstrap_unit="nodes", seed=42)
     .execute(net)
)

# Bootstrap with layer resampling (for multilayer networks)
result = (
    Q.nodes()
     .compute("degree")
     .uq(method="bootstrap", n_samples=50, bootstrap_unit="layers", seed=42)
     .execute(net)
)
```

**Bootstrap Modes**:
- `resample` (default): Sample with replacement
- `permute`: Shuffle/permute existing elements

```python
# Permutation test
result = (
    Q.nodes()
     .compute("betweenness")
     .uq(method="bootstrap", bootstrap_mode="permute", n_samples=100, seed=42)
     .execute(net)
)
```

**2. Perturbation**

Perturbation adds noise to the network structure (drop/add edges) to estimate sensitivity.

```python
result = (
    Q.nodes()
     .compute("degree", "clustering")
     .uq(method="perturbation", n_samples=50, noise_level=0.1, seed=42)
     .execute(net)
)
```

**3. Stratified Perturbation** (NEW - Variance-Reduced)

Stratified perturbation preserves key network structure during perturbation, reducing variance.

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
```

**4. Multi-seed (for Deterministic Algorithms)**

Seed method runs deterministic algorithms with different random seeds.

```python
result = (
    Q.nodes()
     .compute("louvain_community")
     .uq(method="seed", n_samples=20, seed=42)
     .execute(net)
)
```

**5. Null Model Comparison**

Null model method compares observed values against null model distributions.

```python
result = (
    Q.nodes()
     .compute("betweenness_centrality")
     .uq(
         method="null_model",
         null_model="degree_preserving",
         n_null=200,
         seed=42
     )
     .execute(net)
)

# Access null model statistics
for node, uq_dict in result.attributes["betweenness_centrality"].items():
    print(f"Node {node}:")
    print(f"  Observed: {uq_dict['value']}")
    print(f"  Null mean: {uq_dict['mean_null']}")
    print(f"  Z-score: {uq_dict['zscore']}")
    print(f"  P-value: {uq_dict['pvalue']}")
```

**Supported Null Models**:
- `degree_preserving`: Configuration model (preserves degree sequence)
- `erdos_renyi`: Random graph with same edge probability
- `configuration`: Configuration model (alias for degree_preserving)

### UQ Method Summary Table

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| `bootstrap` | General-purpose UQ | Standard, interpretable CIs | Can be slow for large networks |
| `perturbation` | Robustness analysis | Fast, tests sensitivity | May not preserve structure |
| `stratified_perturbation` | Large networks | Variance-reduced, faster convergence | More complex setup |
| `seed` | Deterministic algorithms | Simple, no resampling | Only for non-deterministic algorithms |
| `null_model` | Statistical significance | Hypothesis testing, p-values | Requires null model assumption |

### Working with UQ Results

**Accessing UQ Information**:
```python
result = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=100, seed=42).execute(net)

# Access raw UQ dictionaries
degree_uq = result.attributes["degree"]
for node, uq_dict in degree_uq.items():
    print(f"Node {node}:")
    print(f"  Mean: {uq_dict['mean']}")
    print(f"  Std: {uq_dict['std']}")
    print(f"  95% CI: [{uq_dict['ci_low']}, {uq_dict['ci_high']}]")
```

**Exporting with UQ**:
```python
# Expanded pandas format (deterministic column names)
df = result.to_pandas(expand_uncertainty=True)
# Columns: node, layer, degree_mean, degree_std, degree_ci95_low, degree_ci95_high

# Compact format (UQ in dict columns)
df_compact = result.to_pandas(expand_uncertainty=False)
# Columns: node, layer, degree (where degree is a dict)

# JSON export (full UQ preserved)
result.to_json("results_with_uq.json")
```

### Global UQ Configuration

Set default UQ parameters for all queries:

```python
from py3plex.dsl import set_global_uq_defaults, reset_global_uq_defaults

# Set global defaults
set_global_uq_defaults(
    method="bootstrap",
    n_samples=100,
    ci=0.95,
    seed=42,
    bootstrap_unit="edges"
)

# Now all queries with .uq() or uncertainty=True use these defaults
result = Q.nodes().compute("pagerank").uq().execute(net)  # Uses global defaults

# Override specific parameters
result = Q.nodes().compute("degree").uq(n_samples=200).execute(net)  # Overrides only n_samples

# Reset to library defaults
reset_global_uq_defaults()
```

### Bootstrap Units (Legacy - kept for compatibility)

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
- **Unstable**: VI > 0.5 or NMI < 0.7 -> Tune γ or refine data

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
# High-stakes analysis requiring tight CIs -> stratified_perturbation
Q.nodes().compute("pagerank").uq(method="stratified_perturbation", n_samples=100, seed=42).execute(net)

# Quick exploratory analysis -> perturbation
Q.nodes().compute("degree").uq(method="perturbation", n_samples=50, edge_drop_p=0.1, seed=42).execute(net)

# Stochastic algorithm (Leiden) -> seed
Q.nodes().community(method="leiden").uq(method="seed", n_samples=50, seed=42).execute(net)

# Testing data robustness -> bootstrap
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
Given an edge e, lift : Edge -> K maps edge attributes into semiring space.

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
   - Clipping prevents giant clusters (H->0) or extreme fragmentation from dominating
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
- Multiple metrics -> single scalar via weighted sum
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
# Same seed -> identical results (deterministic)
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
- Determinism: same seed -> same winner -> same elimination order
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
- If multiple non-dominated -> **Consensus partition** computed via co-assignment
- If single non-dominated -> That algorithm is selected

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
            print("  -> Highly significant (p < 0.001)")
        elif z_score > 2.0:
            print("  -> Significant (p < 0.05)")
        else:
            print("  -> Weak signal (may be filtered)")
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

# High degree heterogeneity -> Scale-free network
# High coupling strength -> Strongly multiplex network
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
-  Using single metric (e.g., only modularity) -> Use multi-objective
-  Ignoring uncertainty -> Always use `.uq()` for stability
-  No null calibration -> Use `.null_model()` for significance
-  Treating all nodes equally -> Check `node_confidence` for reliability
-  Ignoring orphan nodes -> Examine `community_stats.orphan_nodes`

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

---

## Diagnostic System and Error Reporting

### Overview

py3plex v1.1.3+ includes a next-generation diagnostic system that transforms error messages into interactive, actionable guidance for both human researchers and LLMs.

**Key Features**:
1. **Unified Diagnostic Model**: All errors, warnings, and info messages use a single `Diagnostic` object format
2. **Stable Error Codes**: Machine-readable codes (e.g., `DSL_SEM_001`, `EXEC_002`) for programmatic handling
3. **Fuzzy Matching**: "Did you mean?" suggestions for typos in field names, measures, layers, etc.
4. **JSON Serialization**: LLM-friendly diagnostic export for automated error recovery
5. **Interactive Help**: `.explain()` and `.debug()` methods on `QueryResult`
6. **AST-Aware**: Errors reference specific builder methods and query fragments

### Diagnostic Structure

Every diagnostic includes:

```python
from py3plex.diagnostics import Diagnostic, DiagnosticSeverity, FixSuggestion

diag = Diagnostic(
    severity=DiagnosticSeverity.ERROR,        # ERROR, WARNING, or INFO
    code="DSL_SEM_001",                        # Stable error code
    message="Unknown field 'degreee'",         # Human-readable summary
    context={                                  # Where it happened
        "builder_method": "where",
        "query_fragment": "degreee__gt=3",
        "ast_node": "WhereClause"
    },
    cause="Field name contains a typo",        # Why it happened
    fixes=[                                    # How to fix it
        FixSuggestion(
            description="Did you mean 'degree'?",
            replacement="degree",
            example="Q.nodes().where(degree__gt=3)"
        )
    ],
    related=[                                  # What to try next
        "Q.nodes().compute()",
        "Available fields: degree, betweenness_centrality"
    ]
)

# Export for LLM consumption
print(diag.to_json())

# Human-readable formatting
print(diag.format(use_color=True))
```

### Error Code Taxonomy

All error codes follow the pattern `<CATEGORY>_<SUBCATEGORY>_<NUMBER>`:

**DSL Parsing Errors** (`DSL_PARSE_*`):
- `DSL_PARSE_001`: Unknown token or keyword
- `DSL_PARSE_002`: Invalid comparison operator
- `DSL_PARSE_003`: Malformed layer expression
- `DSL_PARSE_004`: Invalid aggregation expression

**DSL Semantic Errors** (`DSL_SEM_*`):
- `DSL_SEM_001`: Unknown field (e.g., `degreee` -> suggest `degree`)
- `DSL_SEM_002`: Field not valid for target (edge field on node query)
- `DSL_SEM_003`: Measure incompatible with grouping
- `DSL_SEM_004`: UQ requested on deterministic measure
- `DSL_SEM_005`: Layer expression resolves to empty set

**Execution Errors** (`EXEC_*`):
- `EXEC_001`: Measure failed on graph backend
- `EXEC_002`: Graph too large for algorithm (soft error with alternatives)
- `EXEC_003`: Graph assumption violated (e.g., disconnected graph)
- `EXEC_004`: Randomness used without seed (warning)

**Result Interpretation Warnings** (`RES_*`):
- `RES_001`: Result empty after filters
- `RES_002`: High variance in UQ result
- `RES_003`: Aggregation hides node-level variance
- `RES_004`: Community detection produced degenerate result

**Algorithm Errors** (`ALG_*`):
- `ALG_001`: Unknown algorithm name
- `ALG_002`: Algorithm parameter invalid
- `ALG_003`: Algorithm did not converge

**I/O Errors** (`IO_*`):
- `IO_001`: File not found
- `IO_002`: Invalid file format
- `IO_003`: Missing required column

**Algorithm Requirements Errors** (`ALGO_REQ_*`):
- `ALGO_REQ_001`: Network mode incompatible (e.g., single-layer vs multiplex)
- `ALGO_REQ_002`: Replica model incompatible (strict vs partial)
- `ALGO_REQ_003`: Interlayer coupling incompatible
- `ALGO_REQ_004`: Edge weights required but missing
- `ALGO_REQ_005`: Positive weights required but not satisfied
- `ALGO_REQ_006`: Directedness incompatible
- `ALGO_REQ_007`: Random seed missing (warning)
- `ALGO_REQ_008`: UQ not supported by algorithm
- `ALGO_REQ_009`: UQ method not supported

### Algorithm Requirements & Compatibility System

**New in v1.1+**: py3plex now includes a first-class algorithm requirements system that makes multilayer/multiplex assumptions explicit and enforceable.

#### Overview

Algorithms declare their requirements (network mode, replica model, coupling type, etc.) and networks expose capabilities computed from their structure. A compatibility checker produces standardized diagnostics with actionable fixes.

**Key Components:**
1. `AlgoRequirements`: Dataclass declaring what an algorithm needs
2. `NetworkCapabilities`: Dataclass describing what a network provides
3. `check_compat()`: Compatibility checker returning diagnostics
4. `@requires`: Decorator for attaching requirements to algorithms
5. `AlgorithmCompatibilityError`: Exception with diagnostic details

#### Network Capabilities

Every network can report its capabilities:

```python
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(network_type='multiplex', directed=False)
# ... add nodes/edges ...

# Get capabilities
caps = net.capabilities()

print(f"Mode: {caps.mode}")                           # "multiplex"
print(f"Replica model: {caps.replica_model}")         # "strict" or "partial"
print(f"Coupling: {caps.interlayer_coupling}")        # "identity", "explicit_edges", etc.
print(f"Directed: {caps.directed}")                   # True/False
print(f"Weighted: {caps.weighted}")                   # True/False
print(f"Weight domain: {caps.weight_domain}")         # "positive", "binary", "real"
print(f"Layers: {caps.layer_count}")                  # Number of layers
print(f"Base nodes: {caps.base_node_count}")          # Distinct base nodes
print(f"Node replicas: {caps.node_replica_count}")    # Total node-layer pairs

# Capabilities are cached for performance
caps2 = net.capabilities()  # Reuses cached result
caps3 = net.capabilities(force_recompute=True)  # Forces recomputation

# Enhanced summary includes capabilities
summary = net.summary()
print(summary['Mode'])  # "multiplex"
```

**Network Modes:**
- `"single"`: Single-layer network
- `"multilayer"`: General multilayer (different nodes per layer)
- `"multiplex"`: Strict multiplex (same nodes across layers)
- `"temporal"`: Temporal network (time-stamped edges)

**Replica Models:**
- `"none"`: Single layer, no replica semantics
- `"partial"`: Some nodes appear in some layers (not all)
- `"strict"`: Every base node appears in every layer

**Coupling Types:**
- `"none"`: No interlayer edges
- `"identity"`: Identity coupling (node replicas connected across layers)
- `"explicit_edges"`: Explicit interlayer edges (not identity)
- `"both"`: Both identity and explicit interlayer edges

#### Algorithm Requirements

Algorithms declare their requirements using `AlgoRequirements`:

```python
from py3plex.requirements import AlgoRequirements, requires

# Define requirements
leiden_reqs = AlgoRequirements(
    allowed_modes=("multiplex",),                    # Only works on multiplex
    replica_model=("strict",),                       # Requires strict replicas
    interlayer_coupling=("identity", "both"),        # Needs identity coupling
    requires_edge_weights=False,                     # Weights optional
    requires_positive_weights=False,                 # Can handle any weights
    supports_directed=False,                         # Undirected only
    supports_undirected=True,
    uses_randomness=True,                            # Stochastic algorithm
    requires_seed_for_repro=True,                    # Seed mandatory for reproducibility
    supports_uq=False,                               # UQ not implemented yet
    expected_complexity="O(n * m) per iteration",
    memory_profile="O(n + m) for sparse networks",
    practical_limits={"max_nodes": 100000},
)

# Attach to algorithm using decorator
@requires(leiden_reqs)
def leiden_multilayer(network, **kwargs):
    # Implementation
    pass
```

**AlgoRequirements Fields:**
- `allowed_modes`: Tuple of acceptable NetworkMode values
- `replica_model`: Tuple of acceptable ReplicaModel values
- `interlayer_coupling`: Tuple of acceptable CouplingType values
- `requires_edge_weights`: Whether algorithm needs weighted edges
- `requires_positive_weights`: Whether weights must be positive (> 0)
- `supports_directed`: Whether algorithm works with directed networks
- `supports_undirected`: Whether algorithm works with undirected networks
- `uses_randomness`: Whether algorithm has stochastic components
- `requires_seed_for_repro`: Whether seed is mandatory for reproducibility
- `supports_uq`: Whether algorithm supports uncertainty quantification
- `uq_methods`: Tuple of supported UQ methods (e.g., ("bootstrap", "perturbation"))
- `expected_complexity`: Time/space complexity hint
- `memory_profile`: Memory usage profile
- `practical_limits`: Dict with size limits (e.g., {"max_nodes": 10000})

#### Compatibility Checking

The `check_compat()` function validates network-algorithm compatibility:

```python
from py3plex.requirements import check_compat

# Manual compatibility check
net_caps = net.capabilities()
diagnostics = check_compat(net_caps, leiden_reqs, algorithm_name="leiden")

# Check for errors
errors = [d for d in diagnostics if d.severity.value == 'error']
if errors:
    for error in errors:
        print(error.format())
    # Errors include fix suggestions like:
    # "Convert network: net.to_multiplex(method='intersection')"
    # "Use compatible algorithm: py3plex.algorithms.list(compatible_with=net)"

# Check for warnings
warnings = [d for d in diagnostics if d.severity.value == 'warning']
for warning in warnings:
    print(warning.format())
```

**Diagnostic Codes:**
- `ALGO_REQ_001`: Mode mismatch (e.g., single-layer passed to multiplex algorithm)
- `ALGO_REQ_002`: Replica model mismatch (e.g., partial replicas when strict required)
- `ALGO_REQ_003`: Coupling mismatch (e.g., no coupling when identity required)
- `ALGO_REQ_004`: Weights required but network unweighted
- `ALGO_REQ_005`: Positive weights required but some are negative/zero
- `ALGO_REQ_006`: Directedness mismatch
- `ALGO_REQ_007`: Seed missing (warning when algorithm uses randomness)
- `ALGO_REQ_008`: UQ requested but algorithm doesn't support it
- `ALGO_REQ_009`: UQ method not supported by algorithm

#### @requires Decorator

The `@requires` decorator automates compatibility checking:

```python
from py3plex.requirements import AlgoRequirements, requires

# Define requirements
pagerank_reqs = AlgoRequirements(
    allowed_modes=("multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
)

# Apply decorator
@requires(pagerank_reqs)
def multilayer_pagerank(network, damping=0.85, **kwargs):
    # Implementation...
    pass

# Usage
try:
    result = multilayer_pagerank(net, damping=0.85, seed=42)
except AlgorithmCompatibilityError as e:
    # Error contains diagnostics
    print(e.format_concise())  # Short summary
    print(e.format_verbose())  # Full diagnostic details
    print(e.to_dict())         # JSON-serializable dict
```

**Decorator Behavior:**
1. Checks `network.capabilities()` exists (falls back gracefully if not)
2. Validates compatibility using `check_compat()`
3. Raises `AlgorithmCompatibilityError` if any error diagnostics
4. Attaches warnings to result metadata if result has `.meta` attribute
5. Preserves function signature and docstring

#### DSL v2 Integration

Compatibility checks are automatically integrated into DSL queries:

```python
from py3plex.dsl import Q

# Compatibility checked during execution
try:
    result = (
        Q.communities("leiden")
         .with_params(resolution=1.0, seed=42)
         .execute(net)
    )
except AlgorithmCompatibilityError as e:
    # Diagnostic details in exception
    print(e.format_verbose())

# Warnings attached to result
result = Q.nodes().compute("pagerank").execute(net)
if "diagnostics" in result.meta:
    for diag in result.meta["diagnostics"]:
        print(f"{diag['severity']}: {diag['message']}")

# Explain shows diagnostics
print(result.explain())
# Output includes:
# Diagnostics:
#   warning[ALGO_REQ_007]: Algorithm uses randomness but no seed provided
#     Fix: Pass seed=42 parameter
```

**DSL Diagnostic Integration:**
- `QueryResult.meta["diagnostics"]`: List of diagnostic dicts
- `result.explain()`: Displays diagnostics with colored output
- Errors prevent execution, warnings allow execution

#### AlgorithmCompatibilityError

Exception for algorithm incompatibilities:

```python
from py3plex.requirements import AlgorithmCompatibilityError

try:
    result = leiden_multilayer(single_layer_net)
except AlgorithmCompatibilityError as e:
    # Human-readable
    print(str(e))
    # "Algorithm 'leiden_multilayer' is incompatible with network: 2 error(s)"
    
    # Concise format (for CLI)
    print(e.format_concise())
    # Shows top 2 errors + fix suggestions
    
    # Verbose format (for --verbose)
    print(e.format_verbose())
    # Shows all diagnostics with full details
    
    # JSON export (for LLMs)
    error_dict = e.to_dict()
    # {
    #   "error": "AlgorithmCompatibilityError",
    #   "algorithm": "leiden_multilayer",
    #   "diagnostics": [...],
    #   "summary": {"errors": 2, "warnings": 0}
    # }
    
    # Access diagnostics
    for diag in e.diagnostics:
        print(f"{diag.code}: {diag.message}")
        for fix in diag.fixes:
            print(f"  Fix: {fix.description}")
```

#### Instrumented Algorithms

**Community Detection:**
- `leiden_multilayer()`: Requires multiplex with strict replicas

**Centrality:**
- `MultilayerCentrality.pagerank_centrality()`: Supports multilayer/multiplex

**Dynamics:**
- `SISDynamics`: Supports single/multilayer/multiplex, requires seed

**More algorithms** will be instrumented in future releases.

#### Best Practices

1. **Always set seeds** for stochastic algorithms:
   ```python
   result = leiden_multilayer(net, seed=42)
   ```

2. **Check capabilities** before running algorithms:
   ```python
   caps = net.capabilities()
   print(f"Network is {caps.mode} with {caps.replica_model} replicas")
   ```

3. **Handle compatibility errors** gracefully:
   ```python
   try:
       result = algorithm(net)
   except AlgorithmCompatibilityError as e:
       # Try suggested fix
       if "to_multiplex" in e.diagnostics[0].fixes[0].replacement:
           net_multiplex = net.to_multiplex(method='intersection')
           result = algorithm(net_multiplex)
   ```

4. **Use query-level UQ** to propagate requirements:
   ```python
   result = Q.nodes().compute("betweenness").uq(method="bootstrap", seed=42).execute(net)
   ```

5. **Inspect diagnostics** in results:
   ```python
   if result.meta.get("diagnostics"):
       print(result.explain())  # Shows diagnostics
   ```

### Query Result Inspection

Use `.explain()` and `.debug()` to understand query execution:

#### `.explain()` - Human-Readable Summary

```python
from py3plex.dsl import Q, L

result = (
    Q.nodes()
     .from_layers(L["social"])
     .compute("degree", "betweenness_centrality")
     .where(degree__gt=5)
     .execute(net)
)

print(result.explain())
```

**Output**:
```
Query Explanation
============================================================

Target: nodes
Results: 42 items

Layers: social

Computed metrics:
  - degree
  - betweenness_centrality

Diagnostics:
warning[RES_003]: Aggregation may hide variance
  Cause: Using mean aggregation on heterogeneous data
  Fix 1: Check per-node results before aggregating
    .to_pandas().describe()

Suggested next steps:
  - Group by layer: .per_layer()
  - Add uncertainty: .uq(method='bootstrap', n_samples=100)
  - Export to CSV: .to_pandas().to_csv('results.csv')
```

#### `.debug()` - Technical Details

```python
print(result.debug())
```

**Output**:
```
Query Debug Information
============================================================

Target: nodes
Result count: 42

AST Structure:
{
  "target": "nodes",
  "layer_expr": {"type": "literal", "layers": ["social"]},
  "where_clause": {"field": "degree", "op": ">", "value": 5}
}

Timing:
  parse: 0.001s
  execute: 0.050s
  compute_degree: 0.020s
  compute_betweenness: 0.025s
  total: 0.051s

Cache Statistics:
  Hits: 10
  Misses: 2
  Hit rate: 83.3%

Random Seeds:
  bootstrap: 42
```

### Exception Integration

All DSL errors include diagnostic objects:

```python
from py3plex.dsl import Q
from py3plex.dsl.errors import UnknownMeasureError

try:
    result = Q.nodes().compute("betweennes").execute(net)  # Typo
except UnknownMeasureError as e:
    # Access structured diagnostic
    diag = e.to_diagnostic()
    print(diag.to_json())
    
    # Get "did you mean?" suggestion
    if e.suggestion:
        print(f"Did you mean '{e.suggestion}'?")
    
    # Auto-correct for LLM
    correct_measure = e.suggestion
    result = Q.nodes().compute(correct_measure).execute(net)
```

### LLM-Friendly Error Recovery

Diagnostics are designed for automated recovery:

```python
import json

try:
    result = Q.nodes().compute("unknownmeasure").execute(net)
except Exception as e:
    if hasattr(e, 'to_diagnostic'):
        diag = e.to_diagnostic()
        
        # Parse diagnostic JSON
        diag_dict = json.loads(diag.to_json())
        
        # Extract suggestion
        if diag_dict.get('fixes'):
            suggested_fix = diag_dict['fixes'][0]
            replacement = suggested_fix.get('replacement')
            
            # Retry with suggested fix
            if replacement:
                result = Q.nodes().compute(replacement).execute(net)
```

### Best Practices

1. **Always check suggestions**: DSL errors include "did you mean?" suggestions - use them
2. **Export diagnostics for debugging**: Use `.to_json()` for stable, parseable output
3. **Use `.explain()` early**: Call on first result to understand query behavior
4. **Enable `.debug()` for performance issues**: Shows timing and cache statistics
5. **Handle warnings**: `DiagnosticSeverity.WARNING` indicates potential issues, not errors

### Testing Error Messages

Use snapshot tests for stable error messages:

```python
import pytest

def test_unknown_field_error():
    from py3plex.dsl.errors import UnknownAttributeError
    
    error = UnknownAttributeError(
        attribute="degreee",
        known_attributes=["degree", "betweenness_centrality"]
    )
    
    diag = error.to_diagnostic()
    
    # Verify stable error code
    assert diag.code == "DSL_SEM_001"
    
    # Verify suggestion
    assert diag.fixes[0].replacement == "degree"
    
    # Snapshot JSON for LLM compatibility
    snapshot = diag.to_json()
    # Compare against golden file
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
-  `FileNotFoundError` ->  `Py3plexIOError`
-  `ValueError` ->  `NetworkConstructionError`

---

## Query Planner and Optimization

### Overview

The DSL v2 query planner is an internal optimization layer that sits between AST compilation and execution. It automatically:

1. **Reorders stages** to reduce execution cost (filter early, compute late)
2. **Pushes down computations** to compute only measures needed downstream
3. **Caches expensive results** keyed by stable identifiers + provenance
4. **Provides execution plans** via `explain_plan()` for debugging and optimization
5. **Ensures determinism** - same network + AST + params + seed -> same plan and results

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

**Same input -> Same plan -> Same results**

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

## Query Algebra, Canonicalization, Equivalence

py3plex DSL v2 includes a built-in **query equivalence engine** that lets you
test whether two queries are semantically equivalent, normalise queries to a
canonical form, and obtain a stable hash for equivalent queries.

### Scopes

Two scopes control what counts as equivalent:

- **`"relational"`** (default): Standard relational-algebra equivalence.
  `order_by` is treated as **semantic** in py3plex (it affects result ordering),
  so queries that differ in ordering direction are *not* equivalent.
- **`"strict"`**: Same as relational but additionally deduplicates repeated
  `order_by` items (R8).

### `Query.canonical(scope="relational")`

Returns a new `QueryBuilder` whose internal AST is in canonical normal form.
Canonicalization is **deterministic** and **idempotent**:

```python
q = Q.nodes().where(layer="social", degree__gt=5)
c1 = q.canonical()
c2 = c1.canonical()
assert c1.canonical_ast_hash == c2.canonical_ast_hash   # idempotent
```

Rules applied: R1/R2 (merge/deduplicate where), R3 (normalise predicates),
R5 (intersect consecutive from_layers), R8 (dedup order_by — strict only),
R9 (fold stacked limit).

### `Query.equivalent_to(other, scope="relational", explain=False)`

Returns `True` if two queries are semantically equivalent:

```python
q1 = Q.nodes().where(degree__gt=5).where(layer="social")
q2 = Q.nodes().where(layer="social", degree__gt=5)
assert q1.equivalent_to(q2)   # True
```

Pass `explain=True` for a `(bool, proof)` tuple:

```python
eq, proof = q1.equivalent_to(q2, explain=True)
# proof["self_proof"]  → ["R2:where_idempotence", "R3:predicate_normalization"]
# proof["other_proof"] → ["R3:predicate_normalization"]
# proof["diff"]        → None  (queries are equivalent)
```

### `Query.canonical_ast_hash`

Stable SHA-256 hex hash of the canonical AST.  Equivalent queries always share
the same hash; non-equivalent queries produce different hashes:

```python
q1 = Q.nodes().where(degree__gt=5, layer="social")
q2 = Q.nodes().where(layer="social").where(degree__gt=5)
assert q1.canonical_ast_hash == q2.canonical_ast_hash

q3 = Q.nodes().where(degree__gt=10)   # different threshold
assert q1.canonical_ast_hash != q3.canonical_ast_hash
```

> **Caching note**: The existing `query.ast_hash` is unchanged and operates on the
> raw un-normalised AST.  The new `canonical_ast_hash` uses the normalised form and
> is more stable for cache keys when query construction order varies.

### Implementation

The engine extends `canonicalize_ast` in `py3plex/dsl/ast.py`.  The scope-aware
entry point is `canonicalize_ast_scoped(query_ast, scope)`, which returns a
`(canonical_query_ast, proof_list)` pair.  Tests live in
`tests/test_query_equivalence.py`.

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
print(prov['py3plex_version'])    # "1.1.3"
print(prov['timestamp_utc'])      # ISO8601 timestamp
print(prov['network_fingerprint']) # Node/edge counts, layers
print(prov['query']['ast_hash'])  # Stable hash of query AST
print(prov['randomness']['seed']) # Random seed if used
print(prov['performance']['total_ms']) # Execution time
```

**Correctness verification**:
- **AST hash stability**: Identical queries produce identical AST hashes [CORRECT] (tested)
- **Reproducibility expectations**: Same AST hash + seed + network -> same results [CORRECT]
- **Provenance presence**: All DSL v2 results include provenance metadata [CORRECT] (verified in tests)

**Usage in verification**:
```python
# Verify AST stability
q1 = Q.nodes().compute("degree")
q2 = Q.nodes().compute("degree")
assert q1.to_ast() == q2.to_ast()  # [CORRECT] Structurally identical

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

**Current Coverage** (as of v1.1.3 + comprehensive verification):
- [CORRECT] **Provenance-as-Oracle**: AST hash stability, network fingerprinting, performance tracking (26 tests)
- [CORRECT] **Differential Testing**: Legacy DSL vs DSL v2 vs graph_ops equivalence (22 tests)
- [CORRECT] **Metamorphic Harness**: Relabeling, layer permutation, edge order, weight scaling, isolated nodes (19 tests)
- [CORRECT] **Determinism & Parallelism**: UQ, null models, seed propagation, n_jobs invariance (16 tests)
- [CORRECT] **Centrality measures**: Full metamorphic invariance tests (17 tests)
- [CORRECT] **Community detection**: Certificate-based validation (7 tests)
- [CORRECT] **DSL v2**: Provenance and metadata checks
- [WARNING] Path algorithms: Basic tests (not yet comprehensive)
- [WARNING] Dynamics simulations: Determinism tests (not yet metamorphic)

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
  - Degree centrality [CORRECT]
  - Betweenness centrality [CORRECT]
  - PageRank [CORRECT]
  - Closeness centrality [CORRECT]
- **Layer permutation invariance**: Layer ordering doesn't affect results [CORRECT]
- **Edge order invariance**: Edge insertion order doesn't matter [CORRECT]
- **Finiteness**: All values are finite (no NaN/inf) [CORRECT]
- **PageRank normalization**: Values sum to ≈1.0 within 1e-6 tolerance [CORRECT]

**Community detection** (7 certificate tests):
- **Partition validity**: Every node assigned exactly once [CORRECT]
- **No empty communities**: All communities have at least one member [CORRECT]
- **Modularity certificate**: Recomputed modularity matches and is within bounds [-0.5, 1.0] [CORRECT]
- **Determinism**: Same seed produces identical partitions [CORRECT]
- **Expected structure**: Known structures (e.g., two cliques with bridge) produce reasonable community counts [CORRECT]
- **Relabel equivalence**: Relabeling produces same partition structure (same modularity) [CORRECT]

**DSL v2**:
- **Provenance presence**: All results include provenance metadata [CORRECT]
- **AST stability**: Identical queries produce identical AST representations [CORRECT]

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
# Should select same nodes [CORRECT] (tested where feasible)

# Computed measures (when supported)
legacy_result = execute_query(net, "SELECT nodes COMPUTE degree")
v2_result = Q.nodes().compute("degree").execute(net)
# Should produce same degree values [CORRECT]
```

**Skipped tests**: 9 differential tests are skipped because legacy DSL doesn't support:
- Layer filtering with `FROM` clause (inconsistent syntax)
- Degree filtering with `WHERE degree > N`
- Betweenness/PageRank computation
- Edge selection with `intralayer=True`
- Ordering with `ORDER BY`

**DSL v2 advantages verified**:
- [CORRECT] Richer provenance metadata
- [CORRECT] Stable AST representation
- [CORRECT] Type safety and IDE autocomplete
- [CORRECT] Chainable builder API

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
assert partition1 == partition2  # [CORRECT] Identical

# Uncertainty quantification with seed
result1 = Q.nodes().compute("betweenness").uq(method="bootstrap", n_samples=100, seed=42).execute(net)
result2 = Q.nodes().compute("betweenness").uq(method="bootstrap", n_samples=100, seed=42).execute(net)
# Confidence intervals should be identical [CORRECT]

# Null model generation with seed
null1 = configuration_model(net, seed=123)
null2 = configuration_model(net, seed=123)
# Should produce identical null networks [CORRECT]
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
- [ERROR] Path algorithms: Only basic tests, no comprehensive metamorphic tests
- [ERROR] Null models: Certificate tests not yet comprehensive
- [ERROR] Dynamics simulations: Determinism tested, but not metamorphic properties
- [ERROR] Temporal network algorithms: No verification tests yet
- [ERROR] Graph operations (graph_ops): No differential tests vs DSL v2
- [ERROR] CLI vs Python API: No differential tests
- [ERROR] py3plex vs NetworkX: No cross-implementation comparison tests

**What is partially covered**:
- [WARNING] DSL v2 vs Legacy DSL: 9 tests skipped due to legacy DSL limitations
- [WARNING] Community detection: Strong certificate tests, but stability envelope tests not yet comprehensive

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

### Comprehensive Verification Test Suite (v1.1.3+)

py3plex now includes a comprehensive verification test framework spanning 105+ tests across 4 dedicated verification modules. This framework implements the principles of **provenance-as-oracle**, **differential testing**, **metamorphic transformation**, and **determinism enforcement**.

#### Test Module Overview

**test_verification_provenance_oracles.py** (26 tests):
Foundational provenance-based verification:
- **AST Hash Stability**: Identical queries → identical AST hashes across multiple executions
- **Network Fingerprinting**: Network mutations detected via fingerprint changes
- **Performance Tracking**: Timing metadata present and within reasonable bounds
- **Randomness Metadata**: Seed tracking, provenance warnings for non-deterministic ops
- **Versioning**: py3plex version, engine type, timestamps recorded

**test_verification_api_differential.py** (22 tests):
Cross-API equivalence testing:
- **Legacy DSL vs DSL v2**: Node/edge selection, metric computation (degree, betweenness, pagerank)
- **DSL v2 vs graph_ops**: Node selection, filtering, metric computation
- **Aggregation Consistency**: Mean, median, quantile produce correct values
- **Grouping Logic**: per_layer(), per_layer_pair() metadata correct
- **Ordering & Limiting**: order_by(), limit() semantics consistent

**test_verification_metamorphic_harness.py** (19 tests):
Reusable transformation framework:
- **Relabeling Invariance**: Degree, betweenness, pagerank, DSL queries preserve multisets
- **Layer Permutation Invariance**: Global distributions preserved, per-layer groups permute correctly
- **Edge Order Invariance**: Results identical regardless of edge insertion order
- **Weight Scaling**: Unweighted metrics invariant, weighted metrics predictable
- **Isolated Nodes**: Adding isolated nodes doesn't affect existing node metrics
- **Transformation Composition**: Composing transformations preserves invariants

**test_verification_determinism_parallelism.py** (16 tests):
Stochastic algorithm reproducibility:
- **UQ Determinism**: Same seed → identical bootstrap results, different seeds → different results
- **Parallelism Invariance**: n_jobs ∈ {1, 2} produces identical results with fixed seed
- **Null Models**: Same seed → identical structure, different seeds → different graphs
- **Community Detection**: Leiden/Louvain deterministic with random_state
- **Seed Propagation**: Seeds correctly propagated through call stacks
- **No Global RNG**: Results independent of numpy's global random state

#### Verification Principles for AI Agents

When working with py3plex, AI agents should reason about correctness using these principles:

**1. Provenance-as-Oracle**:
```python
# Always check provenance after query execution
result = Q.nodes().compute("degree").execute(net)
prov = result.meta["provenance"]

# Verify AST hash stability for reproducibility
assert prov["query"]["ast_hash"] is not None

# Check network fingerprint for debugging
assert prov["network_fingerprint"]["node_count"] > 0

# Use performance timings for optimization
assert prov["performance"]["total_ms"] >= 0
```

**2. Differential Validation**:
```python
# When in doubt, compare across APIs
legacy_result = execute_query(net, "SELECT nodes COMPUTE degree")
v2_result = Q.nodes().compute("degree").execute(net)

# Extract and compare sorted values
legacy_degrees = sorted(legacy_result["computed"]["degree"].values())
v2_degrees = sorted(v2_result.to_pandas()["degree"].tolist())
assert legacy_degrees == v2_degrees  # Should match
```

**3. Metamorphic Validation**:
```python
# Test your own code using transformations
from tests.fixtures import relabel_nodes

# Original computation
original_centrality = net.monoplex_nx_wrapper("degree_centrality")
original_values = sorted(original_centrality.values())

# Relabel and recompute
mapping = {node: f"renamed_{node}" for node in net.get_nodes()}
relabeled_net = relabel_nodes(net, mapping)
relabeled_centrality = relabeled_net.monoplex_nx_wrapper("degree_centrality")
relabeled_values = sorted(relabeled_centrality.values())

# Should be identical (multiset equality)
assert original_values == relabeled_values
```

**4. Determinism Enforcement**:
```python
# Always use seeds for stochastic operations
result1 = Q.nodes().compute("degree").uq(
    method="bootstrap", n_samples=100, seed=42, n_jobs=1
).execute(net)

result2 = Q.nodes().compute("degree").uq(
    method="bootstrap", n_samples=100, seed=42, n_jobs=2  # Different n_jobs
).execute(net)

# Results should be identical despite different n_jobs
df1 = result1.to_pandas()
df2 = result2.to_pandas()
assert (df1["degree_mean"] - df2["degree_mean"]).abs().max() < 1e-6
```

#### Verified Invariants Reference

**Centrality Invariants**:
- Relabel invariance: Node naming doesn't affect value distributions
- Layer permutation invariance: Layer ordering doesn't affect global results
- Edge order invariance: Edge insertion order irrelevant
- Finiteness: All values are finite (no NaN/inf)
- PageRank normalization: Sum to 1.0 ± 1e-6

**Community Detection Invariants**:
- Partition validity: All nodes assigned exactly once
- No empty communities
- Modularity bounds: -0.5 ≤ Q ≤ 1.0
- Determinism: Same seed → identical partition
- Relabel equivalence: Relabeling preserves modularity

**UQ Invariants**:
- Seed determinism: Same seed → identical CI/std/mean
- Parallelism invariance: n_jobs doesn't affect seeded results
- Statistical distinguishability: Different seeds → different estimates

**Null Model Invariants**:
- Degree sequence preservation (configuration model)
- Layer preservation
- Node count preservation per layer
- Determinism under fixed seed

#### Coverage Map (Subsystem-by-Subsystem)

| Subsystem | Unit Tests | Integration Tests | Metamorphic Tests | Differential Tests |
|-----------|------------|-------------------|-------------------|-------------------|
| **DSL v2** |  Extensive |  Yes |  Yes |  vs Legacy DSL |
| **Legacy DSL** |  Basic |  Yes |  No |  vs DSL v2 |
| **graph_ops** |  Basic |  Yes |  No |  vs DSL v2 |
| **Centrality** |  Extensive |  Yes |  Comprehensive |  No (planned vs NetworkX) |
| **Community Detection** |  Extensive |  Yes |  Yes |  No |
| **Null Models** |  Yes |  Yes |  Basic |  No |
| **UQ/Bootstrap** |  Yes |  Yes |  No |  No |
| **Dynamics** |  Yes |  Yes |  No (planned) |  No |
| **Temporal** |  Basic |  Yes |  No (planned) |  No |
| **I/O** |  Yes |  Roundtrip tests |  No |  No |
| **CLI** |  Yes |  Yes |  No |  No |
| **Pipeline** |  Yes |  Yes |  No |  No |

**Legend**:
-  = Implemented
-  = Not yet implemented
- "Extensive" = >20 tests
- "Yes" = 5-20 tests
- "Basic" = <5 tests

#### When to Add Verification Tests

**Add metamorphic tests when**:
- Implementing new centrality measures
- Adding new community detection algorithms
- Implementing new graph transformations
- Adding new aggregation functions

**Add differential tests when**:
- Implementing functionality that has equivalent across APIs (DSL v2, Legacy DSL, graph_ops)
- Wrapping external libraries (NetworkX, igraph, etc.)
- Implementing alternative backends for same operation

**Add determinism tests when**:
- Adding stochastic algorithms (community detection, sampling, UQ)
- Implementing parallel execution paths
- Using random number generators

**Add provenance tests when**:
- Modifying query execution engines
- Changing AST representation
- Adding new metadata fields

---


## Multilayer Semantics Guide

This section provides operational guidance on multilayer network semantics for LLM agents. Understanding these concepts is critical for generating correct py3plex code.

### Core Mental Model

**Multilayer Network = Node Replicas + Supra-Adjacency Matrix**

```
Physical nodes: {Alice, Bob, Carol}
Layers: {social, work, family}

Node replicas: 
  (Alice, social), (Alice, work), (Alice, family),
  (Bob, social), (Bob, work), (Bob, family),
  (Carol, social), (Carol, work), (Carol, family)

Total: 3 physical nodes × 3 layers = 9 node replicas
```

**Key insight**: Most py3plex operations work on **node replicas**, not physical nodes.

### Semantic Issue 1: Node Counts

**Problem**: User expects node count to match physical nodes, gets replicas instead.

```python
# Network: 100 physical nodes across 3 layers
net = multinet.multi_layer_network()
# ... load data ...

result = Q.nodes().execute(net)
print(result.count)  # Returns 300, not 100!
```

**LLM agent decision rule**:
```
IF user asks "how many nodes are in the network?"
THEN clarify:
  - Physical nodes: len(set(n[0] for n in network.get_nodes()))
  - Node replicas: len(network.get_nodes())
  - Default py3plex operations return replicas
```

**Correct patterns**:
```python
# [CORRECT] Get physical node count
replicas = Q.nodes().execute(net).items
physical_nodes = len(set(n[0] for n in replicas))

# [CORRECT] Work per-layer (avoids ambiguity)
result = Q.nodes().per_layer().execute(net)
# Now each group is one layer

# [CORRECT] Filter to single layer
result = Q.nodes().from_layers(L["social"]).execute(net)
# Now result.count = physical nodes in social layer
```

### Semantic Issue 2: Degree Ambiguity

**Problem**: "Degree" has three meanings in multilayer networks.

1. **Intra-layer degree**: Edges within the same layer
2. **Inter-layer degree**: Edges to other layers (coupling)
3. **Aggregate degree**: Total degree (intra + inter)

**py3plex default**: Aggregate degree (most common use case).

**LLM agent decision rule**:
```
IF user asks to compute "degree"
THEN:
  1. Check if network is multilayer (>1 layer)
  2. IF multilayer:
       Ask: "Which degree do you want?"
         - Aggregate (default): Q.nodes().compute("degree")
         - Per-layer: Q.nodes().per_layer().compute("degree")
         - Specific layer: Q.nodes().from_layers(L["social"]).compute("degree")
  3. ELSE (single layer):
       Standard degree: Q.nodes().compute("degree")
```

**Correct patterns**:
```python
# [CORRECT] Explicit aggregate degree (default)
result = Q.nodes().compute("degree").execute(net)
# Add comment: "Computing aggregate degree (intra + inter)"

# [CORRECT] Per-layer degree (independent per layer)
result = Q.nodes().per_layer().compute("degree").execute(net)

# [CORRECT] Specific layer degree
result = Q.nodes().from_layers(L["social"]).compute("degree").execute(net)
```

### Semantic Issue 3: Coverage Filters

**Problem**: Coverage filters remove more nodes than expected.

```python
# 5-layer network, top-10 hubs per layer
result = (
    Q.nodes()
     .per_layer()
     .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="all")  # Keep nodes in ALL 5 layers
     .execute(net)
)
# Might return 0-2 nodes if few nodes are top-10 in ALL layers!
```

**Coverage mode semantics**:
- `mode="all"`: Intersection (STRICT — keeps items in ALL groups)
- `mode="any"`: Union (PERMISSIVE — keeps items in ANY group)
- `mode="at_least", k=N`: Items in at least N groups
- `mode="fraction", p=0.X`: Items in at least X% of groups

**LLM agent decision rule**:
```
IF user asks for "nodes present across layers"
THEN clarify:
  - ALL layers (intersection): coverage(mode="all")
  - ANY layer (union): coverage(mode="any")
  - At least N layers: coverage(mode="at_least", k=N)
  - At least X% of layers: coverage(mode="fraction", p=0.X)

DEFAULT: Use mode="at_least" or mode="fraction" (middle ground)
AVOID: mode="all" unless user explicitly wants strict intersection
```

**Correct patterns**:
```python
# [CORRECT] Balanced: nodes in at least 60% of layers
result = (
    Q.nodes()
     .per_layer()
     .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="fraction", p=0.6)
     .execute(net)
)

# [CORRECT] Moderate: nodes in at least 2 layers
result = (
    Q.nodes()
     .per_layer()
     .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="at_least", k=2)
     .execute(net)
)

# [WARNING] Strict: only use if user explicitly wants intersection
result = (
    Q.nodes()
     .per_layer()
     .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="all")  # Very strict!
     .execute(net)
)
```

### Semantic Issue 4: Global vs Per-Layer Operations

**Problem**: User doesn't specify whether operation should span layers or operate per-layer.

**LLM agent decision rule**:
```
IF operation is on multilayer network (>1 layer)
THEN ask:
  "Should this operate globally (across all layers) or per-layer (independently)?"

Common operations:
  - Community detection:
      Global: Q.nodes().community(method="leiden", omega=0.8).execute(net)
      Per-layer: Q.nodes().per_layer().community(method="leiden").end_grouping().execute(net)
  
  - Centrality:
      Global/Aggregate: Q.nodes().compute("betweenness_centrality").execute(net)
      Per-layer: Q.nodes().per_layer().compute("betweenness_centrality").execute(net)
  
  - Top-k nodes:
      Global: Q.nodes().compute("degree").order_by("-degree").limit(10).execute(net)
      Per-layer: Q.nodes().per_layer().top_k(10, "degree").execute(net)
```

**Correct patterns**:
```python
# [CORRECT] Explicit global (aggregate metrics)
result = (
    Q.nodes()
     .compute("betweenness_centrality")  # Aggregate across layers
     .order_by("-betweenness_centrality")
     .limit(10)
     .execute(net)
)

# [CORRECT] Explicit per-layer (independent analysis)
result = (
    Q.nodes()
     .per_layer()
     .compute("betweenness_centrality")  # Per-layer betweenness
     .top_k(10, "betweenness_centrality")
     .end_grouping()
     .execute(net)
)

# [CORRECT] Specific layer (unambiguous)
result = (
    Q.nodes()
     .from_layers(L["social"])
     .compute("betweenness_centrality")
     .execute(net)
)
```

### Decision Flow for LLM Agents

When user asks to analyze multilayer network:

```
1. CHECK: Is network multilayer? (>1 layer)
   ├─ NO -> Use standard single-layer patterns
   └─ YES -> Continue to step 2

2. CLARIFY: Operation scope
   ├─ User specifies layer (e.g., "in social layer") -> Use .from_layers(L[...])
   ├─ User says "across layers" / "global" -> Use global operations
   ├─ User says "per layer" / "each layer" -> Use .per_layer()
   └─ User doesn't specify -> ASK or default to per-layer (safer)

3. CHECK: Metric ambiguity
   ├─ Degree computation -> Clarify: aggregate, per-layer, or specific layer?
   ├─ Community detection -> Clarify: global communities or per-layer?
   └─ Other metrics -> Default to aggregate, document assumption

4. VALIDATE: Node count interpretation
   ├─ If user mentions "N nodes" -> Clarify: physical nodes or replicas?
   ├─ If filtering -> Warn about potential replica count surprises
   └─ Document: "This returns X node replicas (Y physical nodes across Z layers)"

5. COVERAGE: If using .per_layer() with post-grouping filters
   ├─ Default to mode="at_least" or mode="fraction"
   ├─ Avoid mode="all" unless explicitly requested
   └─ Document expected filtering behavior
```

### Common Multilayer Query Patterns

**Pattern 1: Cross-layer hub identification**
```python
# Find nodes that are hubs in multiple layers
result = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
       .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="at_least", k=2)  # In ≥2 layers
     .execute(net)
)
```

**Pattern 2: Layer-specific analysis**
```python
# Analyze specific layer
result = (
    Q.nodes()
     .from_layers(L["social"])
     .compute("degree", "betweenness_centrality")
     .order_by("-betweenness_centrality")
     .limit(20)
     .execute(net)
)
```

**Pattern 3: Per-layer aggregation**
```python
# Compare layers by average metrics
result = (
    Q.nodes()
     .per_layer()
     .compute("degree", "clustering")
     .aggregate("mean", "std")
     .execute(net)
)
```

**Pattern 4: Global multilayer community detection**
```python
# Communities spanning layers
result = (
    Q.nodes()
     .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
     .execute(net)
)
# omega controls inter-layer coupling strength
```

**Pattern 5: Per-layer community detection**
```python
# Independent communities per layer
result = (
    Q.nodes()
     .per_layer()
     .community(method="leiden", gamma=1.2, random_state=42)
     .end_grouping()
     .execute(net)
)
```

### Summary for LLM Agents

**Always clarify**:
1. Physical nodes vs node replicas
2. Aggregate vs per-layer metrics
3. Global vs per-layer operations
4. Coverage mode for cross-layer filters

**Always document**:
1. Which degree type is being computed
2. Whether operation is global or per-layer
3. Expected node counts (replicas vs physical)

**Always validate**:
1. User intent matches query semantics
2. Coverage filters don't over-filter
3. Metric interpretations are multilayer-aware

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

**Problem**: Layer algebra that matches no layers -> empty result

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

### Current Test Coverage State (Updated: March 2026)

**Overall Coverage**: ~14.7% (8,003 of 54,588 statements covered)

**Note**: Test coverage has significantly improved from 8% to 14.7% through focused testing efforts on core modules, utilities, and validation. While this is still relatively low overall, it reflects that py3plex is a mature library with extensive functionality. Test coverage focuses on core algorithms, DSL functionality, and critical infrastructure.

**Recent Test Improvements**:
- **210+ new comprehensive tests added** for previously untested modules:
  - `test_core_schema_validation.py` - 16 tests for FieldValidator and ValidationError
  - `test_core_lazy_evaluation.py` - 15 tests for LazyProperty and CacheManager  
  - `test_core_immutable.py` - 15 tests for ImmutableNetworkView
  - `test_compat_exceptions.py` - 19 tests for CompatibilityError, SchemaError, ConversionNotSupportedError
  - `test_parallel.py` - 19 tests for spawn_seeds, parallel_map, deterministic execution
  - `test_temporal_utils_extended.py` - 40 tests for duration parsing and formatting
  - `test_algorithms_random_generators.py` - 21 tests for BA, ER, and SBM multilayer generators
  - `test_algorithms_attribute_correlation.py` - 23 tests for attribute-centrality correlation
  - `test_visualization_benchmark.py` - 35 tests added/enhanced for benchmark plotting
  - `test_dsl_uq_propagation.py` - 7 tests for UQ propagation semantics
- **AGENTS.md Validation Tests**:
  - `test_agents_golden_paths.py` - Validates 5 Golden Path examples from AGENTS.md (8 tests)
  - `test_agents_ergonomics_features.py` - Tests v1.1+ ergonomics features (.hint(), introspection, warnings) (14 tests)

#### Modules with High Coverage (>70%):
- `__init__.py` - 100%
- `config.py` - 84.2%
- `logging_config.py` - 66.7%

#### Modules with Moderate Coverage (20-70%):
- `exceptions.py` - 40.9% (exception hierarchy)
- `errors.py` - 31.8% (error handling)
- `dsl` - 23.5% (DSL queries, 3,465/4,531 statements uncovered)
- `graph_ops.py` - 22.6% (graph operations)
- `pipeline.py` - 21.7% (pipeline API)
- `uncertainty` - 21.3% (UQ framework)
- `plugins` - 20.7% (plugin system)

#### Modules Previously at 0% Now with Comprehensive Tests:
-  `core/schema_validation.py` - 16 tests added (field validation)
-  `core/lazy_evaluation.py` - 15 tests added (lazy properties & caching)
-  `core/immutable.py` - 15 tests added (immutable network views)
-  `compat/exceptions.py` - 19 tests added (compatibility exceptions)
-  `_parallel.py` - 19 tests added (parallel execution & seed spawning)
-  `temporal_utils_extended.py` - 40 tests added (duration parsing & formatting)
-  `algorithms/advanced_random_generators.py` - 21 tests added (BA, ER, SBM generators)
-  `algorithms/attribute_correlation.py` - 23 tests added (attribute-centrality correlation)

#### Remaining Gaps (modules with tests but reported lower coverage):
- `cli.py` - 70.2% (1,618 statements) - **Has 79 comprehensive tests** in test_cli.py
- `io/` module - **Has 8 test files** covering I/O operations
- `utils.py` - 37.1% (124 statements) - **Has 4 test files** covering utilities
- `validation.py` - 82.6% (121 statements) - **Has 2 test files** covering validation
- `nullmodels` - **Has 6 test files** covering null models
- `dsl_legacy.py` - 8.5% (860 statements) - **Has tests** in test_dsl_legacy_edges.py
- `paths` - Path algorithms (lower priority)
- `stats` - Statistics module (lower priority)
- `temporal_utils.py` - 100% (62 statements) - Basic temporal utilities
- `visualization` - 6.7% → **improved** with 35 new/enhanced tests - Visualization utilities (large module)
- `algorithms` - 1.1% → **improved** with 44 new tests - Algorithm implementations (many specialized)
- `dynamics` - 19.0% (1,366 statements) - **Has extensive tests** (39+ test functions across multiple files)

**Coverage Reporting Files**:
- `coverage_full.json` - Complete coverage data (appears to be from partial test run)
- `coverage_broader.json` - Alternative coverage report

### Test Organization

**Test Suite Statistics**:
- **Total test files**: 539 test_*.py files (553 total Python files in tests/)
- **DSL test files**: 76 files covering DSL v2, legacy DSL, and related features
- **Verification test files**: 10 files with formal correctness guarantees
- **Property-based test files**: 113 files in `tests/property/` using Hypothesis

**Test Categories**:

#### 1. DSL Tests (76 files)
Core DSL v2 functionality, query building, execution, and exports:
- `test_dsl_v2.py` - DSL v2 core builder API
- `test_dsl.py` - Legacy DSL string-based queries
- `test_dsl_executor_*.py` - Query execution engine
- `test_dsl_ast_equivalence.py` - AST stability (21 tests)
- `test_dsl_graphops_equivalence.py` - DSL ↔ graph_ops semantic equivalence (13 tests)
- `test_dsl_aggregation_*.py` - Grouping and aggregation
- `test_dsl_community_*.py` - Community detection integration
- `test_dsl_compositional_uq.py` - UQ composition
- `test_dsl_dynamics_integration.py` - Dynamics simulation integration
- `test_dsl_edge_*.py` - Edge queries and grouping
- `test_dsl_ergonomics.py` - Ergonomics features (.hint(), introspection)
- `test_dsl_errors*.py` - Error handling and diagnostics
- `test_dsl_explain.py` - Query explanation
- `test_dsl_export.py` - Result export (pandas, NetworkX, Arrow)
- `test_dsl_expressions.py` - Field expressions (F.field > value)
- `test_dsl_grouping_coverage.py` - Coverage filtering
- `test_dsl_layer_*.py` - Layer algebra (L["a"] + L["b"])
- `test_dsl_planner.py` - Query optimization
- `test_dsl_provenance.py` - Provenance tracking
- `test_dsl_semiring_integration.py` - Semiring algebra integration
- `test_dsl_temporal_*.py` - Temporal network queries
- `test_dsl_uncertainty.py` - UQ integration
- `test_dsl_patterns.py` - Pattern matching
- `test_dsl_documentation_examples.py` - Documentation code snippets

**NEW: AGENTS.md Documentation Validation**:
- `test_agents_golden_paths.py` - Validates 5 Golden Path examples from AGENTS.md
- `test_agents_ergonomics_features.py` - Tests v1.1+ ergonomics features

See `tests/` directory for complete list of 76 DSL test files.

#### 2. Verification Tests (9 files in tests/verification/)
Formal correctness guarantees with metamorphic and differential testing:
- `test_algorithm_sanity.py` - Algorithm sanity checks
- `test_ast_errors.py` - AST error handling and diagnostics
- `test_cli_smoke.py` - CLI smoke tests
- `test_determinism.py` - Seed determinism and reproducibility
- `test_dsl_equivalence.py` - DSL semantic equivalence
- `test_fuzz_queries.py` - Fuzz testing for query parsing
- `test_io_roundtrip.py` - I/O round-trip invariants
- `test_query_result.py` - QueryResult correctness
- `test_uq_correctness.py` - UQ correctness and invariants

Total: 83+ tests with formal guarantees

#### 3. Property-Based Tests (113 files in tests/property/)
Hypothesis-driven property testing:
- `test_dsl_*_properties.py` - DSL property tests (113 files)
- Covers: aggregation, AST, export, registry, serialization, UQ

#### 4. Core Module Tests
- `test_core_immutable.py` - Immutable network views (15 tests)
- `test_core_lazy_evaluation.py` - Lazy properties (15 tests)
- `test_core_schema_validation.py` - Schema validation (16 tests)
- `test_compat_exceptions.py` - Compatibility exceptions (19 tests)
- `test_parallel.py` - Parallel execution (19 tests)

#### 5. Algorithm Tests
- `test_algorithms_random_generators.py` - BA, ER, SBM generators (21 tests)
- `test_algorithms_attribute_correlation.py` - Attribute-centrality correlation (23 tests)
- `test_algorithm_properties.py` - Algorithm invariants
- `tests/algorithms/` - Specialized algorithm tests (SBM, routing, etc.)

#### 6. Integration Tests
- `test_cli.py` - CLI functionality (79 tests)
- `test_workflows.py` - Workflow orchestration
- `test_temporal.py` - Temporal network operations
- `test_dynamics_*.py` - Dynamics simulation (39+ test functions)
- `test_contracts_*.py` - Design by contract
- `test_readme_flagship_example.py` - README example validation

#### 7. Specialized Tests
- `test_visualization_*.py` - Visualization utilities (35+ tests)
- `test_counterexamples.py` - Counterexample generation
- `test_claim_learning.py` - Claim learning
- `test_nullmodels_*.py` - Null model generation (6 files)
- `test_temporal_utils_extended.py` - Duration parsing (40 tests)

**Test Markers**:
- `@pytest.mark.property` - Property-based (Hypothesis)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.metamorphic` - Metamorphic invariant tests
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.verification` - Correctness verification tests

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_dsl_v2.py

# All verification tests
pytest tests/test_verification_*.py

# With coverage
pytest tests/ --cov=py3plex

# Skip slow tests
pytest tests/ -m "not slow"

# Only property tests
pytest tests/ -m property

# Only metamorphic tests
pytest tests/ -m metamorphic

# Only verification tests (comprehensive)
pytest tests/test_verification_*.py -v

# Targeted test
pytest tests/test_dsl_v2.py::test_query_builder_basic
```

### Test Markers

- `@pytest.mark.property` - Property-based (Hypothesis)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.metamorphic` - Metamorphic invariant tests
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.verification` - Correctness verification tests

---

## Repository State

### Overview Statistics

**Version**: py3plex 1.1.4  
**Python Support**: 3.8+  
**Repository Size**: ~171K lines of code  
**Test Coverage**: 8,942 tests across 539 test files (~14.7% statement coverage)  
**Key Modules**: 459 Python files across core, algorithms, DSL, and utilities  

### Major Subsystems

**Core Infrastructure** (16 modules):
- Network representations (multinet, temporal_multinet, immutable views)
- I/O and data loading (parsers, converters, supporting)
- Network generation (random_generators, advanced_random_generators)
- Schema validation and lazy evaluation

**DSL Subsystem** (~75 modules):
- Query builder (builder.py - 6.9K lines, central module)
- AST representation and execution (ast.py, executor.py, executor_semiring.py)
- Result handling (result.py - 2.2K lines)
- Layer algebra and expressions (layers.py, expressions.py)
- Query planning and optimization (planner.py)
- Uncertainty quantification integration (uq_algebra.py, uq_resolution.py)
- Provenance tracking (provenance.py)
- **NEW**: Static analysis and linting (lint/ — 15 modules, 8 lint rules)
- **NEW**: GraphProgram immutable program objects (program/ — 10 modules, rewrite engine)
- **NEW**: Specialized executors (executors/ — benchmark_executor)

**Algorithms** (119 modules across 16 categories):
- Community detection (16 modules, 6 algorithms)
- Centrality measures (multilayer, supra-matrix, versatility)
- **NEW**: Robustness centrality (`centrality/` package)
- Statistical analysis (11 modules)
- Temporal networks (community, centrality evolution)
- Multilayer-specific algorithms (entanglement, multirank, multixrank)
- Specialized methods (curvature, routing, classification)

**Uncertainty Quantification** (25 modules):
- Bootstrap and resampling methods
- Partition UQ and community ensemble
- Noise models and null model comparison
- Stratified perturbation for variance reduction
- Selection UQ and confidence intervals

**Dynamics** (14 modules):
- Compartmental models (SIS, SIR, SEIR)
- Custom process definitions
- Trajectory simulation and analysis
- DSL integration for dynamics queries

**Advanced Features**:
- Counterexample generation (8 modules)
- Claim learning and hypothesis discovery (6 modules)
- Semiring algebra for path analysis (`semiring/` — 10 modules, `algebra/` — 9 modules)
- Network comparison and benchmarking (5 modules)
- **NEW**: Meta-analysis pooling (`meta/` — 5 modules, DerSimonian–Laird)
- **NEW**: Experiment registry (`experiments/` — 9 modules, filesystem-backed)

**New Infrastructure Packages**:
- **`py3plex/algebra/`** (9 modules): Comprehensive semiring/algebra framework with protocol, built-in semirings, registry, weight lifting, path solvers, closure, fixed-point iteration, backend dispatch, witness tracking
- **`py3plex/embeddings/`** (6 modules): NetMF + MetaPath2Vec node embeddings, link feature operators, embedding cache
- **`py3plex/experiments/`** (9 modules): Experiment tracking registry, ExperimentStore (filesystem), ExperimentRunner, artifact management
- **`py3plex/meta/`** (5 modules): Meta-analytic pooling of network statistics (fixed-effect + random-effects)
- **`py3plex/optimizer/`** (6 modules): Cost-based query optimizer (logical plan → optimizer → physical plan → executor)
- **`py3plex/out_of_core/`** (10 modules): Out-of-core streaming query execution over disk-resident CSV/Arrow/Parquet files without loading full graph into RAM
- **`py3plex/runtime/`** (2 modules): Runtime introspection and capability detection utilities
- **`py3plex/ergonomics.py`**: Convenience helpers (`quick_network`, `quick_analysis`) to reduce boilerplate

### Module Distribution by Category

| Category | Modules | Lines of Code | Purpose |
|----------|---------|---------------|---------|
| Core | 16 | ~50K | Network data structures and I/O |
| DSL | ~75 | ~80K | Query language and execution (+ lint, program, executors) |
| Algorithms | 121 | ~70K | Network analysis algorithms (+ centrality/robustness) |
| Uncertainty | 25 | ~25K | UQ and robustness analysis |
| Dynamics | 14 | ~15K | Spreading processes |
| Algebra | 9 | ~8K | Comprehensive semiring algebra framework |
| Embeddings | 6 | ~6K | NetMF + MetaPath2Vec node embeddings and link features |
| Experiments | 9 | ~6K | Experiment tracking registry |
| Meta | 5 | ~4K | Meta-analytic pooling of network statistics |
| Optimizer | 6 | ~6K | Cost-based query optimizer |
| Out-of-Core | 10 | ~8K | Streaming query execution on disk-resident data |
| Runtime | 2 | ~2K | Runtime introspection and capability detection |
| Utilities | 50+ | ~30K | CLI, validation, profiling, visualization, ergonomics |

### Test Infrastructure

**Test Organization**:
- **539 test files** with **8,942 individual tests**
- **83+ verification tests** across specialized modules (provenance, differential, metamorphic, determinism) — 10 files in `tests/verification/`
- **210+ new tests** added in recent updates (schema validation, parallel execution, temporal utils, random generators, visualization, UQ propagation)
- **113 property-based test files** using Hypothesis in `tests/property/`
- Metamorphic tests for invariant checking
- Integration tests for end-to-end workflows
- **NEW**: Tests for algebra, embeddings, experiments, meta-analysis, out-of-core, optimizer, DSL lint, DSL program objects

**New Test Files for New Modules**:
- `test_algebra_backend.py`, `test_algebra_core.py`, `test_algebra_fixed_point.py`, `test_algebra_paths.py`, `test_algebra_registry.py`, `test_algebra_witness.py` — algebra package
- `test_dsl_lint.py` — DSL static analysis/linting
- `test_dsl_program_rewrite.py`, `test_dsl_program_types.py`, `test_program.py`, `test_program_cost_executor.py` — GraphProgram objects
- `test_experiments.py` — experiment tracking registry
- `test_meta_analysis.py` — meta-analytic pooling
- `test_out_of_core.py` — out-of-core streaming execution
- `test_ergonomics.py`, `test_cli_ergonomics.py` — ergonomics helpers
- `test_centrality_robustness.py`, `test_centrality_robustness_oracles.py`, `test_centrality_explain.py`, `test_centrality_explain_integration.py` — robustness centrality
- `property/test_algebra_properties.py`, `property/test_graph_programs_properties.py`, `property/test_centrality_invariants.py`, `property/test_centrality_rankings.py`, `property/test_io_metamorphic_roundtrip.py`, `property/test_meta_properties.py`, `property/test_versatility_metamorphic.py` — property-based tests

**Coverage Areas**:
- Core functionality: 40-85% coverage
- DSL: 23.5% coverage (high complexity, extensive functionality)
- Algorithms: improved with 44+ new tests
- Uncertainty: 21.3% coverage
- Dynamics: 19.0% coverage with 39+ test functions
- CLI: 70.2% coverage
- Utils: 37.1% coverage
- Validation: 82.6% coverage
- Temporal Utils: 100% coverage
- Algebra: new comprehensive test suite
- Embeddings/Experiments/Meta/Optimizer/Out-of-Core: covered by dedicated test files

### Repository Growth

**Recent Additions** (v1.1.x and v1.2):
- Version 1.1.3 enhancements and documentation updates
- Successive Halving for algorithm racing
- SBM (Stochastic Block Model) integration
- Partition UQ with entropy and stability metrics
- Stratified perturbation for variance-reduced UQ
- AutoCommunity with Pareto-optimal selection
- MetaPath2Vec embedding for heterogeneous/multilayer networks
- Ergonomics features (hint(), enhanced repr, pedagogical errors)
- Algorithm requirements and compatibility system
- Enhanced provenance tracking
- **NEW (v1.2)**: `py3plex/algebra/` — Comprehensive semiring algebra framework (`SemiringProtocol`, built-in semirings, algebra registry, weight lifting, path/closure solvers, fixed-point iteration, backend dispatch, witness support)
- **NEW (v1.2)**: `py3plex/embeddings/` — NetMF + MetaPath2Vec node embedding algorithms, link feature operators, embedding result cache
- **NEW (v1.2)**: `py3plex/experiments/` — Experiment tracking registry with filesystem-backed `ExperimentStore`, `ExperimentRunner`, artifact management, experiment metadata model
- **NEW (v1.2)**: `py3plex/meta/` — Meta-analytic pooling with `MetaBuilder`, `MetaResult`, fixed-effect and DerSimonian–Laird random-effects models
- **NEW (v1.2)**: `py3plex/optimizer/` — Cost-based query optimizer: logical plan, physical plan, cost model, optimization rules, plan nodes
- **NEW (v1.2)**: `py3plex/out_of_core/` — Out-of-core streaming query execution over disk-resident CSV/Arrow/Parquet files, out-of-core network, streaming operators, spill-to-disk support
- **NEW (v1.2)**: `py3plex/runtime/` — Runtime introspection utilities (`capabilities.py`)
- **NEW (v1.2)**: `py3plex/centrality/` — Centrality robustness analysis package
- **NEW (v1.2)**: `py3plex/ergonomics.py` — Ergonomic helper functions (`quick_network`, `quick_analysis`, etc.)
- **NEW (v1.2)**: `py3plex/dsl/lint/` (15 modules) — DSL static analysis and linting framework with 8 lint rules (unknown layer, unknown attribute, type mismatch, unsatisfiable, redundant, full-scan, cross-layer)
- **NEW (v1.2)**: `py3plex/dsl/program/` (10 modules) — `GraphProgram` first-class immutable program objects with rewrite engine, cost model, diff, distribution, and program cache
- **NEW (v1.2)**: `py3plex/dsl/executors/` — Specialized execution engines (`benchmark_executor`)

---

## File Locations

### Core Modules

- `py3plex/core/multinet.py` (4.3K lines) - Main `multi_layer_network` class with 200+ methods
- `py3plex/core/temporal_multinet.py` (19KB) - Temporal network support with time-stamped edges
- `py3plex/core/parsers.py` (30KB) - Network format parsers (edgelist, GML, GraphML, JSON)
- `py3plex/core/random_generators.py` (14KB) - Random network generation (ER, BA, SBM)
- `py3plex/core/converters.py` (8KB) - Format conversion utilities
- `py3plex/core/schema_validation.py` (13KB) - Field validation and schema enforcement
- `py3plex/core/lazy_evaluation.py` (8KB) - LazyProperty and CacheManager
- `py3plex/core/immutable.py` (8KB) - ImmutableNetworkView for safe read-only access
- `py3plex/core/nx_compat.py` (7KB) - NetworkX compatibility layer
- `py3plex/core/supporting.py` (5KB) - Supporting utilities
- `py3plex/core/types.py` (1KB) - Type definitions
- `py3plex/dsl/` - DSL v2 (builder API, AST, executor)
- `py3plex/dsl_legacy.py` (70KB) - Legacy string-based DSL
- `py3plex/graph_ops.py` (50KB) - Dplyr-style chainable API
- `py3plex/pipeline.py` (19KB) - Sklearn-style pipeline
- `py3plex/workflows.py` (21KB) - Config-driven workflows
- `py3plex_mcp/` - MCP server for AI agent integration

### MCP Server

- `py3plex_mcp/server.py` - FastMCP server implementation
- `py3plex_mcp/registry.py` - In-memory network handle storage
- `py3plex_mcp/schemas.py` - Response schema utilities
- `py3plex_mcp/errors.py` - Typed error handling
- `py3plex_mcp/safe_paths.py` - Path validation and safety

### DSL v2 Internals (~75 modules, ~80K lines)

**Core Builder API**:
- `py3plex/dsl/__init__.py` (14KB) - Public API exports (Q, L, UQ, Param, F, C, N, P, D, S)
- `py3plex/dsl/builder.py` (6.9K lines) - Q, L, UQ, Param builders - **central DSL module**
  - QueryBuilder (nodes, edges, communities)
  - LayerExprBuilder and LayerSet for layer algebra
  - UQBuilder for uncertainty quantification
  - ParamRef for parameterized queries
  - SemiringBuilder for path algebra
  - CompareBuilder, NullModelBuilder, PathBuilder, DynamicsBuilder

**AST and Execution**:
- `py3plex/dsl/ast.py` (59KB) - AST node definitions (SelectStmt, CompareStmt, PathStmt, etc.)
- `py3plex/dsl/executor.py` (6.9K lines) - Query execution engine with measure registry
- `py3plex/dsl/executor_semiring.py` (10KB) - Semiring path query executor
- `py3plex/dsl/planner.py` (29KB) - Query optimization and stage reordering
- `py3plex/dsl/cache.py` (7KB) - Query result caching

**Results and Export**:
- `py3plex/dsl/result.py` (72KB) - QueryResult class with export methods
- `py3plex/dsl/export.py` (10KB) - Export utilities (pandas, NetworkX, Arrow)
- `py3plex/dsl/serializer.py` (9KB) - AST serialization

**Query Components**:
- `py3plex/dsl/layers.py` (20KB) - Layer algebra (LayerSet) with set operations
- `py3plex/dsl/expressions.py` (9KB) - F field expressions for filtering
- `py3plex/dsl/communities.py` (8KB) - Community query handling
- `py3plex/dsl/patterns/` - Cypher-like pattern matching (experimental)

**Uncertainty and Provenance**:
- `py3plex/dsl/uq_algebra.py` (32KB) - UQValue algebra with formal guarantees
- `py3plex/dsl/uq_resolution.py` (17KB) - UQ configuration resolution
- `py3plex/dsl/community_uq.py` (14KB) - Community detection UQ
- `py3plex/dsl/selection_uq.py` (11KB) - Algorithm selection UQ
- `py3plex/dsl/compositional_uq.py` (11KB) - Compositional UQ operations
- `py3plex/dsl/provenance.py` (17KB) - Provenance tracking and replay

**Diagnostics and Optimization**:
- `py3plex/dsl/errors.py` (22KB) - DSL-specific exceptions with pedagogical messages
- `py3plex/dsl/warnings.py` (12KB) - Performance and semantic warnings
- `py3plex/dsl/explain.py` (15KB) - Query explanation and debugging
- `py3plex/dsl/benchmark.py` (10KB) - DSL query benchmarking
- `py3plex/dsl/benchmark_result.py` (4KB) - Benchmark result handling

**Supporting Infrastructure**:
- `py3plex/dsl/registry.py` (14KB) - Operator and measure registry
- `py3plex/dsl/operator_registry.py` (5KB) - DSL operator registration
- `py3plex/dsl/algebra.py` (11KB) - Algebraic operations
- `py3plex/dsl/context.py` (1KB) - Execution context

**NEW: DSL Lint / Static Analysis** (`py3plex/dsl/lint/` — 15 modules):
- `py3plex/dsl/lint/__init__.py` - Public API: `lint(query, graph, schema)`, `explain(query, graph, schema)`
- `py3plex/dsl/lint/diagnostic.py` - `Diagnostic` dataclass with severity, code, message, suggested fixes
- `py3plex/dsl/lint/schema.py` - `SchemaProvider`, `NetworkSchemaProvider`, `EntityRef`
- `py3plex/dsl/lint/types.py` - `AttrType`, `TypeEnvironment` for DSL type system
- `py3plex/dsl/lint/type_resolver.py` - Type resolution engine
- `py3plex/dsl/lint/lint_context.py` - `LintContext` threading schema + graph through rules
- `py3plex/dsl/lint/rules/__init__.py` - Rule registry (`get_all_rules()`)
- `py3plex/dsl/lint/rules/base.py` - `LintRule` Protocol
- `py3plex/dsl/lint/rules/dsl001_unknown_layer.py` - Unknown layer detection
- `py3plex/dsl/lint/rules/dsl002_unknown_attribute.py` - Unknown attribute detection with suggestions
- `py3plex/dsl/lint/rules/dsl101_type_mismatch.py` - Type mismatch detection
- `py3plex/dsl/lint/rules/dsl201_unsatisfiable.py` - Unsatisfiable filter detection
- `py3plex/dsl/lint/rules/dsl202_redundant.py` - Redundant clause detection
- `py3plex/dsl/lint/rules/perf301_full_scan.py` - Full-scan performance warning
- `py3plex/dsl/lint/rules/perf302_cross_layer.py` - Cross-layer scan performance warning

**NEW: DSL Program Objects** (`py3plex/dsl/program/` — 10 modules):
- `py3plex/dsl/program/__init__.py` - Public API: `GraphProgram`, `type_check`, `infer_type`, `apply_rewrites`
- `py3plex/dsl/program/program.py` - `GraphProgram` immutable program object with canonical AST
- `py3plex/dsl/program/types.py` - Static type system for DSL IR
- `py3plex/dsl/program/rewrite.py` - `RewriteEngine` with correctness-preserving transformations
- `py3plex/dsl/program/cost.py` - `CostModel` for time/memory estimation
- `py3plex/dsl/program/executor.py` - Program executor
- `py3plex/dsl/program/explain.py` - Execution plan explanation
- `py3plex/dsl/program/diff.py` - Program diff utilities
- `py3plex/dsl/program/distribution.py` - UQ-aware result distribution type
- `py3plex/dsl/program/cache.py` - `ProgramCache` keyed by provenance

**NEW: Specialized Executors** (`py3plex/dsl/executors/` — 2 modules):
- `py3plex/dsl/executors/__init__.py` - Executor registry
- `py3plex/dsl/executors/benchmark_executor.py` - Benchmark-aware execution engine

### Algorithms - Complete Inventory

#### Community Detection (16 modules, 6+ algorithms)

**Core Algorithms**:
- `py3plex/algorithms/community_detection/community_louvain.py` - Multilayer Louvain optimization
- `py3plex/algorithms/community_detection/leiden_multilayer.py` - Multilayer Leiden with CPM
- `py3plex/algorithms/community_detection/leiden_uq.py` - Leiden with uncertainty quantification
- `py3plex/algorithms/community_detection/label_propagation.py` - Supra-graph and consensus label propagation
- `py3plex/algorithms/community_detection/spectral_multilayer.py` - Spectral clustering on supra-adjacency
- `py3plex/algorithms/community_detection/sbm_wrapper.py` - Stochastic Block Model integration

**Algorithm Selection and Benchmarking**:
- `py3plex/algorithms/community_detection/auto_select.py` - Legacy auto-selection with "most wins" logic
- `py3plex/algorithms/community_detection/autocommunity.py` (AutoCommunity) - Pareto-optimal multi-objective selection
- `py3plex/algorithms/community_detection/autocommunity_executor.py` - Execution engine for AutoCommunity
- `py3plex/algorithms/community_detection/successive_halving.py` - Progressive algorithm elimination
- `py3plex/algorithms/community_detection/runner.py` - Unified algorithm runner with BudgetSpec
- `py3plex/algorithms/community_detection/budget.py` - Budget specification for algorithm racing

**Quality Metrics and Evaluation**:
- `py3plex/algorithms/community_detection/multilayer_modularity.py` - Multilayer modularity computation
- `py3plex/algorithms/community_detection/multilayer_quality_metrics.py` - Coverage, cut ratio, replica consistency, layer entropy
- `py3plex/algorithms/community_detection/sbm_metrics.py` - SBM-specific metrics (log-likelihood, MDL, BIC)
- `py3plex/algorithms/community_detection/community_measures.py` - Community-level measures
- `py3plex/algorithms/community_detection/community_ranking.py` - Ranking communities by quality
- `py3plex/algorithms/community_detection/node_ranking.py` - Node importance within communities

**Benchmark Generation**:
- `py3plex/algorithms/community_detection/multilayer_benchmark.py` - LFR, SBM, and coupled ER benchmarks
- `py3plex/algorithms/community_detection/distributional.py` - Distributional community detection

**Supporting Infrastructure**:
- `py3plex/algorithms/community_detection/community_wrapper.py` - Unified wrapper interface
- `py3plex/algorithms/community_detection/NoRC.py` - NoRC algorithm implementation
- `py3plex/algorithms/community_detection/flow_hierarchy.py` - Flow-based hierarchy detection

#### Centrality Measures (7 modules)

**Multilayer Centrality**:
- `py3plex/algorithms/multilayer_algorithms/centrality.py` (93KB) - **Largest algorithm module**
  - PageRank, HITS, Katz centrality
  - Betweenness, closeness, degree centrality
  - Eigenvector centrality
  - Multilayer adaptations with interlayer coupling
- `py3plex/algorithms/multilayer_algorithms/supra_matrix_function_centrality.py` (9KB) - Matrix function centrality
- `py3plex/algorithms/multicentrality.py` - Multiple centrality computation
- `py3plex/algorithms/centrality_toolkit.py` - Centrality computation toolkit

**Specialized Multilayer Measures**:
- `py3plex/algorithms/multilayer_algorithms/versatility.py` (16KB) - Node versatility across layers
- `py3plex/algorithms/multilayer_algorithms/entanglement.py` (6KB) - Layer entanglement measures
- `py3plex/algorithms/multilayer_algorithms/multirank.py` (13KB) - MultiRank centrality
- `py3plex/algorithms/multilayer_algorithms/multixrank.py` (22KB) - MultiXRank for heterogeneous networks

**Centrality Analysis**:
- `py3plex/algorithms/centrality/explain.py` - Centrality explanation utilities
- `py3plex/algorithms/attribute_correlation.py` - Attribute-centrality correlation analysis

#### Statistical Analysis (11 modules)

**Basic Statistics**:
- `py3plex/algorithms/statistics/basic_statistics.py` (4KB) - Degree distribution, clustering coefficient
- `py3plex/algorithms/statistics/multilayer_statistics.py` (76KB) - Comprehensive multilayer statistics
- `py3plex/algorithms/statistics/topology.py` (5KB) - Topological properties

**Advanced Statistical Methods**:
- `py3plex/algorithms/statistics/correlation_networks.py` (2KB) - Correlation network construction
- `py3plex/algorithms/statistics/enrichment_modules.py` (9KB) - Enrichment analysis
- `py3plex/algorithms/statistics/powerlaw.py` (109KB) - Power-law distribution fitting
- `py3plex/algorithms/statistics/stats_comparison.py` (21KB) - Statistical comparison methods

**Bayesian Methods**:
- `py3plex/algorithms/statistics/bayesiantests.py` (22KB) - Bayesian hypothesis testing
- `py3plex/algorithms/statistics/bayesian_distances.py` (1KB) - Bayesian distance measures
- `py3plex/algorithms/statistics/critical_distances.py` (13KB) - Critical distance diagrams

#### Temporal Network Algorithms (3 modules)

- `py3plex/algorithms/temporal/centrality.py` - Temporal centrality evolution
- `py3plex/algorithms/temporal/community.py` - Temporal community detection
- `py3plex/algorithms/temporal_multiplex/` - Temporal multiplex analysis

#### Specialized Algorithms

**Curvature**:
- `py3plex/algorithms/curvature/ollivier_ricci_multilayer.py` - Ollivier-Ricci curvature for multilayer

**Network Classification**:
- `py3plex/algorithms/network_classification/PPR.py` - Personalized PageRank for classification
- `py3plex/algorithms/network_classification/label_propagation.py` - Label propagation classifier

**Routing and Paths**:
- `py3plex/algorithms/routing/multiplex_paths.py` - Path finding in multiplex networks

**Graph Summarization and Embedding**:
- `py3plex/algorithms/graph_summarization.py` - Network summarization methods
- `py3plex/algorithms/layer_similarity.py` - Inter-layer similarity computation
- `py3plex/algorithms/multilayer_clustering.py` - Multilayer clustering

**Robustness and Testing**:
- `py3plex/algorithms/robustness_testing.py` - Network robustness analysis
- `py3plex/algorithms/community_comparison.py` - Community structure comparison
- `py3plex/algorithms/statistical_report.py` - Statistical reporting
- `py3plex/algorithms/meta_flow_report.py` - Meta-analysis flow reporting

**Specialized Methods**:
- `py3plex/algorithms/sir_multiplex.py` - SIR epidemic on multiplex networks
- `py3plex/algorithms/advanced_random_generators.py` - Advanced random graph generators (BA, ER, SBM)
- `py3plex/algorithms/requirements_registry.py` - Algorithm requirements tracking

**Rule Learning (Hedwig)**:
- `py3plex/algorithms/hedwig/` (12 modules) - Rule learning and inductive logic programming
  - Core: KB, rules, predicates, examples
  - Learners: Bottom-up, optimal
  - Stats: Significance, adjustment, validation

**General Algorithms**:
- `py3plex/algorithms/general/walkers.py` - Random walkers and diffusion
- `py3plex/algorithms/general/benchmark_classification.py` - Classification benchmarks

**Node Ranking**:
- `py3plex/algorithms/node_ranking/node_ranking.py` - Various node ranking algorithms

**SBM (Stochastic Block Model)** (8 modules):
- `py3plex/algorithms/sbm/multilayer_sbm.py` - Multilayer SBM implementation
- `py3plex/algorithms/sbm/inference_vi.py` - Variational inference for SBM
- `py3plex/algorithms/sbm/model_selection.py` - Model selection (K selection)
- `py3plex/algorithms/sbm/objectives.py` - ELBO, MDL, BIC objectives
- `py3plex/algorithms/sbm/uq.py` - Uncertainty quantification for SBM
- `py3plex/algorithms/sbm/diagnostics.py` - SBM diagnostics
- `py3plex/algorithms/sbm/conversions.py` - Format conversions
- `py3plex/algorithms/sbm/utils.py` - SBM utilities

### Dynamics Simulation (14 modules, ~15K lines)

**Core Dynamics Engine**:
- `py3plex/dynamics/core.py` (23KB) - DynamicsSimulator base class
- `py3plex/dynamics/executor.py` (12KB) - Dynamics query executor
- `py3plex/dynamics/result.py` (9KB) - DynamicsResult with trajectory analysis

**Compartmental Models**:
- `py3plex/dynamics/models.py` (24KB) - SIS, SIR, SEIR, SIRS models
- `py3plex/dynamics/compartmental.py` (14KB) - Compartmental model framework
- `py3plex/dynamics/processes.py` (9KB) - Custom process definitions

**Configuration and Building**:
- `py3plex/dynamics/builder.py` (7KB) - DynamicsBuilder for DSL integration
- `py3plex/dynamics/config.py` (11KB) - Configuration management
- `py3plex/dynamics/registry.py` (8KB) - Model registry

**Supporting Infrastructure**:
- `py3plex/dynamics/ast.py` (3KB) - Dynamics AST nodes
- `py3plex/dynamics/errors.py` (5KB) - Dynamics-specific errors
- `py3plex/dynamics/serializer.py` (3KB) - Serialization utilities
- `py3plex/dynamics/_utils.py` (5KB) - Internal utilities
- `py3plex/dynamics/__init__.py` (3KB) - Public API exports

### Uncertainty Quantification (26 modules, ~25K lines)

**Bootstrap and Resampling**:
- `py3plex/uncertainty/bootstrap.py` (13KB) - Bootstrap resampling methods
- `py3plex/uncertainty/resampling_graph.py` (8KB) - Graph resampling utilities
- `py3plex/uncertainty/stratification.py` (11KB) - Stratified sampling for variance reduction

**Partition and Community UQ**:
- `py3plex/uncertainty/partition_uq.py` (19KB) - Partition uncertainty quantification
- `py3plex/uncertainty/partition.py` (36KB) - Partition representation and operations
- `py3plex/uncertainty/partition_reducers.py` (28KB) - Partition aggregation methods
- `py3plex/uncertainty/partition_metrics.py` (9KB) - Partition stability metrics
- `py3plex/uncertainty/partition_types.py` (1KB) - Partition type definitions
- `py3plex/uncertainty/community_ensemble.py` (18KB) - Community ensemble methods
- `py3plex/uncertainty/community_result.py` (25KB) - Community UQ result handling

**Selection and Algorithm UQ**:
- `py3plex/uncertainty/selection_uq.py` (13KB) - Algorithm selection UQ
- `py3plex/uncertainty/selection_execution.py` (9KB) - Selection execution
- `py3plex/uncertainty/selection_reducers.py` (16KB) - Selection result aggregation
- `py3plex/uncertainty/selection_types.py` (2KB) - Selection type definitions

**Noise Models and Perturbation**:
- `py3plex/uncertainty/noise_models.py` (15KB) - Edge drop, weight noise, layer drop
- `py3plex/uncertainty/null_models.py` (17KB) - Null model integration for UQ

**Estimation and Confidence**:
- `py3plex/uncertainty/estimation.py` (18KB) - Parameter estimation with UQ
- `py3plex/uncertainty/ci_utils.py` (5KB) - Confidence interval utilities

**Infrastructure**:
- `py3plex/uncertainty/runner.py` (5KB) - UQ execution runner
- `py3plex/uncertainty/plan.py` (6KB) - UQ execution planning
- `py3plex/uncertainty/context.py` (4KB) - UQ context management
- `py3plex/uncertainty/types.py` (12KB) - Type definitions
- `py3plex/uncertainty/__init__.py` (5KB) - Public API exports
- `py3plex/uncertainty/README.md` (9KB) - UQ documentation

**Reducers** (subdirectory):
- Multiple reducer implementations for aggregating UQ results

### Advanced Features

**Counterexample Generation**:
- `py3plex/counterexamples/` (8 modules) - Automated counterexample finding for network claims
  - Claim language parsing and evaluation
  - Witness subgraph extraction
  - Minimization strategies

**Claim Learning**:
- `py3plex/claims/` (6 modules) - Hypothesis discovery from network data
  - Inductive rule learning
  - Support and coverage metrics
  - Integration with counterexample engine

**Semiring Algebra**:
- `py3plex/semiring/` (10 modules) - Formal semiring path algebra
  - Shortest paths, most reliable paths, reachability
  - Fixed-point iteration and closure
  - Custom semiring definitions
  - Pareto frontier for multi-objective paths

**Network Comparison**:
- `py3plex/comparison/` (5 modules) - Network similarity and comparison
  - Multiplex Jaccard, edit distance
  - Structural comparison metrics

**Provenance System**:
- `py3plex/provenance/` - Query provenance tracking
  - Replay and reproducibility
  - Snapshot and delta capture

**Null Models**:
- `py3plex/nullmodels/` - Configuration model, ER, edge swapping
  - Statistical significance testing
  - Null model integration with UQ

**Temporal Utilities**:
- `py3plex/temporal_utils.py` (7KB) - Basic temporal network utilities
- `py3plex/temporal_utils_extended.py` (4KB) - Duration parsing and formatting
- `py3plex/temporal_view.py` (10KB) - Temporal network views

**Other Specialized Modules**:
- `py3plex/paths/` - Path finding algorithms
- `py3plex/stats/` - Statistical utilities
- `py3plex/sensitivity/` - Sensitivity analysis
- `py3plex/selection/` - Algorithm selection utilities
- `py3plex/robustness/` - Robustness analysis
- `py3plex/counterfactual/` - Counterfactual analysis
- `py3plex/contracts/` - Design by contract
- `py3plex/alignment/` - Network alignment
- `py3plex/benchmarks/` - Benchmarking utilities
- `py3plex/lab/` - Experimental features

### I/O and Data

**I/O Handlers**:
- `py3plex/io/` (8 modules) - Input/output format handlers
  - Edgelist, GraphML, GML, JSON formats
  - Apache Arrow support for high-performance I/O
  - Multilayer network serialization
  - Format conversion utilities

**Built-in Datasets**:
- `py3plex/datasets/` - Curated multilayer networks
  - Biological networks (PPI, gene-disease-drug)
  - Social networks (Facebook, Twitter multiplex)
  - Infrastructure networks (transportation, utilities)
  - Benchmark networks (LFR, SBM-generated)

### Utilities and Supporting Infrastructure

**Command-Line Interface**:
- `py3plex/cli.py` (128KB) - **Comprehensive CLI tool**
  - Network creation, statistics, querying
  - Community detection, centrality computation
  - Format conversion
  - Uncertainty quantification integration
  - 79 comprehensive tests in test_cli.py

**Configuration and Validation**:
- `py3plex/config.py` (10KB) - Configuration constants and defaults
- `py3plex/validation.py` (13KB) - Input validation (2 test files)
- `py3plex/errors.py` (23KB) - Error handling utilities
- `py3plex/exceptions.py` (13KB) - Exception hierarchy

**Parallel Execution**:
- `py3plex/_parallel.py` (9KB) - Parallel execution utilities
  - Deterministic seed spawning
  - Parallel map with n_jobs support
  - 19 tests for spawn_seeds and parallel_map

**Performance and Analysis**:
- `py3plex/profiling.py` (11KB) - Performance profiling tools
- `py3plex/linter.py` (27KB) - Code quality checking
- `py3plex/diagnostics/` - Diagnostic system with actionable messages

**Visualization**:
- `py3plex/visualization/` (4 modules) - Network visualization
  - Multilayer layout algorithms
  - Layer-aware visualization
  - Benchmark plotting (35 tests added)
  - Export to various formats

**Plugin System**:
- `py3plex/plugins/` - Extensible plugin architecture
  - Custom operators and measures
  - DSL operator registration
  - 20.7% test coverage

**Supporting Modules**:
- `py3plex/utils.py` (14KB) - General utilities (4 test files)
- `py3plex/requirements.py` (35KB) - Algorithm requirements and compatibility system
- `py3plex/logging_config.py` (1KB) - Logging configuration
- `py3plex/wrappers/` - NetworkX and igraph wrappers
- `py3plex/multinet/` - Legacy multinet support
- `py3plex/compat/` - Compatibility layer (3 modules, 19 tests for exceptions)

### MCP Server (Model Context Protocol)

**MCP Integration** (py3plex_mcp/):
- `py3plex_mcp/server.py` - FastMCP server implementation
- `py3plex_mcp/registry.py` - In-memory network handle storage
- `py3plex_mcp/schemas.py` - Response schema utilities
- `py3plex_mcp/errors.py` - Typed error handling
- `py3plex_mcp/safe_paths.py` - Path validation and safety

**Features**:
- 7 tools (load_network, run_query, community_detect, export, etc.)
- 3 resources (AGENTS.md, DSL reference, tool schemas)
- Security-first design (safe file access, output sandboxing)
- Python 3.10+ required (MCP SDK dependency)

### Documentation

- `AGENTS.md` (10,500+ lines) - **This file** - Comprehensive AI agent documentation
- `README.md` - Quick start and project overview
- `docfiles/` - Documentation source files
- `examples/` - **267 example scripts** demonstrating all features
- `docs/py3plex_book.pdf` (106 pages) - Technical documentation
- `CITATION.cff` - Citation information

### Test Suite

**Test Files** (539 files, 8,942 tests):

**DSL Tests**:
- `tests/test_dsl_v2.py` - DSL v2 core functionality
- `tests/test_dsl_extensions.py` - DSL extensions
- `tests/test_dsl_legacy_edges.py` - Legacy DSL edge queries
- `tests/test_graph_ops.py` - Dplyr-style operations

**Algorithm Tests**:
- `tests/test_community_detection/` - Community detection algorithms
- `tests/test_algorithms_random_generators.py` (21 tests) - BA, ER, SBM generators
- `tests/test_algorithms_attribute_correlation.py` (23 tests) - Attribute-centrality correlation
- `tests/test_metapath2vec.py` - MetaPath2Vec embedding validation

**Infrastructure Tests**:
- `tests/test_pipeline.py` - Pipeline API
- `tests/test_cli.py` (79 tests) - CLI functionality
- `tests/test_parallel.py` (19 tests) - Parallel execution
- `tests/test_core_*.py` - Core module tests (schema validation, lazy evaluation, immutable views)

**UQ and Robustness Tests**:
- `tests/test_uncertainty.py` - Uncertainty quantification
- `tests/test_dynamics.py` - Dynamics simulations (39+ test functions)
- `tests/test_temporal.py` - Temporal networks
- `tests/test_temporal_utils_extended.py` (40 tests) - Duration parsing/formatting

**Specialized Tests**:
- `tests/test_counterexamples.py` - Counterexample generation
- `tests/test_claim_learning.py` - Claim learning
- `tests/test_verification_*.py` (83 tests across 4 modules) - Correctness verification
- `tests/test_visualization_benchmark.py` (35 tests) - Benchmark plotting

**Test Markers**:
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.property` - Property-based (Hypothesis)
- `@pytest.mark.metamorphic` - Metamorphic invariant tests
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.verification` - Correctness verification tests

### Development Tools

**Configuration**:
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `setup.py` - Legacy setup script
- `MANIFEST.in` - Package manifest
- `Makefile` - Build and development tasks

**Quality Assurance**:
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.github/workflows/` - CI/CD pipelines (tests, examples, benchmarks, docs, fuzzing)
- `conftest.py` - Pytest configuration
- `verify_rewrite_engine.py` - Rewrite engine verification

**Docker Support**:
- `Dockerfile` - Container image
- `docker-compose.yml` - Multi-container setup
- `.dockerignore` - Docker build exclusions

**Notebooks and Scripts**:
- `notebooks/` - Jupyter notebooks for interactive analysis
- `scripts/` - Development and maintenance scripts
- `create_mosaic_banner.py` - Banner generation
- `create_showcase_flow.py` - Showcase visualization

**Other Resources**:
- `background_knowledge/` - Domain knowledge and references
- `multilayer_datasets/` - Additional dataset files
- `example_images/` - Example visualizations
- `book/` - Book source files
- `fuzzing/` - Fuzzing harness
- `gui/` - Web GUI (FastAPI + SvelteKit)

---

## Algorithm Quick Reference

### By Use Case

**Community Detection**:
- **Fast, scalable**: Louvain (`louvain_multilayer`)
- **High quality**: Leiden (`leiden_multilayer`)
- **With UQ**: Leiden with ensemble (`leiden_uq`)
- **Auto-selection**: AutoCommunity with Pareto optimization
- **Model-based**: SBM with model selection
- **Label-based**: Supra-graph or consensus label propagation

**Centrality**:
- **Degree centrality**: Built-in to DSL (`Q.nodes().compute("degree")`)
- **Betweenness**: Multilayer betweenness (`compute("betweenness_centrality")`)
- **PageRank**: Multilayer PageRank with interlayer coupling
- **Versatility**: Cross-layer node versatility
- **MultiRank/MultiXRank**: Heterogeneous network ranking

**Statistical Analysis**:
- **Basic stats**: Degree distribution, clustering coefficient
- **Power-law fitting**: Powerlaw module with goodness-of-fit
- **Correlation**: Attribute-centrality correlation
- **Enrichment**: Network enrichment analysis
- **Bayesian testing**: Hypothesis testing with Bayesian methods

**Temporal Analysis**:
- **Centrality evolution**: Temporal centrality tracking
- **Community evolution**: Temporal community detection
- **Snapshot analysis**: Time-slice queries with `.at()` and `.during()`

**Dynamics**:
- **Epidemic models**: SIS, SIR, SEIR on multilayer networks
- **Custom processes**: Define custom spreading dynamics
- **Trajectory analysis**: Multi-replicate simulations with UQ

### Algorithm Selection Guide

| Task | Small Networks (<1K nodes) | Large Networks (>10K nodes) | Multilayer-Specific | UQ Support |
|------|----------------------------|-----------------------------|--------------------|------------|
| **Communities** | Leiden, SBM | Louvain, Label Propagation | Leiden (omega) | Yes (ensemble, seed) |
| **Centrality** | All measures | Degree, PageRank | Versatility, Entanglement | Yes (bootstrap, perturbation) |
| **Paths** | Semiring algebra | — | Layer-aware routing | No |
| **Dynamics** | All models | SIS, SIR | Multilayer SIS/SIR | Yes (replicates) |
| **Statistics** | All methods | Basic stats, power-law | Multilayer statistics | Partial |

### Performance Considerations

**Computational Complexity**:
- **O(n)**: Degree, layer statistics
- **O(m)**: Single-pass edge operations, label propagation
- **O(n·m)**: PageRank (iterative), betweenness centrality
- **O(n²·m)**: Closeness centrality, SBM inference
- **O(n³)**: All-pairs shortest paths, supra-matrix operations

**Memory Requirements**:
- **Low (O(n+m))**: Sparse algorithms, degree-based measures
- **Medium (O(n²))**: Supra-adjacency matrix (stored sparse)
- **High (O(n²·L²))**: Full supra-matrix construction (L = layers)

**Scaling Recommendations**:
- **<1K nodes**: All algorithms work well
- **1K-10K nodes**: Avoid closeness, use sparse betweenness
- **>10K nodes**: Use fast algorithms (Louvain, degree, PageRank), enable caching
- **>100K nodes**: Consider NetworkX backend optimizations, graph-tool for centrality

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

print(py3plex.__version__)  # "1.1.4"
```

### Version Bump Checklist (Canonical)

When the prompt is **"bump version"**, update the canonical project version in `pyproject.toml` and then propagate that same value to all required release surfaces below.

**Authoritative source**:
- `pyproject.toml` → `[project].version`

**Must-update files for every release bump**:
1. Library runtime metadata
   - `py3plex/__init__.py` → `__version__`, `__api_version__`
   - `py3plex/config.py` → `__version__`, `__api_version__`
2. MCP package metadata
   - `py3plex_mcp/__init__.py` → `__version__` (and top docstring version line if present)
3. Documentation build metadata
   - `docfiles/conf.py` → `version`, `release`
4. Book build metadata
   - `book/conf.py` → `version`, `release`
5. Citation metadata
   - `CITATION.cff` → `version` (and `date-released` when doing an actual release cut)

**Book/content version mentions (when version is explicitly printed in prose)**:
- Update book prose references that intentionally pin exact release text:
  - `book/front_matter.rst`
  - `book/bibliography.rst`
  - `book/part5_systems/chapter16_reproducible_environments.rst` (example pins like `py3plex==X.Y.Z`)
  - `book/appendices/appendix_b_docker_deployment.rst` (image tags like `py3plex:X.Y.Z`)

**Validation after bump**:
- Run focused consistency checks:
  - `python -m pytest tests/test_version_consistency.py -q`
  - `python -m pytest tests/test_book_manuscript_integrity.py -q`
  - `python -m pytest tests/test_doc_conf.py tests/test_book_conf.py -q`

These tests are intended to ensure that a single bump request updates library, docs, book, MCP, and citation version surfaces consistently.

**Version History**:
- **1.1.4** (Current): Repository statistics refresh and AGENTS.md consistency updates
- **1.1.3**: Repository state updates and documentation improvements
- **1.1.2**: Removed redundant documentation files
- **1.1.1**: Documentation updates and AutoCommunity examples
- **1.1.0**: DSL v2, Dynamics, UQ, Temporal, Null models, Counterexamples, Claim learning
- **1.0.0**: Initial stable release
- **0.96**: Pre-release

---

## References

- **README.md**: Quick start and flagship example
- **AGENTS.md**: Comprehensive AI agent documentation (this file)
- **docfiles/**: Detailed documentation
- **examples/**: 267 example scripts
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
Q.nodes() -> configure (.where, .compute, etc.) -> .execute(net) -> QueryResult
  lazy         lazy                                 eager          rich object
```

**2. Grouping Pattern**
```
.per_layer() -> .top_k(k) -> .end_grouping() -> .coverage(mode) -> .execute()
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
-> Adds _mean, _std, _ci95_low, _ci95_high columns
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

#### Load -> Analyze -> Export

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
      "py3plex": "1.1.4",
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

**Last Updated**: 2026-03-15 (for py3plex v1.1.4)


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
# -> SBM runs 50 EM iterations, 2 restarts, 20 bootstrap samples for UQ
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


---

## Expanded Test Coverage and Validation

**Status as of January 2026**: The py3plex test suite has been significantly expanded to enforce documented guarantees and architectural claims across all major subsystems.

### Test Coverage Summary

The test suite now includes **203 new deterministic, CI-friendly tests** across 10 specialized test modules:

| Test Module | Tests | Coverage Area |
|-------------|-------|---------------|
| `test_dsl_ast_equivalence.py` | 21 | DSL ↔ DSL v2 AST compilation equivalence |
| `test_provenance_schema.py` | 17 | Provenance completeness and schema stability |
| `test_determinism_randomness.py` | 16 | Seed determinism and randomness boundaries |
| `test_roundtrip_invariants.py` | 21 | Data conversion preservation (dict/pandas/IO) |
| `test_node_edge_parity.py` | 31 | Node/edge operation symmetry |
| `test_exception_taxonomy.py` | 22 | Exception hierarchy enforcement |
| `test_coverage_grouping.py` | 19 | Coverage and grouping correctness |
| `test_nullmodel_sanity.py` | 17 | Null model structural invariants |
| `test_dsl_graphops_equivalence.py` | 13 | DSL ↔ graph_ops semantic equivalence |
| `test_degenerate_networks.py` | 26 | Edge-case and empty network handling |

**Total**: 203 new tests, all automated and passing.

### Enforced Guarantees

These tests enforce the following documented guarantees:

#### 1. Single-AST Compilation Model

**Guarantee**: All DSL frontends (string DSL, Q builder, graph_ops) compile to identical AST structures.

**Tests**: 
- `test_dsl_ast_equivalence.py` verifies:
  - Identical AST hash for equivalent queries
  - Identical AST summary strings
  - AST hash determinism (same query → same hash)
  - AST hash uniqueness (different queries → different hashes)

**Validation**: AST hashes are 16-character SHA256 prefixes, stable across invocations.

#### 2. Provenance Completeness

**Guarantee**: All query execution paths produce complete provenance metadata with stable schema.

**Tests**:
- `test_provenance_schema.py` verifies presence of required keys:
  - `engine` (execution engine identifier)
  - `py3plex_version` (library version)
  - `timestamp_utc` (ISO8601 execution time)
  - `network_fingerprint` (node/edge/layer counts)
  - `query.ast_hash` (16-char AST fingerprint)
  - `performance.total_ms` (execution time)

**Validation**: Snapshot-style tests detect schema drift. Network fingerprints are deterministic and consistent.

#### 3. Determinism and Randomness Boundaries

**Guarantee**: Algorithms with seeds produce identical results; different seeds produce statistically different outputs.

**Tests**:
- `test_determinism_randomness.py` verifies:
  - Same seed → identical results (UQ, null models, community detection)
  - Different seeds → different results (statistical test)
  - seed=None behavior (runs without error)
  - Deterministic metrics (degree, betweenness) remain deterministic

**Validation**: Null models with same seed produce networks with identical node/edge counts. UQ with same seed produces identical confidence intervals.

#### 4. Round-Trip Invariants

**Guarantee**: Data conversions preserve structure and attributes.

**Tests**:
- `test_roundtrip_invariants.py` verifies:
  - QueryResult → dict → QueryResult (structure preserved)
  - QueryResult → pandas → QueryResult (values preserved)
  - Network → IO format → Network (counts preserved)
  - Network fingerprint stability across operations

**Validation**: Node count, edge count, layer count, and network fingerprint remain identical after round-trip conversions.

#### 5. Node–Edge Feature Parity

**Guarantee**: Node queries and edge queries support symmetric operations where documented.

**Tests**:
- `test_node_edge_parity.py` verifies parity for:
  - Filtering (`.where()` conditions)
  - Grouping (`.per_layer()` for nodes, `.per_layer_pair()` for edges)
  - Ordering (`.order_by()` and descending)
  - Limiting (`.limit()` and `.head()`)
  - Export (`.to_pandas()`)

**Validation**: Both nodes and edges support filtering, ordering, limiting, and pandas export with consistent behavior.

#### 6. Exception Taxonomy

**Guarantee**: Public APIs use typed exceptions with informative messages; no raw `Exception` leaks.

**Tests**:
- `test_exception_taxonomy.py` verifies:
  - `DslError` hierarchy (syntax, execution, unknown measure, missing parameter)
  - `Py3plexException` hierarchy (IOError, generic)
  - Non-empty, descriptive error messages
  - Exception hierarchy (specific exceptions inherit from base classes)
  - No system corruption after errors (network remains unchanged)

**Validation**: Invalid operations raise domain-specific exceptions with >10 character messages. System remains usable after errors.

#### 7. Coverage and Grouping Correctness

**Guarantee**: Coverage filtering and grouping produce exact membership, not just correct counts.

**Tests**:
- `test_coverage_grouping.py` verifies:
  - `.coverage(mode="at_least", k=n)` returns correct nodes
  - `.per_layer()` grouping metadata is present
  - `.per_layer_pair()` edge grouping works
  - Grouping with filters combines correctly
  - Edge cases (single layer, empty network) handled gracefully

**Validation**: Synthetic analytical networks with known coverage properties (node A in 3 layers, node B in 2 layers, node C in 1 layer) validate exact membership.

#### 8. Null Model Statistical Sanity

**Guarantee**: Null models preserve structural invariants and produce statistically reasonable results.

**Tests**:
- `test_nullmodel_sanity.py` verifies:
  - Configuration model preserves node count, edge count (approximately), layers
  - Erdos-Renyi model preserves node count
  - Edge swap model preserves node count and edge count (exactly)
  - Layer shuffle model preserves nodes and edges
  - Different seeds produce different networks (probabilistic test)
  - Null model results include seed, model_type, samples

**Validation**: Null models on 10-node networks preserve basic structural properties. Degree distributions remain non-negative and bounded.

#### 9. DSL ↔ graph_ops Semantic Equivalence

**Guarantee**: DSL and graph_ops produce equivalent results for identical analytical operations.

**Tests**:
- `test_dsl_graphops_equivalence.py` verifies:
  - Node selection count matches
  - Edge selection count matches
  - Filtering produces consistent results
  - Ordering produces sorted results
  - Limiting respects bounds
  - Both APIs export to pandas

**Validation**: Simple operations (select all nodes, filter by degree, order by degree) produce same counts and structures in both APIs.

#### 10. Degenerate and Edge-Case Networks

**Guarantee**: No crashes on degenerate inputs; well-defined empty outputs; correct provenance for zero results.

**Tests**:
- `test_degenerate_networks.py` verifies:
  - Empty network handling (0 nodes, 0 edges)
  - Single-node network (degree 0, no edges)
  - Single-layer network (layer_count=1)
  - Disconnected layers (no inter-layer edges)
  - No-match queries (degree > 1000 returns empty)
  - Empty results convert to pandas gracefully
  - Provenance present even for empty results

**Validation**: All edge cases complete without exceptions. Empty results have length 0, convert to empty DataFrames, and include full provenance metadata.

### Architectural Claims Validated

The expanded test suite validates these architectural claims from AGENTS.md:

1. **AST hash stability**: Identical queries produce identical AST hashes  (tested)
2. **Reproducibility guarantee**: Same AST hash + seed + network → same results  (tested)
3. **Provenance schema stability**: All executors produce same provenance keys  (tested)
4. **Deterministic metrics**: Degree, betweenness produce identical values on repeat  (tested)
5. **Network fingerprint stability**: Queries don't modify networks  (tested)
6. **Round-trip safety**: Data conversions preserve structure  (tested)
7. **Exception safety**: Typed exceptions, no state corruption  (tested)
8. **Empty-network robustness**: All operations handle empty inputs  (tested)
9. **Null model correctness**: Structural invariants preserved  (tested)
10. **API symmetry**: Node and edge operations have documented parity  (tested)

### Test Design Principles

All new tests follow these principles:

1. **Small synthetic networks**: Use networks with known ground truth (e.g., known degree sequences, known layer memberships)
2. **No flaky tests**: All tests are deterministic; probabilistic tests use lenient thresholds
3. **Explicit invariants**: Tests assert properties, not just execution success
4. **Meaningful failures**: Each test fails if a documented guarantee breaks
5. **CI-friendly**: All tests complete in <1 second on typical hardware
6. **No external dependencies**: Tests use only pytest (and hypothesis where clearly justified)

### How to Run Tests

```bash
# Run all new test modules
pytest tests/test_dsl_ast_equivalence.py \
       tests/test_provenance_schema.py \
       tests/test_determinism_randomness.py \
       tests/test_roundtrip_invariants.py \
       tests/test_node_edge_parity.py \
       tests/test_exception_taxonomy.py \
       tests/test_coverage_grouping.py \
       tests/test_nullmodel_sanity.py \
       tests/test_dsl_graphops_equivalence.py \
       tests/test_degenerate_networks.py

# Run specific test class
pytest tests/test_dsl_ast_equivalence.py::TestASTStability -v

# Run with coverage
pytest tests/test_*.py --cov=py3plex --cov-report=html
```

### Known Limitations

1. **Legacy DSL equivalence**: String DSL vs Q builder AST equivalence is not fully tested (legacy DSL has different internal representation)
2. **Pipeline provenance**: Pipeline API provenance testing is limited (graph_ops doesn't always attach provenance)
3. **Community detection**: Leiden tests are marked `@pytest.mark.slow` and excluded from fast test runs
4. **Hypothesis integration**: Property-based tests are used conservatively (determinism tests only)

### Future Expansion

Recommended areas for future test coverage:

1. **Performance regression tests**: Benchmark key operations to detect slowdowns
2. **Memory leak tests**: Monitor memory usage for long-running operations
3. **Concurrency tests**: Verify thread-safety of stateful operations
4. **Integration tests**: End-to-end workflows from data loading to export
5. **Property-based tests**: Expand use of Hypothesis for edge-case discovery

---

**Repo State Note**: As of February 2026, py3plex has 210+ new deterministic tests (203 baseline + 7 for UQ propagation) enforcing 10+ major architectural guarantees across DSL, provenance, determinism, round-trips, parity, exceptions, grouping, null models, API equivalence, edge cases, and UQ propagation. All tests are automated, CI-friendly, and passing. Test coverage has improved from 8% to 14.7% through focused testing of core modules, utilities, and validation infrastructure.

**Embedding Primitive Update** (March 2026): Added first-class embedding API under `py3plex/ml/embedding/` (BaseEmbedding, Node2Vec, DeepWalk, NetMF, LINE, MetaPath2Vec, multiplex variants, trainer/utilities, similarity/evaluation helpers), unified `multi_layer_network.embed(...)` entry point, graph_ops `.embed(...)`, DSL embedding method compatibility, and pipeline `NodeEmbedding` step.

**v1.2 Update** (March 2026): Repository expanded with 8 new infrastructure packages (`algebra`, `embeddings`, `experiments`, `meta`, `optimizer`, `out_of_core`, `runtime`, `centrality`) and major DSL subsystem additions (`dsl/lint/`, `dsl/program/`, `dsl/executors/`). Test suite grown to 8,942 tests across 539 test files. Property-based test suite stable at 113 files; added `test_io_metamorphic_roundtrip.py`, `test_meta_properties.py`, `test_versatility_metamorphic.py` to property suite. Embeddings now include MetaPath2Vec (`py3plex/embeddings/metapath2vec.py`) with dedicated coverage in `tests/test_metapath2vec.py`, and examples include `examples/advanced/example_metapath2vec.py`. Total of 267 example scripts, 459 Python modules in py3plex, ~171K LOC.

**v1.1.3 Update** (February 2026): Repository state documentation updated to reflect current statistics: 8,000+ tests across 537 test files (~14.7% coverage), 446 Python modules in py3plex, ~168K total lines of code, and 264 example scripts. Property-based test suite significantly expanded from 13 to 113 files. Test coverage maintained at ~14.7% through ongoing test improvements. Version 1.1.3 includes continued enhancements to the comprehensive AI agent documentation (AGENTS.md).

**v1.1+ UQ Propagation Update** (January 2026): Implemented first-class uncertainty propagation semantics with `mode="propagate"` option in `.uq()`. This enables quantification of selection stability (p_present, p_selected, rank_uq) when queries include filtering, ordering, and selection operations. The propagate mode executes the full query end-to-end per replicate, capturing how uncertain metric values affect which items appear in final results. Aggregation now uses UQAlgebra to preserve uncertainty through grouping operations instead of silently dropping it. All changes are backward compatible (default mode="summarize_only"). New test module: tests/test_dsl_uq_propagation.py (7 deterministic tests).

**March 2026 Statistics Update**: AGENTS.md refreshed with verified repository counts — 539 test files (553 total Python files in tests/), 8,942 individual tests, 113 property-based test files, 459 Python modules in py3plex/, 267 example scripts, ~171K lines of code (~14.7% statement coverage).
