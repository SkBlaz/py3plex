import numpy as np
import pytest

from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity
from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize("directed", [False, True])
def test_sparse_score_matches_pairwise_definition(directed):
    net = multi_layer_network(directed=directed, verbose=False)
    rows = [["a", "L", "a", "L", 2], ["a", "L", "b", "L", 1],
            ["a", "L", "b", "L", 3], ["c", "L", "a", "L", 4],
            ["a", "M", "d", "M", 0], ["a", "L", "d", "M", 9]]
    net.add_edges(rows, input_type="list")
    communities = {("a", "L"): 7, ("b", "L"): 7, ("a", "M"): 7}
    gamma = {"L": 1.25}
    omega = np.array([[0, 0.5], [1.75, 0]])
    matrix = net.get_supra_adjacency_matrix().toarray()
    nodes = list(net.get_nodes())
    score = total = 0
    for i, (u, layer) in enumerate(nodes):
        layer_nodes = [k for k, node in enumerate(nodes) if node[1] == layer]
        mass = matrix[np.ix_(layer_nodes, layer_nodes)].sum()
        for j, (v, other) in enumerate(nodes):
            equal = nodes[i] in communities and communities[nodes[i]] == communities.get(nodes[j])
            if layer == other:
                total += matrix[i, j]
                expected = (matrix[i, layer_nodes].sum() * matrix[j, layer_nodes].sum() / mass
                            if mass else 0)
                score += equal * (matrix[i, j] - gamma.get(layer, 1) * expected)
            elif u == v:
                coupling = omega[net.layers.index(layer), net.layers.index(other)]
                score += equal * coupling
                total += coupling
    assert multilayer_modularity(net, communities, gamma, omega) == pytest.approx(score / total)
