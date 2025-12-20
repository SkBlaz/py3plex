import importlib.util
import itertools
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "advanced"
    / "example_layer_extraction.py"
)
_MODULE_COUNTER = itertools.count()


def _install_stubs(monkeypatch, tmp_path, *, file_exists, layer_specs=None):
    """Install lightweight py3plex stubs to run the example deterministically."""
    networks = []
    stats_calls = []

    if layer_specs is None:
        layer_specs = [
            ("alpha", {"nodes": 3, "edges": 4}, ["a", "b"]),
            ("beta", {"nodes": 5, "edges": 2}, ["c"]),
        ]

    dataset_path = tmp_path / "epigenetics.gpickle"
    if file_exists:
        dataset_path.touch()

    def get_dataset_path(name):
        return dataset_path

    class FakeLayer:
        def __init__(self, name, stats_data, multiedges):
            self.name = name
            self.stats_data = stats_data
            self.multiedges = multiedges

    class FakeNetwork:
        def __init__(self):
            self.trace = []
            networks.append(self)

        def load_network(self, path, directed=True, input_type=None):
            self.trace.append(("load_network", path, directed, input_type))
            self.loaded_path = path
            self.loaded_directed = directed
            self.loaded_input_type = input_type
            return self

        def get_layers(self, verbose=True):
            self.trace.append(("get_layers", verbose))
            layers = [FakeLayer(name, stats, multiedges) for name, stats, multiedges in layer_specs]
            names = [layer.name for layer in layers]
            multiedges = [layer.multiedges for layer in layers]
            return names, layers, multiedges

    def core_network_statistics(network):
        stats_calls.append(network.name)
        return network.stats_data

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda: FakeNetwork()

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    basic_stats_mod = types.ModuleType("py3plex.algorithms.statistics.basic_statistics")
    basic_stats_mod.core_network_statistics = core_network_statistics

    statistics_mod = types.ModuleType("py3plex.algorithms.statistics")
    statistics_mod.basic_statistics = basic_stats_mod

    algorithms_mod = types.ModuleType("py3plex.algorithms")
    algorithms_mod.statistics = statistics_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod
    py3plex_mod.algorithms = algorithms_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms", algorithms_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms.statistics", statistics_mod)
    monkeypatch.setitem(
        sys.modules,
        "py3plex.algorithms.statistics.basic_statistics",
        basic_stats_mod,
    )

    return networks, stats_calls, dataset_path


def _load_module_with_unique_name():
    module_name = f"example_layer_extraction_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_missing_dataset_prints_warning_and_exits(monkeypatch, tmp_path, capsys):
    networks, stats_calls, _ = _install_stubs(monkeypatch, tmp_path, file_exists=False)
    spec, module = _load_module_with_unique_name()

    with pytest.raises(SystemExit) as excinfo:
        spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert "Warning: Dataset file" in out
    assert "This example requires the epigenetics dataset." in out
    assert excinfo.value.code == 1
    assert networks == []  # No network should be constructed when the dataset is missing.
    assert stats_calls == []


def test_successful_run_extracts_layers_and_reports(monkeypatch, tmp_path, capsys):
    networks, stats_calls, dataset_path = _install_stubs(monkeypatch, tmp_path, file_exists=True)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    network = networks[-1]

    assert "Loading multilayer network..." in out
    assert "Extracted 2 layers" in out
    assert "Layer: alpha" in out
    assert "nodes: 3" in out
    assert "edges: 4" in out
    assert "Number of multiedges: 1" in out  # beta has one multiedge entry
    assert "Layer analysis complete!" in out

    # Verify the core workflow was executed in order.
    assert network.trace == [
        ("load_network", dataset_path, False, "gpickle_biomine"),
        ("get_layers", True),
    ]
    assert stats_calls == ["alpha", "beta"]
    assert network.loaded_path == dataset_path
    assert network.loaded_directed is False
    assert network.loaded_input_type == "gpickle_biomine"
