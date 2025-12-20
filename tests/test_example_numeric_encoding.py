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
    / "example_numeric_encoding.py"
)
_MODULE_COUNTER = itertools.count()


def _install_numeric_encoding_stubs(monkeypatch, tmp_path, *, fail_on_load=False):
    dataset_requests = []
    random_calls = []
    load_network_calls = []
    basic_stats_calls = []
    encode_calls = []
    supra_matrices = []
    created_networks = []

    class FakeMatrix:
        def __init__(self, shape):
            self.shape = shape

    class FakeER:
        def __init__(self, n, layers, p, directed):
            random_calls.append({"n": n, "layers": layers, "p": p, "directed": directed})

        def get_supra_adjacency_matrix(self):
            matrix = FakeMatrix((1, 1))
            supra_matrices.append(matrix)
            return matrix

    def random_multilayer_ER(n, layers, p, directed=False):
        return FakeER(n, layers, p, directed)

    class FakeNetwork:
        def __init__(self):
            created_networks.append(self)
            self.numeric_core_network = None
            self.node_order_in_matrix = None

        def load_network(self, input_file, *, directed, input_type):
            load_network_calls.append(
                {
                    "input_file": input_file,
                    "directed": directed,
                    "input_type": input_type,
                }
            )
            if fail_on_load:
                raise ValueError("load failure")
            return self

        def basic_stats(self):
            basic_stats_calls.append("called")

        def _encode_to_numeric(self):
            encode_calls.append("called")
            self.numeric_core_network = FakeMatrix((4, 5))
            self.node_order_in_matrix = ["node_a", "node_b"]

    def multi_layer_network(**kwargs):
        del kwargs  # exercise the kwargs path without using them
        return FakeNetwork()

    def get_dataset_path(name):
        dataset_requests.append(name)
        path = tmp_path / name
        path.write_text("stub dataset")
        return str(path)

    random_generators_mod = types.ModuleType("py3plex.core.random_generators")
    random_generators_mod.random_multilayer_ER = random_multilayer_ER

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = multi_layer_network

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod
    core_mod.random_generators = random_generators_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.random_generators", random_generators_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)

    return {
        "dataset_requests": dataset_requests,
        "random_calls": random_calls,
        "load_network_calls": load_network_calls,
        "basic_stats_calls": basic_stats_calls,
        "encode_calls": encode_calls,
        "supra_matrices": supra_matrices,
        "created_networks": created_networks,
        "tmp_path": tmp_path,
    }


def _load_module_with_unique_name():
    module_name = f"example_numeric_encoding_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_numeric_encoding_example_runs(monkeypatch, tmp_path, capsys):
    trackers = _install_numeric_encoding_stubs(monkeypatch, tmp_path)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    output = capsys.readouterr().out
    dataset_path = tmp_path / "simple_multiplex.edgelist"

    assert trackers["random_calls"] == [
        {"n": 500, "layers": 8, "p": 0.05, "directed": False}
    ]
    assert trackers["dataset_requests"] == ["simple_multiplex.edgelist"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": False, "input_type": "multiplex_edges"}
    ]
    assert trackers["basic_stats_calls"] == ["called"]
    assert trackers["encode_calls"] == ["called"]

    network = trackers["created_networks"][-1]
    assert network.numeric_core_network.shape == (4, 5)
    assert network.node_order_in_matrix == ["node_a", "node_b"]
    assert "(4, 5)" in output
    assert trackers["supra_matrices"] and trackers["supra_matrices"][0].shape == (1, 1)


def test_numeric_encoding_example_bubbles_load_error(monkeypatch, tmp_path):
    trackers = _install_numeric_encoding_stubs(monkeypatch, tmp_path, fail_on_load=True)
    spec, module = _load_module_with_unique_name()

    with pytest.raises(ValueError, match="load failure"):
        spec.loader.exec_module(module)

    dataset_path = tmp_path / "simple_multiplex.edgelist"
    assert trackers["dataset_requests"] == ["simple_multiplex.edgelist"]
    assert trackers["random_calls"] == [
        {"n": 500, "layers": 8, "p": 0.05, "directed": False}
    ]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": False, "input_type": "multiplex_edges"}
    ]
    assert trackers["basic_stats_calls"] == []
    assert trackers["encode_calls"] == []
