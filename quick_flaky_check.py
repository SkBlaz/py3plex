#!/usr/bin/env python
"""
Quick Flaky Test Check - Runs a small subset of tests multiple times.

Usage:
    python quick_flaky_check.py
"""

import subprocess
import sys
import json
from collections import defaultdict

def run_quick_test():
    """Run a small subset of tests to demonstrate flaky detection."""
    print("🔍 Running quick flaky test check on a small test subset...")
    print("   This will run a subset of tests 3 times to demonstrate the concept.")
    
    # Pick a few fast tests to check
    test_files = [
        "tests/test_core_immutable.py",
        "tests/test_parallel.py",
        "tests/test_algebra_core.py",
    ]
    
    results = defaultdict(list)
    
    for run in range(3):
        print(f"\n--- Run {run + 1}/3 ---")
        for test_file in test_files:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_file, "-v", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Count passed/failed
                passed = result.stdout.count("PASSED")
                failed = result.stdout.count("FAILED")
                
                results[test_file].append({
                    "run": run + 1,
                    "passed": passed,
                    "failed": failed,
                    "returncode": result.returncode
                })
                
                print(f"  {test_file}: {passed} passed, {failed} failed")
                
            except Exception as e:
                print(f"  {test_file}: ERROR - {e}")
                results[test_file].append({
                    "run": run + 1,
                    "error": str(e)
                })
    
    # Analyze results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    flaky_found = False
    for test_file, runs in results.items():
        # Check if results are inconsistent
        returncodes = [r.get("returncode", -1) for r in runs]
        if len(set(returncodes)) > 1:
            print(f"\n⚠️  POTENTIALLY FLAKY: {test_file}")
            print(f"   Return codes across runs: {returncodes}")
            flaky_found = True
        else:
            print(f"\n✅ STABLE: {test_file}")
            print(f"   Consistent return code: {returncodes[0]}")
    
    if flaky_found:
        print("\n⚠️  Some tests showed inconsistent behavior.")
        print("Run the full detection script for comprehensive analysis:")
        print("   python detect_flaky_tests.py --runs 5")
    else:
        print("\n✅ All tested files showed consistent behavior.")
    
    return 0 if not flaky_found else 1

if __name__ == "__main__":
    sys.exit(run_quick_test())
