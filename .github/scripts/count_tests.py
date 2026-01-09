#!/usr/bin/env python3
"""
Count the number of test functions in the py3plex test suite.
This script counts test functions (functions starting with 'test_') using AST parsing.
"""

import ast
import json
import os
from pathlib import Path


def count_tests_in_file(filepath):
    """
    Count test functions in a single Python file.
    Returns the number of test functions (functions starting with 'test_').
    """
    test_count = 0
    
    try:
        # Use errors='ignore' to skip files with encoding issues (e.g., binary files)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            tree = ast.parse(content)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_count += 1
                
    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")
        
    return test_count


def count_tests(test_dir):
    """
    Count all test functions in the test directory.
    
    Args:
        test_dir: Root test directory to search
    
    Returns:
        Dictionary with test statistics
    """
    test_dir_path = Path(test_dir)
    
    total_test_files = 0
    total_tests = 0
    
    for filepath in test_dir_path.rglob('*.py'):
        # Skip __pycache__ and other cache directories
        if '__pycache__' in filepath.parts or '.pytest_cache' in filepath.parts:
            continue
            
        # Skip hidden files
        if any(part.startswith('.') for part in filepath.parts[len(test_dir_path.parts):]):
            continue
        
        # Only count files that look like test files
        if filepath.name.startswith('test_') or filepath.name.endswith('_test.py'):
            test_count = count_tests_in_file(filepath)
            if test_count > 0:
                total_test_files += 1
                total_tests += test_count
    
    return {
        'total_test_files': total_test_files,
        'total_tests': total_tests,
    }


def format_number(num):
    """Format number with K suffix for thousands."""
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


def main():
    """Main function to count tests and generate output."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Count test functions in py3plex')
    parser.add_argument('--test-dir', default='tests', help='Test directory to scan')
    parser.add_argument('--json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Count tests
    stats = count_tests(args.test_dir)
    
    # Print summary
    print(f"Test Count Report")
    print(f"{'='*50}")
    print(f"Total test files: {stats['total_test_files']}")
    print(f"Total tests:      {stats['total_tests']:,}")
    print(f"{'='*50}")
    print(f"Badge value:      {format_number(stats['total_tests'])}")
    
    # Add formatted values for badge generation
    stats['total_tests_formatted'] = format_number(stats['total_tests'])
    
    # Write JSON output if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\nJSON output written to: {args.json}")
    
    return stats


if __name__ == '__main__':
    main()
