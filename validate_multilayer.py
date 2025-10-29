#!/usr/bin/env python3
"""
Validation script for multilayer modularity implementation.

This script validates that the implementation is correctly structured
and can be imported (when dependencies are available).
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validate_file_structure():
    """Validate that all required files exist."""
    print("Validating file structure...")
    
    required_files = [
        'py3plex/algorithms/community_detection/multilayer_modularity.py',
        'py3plex/algorithms/community_detection/multilayer_benchmark.py',
        'py3plex/algorithms/community_detection/__init__.py',
        'tests/test_multilayer_modularity.py',
        # 'docs/multilayer_modularity_tutorial.md',  # Moved to LLM.md
        'examples/multilayer/example_multilayer_modularity.py',
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
    """Validate Python syntax of implementation files."""
    print("\nValidating Python syntax...")
    
    import py_compile
    
    files_to_check = [
        'py3plex/algorithms/community_detection/multilayer_modularity.py',
        'py3plex/algorithms/community_detection/multilayer_benchmark.py',
        'tests/test_multilayer_modularity.py',
        'examples/multilayer/example_multilayer_modularity.py',
    ]
    
    all_valid = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for file_path in files_to_check:
        full_path = os.path.join(base_dir, file_path)
        try:
            py_compile.compile(full_path, doraise=True)
            print(f"  ✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file_path}: {e}")
            all_valid = False
    
    return all_valid


def validate_imports():
    """Validate that modules can be imported (if dependencies available)."""
    print("\nValidating imports...")
    
    try:
        # Try importing core dependencies
        import numpy
        import scipy
        import networkx
        deps_available = True
        print("  ✓ Core dependencies available (numpy, scipy, networkx)")
    except ImportError as e:
        deps_available = False
        print(f"  ⚠ Core dependencies not available: {e}")
        print("    Skipping import tests")
        return None
    
    if not deps_available:
        return None
    
    # Try importing implementation
    try:
        from py3plex.algorithms.community_detection.multilayer_modularity import (
            multilayer_modularity,
            build_supra_modularity_matrix,
            louvain_multilayer,
        )
        print("  ✓ multilayer_modularity module imports successfully")
        
        from py3plex.algorithms.community_detection.multilayer_benchmark import (
            generate_multilayer_lfr,
            generate_coupled_er_multilayer,
            generate_sbm_multilayer,
        )
        print("  ✓ multilayer_benchmark module imports successfully")
        
        # Check that functions are callable
        assert callable(multilayer_modularity)
        assert callable(build_supra_modularity_matrix)
        assert callable(louvain_multilayer)
        assert callable(generate_multilayer_lfr)
        assert callable(generate_coupled_er_multilayer)
        assert callable(generate_sbm_multilayer)
        print("  ✓ All functions are callable")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ Functions not callable: {e}")
        return False


def validate_function_signatures():
    """Validate that functions have expected signatures."""
    print("\nValidating function signatures...")
    
    try:
        import inspect
        from py3plex.algorithms.community_detection.multilayer_modularity import (
            multilayer_modularity,
            build_supra_modularity_matrix,
            louvain_multilayer,
        )
        
        # Check multilayer_modularity signature
        sig = inspect.signature(multilayer_modularity)
        expected_params = ['network', 'communities', 'gamma', 'omega', 'weight']
        actual_params = list(sig.parameters.keys())
        
        if all(p in actual_params for p in expected_params):
            print(f"  ✓ multilayer_modularity has expected parameters")
        else:
            print(f"  ✗ multilayer_modularity missing parameters")
            print(f"    Expected: {expected_params}")
            print(f"    Got: {actual_params}")
            return False
        
        # Check louvain_multilayer signature
        sig = inspect.signature(louvain_multilayer)
        expected_params = ['network', 'gamma', 'omega', 'weight', 'max_iter', 'random_state']
        actual_params = list(sig.parameters.keys())
        
        if all(p in actual_params for p in expected_params):
            print(f"  ✓ louvain_multilayer has expected parameters")
        else:
            print(f"  ✗ louvain_multilayer missing parameters")
            return False
        
        return True
        
    except ImportError:
        print("  ⚠ Cannot validate signatures (dependencies not available)")
        return None


def validate_documentation():
    """Validate that documentation exists and has content."""
    print("\nValidating documentation...")
    
    doc_files = [
        # ('docs/multilayer_modularity_tutorial.md', 5000),  # Moved to LLM.md
        ('examples/multilayer/example_multilayer_modularity.py', 5000),
    ]
    
    all_valid = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for doc_file, min_size in doc_files:
        full_path = os.path.join(base_dir, doc_file)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            if size >= min_size:
                print(f"  ✓ {doc_file} ({size} bytes)")
            else:
                print(f"  ⚠ {doc_file} may be incomplete ({size} bytes, expected >{min_size})")
                all_valid = False
        else:
            print(f"  ✗ {doc_file} not found")
            all_valid = False
    
    return all_valid


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("MULTILAYER MODULARITY IMPLEMENTATION VALIDATION")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Run validations
    results['file_structure'] = validate_file_structure()
    results['syntax'] = validate_syntax()
    results['imports'] = validate_imports()
    results['signatures'] = validate_function_signatures()
    results['documentation'] = validate_documentation()
    
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
    
    if all(r in [True, None] for r in results.values()):
        print("✓ VALIDATION PASSED")
        print("\nThe multilayer modularity implementation is correctly structured.")
        print("Install numpy, scipy, and networkx to run the full implementation.")
        return 0
    else:
        print("✗ VALIDATION FAILED")
        print("\nSome validation checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
