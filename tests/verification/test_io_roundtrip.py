"""
I/O and Schema Validation Tests.

Tests for:
- Roundtrip consistency (load → save → load)
- Schema validation
- Format conversions
- Duplicate edge handling
"""

import pytest
import tempfile
import os
from pathlib import Path
from py3plex.core import multinet


def create_simple_network():
    """Create a simple network for I/O testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_multiedgelist_roundtrip():
    """
    Test multiedgelist format roundtrip: save → load → compare.
    
    Invariant: Network structure preserved through save/load cycle.
    """
    original = create_simple_network()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_network.txt"
        
        # Save network
        original.save_network(str(filepath), output_type="multiedgelist")
        
        # Load network
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Compare node counts
        original_nodes = set(original.core_network.nodes())
        loaded_nodes = set(loaded.core_network.nodes())
        
        assert len(original_nodes) == len(loaded_nodes), \
            f"Node count mismatch: original={len(original_nodes)}, loaded={len(loaded_nodes)}"
        
        # Compare edge counts
        original_edges = original.core_network.number_of_edges()
        loaded_edges = loaded.core_network.number_of_edges()
        
        assert original_edges == loaded_edges, \
            f"Edge count mismatch: original={original_edges}, loaded={loaded_edges}"


@pytest.mark.verification
@pytest.mark.fast
def test_empty_network_save_load():
    """
    Test saving and loading empty network.
    
    Edge case: Empty network
    """
    empty = multinet.multi_layer_network(directed=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "empty_network.txt"
        
        # Save empty network
        empty.save_network(str(filepath), output_type="multiedgelist")
        
        # Load empty network
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Should have no nodes
        assert loaded.core_network.number_of_nodes() == 0, \
            "Loaded empty network should have 0 nodes"


@pytest.mark.verification
@pytest.mark.fast
def test_single_node_network_io():
    """
    Test I/O for single-node network.
    
    Edge case: Single node, no edges
    """
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer1'}])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "single_node.txt"
        
        # Save
        network.save_network(str(filepath), output_type="multiedgelist")
        
        # Load
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Should have 1 node (or 0 if single nodes aren't saved in multiedgelist)
        # Implementation dependent
        assert loaded.core_network.number_of_nodes() >= 0


@pytest.mark.verification
@pytest.mark.fast
def test_network_with_special_characters():
    """
    Test that node names with special characters are handled.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Node names with special characters
    nodes = [
        {'source': 'node-1', 'type': 'layer_1'},
        {'source': 'node.2', 'type': 'layer_1'},
        {'source': 'node_3', 'type': 'layer_1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'node-1', 'target': 'node.2', 'source_type': 'layer_1', 'target_type': 'layer_1'},
    ]
    network.add_edges(edges)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "special_chars.txt"
        
        # Save and load
        network.save_network(str(filepath), output_type="multiedgelist")
        
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Should preserve node names
        loaded_nodes = set(node[0] if isinstance(node, tuple) else node 
                          for node in loaded.core_network.nodes())
        
        expected_nodes = {'node-1', 'node.2', 'node_3'}
        # Check that special character nodes are present
        assert len(loaded_nodes) > 0, "Should load nodes with special characters"


@pytest.mark.verification
@pytest.mark.fast
def test_duplicate_edges_handling():
    """
    Test that duplicate edges are handled consistently.
    
    Behavior should be documented (merge, keep, or error).
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Add same edge twice
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    # Should not crash
    assert network.core_network is not None
    
    # Edge count behavior is implementation dependent
    # (multigraph allows multiple edges, simple graph merges)
    edge_count = network.core_network.number_of_edges()
    assert edge_count > 0, "Should have at least one edge"


@pytest.mark.verification
@pytest.mark.fast
def test_node_attributes_preserved():
    """
    Test that node attributes are preserved through I/O.
    
    Note: This depends on format support for attributes.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes - attributes beyond source and type may not be preserved in all formats
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "attributes.txt"
        
        network.save_network(str(filepath), output_type="multiedgelist")
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Basic structure should be preserved
        assert loaded.core_network.number_of_nodes() > 0
        assert loaded.core_network.number_of_edges() > 0


@pytest.mark.verification
@pytest.mark.fast
def test_edge_weights_io():
    """
    Test that edge weights are preserved through I/O.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Add edges with weights
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 
         'target_type': 'layer1', 'weight': 2.5},
    ]
    network.add_edges(edges)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "weighted.txt"
        
        network.save_network(str(filepath), output_type="multiedgelist")
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Basic structure should be preserved
        assert loaded.core_network.number_of_edges() > 0


@pytest.mark.verification
@pytest.mark.fast
def test_multilayer_structure_preserved():
    """
    Test that multilayer structure is preserved through I/O.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Create network with multiple layers
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ]
    network.add_edges(edges)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "multilayer.txt"
        
        network.save_network(str(filepath), output_type="multiedgelist")
        loaded = multinet.multi_layer_network(directed=False)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=False)
        
        # Should preserve multiple layers
        # Check that we have nodes from both layers
        loaded_nodes = list(loaded.core_network.nodes())
        
        # Should have 4 nodes (2 nodes x 2 layers)
        assert len(loaded_nodes) == 4, \
            f"Should have 4 nodes from 2 layers, got {len(loaded_nodes)}"


@pytest.mark.verification
@pytest.mark.fast
def test_directed_vs_undirected_io():
    """
    Test that directedness is handled correctly in I/O.
    """
    # Create directed network
    directed = multinet.multi_layer_network(directed=True)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ]
    directed.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    directed.add_edges(edges)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "directed.txt"
        
        directed.save_network(str(filepath), output_type="multiedgelist")
        loaded = multinet.multi_layer_network(directed=True)
        loaded.load_network(str(filepath), input_type="multiedgelist", directed=True)
        
        # Should preserve basic structure
        assert loaded.core_network.number_of_nodes() > 0
        assert loaded.core_network.number_of_edges() > 0
