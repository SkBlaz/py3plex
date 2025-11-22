# Config-Driven Workflows

This directory contains examples of config-driven workflows in py3plex.

## Overview

Config-driven workflows allow you to define network analysis pipelines using YAML or JSON configuration files. This approach enables:

- **Reproducible research**: Share exact experiment configurations
- **Pipeline automation**: Integrate with CI/CD systems  
- **Batch processing**: Run multiple experiments easily
- **Version control**: Track experimental setups alongside code

## Files

### Sample Data
- `sample_network.graphml` - Sample multilayer network file for examples

### Config Files (Load from File Examples)
- `load_from_file.yaml` - Load network from file and analyze (YAML)
- `load_and_compare.json` - Compare file-loaded vs generated networks (JSON)

### Config Files (Generation Examples)
- `example_config.yaml` - Basic workflow with generated network
- `comparison_config.json` - Multi-dataset comparison workflow

### Scripts
- `example_config_workflow.py` - Python script demonstrating all workflow types

## Running Examples

### Using Python

```bash
python example_config_workflow.py
```

This runs three examples:
1. Loading network from file (YAML)
2. File vs generated comparison (JSON)
3. Network generation (YAML)

### Using CLI

```bash
# Load network from file
py3plex run-config load_from_file.yaml

# Compare file-loaded and generated networks
py3plex run-config load_and_compare.json

# Generate and analyze network
py3plex run-config example_config.yaml

# Validate configuration without running
py3plex run-config load_from_file.yaml --validate-only
```

## Configuration Format

### Basic Structure

```yaml
name: "My Workflow"
description: "Description of what this workflow does"

datasets:
  - name: "network_name"
    type: "file"  # or "generate"
    path: "network.graphml"

operations:
  - type: "stats"
    dataset: "network_name"
    parameters: {}
    
output:
  directory: "results"
  summary: "summary.json"
```

### Dataset Types

**Load from File (Recommended):**
```yaml
- name: "my_network"
  type: "file"
  path: "data/network.graphml"
```

Supported formats:
- GraphML (`.graphml`)
- GPickle (`.gpickle`)
- Multiedgelist (`.edgelist`, `.txt`)

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
