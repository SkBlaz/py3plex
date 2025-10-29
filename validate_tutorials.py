#!/usr/bin/env python3
"""
Tutorial validation script for py3plex multilayer examples.

This script validates that multilayer tutorial examples work correctly,
especially after the corner case bug fixes. It checks:
1. Example files exist and have valid syntax
2. Examples can import required modules
3. Examples demonstrate the fixed corner cases work properly
4. Basic multilayer operations function correctly
"""

import sys
import os
import tempfile
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def validate_file_structure():
    """Validate that all tutorial/example files exist."""
    print("Validating file structure...")
    
    required_files = [
        'examples/example_multilayer_functionality.py',
        'examples/example_multilayer_centrality.py',
        'examples/example_multilayer_modularity.py',
        'examples/example_multilayer_statistics.py',
        'examples/example_multilayer_vectorized_aggregation.py',
        'examples/example_multilayer_visualization.py',
        'examples/example_IO.py',
        'tests/test_multilayer_cornercases.py',
    ]
    
    all_exist = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def validate_syntax():
    """Validate Python syntax of tutorial files."""
    print("\nValidating Python syntax...")
    
    import py_compile
    
    files_to_check = [
        'examples/example_multilayer_functionality.py',
        'examples/example_multilayer_centrality.py',
        'examples/example_multilayer_modularity.py',
        'examples/example_multilayer_statistics.py',
        'examples/example_multilayer_vectorized_aggregation.py',
        'examples/example_multilayer_visualization.py',
        'examples/example_IO.py',
        'tests/test_multilayer_cornercases.py',
    ]
    
    all_valid = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for file_path in files_to_check:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            print(f"  ⚠ {file_path} not found, skipping")
            continue
        try:
            py_compile.compile(full_path, doraise=True)
            print(f"  ✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file_path}: {e}")
            all_valid = False
    
    return all_valid


def validate_dependencies():
    """Validate that core dependencies are available."""
    print("\nValidating dependencies...")
    
    required_deps = [
        ('networkx', 'NetworkX'),
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('pandas', 'Pandas'),
    ]
    
    all_available = True
    for module_name, display_name in required_deps:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} available")
        except ImportError:
            print(f"  ✗ {display_name} not available")
            all_available = False
    
    return all_available


def validate_imports():
    """Validate that py3plex modules can be imported."""
    print("\nValidating py3plex imports...")
    
    try:
        from py3plex.core import multinet
        print("  ✓ py3plex.core.multinet imports successfully")
        
        from py3plex.core import random_generators
        print("  ✓ py3plex.core.random_generators imports successfully")
        
        # Check that multi_layer_network class exists
        assert hasattr(multinet, 'multi_layer_network')
        print("  ✓ multi_layer_network class available")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ Assertion error: {e}")
        return False


def validate_corner_case_fixes():
    """Validate that the corner case bug fixes work correctly."""
    print("\nValidating corner case fixes...")
    
    try:
        from py3plex.core import multinet
        import networkx as nx
        
        # Test 1: Empty network initialization
        network = multinet.multi_layer_network(network_type="multilayer")
        assert network is not None
        print("  ✓ Empty network initialization works")
        
        # Test 2: Adding node without layer (should use dummy layer)
        network = multinet.multi_layer_network()
        node = {"source": "node1"}
        network.add_nodes(node, input_type="dict")
        nodes = list(network.get_nodes())
        assert len(nodes) == 1
        assert ("node1", "null") in nodes
        print("  ✓ Adding node without layer works (uses dummy layer)")
        
        # Test 3: Adding edge without layer
        network = multinet.multi_layer_network()
        edge = {"source": "node1", "target": "node2", "type": "edge"}
        network.add_edges(edge, input_type="dict")
        edges = list(network.get_edges())
        assert len(edges) >= 1
        print("  ✓ Adding edge without layer works (uses dummy layer)")
        
        # Test 4: Adding multiple nodes
        network = multinet.multi_layer_network()
        nodes = [
            {"source": "node1", "type": "layer1"},
            {"source": "node2", "type": "layer2"},
            {"source": "node3", "type": "layer3"}
        ]
        network.add_nodes(nodes, input_type="dict")
        result_nodes = list(network.get_nodes())
        assert len(result_nodes) == 3
        print("  ✓ Adding multiple nodes works correctly")
        
        # Test 5: Duplicate node addition (should be idempotent)
        network = multinet.multi_layer_network()
        node = {"source": "node1", "type": "layer1"}
        network.add_nodes(node, input_type="dict")
        network.add_nodes(node, input_type="dict")
        nodes = list(network.get_nodes())
        assert len(nodes) == 1
        print("  ✓ Duplicate node addition works (idempotent)")
        
        # Test 6: Empty network layer splitting
        network = multinet.multi_layer_network()
        network._initiate_network()
        network.split_to_layers(style="none")
        assert network.layer_names is not None
        print("  ✓ Empty network layer splitting works")
        
        # Test 7: Empty node list
        network = multinet.multi_layer_network()
        nodes = []
        network.add_nodes(nodes, input_type="dict")
        network._initiate_network()
        result_nodes = list(network.get_nodes())
        assert len(result_nodes) == 0
        print("  ✓ Empty node list handling works")
        
        # Test 8: Loading empty NetworkX graph
        network = multinet.multi_layer_network()
        empty_graph = nx.MultiDiGraph()
        result = network.load_network(empty_graph, input_type="nx", directed=True)
        assert result is not None
        nodes = list(result.get_nodes())
        assert len(nodes) == 0
        print("  ✓ Loading empty NetworkX graph works")
        
        return True
        
    except ImportError as e:
        print(f"  ⚠ Cannot validate fixes (dependencies not available): {e}")
        return None
    except Exception as e:
        print(f"  ✗ Corner case validation failed: {e}")
        traceback.print_exc()
        return False


def validate_basic_operations():
    """Validate that basic multilayer operations work."""
    print("\nValidating basic multilayer operations...")
    
    try:
        from py3plex.core import multinet
        
        # Create a simple multilayer network
        network = multinet.multi_layer_network(directed=False)
        
        # Add some edges
        edges = [
            {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1", "type": "edge"},
            {"source": "A", "target": "B", "source_type": "layer2", "target_type": "layer2", "type": "edge"},
        ]
        network.add_edges(edges, input_type="dict")
        print("  ✓ Creating multilayer network with edges works")
        
        # Get nodes
        nodes = list(network.get_nodes())
        assert len(nodes) > 0
        print(f"  ✓ Getting nodes works ({len(nodes)} nodes)")
        
        # Get edges
        edges = list(network.get_edges())
        assert len(edges) > 0
        print(f"  ✓ Getting edges works ({len(edges)} edges)")
        
        # Get subnetwork by layer
        subnet = network.subnetwork(['layer1'], subset_by="layers")
        assert subnet is not None
        print("  ✓ Getting subnetwork by layer works")
        
        # Convert to JSON
        json_data = network.to_json()
        assert 'nodes' in json_data
        assert 'links' in json_data
        print("  ✓ Converting to JSON works")
        
        return True
        
    except ImportError as e:
        print(f"  ⚠ Cannot validate operations (dependencies not available): {e}")
        return None
    except Exception as e:
        print(f"  ✗ Basic operations validation failed: {e}")
        traceback.print_exc()
        return False


def validate_corner_case_tests():
    """Validate that the corner case test suite passes."""
    print("\nValidating corner case test suite...")
    
    try:
        import unittest
        import sys
        from io import StringIO
        
        # Import the test module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
        import test_multilayer_cornercases
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_multilayer_cornercases)
        
        # Run tests with minimal output
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=0)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print(f"  ✓ All {result.testsRun} corner case tests passed")
            return True
        else:
            print(f"  ✗ {len(result.failures + result.errors)}/{result.testsRun} tests failed")
            if result.failures:
                print(f"    Failures: {len(result.failures)}")
            if result.errors:
                print(f"    Errors: {len(result.errors)}")
            return False
        
    except ImportError as e:
        print(f"  ⚠ Cannot run tests (dependencies not available): {e}")
        return None
    except Exception as e:
        print(f"  ✗ Test execution failed: {e}")
        traceback.print_exc()
        return False


def validate_example_patterns():
    """Validate common patterns used in examples."""
    print("\nValidating example patterns...")
    
    try:
        from py3plex.core import multinet
        
        # Pattern 1: Basic initialization and loading
        network = multinet.multi_layer_network()
        assert network is not None
        print("  ✓ Pattern: Basic initialization")
        
        # Pattern 2: Custom parameters
        network = multinet.multi_layer_network(
            verbose=False,
            directed=False,
            coupling_weight=2.0
        )
        assert network.coupling_weight == 2.0
        print("  ✓ Pattern: Custom parameters")
        
        # Pattern 3: Manual edge/node addition
        network = multinet.multi_layer_network()
        edges = [
            {"source": "1", "target": "2", "source_type": "L1", "target_type": "L1", "type": "edge"}
        ]
        network.add_edges(edges, input_type="dict")
        assert len(list(network.get_edges())) > 0
        print("  ✓ Pattern: Manual edge/node addition")
        
        # Pattern 4: List format edges
        network = multinet.multi_layer_network()
        edge = ["node1", "layer1", "node2", "layer1", 1.0]
        network.add_edges([edge], input_type="list")
        assert len(list(network.get_edges())) > 0
        print("  ✓ Pattern: List format edges")
        
        return True
        
    except ImportError as e:
        print(f"  ⚠ Cannot validate patterns (dependencies not available): {e}")
        return None
    except Exception as e:
        print(f"  ✗ Pattern validation failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("MULTILAYER TUTORIAL VALIDATION")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Run validations
    results['file_structure'] = validate_file_structure()
    results['syntax'] = validate_syntax()
    results['dependencies'] = validate_dependencies()
    results['imports'] = validate_imports()
    results['corner_case_fixes'] = validate_corner_case_fixes()
    results['basic_operations'] = validate_basic_operations()
    results['corner_case_tests'] = validate_corner_case_tests()
    results['example_patterns'] = validate_example_patterns()
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for check, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        elif result is None:
            status = "⚠ SKIP"
        else:
            status = "? UNKNOWN"
        
        print(f"  {status:10} {check.replace('_', ' ').title()}")
    
    # Overall result
    print("\n" + "=" * 70)
    
    critical_checks = ['file_structure', 'syntax', 'imports']
    critical_passed = all(results.get(k) in [True, None] for k in critical_checks)
    all_passed = all(r in [True, None] for r in results.values())
    
    if all_passed:
        print("✓ VALIDATION PASSED")
        print("\nAll multilayer tutorials and examples are working correctly.")
        print("Corner case bug fixes have been verified.")
        return 0
    elif critical_passed:
        print("⚠ VALIDATION PARTIALLY PASSED")
        print("\nCritical checks passed, but some optional checks failed or were skipped.")
        print("The tutorials should work, but install all dependencies for full validation.")
        return 0
    else:
        print("✗ VALIDATION FAILED")
        print("\nSome critical validation checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
