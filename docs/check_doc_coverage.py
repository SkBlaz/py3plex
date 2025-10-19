#!/usr/bin/env python3
"""
Documentation Coverage Check Script

This script measures what proportion of public functions in py3plex are documented
in the RST documentation files. It generates a coverage percentage and badge.

The script:
1. Scans all Python files in py3plex to find public functions/classes
2. Scans RST files to find documented functions/classes
3. Calculates coverage percentage
4. Generates a badge and report

Usage:
    python check_doc_coverage.py
    python check_doc_coverage.py --verbose
    python check_doc_coverage.py --badge-only
"""

import ast
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class FunctionCollector(ast.NodeVisitor):
    """AST visitor to collect public functions and classes."""
    
    def __init__(self, filepath: str, module_path: str):
        self.filepath = filepath
        self.module_path = module_path
        self.functions: Set[str] = set()
        self.classes: Set[str] = set()
        self.current_class = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if not node.name.startswith('_'):
            full_name = f"{self.module_path}.{node.name}"
            self.classes.add(full_name)
            
            old_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        # Skip private functions
        if node.name.startswith('_') and node.name != '__init__':
            return
        
        if self.current_class:
            # Method
            full_name = f"{self.module_path}.{self.current_class}.{node.name}"
        else:
            # Top-level function
            full_name = f"{self.module_path}.{node.name}"
        
        self.functions.add(full_name)
        self.generic_visit(node)


def get_module_path(filepath: Path, py3plex_dir: Path) -> str:
    """Convert file path to module path."""
    relative = filepath.relative_to(py3plex_dir.parent)
    module = str(relative.with_suffix('')).replace('/', '.')
    return module


def collect_functions_from_code(py3plex_dir: Path) -> Tuple[Set[str], Set[str]]:
    """Collect all public functions and classes from Python files."""
    all_functions = set()
    all_classes = set()
    
    exclude_patterns = ['__pycache__', 'test_', '_test', '.pyc']
    
    for py_file in py3plex_dir.rglob('*.py'):
        # Skip excluded paths
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            
            module_path = get_module_path(py_file, py3plex_dir)
            collector = FunctionCollector(str(py_file), module_path)
            collector.visit(tree)
            
            all_functions.update(collector.functions)
            all_classes.update(collector.classes)
        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception:
            # Skip files that can't be parsed
            pass
    
    return all_functions, all_classes


def collect_documented_items_from_rst(docfiles_dir: Path, py3plex_dir: Path) -> Tuple[Set[str], Set[str]]:
    """Collect documented functions and classes from RST files."""
    documented_functions = set()
    documented_classes = set()
    documented_modules = set()
    
    # Patterns to match Sphinx autodoc directives
    autofunction_pattern = re.compile(r'^\.\.\s+autofunction::\s+(.+)$', re.MULTILINE)
    automethod_pattern = re.compile(r'^\.\.\s+automethod::\s+(.+)$', re.MULTILINE)
    autoclass_pattern = re.compile(r'^\.\.\s+autoclass::\s+(.+)$', re.MULTILINE)
    automodule_pattern = re.compile(r'^\.\.\s+automodule::\s+(.+)$', re.MULTILINE)
    
    for rst_file in docfiles_dir.rglob('*.rst'):
        try:
            with open(rst_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all autodoc directives
            for match in autofunction_pattern.finditer(content):
                func_name = match.group(1).strip()
                documented_functions.add(func_name)
            
            for match in automethod_pattern.finditer(content):
                method_name = match.group(1).strip()
                documented_functions.add(method_name)
            
            for match in autoclass_pattern.finditer(content):
                class_name = match.group(1).strip()
                documented_classes.add(class_name)
            
            # automodule with :members: documents all public members
            for match in automodule_pattern.finditer(content):
                module_name = match.group(1).strip()
                # Check if it has :members: option
                module_block_start = match.end()
                # Look ahead for the next few lines to check for :members:
                next_lines = content[module_block_start:module_block_start+500]
                if ':members:' in next_lines:
                    # This module's members are documented
                    documented_modules.add(module_name)
        except Exception:
            pass
    
    # For each documented module, collect all its public functions and classes
    for module_name in documented_modules:
        # Convert module name to file path
        module_path = module_name.replace('.', '/')
        module_file = py3plex_dir.parent / f"{module_path}.py"
        module_dir = py3plex_dir.parent / module_path
        
        # Try as a file first
        if module_file.exists():
            try:
                with open(module_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                collector = FunctionCollector(str(module_file), module_name)
                collector.visit(tree)
                documented_functions.update(collector.functions)
                documented_classes.update(collector.classes)
            except Exception:
                pass
        # Try as a package directory
        elif module_dir.exists() and (module_dir / '__init__.py').exists():
            init_file = module_dir / '__init__.py'
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                collector = FunctionCollector(str(init_file), module_name)
                collector.visit(tree)
                documented_functions.update(collector.functions)
                documented_classes.update(collector.classes)
            except Exception:
                pass
    
    return documented_functions, documented_classes


def calculate_coverage(all_items: Set[str], documented_items: Set[str]) -> Tuple[float, int]:
    """Calculate documentation coverage percentage.
    
    Returns:
        Tuple of (coverage_percentage, documented_count)
    """
    if not all_items:
        return 100.0, 0
    
    # Direct matches
    documented = all_items & documented_items
    documented_count = len(documented)
    
    coverage = (documented_count / len(all_items)) * 100
    return coverage, documented_count


def generate_badge_url(coverage: float) -> str:
    """Generate shields.io badge URL for documentation coverage."""
    # Determine color based on coverage
    if coverage >= 80:
        color = 'brightgreen'
    elif coverage >= 60:
        color = 'green'
    elif coverage >= 40:
        color = 'yellow'
    elif coverage >= 20:
        color = 'orange'
    else:
        color = 'red'
    
    badge_url = f"https://img.shields.io/badge/docs%20coverage-{coverage:.1f}%25-{color}"
    return badge_url


def find_undocumented_items(all_items: Set[str], documented_items: Set[str]) -> List[str]:
    """Find items that are not documented."""
    documented = all_items & documented_items
    undocumented = all_items - documented
    return sorted(undocumented)


def main():
    parser = argparse.ArgumentParser(description="Check documentation coverage for py3plex")
    parser.add_argument('--verbose', '-v', action='store_true',
                       help="Show detailed information")
    parser.add_argument('--badge-only', action='store_true',
                       help="Only output badge URL")
    parser.add_argument('--json', type=str,
                       help="Output results to JSON file")
    parser.add_argument('--fail-under', type=float,
                       help="Fail if coverage is under this percentage")
    args = parser.parse_args()
    
    # Find project directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    py3plex_dir = project_root / "py3plex"
    docfiles_dir = project_root / "docfiles"
    
    if not py3plex_dir.exists():
        print(f"Error: py3plex directory not found at {py3plex_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not docfiles_dir.exists():
        print(f"Error: docfiles directory not found at {docfiles_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Collect functions and classes from code
    all_functions, all_classes = collect_functions_from_code(py3plex_dir)
    
    # Collect documented items from RST files
    doc_functions, doc_classes = collect_documented_items_from_rst(docfiles_dir, py3plex_dir)
    
    # Calculate coverage
    func_coverage, func_doc_count = calculate_coverage(all_functions, doc_functions)
    class_coverage, class_doc_count = calculate_coverage(all_classes, doc_classes)
    
    # Overall coverage (weighted by total items)
    total_items = len(all_functions) + len(all_classes)
    if total_items > 0:
        overall_coverage = (
            (len(all_functions) * func_coverage + len(all_classes) * class_coverage) / 
            (total_items * 100)
        ) * 100
    else:
        overall_coverage = 100.0
    
    # Generate badge URL
    badge_url = generate_badge_url(overall_coverage)
    
    # Output based on mode
    if args.badge_only:
        print(badge_url)
        return 0
    
    # Full report
    print("=" * 70)
    print("Documentation Coverage Report")
    print("=" * 70)
    print()
    print(f"Total public functions: {len(all_functions)}")
    print(f"Total public classes: {len(all_classes)}")
    print(f"Total items: {total_items}")
    print()
    print(f"Documented functions: {func_doc_count}")
    print(f"Documented classes: {class_doc_count}")
    print()
    print(f"Function documentation coverage: {func_coverage:.1f}%")
    print(f"Class documentation coverage: {class_coverage:.1f}%")
    print(f"Overall documentation coverage: {overall_coverage:.1f}%")
    print()
    print(f"Badge URL: {badge_url}")
    print()
    
    # Show undocumented items if verbose
    if args.verbose:
        undoc_functions = find_undocumented_items(all_functions, doc_functions)
        undoc_classes = find_undocumented_items(all_classes, doc_classes)
        
        if undoc_functions or undoc_classes:
            print("=" * 70)
            print("Undocumented Items")
            print("=" * 70)
            print()
            
            if undoc_functions:
                print(f"Undocumented Functions ({len(undoc_functions)}):")
                print("-" * 70)
                for func in undoc_functions[:50]:  # Limit to first 50
                    print(f"  {func}")
                if len(undoc_functions) > 50:
                    print(f"  ... and {len(undoc_functions) - 50} more")
                print()
            
            if undoc_classes:
                print(f"Undocumented Classes ({len(undoc_classes)}):")
                print("-" * 70)
                for cls in undoc_classes[:50]:  # Limit to first 50
                    print(f"  {cls}")
                if len(undoc_classes) > 50:
                    print(f"  ... and {len(undoc_classes) - 50} more")
                print()
    
    # Save JSON if requested
    if args.json:
        result = {
            'total_functions': len(all_functions),
            'total_classes': len(all_classes),
            'total_items': total_items,
            'documented_functions': func_doc_count,
            'documented_classes': class_doc_count,
            'function_coverage': func_coverage,
            'class_coverage': class_coverage,
            'overall_coverage': overall_coverage,
            'badge_url': badge_url
        }
        
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Results saved to {args.json}")
        print()
    
    # Check threshold
    if args.fail_under is not None:
        if overall_coverage < args.fail_under:
            print(f"ERROR: Coverage {overall_coverage:.1f}% is below threshold {args.fail_under}%")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
