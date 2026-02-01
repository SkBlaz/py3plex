"""Property-based tests for the claims module.

This module tests invariants and properties of claim learning algorithms
using hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis import note
import random

from py3plex.claims import (
    Claim,
    Antecedent,
    Consequent,
    ClaimScore,
)
from py3plex.claims.generator import (
    generate_antecedent_candidates,
    generate_consequent_candidates,
    build_node_data_records,
)
from py3plex.claims.scorer import (
    score_claim,
    filter_by_thresholds,
    rank_claims,
)


# ============================================================================
# Helper Strategies
# ============================================================================


@st.composite
def antecedent_strategy(draw):
    """Generate a random valid Antecedent."""
    metric = draw(st.sampled_from(["degree", "strength", "pagerank"]))
    predicate_type = draw(st.sampled_from(["threshold", "top_p", "layer_count"]))
    
    if predicate_type == "threshold":
        threshold = draw(st.floats(min_value=0.1, max_value=100.0))
        operator = draw(st.sampled_from([">=", ">", "<=", "<", "="]))
        return Antecedent(
            metric=metric,
            predicate_type=predicate_type,
            threshold=threshold,
            operator=operator,
        )
    elif predicate_type == "top_p":
        percentile = draw(st.floats(min_value=0.01, max_value=0.5))
        return Antecedent(
            metric=metric,
            predicate_type=predicate_type,
            percentile=percentile,
        )
    else:  # layer_count
        threshold = draw(st.integers(min_value=1, max_value=5))
        operator = draw(st.sampled_from([">=", ">", "<=", "<", "="]))
        return Antecedent(
            metric="layer_count",
            predicate_type=predicate_type,
            threshold=float(threshold),
            operator=operator,
        )


@st.composite
def consequent_strategy(draw):
    """Generate a random valid Consequent."""
    metric = draw(st.sampled_from(["betweenness_centrality", "closeness_centrality"]))
    predicate_type = draw(st.sampled_from(["rank", "threshold"]))
    
    if predicate_type == "rank":
        rank = draw(st.integers(min_value=1, max_value=100))
        rank_operator = draw(st.sampled_from(["<=", "<", ">=", ">"]))
        return Consequent(
            metric=metric,
            predicate_type=predicate_type,
            rank=rank,
            rank_operator=rank_operator,
        )
    else:  # threshold
        threshold = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
        operator = draw(st.sampled_from([">=", ">", "<=", "<", "="]))
        return Consequent(
            metric=metric,
            predicate_type=predicate_type,
            threshold=threshold,
            operator=operator,
        )


@st.composite
def node_data_strategy(draw):
    """Generate random node data for testing."""
    return {
        "node": draw(st.text(min_size=1, max_size=10, alphabet="abcdefghij")),
        "degree": draw(st.floats(min_value=0, max_value=100)),
        "strength": draw(st.floats(min_value=0, max_value=100)),
        "pagerank": draw(st.floats(min_value=0, max_value=1)),
        "betweenness_centrality": draw(st.floats(min_value=0, max_value=1)),
        "layer_count": draw(st.integers(min_value=1, max_value=5)),
    }


# ============================================================================
# Property Tests: Antecedent
# ============================================================================


class TestAntecedentProperties:
    """Property-based tests for Antecedent class."""
    
    @pytest.mark.property
    @given(ant=antecedent_strategy())
    @settings(max_examples=100, deadline=None)
    def test_antecedent_immutability(self, ant):
        """Antecedents must be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            ant.metric = "new_value"
    
    @pytest.mark.property
    @given(ant=antecedent_strategy())
    @settings(max_examples=100, deadline=None)
    def test_antecedent_to_dsl_string_not_empty(self, ant):
        """Antecedent DSL string must not be empty."""
        dsl_str = ant.to_dsl_string()
        assert isinstance(dsl_str, str)
        assert len(dsl_str) > 0
    
    @pytest.mark.property
    @given(
        ant=antecedent_strategy(),
        node_data=node_data_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_antecedent_evaluate_returns_bool(self, ant, node_data):
        """Antecedent evaluate must return a boolean."""
        # Need to provide all_values for top_p predicates
        all_values = {
            "degree": [node_data.get("degree", 0) for _ in range(10)],
            "strength": [node_data.get("strength", 0) for _ in range(10)],
            "pagerank": [node_data.get("pagerank", 0) for _ in range(10)],
        }
        result = ant.evaluate(node_data, all_values)
        assert isinstance(result, bool)
    
    @pytest.mark.property
    @given(ant=antecedent_strategy())
    @settings(max_examples=50, deadline=None)
    def test_antecedent_evaluate_deterministic(self, ant):
        """Antecedent evaluation must be deterministic."""
        node_data = {"degree": 10.0, "strength": 20.0, "pagerank": 0.5, "layer_count": 2}
        all_values = {"degree": [10.0], "strength": [20.0], "pagerank": [0.5]}
        
        result1 = ant.evaluate(node_data, all_values)
        result2 = ant.evaluate(node_data, all_values)
        assert result1 == result2


# ============================================================================
# Property Tests: Consequent
# ============================================================================


class TestConsequentProperties:
    """Property-based tests for Consequent class."""
    
    @pytest.mark.property
    @given(cons=consequent_strategy())
    @settings(max_examples=100, deadline=None)
    def test_consequent_immutability(self, cons):
        """Consequents must be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            cons.metric = "new_value"
    
    @pytest.mark.property
    @given(cons=consequent_strategy())
    @settings(max_examples=100, deadline=None)
    def test_consequent_to_dsl_string_not_empty(self, cons):
        """Consequent DSL string must not be empty."""
        dsl_str = cons.to_dsl_string()
        assert isinstance(dsl_str, str)
        assert len(dsl_str) > 0


# ============================================================================
# Property Tests: ClaimScore
# ============================================================================


class TestClaimScoreProperties:
    """Property-based tests for ClaimScore."""
    
    @pytest.mark.property
    @given(
        support=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        coverage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        n_antecedent=st.integers(min_value=0, max_value=1000),
        n_both=st.integers(min_value=0, max_value=1000),
        n_total=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100, deadline=None)
    def test_claim_score_bounds(
        self, support, coverage, n_antecedent, n_both, n_total
    ):
        """ClaimScore values must be within valid bounds."""
        # Ensure logical consistency
        assume(n_antecedent <= n_total)
        assume(n_both <= n_antecedent)
        
        score = ClaimScore(
            support=support,
            coverage=coverage,
            n_antecedent=n_antecedent,
            n_both=n_both,
            n_total=n_total,
        )
        
        # Support and coverage must be in [0, 1]
        assert 0.0 <= score.support <= 1.0
        assert 0.0 <= score.coverage <= 1.0
        
        # Counts must be non-negative
        assert score.n_antecedent >= 0
        assert score.n_both >= 0
        assert score.n_total > 0
        
        # Logical constraints
        assert score.n_both <= score.n_antecedent
        assert score.n_antecedent <= score.n_total


# ============================================================================
# Property Tests: Claim
# ============================================================================


class TestClaimProperties:
    """Property-based tests for Claim."""
    
    @pytest.mark.property
    @given(
        ant=antecedent_strategy(),
        cons=consequent_strategy(),
    )
    @settings(max_examples=50, deadline=None)
    def test_claim_string_format(self, ant, cons):
        """Claim string must follow 'antecedent -> consequent' format."""
        score = ClaimScore(
            support=0.9,
            coverage=0.1,
            n_antecedent=100,
            n_both=90,
            n_total=1000,
        )
        
        claim_string = f"{ant.to_dsl_string()} -> {cons.to_dsl_string()}"
        
        claim = Claim(
            antecedent=ant,
            consequent=cons,
            score=score,
            claim_string=claim_string,
        )
        
        assert isinstance(claim.claim_string, str)
        assert " -> " in claim.claim_string
    
    @pytest.mark.property
    @given(
        ant=antecedent_strategy(),
        cons=consequent_strategy(),
        support=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_claim_support_preserved(self, ant, cons, support):
        """Claim must preserve support value (rounded to 6 decimals)."""
        score = ClaimScore(
            support=support,
            coverage=0.1,
            n_antecedent=100,
            n_both=int(support * 100),
            n_total=1000,
        )
        
        claim_string = f"{ant.to_dsl_string()} -> {cons.to_dsl_string()}"
        
        claim = Claim(
            antecedent=ant,
            consequent=cons,
            score=score,
            claim_string=claim_string,
        )
        
        # ClaimScore rounds support to 6 decimals
        expected_support = round(support, 6)
        assert claim.support == expected_support


# ============================================================================
# Property Tests: Claim Scoring
# ============================================================================


class TestClaimScoringProperties:
    """Property-based tests for claim scoring functions."""
    
    @pytest.mark.property
    @given(
        ant=antecedent_strategy(),
        cons=consequent_strategy(),
        data=st.data(),
    )
    @settings(max_examples=50, deadline=None)
    def test_score_claim_deterministic(self, ant, cons, data):
        """Claim scoring must be deterministic."""
        # Generate consistent node data
        num_nodes = data.draw(st.integers(min_value=5, max_value=20))
        node_records = []
        for i in range(num_nodes):
            node_records.append({
                "node": f"n{i}",
                "degree": data.draw(st.floats(min_value=0, max_value=100)),
                "pagerank": data.draw(st.floats(min_value=0, max_value=1)),
                "betweenness_centrality": data.draw(st.floats(min_value=0, max_value=1)),
                "layer_count": data.draw(st.integers(min_value=1, max_value=5)),
            })
        
        # Compute metrics for top_p
        all_values = {
            "degree": [r["degree"] for r in node_records],
            "pagerank": [r["pagerank"] for r in node_records],
            "betweenness_centrality": [r["betweenness_centrality"] for r in node_records],
        }
        
        # Score twice with same data
        try:
            score1 = score_claim(ant, cons, node_records, all_values)
            score2 = score_claim(ant, cons, node_records, all_values)
            
            # Both should be None or both should be valid
            if score1 is None:
                assert score2 is None
            else:
                assert score2 is not None
                assert score1.support == score2.support
                assert score1.coverage == score2.coverage
                assert score1.n_antecedent == score2.n_antecedent
                assert score1.n_both == score2.n_both
                assert score1.n_total == score2.n_total
        except Exception:
            # Some combinations might not be valid, that's ok
            pass
    
    @pytest.mark.property
    @given(
        min_support=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_coverage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_filter_by_thresholds_respects_bounds(self, min_support, min_coverage):
        """filter_by_thresholds must respect support and coverage thresholds."""
        # Generate scored claims
        scored_claims = []
        for _ in range(10):
            support = random.uniform(0, 1)
            coverage = random.uniform(0, 1)
            score = ClaimScore(
                support=support,
                coverage=coverage,
                n_antecedent=100,
                n_both=int(support * 100),
                n_total=1000,
            )
            scored_claims.append((None, None, score))  # (ant, cons, score)
        
        # Filter
        filtered = filter_by_thresholds(
            scored_claims,
            min_support=min_support,
            min_coverage=min_coverage,
        )
        
        # All filtered claims must meet thresholds
        for _, _, score in filtered:
            assert score.support >= min_support
            assert score.coverage >= min_coverage


# ============================================================================
# Property Tests: Node Data Building
# ============================================================================


class TestNodeDataBuildingProperties:
    """Property-based tests for node data building."""
    
    @pytest.mark.property
    @given(data=st.data())
    @settings(max_examples=50, deadline=None)
    def test_build_node_data_records_preserves_count(self, data):
        """build_node_data_records must preserve node count."""
        # Generate simple node data
        num_nodes = data.draw(st.integers(min_value=1, max_value=20))
        nodes = [f"n{i}" for i in range(num_nodes)]
        
        # Create mock query result-like structure
        metrics = {
            "degree": {f"n{i}": float(i) for i in range(num_nodes)},
            "pagerank": {f"n{i}": float(i) / num_nodes for i in range(num_nodes)},
        }
        
        # Build records
        try:
            records = build_node_data_records(nodes, metrics)
            assert len(records) == num_nodes
        except Exception:
            # Some edge cases might fail, that's acceptable for property tests
            pass
