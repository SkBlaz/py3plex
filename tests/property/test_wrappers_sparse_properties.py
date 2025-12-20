from __future__ import annotations

import numpy as np
import pytest

scipy = pytest.importorskip("scipy")
from scipy import sparse  # noqa: E402

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st  # noqa: E402

from py3plex.wrappers.benchmark_nodes import sparse2graph  # noqa: E402


@given(st.integers(min_value=1, max_value=6))
def test_sparse2graph_deduplicates_and_stringifies_keys(n):
    data = np.ones(n * n)
    row = np.repeat(np.arange(n), n)
    col = np.tile(np.arange(n), n)
    mat = sparse.coo_matrix((data, (row, col)), shape=(n, n))

    graph = sparse2graph(mat)

    assert set(graph.keys()) == {str(i) for i in range(n)}
    for i in range(n):
        # All nodes are connected to every other node (including duplicates), deduped via set.
        assert set(graph[str(i)]) == {str(j) for j in range(n)}


@given(
    st.integers(min_value=1, max_value=6),
    st.integers(min_value=1, max_value=6),
    st.floats(min_value=0.0, max_value=1.0),
)
def test_sparse2graph_matches_nonzero_pattern(rows, cols, density):
    # Build a random binary matrix with given density.
    rng = np.random.default_rng(0)
    mask = rng.random((rows, cols)) < density
    data = np.ones(mask.sum())
    r_idx, c_idx = np.nonzero(mask)
    mat = sparse.csr_matrix((data, (r_idx, c_idx)), shape=(rows, cols))

    graph = sparse2graph(mat)

    for i in range(rows):
        expected_neighbors = {str(j) for j in np.nonzero(mask[i])[0]}
        if expected_neighbors:
            assert str(i) in graph
            assert set(graph[str(i)]) == expected_neighbors
        else:
            assert str(i) not in graph
