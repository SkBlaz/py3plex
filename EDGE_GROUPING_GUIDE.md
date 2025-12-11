# Edge Grouping and Coverage Guide

This guide explains the new DSL features for grouping and analyzing edges across layer pairs in multilayer networks.

## Overview

The DSL now supports:
- **per_layer_pair()** - Group edges by (source_layer, target_layer) pairs
- **Coverage for edges** - Find edges that appear across multiple layer pairs
- **Grouping metadata** - Introspect grouping structure in QueryResult.meta
- **group_summary()** - Summarize grouped results without recomputation

## Quick Start

### Basic Edge Grouping

```python
from py3plex.dsl import Q, L

# Group all edges by layer pairs
result = Q.edges().from_layers(L["*"]).per_layer_pair().execute(network)

# Access grouping metadata
print(result.meta["grouping"])
# Output: {
#   "kind": "per_layer_pair",
#   "target": "edges",
#   "keys": ["src_layer", "dst_layer"],
#   "groups": [...]
# }

# Get summary of groups
summary = result.group_summary()
print(summary)
#   src_layer dst_layer  n_items
# 0    layer0    layer0       10
# 1    layer0    layer1        5
# 2    layer1    layer1        8
```

### Top-K Edges Per Layer Pair

```python
# Get top-5 highest weight edges in each layer pair
result = (
    Q.edges()
     .from_layers(L["*"])
     .per_layer_pair()
        .top_k(5, "weight")
     .end_grouping()
     .execute(network)
)

df = result.to_pandas()
print(df[['source', 'target', 'source_layer', 'target_layer', 'weight']])
```

### Edge Coverage

Find edges that appear in top-k across multiple layer pairs:

```python
# Edges in top-5 of ALL layer pairs
result = (
    Q.edges()
     .from_layers(L["*"])
     .per_layer_pair()
        .top_k(5, "edge_betweenness_centrality")
     .end_grouping()
     .coverage(mode="all")
     .execute(network)
)

# Edges in top-5 of AT LEAST 2 layer pairs
result = (
    Q.edges()
     .from_layers(L["*"])
     .per_layer_pair()
        .top_k(5, "weight")
     .end_grouping()
     .coverage(mode="at_least", k=2)
     .execute(network)
)

# Edges in top-10 of AT LEAST 70% of layer pairs
result = (
    Q.edges()
     .from_layers(L["*"])
     .per_layer_pair()
        .top_k(10, "weight")
     .end_grouping()
     .coverage(mode="fraction", p=0.7)
     .execute(network)
)
```

## API Reference

### per_layer_pair()

Groups edge results by (src_layer, dst_layer) pairs.

**Only valid for edge queries.** Raises `DslExecutionError` if called on node queries.

```python
Q.edges().per_layer_pair().top_k(5, "weight")
```

### per_layer()

Groups node results by layer.

**Only valid for node queries.** Raises `DslExecutionError` if called on edge queries.

```python
Q.nodes().per_layer().top_k(5, "degree")
```

### coverage()

Filter items based on how many groups they appear in.

Works with both node (per_layer) and edge (per_layer_pair) grouping.

**Modes:**
- `"all"` - Items must appear in ALL groups
- `"any"` - Items in at least one group (equivalent to union)
- `"at_least"` - Items in at least k groups (requires `k` parameter)
- `"exact"` - Items in exactly k groups (requires `k` parameter)
- `"fraction"` - Items in at least p fraction of groups (requires `p` parameter, 0-1)

```python
.coverage(mode="all")
.coverage(mode="at_least", k=3)
.coverage(mode="fraction", p=0.8)
```

### group_summary()

Returns a pandas DataFrame with one row per group, showing:
- Grouping key columns (e.g., "layer" or "src_layer"/"dst_layer")
- `n_items` - Number of items in the group
- Any additional group-level metrics

```python
result = Q.edges().per_layer_pair().top_k(5, "weight").execute(network)
summary = result.group_summary()
print(summary)
```

Raises `GroupingError` if called on non-grouped results.

### to_pandas() with Grouping

Enhanced with new parameters:

```python
df = result.to_pandas(
    multiindex=False,      # Set True to use grouping keys as index
    include_grouping=True  # Set False to exclude grouping columns
)
```

## Grouping Metadata Structure

When using per_layer() or per_layer_pair(), `QueryResult.meta["grouping"]` contains:

```python
{
    "kind": str,           # "per_layer", "per_layer_pair", or "custom"
    "target": str,         # "nodes" or "edges"
    "keys": list,          # ["layer"] or ["src_layer", "dst_layer"]
    "groups": [            # List of group metadata
        {
            "key": dict,       # {"layer": "social"} or {"src_layer": "a", "dst_layer": "b"}
            "n_items": int,    # Number of items in this group
            # ... potentially other metrics
        },
        ...
    ]
}
```

## Error Handling

The DSL provides clear error messages for common mistakes:

```python
# Error: per_layer() on edges
Q.edges().per_layer()  
# DslExecutionError: per_layer() is defined only for node queries.
# For edge queries use per_layer_pair().

# Error: per_layer_pair() on nodes
Q.nodes().per_layer_pair()
# DslExecutionError: per_layer_pair() is defined only for edge queries.
# For node queries use per_layer().

# Error: coverage without grouping
Q.edges().coverage(mode="all")
# GroupingError: coverage() requires an active grouping (e.g. per_layer(), group_by('layer')).

# Error: group_summary without grouping
result = Q.edges().execute(network)
result.group_summary()
# GroupingError: group_summary() is only defined for grouped results.
```

## Comparison: Nodes vs Edges

| Feature | Nodes | Edges |
|---------|-------|-------|
| Grouping method | `per_layer()` | `per_layer_pair()` |
| Group by | Single layer | (src_layer, dst_layer) pair |
| Grouping keys | `["layer"]` | `["src_layer", "dst_layer"]` |
| Coverage identity | Node ID | (source, target) tuple |
| DataFrame columns | id, layer | source, target, source_layer, target_layer |

## Examples

See `examples/network_analysis/example_dsl_edge_grouping.py` for complete working examples demonstrating:
1. Basic per_layer_pair grouping
2. Top-k edges per layer pair
3. Coverage filtering for edges
4. Using multiindex DataFrames
5. Comparing node and edge grouping

## Testing

Run tests with:
```bash
pytest tests/test_dsl_edge_grouping_coverage.py
pytest tests/test_dsl_grouping_coverage.py
```

## Implementation Details

- **builder.py**: per_layer() and per_layer_pair() methods with target validation
- **executor.py**: Enhanced grouping logic supporting src_layer/dst_layer fields
- **result.py**: Updated to_pandas() with multiindex support, new group_summary() method
- **Backward compatible**: All existing DSL functionality preserved

## Migration Notes

If you previously had code that tried to use per_layer() on edges:

**Before (would fail or behave unexpectedly):**
```python
Q.edges().per_layer().execute(network)  # Error or wrong behavior
```

**After (use per_layer_pair):**
```python
Q.edges().per_layer_pair().execute(network)  # Correct
```

All node queries continue to work exactly as before.
