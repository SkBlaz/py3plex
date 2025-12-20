import pytest

from benchmarks import benchmark_time as bench


def test_py3plex_visualization_runs_pipeline(monkeypatch):
    time_calls = iter([10.0, 12.5])
    monkeypatch.setattr(bench.time, "time", lambda: next(time_calls))

    draw_default_calls = []
    draw_edge_calls = []
    monkeypatch.setattr(
        bench,
        "draw_multilayer_default",
        lambda graphs, **kwargs: draw_default_calls.append((graphs, kwargs)),
    )
    monkeypatch.setattr(
        bench,
        "draw_multiedges",
        lambda graphs, edges, **kwargs: draw_edge_calls.append((graphs, edges, kwargs)),
    )

    plot_calls = {"show": 0, "clf": 0}
    monkeypatch.setattr(bench.plt, "show", lambda: plot_calls.__setitem__("show", plot_calls["show"] + 1))
    monkeypatch.setattr(bench.plt, "clf", lambda: plot_calls.__setitem__("clf", plot_calls["clf"] + 1))

    class DummyMultilayer:
        def __init__(self):
            self.load_args = None

        def load_network(self, network, directed, input_type):
            self.load_args = (network, directed, input_type)
            return self

        def get_layers(self):
            return (
                ["layer1", "layer2"],
                {"layer1": "g1", "layer2": "g2"},
                {"typeA": [("a", "b")], "typeB": [("c", "d")]},
            )

    created = {}

    def fake_multi_layer_network(verbose=False):
        created["network"] = DummyMultilayer()
        return created["network"]

    monkeypatch.setattr(bench.multinet, "multi_layer_network", fake_multi_layer_network)

    elapsed = bench.py3plex_visualization(network=[("x", "y")])

    assert created["network"].load_args == ([("x", "y")], False, "multiedge_tuple_list")
    assert draw_default_calls == [
        ({"layer1": "g1", "layer2": "g2"}, {"display": False, "background_shape": "circle", "labels": ["layer1", "layer2"], "layout_algorithm": "force", "verbose": False})
    ]
    assert draw_edge_calls == [
        ({"layer1": "g1", "layer2": "g2"}, [("a", "b")], {"alphachannel": 0.2, "linepoints": "-.", "linecolor": "black", "curve_height": 5, "linmod": "upper", "linewidth": 0.4}),
        ({"layer1": "g1", "layer2": "g2"}, [("c", "d")], {"alphachannel": 0.2, "linepoints": "-.", "linecolor": "black", "curve_height": 5, "linmod": "upper", "linewidth": 0.4}),
    ]
    assert plot_calls == {"show": 1, "clf": 1}
    assert elapsed == pytest.approx(2.5)


def test_pymnet_visualization_calls_draw_and_returns_elapsed(monkeypatch):
    time_calls = iter([5.0, 6.2])
    monkeypatch.setattr(bench.time, "time", lambda: next(time_calls))

    draw_calls = []
    monkeypatch.setattr(bench, "draw", lambda network: draw_calls.append(network))

    plot_calls = {"show": 0, "clf": 0}
    monkeypatch.setattr(bench.plt, "show", lambda: plot_calls.__setitem__("show", plot_calls["show"] + 1))
    monkeypatch.setattr(bench.plt, "clf", lambda: plot_calls.__setitem__("clf", plot_calls["clf"] + 1))

    network = object()
    elapsed = bench.pymnet_visualization(network)

    assert draw_calls == [network]
    assert plot_calls == {"show": 1, "clf": 1}
    assert elapsed == pytest.approx(1.2)


def test_main_guard_raises_when_models_missing(monkeypatch):
    import builtins
    import runpy
    import sys

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "py3plex.visualization.multilayer_models":
            raise ImportError("models missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "benchmarks.benchmark_time", raising=False)

    with pytest.raises(ImportError, match="Visualization multilayer models are not available"):
        runpy.run_module("benchmarks.benchmark_time", run_name="__main__")


def test_main_path_runs_with_stubbed_models_and_writes_csv(monkeypatch):
    import runpy
    import sys
    import types

    calls = {
        "product": 0,
        "draw_default": 0,
        "draw_edges": 0,
        "show": 0,
        "clf": 0,
        "frames": [],
        "csv_paths": [],
    }

    # Stub matplotlib pyplot
    fake_plt = types.ModuleType("matplotlib.pyplot")
    fake_plt.show = lambda: calls.__setitem__("show", calls["show"] + 1)
    fake_plt.clf = lambda: calls.__setitem__("clf", calls["clf"] + 1)
    monkeypatch.setitem(sys.modules, "matplotlib", types.ModuleType("matplotlib"))
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_plt)

    # Stub visualization helpers
    fake_multilayer = types.ModuleType("py3plex.visualization.multilayer")
    fake_multilayer.draw_multilayer_default = lambda *a, **k: calls.__setitem__(
        "draw_default", calls["draw_default"] + 1
    )
    fake_multilayer.draw_multiedges = lambda *a, **k: calls.__setitem__("draw_edges", calls["draw_edges"] + 1)
    monkeypatch.setitem(sys.modules, "py3plex", types.ModuleType("py3plex"))
    sys.modules["py3plex"].__path__ = []
    monkeypatch.setitem(sys.modules, "py3plex.visualization", types.ModuleType("py3plex.visualization"))
    sys.modules["py3plex.visualization"].__path__ = []
    monkeypatch.setitem(sys.modules, "py3plex.visualization.multilayer", fake_multilayer)

    # Stub multilayer models to avoid ImportError in __main__
    fake_models = types.ModuleType("py3plex.visualization.multilayer_models")
    fake_models.er_multilayer = lambda N, L, p: types.SimpleNamespace(edges=(N, L, p))
    monkeypatch.setitem(sys.modules, "py3plex.visualization.multilayer_models", fake_models)

    # Stub core network loader
    class DummyNetwork:
        def __init__(self):
            self.load_args = []

        def load_network(self, network, directed, input_type):
            self.load_args.append((network, directed, input_type))
            return self

        def get_layers(self):
            return (["L1"], {"L1": "G1"}, {"etype": [("u", "v")]})

    fake_multinet_mod = types.ModuleType("py3plex.core.multinet")
    fake_multinet_mod.multi_layer_network = lambda verbose=False: DummyNetwork()
    fake_core = types.ModuleType("py3plex.core")
    fake_core.__path__ = []
    fake_core.multinet = fake_multinet_mod
    monkeypatch.setitem(sys.modules, "py3plex.core", fake_core)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", fake_multinet_mod)

    # Stub color defaults
    fake_colors = types.ModuleType("py3plex.visualization.colors")
    fake_colors.colors_default = ["red"]
    monkeypatch.setitem(sys.modules, "py3plex.visualization.colors", fake_colors)

    # Deterministic time
    fake_time_mod = types.ModuleType("time")
    fake_time_mod.time = iter([10.0, 10.5, 20.0, 20.5]).__next__
    monkeypatch.setitem(sys.modules, "time", fake_time_mod)

    # Stub numpy and itertools to keep combinations small
    fake_numpy = types.ModuleType("numpy")

    FakeRange = type("FakeRange", (list,), {"tolist": lambda self: list(self)})

    def fake_arange(*a, **k):
        return FakeRange([1])

    fake_numpy.arange = fake_arange
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)

    import itertools as real_itertools

    def fake_product(*args, **kwargs):
        calls["product"] += 1
        return [("N1", "E1", "P1"), ("N2", "E2", "P2")]

    monkeypatch.setattr(real_itertools, "product", fake_product)

    # Stub pandas DataFrame to capture datapoints and csv output
    fake_pandas = types.ModuleType("pandas")

    class DummyDataFrame:
        def __init__(self, data):
            calls["frames"].append(data)

        def to_csv(self, path):
            calls["csv_paths"].append(path)

    fake_pandas.DataFrame = DummyDataFrame
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)

    # Execute the module as a script
    monkeypatch.delitem(sys.modules, "benchmarks.benchmark_time", raising=False)
    runpy.run_module("benchmarks.benchmark_time", run_name="__main__")

    # Two combinations produced, one datapoint per combination
    assert calls["frames"] and len(calls["frames"][0]) == 2
    assert calls["csv_paths"] == ["example_benchmark2.csv"]
    # Visualization helpers and matplotlib were invoked for each combination
    assert calls["draw_default"] == 2
    assert calls["draw_edges"] == 2
    assert calls["show"] == 2
    assert calls["clf"] == 2
