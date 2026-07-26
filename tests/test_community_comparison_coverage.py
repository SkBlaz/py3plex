"""Tests for community_comparison.py to improve coverage."""

import math
import pytest
import numpy as np

from py3plex.algorithms.community_comparison import (
    compare_communities_ari,
    compare_communities_nmi,
    compare_communities_ami,
    compare_multilayer_communities,
    hierarchical_community_map,
    community_persistence_score,
    _compute_set_similarity,
    SKLEARN_AVAILABLE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _identical():
    """Two identical community assignments."""
    comm = {"A": 0, "B": 0, "C": 1, "D": 1}
    return comm, dict(comm)


def _opposite():
    """Community2 is a label-permuted version of community1 (perfectly correlated)."""
    return {"A": 0, "B": 0, "C": 1, "D": 1}, {"A": 1, "B": 1, "C": 0, "D": 0}


def _random():
    """Two uncorrelated community assignments on the same nodes."""
    return {"A": 0, "B": 0, "C": 0, "D": 0}, {"A": 0, "B": 1, "C": 0, "D": 1}


# ---------------------------------------------------------------------------
# ARI tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestCompareCommunitiesARI:
    def test_identical_partition_returns_one(self):
        c1, c2 = _identical()
        assert compare_communities_ari(c1, c2) == pytest.approx(1.0)

    def test_label_permuted_returns_one(self):
        c1, c2 = _opposite()
        # ARI is label-invariant; opposite labels yield 1.0
        assert compare_communities_ari(c1, c2) == pytest.approx(1.0)

    def test_returns_float(self):
        c1, c2 = _random()
        score = compare_communities_ari(c1, c2)
        assert isinstance(score, float)

    def test_no_common_nodes_raises(self):
        c1 = {"A": 0, "B": 1}
        c2 = {"X": 0, "Y": 1}
        with pytest.raises(ValueError, match="No common nodes"):
            compare_communities_ari(c1, c2)

    def test_partial_overlap_uses_common_nodes(self):
        c1 = {"A": 0, "B": 0, "C": 1, "EXTRA": 2}
        c2 = {"A": 0, "B": 0, "C": 1}
        # Should still work — just uses the 3 common nodes
        score = compare_communities_ari(c1, c2)
        assert score == pytest.approx(1.0)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestCompareCommunitiesNMI:
    def test_identical_returns_one(self):
        c1, c2 = _identical()
        assert compare_communities_nmi(c1, c2) == pytest.approx(1.0)

    def test_label_permuted_returns_one(self):
        c1, c2 = _opposite()
        assert compare_communities_nmi(c1, c2) == pytest.approx(1.0)

    def test_returns_in_unit_interval(self):
        c1, c2 = _random()
        score = compare_communities_nmi(c1, c2)
        assert 0.0 <= score <= 1.0

    def test_no_common_nodes_raises(self):
        c1 = {"A": 0}
        c2 = {"Z": 0}
        with pytest.raises(ValueError):
            compare_communities_nmi(c1, c2)

    def test_average_method_geometric(self):
        c1, c2 = _identical()
        score = compare_communities_nmi(c1, c2, average_method="geometric")
        assert score == pytest.approx(1.0)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestCompareCommunitiesAMI:
    def test_identical_returns_one(self):
        c1, c2 = _identical()
        assert compare_communities_ami(c1, c2) == pytest.approx(1.0)

    def test_label_permuted_returns_one(self):
        c1, c2 = _opposite()
        assert compare_communities_ami(c1, c2) == pytest.approx(1.0)

    def test_returns_float(self):
        c1, c2 = _random()
        score = compare_communities_ami(c1, c2)
        assert isinstance(score, float)

    def test_no_common_nodes_raises(self):
        c1 = {"A": 0}
        c2 = {"B": 0}
        with pytest.raises(ValueError):
            compare_communities_ami(c1, c2)


# ---------------------------------------------------------------------------
# compare_multilayer_communities
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
class TestCompareMultilayerCommunities:
    @pytest.fixture
    def three_layer_comms(self):
        return {
            "social": {"A": 0, "B": 0, "C": 1, "D": 1},
            "work": {"A": 0, "B": 1, "C": 1, "D": 0},
            "family": {"A": 0, "B": 0, "C": 1, "D": 1},
        }

    def test_all_pairs_present(self, three_layer_comms):
        results = compare_multilayer_communities(three_layer_comms)
        assert ("social", "work") in results
        assert ("social", "family") in results
        assert ("work", "family") in results

    def test_all_default_metrics_present(self, three_layer_comms):
        results = compare_multilayer_communities(three_layer_comms)
        for pair_scores in results.values():
            assert "ari" in pair_scores
            assert "nmi" in pair_scores
            assert "ami" in pair_scores

    def test_identical_layers_score_one(self, three_layer_comms):
        results = compare_multilayer_communities(three_layer_comms)
        # social and family are identical
        assert results[("social", "family")]["ari"] == pytest.approx(1.0)

    def test_custom_metrics_subset(self, three_layer_comms):
        results = compare_multilayer_communities(three_layer_comms, metrics=["ari"])
        for pair_scores in results.values():
            assert "ari" in pair_scores
            assert "nmi" not in pair_scores
            assert "ami" not in pair_scores

    def test_single_layer_returns_empty(self):
        layer_comms = {"solo": {"A": 0, "B": 1}}
        results = compare_multilayer_communities(layer_comms)
        assert results == {}


# ---------------------------------------------------------------------------
# hierarchical_community_map
# ---------------------------------------------------------------------------

class TestHierarchicalCommunityMap:
    @pytest.fixture
    def two_layer_comms(self):
        return {
            "L1": {"A": 0, "B": 0, "C": 1, "D": 1},
            "L2": {"A": 0, "B": 1, "C": 1, "D": 0},
        }

    def test_returns_dict(self, two_layer_comms):
        result = hierarchical_community_map(two_layer_comms)
        assert isinstance(result, dict)

    def test_keys_are_4_tuples(self, two_layer_comms):
        result = hierarchical_community_map(two_layer_comms)
        for key in result:
            assert len(key) == 4

    def test_scores_in_unit_interval(self, two_layer_comms):
        result = hierarchical_community_map(two_layer_comms)
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_identical_community_jaccard_is_one(self):
        comms = {
            "L1": {"A": 0, "B": 0},
            "L2": {"A": 0, "B": 0},
        }
        result = hierarchical_community_map(comms, method="jaccard")
        # Both layers have one community (0) with {A, B}
        assert result[("L1", 0, "L2", 0)] == pytest.approx(1.0)

    def test_overlap_method(self, two_layer_comms):
        result = hierarchical_community_map(two_layer_comms, method="overlap")
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_dice_method(self, two_layer_comms):
        result = hierarchical_community_map(two_layer_comms, method="dice")
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_single_layer_returns_empty(self):
        comms = {"only": {"A": 0, "B": 1}}
        result = hierarchical_community_map(comms)
        assert result == {}


# ---------------------------------------------------------------------------
# community_persistence_score
# ---------------------------------------------------------------------------

class TestCommunityPersistenceScore:
    def test_same_community_all_layers_returns_one(self):
        layer_comms = {
            "L1": {"A": 0, "B": 1},
            "L2": {"A": 0, "B": 1},
            "L3": {"A": 0, "B": 1},
        }
        assert community_persistence_score(layer_comms, "A") == pytest.approx(1.0)

    def test_different_communities_all_layers_returns_zero(self):
        layer_comms = {
            "L1": {"A": 0},
            "L2": {"A": 1},
            "L3": {"A": 2},
        }
        # All pairs disagree → 0/3 agreements
        score = community_persistence_score(layer_comms, "A")
        assert score == pytest.approx(0.0)

    def test_node_in_one_layer_returns_one(self):
        layer_comms = {
            "L1": {"A": 0},
            "L2": {"B": 1},  # A not in L2
        }
        assert community_persistence_score(layer_comms, "A") == pytest.approx(1.0)

    def test_partial_agreement(self):
        # A in comm 0 for L1 and L2, comm 1 for L3
        layer_comms = {
            "L1": {"A": 0},
            "L2": {"A": 0},
            "L3": {"A": 1},
        }
        # Pairs: (0,0)=agree, (0,1)=disagree, (0,1)=disagree → 1/3
        score = community_persistence_score(layer_comms, "A")
        assert score == pytest.approx(1 / 3)

    def test_node_absent_everywhere_returns_one(self):
        layer_comms = {
            "L1": {"B": 0},
        }
        # "A" is not present in any layer
        score = community_persistence_score(layer_comms, "A")
        assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _compute_set_similarity
# ---------------------------------------------------------------------------

class TestComputeSetSimilarity:
    def test_jaccard_identical(self):
        s = {1, 2, 3}
        assert _compute_set_similarity(s, s, "jaccard") == pytest.approx(1.0)

    def test_jaccard_disjoint(self):
        assert _compute_set_similarity({1, 2}, {3, 4}, "jaccard") == pytest.approx(0.0)

    def test_jaccard_partial(self):
        # |{1,2,3} ∩ {2,3,4}| / |{1,2,3,4}| = 2/4 = 0.5
        score = _compute_set_similarity({1, 2, 3}, {2, 3, 4}, "jaccard")
        assert score == pytest.approx(0.5)

    def test_jaccard_empty_both(self):
        assert _compute_set_similarity(set(), set(), "jaccard") == pytest.approx(0.0)

    def test_overlap_identical(self):
        s = {1, 2, 3}
        assert _compute_set_similarity(s, s, "overlap") == pytest.approx(1.0)

    def test_overlap_disjoint(self):
        assert _compute_set_similarity({1, 2}, {3, 4}, "overlap") == pytest.approx(0.0)

    def test_dice_identical(self):
        s = {1, 2, 3}
        assert _compute_set_similarity(s, s, "dice") == pytest.approx(1.0)

    def test_dice_disjoint(self):
        assert _compute_set_similarity({1, 2}, {3, 4}, "dice") == pytest.approx(0.0)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="Unknown similarity method"):
            _compute_set_similarity({1}, {1}, "invalid")
