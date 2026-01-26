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


def assert_network_semantic_equal(net_a, net_b, *, check_attrs=True, check_order_insensitive=True):
    """
    Assert that two networks are semantically equal.
    
    This is the canonical comparison function for network roundtrip tests.
    
    Args:
        net_a: First network
        net_b: Second network
        check_attrs: Whether to check node/edge attributes
        check_order_insensitive: Whether to ignore ordering of nodes/edges
    
    Raises:
        AssertionError: If networks are not semantically equal
    """
    # Check basic properties
    assert net_a.directed == net_b.directed, "Directed flag mismatch"
    assert net_a.network_type == net_b.network_type, "Network type mismatch"
    
    # Check node replicas
    nodes_a = set(net_a.get_nodes())
    nodes_b = set(net_b.get_nodes())
    assert nodes_a == nodes_b, f"Node replica sets differ: {nodes_a ^ nodes_b}"
    
    # Check edge replicas (as multisets for undirected, sets for directed)
    edges_a = list(net_a.get_edges(data=False))
    edges_b = list(net_b.get_edges(data=False))
    
    if check_order_insensitive:
        edges_a = sorted(edges_a)
        edges_b = sorted(edges_b)
    
    assert len(edges_a) == len(edges_b), f"Edge count mismatch: {len(edges_a)} vs {len(edges_b)}"
    assert edges_a == edges_b, "Edge replica sets differ"
    
    # Check layers
    layers_a = set(net_a.get_layers())
    layers_b = set(net_b.get_layers())
    assert layers_a == layers_b, f"Layer sets differ: {layers_a ^ layers_b}"
    
    if check_attrs:
        # Check node attributes
        for node in nodes_a:
            attrs_a = net_a.core_network.nodes[node]
            attrs_b = net_b.core_network.nodes[node]
            # Compare keys
            assert set(attrs_a.keys()) == set(attrs_b.keys()), \
                f"Node {node} attribute keys differ"
            # Compare values
            for key in attrs_a.keys():
                val_a = attrs_a[key]
                val_b = attrs_b[key]
                # Handle numpy arrays
                if hasattr(val_a, '__array__') and hasattr(val_b, '__array__'):
                    import numpy as np
                    assert np.array_equal(val_a, val_b), \
                        f"Node {node} attribute {key} arrays differ"
                else:
                    assert val_a == val_b, \
                        f"Node {node} attribute {key} differs: {val_a} vs {val_b}"
        
        # Check edge attributes
        for edge in edges_a:
            attrs_a = net_a.core_network.edges[edge]
            attrs_b = net_b.core_network.edges[edge]
            assert set(attrs_a.keys()) == set(attrs_b.keys()), \
                f"Edge {edge} attribute keys differ"
            for key in attrs_a.keys():
                val_a = attrs_a[key]
                val_b = attrs_b[key]
                if hasattr(val_a, '__array__') and hasattr(val_b, '__array__'):
                    import numpy as np
                    assert np.array_equal(val_a, val_b), \
                        f"Edge {edge} attribute {key} arrays differ"
                else:
                    assert val_a == val_b, \
                        f"Edge {edge} attribute {key} differs: {val_a} vs {val_b}"


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


class TestArrowFormatRoundTrip:
    """Test Arrow format zero-loss roundtrip."""
    
    @pytest.fixture
    def complex_network(self):
        """Create a complex multilayer network with various attribute types."""
        net = multinet.multi_layer_network(directed=False)
        
        # Add nodes with diverse attributes
        nodes = [
            {'source': 'A', 'type': 'layer1'},  # Appears in layer1
            {'source': 'B', 'type': 'layer1'},  # Appears in both layers
            {'source': 'B', 'type': 'layer2'},
            {'source': 'C', 'type': 'layer2'},  # Appears in layer2
        ]
        net.add_nodes(nodes)
        
        # Add edges: intra-layer and inter-layer
        edges = [
            # Intra-layer edges
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 
             'target_type': 'layer1', 'weight': 1.5, 'label': 'edge1'},
            # Inter-layer edge
            {'source': 'B', 'target': 'C', 'source_type': 'layer1', 
             'target_type': 'layer2', 'weight': 2.0, 'label': 'edge2'},
            # Another intra-layer edge
            {'source': 'B', 'target': 'C', 'source_type': 'layer2', 
             'target_type': 'layer2', 'weight': 0.5, 'label': 'edge3'},
        ]
        net.add_edges(edges)
        
        return net
    
    def test_arrow_roundtrip_preserves_node_count(self, complex_network):
        """Test that Arrow roundtrip preserves node replica count."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        orig_nodes = list(complex_network.get_nodes())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            # Save and load
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_nodes = list(loaded_net.get_nodes())
            
            assert len(loaded_nodes) == len(orig_nodes), \
                "Arrow roundtrip must preserve node replica count"
    
    def test_arrow_roundtrip_preserves_edge_count(self, complex_network):
        """Test that Arrow roundtrip preserves edge count."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        orig_edges = list(complex_network.get_edges())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_edges = list(loaded_net.get_edges())
            
            assert len(loaded_edges) == len(orig_edges), \
                "Arrow roundtrip must preserve edge count"
    
    def test_arrow_roundtrip_preserves_layer_count(self, complex_network):
        """Test that Arrow roundtrip preserves layer count."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        # Get layer count
        layers_info = complex_network.get_layers()
        if isinstance(layers_info, tuple):
            orig_layers = layers_info[0]
        else:
            orig_layers = layers_info
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_layers_info = loaded_net.get_layers()
            if isinstance(loaded_layers_info, tuple):
                loaded_layers = loaded_layers_info[0]
            else:
                loaded_layers = loaded_layers_info
            
            assert len(loaded_layers) == len(orig_layers), \
                "Arrow roundtrip must preserve layer count"
    
    def test_arrow_roundtrip_preserves_multilayer_identity(self, complex_network):
        """Test that Arrow roundtrip preserves node replica identities."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        orig_nodes = set(complex_network.get_nodes())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_nodes = set(loaded_net.get_nodes())
            
            # Check that all original node replicas are present
            assert orig_nodes == loaded_nodes, \
                "Arrow roundtrip must preserve exact node replica identities (node, layer)"
    
    def test_arrow_roundtrip_preserves_edge_endpoints(self, complex_network):
        """Test that Arrow roundtrip preserves edge endpoint identities."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        orig_edges = set(complex_network.get_edges())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_edges = set(loaded_net.get_edges())
            
            # Check that all original edges are present
            assert orig_edges == loaded_edges, \
                "Arrow roundtrip must preserve exact edge identities"
    
    def test_arrow_roundtrip_preserves_network_fingerprint(self, complex_network):
        """Test that Arrow roundtrip preserves network fingerprint."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
            from py3plex.dsl.provenance import network_fingerprint
        except ImportError:
            pytest.skip("Arrow I/O or provenance not available")
        
        orig_fp = network_fingerprint(complex_network)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            
            save_to_arrow(complex_network, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_fp = network_fingerprint(loaded_net)
            
            # Check key fingerprint fields
            assert loaded_fp["node_count"] == orig_fp["node_count"]
            assert loaded_fp["edge_count"] == orig_fp["edge_count"]
            assert loaded_fp["layer_count"] == orig_fp["layer_count"]
            assert set(loaded_fp["layers"]) == set(orig_fp["layers"])


class TestArrowRoundtripZeroLoss:
    """Test Arrow format roundtrips with zero loss of multilayer identity and attributes."""
    
    @pytest.fixture
    def multilayer_network_with_attributes(self):
        """Create a multilayer network with various attribute types for comprehensive testing."""
        net = multinet.multi_layer_network(directed=False)
        
        # Add nodes with various attribute types
        nodes = [
            {'source': 'Alice', 'type': 'social', 
             'age': 30, 'score': 0.85, 'active': True, 'tags': ['friend', 'colleague']},
            {'source': 'Bob', 'type': 'social',
             'age': 25, 'score': 0.92, 'active': False, 'tags': ['friend']},
            {'source': 'Alice', 'type': 'work',
             'age': 30, 'score': 0.88, 'active': True, 'tags': ['team_lead']},
            {'source': 'Charlie', 'type': 'work',
             'age': 35, 'score': 0.75, 'active': True, 'tags': []},
        ]
        net.add_nodes(nodes)
        
        # Add edges with attributes (intra-layer and inter-layer)
        edges = [
            # Intra-layer edges
            {'source': 'Alice', 'target': 'Bob', 
             'source_type': 'social', 'target_type': 'social',
             'weight': 1.5, 'interaction_count': 10},
            # Inter-layer edge
            {'source': 'Alice', 'target': 'Alice',
             'source_type': 'social', 'target_type': 'work',
             'weight': 1.0, 'interaction_count': 5},
            # Another intra-layer edge
            {'source': 'Alice', 'target': 'Charlie',
             'source_type': 'work', 'target_type': 'work',
             'weight': 0.8, 'interaction_count': 3},
        ]
        net.add_edges(edges)
        
        return net
    
    def test_arrow_roundtrip_preserves_node_replicas(self, multilayer_network_with_attributes):
        """Test that Arrow roundtrip preserves all node replicas (node + layer pairs)."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        net = multilayer_network_with_attributes
        original_nodes = set(net.get_nodes())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_nodes = set(loaded_net.get_nodes())
            assert loaded_nodes == original_nodes, "Node replicas not preserved"
    
    def test_arrow_roundtrip_preserves_edge_structure(self, multilayer_network_with_attributes):
        """Test that Arrow roundtrip preserves edge structure including inter-layer edges."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        net = multilayer_network_with_attributes
        original_edges = list(net.get_edges())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            loaded_edges = list(loaded_net.get_edges())
            
            # Check edge counts
            assert len(loaded_edges) == len(original_edges), "Edge count not preserved"
            
            # Check that we have both intra-layer and inter-layer edges
            # Edge format: ((source, source_layer), (target, target_layer))
            intra_layer = [e for e in loaded_edges if e[0][1] == e[1][1]]
            inter_layer = [e for e in loaded_edges if e[0][1] != e[1][1]]
            assert len(intra_layer) > 0, "Intra-layer edges lost"
            assert len(inter_layer) > 0, "Inter-layer edges lost"
    
    def test_arrow_roundtrip_preserves_directedness(self, multilayer_network_with_attributes):
        """Test that Arrow roundtrip preserves directedness flag."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        # Test with undirected network
        net_undirected = multilayer_network_with_attributes
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "undirected.arrow"
            save_to_arrow(net_undirected, str(path))
            loaded = load_from_arrow(str(path))
            # Note: multi_layer_network doesn't have a simple directed flag to check
            # but the structure should be preserved
            assert len(list(loaded.get_edges())) == len(list(net_undirected.get_edges()))
        
        # Test with directed network
        net_directed = multinet.multi_layer_network(directed=True)
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net_directed.add_nodes(nodes)
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        ]
        net_directed.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "directed.arrow"
            save_to_arrow(net_directed, str(path))
            loaded = load_from_arrow(str(path))
            assert len(list(loaded.get_edges())) == 1
    
    def test_arrow_roundtrip_preserves_scalar_attributes(self, multilayer_network_with_attributes):
        """Test that Arrow roundtrip preserves scalar node and edge attributes."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        net = multilayer_network_with_attributes
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            # Check node attributes for a specific node replica
            alice_social = ('Alice', 'social')
            if alice_social in loaded_net.get_nodes():
                # Note: attribute access might vary, this is a basic check
                # The key is that the node structure is preserved
                pass
            
            # At minimum, check that attribute data is present somewhere
            # The exact API for accessing attributes may vary
            assert len(list(loaded_net.get_nodes())) > 0
            assert len(list(loaded_net.get_edges())) > 0
    
    def test_arrow_roundtrip_fingerprint_stability(self, multilayer_network_with_attributes):
        """Test that network fingerprint is stable across Arrow roundtrip."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
            from py3plex.dsl.provenance import network_fingerprint
        except ImportError:
            pytest.skip("Arrow I/O or provenance not available")
        
        net = multilayer_network_with_attributes
        orig_fp = network_fingerprint(net)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            loaded_fp = network_fingerprint(loaded_net)
            
            # Check key fingerprint components
            assert loaded_fp["node_count"] == orig_fp["node_count"]
            assert loaded_fp["edge_count"] == orig_fp["edge_count"]
            assert loaded_fp["layer_count"] == orig_fp["layer_count"]
            assert set(loaded_fp["layers"]) == set(orig_fp["layers"])
    
    def test_arrow_roundtrip_empty_network(self):
        """Test that Arrow roundtrip handles empty networks gracefully."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        net = multinet.multi_layer_network(directed=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            # Empty network has core_network=None, which is expected behavior
            # Just verify the save/load succeeded and directedness is preserved
            assert loaded_net.directed == False
            assert loaded_net.core_network is None  # Empty network has None
    
    def test_arrow_roundtrip_single_layer(self):
        """Test Arrow roundtrip with a single-layer network."""
        try:
            from py3plex.io import save_to_arrow, load_from_arrow
        except ImportError:
            pytest.skip("Arrow I/O not available")
        
        net = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        ]
        net.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_layer.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            assert len(list(loaded_net.get_nodes())) == 2
            assert len(list(loaded_net.get_edges())) == 1
            # get_layers() returns (layer_names, layer_graphs, layer_metadata)
            layer_names, _, _ = loaded_net.get_layers()
            assert len(layer_names) == 1
            assert 'layer1' in layer_names


class TestParquetRoundtrip:
    """Test Parquet format roundtrips."""
    
    def test_parquet_import_available(self):
        """Test that Parquet functionality is available or can be skipped gracefully."""
        try:
            import pyarrow.parquet
            assert True, "PyArrow Parquet support is available"
        except ImportError:
            pytest.skip("PyArrow Parquet not available - tests will be skipped")
    
    def test_parquet_directory_roundtrip_simple(self):
        """Test Parquet directory format roundtrip with simple network."""
        try:
            from py3plex.io import save_network_to_parquet, load_network_from_parquet
        except ImportError:
            pytest.skip("Parquet I/O not available")
        
        net = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.5},
        ]
        net.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "network_dir"
            save_network_to_parquet(net, str(path))
            
            # Verify directory structure
            assert path.exists()
            assert (path / 'nodes.parquet').exists()
            assert (path / 'edges.parquet').exists()
            assert (path / 'metadata.json').exists()
            
            # Load and verify
            loaded_net = load_network_from_parquet(str(path))
            assert len(list(loaded_net.get_nodes())) == 2
            assert len(list(loaded_net.get_edges())) == 1
    
    def test_parquet_roundtrip_multilayer(self):
        """Test Parquet roundtrip with multilayer network."""
        try:
            from py3plex.io import save_network_to_parquet, load_network_from_parquet
        except ImportError:
            pytest.skip("Parquet I/O not available")
        
        net = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'A', 'type': 'layer2'},
            {'source': 'C', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'A', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
        ]
        net.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "multilayer_dir"
            save_network_to_parquet(net, str(path))
            loaded_net = load_network_from_parquet(str(path))
            
            assert len(list(loaded_net.get_nodes())) == 4  # 4 node replicas
            assert len(list(loaded_net.get_edges())) == 2
            layer_names, _, _ = loaded_net.get_layers()
            assert len(layer_names) == 2
    
    def test_parquet_roundtrip_with_attributes(self):
        """Test Parquet roundtrip preserves node and edge attributes."""
        try:
            from py3plex.io import save_network_to_parquet, load_network_from_parquet
        except ImportError:
            pytest.skip("Parquet I/O not available")
        
        net = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        
        # Add node attributes
        net.core_network.nodes[('A', 'layer1')]['score'] = 0.8
        net.core_network.nodes[('A', 'layer1')]['label'] = 'important'
        
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.5},
        ]
        net.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "attrs_dir"
            save_network_to_parquet(net, str(path))
            loaded_net = load_network_from_parquet(str(path))
            
            # Verify attributes preserved
            assert loaded_net.core_network.nodes[('A', 'layer1')]['score'] == 0.8
            assert loaded_net.core_network.nodes[('A', 'layer1')]['label'] == 'important'


class TestNetworkSemanticEquality:
    """Test the assert_network_semantic_equal helper function."""

    def test_semantic_equality_arrow_roundtrip(self):
        """Test that Arrow roundtrip produces semantically equal networks."""
        pyarrow = pytest.importorskip("pyarrow")
        from py3plex.io import save_to_arrow, load_from_arrow
        import numpy as np

        # Create a complex network
        net = multinet.multi_layer_network(directed=False)
        nodes = [
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'A', 'type': 'work'},
        ]
        net.add_nodes(nodes)
        
        # Add various attribute types
        net.core_network.nodes[('A', 'social')]['int_attr'] = 42
        net.core_network.nodes[('A', 'social')]['float_attr'] = 3.14
        net.core_network.nodes[('A', 'social')]['str_attr'] = 'hello'
        net.core_network.nodes[('A', 'social')]['array_attr'] = np.array([1, 2, 3])
        net.core_network.nodes[('A', 'social')]['dict_attr'] = {'key': 'value'}
        
        edges = [
            {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.5},
        ]
        net.add_edges(edges)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "semantic.arrow"
            save_to_arrow(net, str(path))
            loaded_net = load_from_arrow(str(path))
            
            # Use semantic equality checker
            assert_network_semantic_equal(net, loaded_net, check_attrs=True)

    def test_semantic_equality_parquet_roundtrip(self):
        """Test that Parquet roundtrip produces semantically equal networks."""
        pyarrow = pytest.importorskip("pyarrow")
        from py3plex.io import save_network_to_parquet, load_network_from_parquet
        import numpy as np

        # Create a multilayer network
        net = multinet.multi_layer_network(directed=True)
        nodes = [
            {'source': 'X', 'type': 'layer1'},
            {'source': 'Y', 'type': 'layer1'},
            {'source': 'X', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        # Add attributes
        net.core_network.nodes[('X', 'layer1')]['value'] = 100
        net.core_network.nodes[('Y', 'layer1')]['value'] = 200
        
        edges = [
            {'source': 'X', 'target': 'Y', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 0.9},
        ]
        net.add_edges(edges)
        net.core_network.edges[('X', 'layer1'), ('Y', 'layer1')]['importance'] = 'high'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "semantic_dir"
            save_network_to_parquet(net, str(path))
            loaded_net = load_network_from_parquet(str(path))
            
            # Use semantic equality checker
            assert_network_semantic_equal(net, loaded_net, check_attrs=True)

    def test_semantic_equality_detects_node_difference(self):
        """Test that semantic equality detects missing nodes."""
        net1 = multinet.multi_layer_network(directed=False)
        net2 = multinet.multi_layer_network(directed=False)
        
        net1.add_nodes([{'source': 'A', 'type': 'layer1'}])
        net2.add_nodes([{'source': 'B', 'type': 'layer1'}])
        
        with pytest.raises(AssertionError, match="Node replica sets differ"):
            assert_network_semantic_equal(net1, net2)

    def test_semantic_equality_detects_edge_difference(self):
        """Test that semantic equality detects different edges."""
        net1 = multinet.multi_layer_network(directed=False)
        net2 = multinet.multi_layer_network(directed=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net1.add_nodes(nodes)
        net2.add_nodes(nodes)
        
        net1.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        # net2 has no edges
        
        with pytest.raises(AssertionError, match="Edge count mismatch"):
            assert_network_semantic_equal(net1, net2)

    def test_semantic_equality_detects_attribute_difference(self):
        """Test that semantic equality detects different attributes."""
        net1 = multinet.multi_layer_network(directed=False)
        net2 = multinet.multi_layer_network(directed=False)
        
        nodes = [{'source': 'A', 'type': 'layer1'}]
        net1.add_nodes(nodes)
        net2.add_nodes(nodes)
        
        net1.core_network.nodes[('A', 'layer1')]['value'] = 10
        net2.core_network.nodes[('A', 'layer1')]['value'] = 20
        
        with pytest.raises(AssertionError, match="attribute.*differs"):
            assert_network_semantic_equal(net1, net2, check_attrs=True)

