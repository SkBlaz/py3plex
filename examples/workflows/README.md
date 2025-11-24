# Workflows and Extensibility

This directory contains examples for complete analysis workflows, configuration-driven analysis, and extending py3plex with custom functionality.

## Examples in This Category

### Config-Driven Workflows
- **`example_config_workflow.py`** - Drive analysis using configuration files
- **`config_driven_README.md`** - Documentation for config-driven workflows

### Plugin System
- **`example_plugin_usage.py`** - Create and use custom algorithms via the plugin system

### Jupyter Notebooks
- **`e2e_analysis_example.ipynb`** - End-to-end analysis workflow
- **`statistical_comparison_example.ipynb`** - Statistical comparison workflow

### Configuration Files
Example configuration files for workflows:
- `example_config.yaml` - YAML configuration example
- `load_and_compare.json` - JSON configuration for loading and comparing
- `comparison_config.json` - Configuration for network comparison
- `load_from_file.yaml` - Configuration for file loading

### Sample Data
- `sample_network.graphml` - Example network in GraphML format
- Various `.png` files - Example outputs

## Config-Driven Analysis

Config-driven workflows let you define entire analysis pipelines in configuration files:

```yaml
# example_config.yaml
network:
  source: "data/network.edgelist"
  directed: false

analysis:
  - type: centrality
    algorithms: [degree, betweenness, eigenvector]
  - type: communities
    algorithm: leiden

output:
  format: report
  path: "results/"
```

Then run:
```python
from py3plex.workflows import run_config
run_config("example_config.yaml")
```

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
