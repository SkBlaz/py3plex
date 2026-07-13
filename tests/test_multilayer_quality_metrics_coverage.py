"""Tests for multilayer_quality_metrics.py to improve coverage."""

import math
import warnings
from unittest.mock import MagicMock

import networkx as nx
import numpy as np
import pytest

from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    iter_layered_assignments,
    layer_entropy,
    mdl_score,
    replica_consistency,
)


class TestIterLayeredAssignments:
    """Tests for iter_layered_assignments()."""

    def test_tuple_keys_extracted(self):
        """Partition with (node, layer) tuple keys should yield (node, layer, comm)."""
        partition = {("A", "social"): 0, ("B", "social"): 1, ("A", "work"): 0}
        results = list(iter_layered_assignments(partition, None))
        assert len(results) == 3
        nodes = {r[0] for r in results}
        layers = {r[1] for r in results}
        assert "A" in nodes and "B" in nodes
        assert "social" in layers and "work" in layers

    def test_plain_keys_yield_none_layer(self):
        """Plain node keys (no tuple) should yield None as the layer."""
        partition = {"nodeA": 0, "nodeB": 1}
        results = list(iter_layered_assignments(partition, None))
        assert all(r[1] is None for r in results)
        assert len(results) == 2

    def test_empty_partition(self):
        results = list(iter_layered_assignments({}, None))
        assert results == []

    def test_comm_ids_preserved(self):
        partition = {("X", "L1"): 7, ("Y", "L1"): 3}
        results = list(iter_layered_assignments(partition, None))
        comm_ids = {r[2] for r in results}
        assert comm_ids == {7, 3}

    def test_three_element_tuple_uses_first_two(self):
        """Tuples longer than 2 should use first two elements as node_id, layer."""
        partition = {("A", "social", "extra"): 0}
        results = list(iter_layered_assignments(partition, None))
        assert results[0][0] == "A"
        assert results[0][1] == "social"


class TestReplicaConsistency:
    """Tests for replica_consistency()."""

    def test_perfect_consistency(self):
        """Node in same community across all layers → RC = 1.0."""
        partition = {
            ("A", "social"): 0, ("A", "work"): 0, ("A", "family"): 0,
            ("B", "social"): 1, ("B", "work"): 1,
        }
        rc = replica_consistency(partition, None)
        assert rc == 1.0

    def test_zero_consistency(self):
        """Node always in different communities across layers → RC = 0.0."""
        partition = {("A", "social"): 0, ("A", "work"): 1}
        rc = replica_consistency(partition, None)
        assert rc == 0.0

    def test_partial_consistency(self):
        """Node partially consistent: 2 agree, 1 differs."""
        partition = {
            ("A", "L1"): 0, ("A", "L2"): 0, ("A", "L3"): 1,
        }
        rc = replica_consistency(partition, None)
        # 1 agreement pair out of 3 total → RC(A) = 1/3
        assert abs(rc - 1 / 3) < 1e-6

    def test_single_layer_node_skipped(self):
        """Nodes appearing in only one layer should be skipped."""
        partition = {("A", "social"): 0}  # Only one layer
        rc = replica_consistency(partition, None)
        assert rc == 0.0

    def test_plain_keys_yield_zero(self):
        """Plain (non-tuple) keys yield None layer → all skipped."""
        partition = {"nodeA": 0, "nodeB": 1}
        rc = replica_consistency(partition, None)
        assert rc == 0.0

    def test_layer_filter(self):
        """Layer filter should restrict which layers are considered."""
        partition = {
            ("A", "social"): 0, ("A", "work"): 0, ("A", "family"): 1,
        }
        # Including only social and work → A is consistent
        rc = replica_consistency(partition, None, layers=["social", "work"])
        assert rc == 1.0

        # Including only social and family → A is inconsistent
        rc2 = replica_consistency(partition, None, layers=["social", "family"])
        assert rc2 == 0.0

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid mode"):
            replica_consistency({}, None, mode="bad_mode")

    def test_multiple_nodes(self):
        """Test with multiple nodes to verify averaging."""
        partition = {
            # Node A: perfectly consistent
            ("A", "L1"): 0, ("A", "L2"): 0,
            # Node B: inconsistent
            ("B", "L1"): 0, ("B", "L2"): 1,
        }
        rc = replica_consistency(partition, None)
        # RC(A) = 1.0, RC(B) = 0.0 → mean = 0.5
        assert abs(rc - 0.5) < 1e-6


class TestLayerEntropy:
    """Tests for layer_entropy()."""

    def test_balanced_partition_high_entropy(self):
        """Equal communities per layer → high entropy."""
        partition = {
            ("A", "social"): 0, ("B", "social"): 1,
            ("C", "social"): 0, ("D", "social"): 1,
        }
        h = layer_entropy(partition, None, clip=(0.0, 1.0))
        assert h > 0.8

    def test_giant_cluster_low_entropy_clipped(self):
        """Single community per layer → entropy 0, clipped to min clip value."""
        partition = {
            ("A", "social"): 0, ("B", "social"): 0, ("C", "social"): 0,
        }
        h = layer_entropy(partition, None, clip=(0.1, 0.9))
        assert h == pytest.approx(0.1)

    def test_empty_partition_returns_zero(self):
        """Empty partition should return 0.0 (with warning)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h = layer_entropy({}, None)
        assert h == 0.0

    def test_plain_keys_returns_zero(self):
        """Plain keys produce no layer assignments → empty → 0.0."""
        partition = {"nodeA": 0, "nodeB": 1}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            h = layer_entropy(partition, None)
        assert h == 0.0

    def test_layer_filter(self):
        """Layer filter should limit which layers are included."""
        partition = {
            ("A", "social"): 0, ("B", "social"): 1,
            ("A", "work"): 0, ("B", "work"): 0,  # degenerate work layer
        }
        h_both = layer_entropy(partition, None, layers=["social", "work"], clip=(0.0, 1.0))
        h_social_only = layer_entropy(partition, None, layers=["social"], clip=(0.0, 1.0))
        assert h_social_only >= h_both  # social is more balanced than both

    def test_base_2(self):
        partition = {
            ("A", "L"): 0, ("B", "L"): 1,
        }
        h = layer_entropy(partition, None, base="2", clip=(0.0, 1.0))
        assert isinstance(h, float)

    def test_base_10(self):
        partition = {
            ("A", "L"): 0, ("B", "L"): 1,
        }
        h = layer_entropy(partition, None, base="10", clip=(0.0, 1.0))
        assert isinstance(h, float)

    def test_invalid_base_raises(self):
        with pytest.raises(ValueError, match="Invalid base"):
            layer_entropy({}, None, base="3")

    def test_multi_community_layer(self):
        """Multiple communities → entropy between 0 and max."""
        partition = {
            ("A", "L"): 0, ("B", "L"): 1, ("C", "L"): 2, ("D", "L"): 3,
        }
        h = layer_entropy(partition, None, clip=(0.0, 1.0))
        assert 0.0 <= h <= 1.0

    def test_clip_respected(self):
        """Custom clip bounds should be respected."""
        partition = {("A", "L"): 0, ("B", "L"): 0}  # single community → 0 entropy
        h = layer_entropy(partition, None, clip=(0.2, 0.8))
        assert h == pytest.approx(0.2)


class TestMDLScore:
    """Tests for mdl_score()."""

    def _make_network(self, edges=None, directed=False):
        """Create a mock network with a simple NetworkX graph as core_network."""
        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()
        if edges:
            G.add_edges_from(edges)
        net = MagicMock()
        net.core_network = G
        return net

    def test_returns_float(self):
        net = self._make_network([("A", "B"), ("C", "D")])
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1, ("D", "L"): 1}
        score = mdl_score(partition, net)
        assert isinstance(score, float)

    def test_score_nonnegative(self):
        net = self._make_network([("A", "B"), ("A", "C"), ("B", "C")])
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1}
        score = mdl_score(partition, net)
        assert score >= 0.0

    def test_empty_partition_returns_zero(self):
        net = self._make_network()
        score = mdl_score({}, net)
        assert score == 0.0

    def test_none_network_still_works(self):
        """If network has no core_network, use partition-only computation."""
        net = MagicMock()
        del net.core_network  # Make getattr return None via spec_set would fail; use spec
        net2 = MagicMock(spec=[])  # No core_network attribute
        partition = {("A", "L"): 0, ("B", "L"): 1}
        score = mdl_score(partition, net2)
        assert isinstance(score, float)

    def test_perfect_2_community_split(self):
        """Two separate cliques should have finite non-negative MDL."""
        net = self._make_network([
            ("A", "B"), ("B", "C"), ("A", "C"),
            ("D", "E"), ("E", "F"), ("D", "F"),
        ])
        partition = {
            ("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 0,
            ("D", "L"): 1, ("E", "L"): 1, ("F", "L"): 1,
        }
        score = mdl_score(partition, net)
        assert score > 0.0 and math.isfinite(score)

    def test_directed_network(self):
        net = self._make_network([("A", "B"), ("B", "C")], directed=True)
        partition = {("A", "L"): 0, ("B", "L"): 0, ("C", "L"): 1}
        score = mdl_score(partition, net)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_multi_layer_partition(self):
        """Partition spanning multiple layers should be scored correctly."""
        net = self._make_network([("A", "B"), ("C", "D")])
        partition = {
            ("A", "L1"): 0, ("B", "L1"): 0,
            ("C", "L2"): 1, ("D", "L2"): 1,
        }
        score = mdl_score(partition, net)
        assert score >= 0.0
