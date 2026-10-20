"""Correlation probabilities stay valid while undefined statistics stay NaN."""

import numpy as np
import pytest
from scipy import stats

from py3plex.algorithms.attribute_correlation import (
    _compute_correlation,
    correlate_attributes_across_layers,
    correlate_attributes_with_centrality,
)
from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize("by_layer", [False, True])
def test_orthogonal_attributes_and_degree_have_unit_probability(by_layer):
    net = multi_layer_network(directed=False, verbose=False)
    net.add_nodes([{"source": i, "type": "L", "score": i + 1} for i in range(3)])
    net.add_edges([[0, "L", 1, "L", 1], [1, "L", 2, "L", 1]], input_type="list")

    result = correlate_attributes_with_centrality(net, "score", by_layer=by_layer)

    coefficient, probability = result["L" if by_layer else "global"]
    assert coefficient == pytest.approx(0.0, abs=1e-15)
    assert probability == 1.0
    assert 0.0 <= probability <= 1.0


def test_orthogonal_cross_layer_attributes_have_unit_probability():
    net = multi_layer_network(verbose=False)
    for layer, scores in [("A", [1, 2, 3]), ("B", [1, 2, 1])]:
        net.add_nodes(
            [
                {"source": node, "type": layer, "score": score}
                for node, score in enumerate(scores)
            ]
        )

    coefficient, probability = correlate_attributes_across_layers(net, "score")[
        ("A", "B")
    ]

    assert coefficient == pytest.approx(0.0, abs=1e-15)
    assert probability == 1.0
    assert 0.0 <= probability <= 1.0


@pytest.mark.parametrize("method", ["pearson", "spearman", "kendall"])
def test_undefined_correlations_remain_nan(method):
    x = np.ones(4)
    y = np.arange(4)
    with np.errstate(invalid="ignore", divide="ignore"):
        coefficient, probability = _compute_correlation(x, y, method)
    assert np.isnan(coefficient)
    assert np.isnan(probability)


@pytest.mark.parametrize(
    "method, oracle",
    [
        ("pearson", stats.pearsonr),
        ("spearman", stats.spearmanr),
        ("kendall", stats.kendalltau),
    ],
)
def test_defined_correlations_match_scipy(method, oracle):
    x = np.array([4, 1, 7, 3, 8, 2])
    y = np.array([1, 6, 3, 4, 8, 7])
    actual = _compute_correlation(x, y, method)
    assert actual == pytest.approx(oracle(x, y))
    assert 0 <= actual[1] <= 1
