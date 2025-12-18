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

try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover - optional dependency
    given = None


def test_multilayer_node_features_zero_degree_entropy_zero():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "L1"},
            {"source": "B", "type": "L1"},
        ]
    )

    features = multilayer_node_features(net)

    assert set(features.keys()) == {"A", "B"}
    for vector in features.values():
        assert vector.shape == (3,)
        assert np.allclose(vector, np.zeros_like(vector))


def test_edge_agreement_penalizes_missing_mapping():
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_edges(
        [{"source": "a", "target": "b", "source_type": "L1", "target_type": "L1"}]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_edges(
        [{"source": "x", "target": "y", "source_type": "L1", "target_type": "L1"}]
    )

    score = edge_agreement(net_a, net_b, node_mapping={"a": "x"})

    assert score == 0.0


def test_align_networks_maps_high_degree_nodes_together():
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_edges(
        [
            {"source": "c", "target": "l1", "source_type": "L1", "target_type": "L1"},
            {"source": "c", "target": "l2", "source_type": "L1", "target_type": "L1"},
            {"source": "c", "target": "l3", "source_type": "L2", "target_type": "L2"},
        ]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_edges(
        [
            {"source": "h", "target": "r1", "source_type": "L1", "target_type": "L1"},
            {"source": "h", "target": "r2", "source_type": "L1", "target_type": "L1"},
            {"source": "h", "target": "r3", "source_type": "L2", "target_type": "L2"},
        ]
    )

    result = align_networks(net_a, net_b)

    assert result.node_mapping["c"] == "h"
    assert set(result.node_mapping.keys()) == {"c", "l1", "l2", "l3"}
    assert set(result.node_mapping.values()) == {"h", "r1", "r2", "r3"}
    assert result.score >= 0.99


def test_degree_correlation_missing_nodes_default_to_zero():
    net_a = multinet.multi_layer_network(directed=False)
    net_a.add_edges(
        [{"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"}]
    )

    net_b = multinet.multi_layer_network(directed=False)
    net_b.add_edges(
        [{"source": "X", "target": "Y", "source_type": "L1", "target_type": "L1"}]
    )

    correlation = degree_correlation(net_a, net_b, node_mapping={"A": "X", "B": "Z"})

    assert correlation == 0.0


if given:

    def _nonzero_vector(dim: int):
        finite = st.floats(
            min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False
        )
        return st.lists(finite, min_size=dim, max_size=dim).filter(
            lambda vals: any(abs(v) > 1e-6 for v in vals)
        )

    @st.composite
    def nonzero_matrix(draw):
        dim = draw(st.integers(min_value=1, max_value=4))
        rows = draw(st.integers(min_value=1, max_value=3))
        vectors = draw(st.lists(_nonzero_vector(dim), min_size=rows, max_size=rows))
        return np.array(vectors, dtype=float)

    @given(nonzero_matrix())
    @settings(max_examples=20)
    def test_cosine_similarity_self_similarity_properties(matrix):
        S = cosine_similarity_matrix(matrix, matrix)

        assert S.shape == (matrix.shape[0], matrix.shape[0])
        assert np.allclose(np.diag(S), 1.0)
        assert np.allclose(S, S.T)
        assert np.all(S <= 1.0 + 1e-12)
        assert np.all(S >= -1.0 - 1e-12)

else:

    def test_cosine_similarity_self_similarity_properties():
        pytest.skip("hypothesis not installed")
