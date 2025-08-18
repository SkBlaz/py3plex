#!/usr/bin/env python3
"""
Unit tests for py3plex.core.supporting module
Tests core supporting functions at function level
"""

import sys
import os
import unittest
from collections import defaultdict
import tempfile

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import what we can
NETWORKX_AVAILABLE = False
parse_gaf_to_uniprot_GO = None
split_to_layers = None
add_mpx_edges = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    pass

try:
    from py3plex.core.supporting import parse_gaf_to_uniprot_GO
except ImportError:
    pass

if NETWORKX_AVAILABLE:
    try:
        from py3plex.core.supporting import split_to_layers, add_mpx_edges
    except ImportError:
        pass


def test_split_to_layers():
    """Test the split_to_layers function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping split_to_layers tests: NetworkX not available")
        return True
        
    print("Testing split_to_layers function...")
    
    # Create test multilayer network
    G = nx.MultiGraph()
    
    # Add nodes with layer information in tuple format (node_id, layer)
    nodes_with_layers = [
        (('node1', 'layer1'), {'type': 'layer1'}),
        (('node2', 'layer1'), {'type': 'layer1'}), 
        (('node3', 'layer2'), {'type': 'layer2'}),
        (('node4', 'layer2'), {'type': 'layer2'}),
        (('node5', 'layer3'), {'type': 'layer3'})
    ]
    
    for node, attrs in nodes_with_layers:
        G.add_node(node, **attrs)
    
    # Add edges within and between layers
    G.add_edge(('node1', 'layer1'), ('node2', 'layer1'))
    G.add_edge(('node3', 'layer2'), ('node4', 'layer2'))
    G.add_edge(('node1', 'layer1'), ('node3', 'layer2'))  # inter-layer edge
    
    # Test the function
    result = split_to_layers(G)
    
    # Verify results
    assert isinstance(result, dict), "Should return dictionary"
    assert 'layer1' in result, "Should contain layer1"
    assert 'layer2' in result, "Should contain layer2" 
    assert 'layer3' in result, "Should contain layer3"
    
    # Check layer1 has correct nodes
    layer1_nodes = list(result['layer1'].nodes())
    expected_layer1 = [('node1', 'layer1'), ('node2', 'layer1')]
    assert len(layer1_nodes) == 2, f"Layer1 should have 2 nodes, got {len(layer1_nodes)}"
    
    # Check layer2 has correct nodes
    layer2_nodes = list(result['layer2'].nodes())
    expected_layer2 = [('node3', 'layer2'), ('node4', 'layer2')]
    assert len(layer2_nodes) == 2, f"Layer2 should have 2 nodes, got {len(layer2_nodes)}"
    
    # Check layer3 has correct node
    layer3_nodes = list(result['layer3'].nodes())
    assert len(layer3_nodes) == 1, f"Layer3 should have 1 node, got {len(layer3_nodes)}"
    
    print("✅ split_to_layers function tests PASSED")
    return True


def test_split_to_layers_fallback():
    """Test split_to_layers with type attribute fallback"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping split_to_layers fallback tests: NetworkX not available")
        return True
        
    print("Testing split_to_layers fallback logic...")
    
    # Create test network with type attributes instead of tuple format
    G = nx.MultiGraph()
    
    # Add nodes with type attributes
    G.add_node('node1', type='typeA')
    G.add_node('node2', type='typeA')
    G.add_node('node3', type='typeB')
    
    # Test the function
    result = split_to_layers(G)
    
    # Verify results
    assert isinstance(result, dict), "Should return dictionary"
    assert 'typeA' in result, "Should contain typeA"
    assert 'typeB' in result, "Should contain typeB"
    
    typeA_nodes = list(result['typeA'].nodes())
    assert len(typeA_nodes) == 2, f"TypeA should have 2 nodes, got {len(typeA_nodes)}"
    
    typeB_nodes = list(result['typeB'].nodes())
    assert len(typeB_nodes) == 1, f"TypeB should have 1 node, got {len(typeB_nodes)}"
    
    print("✅ split_to_layers fallback tests PASSED")
    return True


def test_add_mpx_edges():
    """Test the add_mpx_edges function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping add_mpx_edges tests: NetworkX not available")
        return True
        
    print("Testing add_mpx_edges function...")
    
    # Create test multilayer network with same nodes in different layers
    G = nx.MultiGraph()
    
    # Add same node in different layers  
    G.add_node(('A', 'layer1'), type='layer1')
    G.add_node(('A', 'layer2'), type='layer2')
    G.add_node(('B', 'layer1'), type='layer1') 
    G.add_node(('B', 'layer2'), type='layer2')
    G.add_node(('C', 'layer1'), type='layer1')  # Only in layer1
    
    # Add some intra-layer edges
    G.add_edge(('A', 'layer1'), ('B', 'layer1'))
    G.add_edge(('A', 'layer2'), ('B', 'layer2'))
    
    original_edge_count = G.number_of_edges()
    
    # Test the function
    result = add_mpx_edges(G)
    
    # Verify results
    assert result is G, "Should return the same graph object"
    
    # Should have added multiplex edges for nodes A and B
    new_edge_count = result.number_of_edges()
    assert new_edge_count > original_edge_count, f"Should have added edges: {original_edge_count} -> {new_edge_count}"
    
    # Check for multiplex edges
    mpx_edges = [(u, v, d) for u, v, d in result.edges(data=True) if d.get('type') == 'mpx']
    assert len(mpx_edges) >= 2, f"Should have at least 2 multiplex edges, got {len(mpx_edges)}"
    
    # Verify specific multiplex edges exist
    edge_found_A = False
    edge_found_B = False
    for u, v, d in mpx_edges:
        if u == ('A', 'layer1') and v == ('A', 'layer2'):
            edge_found_A = True
        if u == ('B', 'layer1') and v == ('B', 'layer2'):
            edge_found_B = True
    
    assert edge_found_A or any(u == ('A', 'layer2') and v == ('A', 'layer1') for u, v, d in mpx_edges), "Should have multiplex edge for node A"
    assert edge_found_B or any(u == ('B', 'layer2') and v == ('B', 'layer1') for u, v, d in mpx_edges), "Should have multiplex edge for node B"
    
    print("✅ add_mpx_edges function tests PASSED")
    return True


def test_parse_gaf_to_uniprot_GO():
    """Test the parse_gaf_to_uniprot_GO function"""
    if parse_gaf_to_uniprot_GO is None:
        print("⚠️ Skipping parse_gaf_to_uniprot_GO tests: Function not available")
        return True
        
    print("Testing parse_gaf_to_uniprot_GO function...")
    
    # Create temporary test GAF file
    test_gaf_content = """!gaf-version: 2.1
UniProtKB	P12345	GENE1		GO:0008150	REF:123	IEA	GO:0003674	P	Gene 1	GENE1	protein	taxon:9606	20210101	UniProt
UniProtKB	P67890	GENE2		GO:0008150	REF:456	IEA		P	Gene 2	GENE2	protein	taxon:9606	20210101	UniProt
UniProtKB	P11111	GENE3	NOT	GO:0008150	REF:789	IEA		P	Gene 3	GENE3	protein	taxon:9606	20210101	UniProt
UniProtKB	P12345	GENE1		GO:0003674	REF:101112	IEA		P	Gene 1	GENE1	protein	taxon:9606	20210101	UniProt
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gaf', delete=False) as f:
        f.write(test_gaf_content)
        temp_gaf_file = f.name
    
    try:
        # Test basic functionality
        result = parse_gaf_to_uniprot_GO(temp_gaf_file)
        
        # Verify results
        assert isinstance(result, defaultdict), "Should return defaultdict"
        assert 'P12345' in result, "Should contain P12345"
        assert 'P67890' in result, "Should contain P67890"
        
        # Check P12345 has correct GO terms
        p12345_terms = result['P12345']
        assert 'GO:0008150' in p12345_terms, "P12345 should have GO:0008150"
        assert 'GO:0003674' in p12345_terms, "P12345 should have GO:0003674"
        assert len(p12345_terms) >= 2, f"P12345 should have at least 2 GO terms, got {len(p12345_terms)}"
        
        # Test with filter_terms parameter
        filtered_result = parse_gaf_to_uniprot_GO(temp_gaf_file, filter_terms=1)
        assert isinstance(filtered_result, defaultdict), "Filtered result should be defaultdict"
        
        print("✅ parse_gaf_to_uniprot_GO function tests PASSED")
        return True
        
    finally:
        # Clean up temporary file
        os.unlink(temp_gaf_file)


def run_all_tests():
    """Run all supporting function tests"""
    print("=" * 60)
    print("Running py3plex.core.supporting function tests")
    print("=" * 60)
    
    tests = [
        test_split_to_layers,
        test_split_to_layers_fallback,
        test_add_mpx_edges,
        test_parse_gaf_to_uniprot_GO
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {str(e)}")
            print()
    
    print("=" * 60)
    print(f"Supporting function tests completed: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)