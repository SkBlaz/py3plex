"""Additional tests for claims types module.

This test suite covers edge cases and functions not fully tested in the main
test_claim_learning.py file.
"""

import pytest
from py3plex.claims import Claim, Antecedent, Consequent, ClaimScore


class TestAntecedentEvaluation:
    """Test Antecedent evaluation edge cases."""
    
    def test_antecedent_threshold_gte(self):
        """Test threshold antecedent with >= operator."""
        ant = Antecedent(metric="degree", predicate_type="threshold", 
                        threshold=5.0, operator=">=")
        
        assert ant.evaluate({"degree": 6.0}) is True
        assert ant.evaluate({"degree": 5.0}) is True
        assert ant.evaluate({"degree": 4.0}) is False
    
    def test_antecedent_threshold_lt(self):
        """Test threshold antecedent with < operator."""
        ant = Antecedent(metric="strength", predicate_type="threshold",
                        threshold=10.0, operator="<")
        
        assert ant.evaluate({"strength": 9.0}) is True
        assert ant.evaluate({"strength": 10.0}) is False
        assert ant.evaluate({"strength": 11.0}) is False
    
    def test_antecedent_threshold_eq(self):
        """Test threshold antecedent with = operator."""
        ant = Antecedent(metric="layer_count", predicate_type="threshold",
                        threshold=2.0, operator="=")
        
        assert ant.evaluate({"layer_count": 2.0}) is True
        assert ant.evaluate({"layer_count": 3.0}) is False
    
    def test_antecedent_missing_metric(self):
        """Test antecedent with missing metric returns False."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        
        assert ant.evaluate({"other_metric": 10.0}) is False
        assert ant.evaluate({}) is False
    
    def test_antecedent_top_p(self):
        """Test top_p antecedent evaluation."""
        ant = Antecedent(metric="pagerank", predicate_type="top_p",
                        percentile=0.2)
        
        all_values = {"pagerank": [0.1, 0.2, 0.3, 0.4, 0.5]}
        
        # Top 20% threshold is 0.5 (1 value)
        assert ant.evaluate({"pagerank": 0.5}, all_values) is True
        assert ant.evaluate({"pagerank": 0.3}, all_values) is False
    
    def test_antecedent_top_p_missing_all_values(self):
        """Test top_p antecedent without all_values returns False."""
        ant = Antecedent(metric="pagerank", predicate_type="top_p",
                        percentile=0.1)
        
        assert ant.evaluate({"pagerank": 0.9}) is False
        assert ant.evaluate({"pagerank": 0.9}, {}) is False
    
    def test_antecedent_layer_count(self):
        """Test layer_count antecedent."""
        ant = Antecedent(metric="layer_count", predicate_type="layer_count",
                        threshold=3.0, operator=">=")
        
        assert ant.evaluate({"layer_count": 4}) is True
        assert ant.evaluate({"layer_count": 3}) is True
        assert ant.evaluate({"layer_count": 2}) is False
        assert ant.evaluate({}) is False  # Default to 0


class TestAntecedentDSLString:
    """Test Antecedent DSL string conversion."""
    
    def test_threshold_gte_dsl_string(self):
        """Test DSL string for threshold >= predicate."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        
        assert ant.to_dsl_string() == "degree__gte(5.0)"
    
    def test_threshold_lt_dsl_string(self):
        """Test DSL string for threshold < predicate."""
        ant = Antecedent(metric="strength", predicate_type="threshold",
                        threshold=10.0, operator="<")
        
        assert ant.to_dsl_string() == "strength__lt(10.0)"
    
    def test_threshold_eq_dsl_string(self):
        """Test DSL string for threshold = predicate."""
        ant = Antecedent(metric="layer_count", predicate_type="threshold",
                        threshold=2.0, operator="=")
        
        assert ant.to_dsl_string() == "layer_count__eq(2.0)"
    
    def test_top_p_dsl_string(self):
        """Test DSL string for top_p predicate."""
        ant = Antecedent(metric="pagerank", predicate_type="top_p",
                        percentile=0.1)
        
        assert ant.to_dsl_string() == "top_p(pagerank, 0.1)"
    
    def test_layer_count_dsl_string(self):
        """Test DSL string for layer_count predicate."""
        ant = Antecedent(metric="layer_count", predicate_type="layer_count",
                        threshold=3.0, operator=">=")
        
        assert ant.to_dsl_string() == "layer_count__gte(3.0)"


class TestConsequentEvaluation:
    """Test Consequent evaluation edge cases."""
    
    def test_consequent_rank_predicate(self):
        """Test rank consequent evaluation."""
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        
        # Create all_values for ranking
        all_values = {"pagerank": [0.1, 0.2, 0.3, 0.4, 0.5]}
        
        # Node with pagerank 0.5 should be rank 1 (highest)
        assert cons.evaluate({"pagerank": 0.5}, all_values) is True
        # Node with pagerank 0.1 should be rank 5 (lowest)
        assert cons.evaluate({"pagerank": 0.1}, all_values) is True  # <= 10
    
    def test_consequent_threshold_predicate(self):
        """Test threshold consequent evaluation."""
        cons = Consequent(metric="centrality", predicate_type="threshold",
                         threshold=0.5, operator=">=")
        
        assert cons.evaluate({"centrality": 0.6}) is True
        assert cons.evaluate({"centrality": 0.4}) is False
    
    def test_consequent_missing_metric(self):
        """Test consequent with missing metric returns False."""
        cons = Consequent(metric="centrality", predicate_type="threshold",
                         threshold=0.5, operator=">=")
        
        assert cons.evaluate({}) is False
        assert cons.evaluate({"other": 1.0}) is False


class TestConsequentDSLString:
    """Test Consequent DSL string conversion."""
    
    def test_rank_dsl_string(self):
        """Test DSL string for rank predicate."""
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        
        assert cons.to_dsl_string() == "pagerank__rank_lte(10)"
    
    def test_threshold_dsl_string(self):
        """Test DSL string for threshold predicate."""
        cons = Consequent(metric="centrality", predicate_type="threshold",
                         threshold=0.5, operator=">=")
        
        assert cons.to_dsl_string() == "centrality__gte(0.5)"


class TestClaimScore:
    """Test ClaimScore edge cases."""
    
    def test_claim_score_validation(self):
        """Test ClaimScore validates ranges."""
        # Valid scores
        score = ClaimScore(support=0.95, coverage=0.3,
                          n_antecedent=100, n_both=45, n_total=150)
        assert score.support == 0.95
        
    def test_claim_score_rounding(self):
        """Test ClaimScore rounds floats for determinism."""
        score = ClaimScore(support=0.9123456789, coverage=0.2345678901,
                          n_antecedent=50, n_both=35, n_total=100)
        
        # Should be rounded to 6 decimal places
        assert score.support == 0.912346
        assert score.coverage == 0.234568


class TestClaim:
    """Test Claim edge cases."""
    
    def test_claim_support_property(self):
        """Test Claim support property delegates to score."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        score = ClaimScore(support=0.92, coverage=0.25,
                          n_antecedent=100, n_both=46, n_total=150)
        
        claim = Claim(antecedent=ant, consequent=cons, score=score,
                     claim_string="test claim")
        
        assert claim.support == 0.92
    
    def test_claim_coverage_property(self):
        """Test Claim coverage property delegates to score."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        score = ClaimScore(support=0.92, coverage=0.25,
                          n_antecedent=100, n_both=46, n_total=150)
        
        claim = Claim(antecedent=ant, consequent=cons, score=score,
                     claim_string="test claim")
        
        assert claim.coverage == 0.25
    
    def test_claim_to_dict(self):
        """Test Claim serialization to dict."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        score = ClaimScore(support=0.92, coverage=0.25,
                          n_antecedent=100, n_both=46, n_total=150)
        
        claim = Claim(antecedent=ant, consequent=cons, score=score,
                     claim_string="IF degree >= 5 THEN pagerank_rank <= 10")
        
        data = claim.to_dict()
        
        assert isinstance(data, dict)
        assert "antecedent" in data
        assert "consequent" in data
        assert "score" in data
        assert "claim_string" in data
        assert data["claim_string"] == "IF degree >= 5 THEN pagerank_rank <= 10"
    
    def test_claim_repr(self):
        """Test Claim string representation."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        cons = Consequent(metric="pagerank", predicate_type="rank",
                         rank=10, rank_operator="<=")
        score = ClaimScore(support=0.92, coverage=0.25,
                          n_antecedent=100, n_both=46, n_total=150)
        
        claim = Claim(antecedent=ant, consequent=cons, score=score,
                     claim_string="test claim", meta={"dataset": "test_network"})
        
        repr_str = repr(claim)
        assert "Claim" in repr_str
        assert "support=0.92" in repr_str or "0.92" in repr_str
    
    def test_claim_immutability(self):
        """Test that Antecedent and Consequent are immutable."""
        ant = Antecedent(metric="degree", predicate_type="threshold",
                        threshold=5.0, operator=">=")
        
        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            ant.metric = "strength"


class TestClaimIntegration:
    """Test integration between Claim components."""
    
    def test_claim_with_all_operators(self):
        """Test claims with different operators."""
        operators = [">=", ">", "<=", "<", "="]
        
        for op in operators:
            ant = Antecedent(metric="degree", predicate_type="threshold",
                           threshold=5.0, operator=op)
            cons = Consequent(metric="pagerank", predicate_type="threshold",
                            threshold=0.1, operator=op)
            score = ClaimScore(support=0.9, coverage=0.2,
                              n_antecedent=50, n_both=35, n_total=100)
            
            claim = Claim(antecedent=ant, consequent=cons, score=score,
                         claim_string=f"test claim with {op}")
            
            # Verify claim is created successfully
            assert claim.antecedent.operator == op
            assert claim.consequent.operator == op
