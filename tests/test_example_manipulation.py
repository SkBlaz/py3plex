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
    / "example_manipulation.py"
)
_MODULE_COUNTER = itertools.count()


def _install_manipulation_stubs(monkeypatch):
    networks = []
    random_calls = []
    random_networks = []

    class FakeEdge:
        def __init__(
            self,
            source,
            target,
            source_layer=None,
            target_layer=None,
            weight=None,
            relation_type=None,
            is_multiplex=False,
        ):
            self.source = source
            self.target = target
            self.source_layer = source_layer
            self.target_layer = target_layer
            self.weight = weight
            self.relation_type = relation_type
            self.is_multiplex = is_multiplex

        def key_tuple(self):
            return (
                self.source,
                self.source_layer,
                self.target,
                self.target_layer,
                self.weight,
            )

        def to_data(self):
            return {
                "source": self.source,
                "target": self.target,
                "source_type": self.source_layer,
                "target_type": self.target_layer,
                "weight": self.weight,
                "type": self.relation_type,
                "is_multiplex": self.is_multiplex,
            }

        def to_pair(self):
            return (
                self.source,
                self.source_layer,
                self.target,
                self.target_layer,
                self.weight,
            )

    class FakeNetwork:
        def __init__(self, network_type="multilayer"):
            self.network_type = network_type
            self.nodes = []
            self.edges = []
            self.monitor_log = []

        def _add_node_if_missing(self, source, layer):
            key = (source, layer)
            existing_keys = {(n["source"], n["type"]) for n in self.nodes}
            if key not in existing_keys:
                self.nodes.append({"source": source, "type": layer})

        def add_nodes(self, node_data, input_type="dict"):
            items = node_data if isinstance(node_data, list) else [node_data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                self._add_node_if_missing(item.get("source"), item.get("type"))
            return self

        def add_edges(self, edge_data, input_type="dict", **_):
            items = edge_data if isinstance(edge_data, list) else [edge_data]
            if input_type == "list":
                for entry in items:
                    source, source_layer, target, target_layer, weight = entry
                    self._add_node_if_missing(source, source_layer)
                    self._add_node_if_missing(target, target_layer)
                    self.edges.append(
                        FakeEdge(
                            source,
                            target,
                            source_layer=source_layer,
                            target_layer=target_layer,
                            weight=weight,
                            is_multiplex=self.network_type == "multiplex",
                        )
                    )
                return self

            for entry in items:
                if not isinstance(entry, dict):
                    continue
                source = entry["source"]
                target = entry["target"]
                source_layer = entry.get("source_type") or entry.get("type")
                target_layer = entry.get("target_type") or entry.get("type")
                self._add_node_if_missing(source, source_layer)
                self._add_node_if_missing(target, target_layer)
                self.edges.append(
                    FakeEdge(
                        source,
                        target,
                        source_layer=source_layer,
                        target_layer=target_layer,
                        weight=entry.get("weight"),
                        relation_type=entry.get("type"),
                        is_multiplex=self.network_type == "multiplex",
                    )
                )
            return self

        def get_nodes(self, data=False):
            if data:
                return list(self.nodes)
            return [(node["source"], node["type"]) for node in self.nodes]

        def monitor(self, obj):
            self.monitor_log.append(obj)
            print(obj)
            return obj

        def get_edges(self, data=False, multiplex_edges=None):
            edges = list(self.edges)
            if multiplex_edges is True:
                edges = [edge for edge in edges if edge.is_multiplex]
            elif multiplex_edges is False:
                edges = [edge for edge in edges if not edge.is_multiplex]
            return [edge.to_data() if data else edge.to_pair() for edge in edges]

        def subnetwork(self, subset, subset_by=None):
            new_net = FakeNetwork(network_type=self.network_type)
            subset_layers = set()
            subset_nodes = set()
            if subset_by == "layers":
                subset_layers = set(subset)
            elif subset_by == "node_names":
                subset_nodes = set(subset)
            elif subset_by == "node_layer_names":
                subset_nodes = set(subset)

            for node in self.nodes:
                node_key = (node["source"], node["type"])
                if subset_by == "layers" and node["type"] in subset_layers:
                    new_net.nodes.append(dict(node))
                elif subset_by == "node_names" and node["source"] in subset_nodes:
                    new_net.nodes.append(dict(node))
                elif subset_by == "node_layer_names" and node_key in subset_nodes:
                    new_net.nodes.append(dict(node))

            allowed_keys = {(n["source"], n["type"]) for n in new_net.nodes}
            for edge in self.edges:
                src_key = (edge.source, edge.source_layer)
                tgt_key = (edge.target, edge.target_layer)
                if src_key in allowed_keys and tgt_key in allowed_keys:
                    copied = FakeEdge(
                        edge.source,
                        edge.target,
                        source_layer=edge.source_layer,
                        target_layer=edge.target_layer,
                        weight=edge.weight,
                        relation_type=edge.relation_type,
                        is_multiplex=edge.is_multiplex,
                    )
                    new_net.edges.append(copied)
            return new_net

        def remove_edges(self, edges, input_type="dict", **_):
            items = edges if isinstance(edges, list) else [edges]
            remove_keys = set()
            if input_type == "list":
                for entry in items:
                    remove_keys.add(tuple(entry))
            else:
                for entry in items:
                    if isinstance(entry, dict):
                        remove_keys.add(
                            (
                                entry.get("source"),
                                entry.get("source_type") or entry.get("type"),
                                entry.get("target"),
                                entry.get("target_type") or entry.get("type"),
                                entry.get("weight"),
                            )
                        )
            self.edges = [
                edge for edge in self.edges if edge.key_tuple() not in remove_keys
            ]
            return self

        def remove_nodes(self, nodes, input_type="list", **_):
            items = nodes if isinstance(nodes, list) else [nodes]
            to_remove = set()
            if input_type == "dict":
                for entry in items:
                    if isinstance(entry, dict):
                        to_remove.add((entry.get("source"), entry.get("type")))
            else:
                for entry in items:
                    if isinstance(entry, tuple):
                        to_remove.add(entry)
            self.nodes = [
                node for node in self.nodes if (node["source"], node["type"]) not in to_remove
            ]
            self.edges = [
                edge
                for edge in self.edges
                if (edge.source, edge.source_layer) not in to_remove
                and (edge.target, edge.target_layer) not in to_remove
            ]
            return self

    def multi_layer_network(network_type="multilayer", **_):
        net = FakeNetwork(network_type=network_type)
        networks.append(net)
        return net

    def random_multilayer_ER(n_nodes, n_layers, probability, directed=True):
        random_calls.append((n_nodes, n_layers, probability, directed))
        net = FakeNetwork(network_type="random_er")
        random_networks.append(net)
        return net

    multinet_mod = types.ModuleType("py3plex.core.multinet")
    multinet_mod.multi_layer_network = multi_layer_network

    random_generators_mod = types.ModuleType("py3plex.core.random_generators")
    random_generators_mod.random_multilayer_ER = random_multilayer_ER

    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod
    core_mod.random_generators = random_generators_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.random_generators", random_generators_mod)

    return networks, random_calls, random_networks


def _load_module_with_unique_name():
    module_name = f"example_manipulation_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_manipulation_script_runs_and_records_operations(monkeypatch, capsys):
    networks, random_calls, random_networks = _install_manipulation_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    assert "Printing a single node." in out
    assert "Printing a single edge." in out
    assert "Random ER multilayer graph in progress" in out
    assert random_calls == [(300, 6, 0.05, False)]
    assert len(random_networks) == 1

    first_network = networks[0]
    assert len(first_network.nodes) == 7
    assert len(first_network.edges) == 5
    assert ("node1", "t1") in first_network.get_nodes()
    assert any(edge.weight == 2 and edge.source == "node1" for edge in first_network.edges)
    assert "weight': 2" in out  # printed edge data is included


def test_multiplex_subnetworks_and_removals(monkeypatch, capsys):
    networks, _, _ = _install_manipulation_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out
    multiplex_net = networks[1]

    assert multiplex_net.network_type == "multiplex"
    assert multiplex_net.monitor_log[0]  # multiplex edges were reported
    assert multiplex_net.monitor_log[1] == []  # non-coupled edges filtered out

    assert "[(1, 2), (3, 2)]" in out  # layers subset
    assert "[(2, 1)]" in out  # node_names subset
    assert "[(1, 1), (1, 2)]" in out  # node_layer_names subset

    assert len(multiplex_net.edges) == 0  # removed all edges
    assert set(multiplex_net.get_nodes()) == {(1, 2), (3, 2)}
