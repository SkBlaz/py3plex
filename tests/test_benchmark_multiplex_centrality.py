import os

import pytest

from benchmarks import benchmark_multiplex_centrality as bench


def test_estimate_network_params_clamps_probability_range():
    n_small, p_small = bench.estimate_network_params(1, n_layers=2)
    n_large, p_large = bench.estimate_network_params(10**9, n_layers=2)

    assert n_small > 0
    assert 0.01 <= p_small <= 0.95
    assert 0.01 <= p_large <= 0.95
    assert n_large > 0


def test_build_multiplex_network_delegates_to_random_er(monkeypatch):
    calls = {}

    def fake_random(n_nodes, n_layers, edge_prob, directed):
        calls["args"] = (n_nodes, n_layers, edge_prob, directed)
        return "dummy-network"

    monkeypatch.setattr(bench.random_generators, "random_multilayer_ER", fake_random)

    result = bench.build_multiplex_network(5, 3, 0.2)

    assert result == "dummy-network"
    assert calls["args"] == (5, 3, 0.2, False)


def test_compute_centralities_invokes_all_measures(monkeypatch):
    class DummyCentrality:
        last_instance = None

        def __init__(self, network):
            self.network = network
            self.calls = []
            DummyCentrality.last_instance = self

        def layer_degree_centrality(self, weighted):
            self.calls.append(("degree", weighted))
            return {"degree": 1}

        def overlapping_degree_centrality(self, weighted):
            self.calls.append(("overlapping", weighted))
            return {"overlapping": 2}

        def participation_coefficient(self, weighted):
            self.calls.append(("participation", weighted))
            return {"participation": 3}

        def pagerank_centrality(self, damping):
            self.calls.append(("pagerank", damping))
            return {"pagerank": 4}

        def multilayer_closeness_centrality(self):
            self.calls.append(("closeness", None))
            return {"closeness": 5}

    monkeypatch.setattr(bench, "MultilayerCentrality", DummyCentrality)
    sentinel_network = object()

    result = bench.compute_centralities(sentinel_network)

    assert result == {
        "degree": {"degree": 1},
        "overlapping_degree": {"overlapping": 2},
        "participation": {"participation": 3},
        "pagerank": {"pagerank": 4},
        "closeness": {"closeness": 5},
    }
    assert DummyCentrality.last_instance.network is sentinel_network
    assert DummyCentrality.last_instance.calls == [
        ("degree", False),
        ("overlapping", False),
        ("participation", False),
        ("pagerank", 0.85),
        ("closeness", None),
    ]


def test_get_rss_memory_mb_prefers_resource(monkeypatch):
    import sys as real_sys

    class DummyResource:
        RUSAGE_SELF = 0

        @staticmethod
        def getrusage(which):
            return type("R", (), {"ru_maxrss": 2048})  # kilobytes

    # Make sure psutil is not consulted if resource works
    monkeypatch.setitem(real_sys.modules, "resource", DummyResource)
    monkeypatch.setitem(real_sys.modules, "psutil", None)

    assert bench.get_rss_memory_mb() == pytest.approx(2.0)


def test_get_rss_memory_mb_falls_back_to_psutil(monkeypatch):
    import sys as real_sys

    class DummyPsutil:
        class Process:
            def __init__(self, pid):
                self.pid = pid

            @staticmethod
            def memory_info():
                return type("Mem", (), {"rss": 3 * 1024 * 1024})  # bytes

    # resource import succeeds but lacks getrusage → AttributeError path
    class ResourceWithoutGetrusage:
        RUSAGE_SELF = 0

    monkeypatch.setitem(real_sys.modules, "resource", ResourceWithoutGetrusage)
    monkeypatch.setitem(real_sys.modules, "psutil", DummyPsutil)

    assert bench.get_rss_memory_mb() == pytest.approx(3.0)


def test_get_rss_memory_mb_returns_negative_when_unavailable(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"resource", "psutil"}:
            raise ImportError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert bench.get_rss_memory_mb() == -1.0


def test_serialize_network_invokes_save(monkeypatch, tmp_path):
    calls = {}

    class DummyNetwork:
        def save_network(self, *, output_file, output_type):
            calls["params"] = (output_file, output_type)

    path = tmp_path / "network.edgelist"
    bench.serialize_network(DummyNetwork(), str(path))

    assert calls["params"] == (str(path), "edgelist")


def test_run_benchmark_records_timings_and_memory(monkeypatch):
    perf_calls = iter([0.0, 1.0, 1.0, 2.0, 2.0, 3.5])
    mem_calls = iter([50.0, 70.0, 55.0, 52.0])
    path_holder = {}
    collected = {"gc_called": 0}

    class DummyNetwork:
        def get_edges(self):
            return [(0, 1), (1, 2)]

    def fake_collect():
        collected["gc_called"] += 1

    def fake_estimate(target_edges, n_layers):
        return 4, 0.2

    def fake_build(n_nodes, n_layers, edge_prob):
        return DummyNetwork()

    def fake_centralities(network):
        return {"centrality": {"node": 1.0}}

    def fake_serialize(network, filepath):
        path_holder["path"] = filepath

    monkeypatch.setattr(bench.time, "perf_counter", lambda: next(perf_calls))
    monkeypatch.setattr(bench, "get_rss_memory_mb", lambda: next(mem_calls))
    monkeypatch.setattr(bench.gc, "collect", fake_collect)
    monkeypatch.setattr(bench, "estimate_network_params", fake_estimate)
    monkeypatch.setattr(bench, "build_multiplex_network", fake_build)
    monkeypatch.setattr(bench, "compute_centralities", fake_centralities)
    monkeypatch.setattr(bench, "serialize_network", fake_serialize)

    result = bench.run_benchmark(target_edges=7, n_layers=3)

    assert collected["gc_called"] == 1
    assert result.n_edges == 7
    assert result.n_nodes == 4
    assert result.n_layers == 3
    assert result.construction_time == pytest.approx(1.0)
    assert result.centrality_time == pytest.approx(1.0)
    assert result.serialization_time == pytest.approx(1.5)
    assert result.memory_before_mb == 50.0
    assert result.memory_peak_mb == 70.0
    assert result.memory_after_mb == 52.0
    assert not os.path.exists(path_holder["path"])


def test_print_results_table_formats_rows(capsys):
    first = bench.BenchmarkResult(100)
    first.n_nodes = 10
    first.n_layers = 2
    first.construction_time = 0.1
    first.centrality_time = 0.2
    first.serialization_time = 0.05
    first.memory_peak_mb = 12.0

    second = bench.BenchmarkResult(200)
    second.n_nodes = 20
    second.n_layers = 4
    second.construction_time = 0.2
    second.centrality_time = 0.4
    second.serialization_time = 0.1
    second.memory_peak_mb = 18.0

    bench.print_results_table([first, second])
    captured = capsys.readouterr().out

    assert "BENCHMARK RESULTS" in captured
    assert "100" in captured and "200" in captured
    assert "Peak memory: 18.0" in captured
    assert "TIME BREAKDOWN (N=200" in captured


def test_main_returns_nonzero_when_all_benchmarks_fail(monkeypatch, capsys):
    def fake_run_benchmark(target_edges, n_layers):
        raise RuntimeError("boom")

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    monkeypatch.setattr(bench, "print_results_table", lambda results: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(bench, "print_flamegraph_instructions", lambda: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(bench, "print_optimization_suggestions", lambda: (_ for _ in ()).throw(AssertionError))

    exit_code = bench.main()
    output = capsys.readouterr().out

    assert "No successful benchmarks" in output
    assert exit_code == 1


def test_main_success_path_calls_helpers(monkeypatch):
    calls = {"run": [], "table": 0, "flame": 0, "opt": 0}

    def fake_run_benchmark(target_edges, n_layers):
        calls["run"].append((target_edges, n_layers))
        result = bench.BenchmarkResult(target_edges)
        result.n_layers = n_layers
        return result

    monkeypatch.setattr(bench, "run_benchmark", fake_run_benchmark)
    monkeypatch.setattr(bench, "print_results_table", lambda results: calls.__setitem__("table", calls["table"] + 1))
    monkeypatch.setattr(
        bench,
        "print_flamegraph_instructions",
        lambda: calls.__setitem__("flame", calls["flame"] + 1),
    )
    monkeypatch.setattr(
        bench,
        "print_optimization_suggestions",
        lambda: calls.__setitem__("opt", calls["opt"] + 1),
    )

    exit_code = bench.main()

    assert exit_code == 0
    assert calls["run"] == [(1000, 4), (10000, 4), (100000, 4)]
    assert calls["table"] == 1
    assert calls["flame"] == 1
    assert calls["opt"] == 1
