"""
Py3plex Plugin System

This module provides a plugin system for extending py3plex with external algorithms,
centralities, community detection methods, and other network analysis tools.

The plugin system allows users to:
- Register custom algorithms without modifying py3plex core code
- Discover and load plugins from external packages
- Contribute new methods via simple plugin interfaces

Quick Start:
    >>> from py3plex.plugins import PluginRegistry, CentralityPlugin
    >>> 
    >>> # Define a custom centrality plugin
    >>> @PluginRegistry.register('centrality', 'my_centrality')
    >>> class MyCentrality(CentralityPlugin):
    ...     def compute(self, network, **kwargs):
    ...         # Custom centrality computation
    ...         return {}
    >>> 
    >>> # Use the plugin
    >>> registry = PluginRegistry()
    >>> plugin = registry.get('centrality', 'my_centrality')
    >>> results = plugin.compute(my_network)

Plugin Types:
    - CentralityPlugin: Custom node centrality measures
    - CommunityPlugin: Community detection algorithms
    - LayoutPlugin: Network layout algorithms
    - MetricPlugin: Custom network metrics

For plugin development guide, see documentation at:
https://skblaz.github.io/py3plex/
"""

from py3plex.plugins.base import (
    BasePlugin,
    CentralityPlugin,
    CommunityPlugin,
    LayoutPlugin,
    MetricPlugin,
)
from py3plex.plugins.registry import PluginRegistry, discover_plugins

__all__ = [
    "BasePlugin",
    "CentralityPlugin",
    "CommunityPlugin",
    "LayoutPlugin",
    "MetricPlugin",
    "PluginRegistry",
    "discover_plugins",
]
