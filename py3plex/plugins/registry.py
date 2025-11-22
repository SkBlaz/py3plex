"""
Plugin registry and discovery system.

This module manages plugin registration, discovery, and access.
"""

import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from py3plex.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for managing py3plex plugins.
    
    The registry stores all registered plugins organized by type and name.
    It provides methods for registering, discovering, and retrieving plugins.
    
    Example:
        >>> registry = PluginRegistry()
        >>> 
        >>> # Register a plugin class
        >>> registry.register_plugin('centrality', 'my_centrality', MyPlugin)
        >>> 
        >>> # Get a plugin instance
        >>> plugin = registry.get('centrality', 'my_centrality')
        >>> 
        >>> # List all plugins of a type
        >>> centralities = registry.list_plugins('centrality')
    """

    _instance = None
    _plugins: Dict[str, Dict[str, Type[BasePlugin]]] = {
        "centrality": {},
        "community": {},
        "layout": {},
        "metric": {},
    }

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize plugins dict if it's been cleared
            if not cls._plugins:
                cls._plugins = {
                    "centrality": {},
                    "community": {},
                    "layout": {},
                    "metric": {},
                }
        return cls._instance

    @classmethod
    def register_plugin(
        cls, plugin_type: str, plugin_name: str, plugin_class: Type[BasePlugin]
    ) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_type: Type of plugin ('centrality', 'community', 'layout', 'metric')
            plugin_name: Unique name for this plugin
            plugin_class: Plugin class (must inherit from appropriate base class)
            
        Raises:
            ValueError: If plugin_type is invalid or plugin already registered
            TypeError: If plugin_class doesn't inherit from BasePlugin
        """
        if plugin_type not in cls._plugins:
            raise ValueError(
                f"Invalid plugin type: {plugin_type}. "
                f"Must be one of: {', '.join(cls._plugins.keys())}"
            )

        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(
                f"Plugin class {plugin_class.__name__} must inherit from BasePlugin"
            )

        if plugin_name in cls._plugins[plugin_type]:
            logger.warning(
                f"Plugin '{plugin_name}' of type '{plugin_type}' is already registered. "
                "Overwriting previous registration."
            )

        cls._plugins[plugin_type][plugin_name] = plugin_class
        logger.info(f"Registered plugin: {plugin_type}/{plugin_name}")

    @classmethod
    def register(cls, plugin_type: str, plugin_name: str):
        """
        Decorator for registering plugin classes.
        
        Example:
            >>> @PluginRegistry.register('centrality', 'my_centrality')
            >>> class MyCentrality(CentralityPlugin):
            ...     def compute(self, network, **kwargs):
            ...         return {}
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Unique name for this plugin
            
        Returns:
            Decorator function that registers the class
        """

        def decorator(plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
            cls.register_plugin(plugin_type, plugin_name, plugin_class)
            return plugin_class

        return decorator

    def get(self, plugin_type: str, plugin_name: str) -> BasePlugin:
        """
        Get an instance of a registered plugin.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            
        Returns:
            An instance of the requested plugin
            
        Raises:
            KeyError: If plugin is not found
            RuntimeError: If plugin validation fails
        """
        if plugin_type not in self._plugins:
            raise KeyError(f"Unknown plugin type: {plugin_type}")

        if plugin_name not in self._plugins[plugin_type]:
            available = ", ".join(self._plugins[plugin_type].keys())
            raise KeyError(
                f"Plugin '{plugin_name}' not found in type '{plugin_type}'. "
                f"Available plugins: {available or 'none'}"
            )

        plugin_class = self._plugins[plugin_type][plugin_name]
        plugin_instance = plugin_class()

        # Validate plugin before returning
        if not plugin_instance.validate():
            raise RuntimeError(
                f"Plugin '{plugin_name}' validation failed. "
                "Check dependencies and configuration."
            )

        return plugin_instance

    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all registered plugins.
        
        Args:
            plugin_type: Optional plugin type to filter by
            
        Returns:
            Dictionary mapping plugin types to lists of plugin names
        """
        if plugin_type is not None:
            if plugin_type not in self._plugins:
                raise KeyError(f"Unknown plugin type: {plugin_type}")
            return {plugin_type: list(self._plugins[plugin_type].keys())}

        return {ptype: list(plugins.keys()) for ptype, plugins in self._plugins.items()}

    def get_plugin_info(self, plugin_type: str, plugin_name: str) -> Dict[str, Any]:
        """
        Get metadata about a plugin without instantiating it.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary with plugin metadata (name, version, author, description)
        """
        if plugin_type not in self._plugins:
            raise KeyError(f"Unknown plugin type: {plugin_type}")

        if plugin_name not in self._plugins[plugin_type]:
            raise KeyError(f"Plugin '{plugin_name}' not found in type '{plugin_type}'")

        plugin_class = self._plugins[plugin_type][plugin_name]
        # Create temporary instance to get metadata
        instance = plugin_class()

        return {
            "name": instance.name,
            "version": instance.version,
            "author": instance.author,
            "description": instance.description,
            "type": plugin_type,
        }

    def unregister(self, plugin_type: str, plugin_name: str) -> None:
        """
        Unregister a plugin.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            
        Raises:
            KeyError: If plugin is not found
        """
        if plugin_type not in self._plugins:
            raise KeyError(f"Unknown plugin type: {plugin_type}")

        if plugin_name not in self._plugins[plugin_type]:
            raise KeyError(f"Plugin '{plugin_name}' not found in type '{plugin_type}'")

        del self._plugins[plugin_type][plugin_name]
        logger.info(f"Unregistered plugin: {plugin_type}/{plugin_name}")

    @classmethod
    def reset(cls) -> None:
        """
        Reset the registry to initial state.
        
        This is primarily useful for testing. Clears all registered plugins
        and resets the singleton instance.
        """
        cls._instance = None
        cls._plugins = {
            "centrality": {},
            "community": {},
            "layout": {},
            "metric": {},
        }


def discover_plugins(plugin_dir: Optional[str] = None) -> int:
    """
    Discover and load plugins from a directory or package.
    
    This function searches for Python modules in the specified directory
    and attempts to import them, allowing plugins to self-register using
    the @PluginRegistry.register decorator.
    
    Args:
        plugin_dir: Path to directory containing plugin modules.
                   If None, looks in the PY3PLEX_PLUGIN_DIR environment variable
                   or defaults to ~/.py3plex/plugins/
    
    Returns:
        Number of plugins discovered and loaded
        
    Example:
        >>> # Create a plugin file at ~/.py3plex/plugins/my_plugin.py
        >>> # It will be auto-discovered on import
        >>> from py3plex.plugins import discover_plugins
        >>> count = discover_plugins()
        >>> print(f"Loaded {count} plugins")
    """
    if plugin_dir is None:
        # Try environment variable first
        plugin_dir = os.environ.get("PY3PLEX_PLUGIN_DIR")

        # Default to user's home directory
        if plugin_dir is None:
            plugin_dir = os.path.join(os.path.expanduser("~"), ".py3plex", "plugins")

    plugin_path = Path(plugin_dir)

    if not plugin_path.exists():
        logger.debug(f"Plugin directory does not exist: {plugin_dir}")
        return 0

    if not plugin_path.is_dir():
        logger.warning(f"Plugin path is not a directory: {plugin_dir}")
        return 0

    # Track registry state before discovery
    registry = PluginRegistry()
    plugins_before = sum(
        len(plugins) for plugins in registry.list_plugins().values()
    )

    # Add plugin directory to Python path temporarily
    plugin_path_str = str(plugin_path)
    added_to_path = False
    if plugin_path_str not in sys.path:
        sys.path.insert(0, plugin_path_str)
        added_to_path = True

    try:
        # Import all Python modules in the directory
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip private modules

            module_name = py_file.stem

            # Check if module already exists to avoid conflicts
            if module_name in sys.modules:
                logger.warning(
                    f"Module {module_name} already exists in sys.modules, skipping"
                )
                continue

            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    logger.info(f"Loaded plugin module: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin module {module_name}: {e}")
    finally:
        # Clean up sys.path if we added to it
        if added_to_path and plugin_path_str in sys.path:
            sys.path.remove(plugin_path_str)

    # Count newly registered plugins
    plugins_after = sum(len(plugins) for plugins in registry.list_plugins().values())
    discovered_count = plugins_after - plugins_before

    logger.info(f"Discovered {discovered_count} new plugins from {plugin_dir}")
    return discovered_count
