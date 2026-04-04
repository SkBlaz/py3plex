"""Property-based tests for py3plex.multinet.aggregation."""

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from py3plex.multinet.aggregation import aggregate_layers


@st.composite
def weighted_edges(draw):
    """Generate valid weighted multilayer edge arrays."""
    n_nodes = draw(st.integers(min_value=2, max_value=30))
    n_layers = draw(st.integers(min_value=1, max_value=6))
    n_edges = draw(st.integers(min_value=1, max_value=120))

    rows = []
    for _ in range(n_edges):
        layer = draw(st.integers(min_value=0, max_value=n_layers - 1))
        src = draw(st.integers(min_value=0, max_value=n_nodes - 1))
        dst = draw(st.integers(min_value=0, max_value=n_nodes - 1))
        weight = draw(
            st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
        )
        rows.append([layer, src, dst, weight])

    return np.array(rows, dtype=np.float64)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_sparse_dense_sum_equivalent(edges):
    """sum reducer must match between sparse and dense output modes."""
    sparse = aggregate_layers(edges, reducer="sum", to_sparse=True).toarray()
    dense = aggregate_layers(edges, reducer="sum", to_sparse=False)
    np.testing.assert_allclose(sparse, dense, atol=1e-10, rtol=0.0)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_shape_matches_max_node_id(edges):
    """Output shape must be max(node_id)+1 on each axis."""
    expected_n = int(max(edges[:, 1].max(), edges[:, 2].max())) + 1
    out = aggregate_layers(edges, reducer="sum", to_sparse=True)
    assert out.shape == (expected_n, expected_n)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_permutation_invariance(edges):
    """Edge order should not affect aggregation results."""
    base = aggregate_layers(edges, reducer="mean", to_sparse=False)
    permuted = edges[::-1].copy()
    got = aggregate_layers(permuted, reducer="mean", to_sparse=False)
    np.testing.assert_allclose(base, got, atol=1e-10, rtol=0.0)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_non_negative_output(edges):
    """Non-negative inputs must produce non-negative outputs for all reducers."""
    for reducer in ("sum", "mean", "max"):
        out = aggregate_layers(edges, reducer=reducer, to_sparse=False)
        assert np.all(out >= 0.0)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_reducer_ordering_mean_le_max_le_sum(edges):
    """For non-negative weights: mean <= max <= sum elementwise."""
    mean_mat = aggregate_layers(edges, reducer="mean", to_sparse=False)
    max_mat = aggregate_layers(edges, reducer="max", to_sparse=False)
    sum_mat = aggregate_layers(edges, reducer="sum", to_sparse=False)

    assert np.all(mean_mat <= max_mat + 1e-10)
    assert np.all(max_mat <= sum_mat + 1e-10)


@pytest.mark.property
@given(weighted_edges())
@settings(max_examples=80, deadline=None)
def test_unweighted_sum_equals_occurrence_counts(edges):
    """Without explicit weights, sum reducer should count edge occurrences."""
    unweighted = edges[:, :3]
    got = aggregate_layers(unweighted, reducer="sum", to_sparse=False)

    n = int(max(unweighted[:, 1].max(), unweighted[:, 2].max())) + 1
    expected = np.zeros((n, n), dtype=np.float64)
    for _, src, dst in unweighted:
        expected[int(src), int(dst)] += 1.0

    np.testing.assert_allclose(got, expected, atol=1e-10, rtol=0.0)

