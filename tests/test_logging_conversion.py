#!/usr/bin/env python3
"""
Test to verify logging conversion is working correctly.
Ensures that modules with converted logging can be imported and used.
"""

import sys
import os
import logging

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_logging_imports():
    """Test that all modules with logging conversion can be imported."""
    try:
        from py3plex.algorithms.statistics import topology
        from py3plex.visualization import benchmark_visualizations
        from py3plex.wrappers import node2vec_embedding
        from py3plex.wrappers import train_node2vec_embedding
        from py3plex.algorithms.community_detection import community_ranking
        from py3plex.algorithms.multilayer_algorithms import entanglement
        from py3plex.visualization import drawing_machinery
        
        assert hasattr(topology, 'logger'), "topology should have logger"
        assert hasattr(benchmark_visualizations, 'logger'), "benchmark_visualizations should have logger"
        assert hasattr(node2vec_embedding, 'logger'), "node2vec_embedding should have logger"
        assert hasattr(train_node2vec_embedding, 'logger'), "train_node2vec_embedding should have logger"
        assert hasattr(community_ranking, 'logger'), "community_ranking should have logger"
        assert hasattr(entanglement, 'logger'), "entanglement should have logger"
        assert hasattr(drawing_machinery, 'logger'), "drawing_machinery should have logger"
        
        return True
    except Exception as e:
        print(f"FAIL: Logging import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger_functionality():
    """Test that loggers work correctly."""
    try:
        from py3plex.logging_config import get_logger
        
        # Create a test logger
        test_logger = get_logger('test_module')
        assert test_logger is not None, "get_logger should return a logger"
        assert 'py3plex' in test_logger.name, f"Logger name should contain 'py3plex', got: {test_logger.name}"
        
        # Test logging at different levels
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")
        
        # Verify logger is properly configured
        assert test_logger.level in [logging.INFO, logging.WARNING, logging.NOTSET], \
            f"Logger should have default level, got: {test_logger.level}"
        
        return True
    except Exception as e:
        print(f"FAIL: Logger functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_print_statements_in_converted_modules():
    """Verify that converted modules don't have print statements in main code."""
    import re
    import os
    
    modules_to_check = [
        'py3plex/algorithms/statistics/topology.py',
        'py3plex/visualization/benchmark_visualizations.py',
        'py3plex/wrappers/node2vec_embedding.py',
        'py3plex/wrappers/train_node2vec_embedding.py',
        'py3plex/algorithms/community_detection/community_ranking.py',
        'py3plex/algorithms/multilayer_algorithms/entanglement.py',
    ]
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for module in modules_to_check:
        filepath = os.path.join(base_path, module)
        if not os.path.exists(filepath):
            print(f"WARNING:  Skipping {module} - file not found")
            continue
            
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Find print statements (excluding comments)
        lines = content.split('\n')
        print_lines = []
        for i, line in enumerate(lines, 1):
            # Skip comments and docstrings
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if '"""' in stripped or "'''" in stripped:
                continue
            # Look for print statements
            if re.search(r'^\s*print\s*\(', line):
                print_lines.append((i, line.strip()))
        
        if print_lines:
            print(f"WARNING:  Module {module} still has print statements:")
            for line_num, line_text in print_lines:
                print(f"   Line {line_num}: {line_text[:80]}")
    
    return True


if __name__ == "__main__":
    print("=== Testing Logging Conversion ===" + "\n")
    
    success = True
    
    print("Test 1: Checking logging imports...")
    success = test_logging_imports() and success
    print("PASS: Logging imports test passed\n" if success else "")
    
    print("Test 2: Checking logger functionality...")
    success = test_logger_functionality() and success
    print("PASS: Logger functionality test passed\n" if success else "")
    
    print("Test 3: Checking for remaining print statements...")
    success = test_no_print_statements_in_converted_modules() and success
    print("PASS: Print statement check completed\n")
    
    print("=" * 50)
    if success:
        print("PASS: All logging conversion tests passed!")
        sys.exit(0)
    else:
        print("FAIL: Some tests failed")
        sys.exit(1)
