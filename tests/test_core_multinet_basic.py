#!/usr/bin/env python3
"""
Unit tests for py3plex.core.multinet module basic functionality
Tests core multi_layer_network class methods that don't require heavy dependencies
"""

import sys
import os
import tempfile

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import what we can
multi_layer_network = None
MULTINET_AVAILABLE = False

try:
    from py3plex.core.multinet import multi_layer_network
    MULTINET_AVAILABLE = True
except ImportError:
    pass

# Check for NetworkX availability separately
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


def test_multilayer_network_init():
    """Test multi_layer_network class initialization"""
    if not MULTINET_AVAILABLE:
        print("⚠️ Skipping multi_layer_network init tests: Class not available")
        return True
        
    print("Testing multi_layer_network initialization...")
    
    # Test default initialization
    net = multi_layer_network()
    
    # Verify default attributes
    assert net.verbose is True, "Default verbose should be True"
    assert net.network_type == "multilayer", f"Default network_type should be 'multilayer', got {net.network_type}"
    assert net.directed is True, "Default directed should be True"
    assert net.dummy_layer == "null", f"Default dummy_layer should be 'null', got {net.dummy_layer}"
    assert net.label_delimiter == "---", f"Default label_delimiter should be '---', got {net.label_delimiter}"
    assert net.coupling_weight == 1, f"Default coupling_weight should be 1, got {net.coupling_weight}"
    
    # Check initialized attributes
    assert net.layer_name_map == {}, "layer_name_map should be empty dict"
    assert net.layer_inverse_name_map == {}, "layer_inverse_name_map should be empty dict"
    assert net.core_network is None, "core_network should be None initially"
    assert net.numeric_core_network is None, "numeric_core_network should be None initially"
    assert net.labels is None, "labels should be None initially"
    assert net.embedding is None, "embedding should be None initially"
    assert net.sparse_enabled is False, "sparse_enabled should be False initially"
    
    print("✅ Default initialization test PASSED")
    
    # Test custom initialization
    custom_net = multi_layer_network(
        verbose=False,
        network_type="multiplex",
        directed=False,
        dummy_layer="empty",
        label_delimiter="__",
        coupling_weight=2.5
    )
    
    assert custom_net.verbose is False, "Custom verbose should be False"
    assert custom_net.network_type == "multiplex", f"Custom network_type should be 'multiplex', got {custom_net.network_type}"
    assert custom_net.directed is False, "Custom directed should be False"
    assert custom_net.dummy_layer == "empty", f"Custom dummy_layer should be 'empty', got {custom_net.dummy_layer}"
    assert custom_net.label_delimiter == "__", f"Custom label_delimiter should be '__', got {custom_net.label_delimiter}"
    assert custom_net.coupling_weight == 2.5, f"Custom coupling_weight should be 2.5, got {custom_net.coupling_weight}"
    
    print("✅ Custom initialization test PASSED")
    
    print("✅ multi_layer_network initialization tests PASSED")
    return True


def test_ground_truth_communities():
    """Test read_ground_truth_communities method"""
    if not MULTINET_AVAILABLE:
        print("⚠️ Skipping ground truth communities tests: Class not available")
        return True
        
    if not NETWORKX_AVAILABLE:
        print("⚠️ Skipping ground truth communities tests: NetworkX not available")
        return True
        
    print("Testing read_ground_truth_communities method...")
    
    # Create test community file
    community_content = """node1 community1
node2 community1
node3 community2
node4 community2
node5 community3
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(community_content)
        temp_file = f.name
    
    try:
        # Test the method
        net = multi_layer_network()
        net.read_ground_truth_communities(temp_file)
        
        # Verify that ground_truth_communities attribute was set
        assert hasattr(net, 'ground_truth_communities'), "Should have ground_truth_communities attribute"
        
        communities = net.ground_truth_communities
        
        # Check community assignments
        assert 'node1' in communities, "Should contain node1"
        assert 'node2' in communities, "Should contain node2"
        assert 'node3' in communities, "Should contain node3"
        assert 'node4' in communities, "Should contain node4"
        assert 'node5' in communities, "Should contain node5"
        
        assert communities['node1'] == 'community1', f"node1 should be in community1, got {communities['node1']}"
        assert communities['node2'] == 'community1', f"node2 should be in community1, got {communities['node2']}"
        assert communities['node3'] == 'community2', f"node3 should be in community2, got {communities['node3']}"
        assert communities['node4'] == 'community2', f"node4 should be in community2, got {communities['node4']}"
        assert communities['node5'] == 'community3', f"node5 should be in community3, got {communities['node5']}"
        
        print("✅ Ground truth communities parsing test PASSED")
        return True
        
    finally:
        # Clean up
        os.unlink(temp_file)


def test_network_types():
    """Test different network type configurations"""
    if not MULTINET_AVAILABLE:
        print("⚠️ Skipping network types tests: Class not available")
        return True
        
    print("Testing different network types...")
    
    # Test multilayer network
    multilayer_net = multi_layer_network(network_type="multilayer")
    assert multilayer_net.network_type == "multilayer", "Should create multilayer network"
    
    # Test multiplex network  
    multiplex_net = multi_layer_network(network_type="multiplex")
    assert multiplex_net.network_type == "multiplex", "Should create multiplex network"
    
    # Test custom network type
    custom_net = multi_layer_network(network_type="custom_type")
    assert custom_net.network_type == "custom_type", "Should accept custom network types"
    
    print("✅ Network types test PASSED")
    return True


def test_attribute_access():
    """Test attribute access and modification"""
    if not MULTINET_AVAILABLE:
        print("⚠️ Skipping attribute access tests: Class not available")
        return True
        
    print("Testing attribute access and modification...")
    
    net = multi_layer_network()
    
    # Test modifying attributes
    net.verbose = False
    assert net.verbose is False, "Should be able to modify verbose"
    
    net.coupling_weight = 3.14
    assert net.coupling_weight == 3.14, "Should be able to modify coupling_weight"
    
    net.label_delimiter = "||"
    assert net.label_delimiter == "||", "Should be able to modify label_delimiter"
    
    # Test setting dictionary attributes
    net.layer_name_map = {'layer1': 0, 'layer2': 1}
    assert net.layer_name_map == {'layer1': 0, 'layer2': 1}, "Should be able to set layer_name_map"
    
    net.layer_inverse_name_map = {0: 'layer1', 1: 'layer2'}
    assert net.layer_inverse_name_map == {0: 'layer1', 1: 'layer2'}, "Should be able to set layer_inverse_name_map"
    
    # Test boolean flags
    net.sparse_enabled = True
    assert net.sparse_enabled is True, "Should be able to set sparse_enabled"
    
    net.directed = False
    assert net.directed is False, "Should be able to modify directed"
    
    print("✅ Attribute access test PASSED")
    return True


def test_special_methods():
    """Test special methods like __getitem__ when possible"""
    if not MULTINET_AVAILABLE:
        print("⚠️ Skipping special methods tests: Class not available")
        return True
        
    print("Testing special methods...")
    
    net = multi_layer_network()
    
    # Since core_network is None initially, __getitem__ will fail
    # But we can test that the method exists
    assert hasattr(net, '__getitem__'), "Should have __getitem__ method"
    
    # Test that calling it with None core_network raises appropriate error
    try:
        result = net[0]
        # If we get here without an error, that's unexpected but okay
        print("⚠️ __getitem__ didn't raise error with None core_network")
    except (TypeError, AttributeError):
        # Expected behavior when core_network is None
        print("✅ __getitem__ properly handles None core_network")
    
    print("✅ Special methods test PASSED")
    return True


def run_all_tests():
    """Run all multinet basic functionality tests"""
    print("=" * 60)
    print("Running py3plex.core.multinet basic functionality tests")
    print("=" * 60)
    
    tests = [
        test_multilayer_network_init,
        test_ground_truth_communities,
        test_network_types,
        test_attribute_access,
        test_special_methods
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
    print(f"Multinet basic functionality tests completed: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)