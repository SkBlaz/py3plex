import importlib.util
import itertools
import sys
import types
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_decomposition_and_classification.py"
_MODULE_COUNTER = itertools.count()


def _install_py3plex_fakes(monkeypatch, record, dataset_path):
    """Provide the py3plex module tree expected by the example script."""

    class FakeNetwork:
        def load_network(self, input_file, directed=False, input_type=None):
            record.append(("load_network", input_file, directed, input_type))
            return self

        def basic_stats(self):
            record.append(("basic_stats",))

        def get_decomposition_cycles(self):
            record.append(("get_decomposition_cycles",))
            return [("A", "B", "C"), ("C", "D", "E")]

        def get_decomposition(self, heuristic, cycle):
            record.append(("get_decomposition", tuple(heuristic), tuple(cycle)))
            labels = np.array(
                [[0, "class1"], [1, "class1"], [2, "class2"], [3, "class2"]], dtype=object
            )
            for name in heuristic:
                yield types.SimpleNamespace(name=name), labels, name

    class FakePPR:
        calls = []

        @staticmethod
        def construct_PPR_matrix(network):
            FakePPR.calls.append(network)
            record.append(("construct_PPR_matrix", getattr(network, "name", None)))
            # 4 nodes x 2 dimensions to match the labels above
            return np.array([[0.0, 1.0], [2.0, 3.0], [4.0, 5.0], [6.0, 7.0]])

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

    algorithms_mod = types.ModuleType("py3plex.algorithms")
    algorithms_mod.__path__ = []

    network_classification_mod = types.ModuleType("py3plex.algorithms.network_classification")
    network_classification_mod.PPR = FakePPR

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    algorithms_mod.network_classification = network_classification_mod
    py3plex_mod.core = core_mod
    py3plex_mod.algorithms = algorithms_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", core_mod.multinet)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms", algorithms_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms.network_classification", network_classification_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)

    return FakePPR


def test_decomposition_example_exits_when_dataset_missing(monkeypatch, capsys):
    record = []
    dataset_path = "/datasets/imdb.gpickle"

    _install_py3plex_fakes(monkeypatch, record, dataset_path)
    monkeypatch.setattr("os.path.exists", lambda path: False)

    module_name = f"example_decomp_missing_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)

    with pytest.raises(SystemExit) as excinfo:
        spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert excinfo.value.code == 1
    assert ("Error: Dataset file" in out) and dataset_path in out
    assert record == [("get_dataset_path", "imdb.gpickle")]


def test_decomposition_example_runs_with_lightweight_fakes(monkeypatch, capsys):
    record = []
    dataset_path = "/datasets/imdb.gpickle"

    FakePPR = _install_py3plex_fakes(monkeypatch, record, dataset_path)

    # Keep the example fast and deterministic
    monkeypatch.setattr("os.path.exists", lambda path: True)

    original_arange = np.arange

    def limited_arange(*args, **kwargs):
        if args == (0.1, 1, 0.1) and not kwargs:
            return np.array([0.5])
        return original_arange(*args, **kwargs)

    monkeypatch.setattr(np, "arange", limited_arange)

    time_counter = itertools.count()
    monkeypatch.setattr("time.time", lambda: next(time_counter) * 0.1)

    # Simplify sklearn pieces to avoid heavy computation
    from sklearn import metrics, model_selection, svm

    class FakeSVC:
        def fit(self, X, y):
            self.label = y[0]
            record.append(("fit", len(X)))
            return self

        def predict(self, X):
            record.append(("predict", len(X)))
            return np.full(len(X), self.label)

    def fake_f1_score(y_true, y_pred, average=None):
        record.append(("f1_score", average))
        return 0.5 if average == "micro" else 0.25

    class FakeStratifiedShuffleSplit:
        def __init__(self, n_splits, test_size, random_state):
            record.append(("StratifiedShuffleSplit", n_splits, test_size, random_state))

        def split(self, X, y):
            record.append(("split", len(X), len(y)))
            half = len(y) // 2
            yield np.arange(half), np.arange(half, len(y))

    monkeypatch.setattr(svm, "SVC", FakeSVC)
    monkeypatch.setattr(metrics, "f1_score", fake_f1_score)
    monkeypatch.setattr(model_selection, "StratifiedShuffleSplit", FakeStratifiedShuffleSplit)

    # Avoid GUI popups
    import matplotlib.pyplot as plt

    monkeypatch.setattr(plt, "show", lambda: record.append(("show",)), raising=False)

    module_name = f"example_decomp_ok_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    # Basic progression and ordering
    assert record[0] == ("get_dataset_path", "imdb.gpickle")
    assert ("multi_layer_network",) in record

    load_call = next(entry for entry in record if entry[0] == "load_network")
    assert load_call[1:] == (dataset_path, True, "gpickle")

    # Decomposition pipeline calls
    assert ("basic_stats",) in record
    decomposition_calls = [entry for entry in record if entry[0] == "get_decomposition"]
    assert decomposition_calls, "get_decomposition should be invoked"
    heuristics_used = decomposition_calls[0][1]
    assert heuristics_used == ("idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi")

    # Construct_PPR_matrix is run for each decomposition and uses our fake vectors
    assert len([entry for entry in record if entry[0] == "construct_PPR_matrix"]) == len(heuristics_used)
    assert FakePPR.calls, "PPR should be called with decomposed networks"

    # Classifier loop uses patched sklearn utilities
    assert ("StratifiedShuffleSplit", 10, 0.5, 612312) in record
    assert ("fit", 2) in record  # 2 training samples per our fake split
    assert ("predict", 2) in record
    assert ("f1_score", "micro") in record
    assert ("f1_score", "macro") in record

    # Results frame and winner
    assert hasattr(module, "df")
    assert len(module.df) == len(heuristics_used)
    assert np.allclose(module.df["percent_train"], 0.5)
    assert module.best_heuristic["heuristic"] == "idf"

    # Output includes summary sections and visualization hook was exercised
    assert "CLASSIFICATION RESULTS" in out
    assert "Best Performing Configuration" in out
    assert ("show",) in record
