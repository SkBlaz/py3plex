"""Unit tests for sensitivity executor helper logic."""

from types import SimpleNamespace

import pytest

from py3plex.sensitivity import executor as sensitivity_executor
from py3plex.sensitivity.metrics import parse_metric_spec


def test_extract_conclusion_data_with_uncertainty_wrapped_values():
    query_result = {
        "data": [
            {"id": "n1", "layer": "L1", "degree": {"mean": 3.5}, "community_id": 1},
            {"id": "n2", "layer": "L1", "degree": 2.0, "community": 2},
        ]
    }

    extracted = sensitivity_executor._extract_conclusion_data(query_result)

    assert extracted["ranking"] == ["n1", "n2"]
    assert extracted["partition"] == {"n1": 1, "n2": 2}
    assert extracted["values"]["degree"] == {"n1": 3.5, "n2": 2.0}
    assert extracted["raw"] is query_result


def test_extract_conclusion_data_uses_to_dict_when_available():
    query_result_obj = SimpleNamespace(
        to_dict=lambda: {"data": [{"id": "x"}, {"id": "y"}]}
    )
    extracted = sensitivity_executor._extract_conclusion_data(query_result_obj)
    assert extracted["ranking"] == ["x", "y"]


def test_compute_stability_metric_dispatch_and_unknown_metric():
    baseline = {
        "ranking": ["a", "b", "c"],
        "partition": {"a": 0, "b": 0, "c": 1},
    }
    perturbed = {
        "ranking": ["a", "c", "b"],
        "partition": {"a": 0, "b": 1, "c": 1},
    }

    j = sensitivity_executor._compute_stability_metric(
        "jaccard_at_k", baseline, perturbed, k=2
    )
    t = sensitivity_executor._compute_stability_metric("kendall_tau", baseline, perturbed)
    vi = sensitivity_executor._compute_stability_metric(
        "variation_of_information", baseline, perturbed
    )
    unknown = sensitivity_executor._compute_stability_metric(
        "does_not_exist", baseline, perturbed
    )

    assert 0.0 <= j <= 1.0
    assert -1.0 <= t <= 1.0
    assert vi >= 0.0
    assert unknown == 0.0


def test_find_collapse_point_found_and_not_found():
    assert (
        sensitivity_executor._find_collapse_point(
            values=[0.9, 0.7, 0.4], grid=[0.0, 0.1, 0.2], threshold=0.5
        )
        == 0.2
    )
    assert (
        sensitivity_executor._find_collapse_point(
            values=[0.9, 0.7, 0.6], grid=[0.0, 0.1, 0.2], threshold=0.5
        )
        is None
    )


def test_compute_local_influence_per_node_has_descending_scores():
    baseline = {"ranking": ["n1", "n2", "n3"]}
    influence = sensitivity_executor._compute_local_influence(
        baseline_data=baseline,
        stability_curves={},
        scope="per_node",
    )

    scores = [x.influence_score for x in influence["node"]]
    assert scores == [1.0, 0.5, pytest.approx(1.0 / 3.0)]
    assert [x.entity_id for x in influence["node"]] == ["n1", "n2", "n3"]


def test_run_sensitivity_analysis_with_monkeypatched_perturbation(monkeypatch):
    # Keep perturbation behavior deterministic and lightweight.
    monkeypatch.setattr(
        sensitivity_executor,
        "apply_perturbation",
        lambda network, method, strength, seed=None, **kwargs: network,
    )

    def query_executor(_network):
        return {"data": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]}

    result = sensitivity_executor.run_sensitivity_analysis(
        network=object(),
        query_executor=query_executor,
        query_ast={"dummy": True},
        perturb="edge_drop",
        grid=[0.0, 0.2],
        n_samples=2,
        seed=7,
        metrics=["kendall_tau", "jaccard_at_k(2)"],
    )

    assert result.grid == [0.0, 0.2]
    assert set(result.curves.keys()) == {"kendall_tau", "jaccard_at_k(2)"}
    # Identical baseline and perturbed rankings from monkeypatch => perfect stability.
    assert result.curves["kendall_tau"].values == [1.0, 1.0]
    assert result.curves["jaccard_at_k(2)"].values == [1.0, 1.0]
    assert result.meta["provenance"]["seed"] == 7
    assert result.meta["n_samples"] == 2


def test_parse_metric_spec_variants():
    assert parse_metric_spec("jaccard_at_k(20)") == ("jaccard_at_k", {"k": 20})
    assert parse_metric_spec(" kendall_tau ") == ("kendall_tau", {})
    assert parse_metric_spec("jaccard_at_k(not_an_int)") == ("jaccard_at_k", {})
