"""Tests for counterexample generation module.

This test suite covers:
- Claim parsing and compilation
- Violation finding
- Witness extraction
- Minimization
- Full counterexample generation
- DSL integration
- Provenance
- Determinism
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.counterexamples import (
    find_counterexample,
    Counterexample,
    Budget,
)
from py3plex.counterexamples.claim_lang import (
    parse_claim,
    ClaimParseError,
    compute_claim_hash,
    parse_and_compile_claim,
)
from py3plex.counterexamples.engine import CounterexampleNotFound


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_network():
    """Create a simple network for testing.

    Structure: 3 nodes in layer1, with A having high degree but low PageRank
    (isolated hub pattern).
    """
    net = multinet.multi_layer_network(directed=False)

    # Add nodes
    nodes = [
        {"source": "A", "type": "layer1"},
        {"source": "B", "type": "layer1"},
        {"source": "C", "type": "layer1"},
        {"source": "D", "type": "layer1"},
    ]
    net.add_nodes(nodes)

    # Add edges: A is connected to B, C, D
    # B-C-D form a triangle with higher PageRank
    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "C",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "D",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
        {
            "source": "C",
            "target": "D",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
        {
            "source": "D",
            "target": "B",
            "source_type": "layer1",
            "target_type": "layer1",
            "weight": 1.0,
        },
    ]
    net.add_edges(edges)

    return net


@pytest.fixture
def multilayer_network():
    """Create a multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False)

    # Add nodes in two layers
    nodes = [
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "social"},
        {"source": "A", "type": "work"},
        {"source": "B", "type": "work"},
    ]
    net.add_nodes(nodes)

    # Add edges
    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "social",
            "target_type": "social",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "social",
            "target_type": "social",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "B",
            "source_type": "work",
            "target_type": "work",
            "weight": 1.0,
        },
    ]
    net.add_edges(edges)

    return net


# ============================================================================
# Claim Parser Tests
# ============================================================================


class TestClaimParser:
    """Test claim string parsing."""

    def test_parse_valid_claim(self):
        """Test parsing a valid claim."""
        claim_str = "degree__ge(k) -> pagerank__rank_gt(r)"
        params = {"k": 10, "r": 50}

        normalized, antecedent, consequent = parse_claim(claim_str, params)

        assert "->" in normalized
        assert callable(antecedent)
        assert callable(consequent)

    def test_parse_missing_arrow(self):
        """Test that missing arrow raises error."""
        with pytest.raises(ClaimParseError) as exc_info:
            parse_claim("degree__ge(k)", {})

        assert "must contain '->'" in str(exc_info.value)

    def test_parse_missing_param(self):
        """Test that missing parameter raises error."""
        with pytest.raises(ClaimParseError) as exc_info:
            parse_claim("degree__ge(k) -> pagerank__gt(x)", {})

        assert "Parameter" in str(exc_info.value)

    def test_parse_invalid_comparator(self):
        """Test that invalid comparator raises error."""
        with pytest.raises(ClaimParseError) as exc_info:
            parse_claim("degree__invalid(k) -> pagerank__gt(x)", {"k": 10, "x": 0.5})

        assert "comparator" in str(exc_info.value).lower()

    def test_claim_hash_stable(self):
        """Test that claim hash is stable."""
        claim_str = "degree__ge(k) -> pagerank__rank_gt(r)"
        params = {"k": 10, "r": 50}

        hash1 = compute_claim_hash(claim_str, params)
        hash2 = compute_claim_hash(claim_str, params)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest

    def test_parse_and_compile(self):
        """Test full claim parsing and compilation."""
        claim_str = "degree__ge(k) -> pagerank__rank_gt(r)"
        params = {"k": 10, "r": 50}

        claim = parse_and_compile_claim(claim_str, params)

        assert claim.claim_str == claim_str.strip()
        assert claim.params == params
        assert len(claim.claim_hash) == 64


# ============================================================================
# Counterexample Finding Tests
# ============================================================================


class TestCounterexampleFinding:
    """Test counterexample generation."""

    def test_find_counterexample_simple(self, simple_network):
        """Test finding a basic counterexample."""
        # This claim should be violated: high degree doesn't guarantee high PageRank rank
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=False,
        )

        assert cex is not None
        assert isinstance(cex, Counterexample)
        assert cex.violation is not None
        assert cex.subgraph is not None

    def test_counterexample_not_found(self, simple_network):
        """Test that non-violating claim raises CounterexampleNotFound."""
        # This claim should hold: all nodes have degree >= 0
        claim = "degree__ge(k) -> degree__ge(k)"
        params = {"k": 0}

        with pytest.raises(CounterexampleNotFound):
            find_counterexample(
                simple_network,
                claim,
                params,
                seed=42,
            )

    def test_counterexample_with_minimization(self, simple_network):
        """Test counterexample with minimization enabled."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=True,
        )

        assert cex is not None
        assert cex.minimization is not None
        assert cex.minimization.tests_used >= 0

    def test_counterexample_provenance(self, simple_network):
        """Test that counterexample has proper provenance."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
        )

        assert "provenance" in cex.meta
        prov = cex.meta["provenance"]

        assert prov["engine"] == "counterexample_engine"
        assert "timestamp_utc" in prov
        assert prov["randomness"]["seed"] == 42
        assert "performance" in prov
        assert "claim" in prov
        assert prov["claim"]["claim_hash"] is not None

    def test_counterexample_explain(self, simple_network):
        """Test that counterexample explanation is generated."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
        )

        explanation = cex.explain()

        assert "COUNTEREXAMPLE" in explanation
        assert "Violating Node" in explanation
        assert "Witness subgraph" in explanation

    def test_counterexample_to_dict(self, simple_network):
        """Test that counterexample serializes to dict."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
        )

        cex_dict = cex.to_dict()

        assert "violation" in cex_dict
        assert "witness" in cex_dict
        assert "minimization" in cex_dict
        assert "meta" in cex_dict


# ============================================================================
# Determinism Tests
# ============================================================================


class TestDeterminism:
    """Test deterministic behavior with same seed."""

    def test_same_seed_same_violation(self, simple_network):
        """Test that same seed produces same violation."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex1 = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=False,
        )

        cex2 = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=False,
        )

        # Same violating node
        assert cex1.violation.node == cex2.violation.node
        assert cex1.violation.layer == cex2.violation.layer

    def test_different_seed_may_differ(self, simple_network):
        """Test that different seeds may produce different results."""
        # Note: In this simple network, results should be same, but this tests the seed mechanism
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        cex1 = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=False,
        )

        cex2 = find_counterexample(
            simple_network,
            claim,
            params,
            seed=100,
            find_minimal=False,
        )

        # Both should find a counterexample
        assert cex1 is not None
        assert cex2 is not None


# ============================================================================
# Budget Tests
# ============================================================================


class TestBudget:
    """Test budget enforcement."""

    def test_budget_max_tests(self, simple_network):
        """Test that max_tests budget is respected."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 2, "r": 2}

        budget = Budget(max_tests=5, max_witness_size=500)

        cex = find_counterexample(
            simple_network,
            claim,
            params,
            seed=42,
            find_minimal=True,
            budget=budget,
        )

        assert cex.minimization.tests_used <= budget.max_tests

    def test_budget_max_witness_size(self, multilayer_network):
        """Test that max_witness_size is respected."""
        claim = "degree__ge(k) -> pagerank__rank_le(r)"
        params = {"k": 1, "r": 2}

        budget = Budget(max_tests=100, max_witness_size=3)

        cex = find_counterexample(
            multilayer_network,
            claim,
            params,
            seed=42,
            find_minimal=False,
            budget=budget,
        )

        # Witness should not exceed budget
        assert len(cex.witness_nodes) <= budget.max_witness_size


# ============================================================================
# DSL Integration Tests
# ============================================================================


class TestDSLIntegration:
    """Test DSL v2 integration."""

    def test_q_counterexample_builder(self, simple_network):
        """Test Q.counterexample() builder API."""
        cex = (
            Q.counterexample()
            .claim("degree__ge(k) -> pagerank__rank_le(r)")
            .params(k=2, r=2)
            .seed(42)
            .find_minimal(False)
            .execute(simple_network)
        )

        assert cex is not None
        assert isinstance(cex, Counterexample)

    def test_q_counterexample_with_layers(self, multilayer_network):
        """Test Q.counterexample() with layer selection."""
        from py3plex.dsl import L

        try:
            cex = (
                Q.counterexample()
                .claim("degree__ge(k) -> pagerank__rank_le(r)")
                .params(k=1, r=2)
                .layers(L["social"])
                .seed(42)
                .execute(multilayer_network)
            )

            # If we find a counterexample, great!
            assert cex is not None
        except CounterexampleNotFound:
            # No violation found - that's acceptable for this test
            # We're mainly testing that the layer selection doesn't crash
            pass


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_network(self):
        """Test counterexample on empty network."""
        net = multinet.multi_layer_network(directed=False)

        with pytest.raises(CounterexampleNotFound):
            find_counterexample(
                net,
                "degree__ge(k) -> pagerank__rank_le(r)",
                {"k": 1, "r": 1},
                seed=42,
            )

    def test_single_node_network(self):
        """Test counterexample on single-node network."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{"source": "A", "type": "layer1"}])

        # Depending on claim, may or may not find violation
        # This tests that it doesn't crash
        try:
            cex = find_counterexample(
                net,
                "degree__ge(k) -> degree__ge(k)",
                {"k": 0},
                seed=42,
            )
        except CounterexampleNotFound:
            pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
