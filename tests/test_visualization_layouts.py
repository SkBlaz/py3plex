from __future__ import annotations

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg", force=True)

import networkx as nx  # noqa: E402

from py3plex.exceptions import Py3plexLayoutError  # noqa: E402
from py3plex.visualization.layout_algorithms import compute_random_layout  # noqa: E402
from py3plex.visualization.multilayer import hairball_plot  # noqa: E402


def test_compute_random_layout_is_reproducible_with_seed():
    g = nx.path_graph(5)

    pos1 = compute_random_layout(g, seed=123)
    pos2 = compute_random_layout(g, seed=123)

    assert set(pos1.keys()) == set(g.nodes())
    assert set(pos2.keys()) == set(g.nodes())
    for node in g.nodes():
        np.testing.assert_allclose(pos1[node], pos2[node])
        assert pos1[node].shape == (2,)


def test_hairball_plot_custom_coordinates_passthrough_draw_false():
    g = nx.Graph()
    a = ("a", "L0")
    b = ("b", "L0")
    g.add_edge(a, b)

    # Custom, deterministic coordinates.
    pos = {a: np.array([0.0, 0.0]), b: np.array([1.0, 0.0])}

    returned_g, node_sizes, node_colors, returned_pos = hairball_plot(
        g,
        color_list=[0, 0],
        node_size=1,
        draw=False,
        layout_algorithm="custom_coordinates",
        layout_parameters={"pos": pos},
    )

    assert returned_g is g
    assert returned_pos is pos
    assert len(node_sizes) == g.number_of_nodes()
    assert len(node_colors) == g.number_of_nodes()


def test_hairball_plot_invalid_layout_algorithm_raises():
    g = nx.Graph()
    g.add_edge(("a", "L0"), ("b", "L0"))

    with pytest.raises(Py3plexLayoutError, match="Unknown layout algorithm"):
        hairball_plot(g, draw=False, layout_algorithm="not_a_layout", layout_parameters={})
