"""Targeted tests for py3plex.algorithms.meta_flow_report."""

import builtins
import importlib
import pytest

from py3plex.algorithms.meta_flow_report import MetaFlowReport


def test_compute_centralities_delegates_and_passes_flags(monkeypatch):
    """compute_centralities should call compute_all_centralities with provided flags."""
    centrality_module = importlib.import_module(
        "py3plex.algorithms.multilayer_algorithms.centrality"
    )
    calls = {}

    def fake_compute(network, include_path_based, include_advanced, wf_improved):
        calls["network"] = network
        calls["include_path_based"] = include_path_based
        calls["include_advanced"] = include_advanced
        calls["wf_improved"] = wf_improved
        return {"dummy": {"node": 1.0}}

    monkeypatch.setattr(centrality_module, "compute_all_centralities", fake_compute)

    sentinel_network = object()
    report = MetaFlowReport(sentinel_network)
    result = report.compute_centralities(
        include_path_based=True, include_advanced=True, wf_improved=False
    )

    assert result == {"dummy": {"node": 1.0}}
    assert calls == {
        "network": sentinel_network,
        "include_path_based": True,
        "include_advanced": True,
        "wf_improved": False,
    }


def test_compute_centralities_missing_dependency_warns(monkeypatch):
    """ImportError when loading centrality module should return empty result and warn."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "py3plex.algorithms.multilayer_algorithms.centrality":
            raise ImportError("missing centrality backend")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    report = MetaFlowReport(object())

    with pytest.warns(UserWarning, match="Could not compute centralities"):
        result = report.compute_centralities()

    assert result == {}


def test_detect_communities_uses_available_methods(monkeypatch):
    """detect_communities should collect outputs from both louvain and leiden stubs."""
    modularity_module = importlib.import_module(
        "py3plex.algorithms.community_detection.multilayer_modularity"
    )
    leiden_module = importlib.import_module(
        "py3plex.algorithms.community_detection.leiden_multilayer"
    )
    calls = {}

    def fake_louvain(network, gamma, omega):
        calls["louvain"] = (gamma, omega)
        return {"node": 0}

    class FakeLeidenResult:
        def __init__(self):
            self.communities = {"node": 1}
            self.modularity = 0.5

    def fake_leiden(network, gamma, omega):
        calls["leiden"] = (gamma, omega)
        return FakeLeidenResult()

    monkeypatch.setattr(modularity_module, "louvain_multilayer", fake_louvain)
    monkeypatch.setattr(leiden_module, "leiden_multilayer", fake_leiden)

    report = MetaFlowReport(object())
    result = report.detect_communities(gamma=2.0, omega=0.3)

    assert result["louvain"] == {"node": 0}
    assert result["leiden"] == {"communities": {"node": 1}, "modularity": 0.5}
    assert calls["louvain"] == (2.0, 0.3)
    assert calls["leiden"] == (2.0, 0.3)


def test_detect_communities_handles_errors(monkeypatch):
    """Exceptions in community detection should be converted to warnings."""
    modularity_module = importlib.import_module(
        "py3plex.algorithms.community_detection.multilayer_modularity"
    )

    def failing_louvain(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(modularity_module, "louvain_multilayer", failing_louvain)

    report = MetaFlowReport(object())
    with pytest.warns(UserWarning, match="Error running louvain"):
        result = report.detect_communities(methods=["louvain"])

    assert result == {}


def test_compute_statistics_collects_all_metrics(monkeypatch):
    """compute_statistics should aggregate basic and advanced metrics."""
    mls = importlib.import_module("py3plex.algorithms.statistics.multilayer_statistics")

    monkeypatch.setattr(mls, "layer_density", lambda _n, layer: {"L1": 0.1, "L2": 0.2}[layer])
    monkeypatch.setattr(mls, "node_activity", lambda _n, node: len(node))
    monkeypatch.setattr(mls, "inter_layer_coupling_strength", lambda *_args: 0.3)
    monkeypatch.setattr(mls, "edge_overlap", lambda *_args: 0.4)
    monkeypatch.setattr(mls, "versatility_centrality", lambda *_args, **_kwargs: {"A": 0.5})
    monkeypatch.setattr(mls, "multilayer_clustering_coefficient", lambda *_args: 0.6)

    class FakeNetwork:
        def get_nodes(self):
            return [("A", "L1"), ("B", "L2"), ("C", "L1")]

    report = MetaFlowReport(FakeNetwork())
    stats = report.compute_statistics(include_advanced=True)

    assert stats["layer_densities"]["L1"] == 0.1
    assert stats["layer_densities"]["L2"] == 0.2
    coupling_key = next(iter(stats["inter_layer_coupling"]))
    overlap_key = next(iter(stats["edge_overlap"]))
    assert set(coupling_key.split("-")) == {"L1", "L2"}
    assert set(overlap_key.split("-")) == {"L1", "L2"}
    assert stats["inter_layer_coupling"][coupling_key] == 0.3
    assert stats["edge_overlap"][overlap_key] == 0.4
    assert stats["versatility_centrality"] == {"A": 0.5}
    assert stats["multilayer_clustering"] == 0.6
    assert stats["node_activities"]["A"] == 1


def test_get_top_nodes_respects_measure_and_category():
    """get_top_nodes should return a sorted subset for requested measure."""
    report = MetaFlowReport(object())
    report._results = {
        "centralities": {"score": {"b": 2.0, "a": 3.0, "c": 1.0}},
        "statistics": {"other": {"x": 5}},
    }

    assert report.get_top_nodes("score", n=2) == [("a", 3.0), ("b", 2.0)]
    assert report.get_top_nodes("missing") == []
    assert report.get_top_nodes("score", category="statistics") == []
