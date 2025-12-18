"""Correctness tests for py3plex.multinet.aggregation."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

import numpy as np
import pytest

from py3plex.multinet import aggregate_layers
from py3plex.multinet.aggregation import _validate_no_negative_weights


def _dense_reference(
    edges: np.ndarray, reducer: str = "sum"
) -> Tuple[np.ndarray, Dict[Tuple[int, int], int]]:
    """Reference adjacency computation using Python loops."""
    rows = edges[:, 1].astype(int)
    cols = edges[:, 2].astype(int)
    weights = edges[:, 3] if edges.shape[1] > 3 else np.ones(len(edges))

    n = max(rows.max(), cols.max()) + 1
    sums: Dict[Tuple[int, int], float] = defaultdict(float)
    counts: Dict[Tuple[int, int], int] = defaultdict(int)

    for r, c, w in zip(rows, cols, weights):
        key = (r, c)
        sums[key] += float(w)
        counts[key] += 1

    mat = np.zeros((n, n), dtype=float)
    for (r, c), total in sums.items():
        if reducer == "sum":
            value = total
        elif reducer == "mean":
            value = total / counts[(r, c)]
        elif reducer == "max":
            value = total if counts[(r, c)] == 1 else np.nan  # replaced later
        else:
            raise ValueError("Unsupported reducer in reference")
        mat[r, c] = value

    if reducer == "max":
        # recompute max separately to avoid storing all weights per edge
        mat.fill(0.0)
        max_vals: Dict[Tuple[int, int], float] = defaultdict(lambda: float("-inf"))
        for r, c, w in zip(rows, cols, weights):
            key = (r, c)
            max_vals[key] = max(max_vals[key], float(w))
        for (r, c), value in max_vals.items():
            mat[r, c] = value

    return mat, counts


def test_sum_reducer_matches_reference_dense_and_sparse():
    edges = np.array(
        [
            [0, 0, 1, 1.0],
            [1, 0, 1, 2.5],  # duplicate edge
            [1, 1, 0, 0.5],
            [2, 2, 2, 3.0],  # self-loop
        ]
    )

    ref_dense, _ = _dense_reference(edges, reducer="sum")

    sparse = aggregate_layers(edges, reducer="sum", to_sparse=True)
    dense = aggregate_layers(edges, reducer="sum", to_sparse=False)

    assert sparse.shape == (3, 3)
    assert np.allclose(sparse.toarray(), ref_dense)
    assert np.allclose(dense, ref_dense)
    assert _validate_no_negative_weights(sparse)


def test_mean_reducer_averages_duplicate_edges():
    edges = np.array(
        [
            [0, 0, 1, 2.0],
            [1, 0, 1, 4.0],
            [1, 1, 0, 1.0],
        ]
    )

    ref_dense, counts = _dense_reference(edges, reducer="mean")
    assert counts[(0, 1)] == 2  # ensure duplicate present

    result = aggregate_layers(edges, reducer="mean", to_sparse=False)

    assert np.isclose(result[0, 1], 3.0)  # (2 + 4) / 2
    assert np.allclose(result, ref_dense)


def test_max_reducer_takes_maximum_of_duplicates():
    edges = np.array(
        [
            [0, 0, 1, 1.0],
            [1, 0, 1, 5.0],
            [2, 0, 1, 3.0],
            [0, 1, 2, 2.0],
        ]
    )

    ref_dense, _ = _dense_reference(edges, reducer="max")

    result = aggregate_layers(edges, reducer="max", to_sparse=False)

    assert result[0, 1] == 5.0
    assert np.allclose(result, ref_dense)


def test_missing_weight_column_defaults_to_one():
    edges = np.array(
        [
            [0, 0, 1],
            [0, 1, 2],
        ]
    )

    result = aggregate_layers(edges, reducer="sum", to_sparse=False)

    expected = np.zeros((3, 3), dtype=float)
    expected[0, 1] = 1.0
    expected[1, 2] = 1.0

    assert np.allclose(result, expected)


def test_invalid_edges_shape_raises_value_error():
    edges = np.array([0, 1, 2])  # ndim=1
    with pytest.raises(ValueError):
        aggregate_layers(edges)


def test_invalid_reducer_raises_value_error():
    edges = np.array([[0, 0, 1]])
    with pytest.raises(ValueError):
        aggregate_layers(edges, reducer="median")


def test_empty_edges_array_raises_value_error():
    edges = np.empty((0, 3))
    with pytest.raises(ValueError):
        aggregate_layers(edges)


def test_weight_col_index_is_used_when_provided():
    """`weight_col` should select which column is used for weights (ndarray input)."""
    # Provide 5 columns: (layer, src, dst, wrong_weight, correct_weight)
    edges = np.array(
        [
            [0, 0, 1, 100.0, 1.5],
            [1, 0, 1, 200.0, 2.5],
        ],
        dtype=float,
    )

    # Sum using the correct weight column should be 1.5 + 2.5 = 4.0
    result = aggregate_layers(edges, weight_col=4, reducer="sum", to_sparse=False)
    assert result[0, 1] == pytest.approx(4.0)


def test_weight_col_out_of_bounds_raises_value_error():
    edges = np.array([[0, 0, 1, 1.0]])
    with pytest.raises(ValueError):
        aggregate_layers(edges, weight_col=10, reducer="sum", to_sparse=False)


def test_fractional_node_ids_raise_value_error():
    """Non-integer node ids should not be silently truncated."""
    edges = np.array([[0, 0.2, 1.0, 1.0]], dtype=float)
    with pytest.raises(ValueError):
        aggregate_layers(edges, reducer="sum", to_sparse=False)


try:
    from hypothesis import given, settings, strategies as st

    HYPOTHESIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    HYPOTHESIS_AVAILABLE = False


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
@settings(max_examples=25, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=3),  # layer (ignored)
            st.integers(min_value=0, max_value=4),  # src
            st.integers(min_value=0, max_value=4),  # dst
            st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        ),
        min_size=1,
        max_size=20,
    )
)
def test_sum_property_matches_reference_random_edges(random_edges):
    edges = np.array(random_edges, dtype=float)

    ref_dense, _ = _dense_reference(edges, reducer="sum")
    result = aggregate_layers(edges, reducer="sum", to_sparse=False)

    assert np.allclose(result, ref_dense)


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
@settings(max_examples=25, deadline=None)
@given(
    reducer=st.sampled_from(["mean", "max"]),
    random_edges=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=3),  # layer (ignored)
            st.integers(min_value=0, max_value=4),  # src
            st.integers(min_value=0, max_value=4),  # dst
            st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        ),
        min_size=1,
        max_size=25,
    ),
)
def test_mean_and_max_properties_match_reference_random_edges(reducer, random_edges):
    edges = np.array(random_edges, dtype=float)

    ref_dense, _ = _dense_reference(edges, reducer=reducer)
    result = aggregate_layers(edges, reducer=reducer, to_sparse=False)

    assert np.allclose(result, ref_dense)
