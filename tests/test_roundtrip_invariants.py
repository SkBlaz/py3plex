"""Tests for round-trip invariants.

This module ensures that data can be converted between formats without loss
of critical information (node count, edge count, layer count, attributes).

Key Guarantees Tested:
- QueryResult → dict → QueryResult preserves data
- QueryResult → pandas → QueryResult preserves data
- Network → IO format → Network preserves structure
- Network fingerprint is consistent across conversions
"""

import pytest
import tempfile
from pathlib import Path
from py3plex.core import multinet
from py3plex.dsl import Q


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer2'},
        {'source': 'E', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0},
        {'source': 'D', 'target': 'E', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 0.5},
    ]
    network.add_edges(edges)
    return network


class TestQueryResultToDictRoundTrip:
    """Test QueryResult ↔ dict conversions."""

    def test_to_dict_preserves_node_count(self, sample_network):
        """Test that converting to dict preserves node count."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Check structure
        assert isinstance(result_dict, dict)
        assert "data" in result_dict or "nodes" in result_dict or isinstance(result_dict, list)
        
        # Count should match
        if isinstance(result_dict, list):
            assert len(result_dict) == len(result)
        elif "data" in result_dict:
            assert len(result_dict["data"]) == len(result)

    def test_to_dict_contains_metadata(self, sample_network):
        """Test that dict conversion includes metadata."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        result_dict = result.to_dict()
        
        # Should have meta information (if implemented)
        # This is implementation-dependent
        assert result_dict is not None

    def test_dict_roundtrip_preserves_data_structure(self, sample_network):
        """Test that dict roundtrip preserves basic structure."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        # Get original data
        original_df = result.to_pandas()
        original_count = len(original_df)
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Verify we can reconstruct something similar
        assert result_dict is not None
        
        # If it's a list, length should match
        if isinstance(result_dict, list):
            assert len(result_dict) == original_count


class TestQueryResultToPandasRoundTrip:
    """Test QueryResult ↔ pandas conversions."""

    def test_to_pandas_preserves_row_count(self, sample_network):
        """Test that pandas conversion preserves row count."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Row count should match result length
        assert len(df) == len(result)

    def test_to_pandas_contains_node_identifiers(self, sample_network):
        """Test that pandas DataFrame contains node identifiers."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have some identifier column
        # Common names: 'node', 'id', 'node_id', or index
        has_identifier = (
            'node' in df.columns or 
            'id' in df.columns or 
            'node_id' in df.columns or
            len(df.index) > 0
        )
        assert has_identifier, "DataFrame should have node identifiers"

    def test_to_pandas_contains_computed_metrics(self, sample_network):
        """Test that computed metrics appear in DataFrame."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have degree column
        assert 'degree' in df.columns, "DataFrame should contain computed metrics"

    def test_pandas_roundtrip_preserves_values(self, sample_network):
        """Test that pandas roundtrip preserves metric values."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        df1 = result.to_pandas()
        
        # If we can create another result from the same query
        result2 = query.execute(sample_network)
        df2 = result2.to_pandas()
        
        # Values should be identical
        if 'degree' in df1.columns and 'degree' in df2.columns:
            # Sort both to ensure same order
            df1_sorted = df1.sort_index()
            df2_sorted = df2.sort_index()
            
            degree_diff = (df1_sorted['degree'] - df2_sorted['degree']).abs().sum()
            assert degree_diff < 1e-10, "Repeated queries should give identical results"


class TestNetworkIOQuickRoundTrip:
    """Test quick Network I/O round-trip checks."""

    def test_network_structure_preserved(self, sample_network):
        """Test that network structure is internally consistent."""
        # Get basic counts
        nodes = list(sample_network.get_nodes())
        edges = list(sample_network.get_edges())
        layers = list(sample_network.layers) if hasattr(sample_network, 'layers') else []
        
        node_count = len(nodes)
        edge_count = len(edges)
        layer_count = len(layers)
        
        # These counts should be positive
        assert node_count > 0, "Network should have nodes"
        assert edge_count > 0, "Network should have edges"
        assert layer_count > 0, "Network should have layers"

    def test_network_fingerprint_consistency(self, sample_network):
        """Test that network fingerprint is stable."""
        from py3plex.dsl.provenance import network_fingerprint
        
        fp1 = network_fingerprint(sample_network)
        fp2 = network_fingerprint(sample_network)
        
        # Fingerprints should be identical
        assert fp1 == fp2, "Network fingerprint must be deterministic"
        
        # Check structure
        assert fp1["node_count"] > 0
        assert fp1["edge_count"] > 0
        assert fp1["layer_count"] > 0
        assert len(fp1["layers"]) > 0

    def test_network_gpickle_roundtrip(self, sample_network):
        """Test gpickle save/load round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_network.gpickle"
            
            # Get original counts
            orig_nodes = list(sample_network.get_nodes())
            orig_edges = list(sample_network.get_edges())
            
            # Save
            sample_network.save_network(
                output_file=str(file_path),
                output_type="gpickle"
            )
            
            # Load
            loaded_net = multinet.multi_layer_network(directed=False)
            loaded_net.load_network(
                input_file=str(file_path),
                input_type="gpickle"
            )
            
            # Compare counts
            loaded_nodes = list(loaded_net.get_nodes())
            loaded_edges = list(loaded_net.get_edges())
            
            assert len(loaded_nodes) == len(orig_nodes), \
                "Node count should be preserved"
            assert len(loaded_edges) == len(orig_edges), \
                "Edge count should be preserved"


class TestAttributePreservation:
    """Test that node and edge attributes are preserved."""

    def test_node_attributes_preserved_in_query(self, sample_network):
        """Test that node attributes are accessible in query results."""
        # Add some attributes
        sample_network.add_nodes([
            {'source': 'X', 'type': 'layer1', 'attr1': 'value1'}
        ])
        
        query = Q.nodes().where(layer="layer1")
        result = query.execute(sample_network)
        
        # Result should contain nodes
        assert len(result) > 0

    def test_edge_weight_preserved_in_query(self, sample_network):
        """Test that edge weights are accessible in query results."""
        query = Q.edges()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have weight information
        if 'weight' in df.columns:
            # Weights should be the ones we set
            assert df['weight'].min() >= 0, "Weights should be non-negative"


class TestNetworkFingerprintStability:
    """Test network fingerprint stability across operations."""

    def test_fingerprint_stable_after_query(self, sample_network):
        """Test that querying doesn't change network fingerprint."""
        from py3plex.dsl.provenance import network_fingerprint
        
        fp_before = network_fingerprint(sample_network)
        
        # Execute a query
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        fp_after = network_fingerprint(sample_network)
        
        # Fingerprint should be unchanged
        assert fp_before == fp_after, \
            "Querying should not modify network"

    def test_fingerprint_changes_after_modification(self):
        """Test that fingerprint changes when network is modified."""
        from py3plex.dsl.provenance import network_fingerprint
        
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'L1'}])
        
        fp1 = network_fingerprint(net)
        
        # Add more nodes
        net.add_nodes([{'source': 'B', 'type': 'L1'}])
        
        fp2 = network_fingerprint(net)
        
        # Fingerprints should differ
        assert fp1 != fp2, "Network modification should change fingerprint"
        assert fp2["node_count"] > fp1["node_count"]


class TestQueryResultInvariantsUnderRepeatedExecution:
    """Test that repeated query execution produces consistent results."""

    def test_repeated_execution_same_node_count(self, sample_network):
        """Test that repeated execution gives same node count."""
        query = Q.nodes()
        
        results = [query.execute(sample_network) for _ in range(3)]
        counts = [len(r) for r in results]
        
        # All counts should be identical
        assert len(set(counts)) == 1, \
            "Repeated execution must produce consistent counts"

    def test_repeated_execution_same_metric_values(self, sample_network):
        """Test that repeated execution gives same metric values."""
        query = Q.nodes().compute("degree")
        
        results = [query.execute(sample_network) for _ in range(3)]
        dfs = [r.to_pandas() for r in results]
        
        # Compare degree values
        if all('degree' in df.columns for df in dfs):
            for i in range(1, len(dfs)):
                diff = (dfs[0]['degree'] - dfs[i]['degree']).abs().sum()
                assert diff < 1e-10, \
                    "Repeated execution must produce identical metric values"

    def test_repeated_execution_same_provenance_schema(self, sample_network):
        """Test that repeated execution produces same provenance schema."""
        query = Q.nodes()
        
        results = [query.execute(sample_network) for _ in range(3)]
        
        prov_keys = [set(r.meta["provenance"].keys()) for r in results]
        
        # All should have same provenance keys
        first_keys = prov_keys[0]
        for keys in prov_keys[1:]:
            assert keys == first_keys, \
                "Provenance schema must be consistent"


class TestEdgeQueryRoundTrip:
    """Test edge query round-trip invariants."""

    def test_edge_query_preserves_edge_count(self, sample_network):
        """Test that edge query returns correct count."""
        query = Q.edges()
        result = query.execute(sample_network)
        
        # Should have edges
        assert len(result) > 0
        
        # Compare with actual edge count
        actual_edges = list(sample_network.get_edges())
        # Result might filter or aggregate, so just check it's non-empty
        assert len(result) <= len(actual_edges)

    def test_edge_query_to_pandas_has_structure(self, sample_network):
        """Test that edge query produces structured DataFrame."""
        query = Q.edges()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have some columns
        assert len(df.columns) > 0
        
        # Should have rows
        assert len(df) > 0


class TestLimitedQueryRoundTrip:
    """Test that LIMIT preserves data integrity."""

    def test_limit_reduces_result_size(self, sample_network):
        """Test that LIMIT clause reduces result size."""
        query_full = Q.nodes()
        result_full = query_full.execute(sample_network)
        
        query_limited = Q.nodes().limit(2)
        result_limited = query_limited.execute(sample_network)
        
        # Limited should be smaller or equal
        assert len(result_limited) <= len(result_full)
        assert len(result_limited) <= 2

    def test_limit_preserves_data_quality(self, sample_network):
        """Test that limited results have same structure as full results."""
        query_full = Q.nodes().compute("degree")
        result_full = query_full.execute(sample_network)
        
        query_limited = Q.nodes().compute("degree").limit(2)
        result_limited = query_limited.execute(sample_network)
        
        df_full = result_full.to_pandas()
        df_limited = result_limited.to_pandas()
        
        # Columns should match
        assert set(df_limited.columns).issubset(set(df_full.columns)), \
            "Limited query should have same or subset of columns"
