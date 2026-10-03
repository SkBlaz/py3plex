"""Unsupported AutoCommunity modes must not abort other benchmark runs."""

import pytest

from py3plex.benchmarks.runners import AutoCommunityRunner
from py3plex.core import multinet
from py3plex.dsl import B
from py3plex.exceptions import AlgorithmError


@pytest.fixture
def network():
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        {"source": u, "target": v, "source_type": "L", "target_type": "L"}
        for u, v in [("A", "B"), ("B", "C"), ("C", "A")]
    ])
    return net


@pytest.mark.parametrize("seed", [0, 42])
@pytest.mark.parametrize("candidate_set", ["core", ["louvain"]])
@pytest.mark.parametrize("fast", [False, True])
def test_wins_runner_raises_actionable_algorithm_error(network, seed, candidate_set, fast):
    with pytest.raises(AlgorithmError, match="mode='wins'") as caught:
        AutoCommunityRunner().run(
            network, seed=seed, mode="wins", candidate_set=candidate_set, fast=fast
        )
    assert "mode='pareto'" in str(caught.value)
    assert "auto_select_community" in str(caught.value)


@pytest.mark.parametrize("seed", [0, 42])
@pytest.mark.parametrize("repeats", [1, 2])
def test_wins_failure_is_recorded_and_louvain_still_runs(network, seed, repeats):
    with pytest.warns(UserWarning, match="Algorithm autocommunity failed"):
        result = (
            B.community().on(network)
            .algorithms(("autocommunity", {"mode": "wins"}), "louvain")
            .metrics("modularity").repeat(repeats, seed=seed).execute()
        )
    assert result.target == "communities"
    assert result.count == 2 * repeats
    frame = result.to_pandas()
    failed = frame[frame["algorithm"] == "autocommunity"]
    successful = frame[frame["algorithm"] == "louvain"]
    assert len(failed) == len(successful) == repeats
    assert failed["error"].str.contains("mode='wins'", regex=False).all()
    assert failed["modularity"].isna().all()
    assert successful["error"].isna().all()
    assert successful["modularity"].notna().all()


@pytest.mark.parametrize("explicit_mode", [False, True])
def test_pareto_runner_remains_executable(network, explicit_mode):
    params = {"mode": "pareto"} if explicit_mode else {}
    result = AutoCommunityRunner().run(
        network, seed=42, candidate_set=["louvain"], **params
    )
    assert set(result.partition) == set(network.core_network.nodes())
    assert result.params["mode"] == "pareto"
    assert result.trace


@pytest.mark.parametrize("seed", [0, 42])
def test_benchmark_wins_selection_keeps_pareto_adapter_mode(network, seed):
    result = (
        B.community().on(network)
        .algorithms(("autocommunity", {"candidate_set": ["louvain"]}))
        .metrics("modularity").repeat(1, seed=seed).select("wins").execute()
    )
    assert result.count == 1
    frame = result.to_pandas()
    assert frame["algorithm"].tolist() == ["autocommunity"]
    assert frame["modularity"].notna().all()
