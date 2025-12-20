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
    / "example_PPR.py"
)
_MODULE_COUNTER = itertools.count()


def _install_ppr_stubs(monkeypatch, tmp_path, *, fail_on_load=False, fail_on_validate=False):
    dataset_requests = []
    load_network_calls = []
    validate_calls = []
    plot_calls = []
    svc_calls = []
    created_networks = []

    class FakeSVC:
        def __init__(self, *args, **kwargs):
            svc_calls.append({"args": args, "kwargs": kwargs})

    class FakeNetwork:
        def __init__(self):
            created_networks.append(self)
            self.core_network = {"id": "core"}
            self.labels = ["a", "b"]

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

    def multi_layer_network(**kwargs):
        del kwargs
        return FakeNetwork()

    def get_dataset_path(name):
        dataset_requests.append(name)
        path = tmp_path / name
        path.write_text("stub dataset")
        return str(path)

    def validate_ppr(core_network, labels, *, multiclass_classifier, repetitions):
        validate_calls.append(
            {
                "core_network": core_network,
                "labels": labels,
                "multiclass_classifier": multiclass_classifier,
                "repetitions": repetitions,
            }
        )
        if fail_on_validate:
            raise ValueError("validate failure")
        return {"core": core_network, "labels": labels, "model": multiclass_classifier}

    def plot_core_macro(result):
        plot_calls.append(result)

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = multi_layer_network

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    ppr_mod = types.ModuleType("py3plex.algorithms.network_classification.PPR")
    ppr_mod.validate_ppr = validate_ppr
    ppr_mod.__all__ = ["validate_ppr"]

    nc_mod = types.ModuleType("py3plex.algorithms.network_classification")
    nc_mod.__path__ = []
    nc_mod.PPR = ppr_mod

    algorithms_mod = types.ModuleType("py3plex.algorithms")
    algorithms_mod.__path__ = []
    algorithms_mod.network_classification = nc_mod

    benchmark_mod = types.ModuleType("py3plex.visualization.benchmark_visualizations")
    benchmark_mod.plot_core_macro = plot_core_macro
    benchmark_mod.__all__ = ["plot_core_macro"]

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.__path__ = []
    visualization_mod.benchmark_visualizations = benchmark_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod
    py3plex_mod.algorithms = algorithms_mod
    py3plex_mod.visualization = visualization_mod

    sklearn_svm_mod = types.ModuleType("sklearn.svm")
    sklearn_svm_mod.SVC = FakeSVC

    sklearn_mod = types.ModuleType("sklearn")
    sklearn_mod.__path__ = []
    sklearn_mod.svm = sklearn_svm_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms", algorithms_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms.network_classification", nc_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.algorithms.network_classification.PPR", ppr_mod
    )
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.visualization.benchmark_visualizations", benchmark_mod
    )
    monkeypatch.setitem(sys.modules, "sklearn", sklearn_mod)
    monkeypatch.setitem(sys.modules, "sklearn.svm", sklearn_svm_mod)

    return {
        "dataset_requests": dataset_requests,
        "load_network_calls": load_network_calls,
        "validate_calls": validate_calls,
        "plot_calls": plot_calls,
        "svc_calls": svc_calls,
        "created_networks": created_networks,
        "tmp_path": tmp_path,
    }


def _load_module_with_unique_name():
    module_name = f"example_PPR_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_ppr_example_runs_with_stubbed_dependencies(monkeypatch, tmp_path):
    trackers = _install_ppr_stubs(monkeypatch, tmp_path)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    dataset_path = tmp_path / "cora.mat"
    assert trackers["dataset_requests"] == ["cora.mat"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": False, "input_type": "sparse"}
    ]
    assert trackers["svc_calls"] == [
        {"args": (), "kwargs": {"kernel": "linear", "C": 1, "probability": True}}
    ]

    validate_call = trackers["validate_calls"][0]
    network = trackers["created_networks"][0]
    assert validate_call["core_network"] is network.core_network
    assert validate_call["labels"] is network.labels
    assert validate_call["multiclass_classifier"] is module.model
    assert validate_call["repetitions"] == 2

    assert trackers["plot_calls"] == [module.validation_results]


def test_ppr_example_bubbles_validation_failure(monkeypatch, tmp_path):
    trackers = _install_ppr_stubs(monkeypatch, tmp_path, fail_on_validate=True)
    spec, module = _load_module_with_unique_name()

    with pytest.raises(ValueError, match="validate failure"):
        spec.loader.exec_module(module)

    dataset_path = tmp_path / "cora.mat"
    assert trackers["dataset_requests"] == ["cora.mat"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": False, "input_type": "sparse"}
    ]
    assert trackers["plot_calls"] == []


def test_ppr_example_bubbles_load_failure(monkeypatch, tmp_path):
    trackers = _install_ppr_stubs(monkeypatch, tmp_path, fail_on_load=True)
    spec, module = _load_module_with_unique_name()

    with pytest.raises(ValueError, match="load failure"):
        spec.loader.exec_module(module)

    dataset_path = tmp_path / "cora.mat"
    assert trackers["dataset_requests"] == ["cora.mat"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": False, "input_type": "sparse"}
    ]
    assert trackers["validate_calls"] == []
    assert trackers["plot_calls"] == []
