# Temporal Multilayer Network Examples

This directory contains examples demonstrating the temporal multilayer network features in py3plex.

## Overview

The temporal multilayer network engine provides:

1. **TemporalMultiLayerNetwork**: A class for networks with time-stamped edges
2. **Streaming Algorithms**: Incremental algorithms that process temporal data efficiently
3. **DSL Extensions**: Query syntax for temporal filtering and windowing
4. **Duration Parsing**: Support for human-readable duration strings ("7d", "24h", "30m")
5. **Windowed Query Execution**: Execute queries over sliding time windows with result aggregation

## Examples

### 1. `example_temporal_network.py`

Comprehensive demonstration of temporal network features:

- Creating temporal networks with time-stamped edges
- Time-based slicing and filtering
- Snapshot generation (cumulative and exact)
- Sliding window iteration (overlapping and non-overlapping)
- Streaming PageRank algorithm
- Streaming community change detection

**Run:**
```bash
python examples/temporal/example_temporal_network.py
```

**Key Features Demonstrated:**
```python
# Create temporal network
tnet = TemporalMultiLayerNetwork(directed=True)

# Add time-stamped edges
tnet.add_edge('Alice', 'social', 'Bob', 'social', t=100.0)

# Query by time range
edges = list(tnet.edges_between(100.0, 200.0))

# Create snapshot at specific time
snapshot = tnet.snapshot_at(150.0, mode="up_to")

# Iterate over sliding windows
for t_start, t_end, window_net in tnet.window_iter(window_size=100.0, step=50.0):
    # Process each window
    pass

# Streaming algorithms
for t_start, t_end, scores in streaming_pagerank(tnet, window_size=100.0):
    print(f"Window [{t_start}, {t_end}]: {scores}")
```

### 2. `example_temporal_dsl.py`

Demonstration of DSL temporal query features:

- Temporal filters in `where()` clause
- Window specifications
- Combining temporal and spatial queries
- Complex query composition

**Run:**
```bash
python examples/temporal/example_temporal_dsl.py
```

**Key Features Demonstrated:**
```python
from py3plex.dsl import Q, L

# Temporal filter with t__between
q = Q.edges().where(t__between=(100.0, 200.0))

# Time range filters
q = Q.edges().where(t__gte=100.0, t__lte=200.0)

# Window specification
q = Q.nodes().compute("degree").window(100.0, step=50.0)

# Complex temporal query
q = (
    Q.nodes()
    .from_layers(L["social"] + L["work"])
    .where(t__between=(100.0, 250.0))
    .compute("degree", "betweenness_centrality")
    .window(100.0, step=50.0)
    .order_by("betweenness_centrality", desc=True)
    .limit(5)
)
```

### 3. `example_windowed_queries.py` **[NEW]**

Demonstration of windowed query execution with duration parsing:

- Duration string parsing ("7d", "24h", "30m")
- Windowed query execution with numeric and string durations
- Result aggregation (list and concat modes)
- Complex windowed queries with filtering
- Practical use case: tracking network evolution

**Run:**
```bash
python examples/temporal/example_windowed_queries.py
```

**Key Features Demonstrated:**
```python
from py3plex.dsl import Q
from py3plex.temporal_utils_extended import parse_duration_string

# Parse duration strings
seconds = parse_duration_string("7d")  # 604800.0
seconds = parse_duration_string("1.5h")  # 5400.0

# Windowed query with duration string
q = Q.nodes().compute("degree").window("3d", step="1d")
result = q.execute(tnet)

# Concatenated results across windows
q = Q.nodes().compute("degree").window("2d", aggregation="concat")
result = q.execute(tnet)
df = result.to_pandas()  # Includes window_start, window_end columns

# Complex windowed query
q = (
    Q.nodes()
    .from_layers(L["social"])
    .during(0, 7 * 86400.0)  # First week only
    .compute("degree")
    .window("2d")
    .order_by("degree", desc=True)
)
```

## Core Components

### TemporalMultiLayerNetwork

**Location:** `py3plex/core/temporal_multinet.py`

Main class for temporal multilayer networks. Wraps a `multi_layer_network` and adds temporal capabilities.

**Key Methods:**
- `add_edge(u, layer_u, v, layer_v, t, weight=1.0, **attr)`: Add single time-stamped edge
- `add_edges(edges, input_type="dict")`: Add multiple edges
- `edges_between(t_start, t_end, layers=None)`: Filter edges by time range
- `slice_time_window(t_start, t_end)`: Create time-sliced subnetwork
- `snapshot_at(t, mode="up_to")`: Generate snapshot at specific time
- `window_iter(window_size, step=None)`: Iterate over sliding windows
- `from_pandas(df)`: Create from DataFrame
- `from_multilayer_network(base_network)`: Create from existing network

### Streaming Algorithms

**Location:** `py3plex/algorithms/temporal/`

#### Centrality (`centrality.py`)

- **`streaming_pagerank(temporal_network, window_size, ...)`**
  - Incremental PageRank computation over windows
  - Uses previous window's scores as initialization
  - Much faster than recomputing from scratch

- **`streaming_degree_centrality(temporal_network, window_size, ...)`**
  - Simple degree-based centrality over windows
  - Baseline for comparison

#### Community (`community.py`)

- **`streaming_community_change(temporal_network, community_detector, window_size, ...)`**
  - Apply community detection over sliding windows
  - Compute change scores between consecutive windows
  - Metrics: Jaccard similarity, node moves, NMI

- **`detect_community_events(temporal_network, community_detector, window_size, ...)`**
  - Higher-level event detection (stable, high_change)
  - Identify significant community transitions

### DSL Extensions

**Location:** `py3plex/dsl/`

#### Duration Parsing **[NEW]**

**Location:** `py3plex/temporal_utils_extended.py`

Parse human-readable duration strings into seconds:

**`parse_duration_string(duration)`** - Convert duration strings to numeric values
- Supports: weeks (w), days (d), hours (h), minutes (m), seconds (s)
- Examples: "7d" → 604800.0, "1.5h" → 5400.0, "30m" → 1800.0

**`format_duration(seconds, precision=2)`** - Convert seconds to human-readable string
- Examples: 604800 → "1w", 90061 → "1d 1h", 3661 → "1h 1m"

#### WindowSpec (AST)

Specification for sliding window queries:
```python
WindowSpec(
    window_size: Union[float, str],  # Numeric or "7d", "1h"
    step: Optional[Union[float, str]] = None,
    start: Optional[float] = None,
    end: Optional[float] = None,
    aggregation: str = "list"  # "list", "concat"
)
```

#### Builder Methods

- **`.window(window_size, step=None, ...)`**
  - Add sliding window specification
  - Supports numeric and duration strings

- **`.where(t__between=(start, end))`**
  - Filter by time range

- **`.where(t__gte=time, t__lte=time)`**
  - Filter by time comparisons

- **`.at(t)` / `.during(t0, t1)` / `.before(t)` / `.after(t)`**
  - Existing temporal methods (now work with windows too)

## Use Cases

### 1. Dynamic Network Analysis

Track how network structure evolves over time:
```python
for t_start, t_end, window_net in tnet.window_iter(window_size=30*24*3600):  # 30 days
    # Analyze structure in each window
    density = window_net.get_base_network().core_network.number_of_edges() / ...
```

### 2. Temporal Centrality Evolution

Monitor important nodes over time:
```python
centrality_over_time = {}
for t_start, t_end, scores in streaming_pagerank(tnet, window_size=7*24*3600):
    centrality_over_time[(t_start, t_end)] = scores
```

### 3. Community Evolution

Track how communities form, merge, and split:
```python
for t_start, t_end, communities, change in streaming_community_change(
    tnet, detector, window_size=100
):
    if change > 0.5:
        print(f"Significant change at [{t_start}, {t_end}]")
```

### 4. Event Detection

Identify anomalies or significant events:
```python
for t_start, t_end, event_type, change in detect_community_events(
    tnet, detector, window_size=100, change_threshold=0.3
):
    if event_type == "high_change":
        print(f"Event detected at [{t_start}, {t_end}]")
```

## Testing

Comprehensive test suite with 55+ tests:

```bash
# Run all temporal tests
pytest tests/test_temporal*.py -v

# Run specific test files
pytest tests/test_temporal_multinet.py -v
pytest tests/test_temporal_algorithms.py -v
pytest tests/test_temporal_dsl.py -v
```

## Performance Considerations

### Memory

- TemporalMultiLayerNetwork stores all edges in memory
- For very large networks (>1M edges), consider:
  - Using larger window sizes
  - Processing in chunks
  - Using the streaming algorithms which maintain minimal state

### Computation

- Streaming algorithms are designed for efficiency
- `streaming_pagerank`: O(k * E_w) per window (k = iterations, E_w = edges in window)
- `streaming_community_change`: O(community_detection) per window
- Window iteration: O(E_total) to partition all temporal edges across windows

### Tips

1. Use overlapping windows (small step) for smoother analysis
2. Choose window size based on temporal granularity of your data
3. Use `return_type="snapshot"` for cumulative analysis
4. Use `return_type="temporal"` for incremental analysis

## Future Enhancements

Planned features:
- Executor support for windowed queries (in progress)
- Duration string parsing ("7d" → numeric)
- Result aggregation across windows
- Temporal graph neural network support
- Streaming anomaly detection

## References

- Core temporal utilities: `py3plex/temporal_utils.py`
- Temporal view layer: `py3plex/temporal_view.py`
- DSL documentation: `docfiles/how-to/query_with_dsl.rst`

## Support

For questions or issues:
- GitHub Issues: https://github.com/SkBlaz/py3plex/issues
- Documentation: https://py3plex.readthedocs.io/
