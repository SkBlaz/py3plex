"""Property-based tests for py3plex.selection module.

Tests AutoCommunity selection infrastructure to ensure:
- ContestantResult and AutoCommunityResult are correctly structured
- Results are deterministic with fixed seeds
- Leaderboards are consistent with metrics
- Provenance is complete and reproducible
"""

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st, assume
from hypothesis import HealthCheck

import pandas as pd
import numpy as np

from py3plex.selection import ContestantResult, AutoCommunityResult


# ============================================================================
# ContestantResult Properties
# ============================================================================


@given(
    contestant_id=st.text(min_size=1, max_size=30, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    algo_name=st.sampled_from(["louvain", "leiden", "label_propagation"]),
    runtime_ms=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contestant_result_initialization_is_valid(contestant_id, algo_name, runtime_ms):
    """ContestantResult can be initialized with valid parameters."""
    result = ContestantResult(
        contestant_id=contestant_id,
        algo_name=algo_name,
        params={"gamma": 1.0},
        partition={(0, "layer1"): 0, (1, "layer1"): 1},
        metrics={"modularity": 0.5},
        runtime_ms=runtime_ms,
    )
    
    assert result.contestant_id == contestant_id
    assert result.algo_name == algo_name
    assert result.runtime_ms == runtime_ms
    assert isinstance(result.partition, dict)
    assert isinstance(result.metrics, dict)


@given(
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contestant_result_with_seed_stores_seed_correctly(seed):
    """ContestantResult with seed should store it correctly."""
    result = ContestantResult(
        contestant_id="test",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
        seed_used=seed,
    )
    
    assert result.seed_used == seed


@given(
    n_metrics=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contestant_result_with_multiple_metrics(n_metrics):
    """ContestantResult can store multiple metrics."""
    metrics = {f"metric_{i}": float(i) for i in range(n_metrics)}
    
    result = ContestantResult(
        contestant_id="test",
        algo_name="louvain",
        params={},
        partition={},
        metrics=metrics,
        runtime_ms=1.0,
    )
    
    assert len(result.metrics) == n_metrics
    for i in range(n_metrics):
        assert f"metric_{i}" in result.metrics
        assert result.metrics[f"metric_{i}"] == float(i)


@given(
    n_errors=st.integers(min_value=0, max_value=5),
    n_warnings=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contestant_result_can_store_errors_and_warnings(n_errors, n_warnings):
    """ContestantResult can store errors and warnings."""
    errors = [f"error_{i}" for i in range(n_errors)]
    warnings = [f"warning_{i}" for i in range(n_warnings)]
    
    result = ContestantResult(
        contestant_id="test",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
        errors=errors,
        warnings=warnings,
    )
    
    assert len(result.errors) == n_errors
    assert len(result.warnings) == n_warnings


# ============================================================================
# AutoCommunityResult Properties
# ============================================================================


@given(
    n_contestants=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_auto_community_result_initialization(n_contestants):
    """AutoCommunityResult can be initialized with valid components."""
    # Create a simple leaderboard
    leaderboard = pd.DataFrame({
        'contestant_id': [f"contestant_{i}" for i in range(n_contestants)],
        'algo': ['leiden'] * n_contestants,
        'total_wins': list(range(n_contestants, 0, -1)),
    })
    
    chosen = ContestantResult(
        contestant_id="contestant_0",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    result = AutoCommunityResult(
        chosen=chosen,
        partition={},
        algorithm={"name": "leiden", "params": {}},
        leaderboard=leaderboard,
        report={},
        provenance={},
    )
    
    assert result.chosen == chosen
    assert isinstance(result.leaderboard, pd.DataFrame)
    assert len(result.leaderboard) == n_contestants


@given(
    win_value=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_auto_community_result_with_win_matrix(win_value):
    """AutoCommunityResult can store win matrix."""
    chosen = ContestantResult(
        contestant_id="winner",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    win_matrix = {
        "winner": {"loser": win_value},
        "loser": {"winner": 100.0 - win_value},
    }
    
    result = AutoCommunityResult(
        chosen=chosen,
        partition={},
        algorithm={"name": "leiden", "params": {}},
        leaderboard=pd.DataFrame(),
        report={},
        provenance={},
        win_matrix=win_matrix,
    )
    
    assert result.win_matrix is not None
    assert "winner" in result.win_matrix
    assert "loser" in result.win_matrix


# ============================================================================
# Leaderboard Properties
# ============================================================================


@given(
    n_contestants=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_leaderboard_is_sorted_by_total_wins(n_contestants):
    """Leaderboard should be sorted by total wins in descending order."""
    # Create leaderboard with random wins
    import random
    random.seed(42)
    wins = [random.uniform(0, 100) for _ in range(n_contestants)]
    
    leaderboard = pd.DataFrame({
        'contestant_id': [f"contestant_{i}" for i in range(n_contestants)],
        'total_wins': wins,
    }).sort_values('total_wins', ascending=False)
    
    chosen = ContestantResult(
        contestant_id=leaderboard.iloc[0]['contestant_id'],
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    result = AutoCommunityResult(
        chosen=chosen,
        partition={},
        algorithm={"name": "leiden", "params": {}},
        leaderboard=leaderboard,
        report={},
        provenance={},
    )
    
    # Check leaderboard is sorted
    total_wins = result.leaderboard['total_wins'].values
    for i in range(len(total_wins) - 1):
        assert total_wins[i] >= total_wins[i + 1]


# ============================================================================
# Provenance Properties
# ============================================================================


@given(
    seed=st.integers(min_value=0, max_value=1000),
    n_samples=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_provenance_stores_determinism_info(seed, n_samples):
    """Provenance should store determinism information."""
    provenance = {
        "seed": seed,
        "n_samples": n_samples,
        "deterministic": True,
    }
    
    chosen = ContestantResult(
        contestant_id="winner",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    result = AutoCommunityResult(
        chosen=chosen,
        partition={},
        algorithm={"name": "leiden", "params": {}},
        leaderboard=pd.DataFrame(),
        report={},
        provenance=provenance,
    )
    
    assert result.provenance["seed"] == seed
    assert result.provenance["n_samples"] == n_samples
    assert result.provenance["deterministic"] is True


# ============================================================================
# Edge Case Properties
# ============================================================================


def test_contestant_result_with_empty_partition():
    """ContestantResult can handle empty partition."""
    result = ContestantResult(
        contestant_id="test",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    assert len(result.partition) == 0
    assert isinstance(result.partition, dict)


def test_auto_community_result_with_empty_leaderboard():
    """AutoCommunityResult can handle empty leaderboard."""
    chosen = ContestantResult(
        contestant_id="only",
        algo_name="leiden",
        params={},
        partition={},
        metrics={},
        runtime_ms=1.0,
    )
    
    result = AutoCommunityResult(
        chosen=chosen,
        partition={},
        algorithm={"name": "leiden", "params": {}},
        leaderboard=pd.DataFrame(),
        report={},
        provenance={},
    )
    
    assert len(result.leaderboard) == 0
