# Workflows and Extensibility

This directory contains examples for complete analysis workflows, configuration-driven analysis, and extending py3plex with custom functionality.

## Examples in This Category

### Config-Driven Workflows
- **`example_config_workflow.py`** - Drive analysis using configuration files

### Plugin System
- **`example_plugin_usage.py`** - Create and use custom algorithms via the plugin system

### Jupyter Notebooks
- **`e2e_analysis_example.ipynb`** - End-to-end analysis workflow
- **`statistical_comparison_example.ipynb`** - Statistical comparison workflow

### Configuration Files
Example configuration files for workflows:
- `example_config.yaml` - Basic workflow with generated network (YAML)
- `load_from_file.yaml` - Load network from file and analyze (YAML)
- `load_and_compare.json` - Compare file-loaded vs generated networks (JSON)
- `comparison_config.json` - Multi-dataset comparison workflow (JSON)

### Sample Data
- `sample_network.graphml` - Sample multilayer network file for examples
- Various `.png` files - Example outputs

## Config-Driven Analysis

Config-driven workflows allow you to define network analysis pipelines using YAML or JSON configuration files. This approach enables:

- **Reproducible research**: Share exact experiment configurations
- **Pipeline automation**: Integrate with CI/CD systems
- **Batch processing**: Run multiple experiments easily
- **Version control**: Track experimental setups alongside code

### Running Config-Driven Workflows

#### Using Python

```bash
python example_config_workflow.py
```

This runs three examples:
1. Loading network from file (YAML)
2. File vs generated comparison (JSON)
3. Network generation (YAML)

#### Using CLI

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

### Configuration Format

#### Basic Structure

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

#### Dataset Types

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

#### Available Operations

- `stats` - Compute network statistics
- `community` - Detect communities (louvain algorithm)
- `centrality` - Compute centrality measures (degree, betweenness, closeness)
- `visualize` - Create network visualizations
- `aggregate` - Aggregate multilayer networks
- `convert` - Convert between formats

## Plugin System

Extend py3plex with custom algorithms:

```python
from py3plex.plugins import register_plugin

@register_plugin("my_algorithm")
def my_custom_centrality(network, **kwargs):
    # Your custom implementation
    return results
```

See `example_plugin_usage.py` for complete examples.

## Benefits of Workflows

**Reproducibility**: Save and share exact analysis configurations  
**Automation**: Run the same analysis on multiple networks  
**Documentation**: Config files document your analysis  
**Extensibility**: Add custom algorithms via plugins  

## Use Cases

### Research Pipelines
- Define analysis once, apply to many datasets
- Ensure consistent methodology across experiments
- Easy to share methods with collaborators

### Production Systems
- Automated network analysis services
- Batch processing of multiple networks
- Integration with existing workflows

### Custom Extensions
- Implement domain-specific algorithms
- Integrate proprietary methods
- Create reusable analysis components

## Related Examples

- [Getting Started](../getting_started/) - Learn the basics first
- [Network Analysis](../network_analysis/) - Individual analysis techniques
- [Advanced](../advanced/) - Advanced algorithmic techniques

## Additional Resources

- See [PLUGIN_GUIDE.md](../../PLUGIN_GUIDE.md) for detailed plugin documentation
- Check config files in this directory for examples
- Explore notebooks for interactive workflows
- Online docs: https://skblaz.github.io/py3plex/config_workflows.html
- Local docs: `docfiles/config_workflows.rst`

## Requirements

- py3plex installed
- PyYAML for YAML support (optional, JSON always works)

```bash
pip install pyyaml
```
