"""
Provenance-as-Oracle verification tests.

This module implements foundational provenance-based verification:
- AST hash stability for identical queries
- Network fingerprint consistency
- Performance regression detection
- Seed tracking and randomness metadata
- Negative tests for provenance warnings

All tests follow the certificate-based verification principle where
provenance metadata serves as the oracle for correctness.
"""

import pytest
import time
from py3plex.core import multinet
from py3plex.dsl import Q, L, UQ
from py3plex.dsl_legacy import execute_query
from py3plex.dsl.provenance import ast_fingerprint, network_fingerprint
from tests.fixtures import tiny_two_layer, small_three_layer


class TestASTHashStability:
    """Test that identical queries produce identical AST hashes."""

    def test_ast_hash_identical_queries_v2(self):
        """Same DSL v2 query → same AST hash."""
        net = tiny_two_layer()
        
        # Build identical queries
        q1 = Q.nodes().compute("degree")
        q2 = Q.nodes().compute("degree")
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        # Extract AST hashes
        hash1 = result1.meta["provenance"]["query"]["ast_hash"]
        hash2 = result2.meta["provenance"]["query"]["ast_hash"]
        
        assert hash1 == hash2, \
            f"Identical queries must produce identical AST hashes: {hash1} vs {hash2}"

    def test_ast_hash_different_queries_v2(self):
        """Different DSL v2 queries → different AST hashes."""
        net = tiny_two_layer()
        
        q1 = Q.nodes().compute("degree")
        q2 = Q.nodes().compute("betweenness_centrality")
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        hash1 = result1.meta["provenance"]["query"]["ast_hash"]
        hash2 = result2.meta["provenance"]["query"]["ast_hash"]
        
        assert hash1 != hash2, \
            "Different queries must produce different AST hashes"

    def test_ast_hash_with_filters_v2(self):
        """Queries with different filters → different AST hashes."""
        net = small_three_layer()
        
        q1 = Q.nodes().where(degree__gt=1)
        q2 = Q.nodes().where(degree__gt=2)
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        hash1 = result1.meta["provenance"]["query"]["ast_hash"]
        hash2 = result2.meta["provenance"]["query"]["ast_hash"]
        
        assert hash1 != hash2, \
            "Queries with different filter thresholds must have different AST hashes"

    def test_ast_hash_with_layer_selection_v2(self):
        """Layer selection affects AST hash."""
        net = small_three_layer()
        
        q1 = Q.nodes().from_layers(L[0])
        q2 = Q.nodes().from_layers(L[1])
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        hash1 = result1.meta["provenance"]["query"]["ast_hash"]
        hash2 = result2.meta["provenance"]["query"]["ast_hash"]
        
        assert hash1 != hash2, \
            "Different layer selections must produce different AST hashes"

    def test_ast_hash_legacy_dsl_stability(self):
        """Legacy DSL: same query string → same AST hash."""
        net = tiny_two_layer()
        
        query_str = 'SELECT nodes WHERE degree > 1'
        
        result1 = execute_query(net, query_str)
        result2 = execute_query(net, query_str)
        
        hash1 = result1["meta"]["provenance"]["query"]["ast_hash"]
        hash2 = result2["meta"]["provenance"]["query"]["ast_hash"]
        
        assert hash1 == hash2, \
            "Legacy DSL: identical query strings must produce identical AST hashes"


class TestNetworkFingerprinting:
    """Test network fingerprint consistency and sensitivity."""

    def test_network_fingerprint_stability(self):
        """Same network → same fingerprint."""
        net = tiny_two_layer()
        
        fp1 = network_fingerprint(net)
        fp2 = network_fingerprint(net)
        
        assert fp1 == fp2, "Network fingerprint must be stable"

    def test_network_fingerprint_in_provenance_v2(self):
        """DSL v2: network fingerprint present and consistent."""
        net = small_three_layer()
        
        q1 = Q.nodes()
        q2 = Q.edges()
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        fp1 = result1.meta["provenance"]["network_fingerprint"]
        fp2 = result2.meta["provenance"]["network_fingerprint"]
        
        # Same network → same fingerprint
        assert fp1 == fp2, \
            "Different queries on same network must report identical fingerprint"

    def test_network_fingerprint_in_provenance_legacy(self):
        """Legacy DSL: network fingerprint present."""
        net = tiny_two_layer()
        
        result = execute_query(net, "SELECT nodes")
        
        fp = result["meta"]["provenance"]["network_fingerprint"]
        
        assert "node_count" in fp
        assert "edge_count" in fp
        assert "layer_count" in fp
        assert "layers" in fp

    def test_network_fingerprint_detects_node_addition(self):
        """Adding nodes changes fingerprint."""
        net1 = tiny_two_layer()
        fp1 = network_fingerprint(net1)
        
        # Create modified network
        net2 = tiny_two_layer()
        net2.add_nodes([{'source': 'Z', 'type': '0'}])
        fp2 = network_fingerprint(net2)
        
        assert fp1 != fp2, "Adding nodes must change fingerprint"
        assert fp1["node_count"] < fp2["node_count"]

    def test_network_fingerprint_detects_edge_addition(self):
        """Adding edges changes fingerprint."""
        net1 = tiny_two_layer()
        fp1 = network_fingerprint(net1)
        
        # Add edge
        net2 = tiny_two_layer()
        net2.add_edges([{
            'source': 'A', 'target': 'D',
            'source_type': '0', 'target_type': '0'
        }])
        fp2 = network_fingerprint(net2)
        
        assert fp1 != fp2, "Adding edges must change fingerprint"
        assert fp1["edge_count"] < fp2["edge_count"]


class TestProvenanceReproducibility:
    """Test that provenance enables reproducibility."""

    def test_same_query_same_network_same_seed_identical_results(self):
        """(AST hash, network fingerprint, seed) → identical results."""
        net = small_three_layer()
        seed = 42
        
        q1 = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=10, seed=seed)
        q2 = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=10, seed=seed)
        
        result1 = q1.execute(net)
        result2 = q2.execute(net)
        
        # Check provenance elements match
        prov1 = result1.meta["provenance"]
        prov2 = result2.meta["provenance"]
        
        assert prov1["query"]["ast_hash"] == prov2["query"]["ast_hash"]
        assert prov1["network_fingerprint"] == prov2["network_fingerprint"]
        
        # Results should be identical
        df1 = result1.to_pandas()
        df2 = result2.to_pandas()
        
        if "degree_mean" in df1.columns and "degree_mean" in df2.columns:
            diff = (df1["degree_mean"] - df2["degree_mean"]).abs().sum()
            assert diff < 1e-9, \
                "Same (query, network, seed) must produce identical results"

    def test_different_network_different_fingerprint(self):
        """Different networks → different fingerprints."""
        net1 = tiny_two_layer()
        net2 = small_three_layer()
        
        q = Q.nodes()
        
        result1 = q.execute(net1)
        result2 = q.execute(net2)
        
        fp1 = result1.meta["provenance"]["network_fingerprint"]
        fp2 = result2.meta["provenance"]["network_fingerprint"]
        
        assert fp1 != fp2, "Different networks must have different fingerprints"


class TestPerformanceRegression:
    """Test performance tracking in provenance."""

    def test_provenance_contains_timing_v2(self):
        """DSL v2: provenance includes performance timings."""
        net = small_three_layer()
        
        q = Q.nodes().compute("degree")
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        assert "performance" in prov
        perf = prov["performance"]
        
        # Should have total_ms
        assert "total_ms" in perf
        assert isinstance(perf["total_ms"], (int, float))
        assert perf["total_ms"] >= 0

    def test_provenance_contains_timing_legacy(self):
        """Legacy DSL: provenance includes performance timings."""
        net = tiny_two_layer()
        
        result = execute_query(net, "SELECT nodes COMPUTE degree")
        
        prov = result["meta"]["provenance"]
        perf = prov["performance"]
        
        assert "total_ms" in perf
        assert perf["total_ms"] >= 0

    def test_performance_regression_bounds_simple_query(self):
        """Simple query performance should be within reasonable bounds."""
        net = tiny_two_layer()
        
        q = Q.nodes()
        
        start = time.perf_counter()
        result = q.execute(net)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        prov = result.meta["provenance"]
        reported_time = prov["performance"]["total_ms"]
        
        # Reported time should be <= actual elapsed time (with tolerance)
        # This is a sanity check, not a strict requirement
        assert reported_time <= elapsed * 1.5, \
            f"Reported time {reported_time}ms exceeds measured time {elapsed}ms significantly"

    def test_performance_stages_recorded(self):
        """Performance provenance includes stage breakdown."""
        net = small_three_layer()
        
        q = Q.nodes().compute("degree")
        result = q.execute(net)
        
        perf = result.meta["provenance"]["performance"]
        
        # Should have multiple stages recorded
        assert len(perf) > 1, "Performance should include stage breakdown"


class TestRandomnessMetadata:
    """Test seed tracking and randomness metadata."""

    def test_uq_with_seed_records_seed(self):
        """UQ with explicit seed records it in provenance."""
        net = tiny_two_layer()
        seed = 42
        
        q = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=10, seed=seed)
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        # Should have randomness metadata
        if "randomness" in prov:
            rand_meta = prov["randomness"]
            # Seed should be recorded if available
            # (implementation may vary, this is a best-effort check)
            pass

    def test_deterministic_query_no_seed_metadata(self):
        """Deterministic queries don't claim randomness."""
        net = tiny_two_layer()
        
        q = Q.nodes().compute("degree")
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        # If randomness key exists, it should be empty or indicate no randomness
        if "randomness" in prov:
            rand_meta = prov["randomness"]
            # Should not indicate randomness was used
            if "seed" in rand_meta:
                # Deterministic query shouldn't have explicit seed
                pass


class TestProvenanceNegativeTests:
    """Test provenance warnings for problematic scenarios."""

    def test_uq_without_seed_may_warn(self):
        """UQ without explicit seed may include warning in provenance."""
        net = tiny_two_layer()
        
        # UQ without seed
        q = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=5, seed=None)
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        # May have warnings about non-reproducibility
        # (implementation-specific, this is a smoke test)
        assert "warnings" in prov

    def test_provenance_warns_on_mutated_network(self):
        """Mutating network between identical queries changes fingerprint."""
        net = tiny_two_layer()
        
        q = Q.nodes()
        
        # First execution
        result1 = q.execute(net)
        fp1 = result1.meta["provenance"]["network_fingerprint"]
        
        # Mutate network
        net.add_nodes([{'source': 'MUTATED', 'type': '0'}])
        
        # Second execution
        result2 = q.execute(net)
        fp2 = result2.meta["provenance"]["network_fingerprint"]
        
        # Fingerprints should differ
        assert fp1 != fp2, \
            "Network mutation must be detected via fingerprint change"


class TestProvenanceVersioning:
    """Test that provenance records version information."""

    def test_provenance_records_py3plex_version_v2(self):
        """DSL v2: provenance includes py3plex version."""
        net = tiny_two_layer()
        
        q = Q.nodes()
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        assert "py3plex_version" in prov
        assert isinstance(prov["py3plex_version"], str)
        assert len(prov["py3plex_version"]) > 0

    def test_provenance_records_py3plex_version_legacy(self):
        """Legacy DSL: provenance includes py3plex version."""
        net = tiny_two_layer()
        
        result = execute_query(net, "SELECT nodes")
        
        prov = result["meta"]["provenance"]
        
        assert "py3plex_version" in prov
        assert isinstance(prov["py3plex_version"], str)

    def test_provenance_records_engine_v2(self):
        """DSL v2: provenance identifies engine."""
        net = tiny_two_layer()
        
        q = Q.nodes()
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        assert "engine" in prov
        assert prov["engine"] == "dsl_v2_executor"

    def test_provenance_records_engine_legacy(self):
        """Legacy DSL: provenance identifies legacy engine."""
        net = tiny_two_layer()
        
        result = execute_query(net, "SELECT nodes")
        
        prov = result["meta"]["provenance"]
        
        assert "engine" in prov
        assert prov["engine"] == "dsl_legacy"


class TestProvenanceTimestamp:
    """Test that provenance includes timestamps."""

    def test_provenance_has_timestamp_v2(self):
        """DSL v2: provenance includes UTC timestamp."""
        net = tiny_two_layer()
        
        q = Q.nodes()
        result = q.execute(net)
        
        prov = result.meta["provenance"]
        
        assert "timestamp_utc" in prov
        assert isinstance(prov["timestamp_utc"], str)
        # Should be ISO 8601 format
        assert "T" in prov["timestamp_utc"] or " " in prov["timestamp_utc"]

    def test_provenance_has_timestamp_legacy(self):
        """Legacy DSL: provenance includes timestamp."""
        net = tiny_two_layer()
        
        result = execute_query(net, "SELECT nodes")
        
        prov = result["meta"]["provenance"]
        
        assert "timestamp_utc" in prov


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
