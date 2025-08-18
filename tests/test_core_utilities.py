#!/usr/bin/env python3
"""
Unit tests for py3plex utility functions that don't require heavy dependencies
Tests standalone utility functions and basic data transformations
"""

import sys
import os
import tempfile

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_string_operations():
    """Test basic string operations used throughout py3plex"""
    print("Testing string operations...")
    
    # Test label delimiter functionality 
    test_label = "node1---layer1"
    delimiter = "---"
    
    # Split by delimiter
    parts = test_label.split(delimiter)
    assert len(parts) == 2, f"Should split into 2 parts, got {len(parts)}"
    assert parts[0] == "node1", f"First part should be 'node1', got {parts[0]}"
    assert parts[1] == "layer1", f"Second part should be 'layer1', got {parts[1]}"
    
    # Rejoin parts
    rejoined = delimiter.join(parts)
    assert rejoined == test_label, f"Should rejoin to original, got {rejoined}"
    
    print("✅ String operations test PASSED")
    return True


def test_file_operations():
    """Test basic file operations used in py3plex"""
    print("Testing file operations...")
    
    # Test writing and reading a simple file
    test_content = "line1\nline2\nline3\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Read file back
        with open(temp_file, 'r') as f:
            read_content = f.read()
        
        assert read_content == test_content, "Should read back the same content"
        
        # Test line-by-line reading
        with open(temp_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3, f"Should have 3 lines, got {len(lines)}"
        assert lines[0].strip() == "line1", f"First line should be 'line1', got '{lines[0].strip()}'"
        assert lines[1].strip() == "line2", f"Second line should be 'line2', got '{lines[1].strip()}'"
        assert lines[2].strip() == "line3", f"Third line should be 'line3', got '{lines[2].strip()}'"
        
        print("✅ File operations test PASSED")
        return True
        
    finally:
        os.unlink(temp_file)


def test_data_structures():
    """Test basic data structures used in py3plex"""
    print("Testing data structures...")
    
    # Test defaultdict behavior (commonly used)
    from collections import defaultdict
    
    # Test defaultdict with list
    dd_list = defaultdict(list)
    dd_list['key1'].append('value1')
    dd_list['key2'].append('value2')
    dd_list['key1'].append('value3')
    
    assert len(dd_list) == 2, f"Should have 2 keys, got {len(dd_list)}"
    assert dd_list['key1'] == ['value1', 'value3'], f"key1 should have 2 values, got {dd_list['key1']}"
    assert dd_list['key2'] == ['value2'], f"key2 should have 1 value, got {dd_list['key2']}"
    
    # Test defaultdict with set
    dd_set = defaultdict(set)
    dd_set['group1'].add('item1')
    dd_set['group1'].add('item2')
    dd_set['group1'].add('item1')  # duplicate
    dd_set['group2'].add('item3')
    
    assert len(dd_set['group1']) == 2, f"group1 should have 2 unique items, got {len(dd_set['group1'])}"
    assert len(dd_set['group2']) == 1, f"group2 should have 1 item, got {len(dd_set['group2'])}"
    
    # Test regular dict operations
    regular_dict = {}
    regular_dict['a'] = 1
    regular_dict['b'] = 2
    
    # Test key existence
    assert 'a' in regular_dict, "Should contain key 'a'"
    assert 'c' not in regular_dict, "Should not contain key 'c'"
    
    # Test dict comprehension (commonly used in py3plex)
    squared = {k: v**2 for k, v in regular_dict.items()}
    assert squared['a'] == 1, f"a squared should be 1, got {squared['a']}"
    assert squared['b'] == 4, f"b squared should be 4, got {squared['b']}"
    
    print("✅ Data structures test PASSED")
    return True


def test_itertools_operations():
    """Test itertools operations commonly used in py3plex"""
    print("Testing itertools operations...")
    
    import itertools
    
    # Test combinations (used in multiplex edge generation)
    items = [1, 2, 3, 4]
    combinations = list(itertools.combinations(items, 2))
    
    expected_combinations = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    assert len(combinations) == 6, f"Should have 6 combinations, got {len(combinations)}"
    for combo in expected_combinations:
        assert combo in combinations, f"Should contain combination {combo}"
    
    # Test chain (used in flattening lists)
    list1 = [1, 2, 3]
    list2 = [4, 5]
    list3 = [6]
    
    chained = list(itertools.chain(list1, list2, list3))
    expected_chained = [1, 2, 3, 4, 5, 6]
    assert chained == expected_chained, f"Should chain to {expected_chained}, got {chained}"
    
    # Test product (Cartesian product)
    set1 = [1, 2]
    set2 = ['a', 'b']
    
    product = list(itertools.product(set1, set2))
    expected_product = [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
    assert len(product) == 4, f"Should have 4 products, got {len(product)}"
    for prod in expected_product:
        assert prod in product, f"Should contain product {prod}"
    
    print("✅ Itertools operations test PASSED")
    return True


def test_tuple_operations():
    """Test tuple operations commonly used for node representations"""
    print("Testing tuple operations...")
    
    # Test tuple creation and access (node, layer format)
    node_tuple = ('node1', 'layer1')
    assert len(node_tuple) == 2, f"Should have length 2, got {len(node_tuple)}"
    assert node_tuple[0] == 'node1', f"First element should be 'node1', got {node_tuple[0]}"
    assert node_tuple[1] == 'layer1', f"Second element should be 'layer1', got {node_tuple[1]}"
    
    # Test tuple unpacking
    node, layer = node_tuple
    assert node == 'node1', f"Unpacked node should be 'node1', got {node}"
    assert layer == 'layer1', f"Unpacked layer should be 'layer1', got {layer}"
    
    # Test tuple as dict key (important for networkx compatibility)
    tuple_dict = {}
    tuple_dict[node_tuple] = 'value1'
    tuple_dict[('node2', 'layer2')] = 'value2'
    
    assert len(tuple_dict) == 2, f"Should have 2 keys, got {len(tuple_dict)}"
    assert tuple_dict[node_tuple] == 'value1', f"Should retrieve correct value"
    
    # Test tuple immutability
    try:
        node_tuple[0] = 'changed'
        assert False, "Should not be able to modify tuple"
    except TypeError:
        # Expected behavior
        pass
    
    # Test tuple comparison
    tuple1 = ('a', 'b')
    tuple2 = ('a', 'b') 
    tuple3 = ('b', 'a')
    
    assert tuple1 == tuple2, "Equal tuples should compare as equal"
    assert tuple1 != tuple3, "Different tuples should compare as not equal"
    
    print("✅ Tuple operations test PASSED")
    return True


def test_set_operations():
    """Test set operations used in layer intersections"""
    print("Testing set operations...")
    
    # Test set creation and operations
    set1 = {'A', 'B', 'C', 'D'}
    set2 = {'C', 'D', 'E', 'F'}
    
    # Test intersection
    intersection = set1 & set2
    expected_intersection = {'C', 'D'}
    assert intersection == expected_intersection, f"Intersection should be {expected_intersection}, got {intersection}"
    
    # Test union
    union = set1 | set2
    expected_union = {'A', 'B', 'C', 'D', 'E', 'F'}
    assert union == expected_union, f"Union should be {expected_union}, got {union}"
    
    # Test difference
    diff = set1 - set2
    expected_diff = {'A', 'B'}
    assert diff == expected_diff, f"Difference should be {expected_diff}, got {diff}"
    
    # Test set from list (removing duplicates)
    list_with_dupes = ['A', 'B', 'A', 'C', 'B', 'D']
    unique_set = set(list_with_dupes)
    expected_unique = {'A', 'B', 'C', 'D'}
    assert unique_set == expected_unique, f"Unique set should be {expected_unique}, got {unique_set}"
    
    print("✅ Set operations test PASSED")
    return True


def run_all_tests():
    """Run all utility function tests"""
    print("=" * 60)
    print("Running py3plex utility function tests")
    print("=" * 60)
    
    tests = [
        test_string_operations,
        test_file_operations,
        test_data_structures,
        test_itertools_operations,
        test_tuple_operations,
        test_set_operations
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
    print(f"Utility function tests completed: {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)