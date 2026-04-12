"""Unit tests for sensitivity executor helper logic."""

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def sensitivity_modules(monkeypatch):
    """Load sensitivity modules without importing top-level py3plex package."""
    repo_root = Path(__file__).resolve().parents[1]
    py3plex_root = repo_root / "py3plex"
    sensitivity_root = py3plex_root / "sensitivity"

    py3plex_pkg = ModuleType("py3plex")
    py3plex_pkg.__path__ = [str(py3plex_root)]
    sensitivity_pkg = ModuleType("py3plex.sensitivity")
    sensitivity_pkg.__path__ = [str(sensitivity_root)]

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_pkg)
    monkeypatch.setitem(sys.modules, "py3plex.sensitivity", sensitivity_pkg)
    for module_name in [
        "py3plex.sensitivity.types",
        "py3plex.sensitivity.perturbations",
        "py3plex.sensitivity.metrics",
        "py3plex.sensitivity.executor",
    ]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    metrics = importlib.import_module("py3plex.sensitivity.metrics")
    executor = importlib.import_module("py3plex.sensitivity.executor")
    return executor, metrics


def test_extract_conclusion_data_with_uncertainty_wrapped_values(sensitivity_modules):
    sensitivity_executor, _ = sensitivity_modules
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


def test_extract_conclusion_data_uses_to_dict_when_available(sensitivity_modules):
    sensitivity_executor, _ = sensitivity_modules
    query_result_obj = SimpleNamespace(
        to_dict=lambda: {"data": [{"id": "x"}, {"id": "y"}]}
    )
    extracted = sensitivity_executor._extract_conclusion_data(query_result_obj)
    assert extracted["ranking"] == ["x", "y"]


def test_compute_stability_metric_dispatch_and_unknown_metric(sensitivity_modules):
    sensitivity_executor, _ = sensitivity_modules
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


def test_find_collapse_point_found_and_not_found(sensitivity_modules):
    sensitivity_executor, _ = sensitivity_modules
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


def test_compute_local_influence_per_node_has_descending_scores(sensitivity_modules):
    sensitivity_executor, _ = sensitivity_modules
    baseline = {"ranking": ["n1", "n2", "n3"]}
    influence = sensitivity_executor._compute_local_influence(
        baseline_data=baseline,
        stability_curves={},
        scope="per_node",
    )

    # Influence in current implementation is 1 / (rank + 1):
    # rank 0 -> 1.0, rank 1 -> 0.5, rank 2 -> 1/3.
    scores = [x.influence_score for x in influence["node"]]
    assert scores == pytest.approx([1.0, 0.5, 1.0 / 3.0])
    assert [x.entity_id for x in influence["node"]] == ["n1", "n2", "n3"]


def test_run_sensitivity_analysis_with_monkeypatched_perturbation(
    monkeypatch, sensitivity_modules
):
    sensitivity_executor, _ = sensitivity_modules
    # Keep perturbation behavior deterministic and lightweight.
    monkeypatch.setattr(
        sensitivity_executor,
        "apply_perturbation",
        lambda network, method, strength, seed=None, **kwargs: network,
    )

    def query_executor(_network):
        return {"data": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]}

    dummy_network = SimpleNamespace(kind="unused_in_monkeypatched_test")
    result = sensitivity_executor.run_sensitivity_analysis(
        network=dummy_network,
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


def test_run_sensitivity_analysis_detects_instability(sensitivity_modules, monkeypatch):
    sensitivity_executor, _ = sensitivity_modules

    def fake_apply_perturbation(network, method, strength, seed=None, **kwargs):
        return {"strength": strength}

    monkeypatch.setattr(
        sensitivity_executor, "apply_perturbation", fake_apply_perturbation
    )

    baseline_ranking = ["n1", "n2", "n3"]
    perturbed_ranking = ["n3", "n2", "n1"]

    def query_executor(network_obj):
        strength = network_obj.get("strength", 0.0) if isinstance(network_obj, dict) else 0.0
        ranking = baseline_ranking if strength == 0.0 else perturbed_ranking
        return {"data": [{"id": node_id} for node_id in ranking]}

    result = sensitivity_executor.run_sensitivity_analysis(
        network=SimpleNamespace(kind="baseline"),
        query_executor=query_executor,
        query_ast={"dummy": True},
        perturb="edge_drop",
        grid=[0.0, 0.3],
        n_samples=1,
        seed=11,
        metrics=["kendall_tau"],
    )

    assert result.curves["kendall_tau"].values[0] == pytest.approx(1.0)
    assert result.curves["kendall_tau"].values[1] < 1.0


def test_parse_metric_spec_variants(sensitivity_modules):
    _, sensitivity_metrics = sensitivity_modules
    parse_metric_spec = sensitivity_metrics.parse_metric_spec
    assert parse_metric_spec("jaccard_at_k(20)") == ("jaccard_at_k", {"k": 20})
    assert parse_metric_spec(" kendall_tau ") == ("kendall_tau", {})
    assert parse_metric_spec("jaccard_at_k(not_an_int)") == ("jaccard_at_k", {})
