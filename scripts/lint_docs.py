#!/usr/bin/env python3
"""
Lint documentation sources for common formatting issues and artifacts.

This script checks for:
- Encoding/hyphenation artifacts (￾, ˓→, ␣)
- Page continuation markers
- Docker command inconsistency (stricter check)
- Version inconsistencies

Exit code 0 if all checks pass, 1 if issues found.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Define forbidden patterns
FORBIDDEN_PATTERNS = [
    (r'￾', 'Soft-hyphen artifact (U+FFFE)'),
    (r'˓→', 'Continuation marker glyph'),
    (r'␣', 'Space glyph artifact'),
    (r'continued from previous page', 'Page continuation marker'),
    (r'continues on next page', 'Page continuation marker'),
]

# Patterns for standalone docker-compose commands (not filename references)
DOCKER_COMPOSE_COMMAND_PATTERN = r'^\s*(#\s*)?docker-compose\s+(up|down|build|logs|run|ps|exec|restart|stop|start)'

# Patterns that should be consistent
VERSION_PATTERN = r'py3plex==(\d+\.\d+\.\d+)'

def check_file(filepath: Path) -> List[Tuple[int, str, str]]:
    """
    Check a single file for forbidden patterns.
    
    Returns list of (line_number, pattern_description, line_content) tuples.
    """
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                # Check forbidden patterns
                for pattern, description in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line):
                        issues.append((line_num, description, line.strip()))
                
                # Check for docker-compose commands (not filename references)
                if re.search(DOCKER_COMPOSE_COMMAND_PATTERN, line):
                    issues.append((line_num, 'Legacy docker-compose command (use "docker compose")', line.strip()))
        
    except UnicodeDecodeError:
        issues.append((0, 'File encoding error', str(filepath)))
    
    return issues

def check_version_consistency(doc_paths: List[Path]) -> List[Tuple[str, int, str]]:
    """
    Check for version inconsistencies across documentation.
    
    Returns list of (filepath, line_number, version) tuples.
    """
    versions_found = []
    
    for filepath in doc_paths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    match = re.search(VERSION_PATTERN, line)
                    if match:
                        version = match.group(1)
                        versions_found.append((str(filepath), line_num, version))
        except Exception:
            pass
    
    return versions_found

def main():
    """Main linting function."""
    # Find repository root
    repo_root = Path(__file__).parent.parent
    
    # Check book/ and docfiles/ directories
    doc_dirs = [repo_root / 'book', repo_root / 'docfiles']
    
    all_issues = []
    all_rst_files = []
    
    for doc_dir in doc_dirs:
        if not doc_dir.exists():
            continue
        
        rst_files = list(doc_dir.rglob('*.rst'))
        all_rst_files.extend(rst_files)
        
        for rst_file in rst_files:
            issues = check_file(rst_file)
            if issues:
                all_issues.append((rst_file, issues))
    
    # Report issues
    if all_issues:
        print("❌ Documentation linting found issues:\n")
        for filepath, issues in all_issues:
            print(f"\n📄 {filepath.relative_to(repo_root)}:")
            for line_num, description, line_content in issues:
                if line_num > 0:
                    print(f"  Line {line_num}: {description}")
                    print(f"    → {line_content[:100]}")
                else:
                    print(f"  {description}")
        
        return 1
    
    # Check version consistency
    versions = check_version_consistency(all_rst_files)
    if versions:
        unique_versions = set(v[2] for v in versions)
        if len(unique_versions) > 1:
            print(f"\n⚠️  Warning: Found multiple py3plex versions in examples:")
            for version in sorted(unique_versions):
                print(f"  - py3plex=={version}")
                matching = [v for v in versions if v[2] == version]
                for filepath, line_num, _ in matching[:3]:  # Show first 3 occurrences
                    print(f"    {Path(filepath).relative_to(repo_root)}:{line_num}")
            print("\nNote: Examples should use the current release version.")
            return 0  # Warning only, not a hard failure
    
    print("✅ Documentation linting passed!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
