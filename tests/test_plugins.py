"""Tests for the py3plex plugin registry and example plugins."""

import sys

import pytest

from py3plex.plugins.base import CentralityPlugin
from py3plex.plugins.examples import ExampleNetworkDensity
from py3plex.plugins.registry import PluginRegistry, discover_plugins


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure a clean registry for each test."""
    PluginRegistry.reset()
    yield
    PluginRegistry.reset()


class _DummyCentrality(CentralityPlugin):
    @property
    def name(self):
        return "dummy"

    def compute(self, network, **kwargs):
        return {}


def test_register_plugin_rejects_unknown_type():
    """Invalid plugin types should raise a ValueError."""
    with pytest.raises(ValueError):
        PluginRegistry.register_plugin("unknown", "dummy", _DummyCentrality)


def test_register_plugin_requires_base_class():
    """Plugin classes must inherit from BasePlugin."""
    with pytest.raises(TypeError):
        PluginRegistry.register_plugin("centrality", "not_a_plugin", object)


def test_get_raises_runtime_when_validation_fails():
    """Plugins that fail validation should not be returned."""

    class FailingCentrality(CentralityPlugin):
        @property
        def name(self):
            return "failing"

        def validate(self) -> bool:
            return False

        def compute(self, network, **kwargs):
            return {}

    PluginRegistry.register_plugin("centrality", "failing", FailingCentrality)

    with pytest.raises(RuntimeError):
        PluginRegistry().get("centrality", "failing")


def test_get_plugin_info_reports_metadata():
    """Metadata returned by get_plugin_info should mirror plugin properties."""

    class InfoPlugin(CentralityPlugin):
        @property
        def name(self):
            return "info"

        @property
        def version(self):
            return "2.3"

        @property
        def author(self):
            return "Me"

        @property
        def description(self):
            return "desc"

        def compute(self, network, **kwargs):
            return {}

    PluginRegistry.register_plugin("centrality", "info", InfoPlugin)

    info = PluginRegistry().get_plugin_info("centrality", "info")

    assert info == {
        "name": "info",
        "version": "2.3",
        "author": "Me",
        "description": "desc",
        "type": "centrality",
    }


def test_discover_plugins_loads_from_directory(tmp_path):
    """discover_plugins should import modules and register plugins."""
    module_name = f"temp_plugin_{tmp_path.name}"
    plugin_file = tmp_path / f"{module_name}.py"
    plugin_file.write_text(
        f"""
from py3plex.plugins import PluginRegistry, CentralityPlugin

@PluginRegistry.register("centrality", "{module_name}")
class TempPlugin(CentralityPlugin):
    @property
    def name(self):
        return "{module_name}"

    def compute(self, network, **kwargs):
        return {{"ok": 1}}
"""
    )

    count = discover_plugins(str(tmp_path))

    try:
        assert count == 1
        plugin = PluginRegistry().get("centrality", module_name)
        assert plugin.compute(None)["ok"] == 1
        assert str(tmp_path) not in sys.path
    finally:
        sys.modules.pop(module_name, None)


def test_example_density_raises_for_invalid_network():
    """ExampleNetworkDensity should reject objects without core_network."""
    plugin = ExampleNetworkDensity()

    class NotANetwork:
        pass

    with pytest.raises(ValueError):
        plugin.compute(NotANetwork())
