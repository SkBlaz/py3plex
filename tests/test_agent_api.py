"""Regression tests for stable machine-facing agent API."""

import json
from pathlib import Path

from py3plex.agent import (
    load_network_from_path,
    top_hubs_by_layer,
    uncertainty_centrality,
    summarize_result,
    compare_networks,
    reproducible_export_bundle,
    community_detection_with_uq,
    temporal_slice,
)
from py3plex.core import multinet
from py3plex.dsl import Q


def _build_small_network():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "A", "type": "work"},
            {"source": "B", "type": "work"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "A",
                "target": "B",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    return net


def test_top_hubs_by_layer_structured_contract():
    net = _build_small_network()
    payload = top_hubs_by_layer(net, top_k=1, measure="degree", seed=42)
    assert payload["status"] == "ok"
    assert set(payload.keys()) == {
        "status",
        "assumptions",
        "warnings",
        "result",
        "provenance",
        "replay",
        "export_paths",
    }
    assert payload["replay"]["is_replayable"] is True
    assert payload["result"]["summary"]["target"] == "nodes"


def test_load_network_from_path_contract(tmp_path):
    net = _build_small_network()
    edge_path = tmp_path / "net.edgelist"
    net.save_network(str(edge_path), output_type="edgelist")

    payload = load_network_from_path(str(edge_path), input_type="edgelist")
    assert payload["status"] == "ok"
    assert "network" in payload["result"]
    assert payload["result"]["network_stats"]["layer_count"] >= 1


def test_uncertainty_centrality_deterministic_with_seed():
    net = _build_small_network()
    p1 = uncertainty_centrality(net, measures=["degree"], n_samples=10, seed=7)
    p2 = uncertainty_centrality(net, measures=["degree"], n_samples=10, seed=7)
    assert p1["result"]["summary"] == p2["result"]["summary"]
    assert p1["result"]["attributes"]["degree"] == p2["result"]["attributes"]["degree"]


def test_summarize_result_machine_payload():
    net = _build_small_network()
    result = Q.nodes().compute("degree").execute(net)
    payload = summarize_result(result)
    assert payload["status"] == "ok"
    assert payload["result"]["target"] == "nodes"
    assert "provenance" in payload


def test_compare_networks_contract():
    net_a = _build_small_network()
    net_b = _build_small_network()
    payload = compare_networks(net_a, net_b, measure="degree")
    assert payload["status"] == "ok"
    assert payload["result"]["metric"] == "degree"
    assert payload["result"]["delta"] == 0.0


def test_query_builder_validate_and_machine_plan():
    q = Q.nodes().compute("degree").order_by("degree")
    v = q.validate()
    assert v["target"] == "nodes"
    assert "computed_measures" in v
    assert "warnings" in v

    plan = q.explain_plan_json()
    assert plan["machine"] is True
    assert "validation" in plan
    assert "planner" in plan


def test_query_builder_validate_missing_metric():
    q = Q.nodes().order_by("pagerank")
    v = q.validate()
    assert v["status"] == "needs_attention"
    codes = [m["code"] for m in v["missing_prerequisites"]]
    assert "missing_metric" in codes


def test_top_k_explicit_helpers():
    q1 = Q.nodes().top_k_global(3, "degree")
    q2 = Q.nodes().top_k_per_layer(3, "degree")
    q3 = Q.nodes().top_k_across_layers(3, "degree", coverage_mode="at_least", coverage_k=2)
    assert q1._select.limit == 3
    assert q1._select.group_by == []
    assert q2._select.group_by == ["layer"]
    assert q3._select.group_by == ["layer"]
    assert q3._select.coverage_mode == "at_least"
    assert q3._select.coverage_k == 2


def test_query_result_summary_and_inspect_json_and_counts():
    net = _build_small_network()
    result = Q.nodes().compute("degree").execute(net)
    summary = result.summary_dict()
    assert summary["target"] == "nodes"
    assert summary["replica_count"] == len(result.items)
    assert summary["physical_count"] == 2
    as_json = result.inspect_json()
    parsed = json.loads(as_json)
    assert parsed["target"] == "nodes"
    assert set(result.physical_nodes()) == {"A", "B"}
    assert len(result.replica_nodes()) == len(result.items)


def test_compute_degree_kind_survives_ast():
    q = Q.nodes().compute("degree", kind="intra")
    assert q.to_ast().select.compute[0].kind == "intra"


def test_structured_warning_catalog_and_builder():
    from py3plex.dsl.warnings import STRUCTURED_WARNING_CATALOG, build_structured_warning

    assert "expensive_centrality" in STRUCTURED_WARNING_CATALOG
    w = build_structured_warning("expensive_centrality")
    assert w["code"] == "expensive_centrality"
    assert "autofixable" in w


def test_explain_plan_chainable_flag():
    q = Q.nodes().compute("degree").explain_plan()
    assert hasattr(q, "_explain_plan_flag")
    assert q._explain_plan_flag is True


def test_reproducible_export_bundle_contract(tmp_path):
    net = _build_small_network()
    result = Q.nodes().provenance(mode="replayable", seed=11).compute("degree").execute(net)
    out = tmp_path / "bundle.json.gz"
    payload = reproducible_export_bundle(result, path=str(out), compress=True)
    assert payload["status"] == "ok"
    assert str(out) in payload["export_paths"]
    assert Path(str(out)).exists()


def test_temporal_slice_requires_valid_mode():
    net = _build_small_network()
    try:
        temporal_slice(net)
    except ValueError as exc:
        assert "either 'at' or both 't_start' and 't_end'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing temporal parameters.")


def test_temporal_slice_at_mode_with_mock(monkeypatch):
    net = _build_small_network()
    captured = {}

    class _DummyResult:
        meta = {"warnings": [], "provenance": {}}
        provenance = {}
        is_replayable = False

        def canonical_export_dict(self):
            return {"summary": {"target": "edges"}}

    def _fake_execute(self, network, *args, **kwargs):
        captured["network"] = network
        return _DummyResult()

    monkeypatch.setattr(type(Q.edges()), "execute", _fake_execute, raising=False)
    payload = temporal_slice(net, at=1.5)
    assert payload["status"] == "ok"
    assert payload["result"]["summary"]["target"] == "edges"
    assert captured["network"] is net


def test_temporal_slice_during_mode_with_mock(monkeypatch):
    net = _build_small_network()

    class _DummyResult:
        meta = {"warnings": [], "provenance": {}}
        provenance = {}
        is_replayable = False

        def canonical_export_dict(self):
            return {"summary": {"target": "edges"}}

    def _fake_execute(self, network, *args, **kwargs):
        return _DummyResult()

    monkeypatch.setattr(type(Q.edges()), "execute", _fake_execute, raising=False)
    payload = temporal_slice(net, t_start=0.0, t_end=2.0)
    assert payload["status"] == "ok"
    assert payload["result"]["summary"]["target"] == "edges"


def test_community_detection_with_uq_with_mock(monkeypatch):
    net = _build_small_network()

    class _DummyResult:
        meta = {"warnings": [], "provenance": {}}
        provenance = {}
        is_replayable = False

        def canonical_export_dict(self):
            return {"summary": {"target": "nodes"}}

    def _fake_execute(self, network, *args, **kwargs):
        return _DummyResult()

    monkeypatch.setattr(type(Q.nodes()), "execute", _fake_execute, raising=False)
    payload = community_detection_with_uq(net, method="leiden", n_samples=5, seed=3)
    assert payload["status"] == "ok"
    assert payload["result"]["summary"]["target"] == "nodes"
