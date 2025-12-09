# DSL Grouping and Coverage: Per-Layer Analysis

This document describes the new grouping and coverage features in py3plex DSL v2, which enable elegant per-layer network analysis without manual loops.

## Overview

The new API allows you to:
- Group nodes/edges by layer (or other attributes)
- Apply per-group operations like top-k selection
- Filter results based on coverage across groups (e.g., nodes that appear in top-k in ALL layers)

## Quick Start

### Before: Manual Loop

```python
from py3plex.core import random_generators
from py3plex.dsl import Q, L

net = random_generators.random_multilayer_ER(n=300, l=3, p=0.02, directed=False)

# Manual loop to find cross-layer hubs
layer_top = {}
for layer in net.layers:
    res = (
        Q.nodes()
         .from_layers(L[str(layer)])
         .where(degree__gt=1)
         .compute("degree", "betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(5)
         .execute(net)
    )
    layer_top[layer] = set(res.to_pandas()["id"])

# Find nodes that are hubs in ALL layers
baseline_multi_hubs = set.intersection(*layer_top.values())
```

### After: Single DSL Query

```python
from py3plex.core import random_generators
from py3plex.dsl import Q, L

net = random_generators.random_multilayer_ER(n=300, l=3, p=0.02, directed=False)

# Single elegant query
multi_hubs = (
    Q.nodes()
     .from_layers(L["*"])                   # wildcard: all layers
     .where(degree__gt=1)
     .compute("degree", "betweenness_centrality")
     .per_layer()                           # group by layer
        .top_k(5, "betweenness_centrality") # top 5 per layer
     .end_grouping()
     .coverage(mode="all")                  # intersection across layers
     .execute(net)
)

df = multi_hubs.to_pandas()
multi_hub_ids = set(df["id"])
```

## API Reference

### Grouping

#### `.group_by(*fields)`
Low-level grouping primitive that groups results by specified fields.

```python
Q.nodes().group_by("layer")  # Group by layer
Q.nodes().group_by("layer", "community")  # Group by multiple fields
```

#### `.per_layer()`
Sugar for `.group_by("layer")` - the most common grouping operation.

```python
Q.nodes().per_layer()  # Equivalent to .group_by("layer")
```

### Per-Group Operations

#### `.top_k(k, key=None)`
Keep top-k items per group, ordered by the specified key.

**Requirements:**
- Must be called after `.group_by()` or `.per_layer()`
- If `key` is provided, sets ordering to descending by that key

```python
# Top 5 nodes per layer by betweenness
Q.nodes().per_layer().top_k(5, "betweenness_centrality")

# Top 10 per layer by degree
Q.nodes().per_layer().top_k(10, "degree")

# Use existing ordering
Q.nodes().per_layer().order_by("-degree").top_k(5)
```

#### `.end_grouping()`
Optional marker for readability - separates grouping operations from post-grouping filters.

```python
Q.nodes()
  .per_layer()
    .top_k(5, "degree")
  .end_grouping()  # Visual separator
  .coverage(mode="all")
```

### Coverage Filtering

#### `.coverage(mode, k=None, id_field="id")`
Filter items based on how many groups they appear in.

**Modes:**
- `"all"`: Keep items that appear in **ALL** groups (intersection)
- `"any"`: Keep items that appear in **AT LEAST ONE** group (union)
- `"at_least"`: Keep items that appear in **at least k** groups (requires `k` parameter)
- `"exact"`: Keep items that appear in **exactly k** groups (requires `k` parameter)

**Requirements:**
- Must be called after `.group_by()` or `.per_layer()`
- Currently only supported for node queries (raises clear error for edges)

```python
# Intersection: nodes in top-5 in ALL layers
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="all")

# Union: nodes in top-5 in ANY layer
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="any")

# At least 2: nodes in top-5 in at least 2 layers
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="at_least", k=2)

# Exactly 2: nodes in top-5 in exactly 2 layers
Q.nodes().per_layer().top_k(5, "degree").coverage(mode="exact", k=2)
```

### Wildcard Layer Selection

#### `L["*"]`
Select all layers in the network.

```python
Q.nodes().from_layers(L["*"])  # All layers
Q.nodes().from_layers(L["*"] - L["bots"])  # All layers except "bots"
Q.nodes().from_layers(L["*"] & L["social"])  # Intersection with "social"
```

## Examples

### Example 1: Find Multi-Layer Hubs

Find nodes that are in the top-5 by betweenness centrality in **all** layers:

```python
multi_hubs = (
    Q.nodes()
     .from_layers(L["*"])
     .where(degree__gt=1)
     .compute("betweenness_centrality")
     .per_layer()
        .top_k(5, "betweenness_centrality")
     .end_grouping()
     .coverage(mode="all")
     .execute(net)
)
```

### Example 2: Find Consistent Hubs Across Multiple Layers

Find nodes that appear in top-10 by degree in at least 3 layers:

```python
consistent_hubs = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree")
     .per_layer()
        .top_k(10, "degree")
     .end_grouping()
     .coverage(mode="at_least", k=3)
     .execute(net)
)
```

### Example 3: Layer-Specific Hubs

Find nodes that are hubs in exactly one layer (layer-specific hubs):

```python
layer_specific = (
    Q.nodes()
     .from_layers(L["*"])
     .compute("degree", "betweenness_centrality")
     .per_layer()
        .top_k(5, "betweenness_centrality")
     .end_grouping()
     .coverage(mode="exact", k=1)
     .execute(net)
)
```

### Example 4: Exclude Specific Layers

Find hubs across social and professional layers, excluding bot layer:

```python
human_hubs = (
    Q.nodes()
     .from_layers(L["*"] - L["bots"])
     .where(degree__gt=1)
     .compute("betweenness_centrality")
     .per_layer()
        .top_k(5, "betweenness_centrality")
     .end_grouping()
     .coverage(mode="all")
     .execute(net)
)
```

## Important Notes

### Coverage Identity

For node queries, coverage uses the **logical node ID** (first element of the `(node_id, layer)` tuple). This means:
- `(node_5, layer_0)` and `(node_5, layer_1)` are treated as the **same entity**
- Coverage counts how many layers each unique node ID appears in

### Edge Coverage

Coverage filtering is currently only supported for **node queries**. Attempting to use coverage with edge queries will raise a clear `DslExecutionError`.

### Measure Computation Scope

When using grouping with wildcard layers (`L["*"]`), measures like degree and betweenness are computed on the **combined subgraph** of all selected layers. This differs from computing measures separately per layer.

For strict per-layer computation:
- Use separate queries per layer (manual loop approach)
- This computes measures on each layer's isolated subgraph

The grouping approach is appropriate for analyzing the multilayer structure as a whole.

## Error Handling

The API includes comprehensive validation:

```python
# Error: top_k requires prior grouping
Q.nodes().top_k(5, "degree")  # ❌ ValueError

# Error: coverage requires prior grouping
Q.nodes().coverage(mode="all")  # ❌ ValueError

# Error: at_least mode requires k parameter
Q.nodes().per_layer().coverage(mode="at_least")  # ❌ ValueError

# Error: invalid coverage mode
Q.nodes().per_layer().coverage(mode="invalid")  # ❌ ValueError

# Error: coverage not supported for edges
Q.edges().per_layer().top_k(5, "weight").coverage(mode="all")  # ❌ DslExecutionError
```

## Testing

The implementation includes comprehensive tests:

```bash
# Run grouping and coverage tests
pytest tests/test_dsl_grouping_coverage.py -v

# 23 tests covering:
# - Wildcard layer expressions
# - Grouping basics
# - Top-k per group
# - All coverage modes
# - Error handling
# - Backward compatibility
```

## See Also

- `py3plex/dsl/ast.py` - AST definitions for grouping/coverage
- `py3plex/dsl/builder.py` - Builder API implementation
- `py3plex/dsl/executor.py` - Execution logic for grouping/coverage
- `tests/test_dsl_grouping_coverage.py` - Comprehensive test suite
