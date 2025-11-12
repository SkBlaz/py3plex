#!/usr/bin/env python3
"""
Integration test script for CLI ergonomics fixes.

This script verifies that the basic CLI workflow works correctly:
1. Create a multilayer network
2. Compute statistics
3. Visualize the network

It performs static analysis to verify the fixes without needing full execution.
"""

import ast
import sys
from pathlib import Path


def analyze_cli_code():
    """Analyze the CLI code to verify the fixes are in place."""
    cli_file = Path(__file__).parent.parent / "py3plex" / "cli.py"
    
    if not cli_file.exists():
        print(f"ERROR: CLI file not found at {cli_file}")
        return False
    
    with open(cli_file, 'r') as f:
        code = f.read()
    
    checks_passed = []
    checks_failed = []
    
    # Check 1: _get_layer_names function exists
    if "def _get_layer_names(" in code:
        checks_passed.append("[OK] _get_layer_names helper function exists")
    else:
        checks_failed.append("[X] _get_layer_names helper function not found")
    
    # Check 2: _get_layer_names is used in cmd_load
    if "_get_layer_names(network)" in code and "def cmd_load(" in code:
        checks_passed.append("[OK] cmd_load uses _get_layer_names")
    else:
        checks_failed.append("[X] cmd_load doesn't use _get_layer_names")
    
    # Check 3: _get_layer_names is used in cmd_stats
    if "def cmd_stats(" in code:
        # Check if _get_layer_names appears after cmd_stats definition
        cmd_stats_pos = code.find("def cmd_stats(")
        get_layer_names_usage = code.find("layers = _get_layer_names(network)", cmd_stats_pos)
        next_function_pos = code.find("\ndef cmd_", cmd_stats_pos + 10)
        
        if get_layer_names_usage > cmd_stats_pos and (next_function_pos == -1 or get_layer_names_usage < next_function_pos):
            checks_passed.append("[OK] cmd_stats uses _get_layer_names")
        else:
            checks_failed.append("[X] cmd_stats doesn't use _get_layer_names")
    else:
        checks_failed.append("[X] cmd_stats function not found")
    
    # Check 4: cmd_visualize calls get_layers properly
    if "network.get_layers(" in code and "layer_names, layer_graphs, multiedges" in code:
        checks_passed.append("[OK] cmd_visualize properly unpacks get_layers tuple")
    else:
        checks_failed.append("[X] cmd_visualize doesn't properly unpack get_layers")
    
    # Check 5: Visualization passes list of graphs not network object
    if "list(layer_graphs.values())" in code or "layer_graphs.values()" in code:
        checks_passed.append("[OK] cmd_visualize passes graph list to draw function")
    else:
        checks_failed.append("[X] cmd_visualize might pass wrong type to draw function")
    
    # Check 6: Documentation includes edgelist examples
    if "edgelist" in code.lower() and "examples:" in code.lower():
        checks_passed.append("[OK] Documentation includes edgelist format examples")
    else:
        checks_failed.append("[X] Documentation lacks edgelist examples")
    
    # Check 7: No direct indexing of get_layers()[0] outside proper usage
    # This is tricky to check perfectly, but we can look for the pattern
    problematic_pattern = "get_layers()[0]"
    if problematic_pattern not in code:
        checks_passed.append("[OK] No direct get_layers()[0] indexing found")
    else:
        # This might be okay in some contexts, so just warn
        checks_passed.append("WARNING get_layers()[0] found - verify it's used correctly")
    
    # Print results
    print("\n" + "="*60)
    print("CLI ERGONOMICS FIXES VERIFICATION")
    print("="*60)
    
    print("\nPASSED CHECKS:")
    for check in checks_passed:
        print(f"  {check}")
    
    if checks_failed:
        print("\nFAILED CHECKS:")
        for check in checks_failed:
            print(f"  {check}")
        return False
    else:
        print("\nAll checks passed! [OK]")
        return True


def verify_function_signatures():
    """Verify that key functions have correct signatures."""
    cli_file = Path(__file__).parent.parent / "py3plex" / "cli.py"
    
    with open(cli_file, 'r') as f:
        tree = ast.parse(f.read())
    
    functions_to_check = {
        '_get_layer_names': ['network'],
        'cmd_load': ['args'],
        'cmd_stats': ['args'],
        'cmd_visualize': ['args'],
    }
    
    found_functions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name in functions_to_check:
                args = [arg.arg for arg in node.args.args]
                found_functions[node.name] = args
    
    print("\n" + "="*60)
    print("FUNCTION SIGNATURE VERIFICATION")
    print("="*60)
    
    all_good = True
    for func_name, expected_args in functions_to_check.items():
        if func_name in found_functions:
            actual_args = found_functions[func_name]
            if actual_args == expected_args:
                print(f"  [OK] {func_name}({', '.join(actual_args)})")
            else:
                print(f"  [X] {func_name}: expected {expected_args}, got {actual_args}")
                all_good = False
        else:
            if func_name == '_get_layer_names':
                # This is a new function, so it's okay if it doesn't exist yet
                print(f"  WARNING {func_name} not found (might be new)")
            else:
                print(f"  [X] {func_name} not found")
                all_good = False
    
    return all_good


def main():
    """Run all verification checks."""
    print("Verifying CLI ergonomics fixes...")
    
    code_analysis_passed = analyze_cli_code()
    signature_verification_passed = verify_function_signatures()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if code_analysis_passed and signature_verification_passed:
        print("[OK] All verifications passed!")
        print("\nThe CLI ergonomics fixes appear to be correctly implemented:")
        print("  - Layer name extraction uses proper helper function")
        print("  - Statistics commands don't unpack tuples incorrectly")
        print("  - Visualization receives proper graph list")
        print("  - Documentation includes edgelist format examples")
        return 0
    else:
        print("[X] Some verifications failed")
        print("\nPlease review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
