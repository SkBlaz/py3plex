#!/usr/bin/env python3
"""
Documentation Quality Checker

This script checks documentation source files for common issues that can
cause PDF generation artifacts or inconsistencies.

Exit codes:
    0: All checks passed
    1: One or more checks failed
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Define forbidden patterns that should not appear in documentation sources
FORBIDDEN_PATTERNS = {
    # Unicode artifacts that can appear in PDFs
    '\ufffe': 'U+FFFE (zero-width no-break space)',
    '\u00ad': 'U+00AD (soft hyphen)',
    '￾': 'U+FFFE variant (appears as ￾ in PDFs)',
    '˓→': 'Sphinx line continuation marker',
    '␣': 'Visible space character (U+2423)',
    
    # Page flow artifacts that shouldn't be in sources
    '(continues on next page)': 'Page continuation marker',
    '(continued from previous page)': 'Page continuation marker',
}

# Docker command consistency checks  
# Match docker-compose as a command (not as part of filename, in badges, or in prose)
# Exclude: docker-compose.yml, badges, "docker-compose configurations", "docker-compose development stack"
DOCKER_COMPOSE_HYPHEN_CMD = re.compile(
    r'(?<![a-zA-Z0-9._/-])docker-compose(?!\.(yml|yaml|prod\.yml|gpu\.yml))(?!\s+(configurations?|development|variant|stack|command))'
)
DOCKER_COMPOSE_SPACE = re.compile(r'\bdocker compose\b')


def check_forbidden_patterns(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Check for forbidden patterns in a file.
    
    Returns:
        List of (line_number, pattern, description) tuples
    """
    issues = []
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in FORBIDDEN_PATTERNS.items():
                if pattern in line:
                    issues.append((line_num, pattern, description))
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    return issues


def check_docker_consistency(file_path: Path) -> Tuple[int, int, List[int]]:
    """
    Check Docker command consistency.
    
    Returns:
        Tuple of (hyphenated_count, space_count, line_numbers_with_hyphen_cmd)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Count occurrences of docker compose (space version)
        space_matches = DOCKER_COMPOSE_SPACE.findall(content)
        
        # Count and track occurrences of docker-compose command (not filename)
        hyphen_lines = []
        hyphen_count = 0
        for line_num, line in enumerate(lines, 1):
            if DOCKER_COMPOSE_HYPHEN_CMD.search(line):
                hyphen_lines.append(line_num)
                hyphen_count += 1
        
        return hyphen_count, len(space_matches), hyphen_lines
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return 0, 0, []


def scan_directory(base_path: Path) -> Tuple[bool, dict]:
    """
    Scan a directory tree for documentation issues.
    
    Returns:
        Tuple of (success, results_dict)
    """
    results = {
        'forbidden_patterns': {},
        'docker_inconsistencies': {},
        'total_files': 0,
        'files_with_issues': 0,
    }
    
    # Find all RST and MD files
    patterns = ['**/*.rst', '**/*.md']
    files = []
    for pattern in patterns:
        files.extend(base_path.glob(pattern))
    
    results['total_files'] = len(files)
    
    for file_path in sorted(files):
        # Check for forbidden patterns
        forbidden_issues = check_forbidden_patterns(file_path)
        if forbidden_issues:
            results['forbidden_patterns'][file_path] = forbidden_issues
            results['files_with_issues'] += 1
        
        # Check Docker command consistency
        hyphen_count, space_count, hyphen_lines = check_docker_consistency(file_path)
        
        # Flag files with actual docker-compose command usage (not just filename)
        # Only report if we find actual command usage
        if hyphen_count > 0:
            results['docker_inconsistencies'][file_path] = {
                'hyphenated': hyphen_count,
                'space': space_count,
                'lines': hyphen_lines,
            }
            if file_path not in [f for f in results.get('forbidden_patterns', {})]:
                results['files_with_issues'] += 1
    
    # Success if no issues found
    success = (
        len(results['forbidden_patterns']) == 0 and
        len(results['docker_inconsistencies']) == 0
    )
    
    return success, results


def print_results(results: dict) -> None:
    """Print formatted results."""
    print("\n" + "="*70)
    print("Documentation Quality Check Results")
    print("="*70)
    
    print(f"\nScanned {results['total_files']} documentation files")
    print(f"Files with issues: {results['files_with_issues']}")
    
    # Print forbidden pattern issues
    if results['forbidden_patterns']:
        print("\n" + "-"*70)
        print("FORBIDDEN PATTERNS FOUND:")
        print("-"*70)
        
        for file_path, issues in sorted(results['forbidden_patterns'].items()):
            print(f"\n{file_path}:")
            for line_num, pattern, description in issues:
                print(f"  Line {line_num}: {description}")
                print(f"    Pattern: {repr(pattern)}")
    
    # Print Docker inconsistency issues
    if results['docker_inconsistencies']:
        print("\n" + "-"*70)
        print("LEGACY DOCKER-COMPOSE COMMAND USAGE:")
        print("-"*70)
        print("(Found 'docker-compose' command - should use 'docker compose')")
        
        for file_path, counts in sorted(results['docker_inconsistencies'].items()):
            print(f"\n{file_path}:")
            print(f"  'docker-compose' command: {counts['hyphenated']} occurrences")
            if counts['lines']:
                print(f"  Lines: {', '.join(map(str, counts['lines']))}")
            print(f"  'docker compose' command: {counts['space']} occurrences")
            print("  → Update to 'docker compose' (modern Docker Compose v2+ syntax)")
    
    # Summary
    print("\n" + "="*70)
    if results['files_with_issues'] == 0:
        print("✓ All checks passed!")
    else:
        print(f"✗ Found issues in {results['files_with_issues']} file(s)")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    # Get the docfiles directory
    script_dir = Path(__file__).parent
    docfiles_dir = script_dir
    
    # Also check the book directory if it exists
    book_dir = script_dir.parent / 'book'
    
    print("Checking documentation quality...")
    print(f"Docfiles: {docfiles_dir}")
    
    all_success = True
    combined_results = {
        'forbidden_patterns': {},
        'docker_inconsistencies': {},
        'total_files': 0,
        'files_with_issues': 0,
    }
    
    # Check docfiles
    if docfiles_dir.exists():
        success, results = scan_directory(docfiles_dir)
        all_success = all_success and success
        
        # Merge results
        combined_results['forbidden_patterns'].update(results['forbidden_patterns'])
        combined_results['docker_inconsistencies'].update(results['docker_inconsistencies'])
        combined_results['total_files'] += results['total_files']
        # Don't double-count files_with_issues
        if results['files_with_issues'] > 0:
            combined_results['files_with_issues'] = max(
                combined_results['files_with_issues'],
                len(set(list(results['forbidden_patterns'].keys()) + 
                       list(results['docker_inconsistencies'].keys())))
            )
    
    # Check book directory
    if book_dir.exists():
        print(f"Book: {book_dir}")
        success, results = scan_directory(book_dir)
        all_success = all_success and success
        
        # Merge results
        combined_results['forbidden_patterns'].update(results['forbidden_patterns'])
        combined_results['docker_inconsistencies'].update(results['docker_inconsistencies'])
        combined_results['total_files'] += results['total_files']
        # Recalculate total files with issues
        combined_results['files_with_issues'] = len(set(
            list(combined_results['forbidden_patterns'].keys()) + 
            list(combined_results['docker_inconsistencies'].keys())
        ))
    
    # Print combined results
    print_results(combined_results)
    
    # Exit with appropriate code
    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
