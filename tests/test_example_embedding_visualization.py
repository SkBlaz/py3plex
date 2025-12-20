import importlib.util
import itertools
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_embedding_visualization.py"
_MODULE_COUNTER = itertools.count()


def _install_py3plex_stubs(monkeypatch, record, tmp_path, *, dataset_exists=True, load_embedding_error=None, visualize_error=None):
    """Provide a minimal py3plex substitute so the example can run deterministically."""

    class FakeNetwork:
        def __init__(self):
            record.append(("network_init",))

        def load_embedding(self, path):
            record.append(("load_embedding", Path(path).name))
            if load_embedding_error:
                raise load_embedding_error
            if not Path(path).exists():
                raise FileNotFoundError(path)
            return self

    def get_dataset_path(name):
        record.append(("get_dataset_path", name))
        path = tmp_path / name
        if dataset_exists:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("embedding")
        return str(path)

    def visualize_embedding(network):
        record.append(("visualize_embedding",))
        if visualize_error:
            raise visualize_error

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda: FakeNetwork()

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    embedding_visualization_mod = types.ModuleType("py3plex.visualization.embedding_visualization")
    embedding_visualization_mod.embedding_visualization = types.SimpleNamespace(visualize_embedding=visualize_embedding)

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.embedding_visualization = embedding_visualization_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.visualization = visualization_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization.embedding_visualization", embedding_visualization_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)


def _load_module_with_unique_name():
    module_name = f"example_embedding_visualization_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_visualization_flow_loads_and_visualizes(monkeypatch, tmp_path):
    record = []
    _install_py3plex_stubs(monkeypatch, record, tmp_path)

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    assert record == [
        ("network_init",),
        ("get_dataset_path", "karate.emb"),
        ("load_embedding", "karate.emb"),
        ("visualize_embedding",),
    ]
    assert (tmp_path / "karate.emb").read_text() == "embedding"


def test_missing_embedding_file_raises(monkeypatch, tmp_path):
    record = []
    _install_py3plex_stubs(monkeypatch, record, tmp_path, dataset_exists=False)

    spec, module = _load_module_with_unique_name()

    with pytest.raises(FileNotFoundError):
        spec.loader.exec_module(module)

    # Visualization never reached when embedding is missing
    assert ("visualize_embedding",) not in record


def test_visualization_error_propagates(monkeypatch, tmp_path):
    record = []
    _install_py3plex_stubs(
        monkeypatch,
        record,
        tmp_path,
        visualize_error=RuntimeError("viz failed"),
    )

    spec, module = _load_module_with_unique_name()

    with pytest.raises(RuntimeError, match="viz failed"):
        spec.loader.exec_module(module)

    assert ("visualize_embedding",) in record
