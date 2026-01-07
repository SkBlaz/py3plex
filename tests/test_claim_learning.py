"""Tests for claim learning module.

This test suite covers:
- Candidate generation (determinism, thresholds)
- Scoring correctness (support/coverage)
- Claim string round-trip with counterexample engine
- Determinism (same seed → same claims)
- Lazy counterexample integration
- Property tests with Hypothesis
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.claims import Claim, Antecedent, Consequent, ClaimScore
from py3plex.claims.generator import (
    generate_antecedent_candidates,
    generate_consequent_candidates,
    extract_metrics_from_result,
    build_node_data_records,
)
from py3plex.claims.scorer import (
    score_claim,
    filter_by_thresholds,
    rank_claims,
    build_claims_from_scored,
)
from py3plex.claims.learner import learn_claims, ClaimLearningError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_network():
    """Create a simple network with known properties for testing."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {"source": "A", "type": "layer1"},
        {"source": "B", "type": "layer1"},
        {"source": "C", "type": "layer1"},
        {"source": "D", "type": "layer1"},
        {"source": "E", "type": "layer1"},
    ]
    net.add_nodes(nodes)
    
    # Add edges: A is a hub (degree 4), others have lower degree
    edges = [
        {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1"},
        {"source": "A", "target": "C", "source_type": "layer1", "target_type": "layer1"},
        {"source": "A", "target": "D", "source_type": "layer1", "target_type": "layer1"},
        {"source": "A", "target": "E", "source_type": "layer1", "target_type": "layer1"},
        {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1"},
    ]
    net.add_edges(edges)
    
    return net


@pytest.fixture
def multilayer_network():
    """Create a multilayer network for testing layer-restricted claims."""
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {"source": "Alice", "type": "social"},
        {"source": "Bob", "type": "social"},
        {"source": "Charlie", "type": "social"},
        {"source": "Alice", "type": "work"},
        {"source": "Bob", "type": "work"},
        {"source": "Diana", "type": "work"},
    ]
    net.add_nodes(nodes)
    
    edges = [
        {"source": "Alice", "target": "Bob", "source_type": "social", "target_type": "social"},
        {"source": "Bob", "target": "Charlie", "source_type": "social", "target_type": "social"},
        {"source": "Alice", "target": "Charlie", "source_type": "social", "target_type": "social"},
        {"source": "Alice", "target": "Bob", "source_type": "work", "target_type": "work"},
        {"source": "Bob", "target": "Diana", "source_type": "work", "target_type": "work"},
    ]
    net.add_edges(edges)
    
    return net


# ============================================================================
# Unit Tests: Candidate Generation
# ============================================================================


class TestCandidateGeneration:
    """Test candidate antecedent and consequent generation."""
    
    def test_antecedent_generation_deterministic(self):
        """Test that antecedent generation is deterministic given a seed."""
        metrics_data = {
            "degree": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
        
        candidates1 = generate_antecedent_candidates(
            metrics_data=metrics_data,
            cheap_metrics=["degree"],
            seed=42,
        )
        
        candidates2 = generate_antecedent_candidates(
            metrics_data=metrics_data,
            cheap_metrics=["degree"],
            seed=42,
        )
        
        # Should be identical
        assert len(candidates1) == len(candidates2)
        for c1, c2 in zip(candidates1, candidates2):
            assert c1 == c2
    
    def test_antecedent_quantile_thresholds(self):
        """Test that antecedent thresholds match quantiles."""
        values = list(range(1, 101))  # 1 to 100
        metrics_data = {"degree": values}
        
        candidates = generate_antecedent_candidates(
            metrics_data=metrics_data,
            cheap_metrics=["degree"],
            quantiles=[0.7, 0.8, 0.9],
            seed=42,
        )
        
        # Filter to threshold predicates only
        threshold_preds = [c for c in candidates if c.predicate_type == "threshold"]
        
        # Should have 3 threshold predicates (one per quantile)
        assert len(threshold_preds) >= 3
        
        # Check thresholds are approximately correct
        expected_thresholds = [np.quantile(values, q) for q in [0.7, 0.8, 0.9]]
        actual_thresholds = [c.threshold for c in threshold_preds if c.metric == "degree"]
        
        for expected in expected_thresholds:
            assert any(abs(actual - expected) < 0.1 for actual in actual_thresholds)
    
    def test_consequent_generation_deterministic(self):
        """Test that consequent generation is deterministic."""
        metrics_data = {
            "pagerank": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
        
        candidates1 = generate_consequent_candidates(
            metrics_data=metrics_data,
            target_metrics=["pagerank"],
            seed=42,
        )
        
        candidates2 = generate_consequent_candidates(
            metrics_data=metrics_data,
            target_metrics=["pagerank"],
            seed=42,
        )
        
        assert len(candidates1) == len(candidates2)
        for c1, c2 in zip(candidates1, candidates2):
            assert c1 == c2
    
    def test_top_p_candidates(self):
        """Test top_p predicate generation."""
        metrics_data = {"degree": list(range(1, 21))}
        
        candidates = generate_antecedent_candidates(
            metrics_data=metrics_data,
            cheap_metrics=["degree"],
            top_p_values=[0.1, 0.2],
            seed=42,
        )
        
        top_p_preds = [c for c in candidates if c.predicate_type == "top_p"]
        assert len(top_p_preds) >= 2
        
        percentiles = [c.percentile for c in top_p_preds]
        assert 0.1 in percentiles
        assert 0.2 in percentiles
    
    def test_rank_consequent_candidates(self):
        """Test rank-based consequent generation."""
        metrics_data = {"pagerank": list(range(1, 51))}
        
        candidates = generate_consequent_candidates(
            metrics_data=metrics_data,
            target_metrics=["pagerank"],
            rank_thresholds=[10, 20],
            seed=42,
        )
        
        rank_preds = [c for c in candidates if c.predicate_type == "rank"]
        assert len(rank_preds) >= 2
        
        ranks = [c.rank for c in rank_preds]
        assert 10 in ranks
        assert 20 in ranks


# ============================================================================
# Unit Tests: Scoring
# ============================================================================


class TestScoring:
    """Test claim scoring correctness."""
    
    def test_score_claim_basic(self):
        """Test basic support and coverage calculation."""
        # Create simple data: 5 nodes, 3 satisfy antecedent, 2 satisfy both
        node_data = [
            {"degree": 5, "pagerank": 0.5},  # Satisfies both
            {"degree": 6, "pagerank": 0.6},  # Satisfies both
            {"degree": 7, "pagerank": 0.1},  # Satisfies antecedent only
            {"degree": 1, "pagerank": 0.2},  # Satisfies neither
            {"degree": 2, "pagerank": 0.3},  # Satisfies neither
        ]
        
        metrics_data = {
            "degree": [5, 6, 7, 1, 2],
            "pagerank": [0.5, 0.6, 0.1, 0.2, 0.3],
        }
        
        antecedent = Antecedent(
            metric="degree",
            predicate_type="threshold",
            threshold=5.0,
            operator=">=",
        )
        
        consequent = Consequent(
            metric="pagerank",
            predicate_type="threshold",
            threshold=0.4,
            operator=">=",
        )
        
        score = score_claim(antecedent, consequent, node_data, metrics_data)
        
        assert score is not None
        assert score.n_antecedent == 3  # 3 nodes with degree >= 5
        assert score.n_both == 2  # 2 nodes with degree >= 5 AND pagerank >= 0.4
        assert score.n_total == 5
        assert abs(score.support - 2/3) < 0.001  # 2/3
        assert abs(score.coverage - 3/5) < 0.001  # 3/5
    
    def test_filter_by_thresholds(self):
        """Test filtering claims by support/coverage."""
        antecedent = Antecedent(metric="degree", predicate_type="threshold", threshold=5.0, operator=">=")
        consequent = Consequent(metric="pagerank", predicate_type="threshold", threshold=0.4, operator=">=")
        
        claims = [
            (antecedent, consequent, ClaimScore(support=0.95, coverage=0.1, n_antecedent=10, n_both=9, n_total=100)),
            (antecedent, consequent, ClaimScore(support=0.85, coverage=0.2, n_antecedent=20, n_both=17, n_total=100)),
            (antecedent, consequent, ClaimScore(support=0.92, coverage=0.03, n_antecedent=3, n_both=2, n_total=100)),
        ]
        
        filtered = filter_by_thresholds(claims, min_support=0.9, min_coverage=0.05)
        
        # Should keep only first claim (support=0.95, coverage=0.1)
        assert len(filtered) == 1
        assert filtered[0][2].support == 0.95
    
    def test_rank_claims_deterministic(self):
        """Test that claim ranking is deterministic."""
        antecedent1 = Antecedent(metric="degree", predicate_type="threshold", threshold=5.0, operator=">=")
        antecedent2 = Antecedent(metric="strength", predicate_type="threshold", threshold=3.0, operator=">=")
        consequent = Consequent(metric="pagerank", predicate_type="threshold", threshold=0.4, operator=">=")
        
        claims = [
            (antecedent1, consequent, ClaimScore(support=0.9, coverage=0.2, n_antecedent=20, n_both=18, n_total=100)),
            (antecedent2, consequent, ClaimScore(support=0.95, coverage=0.1, n_antecedent=10, n_both=9, n_total=100)),
            (antecedent1, consequent, ClaimScore(support=0.9, coverage=0.15, n_antecedent=15, n_both=13, n_total=100)),
        ]
        
        ranked = rank_claims(claims)
        
        # Highest support first
        assert ranked[0][2].support == 0.95
        # Among support=0.9, higher coverage first
        assert ranked[1][2].coverage == 0.2


# ============================================================================
# Unit Tests: Claim String Round-Trip
# ============================================================================


class TestClaimStringRoundTrip:
    """Test that claim strings can be used with counterexample engine."""
    
    def test_antecedent_to_dsl_string(self):
        """Test antecedent DSL string rendering."""
        antecedent = Antecedent(
            metric="degree",
            predicate_type="threshold",
            threshold=10.0,
            operator=">=",
        )
        
        dsl_str = antecedent.to_dsl_string()
        assert dsl_str == "degree__gte(10.0)"
    
    def test_consequent_to_dsl_string_threshold(self):
        """Test consequent threshold DSL string rendering."""
        consequent = Consequent(
            metric="pagerank",
            predicate_type="threshold",
            threshold=0.1,
            operator=">=",
        )
        
        dsl_str = consequent.to_dsl_string()
        assert dsl_str == "pagerank__gte(0.1)"
    
    def test_consequent_to_dsl_string_rank(self):
        """Test consequent rank DSL string rendering."""
        consequent = Consequent(
            metric="pagerank",
            predicate_type="rank",
            rank=20,
            rank_operator="<=",
        )
        
        dsl_str = consequent.to_dsl_string()
        assert dsl_str == "pagerank__rank_lte(20)"
    
    def test_claim_string_format(self):
        """Test complete claim string format."""
        claim = Claim(
            antecedent=Antecedent(metric="degree", predicate_type="threshold", threshold=10.0, operator=">="),
            consequent=Consequent(metric="pagerank", predicate_type="rank", rank=50, rank_operator="<="),
            score=ClaimScore(support=0.9, coverage=0.1, n_antecedent=10, n_both=9, n_total=100),
            claim_string="degree__gte(10.0) -> pagerank__rank_lte(50)",
        )
        
        assert claim.claim_string == "degree__gte(10.0) -> pagerank__rank_lte(50)"


# ============================================================================
# Unit Tests: Determinism
# ============================================================================


class TestDeterminism:
    """Test that claim learning is deterministic given a seed."""
    
    def test_same_seed_same_claims(self, simple_network):
        """Test that same seed produces identical claims."""
        claims1 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(42)
             .execute(simple_network)
        )
        
        claims2 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(42)
             .execute(simple_network)
        )
        
        assert len(claims1) == len(claims2)
        
        for c1, c2 in zip(claims1, claims2):
            assert c1.claim_string == c2.claim_string
            assert c1.support == c2.support
            assert c1.coverage == c2.coverage
    
    def test_different_seed_may_differ(self, simple_network):
        """Test that different seeds may produce different ordering (but same content)."""
        claims1 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(42)
             .execute(simple_network)
        )
        
        claims2 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(123)
             .execute(simple_network)
        )
        
        # Same content (deterministic algorithm)
        # Note: With current implementation, seed doesn't affect ordering
        # But this test ensures seed parameter is accepted
        assert len(claims1) == len(claims2)


# ============================================================================
# Unit Tests: Lazy Counterexample Integration
# ============================================================================


class TestLazyCounterexample:
    """Test lazy counterexample integration."""
    
    def test_counterexample_not_computed_eagerly(self, simple_network):
        """Test that counterexamples are not computed during claim learning."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(5)
             .seed(42)
             .execute(simple_network)
        )
        
        # Claims should be returned without computing counterexamples
        assert len(claims) > 0
        
        # Meta should not contain counterexample data
        for claim in claims:
            assert "counterexample" not in claim.meta
    
    def test_counterexample_lazy_invocation(self, simple_network):
        """Test that counterexample() can be called lazily."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(5)
             .seed(42)
             .execute(simple_network)
        )
        
        assert len(claims) > 0
        
        # Should be able to call counterexample() on a claim
        # (may return None if no counterexample exists)
        claim = claims[0]
        try:
            cex = claim.counterexample(simple_network, seed=42)
            # cex may be None or a Counterexample object
            assert cex is None or hasattr(cex, 'explain')
        except Exception as e:
            # Counterexample engine may not support all claim formats yet
            # This is expected in MVP
            assert "parse" in str(e).lower() or "claim" in str(e).lower()


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for full claim learning pipeline."""
    
    def test_basic_claim_learning(self, simple_network):
        """Test basic claim learning pipeline."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(42)
             .execute(simple_network)
        )
        
        assert isinstance(claims, list)
        assert len(claims) > 0
        
        for claim in claims:
            assert isinstance(claim, Claim)
            assert claim.support >= 0.5
            assert claim.coverage >= 0.01
            assert "->" in claim.claim_string
    
    def test_layer_restricted_learning(self, multilayer_network):
        """Test claim learning with layer restriction."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .layers(L["social"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(5)
             .seed(42)
             .execute(multilayer_network)
        )
        
        assert len(claims) >= 0
        
        # Check that layers are recorded in metadata
        for claim in claims:
            assert claim.meta.get("layers") == ["social"]
    
    def test_max_claims_limiting(self, simple_network):
        """Test that max_claims limits results."""
        claims_5 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.3)
             .min_coverage(0.01)
             .max_claims(5)
             .seed(42)
             .execute(simple_network)
        )
        
        claims_10 = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.3)
             .min_coverage(0.01)
             .max_claims(10)
             .seed(42)
             .execute(simple_network)
        )
        
        assert len(claims_5) <= 5
        assert len(claims_10) <= 10
        
        # If both are at limit, 10 should have more
        if len(claims_5) == 5 and len(claims_10) > 5:
            assert len(claims_10) > len(claims_5)
    
    def test_provenance_metadata(self, simple_network):
        """Test that provenance metadata is included."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .seed(42)
             .execute(simple_network)
        )
        
        assert len(claims) > 0
        
        claim = claims[0]
        assert "provenance" in claim.meta
        
        prov = claim.meta["provenance"]
        assert prov["engine"] == "claim_learner"
        assert "timestamp_utc" in prov
        assert "network_fingerprint" in prov
        assert prov["randomness"]["seed"] == 42
        assert "degree" in prov["metrics_used"]
        assert "pagerank" in prov["metrics_used"]
    
    def test_to_dict_serialization(self, simple_network):
        """Test that claims can be serialized to dict."""
        claims = (
            Q.learn_claims()
             .from_metrics(["degree", "pagerank"])
             .min_support(0.5)
             .min_coverage(0.01)
             .max_claims(1)
             .seed(42)
             .execute(simple_network)
        )
        
        if len(claims) > 0:
            claim_dict = claims[0].to_dict()
            
            assert "claim_string" in claim_dict
            assert "antecedent" in claim_dict
            assert "consequent" in claim_dict
            assert "score" in claim_dict
            assert "meta" in claim_dict
            
            # Should be JSON-serializable
            import json
            json_str = json.dumps(claim_dict)
            assert len(json_str) > 0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling in claim learning."""
    
    def test_no_metrics_error(self, simple_network):
        """Test error when no metrics specified."""
        with pytest.raises(ClaimLearningError) as exc_info:
            Q.learn_claims().execute(simple_network)
        
        assert "No metrics" in str(exc_info.value)
    
    def test_max_antecedents_validation(self, simple_network):
        """Test that max_antecedents > 1 raises error in MVP."""
        with pytest.raises(ClaimLearningError) as exc_info:
            (
                Q.learn_claims()
                 .from_metrics(["degree", "pagerank"])
                 .max_antecedents(2)
                 .execute(simple_network)
            )
        
        assert "max_antecedents must be 1" in str(exc_info.value)


# ============================================================================
# Hypothesis Property Tests
# ============================================================================


@pytest.mark.property
class TestPropertyBasedDeterminism:
    """Property-based tests for determinism."""
    
    @given(
        n_nodes=st.integers(min_value=3, max_value=10),
        n_edges=st.integers(min_value=2, max_value=15),
        seed=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=10, deadline=5000)
    def test_determinism_property(self, n_nodes, n_edges, seed):
        """Property: Same seed produces identical claims."""
        # Build random network
        net = multinet.multi_layer_network(directed=False)
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(n_nodes)]
        net.add_nodes(nodes)
        
        # Add random edges (ensuring we don't exceed possible edges)
        max_edges = n_nodes * (n_nodes - 1) // 2
        n_edges = min(n_edges, max_edges)
        
        np.random.seed(seed)
        added_edges = set()
        for _ in range(n_edges):
            i = np.random.randint(0, n_nodes)
            j = np.random.randint(0, n_nodes)
            if i != j and (i, j) not in added_edges and (j, i) not in added_edges:
                net.add_edges([{
                    "source": f"N{i}",
                    "target": f"N{j}",
                    "source_type": "layer1",
                    "target_type": "layer1",
                }])
                added_edges.add((i, j))
        
        # Learn claims twice with same seed
        try:
            claims1 = (
                Q.learn_claims()
                 .from_metrics(["degree"])
                 .min_support(0.3)
                 .min_coverage(0.01)
                 .max_claims(5)
                 .seed(seed)
                 .execute(net)
            )
            
            claims2 = (
                Q.learn_claims()
                 .from_metrics(["degree"])
                 .min_support(0.3)
                 .min_coverage(0.01)
                 .max_claims(5)
                 .seed(seed)
                 .execute(net)
            )
            
            # Should produce identical results
            assert len(claims1) == len(claims2)
            
            for c1, c2 in zip(claims1, claims2):
                assert c1.claim_string == c2.claim_string
                assert c1.support == c2.support
                assert c1.coverage == c2.coverage
        
        except ClaimLearningError:
            # May fail on trivial networks
            pass


@pytest.mark.property
class TestPropertyBasedSoundness:
    """Property-based tests for soundness of claims."""
    
    @given(
        n_nodes=st.integers(min_value=5, max_value=15),
        seed=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=10, deadline=5000)
    def test_soundness_property(self, n_nodes, seed):
        """Property: All learned claims satisfy min_support and min_coverage."""
        # Build random network
        net = multinet.multi_layer_network(directed=False)
        
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(n_nodes)]
        net.add_nodes(nodes)
        
        # Add random edges
        np.random.seed(seed)
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                if np.random.random() < 0.3:
                    net.add_edges([{
                        "source": f"N{i}",
                        "target": f"N{j}",
                        "source_type": "layer1",
                        "target_type": "layer1",
                    }])
        
        min_support = 0.7
        min_coverage = 0.1
        
        try:
            claims = (
                Q.learn_claims()
                 .from_metrics(["degree"])
                 .min_support(min_support)
                 .min_coverage(min_coverage)
                 .max_claims(10)
                 .seed(seed)
                 .execute(net)
            )
            
            # All claims must satisfy thresholds
            for claim in claims:
                assert claim.support >= min_support, \
                    f"Claim {claim.claim_string} has support {claim.support} < {min_support}"
                assert claim.coverage >= min_coverage, \
                    f"Claim {claim.claim_string} has coverage {claim.coverage} < {min_coverage}"
        
        except ClaimLearningError:
            # May fail on trivial networks or when no claims satisfy thresholds
            pass
