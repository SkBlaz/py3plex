"""MAT-to-NetworkX parsing must retain numerical adjacency values."""

import networkx as nx
import numpy as np
import pytest
import scipy.io
import scipy.sparse

from py3plex.core.parsers import parse_matrix_to_nx, parse_network


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("via_dispatch", [False, True])
def test_matrix_network_preserves_weighted_adjacency(tmp_path, directed, via_dispatch):
    adjacency = np.array([
        [0.0, 2.5, 0.0, 0.0],
        [2.5, 0.0, -3.0, 0.0],
        [0.0, -3.0, 1.75, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ])
    if directed:
        adjacency[1, 0] = 0.0
    path = tmp_path / "weighted.mat"
    scipy.io.savemat(str(path), {"network": scipy.sparse.csr_matrix(adjacency)})
    if via_dispatch:
        graph, labels, activity = parse_network(str(path), "sparse_network", directed)
        assert activity is None
    else:
        graph, labels = parse_matrix_to_nx(str(path), directed)
    assert labels is None
    assert graph.is_directed() is directed
    nodes = [(i, "generic") for i in range(4)]
    assert set(graph) == set(nodes)
    assert graph.degree(nodes[-1]) == 0
    np.testing.assert_array_equal(nx.to_numpy_array(graph, nodelist=nodes), adjacency)
    assert graph[nodes[0]][nodes[1]]["weight"] == 2.5
    assert graph[nodes[1]][nodes[2]]["weight"] == -3.0
    assert graph[nodes[2]][nodes[2]]["weight"] == 1.75
