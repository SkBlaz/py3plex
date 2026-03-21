#!/usr/bin/env python3
"""
Generate documentation outputs from examples.

This script:
1. Discovers all examples in examples/getting_started/
2. Executes each example and captures stdout/stderr
3. Saves outputs to docs_outputs/ directory
4. Creates a manifest file mapping examples to outputs

Usage:
    python scripts/generate_docs_outputs.py
    python scripts/generate_docs_outputs.py --example 01_basic_query.py
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Paths
REPO_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples" / "getting_started"
OUTPUTS_DIR = REPO_ROOT / "examples" / "docs_outputs"
MANIFEST_FILE = OUTPUTS_DIR / "manifest.json"


def should_skip(example_path: Path) -> Tuple[bool, str]:
    """Check whether an example declares SKIP_CI and should be skipped.

    Args:
        example_path: Path to the example file

    Returns:
        (skip, reason) tuple
    """
    try:
        content = example_path.read_text(encoding="utf-8")
        for line in content.splitlines()[:20]:
            if "SKIP_CI" in line:
                return True, line.strip()
    except Exception:
        pass
    return False, ""


def run_example(example_path: Path, timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Run an example and capture its output.
    
    Args:
        example_path: Path to the example file
        timeout: Maximum execution time in seconds
        
    Returns:
        (success, stdout, stderr) tuple
    """
    try:
        # Set environment to disable progress bars and verbose logging
        env = {
            **subprocess.os.environ,
            'TQDM_DISABLE': '1',
            'PYTHONWARNINGS': 'ignore',
        }
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{REPO_ROOT}{subprocess.os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(REPO_ROOT)
        )
        
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT,
            env=env,
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)


def save_output(example_name: str, stdout: str, stderr: str) -> None:
    """
    Save example output to files.
    
    Args:
        example_name: Name of the example (without .py extension)
        stdout: Standard output
        stderr: Standard error
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save stdout
    output_file = OUTPUTS_DIR / f"{example_name}.txt"
    output_file.write_text(stdout, encoding='utf-8')
    
    # Save stderr if present
    if stderr:
        error_file = OUTPUTS_DIR / f"{example_name}.err"
        error_file.write_text(stderr, encoding='utf-8')


def save_skipped_output(example_name: str, reason: str) -> None:
    """Save placeholder output for a skipped example."""
    output_file = OUTPUTS_DIR / f"{example_name}.txt"
    output_file.write_text(f"SKIPPED: {reason}\n", encoding="utf-8")


def build_manifest_entry(example_name: str, has_stderr: bool, skipped: bool = False, skip_reason: str = "") -> Dict:
    """Build a manifest entry for an executed or intentionally skipped example."""
    result = {
        "success": True,
        "output_file": f"{example_name}.txt",
        "has_stderr": has_stderr,
    }
    if skipped:
        result["skipped"] = True
        result["skip_reason"] = skip_reason
    return result


def generate_manifest(results: Dict[str, Dict]) -> None:
    """
    Generate manifest file mapping examples to outputs.
    
    Args:
        results: Dictionary mapping example names to their results
    """
    # Ensure output directory exists
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "version": "1.0",
        "generated": "CI",
        "examples": results
    }
    
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding='utf-8'
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate documentation outputs from examples"
    )
    parser.add_argument(
        "--example",
        help="Run specific example (e.g., 01_basic_query.py)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per example in seconds"
    )
    args = parser.parse_args()
    
    # Discover examples
    if args.example:
        examples = [EXAMPLES_DIR / args.example]
    else:
        examples = sorted(EXAMPLES_DIR.glob("*.py"))
    
    if not examples:
        print("No examples found in", EXAMPLES_DIR)
        return 1
    
    print(f"Found {len(examples)} example(s)")
    print()
    
    # Run examples and capture outputs
    results = {}
    failed = []
    
    for example_path in examples:
        example_name = example_path.stem

        skip, skip_reason = should_skip(example_path)
        if skip:
            print(f"Skipping {example_name} ({skip_reason})")
            save_skipped_output(example_name, skip_reason)
            results[example_name] = build_manifest_entry(
                example_name,
                has_stderr=False,
                skipped=True,
                skip_reason=skip_reason,
            )
            print()
            continue

        print(f"Running {example_name}...")
        
        success, stdout, stderr = run_example(example_path, args.timeout)
        
        if success:
            print(f"  ✓ Success")
            save_output(example_name, stdout, stderr)
            results[example_name] = build_manifest_entry(
                example_name,
                has_stderr=bool(stderr),
            )
        else:
            print(f"  ✗ Failed")
            if stderr:
                print(f"    Error: {stderr[:200]}")
            failed.append(example_name)
            results[example_name] = {
                "success": False,
                "error": stderr[:500] if stderr else "Unknown error"
            }
        print()
    
    # Generate manifest
    generate_manifest(results)
    print(f"Manifest saved to {MANIFEST_FILE}")
    
    # Summary
    print()
    print("=" * 60)
    print(f"Total: {len(examples)}")
    print(f"Success: {len(examples) - len(failed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print()
        print("Failed examples:")
        for name in failed:
            print(f"  - {name}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
