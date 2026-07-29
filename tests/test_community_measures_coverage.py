"""Tests for community_measures.py and sbm_metrics.py to improve coverage."""

import networkx as nx
import numpy as np
import pytest

from py3plex.algorithms.community_detection.community_measures import (
    modularity,
    number_of_communities,
    size_distribution,
)
from py3plex.algorithms.community_detection.sbm_metrics import (
    SBM_METRICS,
    sbm_log_likelihood,
    sbm_mdl,
    sbm_n_blocks,
)


class TestModularity:
    """Tests for the modularity() function."""

    def _simple_graph(self):
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("D", "E"), ("D", "F")])
        return G

    def test_perfect_partition_high_modularity(self):
        """Two dense cliques in separate communities should yield high modularity."""
        G = self._simple_graph()
        communities = {0: ["A", "B", "C"], 1: ["D", "E", "F"]}
        Q = modularity(G, communities)
        assert Q > 0

    def test_uniform_partition_low_modularity(self):
        """All nodes in one community → modularity ~ 0."""
        G = self._simple_graph()
        communities = {0: ["A", "B", "C", "D", "E", "F"]}
        Q = modularity(G, communities)
        assert abs(Q) < 1e-6

    def test_returns_float(self):
        G = self._simple_graph()
        Q = modularity(G, {0: ["A", "B"], 1: ["C", "D", "E", "F"]})
        assert isinstance(Q, float)

    def test_modularity_in_valid_range(self):
        """Modularity should be between -0.5 and 1."""
        G = nx.karate_club_graph()
        # two roughly equal halves
        nodes = list(G.nodes())
        half = len(nodes) // 2
        communities = {0: nodes[:half], 1: nodes[half:]}
        Q = modularity(G, communities)
        assert -0.5 <= Q <= 1.0

    def test_directed_graph(self):
        """Modularity should work on directed graphs."""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A"), ("D", "E"), ("E", "D")])
        communities = {0: ["A", "B", "C"], 1: ["D", "E"]}
        Q = modularity(G, communities)
        assert isinstance(Q, float)

    def test_weighted_edges(self):
        """Weighted edges should be handled."""
        G = nx.Graph()
        G.add_edge("A", "B", weight=3.0)
        G.add_edge("C", "D", weight=1.0)
        communities = {0: ["A", "B"], 1: ["C", "D"]}
        Q = modularity(G, communities, weight="weight")
        assert isinstance(Q, float)

    def test_single_node_communities(self):
        """Each node in its own community should return a valid number."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        communities = {0: ["A"], 1: ["B"], 2: ["C"]}
        Q = modularity(G, communities)
        assert isinstance(Q, float)


class TestSizeDistribution:
    """Tests for size_distribution()."""

    def test_basic(self):
        partition = {0: ["A", "B", "C"], 1: ["D", "E"]}
        sizes = size_distribution(partition)
        assert isinstance(sizes, np.ndarray)
        assert set(sizes.tolist()) == {3, 2}

    def test_single_community(self):
        partition = {0: ["A", "B"]}
        sizes = size_distribution(partition)
        assert len(sizes) == 1
        assert sizes[0] == 2

    def test_many_singletons(self):
        partition = {i: [str(i)] for i in range(5)}
        sizes = size_distribution(partition)
        assert len(sizes) == 5
        assert all(s == 1 for s in sizes)

    def test_empty_partition(self):
        partition = {}
        sizes = size_distribution(partition)
        assert len(sizes) == 0


class TestNumberOfCommunities:
    """Tests for number_of_communities()."""

    def test_basic(self):
        partition = {0: ["A", "B"], 1: ["C"], 2: ["D", "E", "F"]}
        assert number_of_communities(partition) == 3

    def test_single_community(self):
        partition = {0: ["A", "B", "C"]}
        assert number_of_communities(partition) == 1

    def test_empty_partition(self):
        partition = {}
        assert number_of_communities(partition) == 0

    def test_five_communities(self):
        partition = {i: [f"n{i}"] for i in range(5)}
        assert number_of_communities(partition) == 5


class TestSBMMetrics:
    """Tests for sbm_log_likelihood, sbm_mdl, sbm_n_blocks, and SBM_METRICS."""

    def _meta(self, log_likelihood=-100.0, mdl=300.0, k=3, bic=None):
        m = {"log_likelihood": log_likelihood, "mdl": mdl, "K_selected": k}
        if bic is not None:
            m["bic"] = bic
        return m

    # --- sbm_log_likelihood ---
    def test_log_likelihood_present(self):
        meta = self._meta(log_likelihood=-200.0)
        result = sbm_log_likelihood(None, {}, meta)
        assert result == -200.0

    def test_log_likelihood_missing(self):
        result = sbm_log_likelihood(None, {}, {})
        assert result is None

    # --- sbm_mdl ---
    def test_mdl_present(self):
        meta = self._meta(mdl=500.0)
        result = sbm_mdl(None, {}, meta)
        assert result == 500.0

    def test_mdl_falls_back_to_bic(self):
        meta = {"bic": 999.0}
        result = sbm_mdl(None, {}, meta)
        assert result == 999.0

    def test_mdl_missing(self):
        result = sbm_mdl(None, {}, {})
        assert result is None

    # --- sbm_n_blocks ---
    def test_n_blocks_present(self):
        meta = self._meta(k=4)
        result = sbm_n_blocks(None, {}, meta)
        assert result == 4

    def test_n_blocks_missing(self):
        result = sbm_n_blocks(None, {}, {})
        assert result is None

    # --- SBM_METRICS registry ---
    def test_registry_keys(self):
        assert "sbm_log_likelihood" in SBM_METRICS
        assert "sbm_mdl" in SBM_METRICS
        assert "sbm_n_blocks" in SBM_METRICS

    def test_registry_directions(self):
        assert SBM_METRICS["sbm_log_likelihood"]["direction"] == "maximize"
        assert SBM_METRICS["sbm_mdl"]["direction"] == "minimize"
        assert SBM_METRICS["sbm_n_blocks"]["direction"] == "none"

    def test_registry_functions_callable(self):
        for key, entry in SBM_METRICS.items():
            assert callable(entry["function"])

    def test_registry_functions_work(self):
        meta = {"log_likelihood": -50.0, "mdl": 100.0, "K_selected": 2}
        for key, entry in SBM_METRICS.items():
            result = entry["function"](None, {}, meta)
            assert result is not None

    def test_registry_requires_field(self):
        for key, entry in SBM_METRICS.items():
            assert "requires" in entry
            assert isinstance(entry["requires"], list)
