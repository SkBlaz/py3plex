"""Tests for mdl_score (Minimum Description Length quality metric).

mdl_score computes an SBM two-part description length for a multilayer
partition (lower is better).

- partial partitions: omitting hard nodes from a partition
  must not lower the score -- see TestMissingPartitionNodes.
- inter-layer edges: cross-layer/coupling edges must be
  scored, not ignored -- see TestInterLayerEdges.
- parallel/weighted edges: multi-edges and edge weight
  magnitude are collapsed/ignored explicitly (not silently clamped), and
  disclosed via a warning -- see TestParallelAndWeightedEdges.
- performance: the data-cost loop is O(n + |E|), not
  quadratic in the number of communities, even under extreme
  fragmentation -- see TestPerformance.
- baseline coverage: empty partitions, single-layer graphs,
  multi-layer graphs, directed graphs, singleton communities, missing
  partition nodes, inter-layer edges, plus additional cases (self-loops,
  determinism, score quality, duck-typed network inputs) judged necessary
  for a metric this easy to silently break.
"""

import time
import warnings

import networkx as nx
import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    mdl_score,
)


def _net(G, directed=False):
    """Build a multi_layer_network wrapping a prebuilt networkx graph."""
    net = multinet.multi_layer_network(directed=directed)
    net.core_network = G
    return net


class TestEmptyPartitions:

    def test_empty_partition_and_empty_network(self):
        """No partition, no network content = 0.0, no warning."""
        net = multinet.multi_layer_network(directed=False)
        assert mdl_score({}, net) == 0.0

    def test_empty_partition_nonempty_network_warns(self):
        """Empty partition but the network has nodes: every node becomes
        its own singleton community and a partial-partition warning fires.
        """
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        net = _net(G)

        with pytest.warns(UserWarning, match="Partition covers 0 of"):
            score = mdl_score({}, net)
        assert score >= 0.0

    def test_empty_partition_none_core_network(self):
        """A network whose core_network was never populated (stays None)
        combined with an empty partition returns 0.0."""
        net = multinet.multi_layer_network(directed=False)
        assert net.core_network is None
        assert mdl_score({}, net) == 0.0


class TestSingleAndMultiLayerGraphs:
    """Single-layer and multi-layer graphs."""

    def test_single_layer_graph(self):
        """Perfect 2-community split on one layer scores a known value."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        score = mdl_score(partition, net)
        assert score == pytest.approx(4.0, abs=1e-6)

    def test_multi_layer_independent_layers_sum_exactly(self):
        """Two structurally identical layers with no coupling edges score
        exactly 2x a single layer's score: layers are scored independently
        and summed, with no spurious inter-layer term when there are no
        cross-layer edges (contrast with TestInterLayerEdges, where coupling
        edges are present and do add a term).
        """
        G1 = nx.Graph()
        G1.add_edge(("A", "L1"), ("B", "L1"))
        G1.add_edge(("C", "L1"), ("D", "L1"))
        p1 = {("A", "L1"): 0, ("B", "L1"): 0, ("C", "L1"): 1, ("D", "L1"): 1}
        single_score = mdl_score(p1, _net(G1))

        G2 = nx.Graph()
        partition2 = {}
        for layer in ("L1", "L2"):
            G2.add_edge(("A", layer), ("B", layer))
            G2.add_edge(("C", layer), ("D", layer))
            partition2[("A", layer)] = 0
            partition2[("B", layer)] = 0
            partition2[("C", layer)] = 1
            partition2[("D", layer)] = 1
        multi_score = mdl_score(partition2, _net(G2))

        assert multi_score == pytest.approx(2 * single_score, rel=1e-9)

    def test_multi_layer_different_partitions_per_layer(self):
        """Layers may have completely different community counts/labels
        without crashing or interfering with each other's scoring."""
        G = nx.Graph()
        G.add_edge(("A", "L1"), ("B", "L1"))
        G.add_edge(("C", "L2"), ("D", "L2"))
        G.add_edge(("D", "L2"), ("E", "L2"))
        net = _net(G)
        partition = {
            ("A", "L1"): 0, ("B", "L1"): 0,
            ("C", "L2"): 0, ("D", "L2"): 1, ("E", "L2"): 2,
        }

        score = mdl_score(partition, net)
        assert np.isfinite(score)
        assert score >= 0.0


class TestDirectedGraphs:
    """Directed graphs."""

    def test_directed_graph_uses_directed_capacity(self):
        """Directed and undirected scores differ on identical
        edges/partition, confirming the directed capacity branch (doubled
        off-diagonal, n*(n-1) on-diagonal) is actually used."""
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        Gd = nx.DiGraph()
        Gd.add_edge(("A", "L"), ("B", "L"))
        Gd.add_edge(("C", "L"), ("D", "L"))
        directed_score = mdl_score(partition, _net(Gd, directed=True))

        Gu = nx.Graph()
        Gu.add_edge(("A", "L"), ("B", "L"))
        Gu.add_edge(("C", "L"), ("D", "L"))
        undirected_score = mdl_score(partition, _net(Gu, directed=False))

        assert directed_score == pytest.approx(8.0, abs=1e-6)
        assert undirected_score == pytest.approx(4.0, abs=1e-6)
        assert directed_score != undirected_score

    def test_directed_multigraph_parallel_edges(self):
        """A directed MultiDiGraph with parallel directed edges collapses
        correctly (ordered dedup key, not frozenset) and warns without
        crashing or producing nan."""
        G = nx.MultiDiGraph()
        for _ in range(5):
            G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G, directed=True)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        with pytest.warns(UserWarning):
            score = mdl_score(partition, net)
        assert score == pytest.approx(8.0, abs=1e-6)
        assert np.isfinite(score)


class TestSingletonCommunities:
    """Singleton communities."""

    def test_singleton_communities_no_crash(self):
        """Every node in its own community should not crash and stays
        finite even with fully fragmented input."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("B", "L"), ("C", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 1, ("C", "L"): 2, ("D", "L"): 3}

        score = mdl_score(partition, net)
        assert np.isfinite(score)
        assert score == pytest.approx(8.0, abs=1e-6)

    def test_non_orderable_community_ids(self):
        """Community ids need only be hashable, not orderable -- using
        plain (non-orderable) objects as labels must not crash the
        frozenset-keyed block-pair counting."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        net = _net(G)
        c0, c1 = object(), object()
        partition = {("A", "L"): c0, ("B", "L"): c1}

        score = mdl_score(partition, net)
        assert np.isfinite(score)
        assert score >= 0.0


class TestMissingPartitionNodes:
    """Regression: partial partitions can't be gamed by
    omitting hard nodes."""

    def test_missing_partition_nodes_cannot_lower_score(self):
        """Omitting hard nodes from the partition must not lower the score
        below what the full partition gets."""
        G = nx.Graph()
        for u, v in [("A", "B"), ("B", "C"), ("C", "A"),
                     ("D", "E"), ("E", "F"), ("F", "D"), ("A", "D")]:
            G.add_edge((u, "L"), (v, "L"))
        net = _net(G)

        full = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 0,
                 ("D", "L"): 1, ("E", "L"): 1, ("F", "L"): 1}
        partial = {k: v for k, v in full.items() if k != ("F", "L")}

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            full_score = mdl_score(full, net)
            partial_score = mdl_score(partial, net)

        assert partial_score >= full_score

    def test_missing_partition_nodes_warns_with_counts(self):
        """Partial partitions emit exactly one warning naming the exact
        coverage counts."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("B", "L"), ("C", "L"))
        net = _net(G)
        partial = {("A", "L"): 0, ("B", "L"): 0}  # "C" omitted

        with pytest.warns(UserWarning, match=r"Partition covers 2 of 3"):
            mdl_score(partial, net)

    def test_fully_covered_partition_does_not_warn_about_coverage(self):
        """No partial-partition warning when every network node is
        assigned."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        net = _net(G)
        full = {("A", "L"): 0, ("B", "L"): 1}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mdl_score(full, net)
        assert not any("Partition covers" in str(w.message) for w in caught)


class TestInterLayerEdges:
    """Regression: inter-layer (coupling) edges are scored,
    not ignored."""

    def test_inter_layer_edges_penalize_replica_inconsistency(self):
        """With identical intra-layer structure, a replica-consistent
        partition must score lower than an inconsistent one once coupling
        edges are present."""
        G = nx.Graph()
        for layer in ("L1", "L2"):
            G.add_edge(("A", layer), ("B", layer))
            G.add_edge(("C", layer), ("D", layer))
        for node in ("A", "B", "C", "D"):
            G.add_edge((node, "L1"), (node, "L2"))
        net = _net(G)

        consistent = {}
        for layer in ("L1", "L2"):
            consistent[("A", layer)] = 0
            consistent[("B", layer)] = 0
            consistent[("C", layer)] = 1
            consistent[("D", layer)] = 1
        inconsistent = dict(consistent)
        inconsistent[("A", "L2")] = 1
        inconsistent[("B", "L2")] = 1
        inconsistent[("C", "L2")] = 0
        inconsistent[("D", "L2")] = 0

        consistent_score = mdl_score(consistent, net)
        inconsistent_score = mdl_score(inconsistent, net)
        assert consistent_score < inconsistent_score

    def test_inter_layer_edges_add_cost_over_no_coupling(self):
        """Adding coupling edges on top of an otherwise-identical network
        cannot decrease the score: the inter-layer term is purely additive
        (zero when there are no cross-layer edges, a non-negative binary
        entropy term otherwise) and never revisits the intra-layer terms.
        """
        G_no_coupling = nx.Graph()
        for layer in ("L1", "L2"):
            G_no_coupling.add_edge(("A", layer), ("B", layer))
        partition = {
            ("A", "L1"): 0, ("B", "L1"): 0,
            ("A", "L2"): 0, ("B", "L2"): 0,
        }
        score_no_coupling = mdl_score(partition, _net(G_no_coupling))

        G_coupling = nx.Graph(G_no_coupling)
        G_coupling.add_edge(("A", "L1"), ("A", "L2"))
        G_coupling.add_edge(("B", "L1"), ("B", "L2"))
        score_with_coupling = mdl_score(partition, _net(G_coupling))

        assert score_with_coupling >= score_no_coupling

    def test_no_inter_layer_edges_means_no_inter_layer_term(self):
        """Two disconnected single-node-pair layers (no coupling at all)
        must score identically to summing each layer's score alone --
        i.e. the inter-layer branch is skipped entirely, not charged as
        zero-cost work that could hide a latent bug."""
        G = nx.Graph()
        G.add_edge(("A", "L1"), ("B", "L1"))
        G.add_edge(("C", "L2"), ("D", "L2"))
        net = _net(G)
        partition = {
            ("A", "L1"): 0, ("B", "L1"): 0,
            ("C", "L2"): 0, ("D", "L2"): 0,
        }

        score = mdl_score(partition, net)

        G1 = nx.Graph()
        G1.add_edge(("A", "L1"), ("B", "L1"))
        score1 = mdl_score({("A", "L1"): 0, ("B", "L1"): 0}, _net(G1))

        G2 = nx.Graph()
        G2.add_edge(("C", "L2"), ("D", "L2"))
        score2 = mdl_score({("C", "L2"): 0, ("D", "L2"): 0}, _net(G2))

        assert score == pytest.approx(score1 + score2, rel=1e-9)


class TestParallelAndWeightedEdges:
    """Regression: parallel/weighted edges are collapsed
    explicitly and disclosed via a warning, never silently clamped."""

    def test_parallel_edges_collapse_to_same_score_as_simple_graph(self):
        """A MultiGraph with 10 parallel edges between the same pair scores
        identically to a simple graph with 1 edge there -- multiplicity is
        discarded by design, not silently corrupted via clamping to
        density 1.0."""
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        Gm = nx.MultiGraph()
        for _ in range(10):
            Gm.add_edge(("A", "L"), ("B", "L"))
        Gm.add_edge(("C", "L"), ("D", "L"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            multigraph_score = mdl_score(partition, _net(Gm))

        Gs = nx.Graph()
        Gs.add_edge(("A", "L"), ("B", "L"))
        Gs.add_edge(("C", "L"), ("D", "L"))
        simple_score = mdl_score(partition, _net(Gs))

        assert np.isfinite(multigraph_score)  # never nan from p > 1
        assert multigraph_score == simple_score

    def test_parallel_edges_warn(self):
        """A MultiGraph with actual parallel edges triggers the
        disclosure warning."""
        G = nx.MultiGraph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("A", "L"), ("B", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 1}

        with pytest.warns(UserWarning, match="parallel edges"):
            mdl_score(partition, net)

    def test_weighted_edges_ignored_matches_unweighted_score(self):
        """Edge weight magnitude does not affect the score -- only
        presence/absence per node pair is modeled."""
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        Gw = nx.Graph()
        Gw.add_edge(("A", "L"), ("B", "L"), weight=100)
        Gw.add_edge(("C", "L"), ("D", "L"), weight=0.5)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            weighted_score = mdl_score(partition, _net(Gw))

        Gs = nx.Graph()
        Gs.add_edge(("A", "L"), ("B", "L"))
        Gs.add_edge(("C", "L"), ("D", "L"))
        unweighted_score = mdl_score(partition, _net(Gs))

        assert weighted_score == unweighted_score

    def test_weighted_edges_warn(self):
        """Non-unit edge weights trigger the disclosure warning."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"), weight=5)
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 1}

        with pytest.warns(UserWarning, match="weight"):
            mdl_score(partition, net)

    def test_unit_weight_does_not_warn(self):
        """An explicit weight=1 is not 'non-unit' and should not warn --
        this metric's notion of 'weighted' is narrower than
        network.capabilities()'s ('any weight key present'), and that's
        intentional: weight=1 everywhere is indistinguishable from
        unweighted under this metric's Bernoulli model."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"), weight=1)
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 1}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mdl_score(partition, net)
        assert len(caught) == 0

    def test_plain_simple_graph_never_warns(self):
        """No false-positive warnings for an ordinary unweighted,
        non-multi graph -- the common case."""
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mdl_score(partition, net)
        assert len(caught) == 0

    def test_multigraph_container_without_actual_parallel_edges_does_not_warn(self):
        """A MultiGraph-typed container with no actual duplicate edges is
        the common case (py3plex's default container type) and must not
        false-positive the warning."""
        G = nx.MultiGraph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mdl_score(partition, net)
        assert len(caught) == 0


class TestSelfLoops:
    """Self-loops must not crash and must not be counted -- they don't fit
    the n_r*(n_r-1) pair capacity model."""

    def test_self_loop_ignored(self):
        G_no_loop = nx.Graph()
        G_no_loop.add_edge(("A", "L"), ("B", "L"))
        G_no_loop.add_edge(("C", "L"), ("D", "L"))
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}
        score_no_loop = mdl_score(partition, _net(G_no_loop))

        G_with_loop = nx.Graph(G_no_loop)
        G_with_loop.add_edge(("A", "L"), ("A", "L"))
        score_with_loop = mdl_score(partition, _net(G_with_loop))

        assert score_with_loop == score_no_loop


class TestDeterminism:
    """Repeated calls must be bit-identical --
    this is a pure computation with no randomness."""

    def test_repeated_calls_identical(self):
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}

        scores = [mdl_score(partition, net) for _ in range(5)]
        assert len(set(scores)) == 1


class TestScoreQuality:
    """Sanity check that mdl_score actually
    rewards better partitions -- otherwise none of the other correctness
    guarantees above matter."""

    def test_true_structure_scores_lower_than_giant_community(self):
        G = nx.Graph()
        G.add_edge(("A", "L"), ("B", "L"))
        G.add_edge(("C", "L"), ("D", "L"))
        net = _net(G)

        true_partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}
        giant_partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 0, ("D", "L"): 0}

        assert mdl_score(true_partition, net) < mdl_score(giant_partition, net)


class TestNetworkInputVariants:
    """Duck-typed / partially-populated network
    objects, since mdl_score's `network` parameter is typed `Any`."""

    def test_network_object_without_core_network_attribute(self):
        """A duck-typed network object with no core_network attribute at
        all falls back gracefully via getattr's default."""
        class BareNetwork:
            pass

        partition = {("A", "L"): 0, ("B", "L"): 1}
        score = mdl_score(partition, BareNetwork())
        assert score == pytest.approx(2.0, abs=1e-6)

    def test_network_with_none_core_network(self):
        """A real multi_layer_network whose core_network was never
        populated behaves the same as the duck-typed case above."""
        net = multinet.multi_layer_network(directed=False)
        assert net.core_network is None
        partition = {("A", "L"): 0, ("B", "L"): 1}
        score = mdl_score(partition, net)
        assert score == pytest.approx(2.0, abs=1e-6)


class TestPerformance:
    """Regression: the data-cost loop is O(n + |E|), not
    quadratic in the number of communities, even under extreme
    fragmentation (many singleton communities)."""

    def test_no_quadratic_blowup_mdl_fragmented(self):
        """mdl_score should stay near-linear even with many singleton
        communities, not quadratic in the number of communities per layer.

        _mdl_single_layer's data cost loop iterates over observed block
        pairs (`edge_counts`), not over all k^2 community pairs, so cost
        tracks O(n + |E|) rather than O(k^2). Extreme fragmentation (every
        node its own community, as an AutoCommunity algorithm might produce
        for a partial/degenerate partition) maximizes k without blowing up
        |E| -- this is exactly the scenario a regression to a k^2 nested
        loop over communities would fail on.
        """
        n = 5000
        nodes = [(f"node_{i}", "layer_0") for i in range(n)]

        # Sparse, deterministic edge set (a cycle): O(n) edges, and since
        # every node is its own community, each edge lands on a distinct
        # community pair -- the worst case for the number of block pairs
        # relative to node count.
        G = nx.Graph()
        G.add_nodes_from(nodes)
        for i in range(n):
            G.add_edge(nodes[i], nodes[(i + 1) % n])

        net = _net(G)

        # Every node in its own singleton community (maximal fragmentation).
        partition = {node: i for i, node in enumerate(nodes)}

        # Partition covers every node on a plain (non-multi, unweighted)
        # graph, so none of mdl_score's warning paths (partial partition,
        # parallel/weighted edges) should fire here.
        start = time.time()
        score = mdl_score(partition, net)
        elapsed = time.time() - start

        # Should complete in reasonable time despite k == n.
        assert elapsed < 2.0
        assert score >= 0.0

    @pytest.mark.slow
    def test_no_quadratic_blowup_mdl_large_scale(self):
        """mdl_score should stay near-linear at ~2M nodes, not just at the
        smaller scale in test_no_quadratic_blowup_mdl_fragmented.

        Marked slow: builds a 2,000,000-node graph and runs the full
        mdl_score computation. Measured ~8s / ~3GB peak RSS on a dev
        machine; a regression to a quadratic-in-communities loop would
        take minutes rather than tens of seconds at this scale. Skip via
        `pytest -m "not slow"` for a fast local/CI run.
        """
        n = 2_000_000
        nodes = [(f"node_{i}", "layer_0") for i in range(n)]

        G = nx.Graph()
        G.add_nodes_from(nodes)
        for i in range(n):
            G.add_edge(nodes[i], nodes[(i + 1) % n])

        net = _net(G)

        # Worst case for _mdl_single_layer's block-pair counting: every
        # node is its own singleton community, maximizing k without
        # increasing |E|.
        partition = {node: i for i, node in enumerate(nodes)}

        start = time.time()
        score = mdl_score(partition, net)
        elapsed = time.time() - start

        # Generous bound to absorb slower/loaded CI hardware while still
        # catching a real regression to quadratic-in-communities behavior.
        assert elapsed < 60.0
        assert score >= 0.0