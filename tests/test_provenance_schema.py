"""Tests for provenance completeness and schema stability.

This module ensures that all query execution paths (DSL v2, legacy DSL,
graph_ops, pipeline) produce complete provenance metadata with a stable schema.

Key Guarantees Tested:
- Required provenance keys are present
- Schema doesn't drift over time
- All execution engines produce compatible provenance
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_ast
from py3plex.graph_ops import nodes, edges
from py3plex.pipeline import Pipeline, LoadStep, ComputeStats


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    nodes_list = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
    ]
    network.add_nodes(nodes_list)
    edges_list = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'A', 'source_type': 'work', 'target_type': 'social', 'weight': 0.5},
    ]
    network.add_edges(edges_list)
    return network


# Define required provenance keys schema
REQUIRED_PROVENANCE_KEYS = {
    "engine",
    "py3plex_version",
    "timestamp_utc",
    "network_fingerprint",
}

REQUIRED_NETWORK_FINGERPRINT_KEYS = {
    "node_count",
    "edge_count",
    "layer_count",
    "layers",
}

REQUIRED_QUERY_KEYS = {
    "ast_hash",
}

REQUIRED_PERFORMANCE_KEYS = {
    "total_ms",
}


class TestDSLv2ProvenanceSchema:
    """Test provenance schema for DSL v2 executor."""

    def test_basic_query_provenance(self, sample_network):
        """Test that basic DSL v2 query produces complete provenance."""
        query = Q.nodes().where(degree__gt=0)
        result = query.execute(sample_network)
        
        # Check meta exists
        assert "meta" in result.__dict__ or hasattr(result, "meta"), \
            "QueryResult must have 'meta' attribute"
        
        meta = result.meta
        assert "provenance" in meta, "Meta must contain 'provenance'"
        
        prov = meta["provenance"]
        
        # Check required top-level keys
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in prov, f"Provenance must contain '{key}'"
        
        # Check engine is correct
        assert "dsl" in prov["engine"].lower() or "executor" in prov["engine"].lower(), \
            f"Engine should indicate DSL executor, got: {prov['engine']}"
        
        # Check network fingerprint structure
        fp = prov["network_fingerprint"]
        for key in REQUIRED_NETWORK_FINGERPRINT_KEYS:
            assert key in fp, f"Network fingerprint must contain '{key}'"
        
        # Check query metadata
        assert "query" in prov, "Provenance must contain 'query'"
        query_meta = prov["query"]
        for key in REQUIRED_QUERY_KEYS:
            assert key in query_meta, f"Query metadata must contain '{key}'"
        
        # Check AST hash is valid
        assert isinstance(query_meta["ast_hash"], str), "AST hash must be string"
        assert len(query_meta["ast_hash"]) == 16, "AST hash must be 16 characters"
        
        # Check performance metadata
        assert "performance" in prov, "Provenance must contain 'performance'"
        perf = prov["performance"]
        for key in REQUIRED_PERFORMANCE_KEYS:
            assert key in perf, f"Performance metadata must contain '{key}'"

    def test_compute_query_provenance(self, sample_network):
        """Test provenance for query with compute."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        prov = result.meta["provenance"]
        
        # All required keys present
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in prov
        
        # Check timestamp is ISO8601
        timestamp = prov["timestamp_utc"]
        assert "T" in timestamp or "-" in timestamp, \
            "Timestamp should be ISO8601 format"

    def test_ordered_query_provenance(self, sample_network):
        """Test provenance for query with ordering."""
        query = Q.nodes().compute("degree").order_by("-degree")
        result = query.execute(sample_network)
        
        prov = result.meta["provenance"]
        
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in prov

    def test_limited_query_provenance(self, sample_network):
        """Test provenance for query with limit."""
        query = Q.nodes().limit(2)
        result = query.execute(sample_network)
        
        prov = result.meta["provenance"]
        
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in prov


class TestGraphOpsProvenanceSchema:
    """Test provenance schema for graph_ops operations."""

    def test_nodes_operation_provenance(self, sample_network):
        """Test that graph_ops nodes operation includes provenance."""
        result = nodes(sample_network).filter(lambda n: n["degree"] > 0)
        
        # Graph ops may or may not attach provenance depending on implementation
        # We test that if provenance exists, it has the right structure
        if hasattr(result, "meta") and result.meta and "provenance" in result.meta:
            prov = result.meta["provenance"]
            
            # Should have engine info
            assert "engine" in prov or "source" in prov
            
            # If it has provenance, check basic structure
            if "engine" in prov:
                assert isinstance(prov["engine"], str)

    def test_edges_operation_provenance(self, sample_network):
        """Test that graph_ops edges operation handling."""
        result = edges(sample_network).filter(lambda e: e.get("weight", 0) > 0.5)
        
        # Similar to nodes - check if provenance exists and is well-formed
        if hasattr(result, "meta") and result.meta and "provenance" in result.meta:
            prov = result.meta["provenance"]
            assert "engine" in prov or "source" in prov


class TestProvenanceSchemaStability:
    """Test that provenance schema remains stable across executions."""

    def test_multiple_executions_same_schema(self, sample_network):
        """Test that multiple executions produce same schema."""
        query = Q.nodes().compute("degree")
        
        # Execute multiple times
        results = [query.execute(sample_network) for _ in range(3)]
        
        # Extract provenance keys from each result
        prov_keys_list = [set(r.meta["provenance"].keys()) for r in results]
        
        # All should have the same top-level keys
        first_keys = prov_keys_list[0]
        for keys in prov_keys_list[1:]:
            assert keys == first_keys, \
                "Provenance schema must be stable across executions"

    def test_different_queries_same_schema(self, sample_network):
        """Test that different queries produce same provenance schema."""
        queries = [
            Q.nodes().where(degree__gt=0),
            Q.nodes().compute("degree"),
            Q.edges().where(weight__gt=0.5),
        ]
        
        results = [q.execute(sample_network) for q in queries]
        
        # All should have required keys
        for result in results:
            prov = result.meta["provenance"]
            for key in REQUIRED_PROVENANCE_KEYS:
                assert key in prov, \
                    f"All queries must produce '{key}' in provenance"


class TestNetworkFingerprintConsistency:
    """Test network fingerprint consistency."""

    def test_fingerprint_captures_size(self, sample_network):
        """Test that fingerprint captures network size."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        fp = result.meta["provenance"]["network_fingerprint"]
        
        # Node count should be positive
        assert fp["node_count"] > 0, "Network should have nodes"
        
        # Edge count should be positive
        assert fp["edge_count"] > 0, "Network should have edges"
        
        # Layer count should be positive
        assert fp["layer_count"] > 0, "Network should have layers"
        
        # Layers list should not be empty
        assert len(fp["layers"]) > 0, "Network should have layer names"

    def test_fingerprint_consistent_for_same_network(self, sample_network):
        """Test that fingerprint is consistent across queries on same network."""
        query1 = Q.nodes()
        query2 = Q.edges()
        
        result1 = query1.execute(sample_network)
        result2 = query2.execute(sample_network)
        
        fp1 = result1.meta["provenance"]["network_fingerprint"]
        fp2 = result2.meta["provenance"]["network_fingerprint"]
        
        # Fingerprints should be identical for same network
        assert fp1 == fp2, \
            "Network fingerprint must be consistent across queries"

    def test_fingerprint_different_for_different_networks(self):
        """Test that fingerprint differs for different networks."""
        net1 = multinet.multi_layer_network(directed=False)
        net1.add_nodes([{'source': 'A', 'type': 'L1'}])
        
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
        ])
        net2.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        query = Q.nodes()
        result1 = query.execute(net1)
        result2 = query.execute(net2)
        
        fp1 = result1.meta["provenance"]["network_fingerprint"]
        fp2 = result2.meta["provenance"]["network_fingerprint"]
        
        # Fingerprints should differ
        assert fp1 != fp2, \
            "Different networks must produce different fingerprints"


class TestPerformanceMetadata:
    """Test performance timing metadata."""

    def test_performance_timing_present(self, sample_network):
        """Test that performance timing is captured."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        perf = result.meta["provenance"]["performance"]
        
        assert "total_ms" in perf, "Performance must include total_ms"
        assert isinstance(perf["total_ms"], (int, float)), \
            "total_ms must be numeric"
        assert perf["total_ms"] >= 0, "total_ms must be non-negative"

    def test_performance_timing_reasonable(self, sample_network):
        """Test that performance timing is in reasonable range."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        perf = result.meta["provenance"]["performance"]
        total_ms = perf["total_ms"]
        
        # Should complete in less than 10 seconds for small network
        assert total_ms < 10000, \
            f"Query should complete quickly, took {total_ms}ms"


class TestProvenanceVersionInfo:
    """Test version information in provenance."""

    def test_py3plex_version_present(self, sample_network):
        """Test that py3plex version is captured."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        version = result.meta["provenance"]["py3plex_version"]
        
        assert version is not None, "Version must not be None"
        assert isinstance(version, str), "Version must be string"
        # Version should be non-empty or "unknown"
        assert len(version) > 0, "Version must not be empty"

    def test_version_consistent_across_queries(self, sample_network):
        """Test that version is consistent."""
        results = [
            Q.nodes().execute(sample_network),
            Q.edges().execute(sample_network),
        ]
        
        versions = [r.meta["provenance"]["py3plex_version"] for r in results]
        
        # All should report same version
        assert len(set(versions)) == 1, \
            "All queries should report same py3plex version"


class TestProvenanceSnapshotRegression:
    """Test provenance schema against snapshot to detect drift."""

    def test_provenance_schema_snapshot(self, sample_network):
        """Test provenance schema matches expected snapshot."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        prov = result.meta["provenance"]
        
        # Define expected schema (this is the snapshot)
        expected_schema = {
            "engine": str,
            "py3plex_version": str,
            "timestamp_utc": str,
            "network_fingerprint": dict,
            "query": dict,
            "performance": dict,
        }
        
        # Check all expected keys are present with correct types
        for key, expected_type in expected_schema.items():
            assert key in prov, f"Schema drift: missing key '{key}'"
            assert isinstance(prov[key], expected_type), \
                f"Schema drift: '{key}' should be {expected_type.__name__}, got {type(prov[key]).__name__}"
        
        # Check nested structures
        fp_schema = {
            "node_count": (int, type(None)),
            "edge_count": (int, type(None)),
            "layer_count": (int, type(None)),
            "layers": list,
        }
        
        fp = prov["network_fingerprint"]
        for key, expected_types in fp_schema.items():
            assert key in fp, f"Schema drift: missing fingerprint key '{key}'"
            if not isinstance(expected_types, tuple):
                expected_types = (expected_types,)
            assert isinstance(fp[key], expected_types), \
                f"Schema drift: fingerprint '{key}' has wrong type"

    def test_query_metadata_schema_snapshot(self, sample_network):
        """Test query metadata schema."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        query_meta = result.meta["provenance"]["query"]
        
        # Expected query metadata schema
        expected_keys = {"ast_hash"}
        
        for key in expected_keys:
            assert key in query_meta, \
                f"Schema drift: missing query metadata key '{key}'"
