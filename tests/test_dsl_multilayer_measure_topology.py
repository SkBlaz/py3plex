"""Tests for measure-computation topology resolution on multilayer networks.

Covers the fix for a silent single-layer/intralayer projection bias in
py3plex/dsl/executor.py: measure functions (degree, betweenness, ...) used to
be computed on a subgraph induced from the query's already
WHERE/coverage/limit-narrowed item list, which silently dropped interlayer
coupling edges and could disagree with predicates evaluated against the full
graph.

Verifies:
- degree/degree_centrality default to "aggregate" (coupling-aware, full
  graph) on multilayer networks, matching the documented (but previously
  unimplemented) intent in warnings.warn_degree_ambiguity
- kind="intra" opts into the old (pre-fix) intralayer-only behavior
- WHERE-filter narrowing no longer shrinks the topology a measure is
  computed on (the "self-contradiction" bug)
- non-degree measures (betweenness) keep from_layers()-restricts-topology
  behavior unchanged, per the community-detection precedent already
  documented in warnings.warn_global_community_detection
- fastpath and slowpath agree on degree values
- the implicit autocompute path (_ensure_attribute) and explicit .compute()
  do not silently diverge
- bootstrap UQ uses the same (fixed) topology as the deterministic path
- the newly-wired MultilayerSemanticWarning functions actually fire
"""

import os
import warnings

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.datasets import load_aarhus_cs
from py3plex.dsl import Q, L
from py3plex.dsl.warnings import MultilayerSemanticWarning, suppress_warnings
from py3plex.utils import get_multilayer_dataset_path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def coupled_multiplex_net():
    """Multiplex network: A-B edge in 'social', identity coupling to 'work'.

    social layer: A-B edge (intralayer)
    work layer: no intralayer edges
    coupling: (A,social)-(A,work) and (B,social)-(B,work), via
    _couple_all_edges() (identity coupling for multiplex networks).

    So on the full graph: A and B each have degree 3 (1 intralayer + 2
    coupling edges, since coupling connects every pair of layers for the
    same node -- here just social<->work, so 1 coupling edge each).
    Intralayer-only degree (kind="intra") for social: A=1, B=1.
    """
    net = multinet.multi_layer_network(directed=False, network_type="multiplex")
    net.add_nodes([
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "A", "type": "work"},
        {"source": "B", "type": "work"},
    ])
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
    ])
    net._couple_all_edges()
    return net


# ---------------------------------------------------------------------------
# Rule 2: degree family defaults to aggregate on multilayer networks
# ---------------------------------------------------------------------------

def test_degree_aggregate_by_default_on_multiplex(coupled_multiplex_net):
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        social_only = Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)
        all_layers = Q.nodes().from_layers(L["*"]).compute("degree").execute(coupled_multiplex_net)

    social_degrees = social_only.attributes["degree"]
    all_degrees = all_layers.attributes["degree"]

    assert social_degrees[("A", "social")] == 3
    assert social_degrees[("B", "social")] == 3
    # Same rows, same values regardless of the layer filter -- aggregate
    # degree is coupling-aware and does not depend on from_layers().
    assert social_degrees[("A", "social")] == all_degrees[("A", "social")]
    assert social_degrees[("B", "social")] == all_degrees[("B", "social")]


def test_degree_kind_intra_opts_into_old_behavior(coupled_multiplex_net):
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        result = Q.nodes().from_layers(L["social"]).compute("degree", kind="intra").execute(coupled_multiplex_net)

    degrees = result.attributes["degree"]
    # Pins down the pre-fix numbers explicitly: intralayer-only degree,
    # ignoring coupling edges.
    assert degrees[("A", "social")] == 1
    assert degrees[("B", "social")] == 1


# ---------------------------------------------------------------------------
# Rule 1: WHERE filtering must not shrink measure topology
# ---------------------------------------------------------------------------

def test_where_filter_does_not_shrink_measure_topology(coupled_multiplex_net):
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .where(degree__gt=2)
            .compute("degree")
            .execute(coupled_multiplex_net)
        )

    # Both A and B have aggregate degree 3, so both should survive the
    # degree > 2 filter, and the displayed degree column must agree with
    # the predicate that selected them (no self-contradiction).
    assert set(result.items) == {("A", "social"), ("B", "social")}
    for node in result.items:
        assert result.attributes["degree"][node] == 3


def test_betweenness_respects_from_layers_restriction_unchanged(coupled_multiplex_net):
    with suppress_warnings("node_replica_confusion"):
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("betweenness_centrality")
            .execute(coupled_multiplex_net)
        )

    social_subgraph = nx.Graph()
    social_subgraph.add_nodes_from([("A", "social"), ("B", "social")])
    social_subgraph.add_edge(("A", "social"), ("B", "social"))
    expected = nx.betweenness_centrality(social_subgraph)

    for node, value in expected.items():
        assert result.attributes["betweenness_centrality"][node] == pytest.approx(value)


def test_where_filter_does_not_shrink_betweenness_topology(coupled_multiplex_net):
    with suppress_warnings("node_replica_confusion"):
        no_filter = Q.nodes().from_layers(L["*"]).compute("betweenness_centrality").execute(coupled_multiplex_net)
        filtered = (
            Q.nodes()
            .from_layers(L["*"])
            .where(degree__gt=0)
            .compute("betweenness_centrality")
            .execute(coupled_multiplex_net)
        )

    for node in filtered.items:
        assert filtered.attributes["betweenness_centrality"][node] == pytest.approx(
            no_filter.attributes["betweenness_centrality"][node]
        )


# ---------------------------------------------------------------------------
# fastpath vs slowpath consistency
# ---------------------------------------------------------------------------

def test_fastpath_and_slowpath_degree_agree(coupled_multiplex_net):
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        # Simple equality-style layer filter: eligible for the fastpath index.
        fast = Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)
        # A WHERE clause on a computed attribute forces the slow path.
        slow = (
            Q.nodes()
            .from_layers(L["social"])
            .where(degree__gt=0)
            .compute("degree")
            .execute(coupled_multiplex_net)
        )

    for node in slow.items:
        assert slow.attributes["degree"][node] == fast.attributes["degree"][node]


# ---------------------------------------------------------------------------
# Implicit autocompute vs explicit compute
# ---------------------------------------------------------------------------

def test_ensure_attribute_autocompute_matches_explicit_compute(coupled_multiplex_net):
    """The implicit autocompute path (_ensure_attribute, used to evaluate a
    bare WHERE predicate like degree__gt=2) must select the same rows that
    filtering an explicitly-.compute()d "degree" column the same way would
    -- i.e. both call sites must resolve the same topology.
    """
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        implicit = Q.nodes().from_layers(L["social"]).where(degree__gt=2).execute(coupled_multiplex_net)
        explicit = Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)

    explicit_matches = {node for node, deg in explicit.attributes["degree"].items() if deg > 2}
    assert set(implicit.items) == explicit_matches


# ---------------------------------------------------------------------------
# UQ / bootstrap interaction
# ---------------------------------------------------------------------------

def test_uq_wrapper_uses_full_topology_for_degree(coupled_multiplex_net):
    """The UQ resampling wrapper (metric_fn_wrapper inside
    _compute_measure_with_uncertainty) must resolve the same layer scope as
    the deterministic path, not re-induce its own subgraph from `items`.

    Uses method="seed" rather than "bootstrap": bootstrap's edge-resampling
    engine (py3plex/uncertainty/bootstrap.py:_resample_edges) has a separate,
    pre-existing bug where it unpacks graph.get_edges(data=True) assuming
    3-tuples, but MultiGraph-backed networks (which multi_layer_network
    always uses) return 4-tuples (u, v, key, data) -- so every edge is
    silently dropped and bootstrap-degree is always 0 regardless of this
    fix. That bug lives outside py3plex/dsl/executor.py and is out of scope
    here; method="seed" exercises the same metric_fn_wrapper/topology-scope
    code path without depending on that separate engine.
    """
    with suppress_warnings("degree_ambiguity", "node_replica_confusion", "high_uq_samples"):
        deterministic = Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)
        uq_result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree", uncertainty=True, method="seed", n_samples=5, random_state=0)
            .execute(coupled_multiplex_net)
        )

    det_degrees = deterministic.attributes["degree"]
    uq_degrees = uq_result.attributes["degree"]
    for node in det_degrees:
        mean = uq_degrees[node]["mean"] if isinstance(uq_degrees[node], dict) else uq_degrees[node]
        assert mean == pytest.approx(det_degrees[node], abs=1.0)


# ---------------------------------------------------------------------------
# Warning wiring
# ---------------------------------------------------------------------------

def test_degree_ambiguity_warning_fires_on_multiplex_default(coupled_multiplex_net):
    with suppress_warnings("node_replica_confusion"):
        with pytest.warns(MultilayerSemanticWarning):
            Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)


def test_degree_ambiguity_warning_suppressed_by_context_manager(coupled_multiplex_net):
    with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
        with warnings.catch_warnings():
            warnings.simplefilter("error", MultilayerSemanticWarning)
            # Should not raise: both warnings are suppressed via the context manager.
            Q.nodes().from_layers(L["social"]).compute("degree").execute(coupled_multiplex_net)


# ---------------------------------------------------------------------------
# Real bundled dataset: Aarhus CS department multiplex social network
# (61 people, 5 layers: coauthor, facebook, leisure, lunch, work; real
# identity-coupling edges auto-generated since it's loaded as network_type=
# "multiplex"). See py3plex.datasets.load_aarhus_cs.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def aarhus_net():
    return load_aarhus_cs()


class TestAarhusRealDataset:
    """Same fix, exercised against a real, published multiplex dataset
    instead of a small hand-built fixture. This is also the test that caught
    a real bug: is_multilayer detection originally used
    network.capabilities(), which raises on this dataset (mixed str/int edge
    weights) and, via the surrounding try/except, silently fell back to
    "not multilayer" -- meaning the aggregate-degree fix never activated on
    real data despite passing every synthetic-fixture test. Fixed by
    switching the check to network.layer_count instead.
    """

    def test_capabilities_call_does_not_crash_the_query(self, aarhus_net):
        # network.capabilities() itself has a separate, pre-existing bug on
        # this dataset (TypeError comparing str and int weights) -- this
        # just documents that the DSL query path no longer depends on it
        # succeeding.
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            result = Q.nodes().from_layers(L["lunch"]).compute("degree").execute(aarhus_net)
        assert len(result.items) > 0

    def test_aggregate_degree_matches_full_graph_on_real_data(self, aarhus_net):
        G = aarhus_net.core_network
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            result = Q.nodes().from_layers(L["lunch"]).compute("degree").execute(aarhus_net)

        degrees = result.attributes["degree"]
        # Spot-check a handful of real nodes against a plain networkx degree
        # count on the full graph (independently computed, not via the DSL).
        for node_id in ["1", "10", "25"]:
            node = (node_id, "lunch")
            assert degrees[node] == G.degree(node)

    def test_intra_degree_excludes_coupling_edges_on_real_data(self, aarhus_net):
        G = aarhus_net.core_network
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            result = Q.nodes().from_layers(L["lunch"]).compute("degree", kind="intra").execute(aarhus_net)

        degrees = result.attributes["degree"]
        for node_id in ["1", "10", "25"]:
            node = (node_id, "lunch")
            expected_intra = len(
                [e for e in G.edges(node, data=True) if e[2].get("type") != "coupling"]
            )
            assert degrees[node] == expected_intra
            # Sanity check the fixture actually has coupling edges to strip,
            # otherwise this test wouldn't be able to tell the two kinds apart.
            assert degrees[node] < G.degree(node)

    def test_where_filter_does_not_shrink_topology_on_real_data(self, aarhus_net):
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            filtered = (
                Q.nodes()
                .from_layers(L["work"])
                .where(degree__gt=10)
                .compute("degree")
                .execute(aarhus_net)
            )
        # Every row that survived the filter must show a degree consistent
        # with the predicate that selected it (no self-contradiction).
        for node in filtered.items:
            assert filtered.attributes["degree"][node] > 10

    def test_fastpath_and_slowpath_agree_on_real_data(self, aarhus_net):
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            fast = Q.nodes().from_layers(L["facebook"]).compute("degree").execute(aarhus_net)
            slow = (
                Q.nodes()
                .from_layers(L["facebook"])
                .where(degree__gt=0)
                .compute("degree")
                .execute(aarhus_net)
            )
        fast_degrees = fast.attributes["degree"]
        slow_degrees = slow.attributes["degree"]
        for node in slow.items:
            assert slow_degrees[node] == fast_degrees[node]

    def test_aggregate_degree_always_at_least_intra_degree(self, aarhus_net):
        # Aggregate degree for a given layer-replica = that replica's own
        # intralayer edges + its coupling edges to the person's other-layer
        # replicas. It is NOT the same number across a person's 5 replicas
        # (each layer has a different intralayer edge count) -- but it must
        # never be *less* than the intra-only count for that same replica,
        # since aggregate strictly adds coupling edges on top, never removes
        # intralayer ones.
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            aggregate = {
                layer: Q.nodes().from_layers(L[layer]).compute("degree").execute(aarhus_net).attributes["degree"]
                for layer in aarhus_net.layers
            }
            intra = {
                layer: Q.nodes().from_layers(L[layer]).compute("degree", kind="intra").execute(aarhus_net).attributes["degree"]
                for layer in aarhus_net.layers
            }

        G = aarhus_net.core_network
        for node_id in ["1", "10", "25"]:
            for layer in aarhus_net.layers:
                node = (node_id, layer)
                if node not in G:
                    continue
                assert aggregate[layer][node] >= intra[layer][node]


# ---------------------------------------------------------------------------
# A second, larger real dataset: a real (not synthetic) sample of the
# MLKing2013 Twitter multiplex network (retweet/mention/reply layers around
# a 2013 hashtag). The full file is ~328k users / 397k edges -- too large
# for a quick test, so a genuine sample (same real edges, bounded count per
# layer) is loaded instead. This scale is what originally caught bug #8:
# network.get_layers() being called on the query-caching hot path, turning
# every query into a multi-minute force-directed layout computation.
# ---------------------------------------------------------------------------

_MLKING_LAYER_NAMES = {"1": "RT", "2": "MT", "3": "RE"}
_MLKING_PER_LAYER_LIMIT = 3000


@pytest.fixture(scope="module")
def mlking_sample_net():
    edges_path = get_multilayer_dataset_path("MLKing/MLKing2013_multiplex.edges")
    if not os.path.exists(edges_path):
        pytest.skip(f"MLKing dataset not available at {edges_path}")

    counts = {k: 0 for k in _MLKING_LAYER_NAMES}
    edges = []
    with open(edges_path) as f:
        for line in f:
            parts = line.split()
            if len(parts) != 4:
                continue
            layer_id, u, v, w = parts
            if layer_id not in counts or counts[layer_id] >= _MLKING_PER_LAYER_LIMIT:
                continue
            counts[layer_id] += 1
            layer = _MLKING_LAYER_NAMES[layer_id]
            edges.append({
                "source": u, "target": v,
                "source_type": layer, "target_type": layer,
                "weight": float(w),
            })
            if all(c >= _MLKING_PER_LAYER_LIMIT for c in counts.values()):
                break

    net = multinet.multi_layer_network(directed=False, network_type="multiplex", verbose=False)
    net.add_edges(edges, input_type="dict")
    net._couple_all_edges()
    return net


class TestMLKingRealDataset:
    """A second, independent real dataset, at a larger scale than Aarhus.
    Mainly a regression guard for bug #8 (network.get_layers() on the query
    caching hot path) -- these tests would take many minutes (or effectively
    hang) if that regressed, rather than just producing a wrong number.
    """

    def test_query_completes_and_matches_full_graph_degree(self, mlking_sample_net):
        net = mlking_sample_net
        G = net.core_network
        assert net.layer_count == 3

        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            result = Q.nodes().from_layers(L["RT"]).compute("degree").execute(net)

        degrees = result.attributes["degree"]
        mismatches = [n for n in list(result.items)[:1000] if degrees[n] != G.degree(n)]
        assert mismatches == []

    def test_intra_degree_differs_from_aggregate_where_coupled(self, mlking_sample_net):
        net = mlking_sample_net
        G = net.core_network

        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            intra = Q.nodes().from_layers(L["RT"]).compute("degree", kind="intra").execute(net)

        intra_degrees = intra.attributes["degree"]
        differing = sum(
            1 for n in list(intra_degrees)[:1000] if intra_degrees[n] != G.degree(n)
        )
        # Most sampled users should have at least one coupling edge to
        # another layer, so most should differ between intra and aggregate.
        assert differing > 0

    def test_where_filter_stays_consistent_on_larger_real_data(self, mlking_sample_net):
        with suppress_warnings("degree_ambiguity", "node_replica_confusion"):
            filtered = (
                Q.nodes()
                .from_layers(L["RT"])
                .where(degree__gt=20)
                .compute("degree")
                .execute(mlking_sample_net)
            )
        for node in filtered.items:
            assert filtered.attributes["degree"][node] > 20
