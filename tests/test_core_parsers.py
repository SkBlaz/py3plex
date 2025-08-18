#!/usr/bin/env python3
"""
Unit tests for py3plex.core.parsers module
Tests core parsing functions at function level
"""

import sys
import os
import tempfile

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import what we can
NETWORKX_AVAILABLE = False
parse_embedding = None
parse_nx = None
parse_simple_edgelist = None
parse_multiedge_tuple_list = None
save_edgelist = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    pass

# Try to import functions that don't require NetworkX
try:
    from py3plex.core.parsers import parse_embedding
except ImportError:
    pass

if NETWORKX_AVAILABLE:
    try:
        from py3plex.core.parsers import (
            parse_nx, parse_simple_edgelist, 
            parse_multiedge_tuple_list, save_edgelist
        )
    except ImportError:
        pass


def test_parse_nx():
    """Test parse_nx function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping parse_nx tests: NetworkX not available")
        return True
        
    print("Testing parse_nx function...")
    
    # Create a simple NetworkX graph
    G = nx.Graph()
    G.add_edge('A', 'B', weight=1.5)
    G.add_edge('B', 'C', weight=2.0)
    G.add_edge('A', 'C', weight=0.5)
    
    # Test undirected
    result, labels, activity = parse_nx(G, directed=False)
    
    # Verify results
    assert isinstance(result, (nx.Graph, nx.MultiGraph)), "Should return NetworkX graph"
    assert result.number_of_nodes() == 3, f"Should have 3 nodes, got {result.number_of_nodes()}"
    assert result.number_of_edges() == 3, f"Should have 3 edges, got {result.number_of_edges()}"
    
    # Check that nodes are preserved
    result_nodes = set(result.nodes())
    expected_nodes = {'A', 'B', 'C'}
    assert result_nodes == expected_nodes, f"Nodes should be {expected_nodes}, got {result_nodes}"
    
    # Test directed
    DG = nx.DiGraph()
    DG.add_edge('X', 'Y', weight=1.0)
    DG.add_edge('Y', 'Z', weight=2.0)
    
    result_directed, _, _ = parse_nx(DG, directed=True)
    assert isinstance(result_directed, (nx.DiGraph, nx.MultiDiGraph)), "Should return directed graph"
    assert result_directed.number_of_nodes() == 3, "Should preserve nodes"
    assert result_directed.number_of_edges() == 2, "Should preserve edges"
    
    print("✅ parse_nx function tests PASSED")
    return True


def test_parse_simple_edgelist():
    """Test parse_simple_edgelist function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping parse_simple_edgelist tests: NetworkX not available")
        return True
        
    print("Testing parse_simple_edgelist function...")
    
    # Create test edgelist content
    edgelist_content = """node1 node2
node2 node3
node1 node3
node4 node5
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write(edgelist_content)
        temp_file = f.name
    
    try:
        # Test undirected
        result, labels, activity = parse_simple_edgelist(temp_file, directed=False)
        
        # Verify results
        assert isinstance(result, (nx.Graph, nx.MultiGraph)), "Should return NetworkX graph"
        assert result.number_of_nodes() == 5, f"Should have 5 nodes, got {result.number_of_nodes()}"
        assert result.number_of_edges() == 4, f"Should have 4 edges, got {result.number_of_edges()}"
        
        # Check specific edges exist
        assert result.has_edge('node1', 'node2'), "Should have edge node1-node2"
        assert result.has_edge('node2', 'node3'), "Should have edge node2-node3"
        assert result.has_edge('node1', 'node3'), "Should have edge node1-node3"
        assert result.has_edge('node4', 'node5'), "Should have edge node4-node5"
        
        # Test directed
        result_directed, _, _ = parse_simple_edgelist(temp_file, directed=True)
        assert isinstance(result_directed, (nx.DiGraph, nx.MultiDiGraph)), "Should return directed graph"
        assert result_directed.number_of_nodes() == 5, "Should have same nodes"
        assert result_directed.number_of_edges() == 4, "Should have same edges"
        
        print("✅ parse_simple_edgelist function tests PASSED")
        return True
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_parse_embedding():
    """Test parse_embedding function"""
    if parse_embedding is None:
        print("⚠️ Skipping parse_embedding tests: Function not available")
        return True
        
    print("Testing parse_embedding function...")
    
    # Create test embedding content
    embedding_content = """3 2
node1 0.1 0.2
node2 0.3 0.4
node3 0.5 0.6
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.emb', delete=False) as f:
        f.write(embedding_content)
        temp_file = f.name
    
    try:
        # Test the function
        result = parse_embedding(temp_file)
        
        # Verify results
        assert isinstance(result, dict), "Should return dictionary"
        assert len(result) == 3, f"Should have 3 embeddings, got {len(result)}"
        
        # Check specific embeddings
        assert 'node1' in result, "Should contain node1"
        assert 'node2' in result, "Should contain node2"
        assert 'node3' in result, "Should contain node3"
        
        # Check embedding values
        node1_emb = result['node1']
        assert len(node1_emb) == 2, f"node1 should have 2D embedding, got {len(node1_emb)}"
        assert abs(float(node1_emb[0]) - 0.1) < 1e-6, f"node1[0] should be 0.1, got {node1_emb[0]}"
        assert abs(float(node1_emb[1]) - 0.2) < 1e-6, f"node1[1] should be 0.2, got {node1_emb[1]}"
        
        node2_emb = result['node2']
        assert abs(float(node2_emb[0]) - 0.3) < 1e-6, f"node2[0] should be 0.3, got {node2_emb[0]}"
        assert abs(float(node2_emb[1]) - 0.4) < 1e-6, f"node2[1] should be 0.4, got {node2_emb[1]}"
        
        print("✅ parse_embedding function tests PASSED")
        return True
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_parse_multiedge_tuple_list():
    """Test parse_multiedge_tuple_list function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping parse_multiedge_tuple_list tests: NetworkX not available")
        return True
        
    print("Testing parse_multiedge_tuple_list function...")
    
    # Create test edge list as tuples
    edge_list = [
        ('A', 'B', {'weight': 1.0, 'type': 'friends'}),
        ('B', 'C', {'weight': 2.0, 'type': 'colleagues'}),
        ('A', 'C', {'weight': 0.5, 'type': 'friends'}),
        ('D', 'E', {'type': 'family'})
    ]
    
    # Test undirected
    result, labels, activity = parse_multiedge_tuple_list(edge_list, directed=False)
    
    # Verify results
    assert isinstance(result, (nx.Graph, nx.MultiGraph)), "Should return NetworkX graph"
    assert result.number_of_nodes() == 5, f"Should have 5 nodes, got {result.number_of_nodes()}"
    assert result.number_of_edges() == 4, f"Should have 4 edges, got {result.number_of_edges()}"
    
    # Check edge attributes are preserved
    edge_data = result.get_edge_data('A', 'B')
    assert edge_data is not None, "Should have edge A-B"
    if isinstance(edge_data, dict) and 'weight' in edge_data:
        assert edge_data['weight'] == 1.0, f"Edge A-B should have weight 1.0"
    
    # Test directed
    result_directed, _, _ = parse_multiedge_tuple_list(edge_list, directed=True)
    assert isinstance(result_directed, (nx.DiGraph, nx.MultiDiGraph)), "Should return directed graph"
    
    print("✅ parse_multiedge_tuple_list function tests PASSED")
    return True


def test_save_edgelist():
    """Test save_edgelist function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping save_edgelist tests: NetworkX not available")
        return True
        
    print("Testing save_edgelist function...")
    
    # Create test graph
    G = nx.Graph()
    G.add_edge('A', 'B', weight=1.5)
    G.add_edge('B', 'C', weight=2.0) 
    G.add_edge('A', 'C', weight=0.5)
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        temp_file = f.name
    
    try:
        # Test saving without attributes
        save_edgelist(G, temp_file, attributes=False)
        
        # Verify file was created and has content
        assert os.path.exists(temp_file), "Output file should be created"
        
        with open(temp_file, 'r') as f:
            content = f.read().strip()
            lines = content.split('\n')
            
        assert len(lines) >= 3, f"Should have at least 3 lines, got {len(lines)}"
        
        # Check that each line has two nodes
        for line in lines:
            if line.strip():  # Skip empty lines
                parts = line.strip().split()
                assert len(parts) >= 2, f"Each line should have at least 2 parts, got {len(parts)} in '{line}'"
        
        # Test saving with attributes
        save_edgelist(G, temp_file, attributes=True)
        
        with open(temp_file, 'r') as f:
            content_with_attrs = f.read().strip()
            
        # With attributes, lines should be longer
        assert len(content_with_attrs) >= len(content), "Content with attributes should be longer"
        
        print("✅ save_edgelist function tests PASSED")
        return True
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def run_all_tests():
    """Run all parser function tests"""
    print("=" * 60)
    print("Running py3plex.core.parsers function tests")
    print("=" * 60)
    
    tests = [
        test_parse_nx,
        test_parse_simple_edgelist,
        test_parse_embedding,
        test_parse_multiedge_tuple_list,
        test_save_edgelist
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
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print(f"Parser function tests completed: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)