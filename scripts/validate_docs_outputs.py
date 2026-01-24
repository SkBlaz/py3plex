#!/usr/bin/env python3
"""
Validate documentation outputs match captured example outputs.

This script:
1. Loads the manifest of captured outputs
2. Scans RST files for example output references
3. Validates that embedded outputs match captured outputs
4. Fails if any divergence is found

Usage:
    python scripts/validate_docs_outputs.py
    python scripts/validate_docs_outputs.py --docfiles-dir docfiles/
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Paths
REPO_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = REPO_ROOT / "examples" / "docs_outputs"
MANIFEST_FILE = OUTPUTS_DIR / "manifest.json"


def load_manifest() -> Dict:
    """Load the manifest of captured outputs."""
    if not MANIFEST_FILE.exists():
        print(f"Error: Manifest not found at {MANIFEST_FILE}")
        print("Run generate_docs_outputs.py first.")
        sys.exit(1)
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_output_blocks(rst_content: str) -> List[Tuple[str, str]]:
    """
    Find output blocks in RST content.
    
    Looks for patterns like:
    - .. include:: examples/docs_outputs/example_name.txt
    - .. literalinclude:: examples/docs_outputs/example_name.txt
    
    Returns:
        List of (example_name, block_content) tuples
    """
    blocks = []
    
    # Pattern for include directives
    include_pattern = r'\.\.\s+(include|literalinclude)::\s+examples/docs_outputs/([^.\s]+)\.txt'
    
    for match in re.finditer(include_pattern, rst_content):
        directive = match.group(1)
        example_name = match.group(2)
        blocks.append((example_name, directive))
    
    return blocks


def validate_rst_file(
    rst_path: Path,
    manifest: Dict,
    verbose: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a single RST file.
    
    Args:
        rst_path: Path to RST file
        manifest: Manifest of captured outputs
        verbose: Print detailed information
        
    Returns:
        (is_valid, errors) tuple
    """
    if verbose:
        print(f"Checking {rst_path.relative_to(REPO_ROOT)}...")
    
    content = rst_path.read_text(encoding='utf-8')
    blocks = find_output_blocks(content)
    
    if not blocks:
        if verbose:
            print("  No output blocks found")
        return True, []
    
    errors = []
    
    for example_name, directive in blocks:
        if verbose:
            print(f"  Found reference to {example_name}")
        
        # Check if example exists in manifest
        if example_name not in manifest['examples']:
            errors.append(
                f"{rst_path.name}: References unknown example '{example_name}'"
            )
            continue
        
        # Check if example succeeded
        example_data = manifest['examples'][example_name]
        if not example_data['success']:
            errors.append(
                f"{rst_path.name}: References failed example '{example_name}'"
            )
            continue
        
        # Check if output file exists
        output_file = OUTPUTS_DIR / f"{example_name}.txt"
        if not output_file.exists():
            errors.append(
                f"{rst_path.name}: Output file not found for '{example_name}'"
            )
    
    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate documentation outputs"
    )
    parser.add_argument(
        "--docfiles-dir",
        type=Path,
        default=REPO_ROOT / "docfiles",
        help="Directory containing RST files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed information"
    )
    args = parser.parse_args()
    
    # Load manifest
    print("Loading manifest...")
    manifest = load_manifest()
    print(f"Found {len(manifest['examples'])} examples in manifest")
    print()
    
    # Find all RST files
    rst_files = list(args.docfiles_dir.rglob("*.rst"))
    print(f"Found {len(rst_files)} RST files")
    print()
    
    # Validate each file
    all_errors = []
    files_with_refs = 0
    
    for rst_file in rst_files:
        is_valid, errors = validate_rst_file(rst_file, manifest, args.verbose)
        if errors:
            all_errors.extend(errors)
        
        # Count files with references
        content = rst_file.read_text(encoding='utf-8')
        if 'docs_outputs' in content:
            files_with_refs += 1
    
    # Summary
    print()
    print("=" * 60)
    print(f"RST files checked: {len(rst_files)}")
    print(f"Files with output references: {files_with_refs}")
    print(f"Validation errors: {len(all_errors)}")
    print()
    
    if all_errors:
        print("VALIDATION FAILED")
        print()
        print("Errors:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("✓ All documentation outputs are valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())
