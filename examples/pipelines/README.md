# Pipeline Examples

This directory contains examples demonstrating the scikit-learn style pipeline functionality in py3plex.

## Overview

The pipeline module provides a composable, scikit-learn inspired API for chaining network analysis operations. This makes it easy to create reproducible workflows and experiment with different analysis strategies.

## Basic Pipeline Concept

```python
from py3plex.pipeline import Pipeline, LoadStep, ComputeStats

pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=50, l=3, p=0.1)),
    ("stats", ComputeStats()),
])

result = pipe.run()
```

## Available Pipeline Steps

### Data Loading and Generation
- **LoadStep**: Load networks from files or generate random networks
  - Supports GraphML, gpickle, multiedgelist formats
  - Can generate random Erdos-Renyi multilayer networks

### Network Transformations
- **AggregateLayers**: Aggregate edges across multiple layers
  - Methods: 'sum', 'mean', 'max'
- **FilterNodes**: Filter nodes based on criteria
  - By degree (min/max)
  - By explicit node list

### Analysis Steps
- **ComputeStats**: Compute basic network statistics
  - Node/edge counts, density
  - Optional layer-specific statistics
- **LouvainCommunity**: Louvain community detection
- **LeidenMultilayer**: Leiden algorithm for multilayer networks (requires leidenalg)

### I/O Steps
- **SaveNetwork**: Save networks to files
  - Formats: GraphML, gpickle, edgelist

## Examples

### Example 1: Basic Statistics Pipeline
**File**: `example_1_basic_stats.py`

Load a random network and compute statistics.

```bash
python example_1_basic_stats.py
```

### Example 2: Aggregation Pipeline
**File**: `example_2_aggregation.py`

Generate a multilayer network, aggregate layers, and compute statistics.

```bash
python example_2_aggregation.py
```

### Example 3: Community Detection Pipeline
**File**: `example_3_community_detection.py`

Detect communities using the Louvain algorithm.

```bash
python example_3_community_detection.py
```

### Example 4: Leiden Multilayer Pipeline
**File**: `example_4_leiden_multilayer.py`

Advanced multilayer community detection using Leiden algorithm.

**Requirements**: `pip install leidenalg`

```bash
python example_4_leiden_multilayer.py
```

### Example 5: Filtering Pipeline
**File**: `example_5_filtering.py`

Filter nodes by degree before analysis.

```bash
python example_5_filtering.py
```

### Example 6: Complex Multi-step Pipeline
**File**: `example_6_complex_pipeline.py`

Demonstrates a complex pipeline: load -> filter -> aggregate -> community detection.

```bash
python example_6_complex_pipeline.py
```

### Example 7: Save and Load Pipeline
**File**: `example_7_save_load.py`

Save intermediate results and load them in subsequent pipelines.

```bash
python example_7_save_load.py
```

## Creating Custom Pipeline Steps

You can create custom pipeline steps by inheriting from `PipelineStep`:

```python
from py3plex.pipeline import PipelineStep

class CustomStep(PipelineStep):
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
    
    def transform(self, data):
        # Your custom transformation logic
        return transformed_data
```

## Key Features

- **Composable**: Chain multiple steps together
- **Type-safe**: Steps validate input types
- **Reproducible**: Set random seeds for deterministic results
- **Flexible**: Easy to add custom steps
- **Logging**: Built-in logging for pipeline execution
- **Parameter inspection**: `get_params()` and `set_params()` methods

## Comparison with Config-Driven Workflows

py3plex also supports config-driven workflows (see `py3plex.workflows`). The key differences:

| Feature | Pipeline | Config-Driven Workflow |
|---------|----------|----------------------|
| Style | Programmatic, scikit-like | Declarative, YAML/JSON |
| Use case | Prototyping, scripting | Production, automation |
| Extensibility | Python classes | Configuration schemas |
| Type hints | Yes | Limited |

Choose pipelines for interactive development and experimentation. Choose config-driven workflows for deployment and automation.
