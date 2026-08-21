"""
`tests/test_mdl_score.py::TestResolutionLimit` proves the
`_block_parameter_cost` fix works at exactly one construction (two 10-node,
~62%-density blocks vs. an all-singleton fragmentation of them). That
leaves open whether the fix merely patches that one example or actually
closes the gap in general -- e.g. a much larger block, a much
sparser/denser one, an asymmetric pair of blocks, a directed graph, or a
partial (not-fully-singleton) fragmentation still finds a crossover point
where a fragmented partition beats the true one.

This sweeps block size, density (including the exact 0.0/1.0 extremes that
define the resolution-limit regime), block-size/density asymmetry,
fragmentation granularity (full singleton down to a handful of
sub-communities per block), and directedness -- scoring ground truth
against every fragmented alternative in the grid and asserting ground
truth always wins. Every violation found (not just the first) is collected
and reported, since the point of this test is to map out whether a
crossover point still exists post-fix, not just to fail fast.
"""

import random
import warnings

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    mdl_score,
)


def _net(G, directed=False):
    net = multinet.multi_layer_network(directed=directed)
    net.core_network = G
    return net


def _dense_component(rng, prefix, n, density, directed):
    """An n-node block with each of the n*(n-1)[/2 if undirected] possible
    edges included independently with probability `density`. Unlike
    `_partial_dense_component` in test_mdl_score.py (a fixed ~62% density
    via a deterministic modulus rule), density is an explicit swept
    parameter here, including the exact 0.0 (empty block) and 1.0 (perfect
    clique) extremes that are the actual resolution-limit-triggering
    regime -- H(p) == 0 at both.
    """
    nodes = [(f"{prefix}{i}", "L") for i in range(n)]
    edges = []
    for i in range(n):
        for j in range(n):
            if i == j or (not directed and j < i):
                continue
            if rng.random() < density:
                edges.append((nodes[i], nodes[j]))
    return nodes, edges


def _build_two_block_graph(rng, n1, n2, d1, d2, directed):
    graph_cls = nx.DiGraph if directed else nx.Graph
    G = graph_cls()
    communities = []
    for prefix, n, d in (("a", n1, d1), ("b", n2, d2)):
        nodes, edges = _dense_component(rng, prefix, n, d, directed)
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        communities.append(nodes)
    ground_truth = {node: c for c, nodes in enumerate(communities) for node in nodes}
    return G, ground_truth, communities


def _full_singleton_partition(G):
    return {node: i for i, node in enumerate(G.nodes())}


def _partial_fragment(communities, k):
    """Split each ground-truth block into k roughly-equal sub-communities
    (rather than all the way down to singletons), so the sweep also covers
    intermediate over-fragmentation, not just the extreme case.
    """
    partition = {}
    next_id = 0
    for nodes in communities:
        chunk = max(1, len(nodes) // k)
        for i, node in enumerate(nodes):
            partition[node] = next_id + min(i // chunk, k - 1)
        next_id += k
    return partition


SIZES = [3, 4, 5, 6, 8, 10, 16, 24, 40, 60]
DENSITIES = [0.0, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 1.0]


def test_full_fragmentation_never_beats_ground_truth_across_size_and_density():
    violations = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for n in SIZES:
            for d in DENSITIES:
                rng = random.Random(f"reslim-sym-{n}-{d}")
                G, gt, _ = _build_two_block_graph(rng, n, n, d, d, directed=False)
                net = _net(G)
                gt_score = mdl_score(gt, net)
                frag_score = mdl_score(_full_singleton_partition(G), net)
                if not gt_score < frag_score:
                    violations.append((n, d, gt_score, frag_score))

    assert not violations, (
        f"ground truth lost to full fragmentation at {len(violations)} "
        f"(block_size, density, gt_score, fragmented_score) configs: {violations}"
    )


def test_partial_fragmentation_never_beats_ground_truth():
    violations = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for n in [8, 10, 16, 24, 32, 48]:
            for d in [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95]:
                rng = random.Random(f"reslim-partial-{n}-{d}")
                G, gt, communities = _build_two_block_graph(rng, n, n, d, d, directed=False)
                net = _net(G)
                gt_score = mdl_score(gt, net)
                for k in range(2, min(n, 10)):
                    partial_score = mdl_score(_partial_fragment(communities, k), net)
                    if not gt_score < partial_score:
                        violations.append((n, d, k, gt_score, partial_score))

    assert not violations, (
        f"ground truth lost to partial fragmentation at {len(violations)} "
        f"(block_size, density, k_sub_communities, gt_score, fragmented_score) "
        f"configs: {violations}"
    )


def test_asymmetric_blocks_and_directed_graphs_never_beat_ground_truth():
    violations = []
    size_pairs = [(5, 20), (8, 40), (3, 30), (10, 10), (15, 45)]
    density_pairs = [(0.9, 0.1), (0.1, 0.9), (0.5, 0.5), (0.05, 0.95), (1.0, 0.0)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for n1, n2 in size_pairs:
            for d1, d2 in density_pairs:
                for directed in (False, True):
                    rng = random.Random(f"reslim-asym-{n1}-{n2}-{d1}-{d2}-{directed}")
                    G, gt, _ = _build_two_block_graph(rng, n1, n2, d1, d2, directed)
                    net = _net(G, directed=directed)
                    gt_score = mdl_score(gt, net)
                    frag_score = mdl_score(_full_singleton_partition(G), net)
                    if not gt_score < frag_score:
                        violations.append((n1, n2, d1, d2, directed, gt_score, frag_score))

    assert not violations, (
        f"ground truth lost to fragmentation at {len(violations)} "
        f"(n1, n2, d1, d2, directed, gt_score, fragmented_score) configs: "
        f"{violations}"
    )
