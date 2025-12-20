import importlib.util
import itertools
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_decomposition_ground_truth.py"
)
_MODULE_COUNTER = itertools.count()


def _install_ground_truth_fakes(monkeypatch, record, dataset_path, cycles=None, decomposition_items=None):
    """Provide the py3plex pieces the example relies on."""
    cycles = cycles if cycles is not None else ["cycle_a", "cycle_a"]
    decomposition_items = decomposition_items if decomposition_items is not None else ["decomp1"]

    class FakeNetwork:
        def load_network(self, input_file, directed=False, input_type=None):
            record.append(("load_network", input_file, directed, input_type))
            return self

        def basic_stats(self):
            record.append(("basic_stats",))

        def get_decomposition_cycles(self):
            record.append(("get_decomposition_cycles",))
            return cycles

        def get_decomposition(self, heuristic, cycle):
            record.append(("get_decomposition", tuple(heuristic), tuple(cycle)))
            yield from decomposition_items

    def fake_multi_layer_network():
        record.append(("multi_layer_network",))
        return FakeNetwork()

    def get_dataset_path(name):
        record.append(("get_dataset_path", name))
        return dataset_path

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []

    core_mod = types.ModuleType("py3plex.core")
    core_mod.__path__ = []
    core_mod.multinet = types.SimpleNamespace(multi_layer_network=fake_multi_layer_network)

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", core_mod.multinet)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)


def _load_module_with_unique_name():
    module_name = f"example_decomp_gt_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_ground_truth_example_runs_and_deduplicates_cycles(monkeypatch, capsys):
    record = []
    dataset_path = "/datasets/imdb_ground_truth.gpickle"
    cycles = ["triplet", "triplet"]  # Duplicated on purpose to verify set() usage
    decompositions = ["decomp_a", "decomp_b"]

    _install_ground_truth_fakes(monkeypatch, record, dataset_path, cycles=cycles, decomposition_items=decompositions)

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    # Ensure the example walks through dataset resolution and network loading
    assert record[:3] == [
        ("get_dataset_path", "imdb.gpickle"),
        ("multi_layer_network",),
        ("load_network", dataset_path, True, "gpickle"),
    ]
    assert ("basic_stats",) in record
    assert ("get_decomposition_cycles",) in record

    # Decomposition uses the expected heuristics and a deduplicated cycle set
    decomposition_call = next(entry for entry in record if entry[0] == "get_decomposition")
    heuristics_used, cycles_seen = decomposition_call[1:]
    assert heuristics_used == ("idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi")
    assert cycles_seen == ("triplet",)

    # Output includes the dataset banner, a single cycle line, and both decomposition entries
    assert f"Running optimization for {dataset_path}" in out
    assert out.count("triplet") == 1
    for item in decompositions:
        assert item in out


def test_ground_truth_example_calls_decomposition_even_with_empty_cycles(monkeypatch, capsys):
    record = []
    dataset_path = "/datasets/emptycycles.gpickle"

    _install_ground_truth_fakes(
        monkeypatch, record, dataset_path, cycles=[], decomposition_items=["single_decomposition"]
    )

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    decomposition_call = next(entry for entry in record if entry[0] == "get_decomposition")
    heuristics_used, cycles_seen = decomposition_call[1:]
    assert heuristics_used == ("idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi")
    assert cycles_seen == ()  # The example forwards the empty cycle list

    # Even without cycles to print, the decomposition results are emitted
    assert "single_decomposition" in out
