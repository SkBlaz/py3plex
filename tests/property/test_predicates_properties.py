"""Property-based tests for robustness contract predicates.

Tests predicate validation, evaluation logic, and invariants.
Using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np

from py3plex.contracts.predicates import Predicate, JaccardAtK


# ============================================================================
# Strategy Helpers
# ============================================================================


@st.composite
def jaccard_predicate(draw):
    """Generate valid JaccardAtK predicate."""
    k = draw(st.integers(min_value=1, max_value=100))
    threshold = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    metric = draw(st.one_of(st.none(), st.sampled_from(["degree", "pagerank", "betweenness"])))
    
    return JaccardAtK(k=k, threshold=threshold, metric=metric)


@st.composite
def mock_query_result(draw, n_items=None):
    """Generate mock QueryResult with items list."""
    if n_items is None:
        n_items = draw(st.integers(min_value=0, max_value=100))
    
    # Create simple list of items (node names)
    items = [f"node_{i}" for i in range(n_items)]
    
    # Return dict mimicking QueryResult structure
    return {"items": items}


# ============================================================================
# JaccardAtK Validation Tests
# ============================================================================


class TestJaccardAtKValidation:
    """Test JaccardAtK parameter validation."""
    
    @pytest.mark.property
    @given(k=st.integers(max_value=0))
    @settings(max_examples=20)
    def test_negative_or_zero_k_raises_error(self, k):
        """k must be positive."""
        with pytest.raises(ValueError, match="k must be positive"):
            JaccardAtK(k=k, threshold=0.85)
    
    @pytest.mark.property
    @given(threshold=st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x < 0.0 or x > 1.0))
    @settings(max_examples=50)
    def test_out_of_range_threshold_raises_error(self, threshold):
        """Threshold must be in [0, 1]."""
        with pytest.raises(ValueError, match="threshold must be in"):
            JaccardAtK(k=10, threshold=threshold)
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=100)
    def test_valid_predicate_constructs_successfully(self, pred):
        """Valid parameters should construct without error."""
        assert pred.k > 0
        assert 0.0 <= pred.threshold <= 1.0


# ============================================================================
# JaccardAtK Serialization Tests
# ============================================================================


class TestJaccardAtKSerialization:
    """Test JaccardAtK serialization."""
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=100)
    def test_to_dict_is_json_serializable(self, pred):
        """to_dict() should produce JSON-serializable dict."""
        data = pred.to_dict()
        
        assert isinstance(data, dict)
        
        # Check all values are JSON-serializable
        for v in data.values():
            assert isinstance(v, (str, int, float, bool, type(None), list, dict))
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=100)
    def test_to_dict_contains_required_fields(self, pred):
        """to_dict() should contain k, threshold, metric."""
        data = pred.to_dict()
        
        assert "k" in data
        assert "threshold" in data
        # metric may or may not be present depending on value
        
        assert data["k"] == pred.k
        assert data["threshold"] == pred.threshold


# ============================================================================
# JaccardAtK Interface Tests
# ============================================================================


class TestJaccardAtKInterface:
    """Test JaccardAtK implements Predicate interface."""
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=50)
    def test_is_predicate_instance(self, pred):
        """JaccardAtK should be a Predicate instance."""
        assert isinstance(pred, Predicate)
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=50)
    def test_has_evaluate_method(self, pred):
        """JaccardAtK should have evaluate method."""
        assert hasattr(pred, "evaluate")
        assert callable(pred.evaluate)
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=50)
    def test_has_get_name_method(self, pred):
        """JaccardAtK should have get_name method."""
        assert hasattr(pred, "get_name")
        name = pred.get_name()
        assert isinstance(name, str)
        assert len(name) > 0


# ============================================================================
# Jaccard Computation Properties
# ============================================================================


class TestJaccardComputationProperties:
    """Test mathematical properties of Jaccard similarity computation."""
    
    @pytest.mark.property
    @given(
        k=st.integers(min_value=1, max_value=20),
        n_baseline=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=50)
    def test_identical_sets_have_jaccard_one(self, k, n_baseline):
        """Jaccard(A, A) = 1.0 for identical sets."""
        assume(n_baseline >= k)
        
        pred = JaccardAtK(k=k, threshold=0.5)
        
        # Create identical baseline and perturbed results
        baseline = mock_query_result(n_items=n_baseline).example()
        perturbed_results = [(0.0, baseline)]  # No perturbation
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        # Jaccard of identical sets should be 1.0
        assert 0.0 in evidence["jaccard_scores"]
        assert evidence["jaccard_scores"][0.0] == 1.0
    
    @pytest.mark.property
    @given(
        k=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50)
    def test_jaccard_is_between_zero_and_one(self, k):
        """Jaccard similarity is always in [0, 1]."""
        pred = JaccardAtK(k=k, threshold=0.5)
        
        # Create baseline and different perturbed result
        baseline = mock_query_result(n_items=k * 2).example()
        perturbed = mock_query_result(n_items=k * 2).example()
        perturbed_results = [(0.1, perturbed)]
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        # All Jaccard scores should be in [0, 1]
        for score in evidence["jaccard_scores"].values():
            assert 0.0 <= score <= 1.0
    
    @pytest.mark.property
    @given(
        k=st.integers(min_value=2, max_value=20),
        n_baseline=st.integers(min_value=3, max_value=50),
    )
    @settings(max_examples=50)
    def test_jaccard_is_symmetric(self, k, n_baseline):
        """Jaccard(A, B) = Jaccard(B, A) - symmetry property."""
        assume(n_baseline >= k)
        
        pred = JaccardAtK(k=k, threshold=0.5)
        
        # Create two different results
        baseline = mock_query_result(n_items=n_baseline).example()
        perturbed = mock_query_result(n_items=n_baseline).example()
        
        # Compute Jaccard(baseline, perturbed)
        _, evidence1 = pred.evaluate(baseline, [(0.1, perturbed)])
        score1 = evidence1["jaccard_scores"][0.1]
        
        # Compute Jaccard(perturbed, baseline) - swap
        _, evidence2 = pred.evaluate(perturbed, [(0.1, baseline)])
        score2 = evidence2["jaccard_scores"][0.1]
        
        # Should be equal (symmetric)
        assert abs(score1 - score2) < 1e-9


# ============================================================================
# Domain Semantics Tests
# ============================================================================


class TestDomainSemantics:
    """Test domain semantics (all_p_leq_pmax, exists_p_leq_pmax)."""
    
    @pytest.mark.property
    @given(
        k=st.integers(min_value=1, max_value=10),
        threshold=st.floats(min_value=0.5, max_value=0.99),
    )
    @settings(max_examples=50)
    def test_all_domain_requires_all_pass(self, k, threshold):
        """'all_p_leq_pmax' domain requires all perturbations pass threshold."""
        pred = JaccardAtK(k=k, threshold=threshold)
        
        baseline = mock_query_result(n_items=k).example()
        
        # Create perturbed results where all pass threshold
        perturbed_results = [(p, baseline) for p in [0.0, 0.1, 0.2]]  # Identical = Jaccard 1.0
        
        passed, evidence = pred.evaluate(baseline, perturbed_results, domain="all_p_leq_pmax")
        
        # All have Jaccard 1.0 >= threshold, so should pass
        assert passed is True
        assert evidence["domain"] == "all_p_leq_pmax"
    
    @pytest.mark.property
    @given(
        k=st.integers(min_value=1, max_value=10),
        threshold=st.floats(min_value=0.5, max_value=0.99),
    )
    @settings(max_examples=50)
    def test_exists_domain_requires_one_pass(self, k, threshold):
        """'exists_p_leq_pmax' domain requires at least one perturbation pass."""
        pred = JaccardAtK(k=k, threshold=threshold)
        
        baseline = mock_query_result(n_items=k).example()
        different = mock_query_result(n_items=k).example()
        
        # Mix: one identical (pass), others different (may fail)
        perturbed_results = [
            (0.0, baseline),   # Identical - will pass
            (0.1, different),  # Different - may fail
        ]
        
        passed, evidence = pred.evaluate(baseline, perturbed_results, domain="exists_p_leq_pmax")
        
        # At least one (p=0.0) has Jaccard 1.0 >= threshold
        assert evidence["domain"] == "exists_p_leq_pmax"
        # exists semantics: at least one must pass
        assert any(score >= threshold for score in evidence["jaccard_scores"].values())


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestJaccardAtKEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.property
    @given(k=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_empty_baseline_fails_gracefully(self, k):
        """Empty baseline should fail with informative error."""
        pred = JaccardAtK(k=k, threshold=0.85)
        
        baseline = mock_query_result(n_items=0).example()
        perturbed_results = [(0.1, baseline)]
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        assert passed is False
        assert "error" in evidence
        assert evidence["error"] == "insufficient_baseline"
    
    @pytest.mark.property
    @given(k=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_baseline_smaller_than_k_fails(self, k):
        """Baseline with fewer than k items should fail."""
        assume(k > 1)
        
        pred = JaccardAtK(k=k, threshold=0.85)
        
        baseline = mock_query_result(n_items=k - 1).example()
        perturbed_results = [(0.1, baseline)]
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        assert passed is False
        assert evidence["baseline_size"] < k
    
    @pytest.mark.property
    @given(k=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_empty_perturbed_results_has_zero_jaccard(self, k):
        """Empty perturbed result should yield Jaccard = 0."""
        pred = JaccardAtK(k=k, threshold=0.5)
        
        baseline = mock_query_result(n_items=k * 2).example()
        perturbed_empty = mock_query_result(n_items=0).example()
        perturbed_results = [(0.1, perturbed_empty)]
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        # Empty perturbed result -> Jaccard = 0
        assert evidence["jaccard_scores"][0.1] == 0.0
    
    @pytest.mark.property
    @given(k=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_no_perturbed_results_completes_successfully(self, k):
        """No perturbed results should complete without error."""
        pred = JaccardAtK(k=k, threshold=0.5)
        
        baseline = mock_query_result(n_items=k * 2).example()
        perturbed_results = []  # Empty list
        
        passed, evidence = pred.evaluate(baseline, perturbed_results)
        
        # Should complete with empty scores
        assert "jaccard_scores" in evidence
        assert len(evidence["jaccard_scores"]) == 0


# ============================================================================
# Invariant Tests
# ============================================================================


class TestJaccardAtKInvariants:
    """Test invariants that must hold for JaccardAtK."""
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=100)
    def test_k_is_always_positive(self, pred):
        """k should always be positive after construction."""
        assert pred.k > 0
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=100)
    def test_threshold_is_probability(self, pred):
        """threshold should always be in [0, 1]."""
        assert 0.0 <= pred.threshold <= 1.0
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=50)
    def test_evaluate_returns_tuple(self, pred):
        """evaluate() should always return (bool, dict) tuple."""
        baseline = mock_query_result(n_items=pred.k * 2).example()
        perturbed_results = [(0.1, baseline)]
        
        result = pred.evaluate(baseline, perturbed_results)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], dict)
    
    @pytest.mark.property
    @given(pred=jaccard_predicate())
    @settings(max_examples=50)
    def test_evidence_contains_required_fields(self, pred):
        """Evidence dict should contain required fields."""
        baseline = mock_query_result(n_items=pred.k * 2).example()
        perturbed_results = [(0.1, baseline)]
        
        _, evidence = pred.evaluate(baseline, perturbed_results)
        
        # Check required fields
        assert "predicate" in evidence
        assert "k" in evidence
        assert "threshold" in evidence
        assert "jaccard_scores" in evidence
        assert "passed" in evidence
        assert "domain" in evidence
