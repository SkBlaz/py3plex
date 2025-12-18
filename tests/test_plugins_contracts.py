"""Correctness contracts for py3plex.plugins.

These tests focus on edge cases and invariants for plugin registration and discovery,
plus algorithmic correctness of the bundled example plugins.
"""

from __future__ import annotations

import sys
import types

import pytest

from py3plex.core import multinet
from py3plex.plugins.examples import (
    ExampleCircularLayout,
    ExampleNetworkDensity,
    ExampleSimpleCommunity,
)
from py3plex.plugins.registry import PluginRegistry, discover_plugins


@pytest.fixture(autouse=True)
def _reset_registry():
    PluginRegistry.reset()
    yield
    PluginRegistry.reset()


def test_registry_errors_on_unknown_types():
    registry = PluginRegistry()

    with pytest.raises(KeyError, match="Unknown plugin type"):
        registry.get("does_not_exist", "x")

    with pytest.raises(KeyError, match="Unknown plugin type"):
        registry.list_plugins("does_not_exist")

    with pytest.raises(KeyError, match="Unknown plugin type"):
        registry.unregister("does_not_exist", "x")


def test_registry_overwrite_returns_newest_implementation():
    from py3plex.plugins.base import CentralityPlugin

    class First(CentralityPlugin):
        @property
        def name(self):
            return "x"

        def compute(self, network, **kwargs):
            return {"v": 1}

    class Second(CentralityPlugin):
        @property
        def name(self):
            return "x"

        def compute(self, network, **kwargs):
            return {"v": 2}

    PluginRegistry.register_plugin("centrality", "x", First)
    PluginRegistry.register_plugin("centrality", "x", Second)

    plugin = PluginRegistry().get("centrality", "x")
    assert plugin.compute(None)["v"] == 2


def test_discover_plugins_skips_private_modules(tmp_path):
    plugin_file = tmp_path / "_private.py"
    plugin_file.write_text(
        """
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register("centrality", "should_not_load")
class Private(CentralityPlugin):
    @property
    def name(self):
        return "should_not_load"

    def compute(self, network, **kwargs):
        return {}
"""
    )

    count = discover_plugins(str(tmp_path))
    assert count == 0
    assert "should_not_load" not in PluginRegistry().list_plugins("centrality")["centrality"]
    assert "_private" not in sys.modules


def test_discover_plugins_skips_already_loaded_module(tmp_path):
    module_name = "collision_module"
    plugin_file = tmp_path / f"{module_name}.py"
    plugin_file.write_text(
        f"""
from py3plex.plugins import CentralityPlugin, PluginRegistry

@PluginRegistry.register("centrality", "collide")
class Collide(CentralityPlugin):
    @property
    def name(self):
        return "collide"

    def compute(self, network, **kwargs):
        return {{"ok": 1}}
"""
    )

    sys.modules[module_name] = types.ModuleType(module_name)
    try:
        count = discover_plugins(str(tmp_path))
        assert count == 0
        assert "collide" not in PluginRegistry().list_plugins("centrality")["centrality"]
    finally:
        sys.modules.pop(module_name, None)


def test_discover_plugins_returns_zero_for_file_path(tmp_path):
    file_path = tmp_path / "not_a_dir.py"
    file_path.write_text("# not a directory")

    assert discover_plugins(str(file_path)) == 0


def test_example_network_density_matches_closed_form():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "A", "type": "L"},
            {"source": "B", "type": "L"},
            {"source": "C", "type": "L"},
        ]
    )
    net.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "L", "target_type": "L"},
            {"source": "B", "target": "C", "source_type": "L", "target_type": "L"},
        ]
    )

    result = ExampleNetworkDensity().compute(net)

    assert result["num_nodes"] == 3
    assert result["num_edges"] == 2
    assert result["density"] == pytest.approx(2 * 2 / (3 * 2))


def test_example_circular_layout_positions_unit_circle_and_2d_only():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "A", "type": "L"},
            {"source": "B", "type": "L"},
            {"source": "C", "type": "L"},
            {"source": "D", "type": "L"},
        ]
    )

    plugin = ExampleCircularLayout()
    positions = plugin.compute_layout(net, dimensions=2)

    assert set(positions) == set(net.core_network.nodes())
    for x, y in positions.values():
        assert (x * x + y * y) == pytest.approx(1.0, abs=1e-10)

    with pytest.raises(ValueError, match="2D"):
        plugin.compute_layout(net, dimensions=3)


def test_example_simple_community_connected_components_and_deterministic():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["A", "L", "B", "L", 1.0],
            ["X", "L", "Y", "L", 1.0],
        ],
        input_type="list",
    )

    plugin = ExampleSimpleCommunity()
    communities1 = plugin.detect(net, num_communities=10)
    communities2 = plugin.detect(net, num_communities=10)

    assert communities1 == communities2
    assert communities1[("A", "L")] == communities1[("B", "L")]
    assert communities1[("X", "L")] == communities1[("Y", "L")]
    assert communities1[("A", "L")] != communities1[("X", "L")]

