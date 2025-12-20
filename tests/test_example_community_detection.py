import argparse
import importlib.util
import itertools
import os
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "_downloads"
    / "cb086ae4f46049a24c87f137770512cc"
    / "example_community_detection.py"
)
_MODULE_COUNTER = itertools.count()


def load_module():
    """Load a fresh instance of the example module for isolation."""
    module_name = f"example_community_detection_test_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module():
    return load_module()


def test_load_network_invokes_sparse_conversion_and_stats(monkeypatch, capsys):
    module = load_module()

    class FakeNetwork:
        def __init__(self):
            self.loaded_args = None
            self.converted = False
            self.stats_called = False

        def load_network(self, input_file, directed, input_type):
            self.loaded_args = (input_file, directed, input_type)
            return self

        def sparse_to_px(self):
            self.converted = True

        def basic_stats(self):
            self.stats_called = True

    fake = FakeNetwork()
    monkeypatch.setattr(module, "multinet", type("M", (), {"multi_layer_network": lambda: fake}))

    returned = module.load_network("path/to/file", "sparse")

    out = capsys.readouterr().out
    assert returned is fake
    assert fake.loaded_args == ("path/to/file", False, "sparse")
    assert fake.converted is True
    assert fake.stats_called is True
    assert "Converting sparse matrix to px format" in out


def test_load_network_skips_sparse_conversion_when_not_sparse(monkeypatch):
    module = load_module()

    class FakeNetwork:
        def __init__(self):
            self.converted = False

        def load_network(self, *args, **kwargs):
            return self

        def sparse_to_px(self):
            self.converted = True

        def basic_stats(self):
            pass

    fake = FakeNetwork()
    monkeypatch.setattr(module, "multinet", type("M", (), {"multi_layer_network": lambda: fake}))

    returned = module.load_network("ignored", "csv")

    assert returned is fake
    assert fake.converted is False


def test_visualize_partition_skips_when_plot_path_disabled(monkeypatch, capsys):
    module = load_module()
    network = type("N", (), {"get_nodes": lambda self: [], "core_network": None})()

    def _should_not_run(*args, **kwargs):
        raise AssertionError("hairball_plot should be skipped when plot_path is 'none'")

    monkeypatch.setattr(module, "hairball_plot", _should_not_run)
    monkeypatch.setattr(module, "plt", object())
    monkeypatch.setattr(module, "matplotlib", object())

    module.visualize_partition(network, {}, iterations=5, plot_path="none", title="title")

    out = capsys.readouterr().out
    assert "Visualization disabled" in out


def test_visualize_partition_calls_hairball_and_saves(monkeypatch, tmp_path):
    module = load_module()

    class FakeNetwork:
        def __init__(self):
            self.core_network = "core"

        def get_nodes(self):
            return [("n1", "l1"), ("n2", "l1"), ("n3", "l2")]

    calls = {}

    def fake_hairball(core, color_list, layout_parameters, scale_by_size, layout_algorithm, legend):
        calls["hairball"] = {
            "core": core,
            "color_list": color_list,
            "layout_parameters": layout_parameters,
            "scale_by_size": scale_by_size,
            "layout_algorithm": layout_algorithm,
            "legend": legend,
        }

    class FakePlt:
        def __init__(self):
            self.titles = []
            self.saved = []
            self.closed = 0

        def title(self, text):
            self.titles.append(text)

        def savefig(self, path, bbox_inches=None):
            path = Path(path)
            path.write_text("plot")
            self.saved.append((path, bbox_inches))

        def close(self):
            self.closed += 1

    fake_network = FakeNetwork()
    plot_path = tmp_path / "out.png"
    monkeypatch.setattr(module, "hairball_plot", fake_hairball)
    monkeypatch.setattr(module, "plt", FakePlt())
    monkeypatch.setattr(module, "matplotlib", object())
    monkeypatch.setattr(module, "colors_default", ["red", "green", "blue", "black"])

    partition = {("n1", "l1"): 1, ("n2", "l1"): 2, ("n3", "l2"): 1}
    module.visualize_partition(
        fake_network,
        partition,
        iterations=7,
        plot_path=str(plot_path),
        title="Louvain communities",
    )

    assert calls["hairball"]["core"] == "core"
    assert calls["hairball"]["color_list"] == ["red", "green", "red"]
    assert calls["hairball"]["layout_parameters"] == {"iterations": 7}
    assert calls["hairball"]["scale_by_size"] is True
    assert calls["hairball"]["layout_algorithm"] == "force"
    assert calls["hairball"]["legend"] is False

    assert module.plt.titles == ["Louvain communities"]
    assert module.plt.saved == [(plot_path, "tight")]
    assert module.plt.closed == 1
    assert plot_path.exists()


def test_run_louvain_returns_partition_and_reports_counts(monkeypatch, capsys):
    module = load_module()
    fake_partition = {("n1", "l1"): 1, ("n2", "l1"): 1, ("n3", "l2"): 2}
    fake_cw = type("CW", (), {"louvain_communities": lambda self, network: fake_partition})()
    monkeypatch.setattr(module, "cw", fake_cw)

    returned = module.run_louvain(network="network")

    out = capsys.readouterr().out
    assert returned == fake_partition
    assert "Total communities found: 2" in out
    assert "Largest community: 2 nodes" in out
    assert "Smallest community: 1 nodes" in out


def test_try_infomap_handles_missing_binary(monkeypatch, capsys):
    module = load_module()

    def _raise_missing(*args, **kwargs):
        raise FileNotFoundError("missing binary")

    fake_cw = type("CW", (), {"infomap_communities": _raise_missing})()
    monkeypatch.setattr(module, "cw", fake_cw)
    monkeypatch.setattr(module, "visualize_partition", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    module.try_infomap(network="net", binary_path="/nope", iterations=5, seed=1, plot_path="skip.png")
    out = capsys.readouterr().out
    assert "Infomap binary not found" in out
    assert "Using Louvain results from above instead." in out


def test_try_infomap_success_invokes_visualization(monkeypatch):
    module = load_module()
    fake_partition = {("n1", "l1"): 1}
    called = {}

    def fake_infomap(self, network, binary, multiplex, verbose, seed):
        called["infomap_args"] = {
            "network": network,
            "binary": binary,
            "multiplex": multiplex,
            "verbose": verbose,
            "seed": seed,
        }
        return fake_partition

    def fake_visualize(network, partition, iterations, plot_path, title):
        called["visualize"] = {
            "network": network,
            "partition": partition,
            "iterations": iterations,
            "plot_path": plot_path,
            "title": title,
        }

    fake_cw = type("CW", (), {"infomap_communities": fake_infomap})()
    monkeypatch.setattr(module, "cw", fake_cw)
    monkeypatch.setattr(module, "visualize_partition", fake_visualize)

    module.try_infomap(network="net", binary_path="/bin/infomap", iterations=3, seed=7, plot_path="out.png")

    assert called["infomap_args"] == {
        "network": "net",
        "binary": "/bin/infomap",
        "multiplex": False,
        "verbose": True,
        "seed": 7,
    }
    assert called["visualize"] == {
        "network": "net",
        "partition": fake_partition,
        "iterations": 3,
        "plot_path": "out.png",
        "title": "Infomap communities",
    }


def test_maybe_save_edgelist_writes_file(monkeypatch, tmp_path):
    module = load_module()

    class FakeNetwork:
        def __init__(self, base):
            self.base = base
            self.saved = None

        def serialize_to_edgelist(self, edgelist_file):
            path = Path(self.base) / edgelist_file
            path.write_text("edges")
            self.saved = path

    monkeypatch.chdir(tmp_path)
    fake = FakeNetwork(tmp_path)

    module.maybe_save_edgelist(fake)

    expected = tmp_path / "tmp_network.txt"
    assert fake.saved == expected
    assert expected.exists()
    assert expected.read_text() == "edges"


def test_main_handles_import_error(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "IMPORT_ERROR", ImportError("boom"))

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert "Error importing dependencies" in out


def test_main_aborts_when_input_missing(monkeypatch, capsys):
    module = load_module()
    args = argparse.Namespace(
        input_network="missing.mat",
        input_type="sparse",
        iterations=10,
        seed=1,
        plot_path="plot.png",
        infomap_binary="infomap",
        infomap_plot_path="infomap.png",
        skip_infomap=False,
        save_edgelist=False,
    )
    monkeypatch.setattr(module, "IMPORT_ERROR", None)
    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module.os.path, "exists", lambda path: False)
    monkeypatch.setattr(module, "load_network", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError))

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert "Input file: missing.mat" in out
    assert "Input file 'missing.mat' not found" in out


def test_main_runs_happy_path_and_skips_infomap(monkeypatch, capsys):
    module = load_module()
    args = argparse.Namespace(
        input_network="present.mat",
        input_type="sparse",
        iterations=3,
        seed=123,
        plot_path="plot.png",
        infomap_binary="infomap",
        infomap_plot_path="infomap_plot.png",
        skip_infomap=True,
        save_edgelist=False,
    )
    calls = {"load": 0, "louvain": 0, "visualize": 0, "infomap": 0, "save": 0}

    monkeypatch.setattr(module, "IMPORT_ERROR", None)
    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module.os.path, "exists", lambda path: True)
    monkeypatch.setattr(module, "load_network", lambda *a, **k: calls.__setitem__("load", calls["load"] + 1) or "net")
    monkeypatch.setattr(module, "run_louvain", lambda net: calls.__setitem__("louvain", calls["louvain"] + 1) or {"n": 1})
    monkeypatch.setattr(
        module,
        "visualize_partition",
        lambda net, part, iterations, plot_path, title: calls.__setitem__("visualize", calls["visualize"] + 1),
    )
    monkeypatch.setattr(
        module,
        "try_infomap",
        lambda *a, **k: calls.__setitem__("infomap", calls["infomap"] + 1),
    )
    monkeypatch.setattr(module, "maybe_save_edgelist", lambda net: calls.__setitem__("save", calls["save"] + 1))

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert calls == {"load": 1, "louvain": 1, "visualize": 1, "infomap": 0, "save": 0}
    assert "Infomap step skipped by user request" in out
    assert "COMMUNITY DETECTION COMPLETE" in out
