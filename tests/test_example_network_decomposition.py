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
    / "example_network_decomposition.py"
)
_MODULE_COUNTER = itertools.count()


def _install_decomposition_stubs(monkeypatch, tmp_path, *, decompositions=None):
    dataset_requests = []
    load_network_calls = []
    basic_stats_calls = []
    get_decomposition_calls = []
    validate_calls = []
    created_dataframes = []

    decompositions = decompositions if decompositions is not None else [
        ("matrix_a", "labels_a"),
        ("matrix_b", "labels_b"),
    ]

    class FakeDataFrame:
        def __init__(self, rows=None):
            self.rows = list(rows) if rows else []
            created_dataframes.append(self)

        def append(self, other, ignore_index=False):
            del ignore_index  # unused but accepted for API compatibility
            new_rows = list(self.rows)
            if isinstance(other, FakeDataFrame):
                new_rows.extend(other.rows)
            else:
                new_rows.append(other)
            return FakeDataFrame(new_rows)

        def __str__(self):
            return f"FakeDataFrame(rows={self.rows})"

        __repr__ = __str__

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

        def get_decomposition(self):
            get_decomposition_calls.append("called")
            return decompositions

    def get_dataset_path(name):
        dataset_requests.append(name)
        path = tmp_path / name
        path.write_text("stub dataset")
        return str(path)

    def validate_label_propagation(matrix, labels, *, dataset_name, repetitions, normalization_scheme):
        validate_calls.append(
            {
                "matrix": matrix,
                "labels": labels,
                "dataset_name": dataset_name,
                "repetitions": repetitions,
                "normalization_scheme": normalization_scheme,
            }
        )
        return {
            "matrix": matrix,
            "labels": labels,
            "dataset_name": dataset_name,
            "repetitions": repetitions,
            "normalization_scheme": normalization_scheme,
        }

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda: FakeNetwork()

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    network_classification_mod = types.ModuleType("py3plex.algorithms.network_classification")
    network_classification_mod.validate_label_propagation = validate_label_propagation
    network_classification_mod.__all__ = ["validate_label_propagation"]

    algorithms_mod = types.ModuleType("py3plex.algorithms")
    algorithms_mod.network_classification = network_classification_mod

    benchmark_visualizations_mod = types.ModuleType("py3plex.visualization.benchmark_visualizations")
    benchmark_visualizations_mod.__all__ = []

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.benchmark_visualizations = benchmark_visualizations_mod

    pandas_mod = types.ModuleType("pandas")
    pandas_mod.DataFrame = FakeDataFrame

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod
    py3plex_mod.algorithms = algorithms_mod
    py3plex_mod.visualization = visualization_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms", algorithms_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.algorithms.network_classification", network_classification_mod
    )
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.visualization.benchmark_visualizations", benchmark_visualizations_mod
    )
    monkeypatch.setitem(sys.modules, "pandas", pandas_mod)

    return {
        "dataset_requests": dataset_requests,
        "load_network_calls": load_network_calls,
        "basic_stats_calls": basic_stats_calls,
        "get_decomposition_calls": get_decomposition_calls,
        "validate_calls": validate_calls,
        "created_dataframes": created_dataframes,
        "decompositions": decompositions,
        "tmp_path": tmp_path,
    }


def _load_module_with_unique_name():
    module_name = f"example_network_decomposition_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_network_decomposition_example_runs(monkeypatch, tmp_path, capsys):
    trackers = _install_decomposition_stubs(monkeypatch, tmp_path)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    dataset_path = tmp_path / "imdb_gml.gml"

    assert trackers["dataset_requests"] == ["imdb_gml.gml"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": True, "input_type": "gml"}
    ]
    assert trackers["basic_stats_calls"] == ["called"]
    assert trackers["get_decomposition_calls"] == ["called"]

    assert trackers["validate_calls"] == [
        {
            "matrix": "matrix_a",
            "labels": "labels_a",
            "dataset_name": "imdb_classic",
            "repetitions": 5,
            "normalization_scheme": "freq",
        },
        {
            "matrix": "matrix_b",
            "labels": "labels_b",
            "dataset_name": "imdb_classic",
            "repetitions": 5,
            "normalization_scheme": "freq",
        },
    ]

    assert "FakeDataFrame(rows=[{'matrix': 'matrix_a'" in out
    assert "'labels': 'labels_b'" in out


def test_network_decomposition_example_raises_without_decomposition(monkeypatch, tmp_path):
    trackers = _install_decomposition_stubs(monkeypatch, tmp_path, decompositions=[])
    spec, module = _load_module_with_unique_name()

    with pytest.raises(NameError) as excinfo:
        spec.loader.exec_module(module)

    dataset_path = tmp_path / "imdb_gml.gml"
    assert trackers["dataset_requests"] == ["imdb_gml.gml"]
    assert trackers["load_network_calls"] == [
        {"input_file": str(dataset_path), "directed": True, "input_type": "gml"}
    ]
    assert trackers["basic_stats_calls"] == ["called"]
    assert trackers["get_decomposition_calls"] == ["called"]
    assert trackers["validate_calls"] == []
    assert "validation_results" in str(excinfo.value)
