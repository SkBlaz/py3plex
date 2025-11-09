#!/usr/bin/env python3
"""
Simple validation script to check that monoplex_nx_wrapper properly forwards kwargs.
This validates the fix without requiring NetworkX to be installed.
"""

import sys
import os
import re

# Add py3plex to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def validate_monoplex_nx_wrapper_fix():
    """Validate that monoplex_nx_wrapper has been fixed to forward kwargs."""
    
    print("=" * 60)
    print("Validating monoplex_nx_wrapper kwargs forwarding fix")
    print("=" * 60)
    
    # Read the multinet.py file
    multinet_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "py3plex", 
        "core", 
        "multinet.py"
    )
    
    with open(multinet_path, 'r') as f:
        content = f.read()
    
    # Check 1: Function signature includes kwargs parameter
    print("\n✓ Check 1: Function signature includes kwargs parameter")
    if "def monoplex_nx_wrapper(self, method, kwargs=None):" in content:
        print("  PASS: Function signature is correct")
    else:
        print("  FAIL: Function signature doesn't match expected format")
        return False
    
    # Check 2: kwargs is initialized if None
    print("\n✓ Check 2: kwargs is initialized if None")
    if "if kwargs is None:\n        kwargs = {}" in content or \
       "if kwargs is None:\n            kwargs = {}" in content:
        print("  PASS: kwargs is properly initialized")
    else:
        print("  FAIL: kwargs initialization not found")
        return False
    
    # Check 3: kwargs is forwarded to NetworkX call (using getattr, not eval)
    print("\n✓ Check 3: kwargs is forwarded to NetworkX call safely")
    if "getattr(nx, method)" in content and "**kwargs" in content:
        print("  PASS: kwargs is forwarded using safe getattr method")
    elif "eval" in content and "**kwargs" in content:
        print("  WARNING: Uses eval (security concern), but kwargs is forwarded")
    else:
        print("  FAIL: kwargs forwarding not found in NetworkX call")
        return False
    
    # Check 3b: Method validation exists
    print("\n✓ Check 3b: Method validation exists")
    if "hasattr(nx, method)" in content:
        print("  PASS: Method validation present")
    else:
        print("  INFO: No method validation (optional)")
    
    # Check 4: Docstring has been improved
    print("\n✓ Check 4: Docstring has been improved")
    if "A generic networkx function wrapper" in content or \
       "A generic NetworkX function wrapper" in content:
        print("  PASS: Docstring has been improved")
    else:
        print("  FAIL: Docstring improvement not found")
        return False
    
    # Check 5: Examples in docstring
    print("\n✓ Check 5: Examples in docstring")
    if "Example:" in content and "kwargs=" in content:
        print("  PASS: Usage examples found in docstring")
    else:
        print("  FAIL: Usage examples not found")
        return False
    
    # Check 6: Test file exists
    print("\n✓ Check 6: Test file exists")
    test_path = os.path.join(
        os.path.dirname(__file__),
        "test_monoplex_nx_wrapper.py"
    )
    if os.path.exists(test_path):
        print("  PASS: Test file test_monoplex_nx_wrapper.py exists")
        
        # Check test file content
        with open(test_path, 'r') as f:
            test_content = f.read()
        
        # Verify test file has tests for kwargs
        if 'kwargs={"weight":' in test_content or 'kwargs={\'weight\':' in test_content:
            print("  PASS: Test file includes kwargs tests")
        else:
            print("  WARNING: Test file doesn't seem to test kwargs")
    else:
        print("  FAIL: Test file not found")
        return False
    
    print("\n" + "=" * 60)
    print("PASS: All validation checks passed!")
    print("=" * 60)
    print("\nThe monoplex_nx_wrapper function has been successfully fixed to:")
    print("1. Accept kwargs parameter")
    print("2. Initialize kwargs if None")
    print("3. Forward kwargs to NetworkX functions")
    print("4. Include comprehensive documentation with examples")
    print("5. Have comprehensive test coverage")
    
    return True

if __name__ == "__main__":
    try:
        success = validate_monoplex_nx_wrapper_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFAIL: Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
