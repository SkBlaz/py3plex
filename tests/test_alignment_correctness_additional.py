import math

import numpy as np
import pytest

from py3plex.alignment import (
    align_networks,
    degree_correlation,
    edge_agreement,
    multilayer_node_features,
)
from py3plex.core import multinet

try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover - optional dependency
    given = None


def _degree_correlation_reference(net_a, net_b, mapping):
    def degrees(net):
        deg = {}
        for edge in net.get_edges():
            src, tgt = edge[0], edge[1]
            src_id = src[0] if isinstance(src, tuple) and len(src) >= 2 else src
            tgt_id = tgt[0] if isinstance(tgt, tuple) and len(tgt) >= 2 else tgt
            deg[src_id] = deg.get(src_id, 0) + 1
            deg[tgt_id] = deg.get(tgt_id, 0) + 1
        return deg

    deg_a = degrees(net_a)
    deg_b = degrees(net_b)

    xs, ys = [], []
    for a, b in mapping.items():
        xs.append(deg_a.get(a, 0))
        ys.append(deg_b.get(b, 0))

    if len(xs) < 2:
        return 0.0

    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if xs.std() == 0 or ys.std() == 0:
        return 0.0

    corr = float(np.corrcoef(xs, ys)[0, 1])
    return 0.0 if np.isnan(corr) else corr


def test_multilayer_node_features_interlayer_self_edge_counts_both_endpoints():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "A",
                "source_type": "L1",
                "target_type": "L2",
            }
        ]
    )

    feats = multilayer_node_features(net, layers=["L1", "L2"])
    vec = feats["A"]

    assert vec.shape == (4,)
    assert vec[0] == pytest.approx(2.0)  # total degree
    assert vec[1] == pytest.approx(1.0)  # deg in L1
    assert vec[2] == pytest.approx(1.0)  # deg in L2
    assert vec[3] == pytest.approx(math.log(2.0))  # entropy with p=(0.5, 0.5)


def test_multilayer_node_features_respects_layer_order():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
            {"source": "A", "target": "C", "source_type": "L2", "target_type": "L2"},
        ]
    )

    feats_12 = multilayer_node_features(net, layers=["L1", "L2"], include_layer_entropy=False)
    feats_21 = multilayer_node_features(net, layers=["L2", "L1"], include_layer_entropy=False)

    # A participates once in each layer, but the per-layer slots should swap.
    assert feats_12["A"][1:].tolist() == [1.0, 1.0]
    assert feats_21["A"][1:].tolist() == [1.0, 1.0]

    # B participates only in L1, C only in L2.
    assert feats_12["B"][1:].tolist() == [1.0, 0.0]
    assert feats_21["B"][1:].tolist() == [0.0, 1.0]
    assert feats_12["C"][1:].tolist() == [0.0, 1.0]
    assert feats_21["C"][1:].tolist() == [1.0, 0.0]


def test_edge_agreement_supports_interlayer_self_edges():
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_a.add_edges([{"source": "A", "target": "A", "source_type": "L1", "target_type": "L2"}])

    net_b = multinet.multi_layer_network(directed=False, verbose=False)
    net_b.add_edges([{"source": "X", "target": "X", "source_type": "L1", "target_type": "L2"}])

    assert edge_agreement(net_a, net_b, node_mapping={"A": "X"}) == 1.0


def test_degree_correlation_matches_reference_with_interlayer_self_edge():
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_a.add_edges(
        [
            {"source": "A", "target": "A", "source_type": "L1", "target_type": "L2"},
            {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
            {"source": "B", "target": "C", "source_type": "L1", "target_type": "L1"},
        ]
    )

    net_b = multinet.multi_layer_network(directed=False, verbose=False)
    net_b.add_edges(
        [
            {"source": "Y", "target": "X", "source_type": "L1", "target_type": "L1"},
            {"source": "Y", "target": "Z", "source_type": "L1", "target_type": "L1"},
        ]
    )

    mapping = {"A": "Y", "B": "X", "C": "Z"}

    expected = _degree_correlation_reference(net_a, net_b, mapping)
    observed = degree_correlation(net_a, net_b, mapping)

    assert observed == pytest.approx(expected)


def test_align_networks_empty_networks_return_empty_alignment():
    pytest.importorskip("scipy")
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_b = multinet.multi_layer_network(directed=False, verbose=False)

    result = align_networks(net_a, net_b)

    assert result.node_mapping == {}
    assert result.layer_mapping is None
    assert result.score == 0.0
    assert result.similarity_matrix is None


def test_align_networks_rejects_unsupported_method():
    pytest.importorskip("scipy")
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_b = multinet.multi_layer_network(directed=False, verbose=False)

    with pytest.raises(ValueError, match="Unsupported alignment method"):
        align_networks(net_a, net_b, method="made_up")  # type: ignore[arg-type]


def test_align_networks_unique_mapping_oracle():
    pytest.importorskip("scipy")
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_a.add_edges(
        [
            {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
            {"source": "B", "target": "C", "source_type": "L2", "target_type": "L2"},
        ]
    )

    net_b = multinet.multi_layer_network(directed=False, verbose=False)
    net_b.add_edges(
        [
            {"source": "X", "target": "Y", "source_type": "L1", "target_type": "L1"},
            {"source": "Y", "target": "Z", "source_type": "L2", "target_type": "L2"},
        ]
    )

    result = align_networks(net_a, net_b)

    assert result.node_mapping == {"A": "X", "B": "Y", "C": "Z"}
    assert result.score == pytest.approx(1.0)
    assert result.similarity_matrix is not None
    assert result.similarity_matrix.shape == (3, 3)


if given:

    @st.composite
    def multilayer_edges(draw):
        node_ids = ["A", "B", "C"]
        layers = ["L1", "L2", "L3"][: draw(st.integers(min_value=1, max_value=3))]

        n_edges = draw(st.integers(min_value=0, max_value=10))
        edges = []
        for _ in range(n_edges):
            src = draw(st.sampled_from(node_ids))
            tgt = draw(st.sampled_from(node_ids))
            src_layer = draw(st.sampled_from(layers))
            tgt_layer = draw(st.sampled_from(layers))
            edges.append(
                {"source": src, "target": tgt, "source_type": src_layer, "target_type": tgt_layer}
            )
        return layers, edges

    @given(multilayer_edges())
    @settings(max_examples=40)
    def test_property_multilayer_node_features_matches_reference_degrees(data):
        layers, edges = data
        net = multinet.multi_layer_network(directed=False, verbose=False)
        if edges:
            net.add_edges(edges)

        feats = multilayer_node_features(net, layers=layers, include_layer_entropy=False)

        layer_idx = {layer: i for i, layer in enumerate(layers)}
        ref = {node_id: np.zeros(len(layers), dtype=float) for node_id in feats.keys()}

        edge_iter = [] if getattr(net, "core_network", None) is None else net.get_edges()
        for edge in edge_iter:
            src, tgt = edge[0], edge[1]
            src_id, src_layer = src[0], src[1]
            tgt_id, tgt_layer = tgt[0], tgt[1]

            ref[src_id][layer_idx[src_layer]] += 1.0
            ref[tgt_id][layer_idx[tgt_layer]] += 1.0

        for node_id, vec in feats.items():
            assert vec.shape == (1 + len(layers),)
            assert vec[0] == pytest.approx(float(ref[node_id].sum()))
            assert np.allclose(vec[1:], ref[node_id])

else:

    def test_property_multilayer_node_features_matches_reference_degrees():
        pytest.skip("hypothesis not installed")
