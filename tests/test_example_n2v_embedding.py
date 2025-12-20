import importlib.util
import itertools
import json
import sys
import types
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "advanced"
    / "example_n2v_embedding.py"
)
_MODULE_COUNTER = itertools.count()


def _install_n2v_stubs(monkeypatch, tmp_path, *, raise_on_binary=False):
    dataset_requests = []
    data_path_requests = []
    load_network_calls = []
    save_network_calls = []
    load_embedding_calls = []
    call_node2vec_calls = []
    visualize_calls = []
    get_coords_calls = []
    created_networks = []

    class FakeNetwork:
        def __init__(self):
            self.saved_paths = []

        def load_network(self, path, directed, input_type):
            load_network_calls.append(
                {"path": path, "directed": directed, "input_type": input_type}
            )
            return self

        def save_network(self, path):
            save_network_calls.append(path)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("fake edgelist")
            self.saved_paths.append(path)
            return self

        def load_embedding(self, path):
            load_embedding_calls.append(path)
            return self

    def get_dataset_path(name):
        dataset_requests.append(name)
        return str(tmp_path / name)

    def get_data_path(name):
        data_path_requests.append(name)
        dest = tmp_path / name
        dest.mkdir(parents=True, exist_ok=True)
        return str(dest)

    def call_node2vec_binary(edgelist_path, embedding_path, binary, weighted):
        call_node2vec_calls.append(
            {
                "edgelist_path": edgelist_path,
                "embedding_path": embedding_path,
                "binary": binary,
                "weighted": weighted,
            }
        )
        if raise_on_binary:
            raise FileNotFoundError(binary)
        Path(embedding_path).write_text("embedding content")

    def visualize_embedding(network):
        visualize_calls.append(network)

    def get_2d_coordinates_tsne(network, output_format):
        get_coords_calls.append({"network": network, "output_format": output_format})
        return {"coords": [[1, 2], [3, 4]]}

    def multi_layer_network():
        network = FakeNetwork()
        created_networks.append(network)
        return network

    train_node2vec_mod = types.ModuleType("py3plex.wrappers.train_node2vec_embedding")
    train_node2vec_mod.call_node2vec_binary = call_node2vec_binary

    wrappers_mod = types.ModuleType("py3plex.wrappers")
    wrappers_mod.train_node2vec_embedding = train_node2vec_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path
    utils_mod.get_data_path = get_data_path

    multinet_mod = types.SimpleNamespace(multi_layer_network=multi_layer_network)
    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    embedding_visualization_obj = types.SimpleNamespace(
        visualize_embedding=visualize_embedding
    )
    embedding_tools_mod = types.SimpleNamespace(
        get_2d_coordinates_tsne=get_2d_coordinates_tsne
    )
    embedding_visualization_mod = types.ModuleType(
        "py3plex.visualization.embedding_visualization"
    )
    embedding_visualization_mod.embedding_visualization = embedding_visualization_obj
    embedding_visualization_mod.embedding_tools = embedding_tools_mod

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.embedding_visualization = embedding_visualization_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.wrappers = wrappers_mod
    py3plex_mod.utils = utils_mod
    py3plex_mod.visualization = visualization_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.wrappers", wrappers_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.wrappers.train_node2vec_embedding", train_node2vec_mod
    )
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(
        sys.modules,
        "py3plex.visualization.embedding_visualization",
        embedding_visualization_mod,
    )

    return {
        "dataset_requests": dataset_requests,
        "data_path_requests": data_path_requests,
        "load_network_calls": load_network_calls,
        "save_network_calls": save_network_calls,
        "load_embedding_calls": load_embedding_calls,
        "call_node2vec_calls": call_node2vec_calls,
        "visualize_calls": visualize_calls,
        "get_coords_calls": get_coords_calls,
        "created_networks": created_networks,
        "tmp_path": tmp_path,
    }


def _load_module_with_unique_name():
    module_name = f"example_n2v_embedding_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_n2v_example_runs_happy_path(monkeypatch, tmp_path, capsys):
    trackers = _install_n2v_stubs(monkeypatch, tmp_path)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert out == ""

    datasets_dir = tmp_path / "datasets"
    assert trackers["dataset_requests"] == ["imdb_gml.gml"]
    assert trackers["data_path_requests"] == ["datasets"]

    assert trackers["load_network_calls"] == [
        {
            "path": str(tmp_path / "imdb_gml.gml"),
            "directed": True,
            "input_type": "gml",
        }
    ]
    assert trackers["save_network_calls"] == [str(datasets_dir / "test.edgelist")]

    assert trackers["call_node2vec_calls"] == [
        {
            "edgelist_path": str(datasets_dir / "test.edgelist"),
            "embedding_path": str(datasets_dir / "test_embedding.emb"),
            "binary": "./node2vec",
            "weighted": False,
        }
    ]
    assert trackers["load_embedding_calls"] == [
        str(datasets_dir / "test_embedding.emb")
    ]
    assert trackers["visualize_calls"] == trackers["created_networks"]
    assert trackers["get_coords_calls"] == [
        {"network": trackers["created_networks"][0], "output_format": "json"}
    ]

    json_path = datasets_dir / "embedding_coordinates.json"
    assert json_path.exists()
    assert json.loads(json_path.read_text()) == {"coords": [[1, 2], [3, 4]]}


def test_n2v_example_handles_missing_binary(monkeypatch, tmp_path, capsys):
    trackers = _install_n2v_stubs(monkeypatch, tmp_path, raise_on_binary=True)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert "Node2Vec binary not found: ./node2vec" in out
    assert "Consider using pure Python alternatives:" in out
    assert "pip install node2vec" in out
    assert "pip install pecanpy" in out

    datasets_dir = tmp_path / "datasets"
    assert trackers["call_node2vec_calls"][0]["embedding_path"] == str(
        datasets_dir / "test_embedding.emb"
    )

    assert trackers["load_embedding_calls"] == []
    assert trackers["visualize_calls"] == []
    assert trackers["get_coords_calls"] == []
    assert not (datasets_dir / "embedding_coordinates.json").exists()
