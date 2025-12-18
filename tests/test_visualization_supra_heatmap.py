from __future__ import annotations

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg", force=True)

from py3plex.core import multinet  # noqa: E402
from py3plex.exceptions import VisualizationError  # noqa: E402
from py3plex.visualization.multilayer import plot_supra_adjacency_heatmap  # noqa: E402


def _tiny_two_layer_net() -> multinet.multi_layer_network:
    net = multinet.multi_layer_network(directed=False, verbose=False)
    # Layer L1: a -- b (weight 2)
    # Layer L2: a -- c (weight 1)
    net.add_edges(
        [
            ["a", "L1", "b", "L1", 2.0],
            ["a", "L2", "c", "L2", 1.0],
        ],
        input_type="list",
    )
    return net


def _extract_imshow_matrix(fig) -> np.ndarray:
    ax = fig.axes[0]
    assert ax.images, "Expected heatmap image in axes"
    # `imshow` stores a masked array; coerce to ndarray.
    return np.asarray(ax.images[0].get_array())


def test_plot_supra_adjacency_heatmap_block_structure_no_interlayer():
    net = _tiny_two_layer_net()

    fig = plot_supra_adjacency_heatmap(net, include_inter_layer=False, node_order=["a", "b", "c"])
    m = _extract_imshow_matrix(fig)

    # 2 layers, 3 nodes => 6x6 matrix
    assert m.shape == (6, 6)

    # Layer ordering is sorted by name: ["L1", "L2"]
    # L1 block at [0:3, 0:3]; L2 block at [3:6, 3:6]
    expected = np.zeros((6, 6))
    # L1: a-b weight 2
    expected[0, 1] = expected[1, 0] = 2.0
    # L2: a-c weight 1 (within L2 block)
    expected[3 + 0, 3 + 2] = expected[3 + 2, 3 + 0] = 1.0

    np.testing.assert_allclose(m, expected)


def test_plot_supra_adjacency_heatmap_interlayer_coupling_added_for_common_nodes():
    net = _tiny_two_layer_net()

    fig = plot_supra_adjacency_heatmap(
        net,
        include_inter_layer=True,
        inter_layer_weight=5.0,
        node_order=["a", "b", "c"],
    )
    m = _extract_imshow_matrix(fig)

    # Common node across L1 and L2 is "a": coupling between the two diagonal blocks.
    assert m[0, 3] == 5.0
    assert m[3, 0] == 5.0

    # Non-common nodes should not be coupled.
    assert m[1, 4] == 0.0  # b(L1) - b(L2) doesn't exist in L2
    assert m[2, 5] == 0.0  # c(L1) - c(L2) doesn't exist in L1


def test_plot_supra_adjacency_heatmap_raises_on_empty_network():
    net = multinet.multi_layer_network(directed=False, verbose=False)

    # Empty py3plex networks may not have `core_network` initialized yet.
    with pytest.raises(VisualizationError, match="core_network"):
        plot_supra_adjacency_heatmap(net)
