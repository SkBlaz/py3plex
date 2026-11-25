import numpy as np
import pytest

from py3plex.algorithms.community_detection.multilayer_modularity import (
    louvain_multilayer, multilayer_modularity,
)
from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize("directed", [True, False])
def test_seeded_louvain_matches_full_score_moves(directed):
    net = multi_layer_network(directed=directed, verbose=False)
    rng = np.random.default_rng(42)
    for layer in ["L", "M"]:
        for i in range(6):
            for j in (i, (i + 1) % 6, int(rng.integers(6))):
                net.add_edges([[i, layer, j, layer, float(rng.uniform(.1, 2))]], input_type="list")
    gamma = {"L": .82, "M": 1.13}
    omega = np.array([[0., .3], [.4, 0.]])
    matrix = net.get_supra_adjacency_matrix()
    nodes = list(net.get_nodes())
    part = {node: i for i, node in enumerate(nodes)}
    order = np.random.RandomState(21)
    for _ in range(4):
        changed = False
        for i in order.permutation(len(nodes)):
            u = nodes[i]
            candidates = {part[v] for j, v in enumerate(nodes)
                          if matrix[i, j] > 0 or u[0] == v[0]}
            current = part[u]
            score = multilayer_modularity(net, part, gamma, omega)
            best = current
            for candidate in candidates - {current}:
                part[u] = candidate
                trial = multilayer_modularity(net, part, gamma, omega)
                if trial > score:
                    score, best = trial, candidate
            part[u] = best
            changed |= best != current
        if not changed:
            break
    actual = louvain_multilayer(net, gamma, omega, random_state=21, max_iter=4)
    assert {frozenset(k for k in nodes if part[k] == part[v]) for v in nodes} == {
        frozenset(k for k in nodes if actual[k] == actual[v]) for v in nodes
    }
