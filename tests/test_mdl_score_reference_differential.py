"""Differential test: mdl_score vs. an independent, brute-force reference.

Purpose: validate that the implementation of mdl_score is correct, as
opposed to `mdl_benchmark.py` / `test_mdl_benchmark.py`, which check
whether mdl_score is a useful ranking signal on realistic (LFR) graphs.

The check here is a classic differential test: `reference_mdl_score`
below reimplements the same SBM two-part description length from the
docstring of `mdl_score` (multilayer_quality_metrics.py), independently
and deliberately naively -- most importantly, `_block_parameter_cost`'s
O(D^2) size-class-grouped computation of the per-block-pair parameter
cost is replaced here with a brute-force O(k^2) loop over every literal
community pair. If the grouping optimization is mathematically wrong (as
opposed to merely slow), this is what would catch it -- the existing
hand-computed cases in test_mdl_score.py already exercise small enough k
that D == k and the optimization is never actually exercised as an
optimization.

Both implementations are run on many randomly generated small multilayer
graphs and partitions (directed/undirected, single/multi-layer, with and
without parallel edges, with and without unassigned/dropped nodes) and
must agree to float tolerance on every one.
"""

import math
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

# Independent reference implementation.
# Deliberately does not import or call anything from
# multilayer_quality_metrics.py, so a bug shared between the two would have
# to be an independently-made identical mistake, not a shared helper.

def _reference_dedupe(edges, directed):
    seen = set()
    deduped = []
    for u, v in edges:
        key = (u, v) if directed else frozenset((u, v))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((u, v))
    return deduped


def _reference_block_capacity(n_r, n_s, same_block, directed):
    if same_block:
        return n_r * (n_r - 1) if directed else n_r * (n_r - 1) / 2
    return 2 * n_r * n_s if directed else n_r * n_s


def _reference_mdl_single_layer(layer_partition, layer_edges, directed, include_model_cost):
    communities = {}
    for node, comm in layer_partition.items():
        communities.setdefault(comm, []).append(node)

    k = len(communities)
    n = len(layer_partition)
    if k == 0 or n == 0:
        return 0.0

    sizes = {c: len(members) for c, members in communities.items()}
    comm_ids = list(communities.keys())

    model_cost = n * math.log2(k) if (include_model_cost and k > 1) else 0.0

    # Brute-force parameter cost: every unordered community pair (r, s),
    # including r == s, visited individually -- no size-class grouping.
    data_cost = 0.0
    for i, r in enumerate(comm_ids):
        for s in comm_ids[i:]:
            m_rs = _reference_block_capacity(sizes[r], sizes[s], r == s, directed)
            if m_rs > 0:
                data_cost += math.log2(m_rs + 1)

    deduped_edges = _reference_dedupe(layer_edges, directed)
    edge_counts = {}
    for u, v in deduped_edges:
        if u == v:
            continue
        r = layer_partition.get(u)
        s = layer_partition.get(v)
        if r is None or s is None:
            continue
        key = frozenset((r, s))
        edge_counts[key] = edge_counts.get(key, 0) + 1

    for pair, e_rs in edge_counts.items():
        if len(pair) == 1:
            (r,) = pair
            s = r
        else:
            r, s = tuple(pair)
        m_rs = _reference_block_capacity(sizes[r], sizes[s], r == s, directed)
        if m_rs == 0:
            continue
        p = min(e_rs / m_rs, 1.0)
        if 0.0 < p < 1.0:
            data_cost += m_rs * (-p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p))

    return model_cost + data_cost


def reference_mdl_score(partition, network):
    G = network.core_network
    all_nodes = set(G.nodes()) | set(partition.keys())
    if not all_nodes:
        return 0.0
    directed = G.is_directed()
    raw_edges = list(G.edges())

    def layer_of(node):
        return node[1] if isinstance(node, tuple) and len(node) >= 2 else None

    layer_partitions = {}
    for node in all_nodes:
        layer = layer_of(node)
        layer_partitions.setdefault(layer, {})
        layer_partitions[layer][node] = partition[node] if node in partition else object()

    layer_edges = {}
    inter_layer_edges = []
    for u, v in raw_edges:
        if layer_of(u) == layer_of(v):
            layer_edges.setdefault(layer_of(u), []).append((u, v))
        else:
            inter_layer_edges.append((u, v))

    total = 0.0
    global_partition = {}
    for layer, lpartition in layer_partitions.items():
        total += _reference_mdl_single_layer(lpartition, layer_edges.get(layer, []), directed, True)
        global_partition.update(lpartition)

    if inter_layer_edges:
        total += _reference_mdl_single_layer(global_partition, inter_layer_edges, directed, False)

    return total


# Sanity anchor: the reference must reproduce a hand-verified value before
# it's trusted as an oracle for the randomized sweep below.

def test_reference_matches_hand_verified_value():
    """Same fixture as test_mdl_score.py::test_single_layer_graph."""
    G = nx.Graph()
    G.add_edge(("A", "L"), ("B", "L"))
    G.add_edge(("C", "L"), ("D", "L"))
    net = _net(G)
    partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

    expected = 4.0 + 2 * math.log2(2) + math.log2(5)
    assert reference_mdl_score(partition, net) == pytest.approx(expected, abs=1e-6)


# Randomized graph/partition generation.

def _random_multilayer_graph(rng, n_base, layers, edge_prob, coupling_prob, directed, allow_multi):
    base_ids = [f"n{i}" for i in range(n_base)]
    nodes = [(b, l) for b in base_ids for l in layers if rng.random() < 0.85]
    if not nodes:
        nodes = [(base_ids[0], layers[0])]

    if directed:
        graph_cls = nx.MultiDiGraph if allow_multi else nx.DiGraph
    else:
        graph_cls = nx.MultiGraph if allow_multi else nx.Graph
    G = graph_cls()
    G.add_nodes_from(nodes)

    for layer in layers:
        layer_nodes = [nl for nl in nodes if nl[1] == layer]
        for i in range(len(layer_nodes)):
            for j in range(len(layer_nodes)):
                if i == j or (not directed and j < i):
                    continue
                if rng.random() < edge_prob:
                    G.add_edge(layer_nodes[i], layer_nodes[j])
                    if allow_multi and rng.random() < 0.25:
                        G.add_edge(layer_nodes[i], layer_nodes[j])

    for b in base_ids:
        replicas = [nl for nl in nodes if nl[0] == b]
        for i in range(len(replicas)):
            for j in range(i + 1, len(replicas)):
                if rng.random() < coupling_prob:
                    G.add_edge(replicas[i], replicas[j])
                    if directed and rng.random() < 0.5:
                        G.add_edge(replicas[j], replicas[i])

    return G, nodes


def _random_partition(rng, nodes, max_communities, drop_prob):
    partition = {}
    for nl in nodes:
        if rng.random() < drop_prob:
            continue
        partition[nl] = rng.randrange(max_communities)
    return partition


CONFIGS = [
    dict(directed=False, allow_multi=False, drop_prob=0.0),
    dict(directed=True, allow_multi=False, drop_prob=0.0),
    dict(directed=False, allow_multi=True, drop_prob=0.0),
    dict(directed=True, allow_multi=True, drop_prob=0.0),
    dict(directed=False, allow_multi=False, drop_prob=0.25),
    dict(directed=True, allow_multi=False, drop_prob=0.25),
]


@pytest.mark.parametrize(
    "config",
    CONFIGS,
    ids=[
        "undirected-simple",
        "directed-simple",
        "undirected-multigraph",
        "directed-multigraph",
        "undirected-partial-partition",
        "directed-partial-partition",
    ],
)
def test_matches_reference_on_random_graphs(config):
    seed = f"mdl-diff-{config}"
    rng = random.Random(seed)

    for trial in range(40):
        n_base = rng.randint(3, 8)
        n_layers = rng.randint(1, 3)
        layers = tuple(f"L{i}" for i in range(n_layers))
        edge_prob = rng.uniform(0.1, 0.6)
        coupling_prob = rng.uniform(0.0, 0.6) if n_layers > 1 else 0.0

        G, nodes = _random_multilayer_graph(
            rng,
            n_base=n_base,
            layers=layers,
            edge_prob=edge_prob,
            coupling_prob=coupling_prob,
            directed=config["directed"],
            allow_multi=config["allow_multi"],
        )
        max_communities = rng.randint(1, max(1, len(nodes)))
        partition = _random_partition(rng, nodes, max_communities, config["drop_prob"])
        net = _net(G, directed=config["directed"])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = mdl_score(partition, net)
            expected = reference_mdl_score(partition, net)

        assert got == pytest.approx(expected, rel=1e-9, abs=1e-9), (
            f"trial={trial} config={config} n_base={n_base} layers={layers} "
            f"edge_prob={edge_prob:.2f} coupling_prob={coupling_prob:.2f} "
            f"max_communities={max_communities} nodes={nodes} "
            f"partition={partition}"
        )