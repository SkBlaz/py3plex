import importlib.util
import itertools
import sys
import types
from pathlib import Path
import numpy as np


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "advanced"
    / "example_network_decomposition_different_meta_paths.py"
)
_MODULE_COUNTER = itertools.count()


def _install_decomposition_stubs(monkeypatch, tmp_path, *, cycles=None):
    dataset_requests = []
    load_network_calls = []
    basic_stats_calls = []
    decomposition_cycle_calls = []
    decomposition_calls = []
    created_matrices = []
    cycles = cycles if cycles is not None else [("a", "b", "c")]

    class FakeMatrix:
        def __init__(self, data, label):
            self.data = data
            self.label = label

        def todense(self):
            return self.data

        def __array__(self, dtype=None):
            return self.data if dtype is None else self.data.astype(dtype)

    class FakeNetwork:
        def load_network(self, *, input_file, directed, input_type):
            load_network_calls.append(
                {
                    "input_file": input_file,
                    "directed": directed,
                    "input_type": input_type,
                }
            )
            return self

        def basic_stats(self):
            basic_stats_calls.append("called")

        def get_decomposition_cycles(self):
            decomposition_cycle_calls.append("called")
            return cycles

        def get_decomposition(self, heuristic, cycle):
            decomposition_calls.append({"heuristic": heuristic, "cycle": cycle})
            results = []
            for idx, cyc in enumerate(cycle):
                matrix = FakeMatrix(
                    data=np.array([[0, idx + 1], [idx + 1, 0]]),
                    label=cyc,
                )
                created_matrices.append(matrix)
                results.append((matrix,))
            return results

    def get_dataset_path(name):
        dataset_requests.append(name)
        path = tmp_path / name
        path.write_text("stub dataset")
        return str(path)

    multinet_mod = types.SimpleNamespace(multi_layer_network=lambda: FakeNetwork())
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

    return {
        "dataset_requests": dataset_requests,
        "load_network_calls": load_network_calls,
        "basic_stats_calls": basic_stats_calls,
        "decomposition_cycle_calls": decomposition_cycle_calls,
        "decomposition_calls": decomposition_calls,
        "created_matrices": created_matrices,
        "cycles": cycles,
        "tmp_path": tmp_path,
    }


def _load_module_with_unique_name():
    module_name = f"example_decomposition_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_decomposition_example_runs_with_cycle(monkeypatch, tmp_path, capsys):
    trackers = _install_decomposition_stubs(monkeypatch, tmp_path)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    dataset_path = tmp_path / "imdb.gpickle"

    assert trackers["dataset_requests"] == ["imdb.gpickle"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": True, "input_type": "gpickle"}
    ]
    assert trackers["basic_stats_calls"] == ["called"]
    assert trackers["decomposition_cycle_calls"] == ["called"]

    assert trackers["decomposition_calls"] == [
        {"heuristic": ["tf"], "cycle": [("a", "b", "c")]},
        {"heuristic": ["tf"], "cycle": [("a", "b", "c")]},
    ]

    assert "Running optimization for" in out
    assert str(trackers["cycles"][0]) in out
    assert "[[0 1]" in out
    assert out.strip().endswith("1")


def test_decomposition_example_runs_with_no_cycles(monkeypatch, tmp_path, capsys):
    trackers = _install_decomposition_stubs(monkeypatch, tmp_path, cycles=[])
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    dataset_path = tmp_path / "imdb.gpickle"

    assert trackers["dataset_requests"] == ["imdb.gpickle"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": True, "input_type": "gpickle"}
    ]
    assert trackers["basic_stats_calls"] == ["called"]
    assert trackers["decomposition_cycle_calls"] == ["called"]

    # Only the aggregated call should happen when no cycles are returned.
    assert trackers["decomposition_calls"] == [{"heuristic": ["tf"], "cycle": []}]

    assert "Running optimization for" in out
    assert "[[" not in out
    assert "('a', 'b', 'c')" not in out
