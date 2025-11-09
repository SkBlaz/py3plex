#!/usr/bin/env python3
"""
Script to run py3plex example files with timeout and filtering.

This script:
1. Discovers all Python example files in the examples/ directory
2. Checks for skip markers in the file headers
3. Runs examples that are marked as fast (< 10 seconds)
4. Provides detailed reporting on success/failure/skipped examples

Examples can be marked with special comments to control execution:
  # SKIP_CI: true - Skip this example in CI entirely
  # SKIP_CI: slow - Skip because it takes > 10 seconds
  # SKIP_CI: external_deps - Skip because it requires external binaries
  # SKIP_CI: interactive - Skip because it requires user interaction
"""

import argparse
import ast
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    GRAY = '\033[90m'


# Configuration constants
MAX_ERROR_LENGTH = 500  # Maximum length of error messages to display
MAX_HEADER_LINES = 50   # Maximum number of lines to check for skip markers


def check_skip_marker(file_path: Path) -> Tuple[bool, str]:
    """
    Check if a file has a SKIP_CI marker in its header.
    
    Returns:
        (should_skip, reason) tuple
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Only check first MAX_HEADER_LINES for performance
            for i, line in enumerate(f):
                if i >= MAX_HEADER_LINES:
                    break
                
                # Check for SKIP_CI marker (can be in comments or docstrings)
                if 'SKIP_CI' in line:
                    # Extract the reason
                    if 'SKIP_CI:' in line:
                        reason = line.split('SKIP_CI:')[1].strip().strip('#').strip()
                        return True, reason
                    elif 'SKIP_CI' in line:
                        return True, "marked for skip"
                        
        return False, ""
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Could not read {file_path}: {e}{Colors.RESET}")
        return False, ""


def check_imports_external_deps(file_path: Path) -> bool:
    """
    Check if a file imports modules that require external binaries.
    
    Returns:
        True if the file likely needs external dependencies
    """
    external_indicators = [
        'imagemagick',
        'node2vec',
        'infomap',
        'animation.ArtistAnimation',
        'show=True',  # Interactive visualization
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Skip files marked as FAST standalone
            if 'Runtime: FAST' in content[:2000]:
                return False
                
            for indicator in external_indicators:
                if indicator in content:
                    return True
        return False
    except Exception:
        return False


def discover_examples(examples_dir: Path, fast_only: bool = False) -> List[Tuple[Path, str]]:
    """
    Discover all example Python files.
    
    Returns:
        List of (file_path, status) tuples where status is 'run' or 'skip:reason'
    """
    examples = []
    
    for py_file in sorted(examples_dir.rglob("*.py")):
        # Skip __init__.py files
        if py_file.name == "__init__.py":
            continue
            
        # Check for explicit skip marker
        should_skip, reason = check_skip_marker(py_file)
        
        if should_skip:
            examples.append((py_file, f"skip:{reason}"))
            continue
        
        # If fast_only mode, check for external dependencies
        if fast_only and check_imports_external_deps(py_file):
            examples.append((py_file, "skip:external_deps_or_interactive"))
            continue
            
        examples.append((py_file, "run"))
    
    return examples


def run_example(file_path: Path, timeout: int) -> Tuple[bool, float, str]:
    """
    Run a single example file with timeout.
    
    Returns:
        (success, duration, error_message) tuple
    """
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(file_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=file_path.parent
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            return True, duration, ""
        else:
            error_msg = result.stderr[-MAX_ERROR_LENGTH:] if result.stderr else "Unknown error"
            return False, duration, error_msg
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, f"Timeout after {timeout}s"
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Run py3plex example files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--fast-only",
        action="store_true",
        help="Only run fast examples (< 10 seconds, no external deps)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds for each example (default: 10)"
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("examples"),
        help="Path to examples directory (default: examples)"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the repo root
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)
    
    examples_dir = repo_root / args.examples_dir
    
    if not examples_dir.exists():
        print(f"{Colors.RED}Error: Examples directory not found: {examples_dir}{Colors.RESET}")
        sys.exit(1)
    
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Py3plex Examples CI Runner{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"Examples directory: {examples_dir}")
    print(f"Fast-only mode: {args.fast_only}")
    print(f"Timeout: {args.timeout}s per example")
    print()
    
    # Discover examples
    examples = discover_examples(examples_dir, fast_only=args.fast_only)
    
    # Separate into run vs skip
    to_run = [(f, s) for f, s in examples if s == "run"]
    to_skip = [(f, s) for f, s in examples if s.startswith("skip:")]
    
    print(f"{Colors.BOLD}Discovery Summary:{Colors.RESET}")
    print(f"  Total examples found: {len(examples)}")
    print(f"  Examples to run: {Colors.GREEN}{len(to_run)}{Colors.RESET}")
    print(f"  Examples to skip: {Colors.YELLOW}{len(to_skip)}{Colors.RESET}")
    print()
    
    # Show skipped examples
    if to_skip:
        print(f"{Colors.BOLD}Skipped Examples:{Colors.RESET}")
        for file_path, status in to_skip:
            reason = status.split(":", 1)[1] if ":" in status else "unknown"
            rel_path = file_path.relative_to(examples_dir)
            print(f"  {Colors.GRAY}⊘ {rel_path}{Colors.RESET} - {reason}")
        print()
    
    # Run examples
    if not to_run:
        print(f"{Colors.YELLOW}No examples to run!{Colors.RESET}")
        sys.exit(0)
    
    print(f"{Colors.BOLD}Running Examples:{Colors.RESET}")
    print()
    
    results = []
    for i, (file_path, _) in enumerate(to_run, 1):
        rel_path = file_path.relative_to(examples_dir)
        print(f"[{i}/{len(to_run)}] {rel_path}... ", end="", flush=True)
        
        success, duration, error = run_example(file_path, args.timeout)
        results.append((file_path, success, duration, error))
        
        if success:
            print(f"{Colors.GREEN}[OK]{Colors.RESET} ({duration:.2f}s)")
        else:
            print(f"{Colors.RED}[X]{Colors.RESET} ({duration:.2f}s)")
            if error:
                # Print first line of error
                error_line = error.split('\n')[0][:80]
                print(f"    {Colors.RED}{error_line}{Colors.RESET}")
    
    # Summary
    print()
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Results Summary:{Colors.RESET}")
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    total_time = sum(r[2] for r in results)
    
    print(f"  Total examples run: {len(results)}")
    print(f"  {Colors.GREEN}Successful: {len(successful)}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {len(failed)}{Colors.RESET}")
    print(f"  Total time: {total_time:.2f}s")
    
    if failed:
        print()
        print(f"{Colors.BOLD}{Colors.RED}Failed Examples:{Colors.RESET}")
        for file_path, _, duration, error in failed:
            rel_path = file_path.relative_to(examples_dir)
            print(f"  [X] {rel_path} ({duration:.2f}s)")
            if error:
                print(f"    {Colors.GRAY}{error[:MAX_ERROR_LENGTH]}{Colors.RESET}")
    
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    
    # Exit with error code if any failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
