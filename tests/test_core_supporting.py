"""
Tests for core supporting utilities.

This module tests utility functions for network parsing and conversion.
"""
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from py3plex.core.supporting import (
    add_mpx_edges,
    parse_gaf_to_uniprot_GO,
    split_to_layers,
)


def test_split_to_layers_simple():
    """Test splitting network into layers."""
    G = nx.Graph()
    G.add_node(('A', 'layer1'))
    G.add_node(('B', 'layer1'))
    G.add_node(('C', 'layer2'))
    G.add_node(('D', 'layer2'))
    
    layers = split_to_layers(G)
    
    assert isinstance(layers, dict)
    assert 'layer1' in layers
    assert 'layer2' in layers
    assert len(layers['layer1'].nodes()) == 2
    assert len(layers['layer2'].nodes()) == 2


def test_split_to_layers_with_edges():
    """Test that split preserves edges within layers."""
    G = nx.Graph()
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))
    G.add_edge(('C', 'layer2'), ('D', 'layer2'))
    
    layers = split_to_layers(G)
    
    assert layers['layer1'].has_edge(('A', 'layer1'), ('B', 'layer1'))
    assert layers['layer2'].has_edge(('C', 'layer2'), ('D', 'layer2'))


def test_split_to_layers_with_type_attribute():
    """Test splitting when layer info is in node 'type' attribute."""
    G = nx.Graph()
    G.add_node('A', type='layer1')
    G.add_node('B', type='layer1')
    G.add_node('C', type='layer2')
    
    layers = split_to_layers(G)
    
    assert 'layer1' in layers
    assert 'layer2' in layers
    assert 'A' in layers['layer1'].nodes()
    assert 'C' in layers['layer2'].nodes()


def test_split_to_layers_empty_network():
    """Test splitting empty network."""
    G = nx.Graph()
    
    layers = split_to_layers(G)
    
    assert isinstance(layers, dict)
    assert len(layers) == 0


def test_split_to_layers_single_layer():
    """Test splitting network with single layer."""
    G = nx.Graph()
    G.add_node(('A', 'layer1'))
    G.add_node(('B', 'layer1'))
    
    layers = split_to_layers(G)
    
    assert len(layers) == 1
    assert 'layer1' in layers


def test_split_to_layers_directed():
    """Test splitting directed graph."""
    G = nx.DiGraph()
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))
    G.add_edge(('C', 'layer2'), ('D', 'layer2'))
    
    layers = split_to_layers(G)
    
    assert isinstance(layers['layer1'], (nx.DiGraph, nx.MultiDiGraph))
    assert isinstance(layers['layer2'], (nx.DiGraph, nx.MultiDiGraph))


def test_split_to_layers_multigraph():
    """Test splitting multigraph."""
    G = nx.MultiGraph()
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))  # Parallel edge
    
    layers = split_to_layers(G)
    
    assert isinstance(layers['layer1'], (nx.MultiGraph, nx.MultiDiGraph))


def test_add_mpx_edges_simple():
    """Test adding multiplex edges between layers."""
    G = nx.Graph()
    # Same node 'A' in two layers
    G.add_node(('A', 'layer1'))
    G.add_node(('A', 'layer2'))
    # Different node 'B' in one layer
    G.add_node(('B', 'layer1'))
    
    G_with_mpx = add_mpx_edges(G)
    
    # Should have multiplex edge between ('A', 'layer1') and ('A', 'layer2')
    assert G_with_mpx.has_edge(('A', 'layer1'), ('A', 'layer2'))
    # No multiplex edge for B (not in layer2)
    assert not G_with_mpx.has_edge(('B', 'layer1'), ('B', 'layer2'))


def test_add_mpx_edges_multiple_nodes():
    """Test adding multiplex edges for multiple shared nodes."""
    G = nx.Graph()
    # Nodes A and B exist in both layers
    for node in ['A', 'B']:
        G.add_node((node, 'layer1'))
        G.add_node((node, 'layer2'))
    
    G_with_mpx = add_mpx_edges(G)
    
    # Both should have multiplex edges
    assert G_with_mpx.has_edge(('A', 'layer1'), ('A', 'layer2'))
    assert G_with_mpx.has_edge(('B', 'layer1'), ('B', 'layer2'))


def test_add_mpx_edges_three_layers():
    """Test multiplex edges across three layers."""
    G = nx.Graph()
    # Node A exists in all three layers
    for layer in ['layer1', 'layer2', 'layer3']:
        G.add_node(('A', layer))
    
    G_with_mpx = add_mpx_edges(G)
    
    # Should have edges between all pairs
    assert G_with_mpx.has_edge(('A', 'layer1'), ('A', 'layer2'))
    assert G_with_mpx.has_edge(('A', 'layer1'), ('A', 'layer3'))
    assert G_with_mpx.has_edge(('A', 'layer2'), ('A', 'layer3'))


def test_add_mpx_edges_preserves_existing():
    """Test that adding multiplex edges preserves existing edges."""
    G = nx.Graph()
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))
    G.add_node(('A', 'layer2'))
    
    G_with_mpx = add_mpx_edges(G)
    
    # Original edge should still exist
    assert G_with_mpx.has_edge(('A', 'layer1'), ('B', 'layer1'))
    # Multiplex edge should be added
    assert G_with_mpx.has_edge(('A', 'layer1'), ('A', 'layer2'))


def test_add_mpx_edges_no_shared_nodes():
    """Test adding multiplex edges when layers share no nodes."""
    G = nx.Graph()
    G.add_node(('A', 'layer1'))
    G.add_node(('B', 'layer2'))
    
    G_with_mpx = add_mpx_edges(G)
    
    # No multiplex edges should be added
    assert not G_with_mpx.has_edge(('A', 'layer1'), ('B', 'layer2'))


def test_add_mpx_edges_empty_network():
    """Test adding multiplex edges to empty network."""
    G = nx.Graph()
    
    G_with_mpx = add_mpx_edges(G)
    
    assert len(G_with_mpx.edges()) == 0


def test_parse_gaf_basic():
    """Test basic GAF parsing."""
    # Create temporary GAF file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gaf', delete=False) as f:
        f.write("!\tcomment line\n")
        f.write("col1\tUNIPROT1\tcol3\tGO:0001234\tcol5\n")
        f.write("col1\tUNIPROT2\tcol3\tcol4\tGO:0005678\n")
        gaf_file = f.name
    
    try:
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        assert isinstance(result, dict)
        assert 'UNIPROT1' in result
        assert 'UNIPROT2' in result
        # Check that GO terms are present (may have trailing newlines/whitespace)
        assert any('GO:0001234' in term for term in result['UNIPROT1'])
        assert any('GO:0005678' in term for term in result['UNIPROT2'])
    finally:
        Path(gaf_file).unlink()


def test_parse_gaf_with_filtering():
    """Test GAF parsing with term filtering."""
    # Create temporary GAF file with repeated terms
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gaf', delete=False) as f:
        # GO:0001234 appears twice, GO:0005678 once
        f.write("col1\tUNIPROT1\tcol3\tGO:0001234\tcol5\n")
        f.write("col1\tUNIPROT2\tcol3\tGO:0001234\tcol5\n")
        f.write("col1\tUNIPROT3\tcol3\tGO:0005678\tcol5\n")
        gaf_file = f.name
    
    try:
        # Filter to keep only top 1 term (should be GO:0001234)
        result = parse_gaf_to_uniprot_GO(gaf_file, filter_terms=1)
        
        # Only proteins with GO:0001234 should remain
        assert 'UNIPROT1' in result
        assert 'UNIPROT2' in result
        if 'UNIPROT3' in result:
            assert len(result['UNIPROT3']) == 0  # filtered out
    finally:
        Path(gaf_file).unlink()


def test_parse_gaf_malformed_lines():
    """Test that malformed GAF lines are skipped."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gaf', delete=False) as f:
        f.write("valid\tUNIPROT1\tvalid\tGO:0001234\tvalid\n")
        f.write("incomplete\n")  # Malformed
        f.write("valid\tUNIPROT2\tvalid\tGO:0005678\tvalid\n")
        gaf_file = f.name
    
    try:
        result = parse_gaf_to_uniprot_GO(gaf_file)
        
        # Should successfully parse valid lines
        assert 'UNIPROT1' in result
        assert 'UNIPROT2' in result
    finally:
        Path(gaf_file).unlink()


def test_split_to_layers_returns_networkx():
    """Test that split_to_layers returns NetworkX graph objects."""
    G = nx.Graph()
    G.add_node(('A', 'layer1'))
    
    layers = split_to_layers(G)
    
    for layer_graph in layers.values():
        assert isinstance(layer_graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))


def test_add_mpx_edges_returns_networkx():
    """Test that add_mpx_edges returns NetworkX graph."""
    G = nx.Graph()
    G.add_node(('A', 'layer1'))
    
    result = add_mpx_edges(G)
    
    assert isinstance(result, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
