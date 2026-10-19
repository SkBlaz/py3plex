"""Cross-layer correlation aligns values by physical ID without sorting IDs."""

import pytest
from scipy import stats

from py3plex.algorithms.attribute_correlation import correlate_attributes_across_layers
from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize(
    "method, oracle",
    [
        ("pearson", stats.pearsonr),
        ("spearman", stats.spearmanr),
        ("kendall", stats.kendalltau),
    ],
)
def test_correlations_align_shared_mixed_identifiers(method, oracle):
    net = multi_layer_network(verbose=False)
    # Different insertion order in each layer, plus nodes missing a counterpart
    # or the requested attribute, must not shift the value pairs.
    left = [(0, 2.0), ("0", -1.0), (("node", 7), 4.0), ("left-only", 1000.0)]
    right = [(("node", 7), 1.0), ("right-only", -1000.0), ("0", -5.0), (0, 7.0)]
    for layer, values in [("A", left), ("B", right)]:
        net.add_nodes(
            [{"source": node, "type": layer, "score": value} for node, value in values]
        )
    net.add_nodes(
        [
            {"source": "missing-score", "type": "A", "score": 100.0},
            {"source": "missing-score", "type": "B"},
        ]
    )
    before = {node: data.copy() for node, data in net.core_network.nodes(data=True)}

    result = correlate_attributes_across_layers(net, "score", correlation_method=method)

    assert set(result) == {("A", "B")}
    expected = oracle([2.0, -1.0, 4.0], [7.0, -5.0, 1.0])
    assert result[("A", "B")] == pytest.approx(expected)
    assert dict(net.core_network.nodes(data=True)) == before


def test_two_shared_mixed_identifiers():
    net = multi_layer_network(verbose=False)
    net.add_nodes(
        [
            {"source": node, "type": layer, "score": value}
            for layer in ["A", "B"]
            for node, value in [(0, 1.0), ("0", 3.0)]
        ]
    )
    result = correlate_attributes_across_layers(net, "score")
    assert result == {("A", "B"): pytest.approx((1.0, 1.0))}


@pytest.mark.parametrize("n_common", [0, 1])
def test_insufficient_common_attributes_are_not_correlated(n_common):
    net = multi_layer_network(verbose=False)
    net.add_nodes(
        [
            {"source": node, "type": layer, "score": value}
            for layer, entries in [
                ("A", [(0, 1.0), ("left", 2.0)]),
                ("B", [("right", 3.0)]),
            ]
            for node, value in entries
        ]
    )
    if n_common:
        net.add_nodes([{"source": 0, "type": "B", "score": 4.0}])
    assert correlate_attributes_across_layers(net, "score") == {}
