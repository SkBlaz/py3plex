"""Additional tests for py3plex.multinet.aggregation."""

import numpy as np
import pytest
import scipy.sparse as sp

from py3plex.multinet import aggregation


def test_mean_aggregation_unsorted_duplicates_sparse():
    """Mean reducer should handle duplicate edges even when unsorted."""
    edges = np.array(
        [
            [0, 0, 2, 2.0],
            [1, 5, 6, 4.0],
            [2, 0, 2, 4.0],  # duplicate of (0,2) separated by other edge
        ]
    )

    mat = aggregation.aggregate_layers(edges, reducer="mean", to_sparse=True)

    assert sp.isspmatrix_csr(mat)
    assert mat.shape == (7, 7)
    assert mat[0, 2] == pytest.approx(3.0)  # mean of 2.0 and 4.0
    assert mat[5, 6] == pytest.approx(4.0)


def test_max_aggregation_sparse_deduplicates():
    """Max reducer should keep only the largest weight per edge."""
    edges = np.array(
        [
            [0, 3, 4, 1.5],
            [1, 3, 4, 2.5],
            [2, 3, 4, 2.0],
        ]
    )

    mat = aggregation.aggregate_layers(edges, reducer="max", to_sparse=True)

    assert sp.isspmatrix_csr(mat)
    assert mat.nnz == 1
    assert mat[3, 4] == pytest.approx(2.5)


def test_non_integer_node_ids_raise_value_error():
    """Node identifiers must be castable to integers."""
    edges = np.array([["0", "a", "1", "1.0"]], dtype=object)

    with pytest.raises(ValueError):
        aggregation.aggregate_layers(edges, reducer="sum", to_sparse=False)


def test_validation_helpers_detect_invalid_results():
    """Helper validators should flag invalid shapes and negative weights."""
    edges = np.array([[0, 0, 2, 1.0]])
    bad_dense = np.zeros((2, 2))
    bad_sparse = sp.csr_matrix(np.array([[0, -1], [0, 0]]))

    assert aggregation._validate_node_preservation(bad_dense, edges) is False
    assert aggregation._validate_no_negative_weights(bad_sparse) is False
