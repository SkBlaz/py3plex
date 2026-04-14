"""Focused tests for pure helper functions in ricci_layout."""

from __future__ import annotations

import numpy as np
import networkx as nx

from py3plex.visualization.ricci_layout import (
    _compute_mds_layout,
    _compute_spectral_layout,
    _ensure_edge_weights,
)


def test_ensure_edge_weights_adds_missing_default_only() -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C", weight=2.5)

    _ensure_edge_weights(graph, "weight")

    assert graph["A"]["B"]["weight"] == 1.0
    assert graph["B"]["C"]["weight"] == 2.5


def test_compute_mds_layout_handles_disconnected_graph() -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B", weight=1.0)
    graph.add_edge("C", "D", weight=2.0)

    pos = _compute_mds_layout(
        graph,
        dim=2,
        use_geodesic_distances=True,
        weight_attr="weight",
        random_state=7,
    )

    assert set(pos.keys()) == {"A", "B", "C", "D"}
    for coords in pos.values():
        assert isinstance(coords, np.ndarray)
        assert coords.shape == (2,)
        assert np.isfinite(coords).all()


def test_compute_spectral_layout_with_dim3_falls_back_to_2d(caplog) -> None:
    graph = nx.Graph()
    graph.add_edge("A", "B", weight=1.0)
    graph.add_edge("B", "C", weight=1.0)

    pos = _compute_spectral_layout(graph, dim=3, weight_attr="weight")

    assert set(pos.keys()) == {"A", "B", "C"}
    for coords in pos.values():
        assert isinstance(coords, np.ndarray)
        assert coords.shape == (2,)
    assert "only supports dim=2" in caplog.text
