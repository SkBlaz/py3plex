Plugin System
=============

The py3plex plugin system allows developers to extend the library with custom algorithms without modifying the core codebase. This makes it easy to contribute new centrality measures, community detection algorithms, layout methods, and network metrics.

Overview
--------

The plugin system provides:

* **Four plugin types** for different algorithm categories
* **Decorator-based registration** for easy plugin creation
* **Automatic discovery** from external directories
* **Safe module loading** with conflict detection
* **Validation** before plugin instantiation

Plugin Types
------------

CentralityPlugin
~~~~~~~~~~~~~~~~

For custom node centrality measures.

**Required Methods:**

* ``compute(network, **kwargs) -> Dict[str, float]``: Returns node-to-score mapping

**Optional Properties:**

* ``supports_weighted: bool``: Whether algorithm supports weighted networks (default: False)
* ``supports_directed: bool``: Whether algorithm supports directed networks (default: False)
* ``supports_multilayer: bool``: Whether algorithm supports multilayer networks (default: False)

**Example:**

.. code-block:: python

    from py3plex.plugins import CentralityPlugin, PluginRegistry

    @PluginRegistry.register('centrality', 'my_centrality')
    class MyCustomCentrality(CentralityPlugin):
        @property
        def name(self):
            return 'my_centrality'
        
        @property
        def description(self):
            return 'My custom centrality measure'
        
        @property
        def supports_weighted(self):
            return True
        
        def compute(self, network, normalized=False, **kwargs):
            """Compute centrality scores for all nodes."""
            centrality = {}
            
            # Your algorithm here
            G = network.core_network
            for node in G.nodes():
                centrality[node] = compute_score(node)
            
            return centrality

CommunityPlugin
~~~~~~~~~~~~~~~

For community detection algorithms.

**Required Methods:**

* ``detect(network, **kwargs) -> Dict[str, int]``: Returns node-to-community-id mapping

**Optional Properties:**

* ``supports_weighted: bool``: Whether algorithm supports weighted networks (default: False)
* ``supports_overlapping: bool``: Whether algorithm finds overlapping communities (default: False)
* ``supports_hierarchical: bool``: Whether algorithm produces hierarchy (default: False)

**Example:**

.. code-block:: python

    from py3plex.plugins import CommunityPlugin, PluginRegistry

    @PluginRegistry.register('community', 'my_detector')
    class MyDetector(CommunityPlugin):
        @property
        def name(self):
            return 'my_detector'
        
        @property
        def supports_weighted(self):
            return True
        
        def detect(self, network, resolution=1.0, **kwargs):
            """Detect communities in the network."""
            communities = {}
            
            # Your algorithm here
            G = network.core_network
            # ... community detection logic ...
            
            return communities

LayoutPlugin
~~~~~~~~~~~~

For network layout algorithms.

**Required Methods:**

* ``compute_layout(network, dimensions=2, **kwargs) -> Dict[str, tuple]``: Returns node-to-position mapping

**Optional Properties:**

* ``supports_3d: bool``: Whether layout supports 3D positions (default: False)
* ``supports_weighted: bool``: Whether layout considers edge weights (default: False)

**Example:**

.. code-block:: python

    from py3plex.plugins import LayoutPlugin, PluginRegistry

    @PluginRegistry.register('layout', 'my_layout')
    class MyLayout(LayoutPlugin):
        @property
        def name(self):
            return 'my_layout'
        
        @property
        def supports_3d(self):
            return True
        
        def compute_layout(self, network, dimensions=2, **kwargs):
            """Compute layout positions."""
            import math
            
            positions = {}
            G = network.core_network
            nodes = list(G.nodes())
            
            # Your layout algorithm here
            for i, node in enumerate(nodes):
                if dimensions == 2:
                    positions[node] = (x, y)
                elif dimensions == 3:
                    positions[node] = (x, y, z)
            
            return positions

MetricPlugin
~~~~~~~~~~~~

For custom network metrics.

**Required Methods:**

* ``compute(network, **kwargs) -> Dict[str, Any]``: Returns metric names to values

**Optional Properties:**

* ``metric_type: str``: 'global', 'local', or 'both' (default: 'global')

**Example:**

.. code-block:: python

    from py3plex.plugins import MetricPlugin, PluginRegistry

    @PluginRegistry.register('metric', 'my_metric')
    class MyMetric(MetricPlugin):
        @property
        def name(self):
            return 'my_metric'
        
        @property
        def metric_type(self):
            return 'global'
        
        def compute(self, network, **kwargs):
            """Compute network metrics."""
            G = network.core_network
            
            # Your metric computation
            value = compute_metric(G)
            
            return {'metric_name': value}

Using Plugins
-------------

Registering Plugins
~~~~~~~~~~~~~~~~~~~

**Method 1: Decorator (Recommended)**

.. code-block:: python

    from py3plex.plugins import PluginRegistry, CentralityPlugin

    @PluginRegistry.register('centrality', 'my_plugin')
    class MyPlugin(CentralityPlugin):
        # Implementation
        pass

**Method 2: Direct Registration**

.. code-block:: python

    from py3plex.plugins import PluginRegistry

    registry = PluginRegistry()
    registry.register_plugin('centrality', 'my_plugin', MyPluginClass)

Getting and Using Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex import PluginRegistry, multi_layer_network

    # Get plugin instance
    registry = PluginRegistry()
    plugin = registry.get('centrality', 'my_plugin')

    # Use plugin
    network = multi_layer_network()
    # ... add nodes and edges ...
    results = plugin.compute(network)

Listing Available Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex import PluginRegistry

    registry = PluginRegistry()

    # List all plugins
    all_plugins = registry.list_plugins()
    print(all_plugins)
    # {'centrality': ['my_plugin', ...], 'community': [...], ...}

    # List specific type
    centralities = registry.list_plugins('centrality')
    print(centralities)
    # {'centrality': ['my_plugin', 'example_degree', ...]}

Getting Plugin Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex import PluginRegistry

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

Plugin Discovery
----------------

Automatic Plugin Loading
~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex can automatically discover plugins from external directories.

**Default Plugin Directory**

By default, plugins are loaded from ``~/.py3plex/plugins/``

**Setting Custom Plugin Directory**

Via environment variable:

.. code-block:: bash

    export PY3PLEX_PLUGIN_DIR=/path/to/my/plugins

Programmatically:

.. code-block:: python

    from py3plex.plugins import discover_plugins

    # Discover plugins from custom directory
    count = discover_plugins('/path/to/my/plugins')
    print(f"Loaded {count} plugins")

Creating Discoverable Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create a Python file in your plugin directory:

.. code-block:: bash

    mkdir -p ~/.py3plex/plugins

2. Write your plugin (e.g., ``~/.py3plex/plugins/my_plugin.py``):

.. code-block:: python

    from py3plex.plugins import CentralityPlugin, PluginRegistry

    @PluginRegistry.register('centrality', 'my_auto_plugin')
    class MyAutoPlugin(CentralityPlugin):
        @property
        def name(self):
            return 'my_auto_plugin'
        
        def compute(self, network, **kwargs):
            # Implementation
            return {}

3. The plugin will be automatically discovered when you import py3plex:

.. code-block:: python

    from py3plex.plugins import discover_plugins
    discover_plugins()  # Loads from default directory

Best Practices
--------------

Input Validation
~~~~~~~~~~~~~~~~

Always validate input in your plugins:

.. code-block:: python

    def compute(self, network, **kwargs):
        if not hasattr(network, 'core_network'):
            raise ValueError("Network must be a py3plex multi_layer_network object")
        
        # Your implementation

Documentation
~~~~~~~~~~~~~

Provide clear docstrings:

.. code-block:: python

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

Dependency Checking
~~~~~~~~~~~~~~~~~~~

Check for optional dependencies:

.. code-block:: python

    def validate(self):
        """Check if plugin can run."""
        try:
            import optional_library
            return True
        except ImportError:
            return False

Error Handling
~~~~~~~~~~~~~~

Handle errors gracefully:

.. code-block:: python

    def compute(self, network, **kwargs):
        try:
            # Your algorithm
            return results
        except Exception as e:
            raise ValueError(f"Failed to compute centrality: {e}")

Example Plugins
---------------

Built-in Examples
~~~~~~~~~~~~~~~~~

Py3plex includes example plugins demonstrating all plugin types. Import them to see available examples:

.. code-block:: python

    import py3plex.plugins.examples
    from py3plex import PluginRegistry

    registry = PluginRegistry()
    plugins = registry.list_plugins()
    
    # Example plugins available:
    # - centrality/example_degree: Simple degree centrality
    # - community/example_simple: Simple community detection
    # - layout/example_circular: Circular layout
    # - metric/example_density: Network density

Complete Example
~~~~~~~~~~~~~~~~

See ``examples/plugins/example_plugin_usage.py`` for a complete working example demonstrating:

* Creating custom centrality plugins
* Creating custom community detection plugins
* Using built-in example plugins
* Plugin discovery and registration
* Getting plugin information

.. code-block:: python

    from py3plex import multi_layer_network, PluginRegistry
    from py3plex.plugins import CentralityPlugin

    # Define custom plugin
    @PluginRegistry.register('centrality', 'closeness_simple')
    class SimpleCloseness(CentralityPlugin):
        @property
        def name(self):
            return 'closeness_simple'
        
        def compute(self, network, **kwargs):
            import networkx as nx
            G = network.core_network
            
            centrality = {}
            for node in G.nodes():
                lengths = nx.single_source_shortest_path_length(G, node)
                lengths.pop(node, None)
                
                if lengths:
                    avg_length = sum(lengths.values()) / len(lengths)
                    centrality[node] = 1.0 / avg_length if avg_length > 0 else 0.0
                else:
                    centrality[node] = 0.0
            
            return centrality

    # Create network
    net = multi_layer_network()
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ])

    # Use plugin
    registry = PluginRegistry()
    plugin = registry.get('centrality', 'closeness_simple')
    scores = plugin.compute(net)
    
    for node, score in sorted(scores.items()):
        print(f"Node {node}: {score:.4f}")

Contributing Plugins
--------------------

To contribute plugins to the py3plex ecosystem:

1. **Create your plugin** following this guide
2. **Test your plugin** thoroughly
3. **Package your plugin** as a Python package
4. **Publish to PyPI** or share on GitHub
5. **Submit a PR** to add your plugin to the official plugin registry

Plugin Package Structure
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    my-py3plex-plugin/
    ├── setup.py
    ├── README.md
    ├── my_plugin/
    │   ├── __init__.py
    │   └── plugin.py
    └── tests/
        └── test_plugin.py

Example setup.py
~~~~~~~~~~~~~~~~

.. code-block:: python

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

API Reference
-------------

PluginRegistry
~~~~~~~~~~~~~~

.. py:class:: PluginRegistry()

   Central registry for managing py3plex plugins.

   .. py:method:: register_plugin(plugin_type: str, plugin_name: str, plugin_class: Type[BasePlugin]) -> None

      Register a plugin class.

      :param plugin_type: Type of plugin ('centrality', 'community', 'layout', 'metric')
      :param plugin_name: Unique name for this plugin
      :param plugin_class: Plugin class (must inherit from appropriate base class)
      :raises ValueError: If plugin_type is invalid or plugin already registered
      :raises TypeError: If plugin_class doesn't inherit from BasePlugin

   .. py:method:: get(plugin_type: str, plugin_name: str) -> BasePlugin

      Get an instance of a registered plugin.

      :param plugin_type: Type of plugin
      :param plugin_name: Name of the plugin
      :return: An instance of the requested plugin
      :raises KeyError: If plugin is not found
      :raises RuntimeError: If plugin validation fails

   .. py:method:: list_plugins(plugin_type: Optional[str] = None) -> Dict[str, List[str]]

      List all registered plugins.

      :param plugin_type: Optional plugin type to filter by
      :return: Dictionary mapping plugin types to lists of plugin names

   .. py:method:: get_plugin_info(plugin_type: str, plugin_name: str) -> Dict[str, Any]

      Get metadata about a plugin without instantiating it.

      :param plugin_type: Type of plugin
      :param plugin_name: Name of the plugin
      :return: Dictionary with plugin metadata

   .. py:method:: unregister(plugin_type: str, plugin_name: str) -> None

      Unregister a plugin.

      :param plugin_type: Type of plugin
      :param plugin_name: Name of the plugin
      :raises KeyError: If plugin is not found

   .. py:classmethod:: reset() -> None

      Reset the registry to initial state. Primarily useful for testing.

discover_plugins
~~~~~~~~~~~~~~~~

.. py:function:: discover_plugins(plugin_dir: Optional[str] = None) -> int

   Discover and load plugins from a directory.

   :param plugin_dir: Path to directory containing plugin modules. If None, looks in PY3PLEX_PLUGIN_DIR environment variable or defaults to ~/.py3plex/plugins/
   :return: Number of plugins discovered and loaded

Support
-------

* **Documentation**: https://py3plex.readthedocs.io
* **Issues**: https://github.com/SkBlaz/py3plex/issues
* **Discussions**: https://github.com/SkBlaz/py3plex/discussions

See Also
--------

* :doc:`contributing` - General contribution guidelines
* :doc:`algorithm_guide` - Guide to built-in algorithms
* :doc:`development` - Development setup and practices
