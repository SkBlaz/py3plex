#!/usr/bin/env python3
"""
CrossHair testing script for py3plex pure functions.

This script can be used to test the pure/deterministic functions
identified in CROSSHAIR_FUNCTIONS.md with CrossHair symbolic testing.

Usage:
    python crosshair_test.py --list              # List all testable functions
    python crosshair_test.py --test <module>     # Test specific module
    python crosshair_test.py --test-all          # Test all identified functions
"""

import argparse
import subprocess
import sys
from typing import List, Tuple


# Functions suitable for CrossHair testing (from CROSSHAIR_FUNCTIONS.md)
TESTABLE_FUNCTIONS = [
    # Algorithms/Statistics
    "py3plex.algorithms.statistics.basic_statistics:identify_n_hubs",
    "py3plex.algorithms.statistics.basic_statistics:core_network_statistics",
    "py3plex.algorithms.statistics.topology:basic_pl_stats",
    "py3plex.algorithms.statistics.stats_comparison:bootstrap_confidence_interval",
    "py3plex.algorithms.statistics.critical_distances:center",
    "py3plex.algorithms.statistics.critical_distances:name_length",
    "py3plex.algorithms.statistics.critical_distances:remove_backslash",
    
    # Core/Converters
    "py3plex.core.converters:compute_layout",
    
    # Core/Supporting
    "py3plex.core.supporting:split_to_layers",
    "py3plex.core.supporting:add_mpx_edges",
    
    # Core/Parsers (note: some involve I/O)
    "py3plex.core.parsers:parse_gml",
    "py3plex.core.parsers:parse_gpickle_biomine",
    "py3plex.core.parsers:parse_matrix",
    "py3plex.core.parsers:parse_matrix_to_nx",
    "py3plex.core.parsers:parse_multiedge_tuple_list",
    "py3plex.core.parsers:parse_network",
    "py3plex.core.parsers:parse_nx",
    "py3plex.core.parsers:save_gpickle",
    "py3plex.core.parsers:load_temporal_edge_information",
    
    # Core/Random Generators
    "py3plex.core.random_generators:random_multilayer_ER",
    "py3plex.core.random_generators:random_multiplex_ER",
    "py3plex.core.random_generators:random_multiplex_generator",
    
    # Utils
    "py3plex.utils:get_rng",
    "py3plex.utils:deprecated",
    "py3plex.utils:warn_if_deprecated",
    
    # Visualization
    "py3plex.visualization.layout_algorithms:compute_random_layout",
]


def group_by_module(functions: List[str]) -> dict:
    """Group functions by their module."""
    modules = {}
    for func in functions:
        module = func.split(":")[0]
        if module not in modules:
            modules[module] = []
        modules[module].append(func)
    return modules


def list_functions():
    """List all testable functions grouped by module."""
    modules = group_by_module(TESTABLE_FUNCTIONS)
    
    print("\n=== CrossHair Testable Functions ===\n")
    for module, funcs in sorted(modules.items()):
        print(f"{module}:")
        for func in funcs:
            func_name = func.split(":")[1]
            print(f"  - {func_name}")
        print()
    
    print(f"Total: {len(TESTABLE_FUNCTIONS)} functions in {len(modules)} modules\n")


def run_crosshair_check(target: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    Run CrossHair check on a target function or module.
    
    Args:
        target: Module or function to test (e.g., 'py3plex.utils' or 'py3plex.utils:get_rng')
        timeout: Timeout per condition in seconds
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    cmd = [
        "crosshair",
        "check",
        "--per_condition_timeout", str(timeout),
        target
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout * 10  # Overall timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Timeout expired for {target}"
    except FileNotFoundError:
        return False, "CrossHair not found. Install with: pip install crosshair-tool"
    except Exception as e:
        return False, f"Error running CrossHair: {e}"


def test_module(module: str, timeout: int = 5):
    """Test all functions in a specific module."""
    functions = [f for f in TESTABLE_FUNCTIONS if f.startswith(module)]
    
    if not functions:
        print(f"No testable functions found in {module}")
        return
    
    print(f"\n=== Testing {module} ===")
    print(f"Functions: {len(functions)}\n")
    
    success_count = 0
    for func in functions:
        func_name = func.split(":")[1]
        print(f"Testing {func_name}...", end=" ")
        success, output = run_crosshair_check(func, timeout)
        
        if success:
            print("✓ PASSED")
            success_count += 1
        else:
            print("✗ FAILED")
            if output:
                print(f"  {output[:200]}...")
    
    print(f"\nResults: {success_count}/{len(functions)} passed\n")


def test_all(timeout: int = 5):
    """Test all identified functions."""
    modules = group_by_module(TESTABLE_FUNCTIONS)
    
    print(f"\n=== Testing All Modules ===")
    print(f"Modules: {len(modules)}, Functions: {len(TESTABLE_FUNCTIONS)}\n")
    
    total_success = 0
    for module in sorted(modules.keys()):
        functions = modules[module]
        module_success = 0
        
        for func in functions:
            success, _ = run_crosshair_check(func, timeout)
            if success:
                module_success += 1
                total_success += 1
        
        status = "✓" if module_success == len(functions) else "✗"
        print(f"{status} {module}: {module_success}/{len(functions)}")
    
    print(f"\n=== Overall Results ===")
    print(f"Total: {total_success}/{len(TESTABLE_FUNCTIONS)} passed\n")


def main():
    parser = argparse.ArgumentParser(
        description="CrossHair testing for py3plex pure functions"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all testable functions"
    )
    parser.add_argument(
        "--test",
        metavar="MODULE",
        help="Test specific module (e.g., py3plex.utils)"
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Test all identified functions"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout per condition in seconds (default: 5)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_functions()
    elif args.test:
        test_module(args.test, args.timeout)
    elif args.test_all:
        test_all(args.timeout)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
