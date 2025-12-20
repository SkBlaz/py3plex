import importlib.util
import itertools
import sys
import types
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "advanced"
    / "example_multilayer_vectorized_aggregation.py"
)
_MODULE_COUNTER = itertools.count()


def _install_vectorized_stubs(monkeypatch):
    aggregator_calls = []
    networks = []
    random_networks = []
    networkx_calls = []

    class FakeSparseMatrix:
        def __init__(self, shape, data):
            self.shape = shape
            self._data = data

        @property
        def nnz(self):
            return sum(1 for value in self._data.values() if value != 0)

        def __getitem__(self, key):
            return self._data.get(key, 0.0)

        def iter_nonzero(self):
            return ((key, value) for key, value in self._data.items() if value != 0)

    def aggregate_layers(edges_array, reducer="sum", to_sparse=True):
        by_pair = {}
        for row in edges_array:
            src, dst, weight = int(row[1]), int(row[2]), float(row[3])
            by_pair.setdefault((src, dst), []).append(weight)

        reducer_fn = {
            "sum": lambda weights: sum(weights),
            "mean": lambda weights: sum(weights) / len(weights),
            "max": lambda weights: max(weights),
        }[reducer]

        if by_pair:
            max_node = max(max(src, dst) for src, dst in by_pair)
            shape = (max_node + 1, max_node + 1)
        else:
            shape = (0, 0)

        aggregated = {pair: reducer_fn(weights) for pair, weights in by_pair.items()}

        if to_sparse:
            matrix = FakeSparseMatrix(shape, aggregated)
        else:
            matrix = np.zeros(shape, dtype=float)
            for (src, dst), weight in aggregated.items():
                matrix[src, dst] = weight

        aggregator_calls.append(
            {
                "reducer": reducer,
                "to_sparse": to_sparse,
                "edges": edges_array.copy(),
                "result": matrix,
            }
        )
        return matrix

    class FakeNetwork:
        def __init__(self, name="multilayer"):
            self.name = name
            self.edges = []
            self.nodes = set()

        def add_edges(self, edges_data, **_):
            for entry in edges_data:
                src = entry["source"]
                dst = entry["target"]
                layer = entry.get("source_type") or entry.get("type")
                tgt_layer = entry.get("target_type") or layer
                weight = entry.get("weight", 1.0)
                self.edges.append((src, dst, layer, weight))
                self.nodes.add((src, layer))
                self.nodes.add((dst, tgt_layer))
            return self

        def basic_stats(self):
            print(f"Fake stats: {len(self.nodes)} nodes, {len(self.edges)} edges")

        def get_edges(self, data=False, multiplex_edges=None):
            if data:
                data_edges = []
                for src, dst, layer, weight in self.edges:
                    data_edges.append(((src, layer), (dst, layer), {"weight": weight}))
                return data_edges
            return list(self.edges)

    def multi_layer_network(directed=False, network_type="multilayer", **_):
        net = FakeNetwork(name=network_type)
        networks.append(net)
        return net

    def random_multiplex_ER(n_nodes, n_layers, probability, directed=False):
        net = FakeNetwork(name="multiplex")
        edges = [
            {"source": 0, "target": 1, "source_type": "L0", "target_type": "L0"},
            {"source": 0, "target": 1, "source_type": "L1", "target_type": "L1"},
            {"source": 2, "target": 3, "source_type": "L1", "target_type": "L1"},
            {"source": 4, "target": 2, "source_type": "L0", "target_type": "L0"},
        ]
        net.add_edges(edges)
        random_networks.append((n_nodes, n_layers, probability, directed))
        return net

    class FakeGraph:
        def __init__(self, matrix):
            self.matrix = matrix

        def number_of_nodes(self):
            return self.matrix.shape[0]

        def number_of_edges(self):
            return self.matrix.nnz

    def _nonzero_items(matrix):
        if hasattr(matrix, "iter_nonzero"):
            for (src, dst), value in matrix.iter_nonzero():
                yield src, dst, value
        elif hasattr(matrix, "nonzero"):
            rows, cols = matrix.nonzero()
            for src, dst in zip(rows, cols):
                yield src, dst, matrix[src, dst]

    def from_scipy_sparse_array(matrix, create_using=None):
        networkx_calls.append(("from_scipy_sparse_array", matrix, create_using))
        return FakeGraph(matrix)

    def degree_centrality(graph):
        n = graph.number_of_nodes()
        degrees = {node: 0.0 for node in range(n)}
        for src, dst, value in _nonzero_items(graph.matrix):
            degrees[src] += value
            degrees[dst] += value
        if n <= 1:
            return degrees
        scale = 1 / (n - 1)
        return {node: deg * scale for node, deg in degrees.items()}

    networkx_mod = types.ModuleType("networkx")
    networkx_mod.Graph = FakeGraph
    networkx_mod.from_scipy_sparse_array = from_scipy_sparse_array
    networkx_mod.degree_centrality = degree_centrality

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = multi_layer_network

    random_generators_mod = types.ModuleType("py3plex.core.random_generators")
    random_generators_mod.random_multiplex_ER = random_multiplex_ER

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod
    core_mod.random_generators = random_generators_mod

    aggregation_mod = types.ModuleType("py3plex.multinet.aggregation")
    aggregation_mod.aggregate_layers = aggregate_layers

    multinet_pkg = types.ModuleType("py3plex.multinet")
    multinet_pkg.aggregation = aggregation_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.multinet = multinet_pkg

    monkeypatch.setitem(sys.modules, "networkx", networkx_mod)
    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.random_generators", random_generators_mod)
    monkeypatch.setitem(sys.modules, "py3plex.multinet", multinet_pkg)
    monkeypatch.setitem(sys.modules, "py3plex.multinet.aggregation", aggregation_mod)

    monkeypatch.setattr(np.random, "rand", lambda n: np.linspace(0.1, 0.4, num=n))

    return aggregator_calls, networks, random_networks, networkx_calls


def _load_module_with_unique_name():
    module_name = (
        "example_multilayer_vectorized_aggregation_"
        f"{next(_MODULE_COUNTER)}"
    )
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_vectorized_example_runs_and_aggregates(monkeypatch, capsys):
    aggregator_calls, networks, random_networks, networkx_calls = _install_vectorized_stubs(
        monkeypatch
    )
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    assert "Vectorized Aggregation with multi_layer_network Object" in out
    assert "Extracted 6 edges from network" in out
    assert "Testing different reducer modes" in out
    assert "Top 5 nodes by degree centrality" in out

    assert len(networks) == 1
    assert random_networks == [(500, 4, 0.01, False)]
    assert len(aggregator_calls) == 5

    first_result = aggregator_calls[0]["result"]
    assert aggregator_calls[0]["reducer"] == "sum"
    assert first_result[0, 1] == pytest.approx(3.0)
    assert first_result.nnz == 4  # four unique directed pairs in the small network

    # Reducer variations share the weighted edges; (0,1) appears twice
    sum_result = aggregator_calls[2]["result"]
    mean_result = aggregator_calls[3]["result"]
    max_result = aggregator_calls[4]["result"]
    assert sum_result[0, 1] == pytest.approx(1.5)  # 0.5 + 1.0 from deterministic rand
    assert mean_result[0, 1] == pytest.approx(0.75)
    assert max_result[0, 1] == pytest.approx(1.0)

    assert any(call[0] == "from_scipy_sparse_array" for call in networkx_calls)

