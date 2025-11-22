"""
Tests for the py3plex plugin system.

This module tests plugin registration, discovery, and usage.
"""

import os
import tempfile
from pathlib import Path

import pytest

from py3plex.plugins import (
    BasePlugin,
    CentralityPlugin,
    CommunityPlugin,
    LayoutPlugin,
    MetricPlugin,
    PluginRegistry,
    discover_plugins,
)


class TestBasePlugin:
    """Tests for BasePlugin abstract class."""

    def test_base_plugin_cannot_be_instantiated(self):
        """Test that BasePlugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePlugin()

    def test_plugin_must_implement_name(self):
        """Test that plugins must implement the name property."""

        class IncompletePlugin(BasePlugin):
            pass

        with pytest.raises(TypeError):
            IncompletePlugin()


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        # Use the public reset method
        PluginRegistry.reset()

    def test_registry_is_singleton(self):
        """Test that PluginRegistry is a singleton."""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()
        assert registry1 is registry2

    def test_register_plugin_with_decorator(self):
        """Test registering a plugin using decorator."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "test_centrality")
        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test_centrality"

            def compute(self, network, **kwargs):
                return {}

        plugins = registry.list_plugins("centrality")
        assert "test_centrality" in plugins["centrality"]

    def test_register_plugin_directly(self):
        """Test registering a plugin directly."""
        registry = PluginRegistry()

        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test_direct"

            def compute(self, network, **kwargs):
                return {}

        registry.register_plugin("centrality", "test_direct", TestCentrality)

        plugins = registry.list_plugins("centrality")
        assert "test_direct" in plugins["centrality"]

    def test_register_invalid_type(self):
        """Test that registering with invalid type raises error."""
        registry = PluginRegistry()

        class TestPlugin(BasePlugin):
            @property
            def name(self):
                return "test"

        with pytest.raises(ValueError, match="Invalid plugin type"):
            registry.register_plugin("invalid_type", "test", TestPlugin)

    def test_register_non_plugin_class(self):
        """Test that registering non-plugin class raises error."""
        registry = PluginRegistry()

        class NotAPlugin:
            pass

        with pytest.raises(TypeError, match="must inherit from BasePlugin"):
            registry.register_plugin("centrality", "test", NotAPlugin)

    def test_get_registered_plugin(self):
        """Test retrieving a registered plugin."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "test_get")
        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test_get"

            def compute(self, network, **kwargs):
                return {"A": 1.0}

        plugin = registry.get("centrality", "test_get")
        assert isinstance(plugin, CentralityPlugin)
        assert plugin.name == "test_get"

    def test_get_nonexistent_plugin(self):
        """Test that getting nonexistent plugin raises error."""
        registry = PluginRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("centrality", "nonexistent")

    def test_get_plugin_info(self):
        """Test getting plugin metadata."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "test_info")
        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test_info"

            @property
            def version(self):
                return "1.2.3"

            @property
            def author(self):
                return "Test Author"

            @property
            def description(self):
                return "Test description"

            def compute(self, network, **kwargs):
                return {}

        info = registry.get_plugin_info("centrality", "test_info")
        assert info["name"] == "test_info"
        assert info["version"] == "1.2.3"
        assert info["author"] == "Test Author"
        assert info["description"] == "Test description"
        assert info["type"] == "centrality"

    def test_list_plugins_all_types(self):
        """Test listing all plugins."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "cent1")
        class Cent1(CentralityPlugin):
            @property
            def name(self):
                return "cent1"

            def compute(self, network, **kwargs):
                return {}

        @PluginRegistry.register("community", "comm1")
        class Comm1(CommunityPlugin):
            @property
            def name(self):
                return "comm1"

            def detect(self, network, **kwargs):
                return {}

        plugins = registry.list_plugins()
        assert "cent1" in plugins["centrality"]
        assert "comm1" in plugins["community"]

    def test_list_plugins_specific_type(self):
        """Test listing plugins of a specific type."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "cent1")
        class Cent1(CentralityPlugin):
            @property
            def name(self):
                return "cent1"

            def compute(self, network, **kwargs):
                return {}

        plugins = registry.list_plugins("centrality")
        assert "centrality" in plugins
        assert "cent1" in plugins["centrality"]

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "test_unregister")
        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test_unregister"

            def compute(self, network, **kwargs):
                return {}

        # Verify it's registered
        plugins = registry.list_plugins("centrality")
        assert "test_unregister" in plugins["centrality"]

        # Unregister
        registry.unregister("centrality", "test_unregister")

        # Verify it's gone
        plugins = registry.list_plugins("centrality")
        assert "test_unregister" not in plugins["centrality"]

    def test_plugin_overwrite_warning(self, caplog):
        """Test that overwriting a plugin logs a warning."""
        registry = PluginRegistry()

        @PluginRegistry.register("centrality", "test_overwrite")
        class TestCentrality1(CentralityPlugin):
            @property
            def name(self):
                return "test_overwrite"

            def compute(self, network, **kwargs):
                return {}

        # Register again with same name
        @PluginRegistry.register("centrality", "test_overwrite")
        class TestCentrality2(CentralityPlugin):
            @property
            def name(self):
                return "test_overwrite"

            def compute(self, network, **kwargs):
                return {"different": True}

        assert "already registered" in caplog.text.lower()


class TestCentralityPlugin:
    """Tests for CentralityPlugin base class."""

    def test_centrality_plugin_properties(self):
        """Test that centrality plugin has expected properties."""

        class TestCentrality(CentralityPlugin):
            @property
            def name(self):
                return "test"

            @property
            def supports_weighted(self):
                return True

            def compute(self, network, **kwargs):
                return {}

        plugin = TestCentrality()
        assert plugin.supports_weighted is True
        assert plugin.supports_directed is False  # default
        assert plugin.supports_multilayer is False  # default


class TestCommunityPlugin:
    """Tests for CommunityPlugin base class."""

    def test_community_plugin_properties(self):
        """Test that community plugin has expected properties."""

        class TestCommunity(CommunityPlugin):
            @property
            def name(self):
                return "test"

            @property
            def supports_overlapping(self):
                return True

            def detect(self, network, **kwargs):
                return {}

        plugin = TestCommunity()
        assert plugin.supports_overlapping is True
        assert plugin.supports_hierarchical is False  # default


class TestPluginDiscovery:
    """Tests for plugin discovery system."""

    def test_discover_plugins_empty_directory(self):
        """Test discovering plugins from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            count = discover_plugins(tmpdir)
            assert count == 0

    def test_discover_plugins_nonexistent_directory(self):
        """Test discovering plugins from nonexistent directory."""
        count = discover_plugins("/nonexistent/path/to/plugins")
        assert count == 0

    def test_discover_plugins_from_directory(self):
        """Test discovering plugins from a directory with plugin files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the public reset method
            PluginRegistry.reset()

            # Create a plugin file
            plugin_file = Path(tmpdir) / "test_plugin.py"
            plugin_file.write_text(
                """
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register('centrality', 'discovered')
class DiscoveredPlugin(CentralityPlugin):
    @property
    def name(self):
        return 'discovered'
    
    def compute(self, network, **kwargs):
        return {}
"""
            )

            # Discover plugins
            count = discover_plugins(tmpdir)
            assert count == 1

            # Verify plugin was registered
            registry = PluginRegistry()
            plugins = registry.list_plugins("centrality")
            assert "discovered" in plugins["centrality"]

    def test_discover_plugins_env_variable(self, monkeypatch):
        """Test that plugin discovery uses PY3PLEX_PLUGIN_DIR env variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the public reset method
            PluginRegistry.reset()

            # Set environment variable
            monkeypatch.setenv("PY3PLEX_PLUGIN_DIR", tmpdir)

            # Create a plugin file
            plugin_file = Path(tmpdir) / "env_plugin.py"
            plugin_file.write_text(
                """
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register('centrality', 'env_discovered')
class EnvPlugin(CentralityPlugin):
    @property
    def name(self):
        return 'env_discovered'
    
    def compute(self, network, **kwargs):
        return {}
"""
            )

            # Discover plugins (should use env variable)
            count = discover_plugins()
            assert count >= 1

            # Verify plugin was registered
            registry = PluginRegistry()
            plugins = registry.list_plugins("centrality")
            assert "env_discovered" in plugins["centrality"]


class TestExamplePlugins:
    """Tests for the example plugins."""

    def setup_method(self):
        """Import example plugins before each test."""
        # Use the public reset method
        PluginRegistry.reset()
        # Force re-import of examples to register them
        import sys
        import importlib
        if 'py3plex.plugins.examples' in sys.modules:
            importlib.reload(sys.modules['py3plex.plugins.examples'])
        else:
            import py3plex.plugins.examples  # noqa: F401

    def test_example_plugins_registered(self):
        """Test that example plugins are registered on import."""
        registry = PluginRegistry()
        plugins = registry.list_plugins()

        assert "example_degree" in plugins["centrality"]
        assert "example_simple" in plugins["community"]
        assert "example_density" in plugins["metric"]
        assert "example_circular" in plugins["layout"]

    def test_example_centrality_plugin_metadata(self):
        """Test example centrality plugin metadata."""
        registry = PluginRegistry()
        info = registry.get_plugin_info("centrality", "example_degree")

        assert info["name"] == "example_degree"
        assert "degree" in info["description"].lower()

    def test_example_centrality_plugin_supports(self):
        """Test example centrality plugin capabilities."""
        registry = PluginRegistry()
        plugin = registry.get("centrality", "example_degree")

        assert plugin.supports_weighted is True
        assert plugin.supports_directed is True
        assert plugin.supports_multilayer is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
