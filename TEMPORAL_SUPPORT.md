# Temporal Support in py3plex

This document describes the temporal support features added to py3plex, allowing time-aware analysis of multilayer networks.

## Overview

Py3plex now supports optional temporal information on edges, enabling:
- Time-based network analysis without breaking existing code
- Snapshot queries (network state at a specific time)
- Time range queries (network state during a time interval)
- Integration with the DSL for high-level temporal queries

## Features

### 1. Temporal Attribute Conventions

Edges can have optional temporal attributes following these conventions:

#### Point-in-Time Edges
```python
{'source': 'A', 'target': 'B', 't': 100.0, ...}
```
- Represents a discrete event at time `t`
- Active only at exactly time `t` in snapshot queries
- Included in range queries if `t` is within the range

#### Interval Edges
```python
{'source': 'A', 'target': 'B', 't_start': 100.0, 't_end': 200.0, ...}
```
- Represents a continuous state during `[t_start, t_end]`
- Active during the entire interval
- Included in queries if the interval overlaps the query range

#### Atemporal Edges
```python
{'source': 'A', 'target': 'B', 'weight': 1.0}
```
- Edges without any temporal attributes
- Always included in temporal queries
- Ensures backwards compatibility with existing networks

### 2. TemporalMultinetView

A thin, non-owning wrapper that filters edges based on temporal constraints.

```python
from py3plex.temporal_view import TemporalMultinetView

# Create temporal view
view = TemporalMultinetView(network)

# Snapshot at specific time
snapshot = view.snapshot_at(150.0)
edges = list(snapshot.iter_edges())

# Time range query
range_view = view.with_slice(100.0, 200.0)
edges = list(range_view.iter_edges())

# Open-ended ranges
after_view = view.with_slice(200.0, None)  # From 200 onwards
before_view = view.with_slice(None, 150.0)  # Up to 150
```

### 3. DSL Builder API

High-level temporal queries using the chainable builder API.

```python
from py3plex.dsl import Q

# Snapshot query
result = Q.edges().at(150.0).execute(network)

# Time range query
result = Q.edges().during(100.0, 200.0).execute(network)

# Open-ended ranges
result = Q.edges().during(100.0, None).execute(network)

# Chain with other clauses
result = (
    Q.edges()
     .during(100.0, 200.0)
     .limit(10)
     .execute(network)
)
```

### 4. Temporal Utilities

Utilities for parsing and extracting temporal information.

```python
from py3plex.temporal_utils import extract_edge_time, _parse_time

# Parse various time formats
t = _parse_time(1234567890)           # int/float
t = _parse_time("2009-02-13T23:31:30")  # ISO string
t = _parse_time(datetime_object)        # datetime

# Extract edge temporal information
edge_attrs = {'t': 100.0, 'weight': 1.0}
interval = extract_edge_time(edge_attrs)
# Returns: EdgeTimeInterval(start=100.0, end=100.0)
```

## Implementation Details

### Architecture

The temporal support is implemented as a thin layer on top of existing py3plex functionality:

1. **temporal_utils.py**: Parsing and extraction utilities
2. **temporal_view.py**: TemporalMultinetView wrapper class
3. **dsl/ast.py**: TemporalContext AST node
4. **dsl/executor.py**: Temporal query execution
5. **dsl/builder.py**: Builder API methods (at(), during())

### Design Principles

- **Minimal and non-breaking**: No changes to core data structures
- **Opt-in**: Temporal features are used only when explicitly requested
- **Backwards compatible**: Networks without time data work unchanged
- **Read-only**: TemporalMultinetView doesn't copy or modify data
- **Type-safe**: Full type hints throughout

### Performance

- **Zero overhead**: No performance cost for networks without temporal queries
- **Efficient filtering**: Only filters on access, no data copying
- **Lazy evaluation**: Iterator-based design for large networks

## Examples

See `examples/network_analysis/example_temporal_networks.py` for comprehensive examples including:

1. Low-level TemporalMultinetView usage
2. High-level DSL builder API
3. Analyzing network evolution over time
4. Different temporal attribute conventions
5. Backwards compatibility demonstrations

## Testing

The temporal support includes 36 comprehensive tests:

- **temporal_utils.py**: 13 tests covering parsing and extraction
- **temporal_view.py**: 11 tests covering filtering and views
- **DSL integration**: 4 tests for AST and executor
- **Builder API**: 6 tests for at() and during()
- **Graceful degradation**: 2 tests for atemporal networks

All existing tests (325 total) continue to pass.

## API Reference

### TemporalMultinetView

```python
class TemporalMultinetView:
    def __init__(self, base_multinet, time_attr="t", 
                 t_start_attr="t_start", t_end_attr="t_end")
    
    def with_slice(self, t0: Optional[float], t1: Optional[float]) -> "TemporalMultinetView"
    def snapshot_at(self, t: float) -> "TemporalMultinetView"
    def iter_edges(self, *args, **kwargs) -> Iterator[Any]
    def get_edges(self, *args, **kwargs) -> List[Any]
    
    @property
    def base_network(self) -> Any
    
    @property
    def temporal_slice(self) -> TemporalSlice
```

### DSL Builder API

```python
class QueryBuilder:
    def at(self, t: float) -> "QueryBuilder"
    def during(self, t0: Optional[float] = None, 
               t1: Optional[float] = None) -> "QueryBuilder"
```

### Temporal Utilities

```python
def _parse_time(value: TimeLike) -> float
def extract_edge_time(attrs: dict[str, Any]) -> EdgeTimeInterval

@dataclass
class EdgeTimeInterval:
    start: Optional[float]
    end: Optional[float]
    
    def overlaps(self, t0: Optional[float], t1: Optional[float]) -> bool
```

## Future Enhancements

The following features are deferred for future development:

1. **Named temporal ranges**: `DEFINE RANGE Q1_2023 AS [start, end]`
2. **String DSL parser**: `AT 150.0` and `DURING [100, 200]` syntax
3. **Parametric temporal queries**: Support for `Param` references in temporal contexts
4. **Temporal aggregations**: Time-windowed statistics and metrics
5. **Temporal joins**: Combining networks based on temporal overlap

## Migration Guide

### For New Code

Add temporal attributes to edges when creating networks:

```python
network.add_edges([
    {'source': 'A', 'target': 'B', 
     'source_type': 'layer1', 'target_type': 'layer1',
     't': 100.0},  # Point-in-time
])
```

Use temporal queries when needed:

```python
# Low-level API
view = TemporalMultinetView(network)
snapshot = view.snapshot_at(150.0)

# High-level API
result = Q.edges().at(150.0).execute(network)
```

### For Existing Code

No changes required! The temporal support is:
- Completely opt-in
- Backwards compatible
- Zero overhead when not used

Existing networks without temporal attributes work exactly as before.

## References

- **Issue**: #[issue-number] - Temporal support implementation
- **Examples**: `examples/network_analysis/example_temporal_networks.py`
- **Tests**: `tests/test_temporal*.py`
- **Documentation**: Module docstrings in `temporal_utils.py` and `temporal_view.py`
