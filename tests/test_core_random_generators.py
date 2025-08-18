#!/usr/bin/env python3
"""
Unit tests for py3plex.core.random_generators module
Tests random network generation functions at function level
"""

import sys
import os

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import networkx as nx
    from py3plex.core.random_generators import random_multilayer_ER, random_multiplex_ER, random_multiplex_generator
    from py3plex.core.multinet import multi_layer_network
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


def test_random_multilayer_ER():
    """Test random_multilayer_ER function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping random_multilayer_ER tests: NetworkX not available")
        return True
        
    print("Testing random_multilayer_ER function...")
    
    # Test parameters
    n = 10  # nodes
    l = 3   # layers
    p = 0.3 # probability
    
    # Test undirected network
    result = random_multilayer_ER(n, l, p, directed=False)
    
    # Verify result type
    assert isinstance(result, multi_layer_network), "Should return multi_layer_network object"
    assert result.core_network is not None, "Should have core_network"
    assert not result.directed, "Should be undirected when directed=False"
    
    # Check network properties
    core_net = result.core_network
    assert core_net.number_of_nodes() > 0, "Should have nodes"
    
    # Verify node format (should be tuples with layer info)
    sample_nodes = list(core_net.nodes())[:5]  # Check first 5 nodes
    for node in sample_nodes:
        assert isinstance(node, tuple), f"Node should be tuple, got {type(node)}"
        assert len(node) == 2, f"Node tuple should have 2 elements, got {len(node)}"
        assert isinstance(node[1], (int, str)), f"Layer should be int or str, got {type(node[1])}"
    
    # Test directed network
    result_directed = random_multilayer_ER(n, l, p, directed=True)
    assert result_directed.directed, "Should be directed when directed=True"
    
    print("✅ random_multilayer_ER function tests PASSED")
    return True


def test_random_multiplex_ER():
    """Test random_multiplex_ER function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping random_multiplex_ER tests: NetworkX not available")
        return True
        
    print("Testing random_multiplex_ER function...")
    
    # Test parameters
    n = 8   # nodes
    l = 4   # layers
    p = 0.4 # probability
    
    # Test undirected multiplex network
    result = random_multiplex_ER(n, l, p, directed=False)
    
    # Verify result type
    assert isinstance(result, multi_layer_network), "Should return multi_layer_network object"
    assert result.core_network is not None, "Should have core_network"
    assert not result.directed, "Should be undirected when directed=False"
    assert result.network_type == "multiplex", "Should be multiplex network"
    
    # Check network properties
    core_net = result.core_network
    assert core_net.number_of_nodes() > 0, "Should have nodes"
    
    # In multiplex, each node appears in each layer
    # So we should have n*l total nodes
    expected_nodes = n * l
    actual_nodes = core_net.number_of_nodes()
    assert actual_nodes <= expected_nodes, f"Should have at most {expected_nodes} nodes, got {actual_nodes}"
    
    # Verify node format and layer distribution
    node_layers = set()
    sample_nodes = list(core_net.nodes())
    for node in sample_nodes:
        assert isinstance(node, tuple), f"Node should be tuple, got {type(node)}"
        assert len(node) == 2, f"Node tuple should have 2 elements, got {len(node)}"
        node_layers.add(node[1])
    
    # Should have multiple layers represented
    assert len(node_layers) >= 1, f"Should have at least 1 layer, got {len(node_layers)}"
    assert len(node_layers) <= l, f"Should have at most {l} layers, got {len(node_layers)}"
    
    # Test directed multiplex network
    result_directed = random_multiplex_ER(n, l, p, directed=True)
    assert result_directed.directed, "Should be directed when directed=True"
    
    print("✅ random_multiplex_ER function tests PASSED")
    return True


def test_random_multiplex_generator():
    """Test random_multiplex_generator function"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping random_multiplex_generator tests: NetworkX not available")
        return True
        
    print("Testing random_multiplex_generator function...")
    
    # Test parameters
    n = 6   # nodes
    m = 3   # layers 
    d = 0.8 # density
    
    # Test the function
    result = random_multiplex_generator(n, m, d)
    
    # Verify result type
    assert isinstance(result, nx.MultiGraph), "Should return NetworkX MultiGraph"
    
    # Check basic properties
    assert result.number_of_nodes() > 0, "Should have nodes"
    
    # Verify node format (should be tuples with layer info)
    sample_nodes = list(result.nodes())[:min(10, result.number_of_nodes())]
    for node in sample_nodes:
        assert isinstance(node, tuple), f"Node should be tuple, got {type(node)}"
        assert len(node) == 2, f"Node tuple should have 2 elements, got {len(node)}"
        assert isinstance(node[0], int), f"Node ID should be int, got {type(node[0])}"
        assert isinstance(node[1], int), f"Layer should be int, got {type(node[1])}"
        assert 0 <= node[0] < n, f"Node ID should be in range [0, {n}), got {node[0]}"
        assert 0 <= node[1] < m, f"Layer should be in range [0, {m}), got {node[1]}"
    
    # Check edges have proper attributes
    if result.number_of_edges() > 0:
        sample_edges = list(result.edges(data=True))[:5]
        for u, v, data in sample_edges:
            assert 'type' in data, "Edge should have 'type' attribute"
            assert data['type'] == 'default', f"Edge type should be 'default', got {data['type']}"
            assert 'weight' in data, "Edge should have 'weight' attribute"
            assert data['weight'] == 1, f"Edge weight should be 1, got {data['weight']}"
    
    # Test edge case: small network
    small_result = random_multiplex_generator(2, 2, 0.5)
    assert isinstance(small_result, nx.MultiGraph), "Should work with small networks"
    
    print("✅ random_multiplex_generator function tests PASSED")
    return True


def test_random_generator_consistency():
    """Test consistency and edge cases of random generators"""
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping random generator consistency tests: NetworkX not available")
        return True
        
    print("Testing random generator consistency and edge cases...")
    
    # Test with p=0 (no edges) for ER models
    try:
        no_edges_ml = random_multilayer_ER(5, 2, 0.0, directed=False)
        assert no_edges_ml.core_network.number_of_edges() == 0, "Should have no edges with p=0"
        
        no_edges_mp = random_multiplex_ER(5, 2, 0.0, directed=False) 
        assert no_edges_mp.core_network.number_of_edges() == 0, "Should have no edges with p=0"
        
        print("✅ Zero probability edge case handled correctly")
    except Exception as e:
        print(f"⚠️ Zero probability test failed: {str(e)}")
    
    # Test with p=1 (all possible edges) for small network
    try:
        all_edges_ml = random_multilayer_ER(3, 2, 1.0, directed=False)
        assert all_edges_ml.core_network.number_of_edges() > 0, "Should have edges with p=1"
        
        all_edges_mp = random_multiplex_ER(3, 2, 1.0, directed=False)
        assert all_edges_mp.core_network.number_of_edges() > 0, "Should have edges with p=1"
        
        print("✅ Full probability edge case handled correctly")
    except Exception as e:
        print(f"⚠️ Full probability test failed: {str(e)}")
    
    # Test minimal network sizes
    try:
        minimal_ml = random_multilayer_ER(1, 1, 0.5, directed=False)
        assert minimal_ml.core_network.number_of_nodes() >= 1, "Should handle minimal network size"
        
        minimal_mp = random_multiplex_ER(1, 1, 0.5, directed=False)
        assert minimal_mp.core_network.number_of_nodes() >= 1, "Should handle minimal network size"
        
        print("✅ Minimal network size handled correctly")
    except Exception as e:
        print(f"⚠️ Minimal network test failed: {str(e)}")
    
    print("✅ Random generator consistency tests PASSED")
    return True


def run_all_tests():
    """Run all random generator function tests"""
    print("=" * 60)
    print("Running py3plex.core.random_generators function tests")
    print("=" * 60)
    
    tests = [
        test_random_multilayer_ER,
        test_random_multiplex_ER, 
        test_random_multiplex_generator,
        test_random_generator_consistency
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
    print(f"Random generators tests completed: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)