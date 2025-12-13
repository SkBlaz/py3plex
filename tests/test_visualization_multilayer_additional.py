"""Additional tests for py3plex.visualization APIs."""

import random

import matplotlib

matplotlib.use("Agg")  # Headless backend for CI environments
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.exceptions import Py3plexLayoutError, VisualizationError
from py3plex.visualization.multilayer import (
    hairball_plot,
    plot_edge_colored_projection,
    plot_ego_multilayer,
    supra_adjacency_matrix_plot,
    visualize_multilayer_network,
)


@pytest.fixture(autouse=True)
def _seed_randomness():
    random.seed(0)
    np.random.seed(0)


def _simple_multilayer_network():
    """Create a small deterministic multilayer network."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L1", "b", "L1", 1.0],
            ["b", "L1", "c", "L1", 1.0],
            ["a", "L2", "b", "L2", 1.0],
        ],
        input_type="list",
    )
    return net


def test_visualize_multilayer_network_unknown_type():
    """Requesting an unknown visualization type raises a clear error."""
    net = _simple_multilayer_network()
    with pytest.raises(VisualizationError, match="Unknown visualization_type"):
        visualize_multilayer_network(net, visualization_type="not_a_mode")


def test_hairball_plot_unknown_layout_raises():
    """hairball_plot surfaces layout validation errors."""
    graph = nx.Graph()
    graph.add_edge(("x", "L1"), ("y", "L1"))
    with pytest.raises(Py3plexLayoutError, match="Unknown layout algorithm"):
        hairball_plot(graph, layout_algorithm="invalid_algo", draw=False)


def test_supra_adjacency_matrix_plot_returns_axes(tmp_path):
    """Supra adjacency plotting attaches image data and can be saved."""
    matrix = np.array([[0, 1], [1, 0]])
    fig, ax = plt.subplots()
    result_ax = supra_adjacency_matrix_plot(matrix, ax=ax)
    assert result_ax.images, "imshow should attach an image to the axis"

    out_path = tmp_path / "supra.png"
    fig.savefig(out_path)
    assert out_path.exists()
    plt.close(fig)


def test_plot_edge_colored_projection_generates_lines(tmp_path):
    """Edge-colored projection draws edges for each layer without display."""
    net = _simple_multilayer_network()
    fig = plot_edge_colored_projection(net, layout="spring")
    ax = fig.axes[0]
    # NetworkX adds edges as collections; ensure at least one is present
    assert any(getattr(coll, "get_segments", None) for coll in ax.collections)

    out_path = tmp_path / "projection.png"
    fig.savefig(out_path)
    assert out_path.exists()
    plt.close(fig)


def test_plot_ego_multilayer_missing_node_raises():
    """Ego visualization reports missing ego across layers."""
    net = _simple_multilayer_network()
    with pytest.raises(ValueError, match="not found in any layer"):
        plot_ego_multilayer(net, ego="nonexistent", max_depth=1)
