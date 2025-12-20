import importlib.util
import itertools
import sys
import types
from pathlib import Path

import networkx as nx


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_incidence_gadget_encoding.py"
_MODULE_COUNTER = itertools.count()


def _install_stubs(monkeypatch):
    """Install lightweight sympy/py3plex stand-ins so the example can run deterministically."""
    networks = []

    def primerange(start, stop=None):
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        if stop is None:
            stop = start
            start = 0
        return (p for p in primes if start <= p < stop)

    sympy_mod = types.ModuleType("sympy")
    sympy_mod.primerange = primerange

    class FakeNetwork:
        def __init__(self, directed=True):
            self.directed = directed
            self.nodes = set()
            self.edges = []
            networks.append(self)

        def add_nodes(self, nodes, input_type=None):
            for entry in nodes:
                self.nodes.add((entry["source"], entry["type"]))

        def add_edges(self, edges, input_type=None):
            for edge in edges:
                u = (edge["source"], edge["source_type"])
                v = (edge["target"], edge["target_type"])
                self.edges.append((u, v))
                self.nodes.update([u, v])

        def get_nodes(self):
            return list(self.nodes)

        def get_edges(self):
            return list(self.edges)

        def to_homogeneous_hypergraph(self):
            H = nx.Graph()
            node_mapping = {}
            layer_signatures = {}

            for idx, (node, layer) in enumerate(sorted(self.nodes)):
                mapped = f"v_{node}_{layer}"
                node_mapping[(node, layer)] = mapped
                H.add_node(mapped)
                if layer not in layer_signatures:
                    sig = f"{layer}_sig"
                    layer_signatures[layer] = sig
                    H.add_node(sig)
                H.add_edge(mapped, layer_signatures[layer])

            edge_info = {}
            for idx, ((u, u_layer), (v, v_layer)) in enumerate(self.edges):
                edge_node = f"e_{idx}"
                H.add_node(edge_node)

                for mapped in (node_mapping[(u, u_layer)], node_mapping[(v, v_layer)]):
                    H.add_edge(edge_node, mapped)
                H.add_edge(node_mapping[(u, u_layer)], node_mapping[(v, v_layer)])
                H.add_edge(edge_node, layer_signatures[u_layer])

                edge_info[edge_node] = (u_layer, (u, v))

            self._last_H = H
            self._last_node_mapping = node_mapping
            self._last_edge_info = edge_info
            return H, node_mapping, edge_info

        def from_homogeneous_hypergraph(self, _graph):
            recovered = {}
            for layer, endpoints in self._last_edge_info.values():
                recovered.setdefault(layer, []).append(endpoints)
            self._last_recovered = recovered
            return recovered

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = lambda directed=True: FakeNetwork(directed=directed)

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod

    monkeypatch.setitem(sys.modules, "sympy", sympy_mod)
    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)

    return networks


def _load_module_with_unique_name():
    module_name = f"example_incidence_gadget_encoding_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_basic_encoding_roundtrip(monkeypatch, capsys):
    networks = _install_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.example_basic_encoding()
    out = capsys.readouterr().out

    network = networks[-1]
    assert "BASIC INCIDENCE GADGET ENCODING EXAMPLE" in out
    assert "Nodes: 7" in out
    assert "Edges: 4" in out
    assert f"Nodes: {len(network._last_H.nodes())}" in out
    assert f"Edges: {len(network._last_H.edges())}" in out

    assert sum(len(edges) for edges in network._last_recovered.values()) == len(
        network.edges
    )


def test_social_network_components(monkeypatch, capsys):
    networks = _install_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.example_social_network()
    out = capsys.readouterr().out

    network = networks[-1]
    expected_components = nx.number_connected_components(network._last_H)
    assert f"Connected components: {expected_components}" in out
    assert expected_components == 3

    recovered_edges = sum(len(v) for v in network._last_recovered.values())
    assert recovered_edges == len(network.edges)


def test_cycle_detection_reports_prime_cycles(monkeypatch, capsys):
    networks = _install_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.example_cycle_detection()
    out = capsys.readouterr().out

    network = networks[-1]
    cycles = nx.cycle_basis(network._last_H)
    cycle_lengths = sorted(len(c) for c in cycles)
    assert cycle_lengths and all(length in {2, 3, 5, 7, 11} for length in cycle_lengths)

    for edge_node in network._last_edge_info:
        assert f"{edge_node} (layer" in out


def test_network_properties_counts(monkeypatch, capsys):
    networks = _install_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.example_network_properties()
    out = capsys.readouterr().out

    network = networks[-1]
    H = network._last_H
    vertex_nodes = [n for n in H.nodes() if str(n).startswith("v_")]
    edge_nodes = [n for n in H.nodes() if str(n).startswith("e_")]
    signature_nodes = [
        n
        for n in H.nodes()
        if not str(n).startswith("v_") and not str(n).startswith("e_")
    ]

    assert len(vertex_nodes) == 12  # 6 nodes per layer, 2 layers
    assert len(edge_nodes) == 12
    assert len(signature_nodes) == 2
    assert f"Nodes: {len(H.nodes())}" in out
    assert f"Edges: {len(H.edges())}" in out
