"""Tests for query provenance tracking.

Tests cover:
- DSL v2 provenance presence and structure
- Legacy DSL provenance
- AST hash stability
- QueryResult backward compatibility
- Provenance fields and types
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, execute_ast, Query, SelectStmt, Target, ConditionExpr, ConditionAtom, Comparison, ComputeItem
from py3plex.dsl_legacy import execute_query
from py3plex.dsl.provenance import (
    ProvenanceBuilder,
    ast_fingerprint,
    ast_summary,
    network_fingerprint,
    get_py3plex_version,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


class TestProvenanceHelpers:
    """Test provenance helper functions."""

    def test_get_py3plex_version(self):
        """Test version extraction."""
        version = get_py3plex_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_network_fingerprint(self, sample_network):
        """Test network fingerprinting."""
        fp = network_fingerprint(sample_network)
        
        assert isinstance(fp, dict)
        assert "node_count" in fp
        assert "edge_count" in fp
        assert "layer_count" in fp
        assert "layers" in fp
        
        assert fp["node_count"] == 5
        assert fp["edge_count"] == 4
        assert fp["layer_count"] == 2
        assert set(fp["layers"]) == {"social", "work"}

    def test_ast_fingerprint_stability(self):
        """Test that AST fingerprint is stable across identical queries."""
        query1 = SelectStmt(target=Target.NODES, where=ConditionExpr(atoms=[ConditionAtom(comparison=Comparison("degree", ">", 5))], ops=[]))
        query2 = SelectStmt(target=Target.NODES, where=ConditionExpr(atoms=[ConditionAtom(comparison=Comparison("degree", ">", 5))], ops=[]))
        
        hash1 = ast_fingerprint(query1)
        hash2 = ast_fingerprint(query2)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_ast_fingerprint_different_queries(self):
        """Test that different queries have different fingerprints."""
        query1 = SelectStmt(target=Target.NODES, where=ConditionExpr(atoms=[ConditionAtom(comparison=Comparison("degree", ">", 5))], ops=[]))
        query2 = SelectStmt(target=Target.NODES, where=ConditionExpr(atoms=[ConditionAtom(comparison=Comparison("degree", ">", 10))], ops=[]))
        
        hash1 = ast_fingerprint(query1)
        hash2 = ast_fingerprint(query2)
        
        assert hash1 != hash2

    def test_ast_summary(self):
        """Test AST summary generation."""
        query = SelectStmt(target=Target.NODES, compute=[ComputeItem(name="betweenness")], limit=10)
        
        summary = ast_summary(query)
        
        assert isinstance(summary, str)
        assert "SELECT nodes" in summary
        assert "COMPUTE" in summary
        assert "LIMIT" in summary


class TestProvenanceBuilder:
    """Test ProvenanceBuilder class."""

    def test_builder_basic(self, sample_network):
        """Test basic builder functionality."""
        builder = ProvenanceBuilder("test_engine")
        builder.start_timer()
        builder.set_network(sample_network)
        builder.record_stage("test_stage", 10.5)
        builder.add_warning("test warning")
        
        prov = builder.build()
        
        assert isinstance(prov, dict)
        assert prov["engine"] == "test_engine"
        assert "py3plex_version" in prov
        assert "timestamp_utc" in prov
        assert "network_fingerprint" in prov
        assert prov["performance"]["test_stage"] == 10.5
        assert "test warning" in prov["warnings"]

    def test_builder_with_query_ast(self, sample_network):
        """Test builder with query AST."""
        query = Query(select=SelectStmt(target=Target.NODES), explain=False)
        
        builder = ProvenanceBuilder("dsl_v2_executor")
        builder.set_network(sample_network)
        builder.set_query_ast(query)
        
        prov = builder.build()
        
        assert "query" in prov
        assert prov["query"]["target"] == "nodes"
        assert "ast_hash" in prov["query"]
        assert "ast_summary" in prov["query"]

    def test_builder_with_legacy_query(self, sample_network):
        """Test builder with legacy query string."""
        query_str = 'SELECT nodes WHERE degree > 5'
        
        builder = ProvenanceBuilder("dsl_legacy")
        builder.set_network(sample_network)
        builder.set_query_legacy(query_str, "nodes")
        
        prov = builder.build()
        
        assert "query" in prov
        assert prov["query"]["target"] == "nodes"
        assert prov["query"]["raw_string"] == query_str
        assert "ast_hash" in prov["query"]


class TestDSLv2Provenance:
    """Test provenance in DSL v2."""

    def test_provenance_exists(self, sample_network):
        """Test that provenance is present in QueryResult."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        assert "provenance" in result.meta
        prov = result.meta["provenance"]
        
        assert isinstance(prov, dict)
        assert prov["engine"] == "dsl_v2_executor"

    def test_provenance_structure(self, sample_network):
        """Test that provenance has the expected structure."""
        q = Q.nodes().compute("degree")
        result = q.execute(sample_network)
        
        prov = result.meta["provenance"]
        
        # Check required top-level keys
        assert "engine" in prov
        assert "py3plex_version" in prov
        assert "timestamp_utc" in prov
        assert "network_fingerprint" in prov
        assert "query" in prov
        assert "randomness" in prov
        assert "backend" in prov
        assert "performance" in prov
        assert "warnings" in prov

    def test_provenance_network_fingerprint(self, sample_network):
        """Test network fingerprint in provenance."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        prov = result.meta["provenance"]
        fp = prov["network_fingerprint"]
        
        assert fp["node_count"] == 5
        assert fp["edge_count"] == 4
        assert fp["layer_count"] == 2

    def test_provenance_query_info(self, sample_network):
        """Test query information in provenance."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        prov = result.meta["provenance"]
        query_info = prov["query"]
        
        assert query_info["target"] == "nodes"
        assert "ast_hash" in query_info
        assert "ast_summary" in query_info
        assert isinstance(query_info["ast_hash"], str)
        assert isinstance(query_info["ast_summary"], str)

    def test_provenance_performance_timings(self, sample_network):
        """Test that performance timings are present and valid."""
        q = Q.nodes().compute("degree")
        result = q.execute(sample_network)
        
        prov = result.meta["provenance"]
        perf = prov["performance"]
        
        # Check that we have timing entries
        assert len(perf) > 0
        
        # Check that timings are non-negative numbers
        for stage, timing in perf.items():
            assert isinstance(timing, (int, float))
            assert timing >= 0
        
        # Should have total_ms
        assert "total_ms" in perf

    def test_provenance_backend_info(self, sample_network):
        """Test backend information in provenance."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        prov = result.meta["provenance"]
        backend = prov["backend"]
        
        assert "graph_backend" in backend
        assert backend["graph_backend"] == "networkx"

    def test_provenance_with_params(self, sample_network):
        """Test provenance with query parameters - skip for now."""
        # Note: Param API needs clarification - skipping this test
        pytest.skip("Param API usage needs clarification")

    def test_provenance_ast_hash_stability(self, sample_network):
        """Test that AST hash is stable across identical queries."""
        q = Q.nodes()
        
        result1 = q.execute(sample_network)
        result2 = q.execute(sample_network)
        
        hash1 = result1.meta["provenance"]["query"]["ast_hash"]
        hash2 = result2.meta["provenance"]["query"]["ast_hash"]
        
        assert hash1 == hash2


class TestLegacyDSLProvenance:
    """Test provenance in legacy DSL."""

    def test_legacy_provenance_exists(self, sample_network):
        """Test that provenance is present in legacy DSL results."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="social"')
        
        assert "meta" in result
        assert "provenance" in result["meta"]
        prov = result["meta"]["provenance"]
        
        assert isinstance(prov, dict)
        assert prov["engine"] == "dsl_legacy"

    def test_legacy_provenance_structure(self, sample_network):
        """Test legacy provenance structure."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 0')
        
        prov = result["meta"]["provenance"]
        
        # Check required top-level keys
        assert "engine" in prov
        assert "py3plex_version" in prov
        assert "timestamp_utc" in prov
        assert "network_fingerprint" in prov
        assert "query" in prov
        assert "performance" in prov

    def test_legacy_provenance_query_info(self, sample_network):
        """Test query info in legacy provenance."""
        query_str = 'SELECT nodes WHERE layer="social"'
        result = execute_query(sample_network, query_str)
        
        prov = result["meta"]["provenance"]
        query_info = prov["query"]
        
        assert query_info["target"] == "nodes"
        assert query_info["raw_string"] == query_str
        assert "ast_hash" in query_info

    def test_legacy_provenance_timings(self, sample_network):
        """Test that legacy DSL records timings."""
        result = execute_query(sample_network, 'SELECT nodes')
        
        prov = result["meta"]["provenance"]
        perf = prov["performance"]
        
        # Should have parse and execute stages
        assert "parse" in perf
        assert "execute" in perf
        assert "total_ms" in perf
        
        # All timings should be non-negative
        for stage, timing in perf.items():
            assert isinstance(timing, (int, float))
            assert timing >= 0


class TestBackwardCompatibility:
    """Test that provenance doesn't break existing code."""

    def test_result_without_provenance_access(self, sample_network):
        """Test that results can still be used without accessing provenance."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        # These operations should work regardless of provenance
        assert result.target == "nodes"
        assert len(result) >= 0
        assert isinstance(result.items, list)
        assert isinstance(result.attributes, dict)

    def test_result_serialization_with_provenance(self, sample_network):
        """Test that QueryResult with provenance can be serialized."""
        q = Q.nodes().compute("degree")
        result = q.execute(sample_network)
        
        # to_dict should work
        result_dict = result.to_dict()
        assert "meta" in result_dict
        assert "provenance" in result_dict["meta"]
        
        # Provenance itself should be dict-serializable
        prov = result_dict["meta"]["provenance"]
        assert isinstance(prov, dict)
        
        # Check basic structure
        assert "engine" in prov
        assert "timestamp_utc" in prov

    def test_legacy_result_backward_compat(self, sample_network):
        """Test that legacy results remain backward compatible."""
        result = execute_query(sample_network, 'SELECT nodes')
        
        # Standard keys should still exist
        assert "nodes" in result or "edges" in result
        assert "count" in result
        
        # Meta is added but doesn't break anything
        assert "meta" in result
        assert isinstance(result["meta"], dict)

    def test_provenance_optional_in_meta(self, sample_network):
        """Test that code checking for provenance works correctly."""
        q = Q.nodes()
        result = q.execute(sample_network)
        
        # Should be able to check safely
        if "provenance" in result.meta:
            prov = result.meta["provenance"]
            assert isinstance(prov, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
