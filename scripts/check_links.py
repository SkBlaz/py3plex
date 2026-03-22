#!/usr/bin/env python3
"""
Link checker for py3plex repository.
Validates all HTTP/HTTPS links in markdown files and RST files.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse
import subprocess


def find_markdown_files(root: Path) -> List[Path]:
    """Find all markdown files in the repository."""
    return list(root.rglob("*.md"))


def find_rst_files(root: Path) -> List[Path]:
    """Find all RST files in the repository."""
    return list(root.rglob("*.rst"))


def extract_links_from_markdown(file_path: Path) -> List[Tuple[str, int]]:
    """Extract all HTTP/HTTPS links from a markdown file."""
    links = []
    try:
        content = file_path.read_text(encoding='utf-8')
        # Match markdown links: [text](url)
        md_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
        # Match bare URLs
        bare_links = re.findall(r'https?://[^\s<>"]+', content)
        
        # Get line numbers for better reporting
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for match in re.finditer(r'https?://[^\s<>"]+', line):
                links.append((match.group(), i))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return links


def extract_links_from_rst(file_path: Path) -> List[Tuple[str, int]]:
    """Extract all HTTP/HTTPS links from an RST file."""
    links = []
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Match URLs in various RST formats
            for match in re.finditer(r'https?://[^\s<>"]+', line):
                links.append((match.group(), i))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return links


def categorize_links(links: List[Tuple[str, int]]) -> Dict[str, List[Tuple[str, int]]]:
    """Categorize links by domain."""
    categories = {
        'github': [],
        'docs': [],
        'pypi': [],
        'badges': [],
        'external': []
    }
    
    for link, line_num in links:
        # Clean up link (remove trailing punctuation)
        link = link.rstrip('.,;:)')
        
        if 'github.com' in link:
            categories['github'].append((link, line_num))
        elif 'skblaz.github.io/py3plex' in link or 'readthedocs' in link:
            categories['docs'].append((link, line_num))
        elif 'pypi.org' in link:
            categories['pypi'].append((link, line_num))
        elif 'shields.io' in link or 'img.shields.io' in link or 'badge' in link.lower():
            categories['badges'].append((link, line_num))
        else:
            categories['external'].append((link, line_num))
    
    return categories


def check_local_file_references(root: Path, file_path: Path, links: List[Tuple[str, int]]) -> List[str]:
    """Check if relative file references exist."""
    errors = []
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check markdown links for local files
        for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', content):
            link = match.group(2)
            if not link.startswith('http') and not link.startswith('#'):
                # Split off anchor if present
                file_part = link.split('#')[0]
                anchor_part = link.split('#')[1] if '#' in link else None
                
                # Skip pure anchors
                if not file_part:
                    continue
                
                # Relative file path
                if not file_part.startswith('/'):
                    # Relative to current file
                    target_path = (file_path.parent / file_part).resolve()
                else:
                    # Absolute from repo root
                    target_path = (root / file_part.lstrip('/')).resolve()
                
                if not target_path.exists():
                    errors.append(f"  Broken local link: {link} -> {target_path}")
    except Exception as e:
        errors.append(f"  Error checking local references: {e}")
    
    return errors


def validate_github_links(links: List[Tuple[str, int]], repo_path: Path) -> List[str]:
    """Validate GitHub links point to existing files/workflows."""
    errors = []
    
    for link, line_num in links:
        # Check workflow badge links
        if '/actions/workflows/' in link and link.endswith('.svg)'):
            workflow_name = link.split('/actions/workflows/')[-1].replace('.svg)', '')
            workflow_file = repo_path / '.github' / 'workflows' / workflow_name
            if not workflow_file.exists():
                errors.append(f"  Line {line_num}: Workflow not found: {workflow_name}")
        
        # Check blob links
        if '/blob/' in link:
            # Extract file path from URL
            parts = link.split('/blob/')
            if len(parts) == 2:
                file_ref = parts[1]
                # Remove branch name
                path_parts = file_ref.split('/', 1)
                if len(path_parts) == 2:
                    file_path = path_parts[1]
                    target = repo_path / file_path
                    if not target.exists():
                        errors.append(f"  Line {line_num}: File not found: {file_path}")
    
    return errors


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent.resolve()
    
    print("=" * 80)
    print("py3plex Link Checker")
    print("=" * 80)
    print()
    
    # Find all markdown and RST files
    print(" Finding documentation files...")
    md_files = find_markdown_files(repo_root)
    rst_files = find_rst_files(repo_root / 'docfiles')
    
    print(f"  Found {len(md_files)} markdown files")
    print(f"  Found {len(rst_files)} RST files")
    print()
    
    # Extract all links
    print(" Extracting links...")
    all_links = {}
    
    for md_file in md_files:
        links = extract_links_from_markdown(md_file)
        if links:
            all_links[md_file] = links
    
    for rst_file in rst_files:
        links = extract_links_from_rst(rst_file)
        if links:
            all_links[rst_file] = links
    
    total_links = sum(len(links) for links in all_links.values())
    print(f"  Extracted {total_links} links from {len(all_links)} files")
    print()
    
    # Check links by category
    print(" Validating links...")
    errors = []
    
    for file_path, links in all_links.items():
        rel_path = file_path.relative_to(repo_root)
        
        # Check local file references
        local_errors = check_local_file_references(repo_root, file_path, links)
        if local_errors:
            errors.append(f"\n{rel_path}:")
            errors.extend(local_errors)
        
        # Categorize and validate GitHub links
        categories = categorize_links(links)
        github_errors = validate_github_links(categories['github'], repo_root)
        if github_errors:
            if not local_errors:
                errors.append(f"\n{rel_path}:")
            errors.extend(github_errors)
    
    # Report results
    print()
    if errors:
        print(" Link validation FAILED")
        print("=" * 80)
        for error in errors:
            print(error)
        print()
        return 1
    else:
        print(" All links validated successfully!")
        print()
        
        # Print summary statistics
        all_link_list = []
        for links in all_links.values():
            all_link_list.extend(links)
        
        categories = categorize_links(all_link_list)
        print(" Link Statistics:")
        print(f"  GitHub links: {len(categories['github'])}")
        print(f"  Documentation links: {len(categories['docs'])}")
        print(f"  PyPI links: {len(categories['pypi'])}")
        print(f"  Badge links: {len(categories['badges'])}")
        print(f"  External links: {len(categories['external'])}")
        print(f"  Total: {len(all_link_list)}")
        print()
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
