#!/usr/bin/env python3
"""
API Consistency Check Script

This script validates that all public functions in py3plex have:
1. Proper docstrings
2. Type hints (where applicable)
3. Examples in docstrings
4. Consistent parameter documentation

Usage:
    python check_api_consistency.py
    python check_api_consistency.py --verbose
    python check_api_consistency.py --module py3plex.core
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class APIChecker(ast.NodeVisitor):
    """AST visitor to check API consistency."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues: List[Dict[str, str]] = []
        self.current_class = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Check class docstring
        docstring = ast.get_docstring(node)
        if not docstring and not node.name.startswith('_'):
            self.issues.append({
                'type': 'missing_docstring',
                'location': f"{self.filepath}:{node.lineno}",
                'name': f"class {node.name}",
                'message': "Public class missing docstring"
            })
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        # Skip private functions
        if node.name.startswith('_') and node.name != '__init__':
            return
        
        full_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        
        # Check docstring
        docstring = ast.get_docstring(node)
        if not docstring:
            self.issues.append({
                'type': 'missing_docstring',
                'location': f"{self.filepath}:{node.lineno}",
                'name': full_name,
                'message': "Public function missing docstring"
            })
        else:
            # Check for common docstring sections
            has_args = 'Args:' in docstring or 'Parameters:' in docstring
            has_returns = 'Returns:' in docstring or 'Return:' in docstring
            has_example = 'Example' in docstring or '>>>' in docstring
            
            # Check if function has parameters (excluding self, cls)
            params = [arg.arg for arg in node.args.args 
                     if arg.arg not in ('self', 'cls')]
            
            if params and not has_args:
                self.issues.append({
                    'type': 'missing_args_doc',
                    'location': f"{self.filepath}:{node.lineno}",
                    'name': full_name,
                    'message': f"Function has parameters but docstring lacks Args section"
                })
            
            # Check for Returns documentation
            has_return_stmt = any(isinstance(n, ast.Return) and n.value 
                                 for n in ast.walk(node))
            if has_return_stmt and not has_returns and node.name != '__init__':
                self.issues.append({
                    'type': 'missing_returns_doc',
                    'location': f"{self.filepath}:{node.lineno}",
                    'name': full_name,
                    'message': "Function returns value but docstring lacks Returns section"
                })
            
            # Check for example
            if not has_example and not node.name.startswith('_'):
                self.issues.append({
                    'type': 'missing_example',
                    'location': f"{self.filepath}:{node.lineno}",
                    'name': full_name,
                    'message': "Public function missing example in docstring"
                })
        
        # Check type hints
        missing_hints = []
        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            if arg.annotation is None:
                missing_hints.append(arg.arg)
        
        if missing_hints and node.name != '__init__':
            self.issues.append({
                'type': 'missing_type_hints',
                'location': f"{self.filepath}:{node.lineno}",
                'name': full_name,
                'message': f"Missing type hints for parameters: {', '.join(missing_hints)}"
            })
        
        self.generic_visit(node)


def check_file(filepath: Path) -> List[Dict[str, str]]:
    """Check a single Python file for API consistency."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        checker = APIChecker(str(filepath))
        checker.visit(tree)
        return checker.issues
    except SyntaxError as e:
        return [{
            'type': 'syntax_error',
            'location': f"{filepath}:{e.lineno}",
            'name': filepath.name,
            'message': f"Syntax error: {e.msg}"
        }]
    except Exception as e:
        return [{
            'type': 'error',
            'location': str(filepath),
            'name': filepath.name,
            'message': f"Error processing file: {str(e)}"
        }]


def find_python_files(root: Path, exclude_patterns: List[str]) -> List[Path]:
    """Find all Python files in the directory tree."""
    python_files = []
    for path in root.rglob("*.py"):
        # Skip excluded paths
        if any(pattern in str(path) for pattern in exclude_patterns):
            continue
        python_files.append(path)
    return python_files


def main():
    parser = argparse.ArgumentParser(description="Check API consistency for py3plex")
    parser.add_argument('--verbose', '-v', action='store_true',
                       help="Show all issues including suggestions")
    parser.add_argument('--module', '-m', type=str,
                       help="Check specific module (e.g., py3plex.core)")
    parser.add_argument('--fail-on-error', action='store_true',
                       help="Exit with error code if issues found")
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    py3plex_dir = project_root / "py3plex"
    
    if not py3plex_dir.exists():
        print(f"Error: py3plex directory not found at {py3plex_dir}")
        sys.exit(1)
    
    # Determine which files to check
    if args.module:
        module_path = args.module.replace('.', '/')
        check_dir = py3plex_dir / module_path
        if not check_dir.exists():
            # Try as a file
            check_file_path = py3plex_dir / f"{module_path}.py"
            if check_file_path.exists():
                files = [check_file_path]
            else:
                print(f"Error: Module {args.module} not found")
                sys.exit(1)
        else:
            files = find_python_files(check_dir, ['__pycache__', 'test_', '_test'])
    else:
        # Check all files
        files = find_python_files(py3plex_dir, ['__pycache__', 'test_', '_test', 
                                                 'infomap', 'hedwig'])
    
    print(f"Checking {len(files)} Python files...")
    print()
    
    # Collect all issues
    all_issues = []
    for filepath in sorted(files):
        issues = check_file(filepath)
        all_issues.extend(issues)
    
    # Group issues by type
    issues_by_type = {}
    for issue in all_issues:
        issue_type = issue['type']
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
    
    # Display summary
    print("=" * 70)
    print("API Consistency Check Summary")
    print("=" * 70)
    print()
    
    if not all_issues:
        print("[OK] No API consistency issues found!")
        print()
        return 0
    
    # Show counts by type
    print(f"Total issues found: {len(all_issues)}")
    print()
    for issue_type, issues in sorted(issues_by_type.items()):
        print(f"  {issue_type}: {len(issues)}")
    print()
    
    # Show detailed issues if verbose
    if args.verbose:
        print("=" * 70)
        print("Detailed Issues")
        print("=" * 70)
        print()
        
        for issue_type, issues in sorted(issues_by_type.items()):
            print(f"{issue_type.upper().replace('_', ' ')} ({len(issues)} issues):")
            print("-" * 70)
            for issue in issues:
                print(f"  {issue['location']}")
                print(f"  {issue['name']}: {issue['message']}")
                print()
    else:
        print("Run with --verbose to see detailed issues")
        print()
    
    # Show suggestions
    print("=" * 70)
    print("Suggestions")
    print("=" * 70)
    print()
    print("1. Add docstrings to all public functions and classes")
    print("2. Include Args, Returns, and Example sections in docstrings")
    print("3. Add type hints to function parameters")
    print("4. Follow Google Python Style Guide for docstrings")
    print()
    
    if args.fail_on_error:
        return 1 if all_issues else 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
