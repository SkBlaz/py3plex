# RewriteEngine Documentation

## Overview

The RewriteEngine implements correctness-preserving program transformations for py3plex Graph Programs. It applies equivalence-preserving rewrite rules to optimize queries without changing semantics.

## Architecture

### Core Components

1. **Match**: Represents a successful pattern match with captured subexpressions
2. **RewriteContext**: Execution context with network statistics and metadata
3. **RuleGuard**: Preconditions for safe rule application
4. **RewriteRule**: Pattern + guard + transformation
5. **RewriteEngine**: Orchestrates rule application with provenance tracking

### Design Principles

- **Correctness-preserving**: All transformations preserve query semantics
- **Immutable**: Returns new GraphProgram instances
- **Guarded**: Safety checks before applying transformations
- **Provenance**: Tracks all applied rules
- **Fixpoint**: Iterates until no more rules apply

## Implemented Rewrite Rules (17 total)

### A. Pushdown/Fusion Rules (5 rules)

#### 1. `push_where_past_compute`
**Pattern**: `COMPUTE(x) WHERE(intrinsic_field=v)`  
**Transform**: `WHERE(intrinsic_field=v) COMPUTE(x)`  
**Benefit**: Reduces number of nodes/edges to compute metrics for  
**Guard**: WHERE uses only intrinsic fields (layer, type, id, source, target)

```python
# Before
Q.nodes().compute("degree").where(layer="social")

# After (conceptually)
Q.nodes().where(layer="social").compute("degree")
# → Fewer nodes to compute degree for
```

#### 2. `fuse_compute`
**Pattern**: Multiple COMPUTE operations  
**Transform**: Batch into single compute pass  
**Benefit**: Reduces overhead from multiple computation passes  
**Guard**: Always safe

```python
# Before
compute("degree") → compute("betweenness") → compute("clustering")

# After
compute("degree", "betweenness", "clustering")
```

#### 3. `fuse_where`
**Pattern**: Multiple WHERE clauses with AND  
**Transform**: Single normalized predicate  
**Benefit**: Reduces filtering passes  
**Guard**: Always safe

```python
# Before
WHERE(a) AND WHERE(b)

# After
WHERE(a AND b)
```

#### 4. `push_limit_early`
**Pattern**: `COMPUTE(x) LIMIT(k)` [no ORDER BY]  
**Transform**: `LIMIT(k) COMPUTE(x)`  
**Benefit**: Computes metrics for fewer items  
**Guard**: No ORDER BY present

```python
# Before
Q.nodes().compute("degree").limit(10)  # No order_by

# After (conceptually)
Q.nodes().limit(10).compute("degree")
```

#### 5. `push_projection`
**Pattern**: `COMPUTE(a, b, c) SELECT_COLS(a, b)`  
**Transform**: `COMPUTE(a, b) SELECT_COLS(a, b)`  
**Benefit**: Eliminates unused metric computation  
**Guard**: Unused metrics not referenced in ORDER BY or WHERE

```python
# Before
compute("degree", "betweenness", "clustering").select("degree", "betweenness")

# After
compute("degree", "betweenness").select("degree", "betweenness")
# → Clustering not computed at all
```

### B. Layer Distributivity Rules (3 rules)

#### 6. `move_per_layer_early`
**Pattern**: `COMPUTE(layer_local_metric) PER_LAYER()`  
**Transform**: `PER_LAYER() COMPUTE(layer_local_metric)`  
**Benefit**: Enables layer-parallel processing  
**Guard**: All metrics are layer-local (degree, clustering, triangles)

```python
# Before
Q.nodes().compute("degree").per_layer()

# After (conceptually)
Q.nodes().per_layer().compute("degree")
# → Each layer processed independently
```

#### 7. `fuse_per_layer`
**Pattern**: Nested PER_LAYER groupings  
**Transform**: Single PER_LAYER  
**Benefit**: Eliminates redundant grouping  
**Guard**: Always safe

#### 8. `group_by_to_per_layer`
**Pattern**: `GROUP_BY(layer)`  
**Transform**: Canonical PER_LAYER form  
**Benefit**: Normalizes representation  
**Guard**: Always safe

### C. UQ-Aware Rules (3 rules)

#### 9. `move_deterministic_into_uq`
**Pattern**: `UQ(COMPUTE(x)) WHERE(intrinsic)`  
**Transform**: `UQ(WHERE(intrinsic) COMPUTE(x))`  
**Benefit**: Reduces sampling cost by filtering first  
**Guard**: WHERE is deterministic (intrinsic fields only)

```python
# Before
Q.nodes().compute("degree").uq(method="bootstrap", n_samples=100).where(layer="social")

# After (conceptually)
Q.nodes().where(layer="social").compute("degree").uq(method="bootstrap", n_samples=100)
# → Filter applied before each sample
```

#### 10. `hoist_reporting_outside_uq`
**Pattern**: `UQ(COMPUTE(x) EXPORT(csv))`  
**Transform**: `EXPORT(UQ(COMPUTE(x)), csv)`  
**Benefit**: Avoids exporting intermediate samples  
**Guard**: EXPORT is pure reporting

#### 11. `cache_uq_subprogram`
**Pattern**: `UQ(COMPUTE(deterministic_metrics))`  
**Transform**: Add caching hint  
**Benefit**: Avoids recomputing deterministic parts across samples  
**Guard**: All metrics are deterministic

### D. Community-Specific Rules (3 rules)

#### 12. `fuse_community_annotation`
**Pattern**: `COMMUNITIES(method) JOIN NODES`  
**Transform**: `NODES.annotate_community(method)`  
**Benefit**: Avoids materializing full community table  
**Guard**: Communities only used for annotation

#### 13. `community_to_partition_slice`
**Pattern**: `COMMUNITIES() WHERE(community_id=k)`  
**Transform**: `PARTITION_SLICE(k)`  
**Benefit**: Direct access to single community  
**Guard**: Single community filter

```python
# Before
Q.communities().where(community_id=5)

# After (conceptually)
# Direct partition slice access
```

#### 14. `batch_community_metrics`
**Pattern**: Multiple COMPUTE on communities  
**Transform**: Batched computation  
**Benefit**: Single pass over communities  
**Guard**: Always safe

### E. CSE/Caching Rules (2 rules)

#### 15. `detect_common_subexpression`
**Pattern**: Metric used in multiple places  
**Transform**: Mark for caching  
**Benefit**: Compute once, reuse multiple times  
**Guard**: Multiple uses detected

```python
# Before
compute("degree").where(degree__gt=5).order_by("degree")
# → degree used 3 times

# After
compute("degree") [cache=True].where(degree__gt=5).order_by("degree")
# → degree computed once and cached
```

#### 16. `cache_expensive_metrics`
**Pattern**: Expensive centrality metrics  
**Transform**: Mark for aggressive caching  
**Benefit**: Avoids recomputation of expensive metrics  
**Guard**: Not already cached

```python
# Expensive metrics automatically cached
compute("betweenness_centrality", "closeness_centrality")
```

### F. Additional Optimization Rules (2 bonus rules)

#### 17. `eliminate_redundant_order_by`
**Pattern**: `ORDER_BY(x) GROUP_BY(y)` where y ≠ x  
**Transform**: Remove ORDER_BY  
**Benefit**: Avoids unnecessary sorting  
**Guard**: ORDER BY rendered redundant by GROUP BY

#### 18. `optimize_top_k`
**Pattern**: `ORDER_BY(x) LIMIT(k)`  
**Transform**: `TOP_K(x, k)` [heap-based]  
**Benefit**: O(n log k) instead of O(n log n)  
**Guard**: k < n/10 (k is small relative to n)

```python
# Before
Q.nodes().compute("degree").order_by("degree", desc=True).limit(10)
# → Full sort O(n log n)

# After (conceptually)
Q.nodes().compute("degree").top_k("degree", 10)
# → Heap-based O(n log k)
```

## Usage

### Basic Usage

```python
from py3plex.dsl import Q
from py3plex.dsl.program import GraphProgram, apply_rewrites

# Create query
query = Q.nodes().compute("degree").where(layer="social").to_ast()
program = GraphProgram.from_ast(query)

# Apply rewrites
optimized = apply_rewrites(program)

# Execute
result = optimized.execute(network)
```

### With Custom Context

```python
from py3plex.dsl.program import apply_rewrites, RewriteContext

# Create context with network statistics
context = RewriteContext(
    network_stats={'node_count': 10000, 'edge_count': 50000},
    available_metrics={'degree'},  # Already computed
    safety_mode=False,
)

# Apply rewrites with context
optimized = apply_rewrites(program, context=context)
```

### Custom Rule Sets

```python
from py3plex.dsl.program import (
    apply_rewrites,
    get_standard_rules,
    get_conservative_rules,
    get_aggressive_rules,
)

# Conservative (safe subset)
optimized = apply_rewrites(program, rules=get_conservative_rules())

# Aggressive (all rules)
optimized = apply_rewrites(program, rules=get_aggressive_rules())

# Custom selection
from py3plex.dsl.program.rewrite import rule_push_where_past_compute, rule_fuse_compute
custom_rules = [rule_push_where_past_compute(), rule_fuse_compute()]
optimized = apply_rewrites(program, rules=custom_rules)
```

### Using RewriteEngine Directly

```python
from py3plex.dsl.program import RewriteEngine, get_standard_rules

# Create engine
engine = RewriteEngine(
    rules=get_standard_rules(),
    max_iterations=10,
    enable_provenance=True,
)

# Apply with fixpoint
optimized = engine.apply(program, fixpoint=True)

# Explain which rewrites would apply
applicable = engine.explain_rewrites(program)
print(f"Applicable rules: {applicable}")
```

### Provenance Tracking

```python
# Check provenance
print(optimized.metadata.provenance_chain)
# ['from_ast', 'rewrites:push_where_past_compute,fuse_compute,cache_expensive_metrics']

# Compare before/after
diff = optimized.diff(program)
print(f"Programs identical: {diff['identical']}")
```

## Rule Priority

Rules are applied in priority order (higher priority first):

- Priority 10: `push_where_past_compute`
- Priority 9: `push_limit_early`
- Priority 8: `fuse_compute`, `fuse_where`, `move_deterministic_into_uq`
- Priority 7: `push_projection`, `move_per_layer_early`, `hoist_reporting_outside_uq`, `fuse_community_annotation`, `optimize_top_k`
- Priority 6: `fuse_per_layer`, `cache_uq_subprogram`, `community_to_partition_slice`, `cache_expensive_metrics`
- Priority 5: `group_by_to_per_layer`, `batch_community_metrics`, `detect_common_subexpression`
- Priority 4: `eliminate_redundant_order_by`

## Fixpoint Iteration

By default, the engine applies rules iteratively until no more rules apply (fixpoint):

```python
# Fixpoint mode (default)
optimized = apply_rewrites(program, fixpoint=True)

# Single pass mode
optimized = apply_rewrites(program, fixpoint=False)
```

The engine will iterate up to `max_iterations` (default: 10) to prevent infinite loops.

## Equivalence Guarantees

All rewrite rules preserve query semantics:

1. **Result equivalence**: Same results on same input network
2. **Type preservation**: Output type signature unchanged
3. **Determinism**: Same rewrites produce same optimized program
4. **Composability**: Rewrites can be applied in any valid order

### Testing Equivalence

```python
# Run both versions and compare results
result_original = program.execute(network)
result_optimized = optimized.execute(network)

# Results should be equivalent
assert result_original.to_pandas().equals(result_optimized.to_pandas())
```

## Performance Impact

Expected speedups from rewrites:

- **Pushdown rules**: 2-10x (fewer items to process)
- **Projection pushdown**: 1.5-5x (fewer metrics to compute)
- **UQ-aware rules**: 2-5x (reduced sampling cost)
- **CSE/Caching**: 2-10x (avoid recomputation)
- **TOP-K optimization**: 5-20x for small k (heap vs. full sort)
- **Community optimization**: 10-100x (direct slice access)

## Integration with GraphProgram

The RewriteEngine integrates with GraphProgram's `optimize()` method:

```python
# GraphProgram.optimize() will use rewrite engine (when implemented)
program = GraphProgram.from_ast(query)
optimized = program.optimize()  # Currently returns self (placeholder)
```

## Future Extensions

Planned enhancements:

1. **Cost-based optimization**: Use network statistics for cost estimation
2. **Learned rules**: Machine learning to identify beneficial rewrites
3. **Custom rules**: User-defined rewrite patterns
4. **Verification**: Formal proof of equivalence
5. **Profile-guided optimization**: Use execution profiles to select rules

## References

- AGENTS.md: Comprehensive AI agent documentation
- IMPLEMENTATION_GRAPH_PROGRAM.md: Graph Program implementation details
- py3plex/dsl/program/rewrite.py: Implementation
- tests/test_dsl_program_rewrite.py: Test suite
- examples/example_rewrite_engine.py: Working examples
