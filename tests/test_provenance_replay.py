"""Tests for replayable provenance and query replay.

Tests cover:
- Provenance schema validation
- Network capture and restoration
- Query serialization and deserialization
- Replay functionality
- Bundle export/import
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.provenance import (
    ProvenanceSchema,
    ProvenanceMode,
    CaptureMethod,
    NetworkCapture,
    capture_network,
    restore_network,
    export_bundle,
    load_bundle,
    replay_from_bundle,
    ReplayError,
)


@pytest.fixture
def sample_network():
    """Create a small sample network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'D', 'source_type': 'work', 'target_type': 'work', 'weight': 0.5},
    ]
    network.add_edges(edges)
    
    return network


class TestNetworkCapture:
    """Test network capture and restoration."""
    
    def test_capture_and_restore_nodes(self, sample_network):
        """Test that we can capture and restore a network."""
        # Capture
        capture = capture_network(sample_network, include_attributes=True)
        
        assert isinstance(capture, NetworkCapture)
        assert len(capture.nodes) == 4
        assert len(capture.edges) == 3
        
        # Restore
        restored = restore_network(capture)
        
        # Check node count
        assert len(list(restored.get_nodes())) == 4
        assert len(list(restored.get_edges())) == 3
    
    def test_capture_preserves_layers(self, sample_network):
        """Test that layer information is preserved."""
        capture = capture_network(sample_network)
        
        # Check that layers are captured
        layers = [n['layer'] for n in capture.nodes]
        assert 'social' in layers
        assert 'work' in layers
        
        # Restore and verify
        restored = restore_network(capture)
        restored_nodes = list(restored.get_nodes())
        
        # Check that at least one node has each layer
        layers_present = set()
        for node in restored_nodes:
            if isinstance(node, tuple) and len(node) >= 2:
                layers_present.add(node[1])
        
        assert 'social' in layers_present
        assert 'work' in layers_present
    
    def test_capture_stable_ordering(self, sample_network):
        """Test that capture produces stable ordering."""
        capture1 = capture_network(sample_network)
        capture2 = capture_network(sample_network)
        
        # Check that hashes are the same
        assert capture1.compute_hash() == capture2.compute_hash()


class TestProvenanceQuery:
    """Test provenance-enabled queries."""
    
    def test_query_with_replayable_provenance(self, sample_network):
        """Test that we can execute a query with replayable provenance."""
        result = (
            Q.nodes()
             .provenance(mode="replayable", capture="auto", seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Check that provenance is present
        assert result.provenance is not None
        prov = result.provenance
        
        # Check mode
        assert prov.get("mode") == "replayable"
        
        # Check that network was captured
        nc = prov.get("network_capture", {})
        assert nc.get("node_count") == 4
        assert nc.get("edge_count") == 3
    
    def test_result_is_replayable(self, sample_network):
        """Test that result reports as replayable."""
        result = (
            Q.nodes()
             .provenance(mode="replayable", capture="snapshot", seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Should be replayable
        assert result.is_replayable
    
    def test_result_not_replayable_without_provenance(self, sample_network):
        """Test that result without provenance is not replayable."""
        result = (
            Q.nodes()
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Should not be replayable (uses log mode by default)
        assert not result.is_replayable


class TestReplay:
    """Test query replay functionality."""
    
    def test_basic_replay(self, sample_network):
        """Test that we can replay a simple query."""
        # Execute with replayable provenance
        result1 = (
            Q.nodes()
             .provenance(mode="replayable", capture="snapshot", seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Replay
        result2 = result1.replay(strict=False)
        
        # Check that results match
        assert result1.count == result2.count
        assert set(result1.items) == set(result2.items)
        
        # Check degree values match
        for node in result1.items:
            deg1 = result1.attributes['degree'].get(node)
            deg2 = result2.attributes['degree'].get(node)
            if deg1 is not None and deg2 is not None:
                assert deg1 == deg2


class TestBundleIO:
    """Test bundle export and import."""
    
    def test_export_and_load_bundle(self, sample_network, tmp_path):
        """Test that we can export and load a bundle."""
        # Execute query
        result = (
            Q.nodes()
             .provenance(mode="replayable", capture="snapshot", seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Export bundle
        bundle_path = tmp_path / "test_bundle.json.gz"
        result.export_bundle(bundle_path, compress=True)
        
        # Check that file was created
        assert bundle_path.exists()
        
        # Load bundle
        bundle = load_bundle(bundle_path)
        
        # Check structure
        assert "provenance" in bundle
        assert "result" in bundle
    
    def test_replay_from_bundle(self, sample_network, tmp_path):
        """Test that we can replay from a bundle."""
        # Execute query
        result1 = (
            Q.nodes()
             .provenance(mode="replayable", capture="snapshot", seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Export bundle
        bundle_path = tmp_path / "test_bundle.json.gz"
        result1.export_bundle(bundle_path)
        
        # Replay from bundle
        result2 = replay_from_bundle(bundle_path, strict=False)
        
        # Check that results match
        assert result1.count == result2.count


class TestBackwardCompatibility:
    """Test that existing code still works."""
    
    def test_query_without_provenance_config(self, sample_network):
        """Test that queries without provenance config still work."""
        result = (
            Q.nodes()
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Should have legacy provenance
        assert result.provenance is not None
        assert result.provenance.get("engine") == "dsl_v2_executor"
        
        # Should not be replayable
        assert not result.is_replayable
    
    def test_reproducible_sugar(self, sample_network):
        """Test the reproducible() convenience method."""
        result = (
            Q.nodes()
             .reproducible(True, seed=42)
             .compute("degree")
             .execute(sample_network, progress=False)
        )
        
        # Should be replayable
        assert result.is_replayable
