"""Tests for py3plex.algorithms.layer_similarity utilities."""

import types

import networkx as nx
import pytest

from py3plex.algorithms import layer_similarity as ls


def _net_with_graph(graph: nx.Graph):
    net = types.SimpleNamespace()
    net.core_network = graph
    return net


def test_jaccard_similarity_on_nodes_and_edges():
    """Jaccard similarity should compare overlaps per element type."""
    g = nx.Graph()
    g.add_nodes_from([("A", "L1"), ("B", "L1"), ("A", "L2"), ("C", "L2")])
    g.add_edges_from(
        [
            (("A", "L1"), ("B", "L1")),  # only in L1
            (("A", "L2"), ("C", "L2")),  # only in L2
        ]
    )
    net = _net_with_graph(g)

    node_sim = ls.jaccard_layer_similarity(net, "L1", "L2", element="nodes")
    edge_sim = ls.jaccard_layer_similarity(net, "L1", "L2", element="edges")
    pairs = ls.all_pairs_jaccard_similarity(net, element="nodes")

    assert node_sim == pytest.approx(1 / 3)
    assert edge_sim == 0.0
    assert pairs == {("L1", "L2"): node_sim}


def test_layer_similarity_validates_inputs():
    """Functions should raise ValueError for invalid setup."""
    with pytest.raises(ValueError, match="core_network"):
        ls.jaccard_layer_similarity(object(), "L1", "L2")

    g = nx.Graph()
    g.add_nodes_from([("A", "L1"), ("B", "L2")])
    net = _net_with_graph(g)

    with pytest.raises(ValueError, match="Unknown element"):
        ls.jaccard_layer_similarity(net, "L1", "L2", element="invalid")

    with pytest.raises(ValueError, match="Unknown method"):
        ls.layer_correlation_matrix(net, method="bad")


def test_frobenius_distance_identical_layers():
    """Identical layer subgraphs should have zero Frobenius distance."""
    g = nx.Graph()
    g.add_nodes_from([("A", "X"), ("B", "X"), ("A", "Y"), ("B", "Y")])
    g.add_edge(("A", "X"), ("B", "X"))
    g.add_edge(("A", "Y"), ("B", "Y"))
    net = _net_with_graph(g)

    distance = ls.frobenius_distance_layers(net, "X", "Y", normalized=True)
    assert distance == pytest.approx(0.0)


def test_layer_dissimilarity_index_averages_pairwise():
    """Dissimilarity index should aggregate 1 - average similarity."""
    g = nx.Graph()
    g.add_nodes_from(
        [
            ("A", "L1"),
            ("B", "L1"),
            ("A", "L2"),
            ("C", "L2"),
            ("D", "L3"),
            ("A", "L3"),
        ]
    )
    g.add_edges_from(
        [
            (("A", "L1"), ("B", "L1")),
            (("A", "L2"), ("C", "L2")),
            (("A", "L3"), ("D", "L3")),
        ]
    )
    net = _net_with_graph(g)

    dissimilarity = ls.layer_dissimilarity_index(net, method="jaccard")

    # Pairwise node overlaps: L1-L2 (1/3), L1-L3 (1/2), L2-L3 (1/3); average similarity = 7/18
    expected_similarity = (1 / 3 + 1 / 2 + 1 / 3) / 3
    assert dissimilarity == pytest.approx(1 - expected_similarity)
