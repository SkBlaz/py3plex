# CLI Examples with Unix Piping

This directory contains examples demonstrating how to use py3plex from the command line with Unix piping for efficient data analysis workflows.

## Quick Start

```bash
# Verify installation
py3plex selftest

# Interactive tutorial
py3plex tutorial

# Quick demo
py3plex quickstart
```

## Core Commands

| Command | Description |
|---------|-------------|
| `create` | Generate random multilayer networks |
| `load` | Load and inspect network files |
| `query` | Execute DSL queries on networks |
| `stats` | Compute multilayer statistics |
| `community` | Detect communities |
| `centrality` | Compute node centrality |
| `visualize` | Create network visualizations |
| `convert` | Convert between file formats |

## Unix Piping Support

py3plex supports Unix piping with `-` as input argument. This enables powerful command-line workflows.

### Basic Piping Examples

```bash
# Pipe network data to load command
cat network.edgelist | py3plex load - --info

# Pipe to query command
cat network.edgelist | py3plex query - "SELECT nodes COMPUTE degree"

# Chain commands: create and query
py3plex create --nodes 50 --layers 3 -o /dev/stdout 2>/dev/null | \
  py3plex query - "SELECT nodes COMPUTE degree" --format table
```

### Query Command

The `query` command executes DSL queries on networks and outputs results in JSON, CSV, or table format.

#### String DSL Syntax

```bash
# Get all nodes
py3plex query network.edgelist "SELECT nodes"

# Filter by layer
py3plex query network.edgelist "SELECT nodes WHERE layer='social'"

# Compute metrics
py3plex query network.edgelist "SELECT nodes COMPUTE degree"

# Multiple computations
py3plex query network.edgelist "SELECT nodes COMPUTE degree, betweenness_centrality"
```

#### Python DSL Builder Syntax

Use `--dsl` flag for the Python DSL builder syntax:

```bash
# Basic query with DSL builder
py3plex query network.edgelist 'Q.nodes().compute("degree")' --dsl

# With filtering and limiting
py3plex query network.edgelist 'Q.nodes().where(layer="social").compute("degree").order_by("-degree").limit(10)' --dsl

# Layer algebra
py3plex query network.edgelist 'Q.nodes().from_layers(L["social"] + L["work"]).compute("degree")' --dsl
```

### Output Formats

```bash
# JSON output (default) - good for further processing
py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format json

# CSV output - good for spreadsheets
py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format csv > nodes.csv

# Table output - good for human reading
py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format table
```

### Piping with jq

Combine with `jq` for JSON processing:

```bash
# Get top 5 nodes by degree
py3plex query network.edgelist "SELECT nodes COMPUTE degree" 2>/dev/null | \
  jq '.nodes[:5]'

# Extract just the computed values
py3plex query network.edgelist "SELECT nodes COMPUTE degree" 2>/dev/null | \
  jq '.computed.degree'

# Count nodes
py3plex query network.edgelist "SELECT nodes" 2>/dev/null | \
  jq '.count'
```

## Complete Workflow Examples

### Example 1: Network Analysis Pipeline

```bash
#!/bin/bash
# Generate network, analyze, and save results

# Create network
py3plex create --nodes 100 --layers 3 --probability 0.1 -o network.edgelist --seed 42

# Get basic info
py3plex load network.edgelist --info

# Compute centrality and save top nodes
py3plex query network.edgelist 'Q.nodes().compute("degree", "betweenness_centrality").order_by("-degree").limit(20)' --dsl -o top_nodes.json

# Detect communities
py3plex community network.edgelist --algorithm louvain -o communities.json
```

### Example 2: Batch Processing

```bash
#!/bin/bash
# Process multiple network files

for file in networks/*.edgelist; do
    echo "Processing $file..."
    py3plex query "$file" "SELECT nodes COMPUTE degree" --format csv > "${file%.edgelist}_degrees.csv"
done
```

### Example 3: Interactive Exploration with Piping

```bash
#!/bin/bash
# Create and immediately query

py3plex create --nodes 50 --layers 2 -o /dev/stdout 2>/dev/null | \
  py3plex query - 'Q.nodes().compute("degree").order_by("-degree").limit(5)' --dsl
```

## DSL Query Reference

### Select Target

```
SELECT nodes    # Select network nodes
SELECT edges    # Select network edges
```

### Layer Filtering

```
FROM LAYER("social")                    # Single layer
FROM LAYER("social") + LAYER("work")    # Multiple layers (union)
```

### Conditions

```
WHERE layer = "social"        # Filter by layer
WHERE degree > 5              # Filter by computed value
WHERE layer = "social" AND degree > 5   # Multiple conditions
```

### Compute Measures

Available measures:
- `degree` / `degree_centrality`
- `betweenness_centrality` / `betweenness`
- `closeness_centrality` / `closeness`
- `eigenvector_centrality` / `eigenvector`
- `pagerank`
- `clustering`
- `communities`

```
COMPUTE degree
COMPUTE degree, betweenness_centrality
COMPUTE betweenness_centrality AS bc
```

### Ordering and Limiting

Only available with `--dsl` flag:

```python
Q.nodes().compute("degree").order_by("-degree")  # Descending
Q.nodes().compute("degree").order_by("degree")   # Ascending
Q.nodes().limit(10)                               # Limit results
```

## Tips

1. **Suppress logging**: Redirect stderr with `2>/dev/null` when piping
2. **Large networks**: Use `--format csv` for large datasets
3. **Reproducibility**: Always use `--seed` when creating random networks
4. **Debugging**: Use `--format table` for quick visual inspection

## See Also

- `py3plex --help` - Full command list
- `py3plex query --help` - Query command details
- `py3plex tutorial` - Interactive tutorial
- Pipeline examples in `../pipelines/`
