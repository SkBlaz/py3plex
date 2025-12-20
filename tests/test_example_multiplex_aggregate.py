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
    / "example_multiplex_aggregate.py"
)
_MODULE_COUNTER = itertools.count()


def _install_multiplex_stubs(monkeypatch):
    pipeline_runs = []
    load_calls = []
    aggregate_calls = []
    subnetwork_calls = []

    class FakeCoreGraph:
        def __init__(self, nodes, edges):
            self._nodes = nodes
            self._edges = edges

        def number_of_nodes(self):
            return self._nodes

        def number_of_edges(self):
            return self._edges

    class FakeAggregatedGraph:
        def __init__(self, nodes, edges):
            self._nodes = nodes
            self._edges = edges

        def number_of_nodes(self):
            return self._nodes

        def number_of_edges(self):
            return self._edges

    class FakeNetwork:
        def __init__(self, nodes, edges, name="multilayer"):
            self.core_network = FakeCoreGraph(nodes, edges)
            self.node_count = nodes
            self.edge_count = edges
            self.name = name

        def aggregate_edges(self, metric, normalize_by=None):
            # Differing normalizations shrink edges at different rates
            if normalize_by == "degree":
                edges = max(1, self.edge_count // 3)
            elif normalize_by == "raw":
                edges = max(1, self.edge_count // 2)
            else:
                edges = max(1, self.edge_count // 2)

            aggregate_calls.append(
                {
                    "metric": metric,
                    "normalize_by": normalize_by,
                    "source": self.name,
                    "nodes": self.node_count,
                    "edges": self.edge_count,
                }
            )
            return FakeAggregatedGraph(self.node_count, edges)

        def subnetwork(self, input_list, subset_by):
            subnetwork_calls.append((tuple(input_list), subset_by))
            # Shrink nodes/edges to simulate layer filtering
            return FakeNetwork(nodes=max(1, self.node_count // 10), edges=max(1, self.edge_count // 10))

        def basic_stats(self):
            print(f"Fake stats: {self.node_count} nodes, {self.edge_count} edges")

    class LoadStep:
        def __init__(self, generator, n, l, p):
            self.generator = generator
            self.n = n
            self.l = l
            self.p = p

        def __repr__(self):
            return f"LoadStep(generator={self.generator}, n={self.n}, l={self.l}, p={self.p})"

        def transform(self, _):
            load_calls.append((self.generator, self.n, self.l, self.p))
            nodes = self.n * self.l
            edges = max(1, int(self.n * self.l * self.p * 10))
            return FakeNetwork(nodes=nodes, edges=edges, name="load_step")

    class AggregateLayers:
        def __init__(self, method):
            self.method = method

        def __repr__(self):
            return f"AggregateLayers(method={self.method})"

        def transform(self, network):
            return network.aggregate_edges(metric=self.method)

    class ComputeStats:
        def __repr__(self):
            return "ComputeStats()"

        def transform(self, network):
            nodes = network.number_of_nodes()
            edges = network.number_of_edges()
            density = 0 if nodes <= 1 else edges / (nodes * (nodes - 1))
            return {"nodes": nodes, "edges": edges, "density": density}

    class Pipeline:
        def __init__(self, steps):
            self.steps = steps

        def __repr__(self):
            step_desc = " -> ".join(name for name, _ in self.steps)
            return f"Pipeline({step_desc})"

        def run(self):
            value = None
            for name, step in self.steps:
                value = step.transform(value)
                pipeline_runs.append(name)
            return value

    def execute_query(network, query):
        return {
            "query": query,
            "target": "nodes",
            "count": 7,
            "nodes": [(f"node{i}", "L0") for i in range(7)],
        }

    def random_multiplex_ER(nodes, layers, probability, directed=False):
        return FakeNetwork(nodes=nodes * layers, edges=250, name="random_multiplex")

    pipeline_mod = types.ModuleType("py3plex.pipeline")
    pipeline_mod.Pipeline = Pipeline
    pipeline_mod.LoadStep = LoadStep
    pipeline_mod.AggregateLayers = AggregateLayers
    pipeline_mod.ComputeStats = ComputeStats

    dsl_mod = types.ModuleType("py3plex.dsl")
    dsl_mod.execute_query = execute_query

    random_generators_mod = types.ModuleType("py3plex.core.random_generators")
    random_generators_mod.random_multiplex_ER = random_multiplex_ER

    core_mod = types.ModuleType("py3plex.core")
    core_mod.random_generators = random_generators_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.pipeline = pipeline_mod
    py3plex_mod.dsl = dsl_mod
    py3plex_mod.core = core_mod

    # networkx is imported but unused; supply a stub to avoid external dependency
    networkx_mod = types.ModuleType("networkx")

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.pipeline", pipeline_mod)
    monkeypatch.setitem(sys.modules, "py3plex.dsl", dsl_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.random_generators", random_generators_mod)
    monkeypatch.setitem(sys.modules, "networkx", networkx_mod)

    return {
        "pipeline_runs": pipeline_runs,
        "load_calls": load_calls,
        "aggregate_calls": aggregate_calls,
        "subnetwork_calls": subnetwork_calls,
    }


def _load_module_with_unique_name():
    module_name = f"example_multiplex_aggregate_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_multiplex_aggregate_example_runs(monkeypatch, capsys):
    trackers = _install_multiplex_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    # Section headers and milestones
    assert "MULTIPLEX NETWORK AGGREGATION" in out
    assert "Approach 1: Pipeline-based Aggregation" in out
    assert "Approach 2: Interoperability - Pipeline + DSL" in out
    assert "Approach 3: Direct Method Calls" in out
    assert "SUMMARY: Object Interoperability" in out

    # Pipeline section output
    assert "Pipeline structure: Pipeline(generate -> aggregate -> stats)" in out
    assert "Pipeline results:" in out
    assert "Density:" in out

    # DSL interoperability path
    assert "Generated network: 150 nodes" in out
    assert "High-degree nodes found: 7" in out
    assert "Aggregated network: 150 nodes, 60 edges" in out

    # Direct aggregation path
    assert "Nodes: 500, Layers: 8, Edge probability: 0.0005" in out
    assert "Fake stats: 4000 nodes, 250 edges" in out
    assert "[OK] Extracted 4 separate layers" in out
    assert "Aggregating with degree normalization" in out
    assert "Aggregating with raw counts" in out

    # Pipeline steps executed in order
    assert trackers["pipeline_runs"] == ["generate", "aggregate", "stats"]

    # LoadStep invocations from pipeline and DSL path
    assert trackers["load_calls"] == [
        ("random_er", 100, 4, 0.03),
        ("random_er", 50, 3, 0.08),
    ]

    # Aggregate edges called for pipeline, DSL, and two direct calls
    assert [call["metric"] for call in trackers["aggregate_calls"]] == [
        "sum",
        "sum",
        "count",
        "count",
    ]
    assert [call["normalize_by"] for call in trackers["aggregate_calls"]] == [
        None,
        None,
        "degree",
        "raw",
    ]

    # Four separate layer extraction calls
    assert trackers["subnetwork_calls"] == [
        ((1,), "layers"),
        ((2,), "layers"),
        ((3,), "layers"),
        ((4,), "layers"),
    ]
