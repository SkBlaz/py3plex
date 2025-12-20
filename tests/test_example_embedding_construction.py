import importlib.util
import itertools
import json
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_embedding_construction.py"
_MODULE_COUNTER = itertools.count()


def _install_py3plex_stubs(
    monkeypatch,
    record,
    tmp_path,
    *,
    dataset_exists=True,
    node2vec_error=None,
    visualization_error=None,
):
    """Provide a lightweight py3plex substitute the example can import."""

    class FakeNetwork:
        def __init__(self):
            record.append(("network_init",))

        def load_network(self, path, directed=True, input_type=None):
            record.append(("load_network", Path(path).name, directed, input_type))
            return self

        def save_network(self, path):
            record.append(("save_network", Path(path).name))
            Path(path).write_text("u v\n")

        def load_embedding(self, path):
            record.append(("load_embedding", Path(path).name))

    def get_dataset_path(name):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "imdb_gml.gml" and dataset_exists and not path.exists():
            path.write_text("gml")
        return str(path)

    def call_node2vec_binary(edgelist_file, embedding_file, binary="./node2vec", weighted=False):
        record.append(("call_node2vec_binary", Path(edgelist_file).name, Path(embedding_file).name, binary, weighted))
        if node2vec_error:
            raise node2vec_error
        Path(embedding_file).write_text("emb")

    def visualize_embedding(network):
        record.append(("visualize_embedding",))
        if visualization_error:
            raise visualization_error

    def get_2d_coordinates_tsne(network, output_format="json"):
        record.append(("get_2d_coordinates_tsne", output_format))
        return {"n1": [0.0, 1.0], "n2": [1.0, 0.0]}

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda: FakeNetwork()

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    train_node2vec_embedding_mod = types.ModuleType("py3plex.wrappers.train_node2vec_embedding")
    train_node2vec_embedding_mod.call_node2vec_binary = call_node2vec_binary

    wrappers_mod = types.ModuleType("py3plex.wrappers")
    wrappers_mod.train_node2vec_embedding = train_node2vec_embedding_mod

    embedding_visualization_mod = types.ModuleType("py3plex.visualization.embedding_visualization")
    embedding_visualization_mod.embedding_visualization = types.SimpleNamespace(visualize_embedding=visualize_embedding)
    embedding_visualization_mod.embedding_tools = types.SimpleNamespace(get_2d_coordinates_tsne=get_2d_coordinates_tsne)

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.embedding_visualization = embedding_visualization_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.wrappers = wrappers_mod
    py3plex_mod.visualization = visualization_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.wrappers", wrappers_mod)
    monkeypatch.setitem(sys.modules, "py3plex.wrappers.train_node2vec_embedding", train_node2vec_embedding_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization.embedding_visualization", embedding_visualization_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)


def _load_module_with_unique_name():
    module_name = f"example_embedding_construction_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_exits_early_when_dataset_missing(monkeypatch, capsys, tmp_path):
    record = []
    _install_py3plex_stubs(monkeypatch, record, tmp_path, dataset_exists=False)

    spec, module = _load_module_with_unique_name()

    with pytest.raises(SystemExit) as excinfo:
        spec.loader.exec_module(module)

    out = capsys.readouterr().out

    assert excinfo.value.code == 1
    assert "Error: Input file" in out
    assert record == []  # no dynamics invoked after missing dataset check


def test_full_flow_runs_and_exports_coordinates(monkeypatch, capsys, tmp_path):
    record = []
    _install_py3plex_stubs(monkeypatch, record, tmp_path)

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    assert ("load_network", "imdb_gml.gml", True, "gml") in record
    assert ("save_network", "test.edgelist") in record
    assert ("call_node2vec_binary", "test.edgelist", "test_embedding.emb", "./node2vec", False) in record
    assert ("load_embedding", "test_embedding.emb") in record
    assert ("visualize_embedding",) in record
    assert ("get_2d_coordinates_tsne", "json") in record

    json_path = tmp_path / "embedding_coordinates.json"
    assert json_path.exists()
    assert json.loads(json_path.read_text()) == {"n1": [0.0, 1.0], "n2": [1.0, 0.0]}

    assert "EMBEDDING CONSTRUCTION COMPLETE" in out
    assert "Coordinates (JSON):" in out


def test_visualization_failure_still_exports(monkeypatch, capsys, tmp_path):
    record = []
    _install_py3plex_stubs(monkeypatch, record, tmp_path, visualization_error=RuntimeError("boom"))

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    assert ("visualize_embedding",) in record
    assert ("get_2d_coordinates_tsne", "json") in record  # continues after visualization error
    assert "Visualization error: boom" in out
    assert (tmp_path / "embedding_coordinates.json").exists()


def test_node2vec_missing_binary_exits(monkeypatch, capsys, tmp_path):
    record = []
    _install_py3plex_stubs(
        monkeypatch,
        record,
        tmp_path,
        node2vec_error=FileNotFoundError("node2vec missing"),
    )

    spec, module = _load_module_with_unique_name()

    with pytest.raises(SystemExit) as excinfo:
        spec.loader.exec_module(module)

    out = capsys.readouterr().out

    assert excinfo.value.code == 1
    assert "Node2Vec binary not found" in out
    assert ("load_network", "imdb_gml.gml", True, "gml") in record
    assert ("save_network", "test.edgelist") in record
    assert ("call_node2vec_binary", "test.edgelist", "test_embedding.emb", "./node2vec", False) in record
    assert ("load_embedding", "test_embedding.emb") not in record
