# Config-Driven Workflows

This directory contains examples of config-driven workflows in py3plex.

## Overview

Config-driven workflows allow you to define network analysis pipelines using YAML or JSON configuration files. This approach enables:

- **Reproducible research**: Share exact experiment configurations
- **Pipeline automation**: Integrate with CI/CD systems  
- **Batch processing**: Run multiple experiments easily
- **Version control**: Track experimental setups alongside code

## Files

- `example_config.yaml` - Basic workflow with generated network
- `comparison_config.json` - Multi-dataset comparison workflow
- `example_config_workflow.py` - Python script demonstrating workflow execution

## Running Examples

### Using Python

```bash
python example_config_workflow.py
```

### Using CLI

```bash
# Run YAML workflow
py3plex run-config example_config.yaml

# Run JSON workflow
py3plex run-config comparison_config.json

# Validate configuration without running
py3plex run-config example_config.yaml --validate-only
```

## Configuration Format

### Basic Structure

```yaml
name: "My Workflow"
description: "Description of what this workflow does"

datasets:
  - name: "network_name"
    type: "generate"  # or "file"
    generator: "random"
    parameters:
      nodes: 50
      layers: 2
      probability: 0.15

operations:
  - type: "stats"
    dataset: "network_name"
    parameters: {}
    
output:
  directory: "results"
  summary: "summary.json"
```

### Dataset Types

**Generate Networks:**
```yaml
- name: "generated_net"
  type: "generate"
  generator: "random"
  parameters:
    nodes: 100
    layers: 3
    probability: 0.1
    seed: 42  # optional, for reproducibility
```

**Load from File:**
```yaml
- name: "my_network"
  type: "file"
  path: "data/network.graphml"
```

### Available Operations

- `stats` - Compute network statistics
- `community` - Detect communities (louvain algorithm)
- `centrality` - Compute centrality measures (degree, betweenness, closeness)
- `visualize` - Create network visualizations
- `aggregate` - Aggregate multilayer networks
- `convert` - Convert between formats

## Documentation

For detailed documentation, see:
- Online docs: https://skblaz.github.io/py3plex/config_workflows.html
- Local docs: `docfiles/config_workflows.rst`

## Requirements

- py3plex installed
- PyYAML for YAML support (optional, JSON always works)

```bash
pip install pyyaml
```
