"""Tests for helper functions in py3plex.ergonomics."""

from unittest.mock import Mock

import pytest

import py3plex.algorithms.community_detection as cd
from py3plex.ergonomics import (
    quick_analysis,
    quick_communities,
    quick_network,
    show_network_summary,
)


def test_quick_network_node_and_edge_creation():
    net = quick_network(
        people=["Alice", "Bob", "Carol"],
        layers=["work", "social"],
        connections=[("Alice", "Bob", "work"), ("Bob", "Carol", "social")],
        directed=False,
    )

    assert net.directed is False
    assert len(list(net.get_nodes())) == 6  # 3 people x 2 layers
    assert len(list(net.get_edges())) == 2


def test_quick_network_supports_interlayer_edges():
    net = quick_network(
        people=["Alice", "Bob"],
        layers=["work", "social"],
        connections=[("Alice", "Bob", "work", "social")],
        directed=True,
    )

    assert net.directed is True
    edges = list(net.get_edges())
    assert len(edges) == 1
    assert edges[0][0][1] == "work"
    assert edges[0][1][1] == "social"


def test_quick_analysis_returns_expected_shape():
    net = quick_network(
        people=["A", "B", "C"],
        layers=["layer1"],
        connections=[("A", "B", "layer1"), ("B", "C", "layer1")],
    )

    result = quick_analysis(net, metrics=["degree"], top_k=2, min_degree=1)

    assert set(result.keys()) == {"dataframe", "count", "network_stats"}
    assert result["count"] <= 2
    assert result["network_stats"]["nodes"] == 3
    assert result["network_stats"]["edges"] == 2
    assert result["network_stats"]["layers"] == len(list(net.get_layers()))
    assert "degree" in result["dataframe"].columns


def test_quick_communities_invalid_algorithm_raises():
    net = quick_network(people=["A", "B"], layers=["layer1"])

    with pytest.raises(ValueError, match="Unknown algorithm"):
        quick_communities(net, algorithm="not-an-algo")


def test_quick_communities_uses_louvain(monkeypatch):
    net = quick_network(people=["A", "B"], layers=["layer1"])

    mock_louvain = Mock(return_value={("A", "layer1"): 0, ("B", "layer1"): 1})
    monkeypatch.setattr(cd, "louvain_multilayer", mock_louvain)

    result = quick_communities(net, algorithm="louvain", seed=123)
    mock_louvain.assert_called_once_with(net, random_state=123)
    assert result["n_communities"] == 2
    assert result["sizes"] == {0: 1, 1: 1}


def test_quick_communities_uses_leiden(monkeypatch):
    net = quick_network(people=["A", "B"], layers=["layer1"])

    mock_leiden = Mock(return_value={("A", "layer1"): 3, ("B", "layer1"): 3})
    monkeypatch.setattr(cd, "leiden_multilayer", mock_leiden)

    result = quick_communities(net, algorithm="leiden", seed=7)
    mock_leiden.assert_called_once_with(net, random_state=7)
    assert result["n_communities"] == 1
    assert result["sizes"] == {3: 2}


def test_show_network_summary_prints_core_sections(capsys):
    net = quick_network(
        people=["Alice", "Bob"],
        layers=["work", "social"],
        connections=[("Alice", "Bob", "work", "social")],
    )

    show_network_summary(net)
    output = capsys.readouterr().out

    assert "NETWORK SUMMARY" in output
    assert "Nodes (replicas): 4" in output
    assert "Physical nodes: 2" in output
    assert "Inter-layer edges: 1" in output
