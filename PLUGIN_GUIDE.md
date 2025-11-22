# Plugin Development Guide

Py3plex includes a flexible plugin system that allows developers to extend the library with custom algorithms without modifying the core codebase. This guide will help you create and contribute plugins.

## Overview

The plugin system supports four types of plugins:

1. **CentralityPlugin**: Custom node centrality measures
2. **CommunityPlugin**: Community detection algorithms
3. **LayoutPlugin**: Network layout algorithms
4. **MetricPlugin**: Custom network metrics

## Quick Start

Here's a simple example of creating a custom centrality plugin:

```python
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register('centrality', 'my_custom_centrality')
class MyCustomCentrality(CentralityPlugin):
    @property
    def name(self):
        return 'my_custom_centrality'
    
    @property
    def description(self):
        return 'My custom centrality measure'
    
    @property
    def author(self):
        return 'Your Name <your.email@example.com>'
    
    @property
    def version(self):
        return '1.0.0'
    
    def compute(self, network, **kwargs):
        """Compute centrality scores for all nodes."""
        centrality = {}
        
        # Your algorithm here
        for node in network.get_nodes():
            centrality[node] = compute_score(node)
        
        return centrality
```

## Plugin Types

### 1. CentralityPlugin

Centrality plugins compute importance scores for nodes in a network.

**Required Methods:**
- `compute(network, **kwargs) -> Dict[str, float]`: Returns node-to-score mapping

**Optional Properties:**
- `supports_weighted: bool`: Whether algorithm supports weighted networks (default: False)
- `supports_directed: bool`: Whether algorithm supports directed networks (default: False)
- `supports_multilayer: bool`: Whether algorithm supports multilayer networks (default: False)

**Example:**
```python
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register('centrality', 'custom_betweenness')
class CustomBetweenness(CentralityPlugin):
    @property
    def name(self):
        return 'custom_betweenness'
    
    @property
    def supports_weighted(self):
        return True
    
    def compute(self, network, normalized=True, **kwargs):
        # Implementation
        return betweenness_scores
```

### 2. CommunityPlugin

Community plugins identify groups of densely connected nodes.

**Required Methods:**
- `detect(network, **kwargs) -> Dict[str, int]`: Returns node-to-community-id mapping

**Optional Properties:**
- `supports_weighted: bool`: Whether algorithm supports weighted networks (default: False)
- `supports_overlapping: bool`: Whether algorithm finds overlapping communities (default: False)
- `supports_hierarchical: bool`: Whether algorithm produces hierarchy (default: False)

**Example:**
```python
from py3plex.plugins import CommunityPlugin, PluginRegistry

@PluginRegistry.register('community', 'custom_louvain')
class CustomLouvain(CommunityPlugin):
    @property
    def name(self):
        return 'custom_louvain'
    
    @property
    def supports_weighted(self):
        return True
    
    def detect(self, network, resolution=1.0, **kwargs):
        # Implementation
        return communities
```

### 3. LayoutPlugin

Layout plugins compute 2D/3D positions for visualizing networks.

**Required Methods:**
- `compute_layout(network, dimensions=2, **kwargs) -> Dict[str, tuple]`: Returns node-to-position mapping

**Optional Properties:**
- `supports_3d: bool`: Whether layout supports 3D positions (default: False)
- `supports_weighted: bool`: Whether layout considers edge weights (default: False)

**Example:**
```python
from py3plex.plugins import LayoutPlugin, PluginRegistry

@PluginRegistry.register('layout', 'custom_force')
class CustomForceLayout(LayoutPlugin):
    @property
    def name(self):
        return 'custom_force'
    
    @property
    def supports_3d(self):
        return True
    
    def compute_layout(self, network, dimensions=2, iterations=100, **kwargs):
        # Implementation
        return positions
```

### 4. MetricPlugin

Metric plugins compute global or local network properties.

**Required Methods:**
- `compute(network, **kwargs) -> Dict[str, Any]`: Returns metric names to values

**Optional Properties:**
- `metric_type: str`: 'global', 'local', or 'both' (default: 'global')

**Example:**
```python
from py3plex.plugins import MetricPlugin, PluginRegistry

@PluginRegistry.register('metric', 'custom_modularity')
class CustomModularity(MetricPlugin):
    @property
    def name(self):
        return 'custom_modularity'
    
    @property
    def metric_type(self):
        return 'global'
    
    def compute(self, network, communities=None, **kwargs):
        # Implementation
        return {'modularity': score}
```

## Using Plugins

### Registering Plugins

**Method 1: Decorator (Recommended)**
```python
from py3plex.plugins import PluginRegistry, CentralityPlugin

@PluginRegistry.register('centrality', 'my_plugin')
class MyPlugin(CentralityPlugin):
    # Implementation
    pass
```

**Method 2: Direct Registration**
```python
from py3plex.plugins import PluginRegistry

registry = PluginRegistry()
registry.register_plugin('centrality', 'my_plugin', MyPluginClass)
```

### Getting and Using Plugins

```python
from py3plex.plugins import PluginRegistry

# Get plugin instance
registry = PluginRegistry()
plugin = registry.get('centrality', 'my_plugin')

# Use plugin
network = multi_layer_network()
# ... add nodes and edges ...
results = plugin.compute(network)
```

### Listing Available Plugins

```python
from py3plex.plugins import PluginRegistry

registry = PluginRegistry()

# List all plugins
all_plugins = registry.list_plugins()
print(all_plugins)
# {'centrality': ['my_plugin', ...], 'community': [...], ...}

# List specific type
centralities = registry.list_plugins('centrality')
print(centralities)
# {'centrality': ['my_plugin', 'example_degree', ...]}
```

### Getting Plugin Information

```python
from py3plex.plugins import PluginRegistry

registry = PluginRegistry()
info = registry.get_plugin_info('centrality', 'my_plugin')
print(info)
# {
#     'name': 'my_plugin',
#     'version': '1.0.0',
#     'author': 'Your Name',
#     'description': 'Description here',
#     'type': 'centrality'
# }
```

## Plugin Discovery

Py3plex can automatically discover plugins from external directories.

### Default Plugin Directory

By default, plugins are loaded from `~/.py3plex/plugins/`

### Setting Custom Plugin Directory

**Via Environment Variable:**
```bash
export PY3PLEX_PLUGIN_DIR=/path/to/my/plugins
```

**Programmatically:**
```python
from py3plex.plugins import discover_plugins

# Discover plugins from custom directory
count = discover_plugins('/path/to/my/plugins')
print(f"Loaded {count} plugins")
```

### Creating Discoverable Plugins

1. Create a Python file in your plugin directory:
```bash
mkdir -p ~/.py3plex/plugins
```

2. Write your plugin (e.g., `~/.py3plex/plugins/my_plugin.py`):
```python
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register('centrality', 'my_auto_plugin')
class MyAutoPlugin(CentralityPlugin):
    # Implementation
    pass
```

3. The plugin will be automatically discovered when you import py3plex:
```python
from py3plex.plugins import discover_plugins
discover_plugins()  # Loads from default directory
```

## Best Practices

### 1. Validation

Always validate input in your plugins:
```python
def compute(self, network, **kwargs):
    if not hasattr(network, 'get_nodes'):
        raise ValueError("Network must be a py3plex multi_layer_network object")
    
    # Your implementation
```

### 2. Documentation

Provide clear docstrings:
```python
def compute(self, network, threshold=0.5, **kwargs):
    """
    Compute custom centrality.
    
    Args:
        network: A py3plex multi_layer_network object
        threshold: Minimum score threshold (default: 0.5)
        **kwargs: Additional parameters
        
    Returns:
        Dictionary mapping node IDs to centrality scores
        
    Raises:
        ValueError: If network is invalid
    """
```

### 3. Dependencies

Check for optional dependencies:
```python
def validate(self):
    """Check if plugin can run."""
    try:
        import optional_library
        return True
    except ImportError:
        return False
```

### 4. Error Handling

Handle errors gracefully:
```python
def compute(self, network, **kwargs):
    try:
        # Your algorithm
        return results
    except Exception as e:
        raise ValueError(f"Failed to compute centrality: {e}")
```

## Contributing Plugins

To contribute plugins to the py3plex ecosystem:

1. **Create your plugin** following this guide
2. **Test your plugin** thoroughly
3. **Package your plugin** as a Python package
4. **Publish to PyPI** or share on GitHub
5. **Submit a PR** to add your plugin to the official plugin registry

### Plugin Package Structure

```
my-py3plex-plugin/
├── setup.py
├── README.md
├── my_plugin/
│   ├── __init__.py
│   └── plugin.py
└── tests/
    └── test_plugin.py
```

### Example setup.py

```python
from setuptools import setup, find_packages

setup(
    name='py3plex-my-plugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'py3plex>=0.96',
    ],
    entry_points={
        'py3plex.plugins': [
            'my_plugin = my_plugin.plugin',
        ],
    },
)
```

## Examples

See `py3plex/plugins/examples.py` for complete working examples of all plugin types.

## Support

- **Documentation**: https://py3plex.readthedocs.io
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Discussions**: https://github.com/SkBlaz/py3plex/discussions
