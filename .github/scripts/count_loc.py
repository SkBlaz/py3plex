#!/usr/bin/env python3
"""
Count Lines of Code (LOC) in the py3plex repository.
This script counts total lines, code lines, and excludes comments and blank lines.
"""

import os
import json
from pathlib import Path


def count_lines_in_file(filepath):
    """
    Count lines in a single file.
    Returns tuple: (total_lines, code_lines, comment_lines, blank_lines)
    """
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                stripped = line.strip()
                
                if not stripped:
                    blank_lines += 1
                elif stripped.startswith('#'):
                    comment_lines += 1
                else:
                    code_lines += 1
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        
    return total_lines, code_lines, comment_lines, blank_lines


def count_loc(root_dir, extensions=None):
    """
    Count lines of code in all files with specified extensions.
    
    Args:
        root_dir: Root directory to search
        extensions: List of file extensions to include (e.g., ['.py', '.js'])
    
    Returns:
        Dictionary with LOC statistics
    """
    if extensions is None:
        extensions = ['.py']
    
    root_path = Path(root_dir)
    
    # Directories to exclude
    exclude_dirs = {
        '.git', '.github', '__pycache__', '.pytest_cache', 
        '.venv', 'venv', 'env', '.env', 'node_modules',
        'build', 'dist', '*.egg-info', '.tox', '.mypy_cache',
        'htmlcov', '.coverage', 'docs/_build'
    }
    
    total_files = 0
    total_lines = 0
    total_code = 0
    total_comments = 0
    total_blanks = 0
    
    for ext in extensions:
        for filepath in root_path.rglob(f'*{ext}'):
            # Skip excluded directories
            if any(excluded in filepath.parts for excluded in exclude_dirs):
                continue
            
            # Skip hidden files
            if any(part.startswith('.') for part in filepath.parts[len(root_path.parts):]):
                continue
                
            lines, code, comments, blanks = count_lines_in_file(filepath)
            total_files += 1
            total_lines += lines
            total_code += code
            total_comments += comments
            total_blanks += blanks
    
    return {
        'total_files': total_files,
        'total_lines': total_lines,
        'code_lines': total_code,
        'comment_lines': total_comments,
        'blank_lines': total_blanks,
        'extensions': extensions
    }


def format_number(num):
    """Format number with K suffix for thousands."""
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


def main():
    """Main function to count LOC and generate output."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Count lines of code in py3plex')
    parser.add_argument('--root', default='.', help='Root directory to scan')
    parser.add_argument('--json', help='Output JSON file path')
    parser.add_argument('--extensions', nargs='+', default=['.py'], 
                        help='File extensions to count (default: .py)')
    
    args = parser.parse_args()
    
    # Count LOC
    stats = count_loc(args.root, args.extensions)
    
    # Print summary
    print(f"Lines of Code Report")
    print(f"{'='*50}")
    print(f"Total files:    {stats['total_files']}")
    print(f"Total lines:    {stats['total_lines']:,}")
    print(f"Code lines:     {stats['code_lines']:,}")
    print(f"Comment lines:  {stats['comment_lines']:,}")
    print(f"Blank lines:    {stats['blank_lines']:,}")
    print(f"Extensions:     {', '.join(stats['extensions'])}")
    print(f"{'='*50}")
    print(f"Badge value:    {format_number(stats['total_lines'])}")
    
    # Add formatted values for badge generation
    stats['total_lines_formatted'] = format_number(stats['total_lines'])
    stats['code_lines_formatted'] = format_number(stats['code_lines'])
    
    # Write JSON output if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\nJSON output written to: {args.json}")
    
    return stats


if __name__ == '__main__':
    main()
