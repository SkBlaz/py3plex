"""Additional tests for py3plex.alignment utilities."""

import numpy as np
import pytest

from py3plex.alignment import (
    align_networks,
    cosine_similarity_matrix,
    degree_correlation,
    edge_agreement,
    multilayer_node_features,
)
from py3plex.core import multinet


def test_features_respect_layer_order_and_entropy():
    """Layer order argument should drive per-layer degree ordering and entropy."""
    net = multinet.multi_layer_network(directed=False)
    net.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
            {"source": "A", "target": "C", "source_type": "L1", "target_type": "L1"},
            {"source": "A", "target": "D", "source_type": "L2", "target_type": "L2"},
        ]
    )

    features = multilayer_node_features(net, layers=["L2", "L1"])
    feat_a = features["A"]

    total, l2_degree, l1_degree, entropy = feat_a
    expected_entropy = -(
        (1 / 3) * np.log(1 / 3) + (2 / 3) * np.log(2 / 3)
    )

    assert total == pytest.approx(3.0)
    assert l2_degree == pytest.approx(1.0)
    assert l1_degree == pytest.approx(2.0)
    assert entropy == pytest.approx(expected_entropy)


def test_edge_agreement_respects_layer_mapping():
    """Cross-layer mapping should allow matching edges in different layer names."""
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_edges(
        [{"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"}]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_edges(
        [{"source": "X", "target": "Y", "source_type": "L2", "target_type": "L2"}]
    )

    mapping = {"A": "X", "B": "Y"}
    score = edge_agreement(net_a, net_b, mapping, layer_mapping={"L1": "L2"})

    assert score == 1.0


def test_align_networks_handles_edgeless_inputs():
    """Networks with only nodes (no edges) should align with zero similarity."""
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_nodes(
        [
            {"source": "A", "type": "L1"},
            {"source": "B", "type": "L1"},
        ]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_nodes(
        [
            {"source": "X", "type": "L1"},
            {"source": "Y", "type": "L1"},
        ]
    )

    result = align_networks(net_a, net_b)

    assert set(result.node_mapping.keys()) == {"A", "B"}
    assert set(result.node_mapping.values()) == {"X", "Y"}
    assert result.layer_mapping == {"L1": "L1"}
    assert result.score == 0.0
    assert result.similarity_matrix.shape == (2, 2)


def test_degree_correlation_zero_variance_returns_zero():
    """Constant degree vectors should short-circuit to zero correlation."""
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_edges(
        [{"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"}]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_edges(
        [{"source": "X", "target": "Y", "source_type": "L2", "target_type": "L2"}]
    )

    mapping = {"A": "X", "B": "Y"}
    correlation = degree_correlation(net_a, net_b, mapping)

    assert correlation == 0.0


def test_cosine_similarity_matrix_dimension_mismatch_raises():
    """Invalid feature shapes should propagate a ValueError during matmul."""
    A = np.ones((2, 3))
    B = np.ones((2, 2))

    with pytest.raises(ValueError):
        cosine_similarity_matrix(A, B)
