"""Smoke tests for the MDL metric benchmark (mdl_benchmark.py).

This exercises the benchmark machinery itself (partition generation,
scoring, and the ranking/scaling reports) on tiny graphs. It deliberately
does not assert that mdl_score ranks ground truth best: that property now
holds in practice on the default LFR sweep (see
`MDL_BENCHMARK_RESULTS.md` at the repo root, generated after the
resolution-limit fix in `_block_parameter_cost` closed the gap that used to
let maximally-fragmented, near-clique partitions beat the true generative
one), but it is an empirical property of a specific benchmark
configuration, not a mathematical guarantee mdl_score gives for every
graph/partition -- so it does not belong in a fast, tiny-graph smoke test
as a hard assertion.
"""

import warnings

import pytest

from py3plex.algorithms.community_detection.mdl_benchmark import (
    PartitionScore,
    ranking_agreement_report,
    run_benchmark,
    scaling_report,
)


@pytest.fixture
def small_records():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_benchmark(
            mu_values=(0.05, 0.3),
            ns=(60,),
            layers=("L1", "L2"),
            avg_degree=6.0,
            min_community=10,
            seeds=(1, 2),
        )


def test_run_benchmark_produces_all_partition_types(small_records):
    n_groups = len({(r.mu, r.n_nodes, r.seed) for r in small_records})
    assert n_groups == 4  # 2 mu values x 2 seeds

    types_per_group = {}
    for r in small_records:
        types_per_group.setdefault((r.mu, r.n_nodes, r.seed), set()).add(
            r.partition_type
        )
    for types in types_per_group.values():
        assert types == {"ground_truth", "corrupted", "louvain"}


def test_scores_are_finite(small_records):
    for r in small_records:
        assert isinstance(r, PartitionScore)
        assert r.mdl >= 0.0
        assert -1.0 <= r.modularity <= 1.0
        assert r.mdl_time_s >= 0.0
        assert r.modularity_time_s >= 0.0
        assert r.rc_time_s >= 0.0


def test_ranking_agreement_report_shape(small_records):
    report = ranking_agreement_report(small_records)
    assert 0.0 <= report["ground_truth_best_rate"] <= 1.0
    assert set(report["mean_spearman_by_mu"].keys()) == {0.05, 0.3}
    for d in report["disagreements"]:
        assert {"mu", "n_nodes", "seed", "mdl_best", "modularity_best", "scores"} <= d.keys()


def test_scaling_report_has_all_metrics(small_records):
    report = scaling_report(small_records)
    assert len(report) >= 1
    for metrics in report.values():
        assert set(metrics.keys()) == {
            "mdl_score",
            "multilayer_modularity",
            "replica_consistency",
        }
        for v in metrics.values():
            assert v >= 0.0
