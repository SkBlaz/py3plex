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
    / "example_inverse_network.py"
)
_MODULE_COUNTER = itertools.count()


def _install_stubs(monkeypatch, tmp_path, *, file_exists):
    """Install lightweight py3plex stubs to run the example deterministically."""
    networks = []
    dataset_path = tmp_path / "epigenetics.gpickle"
    if file_exists:
        dataset_path.touch()

    def get_dataset_path(name):
        return dataset_path

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

        def basic_stats(self):
            self.trace.append(("basic_stats",))

        def invert(self, override_core=False):
            self.trace.append(("invert", override_core))
            self.override_core_used = override_core

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda: FakeNetwork()

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)

    return networks, dataset_path


def _load_module_with_unique_name():
    module_name = f"example_inverse_network_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_missing_dataset_prints_warning_and_exits(monkeypatch, tmp_path, capsys):
    networks, _ = _install_stubs(monkeypatch, tmp_path, file_exists=False)
    spec, module = _load_module_with_unique_name()

    with pytest.raises(SystemExit) as excinfo:
        spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert "Warning: Dataset file" in out
    assert "This example requires the epigenetics dataset." in out
    assert excinfo.value.code == 1
    assert networks == []  # No network should be constructed when the dataset is missing.


def test_successful_run_loads_inverts_and_reports(monkeypatch, tmp_path, capsys):
    networks, dataset_path = _install_stubs(monkeypatch, tmp_path, file_exists=True)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    network = networks[-1]

    assert "Loading directed multilayer network..." in out
    assert "INVERTING NETWORK (reversing all edge directions)..." in out
    assert "INVERTED NETWORK STATISTICS" in out

    # Verify the core workflow was executed in order.
    assert network.trace == [
        ("load_network", dataset_path, True, "gpickle_biomine"),
        ("basic_stats",),
        ("invert", True),
        ("basic_stats",),
    ]
    assert network.loaded_path == dataset_path
    assert network.loaded_directed is True
    assert network.loaded_input_type == "gpickle_biomine"
    assert network.override_core_used is True
