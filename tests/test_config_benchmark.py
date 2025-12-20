import random
import sys
import types

import pytest

from benchmarks import config_benchmark as bench


def test_benchmark_network_creation_uses_networkx_and_multinet(monkeypatch):
    time_calls = iter([1.0, 4.5])
    monkeypatch.setattr(bench.time, "time", lambda: next(time_calls))

    erdos_calls = []

    class GraphFake:
        def __init__(self, n):
            self._n = n

        def number_of_nodes(self):
            return self._n

        def number_of_edges(self):
            return self._n - 1

    def fake_erdos(nodes, prob, seed=None):
        erdos_calls.append((nodes, prob, seed))
        return GraphFake(nodes)

    monkeypatch.setattr(bench.nx, "erdos_renyi_graph", fake_erdos)

    class DummyMultiLayer:
        def __init__(self):
            self.layers = []

        def add_layer(self, graph, layer_id):
            self.layers.append((graph, layer_id))

        def get_number_of_nodes(self):
            return sum(graph.number_of_nodes() for graph, _ in self.layers)

        def get_number_of_edges(self):
            return sum(graph.number_of_edges() for graph, _ in self.layers)

    created = {}

    def fake_multi_layer_network(network_type=None):
        created["network_type"] = network_type
        created["network"] = DummyMultiLayer()
        return created["network"]

    monkeypatch.setattr(bench.multinet, "multi_layer_network", fake_multi_layer_network)

    result = bench.benchmark_network_creation(num_layers=2, nodes_per_layer=4)

    assert created["network_type"] == "multiplex"
    assert len(created["network"].layers) == 2
    assert erdos_calls == [(4, 0.1, bench.config.RANDOM_SEED), (4, 0.1, bench.config.RANDOM_SEED)]
    assert result["creation_time"] == pytest.approx(3.5)
    assert result["num_nodes"] == 8  # 4 per layer
    assert result["num_edges"] == 6  # (4-1) per layer


def test_demonstrate_config_usage_prints_expected_settings(monkeypatch, capsys):
    monkeypatch.setattr(bench.config, "DEFAULT_NODE_SIZE", 1.5)
    monkeypatch.setattr(bench.config, "DEFAULT_EDGE_ALPHA", 0.25)
    monkeypatch.setattr(bench.config, "DEFAULT_COLOR_PALETTE", "alpha")
    monkeypatch.setattr(bench.config, "RANDOM_SEED", 123)
    monkeypatch.setattr(bench.config, "__api_version__", "2024.01")

    palettes = {"alpha": ["a1", "a2"], "colorblind_safe": ["cb1", "cb2", "cb3"]}
    monkeypatch.setattr(bench.config, "COLOR_PALETTES", palettes)

    def fake_palette(name=None):
        key = name or "alpha"
        return [f"{key}-c1", f"{key}-c2", f"{key}-c3"]

    monkeypatch.setattr(bench.config, "get_color_palette", fake_palette)

    bench.demonstrate_config_usage()
    out = capsys.readouterr().out

    assert "Configuration Module Demonstration" in out
    assert "Default node size: 1.5" in out
    assert "Default edge alpha: 0.25" in out
    assert "Default color palette: alpha" in out
    assert "Random seed: 123" in out
    assert "API version: 2024.01" in out
    assert "alpha" in out and "colorblind_safe" in out
    assert "alpha-c1" in out
    assert "colorblind_safe-c1" in out


def test_demonstrate_reproducibility_reports_success(monkeypatch, capsys):
    def fake_rng(seed):
        return random.Random(seed)

    monkeypatch.setattr(bench, "get_rng", fake_rng)

    bench.demonstrate_reproducibility()
    out = capsys.readouterr().out

    assert "Reproducibility Demonstration" in out
    assert "SUCCESS: Results are reproducible!" in out
    lines = [line.strip() for line in out.splitlines() if "Random values" in line]
    assert len(lines) == 2
    assert lines[0].split(":")[1].strip() == lines[1].split(":")[1].strip()


def test_demonstrate_reproducibility_reports_error(monkeypatch, capsys):
    sequences = [[0.1, 0.2, 0.3, 0.4, 0.5], [0.9, 0.8, 0.7, 0.6, 0.5]]

    class SeqRNG:
        def __init__(self, seq):
            self._it = iter(seq)

        def random(self):
            return next(self._it)

    def fake_rng(seed):
        return SeqRNG(sequences.pop(0))

    monkeypatch.setattr(bench, "get_rng", fake_rng)

    bench.demonstrate_reproducibility()
    out = capsys.readouterr().out

    assert "Reproducibility Demonstration" in out
    assert "ERROR: Results differ (unexpected)" in out
    lines = [line.strip() for line in out.splitlines() if "Random values" in line]
    assert len(lines) == 2
    assert lines[0].split(":")[1].strip() != lines[1].split(":")[1].strip()


def test_run_benchmarks_handles_success_and_error(monkeypatch, capsys):
    calls = []

    def fake_benchmark(num_layers, nodes_per_layer):
        calls.append((num_layers, nodes_per_layer))
        if num_layers == 5:
            raise ValueError("boom")
        return {"creation_time": 0.5, "num_nodes": 10, "num_edges": 20}

    monkeypatch.setattr(bench, "benchmark_network_creation", fake_benchmark)

    bench.run_benchmarks()
    out = capsys.readouterr().out

    assert calls == [(3, 50), (5, 100), (10, 100)]
    assert "Creation time: 0.500s" in out
    assert "ERROR: Error: boom" in out


def test_main_orchestrates_steps(monkeypatch, capsys):
    calls = []

    def record(name):
        def _inner():
            calls.append(name)
        return _inner

    monkeypatch.setattr(bench, "demonstrate_config_usage", record("config"))
    monkeypatch.setattr(bench, "demonstrate_reproducibility", record("repro"))
    monkeypatch.setattr(bench, "run_benchmarks", record("bench"))

    fake_py3plex = types.ModuleType("py3plex")
    fake_py3plex.__version__ = "9.9.9"
    fake_py3plex.__api_version__ = "1.2.3"
    monkeypatch.setitem(sys.modules, "py3plex", fake_py3plex)

    bench.main()
    out = capsys.readouterr().out

    assert calls == ["config", "repro", "bench"]
    assert "py3plex version: 9.9.9" in out
    assert "API version: 1.2.3" in out
    assert "SUCCESS: Benchmark complete!" in out


def test_import_guard_exits_when_py3plex_missing(monkeypatch, capsys):
    import builtins
    import runpy

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("py3plex"):
            raise ImportError("missing py3plex")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "benchmarks.config_benchmark", raising=False)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("benchmarks.config_benchmark", run_name="__main__")

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "ERROR: Import failed: missing py3plex" in output
    assert "Make sure py3plex is installed" in output
