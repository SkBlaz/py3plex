"""Correctness check: mdl_score must worsen monotonically under corruption.

This test builds a graded sequence of partitions at increasing
corruption fractions (0%, 10%, ..., 100% of nodes reassigned to a random
community) on a single graph with known ground truth, and checks that the
*expected* mdl_score (averaged over many random corruptions per level, to
wash out per-trial sampling noise) is non-decreasing across the whole
sequence -- not just at the two ends.
"""

import random
import warnings

import networkx as nx
import pytest
from scipy.stats import spearmanr

from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    mdl_score,
)

LEVELS = [i / 10 for i in range(11)]  # 0.0, 0.1, ..., 1.0
N_TRIALS_PER_LEVEL = 25
# Averaged-score noise floor: adjacent levels are allowed to dip by this
# much (relative to the score's own scale) without failing, since
# N_TRIALS_PER_LEVEL random corruptions per level reduce but do not
# eliminate sampling noise. The monotonicity trend below is the real
# assertion; this tolerance only guards against flakiness from that noise.
ADJACENT_LEVEL_TOLERANCE = 0.01


def _net(G, directed=False):
    net = multinet.multi_layer_network(directed=directed)
    net.core_network = G
    return net


def _build_community_graph(rng, n_communities=6, community_size=15, p_in=0.4, p_out=0.02):
    """A 6-community, 90-node graph with real (non-adversarial) partial
    density: p_in=0.4 intra-community, p_out=0.02 inter-community. Multiple
    communities of equal size (unlike the two-community toy graphs
    elsewhere in the test suite) so the corruption sweep has enough
    structure to be graded rather than binary.
    """
    G = nx.Graph()
    ground_truth = {}
    communities = []
    for c in range(n_communities):
        members = [(f"c{c}_{i}", "L") for i in range(community_size)]
        G.add_nodes_from(members)
        communities.append(members)
        for m in members:
            ground_truth[m] = c
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if rng.random() < p_in:
                    G.add_edge(members[i], members[j])

    all_members = [m for members in communities for m in members]
    for i in range(len(all_members)):
        for j in range(i + 1, len(all_members)):
            u, v = all_members[i], all_members[j]
            if ground_truth[u] == ground_truth[v]:
                continue
            if rng.random() < p_out:
                G.add_edge(u, v)

    return G, ground_truth


def _corrupt_partition(rng, ground_truth, fraction, n_communities):
    """Reassign `fraction` of nodes to a uniformly random community.

    At fraction=0.0 this is exactly ground truth; at fraction=1.0 every
    node is independently relabeled (a node can coincidentally land back
    on its true community), so the curve is expected to flatten out
    approaching 1.0 rather than keep climbing indefinitely -- monotonic
    non-decreasing, not linear.
    """
    corrupted = dict(ground_truth)
    nodes = list(ground_truth.keys())
    n_to_corrupt = round(fraction * len(nodes))
    for node in rng.sample(nodes, n_to_corrupt):
        corrupted[node] = rng.randrange(n_communities)
    return corrupted


def test_mdl_score_monotonically_worsens_with_corruption():
    rng = random.Random("mdl-corruption-monotonicity")
    G, ground_truth = _build_community_graph(rng)
    net = _net(G)
    n_communities = len(set(ground_truth.values()))

    mean_scores = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for level in LEVELS:
            scores = [
                mdl_score(_corrupt_partition(rng, ground_truth, level, n_communities), net)
                for _ in range(N_TRIALS_PER_LEVEL)
            ]
            mean_scores.append(sum(scores) / len(scores))

    for level, (lo, hi) in zip(LEVELS, zip(mean_scores, mean_scores[1:])):
        assert hi >= lo - ADJACENT_LEVEL_TOLERANCE * lo, (
            f"mean mdl_score dropped from {lo:.3f} to {hi:.3f} going from "
            f"corruption level {level:.1f} to {level + 0.1:.1f}: {mean_scores}"
        )

    correlation, _ = spearmanr(LEVELS, mean_scores)
    assert correlation > 0.95, (
        f"expected corruption level and mean mdl_score to be strongly "
        f"rank-correlated, got spearman={correlation:.3f}: {mean_scores}"
    )