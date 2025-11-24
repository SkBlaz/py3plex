#!/usr/bin/env python3
"""
Type Coverage Check Script

This script measures type annotation coverage in py3plex using mypy.
It generates a coverage percentage, badge, and detailed report.

The script:
1. Runs mypy with coverage reports
2. Parses the linecount report to extract metrics
3. Calculates type precision/imprecision percentages
4. Generates a badge URL and JSON report

Usage:
    python check_type_coverage.py
    python check_type_coverage.py --verbose
    python check_type_coverage.py --json coverage.json
    python check_type_coverage.py --badge-only
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple


def run_mypy_coverage(package_path: Path, temp_dir: Path) -> Tuple[str, int]:
    """
    Run mypy with coverage reports.
    
    Args:
        package_path: Path to the package to analyze
        temp_dir: Temporary directory for reports
    
    Returns:
        Tuple of (txt report path, exit code)
    """
    lineprecision_dir = temp_dir / "lineprecision"
    html_dir = temp_dir / "html"
    txt_dir = temp_dir / "txt"
    any_dir = temp_dir / "any"
    
    cmd = [
        "mypy",
        str(package_path),
        "--ignore-missing-imports",
        "--lineprecision-report", str(lineprecision_dir),
        "--html-report", str(html_dir),
        "--txt-report", str(txt_dir),
        "--any-exprs-report", str(any_dir),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        txt_report = txt_dir / "index.txt"
        return str(txt_report), result.returncode
    
    except subprocess.TimeoutExpired:
        print("Error: mypy timed out after 5 minutes", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: mypy not found. Install with: pip install mypy lxml", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running mypy: {e}", file=sys.stderr)
        sys.exit(1)


def parse_linecount_report(report_path: str) -> Dict[str, any]:
    """
    Parse mypy txt report to extract coverage metrics.
    
    Args:
        report_path: Path to the txt report (index.txt)
    
    Returns:
        Dictionary with coverage metrics
    """
    try:
        with open(report_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse the summary line at the bottom
    # Format: "| Total                    |  34.09% imprecise | 26465 LOC |"
    total_line_pattern = r'\|\s*Total\s*\|\s*(\d+\.\d+)%\s*imprecise\s*\|\s*(\d+)\s*LOC\s*\|'
    match = re.search(total_line_pattern, content)
    
    if not match:
        print("Error: Could not parse total coverage from report", file=sys.stderr)
        sys.exit(1)
    
    imprecise_percent = float(match.group(1))
    total_loc = int(match.group(2))
    
    # Calculate metrics
    precise_percent = 100.0 - imprecise_percent
    imprecise_loc = int(total_loc * imprecise_percent / 100)
    precise_loc = total_loc - imprecise_loc
    
    # Parse per-module data for detailed report
    modules = []
    # Format: "| py3plex.module.name                |  25.00% imprecise |  100 LOC |"
    module_pattern = r'\|\s*([^\|]+?)\s*\|\s*(\d+\.\d+)%\s*imprecise\s*\|\s*(\d+)\s*LOC\s*\|'
    
    for match in re.finditer(module_pattern, content):
        module_name = match.group(1).strip()
        if module_name == "Total":
            continue
        
        module_imprecise = float(match.group(2))
        module_loc = int(match.group(3))
        
        modules.append({
            "name": module_name,
            "imprecise_percent": module_imprecise,
            "precise_percent": 100.0 - module_imprecise,
            "total_loc": module_loc,
            "imprecise_loc": int(module_loc * module_imprecise / 100),
            "precise_loc": int(module_loc * (100.0 - module_imprecise) / 100)
        })
    
    return {
        "total_loc": total_loc,
        "precise_loc": precise_loc,
        "imprecise_loc": imprecise_loc,
        "precise_percent": precise_percent,
        "imprecise_percent": imprecise_percent,
        "modules": modules
    }


def generate_badge_url(coverage_percent: float) -> str:
    """
    Generate shields.io badge URL for type coverage.
    
    Args:
        coverage_percent: Type coverage percentage (precise %)
    
    Returns:
        Badge URL
    """
    # Color based on coverage
    if coverage_percent >= 90:
        color = "brightgreen"
    elif coverage_percent >= 80:
        color = "green"
    elif coverage_percent >= 70:
        color = "yellowgreen"
    elif coverage_percent >= 60:
        color = "yellow"
    elif coverage_percent >= 50:
        color = "orange"
    else:
        color = "red"
    
    badge_url = f"https://img.shields.io/badge/type_coverage-{coverage_percent:.1f}%25-{color}"
    return badge_url


def format_top_imprecise_modules(modules: List[Dict], top_n: int = 10) -> str:
    """
    Format the top N most imprecise modules for display.
    
    Args:
        modules: List of module metrics
        top_n: Number of modules to display
    
    Returns:
        Formatted string
    """
    # Sort by imprecise percentage (descending)
    sorted_modules = sorted(
        modules,
        key=lambda m: m["imprecise_percent"],
        reverse=True
    )
    
    lines = []
    lines.append(f"\nTop {top_n} Most Imprecise Modules:")
    lines.append("-" * 80)
    
    for i, module in enumerate(sorted_modules[:top_n], 1):
        lines.append(
            f"{i:2}. {module['name'][:60]:<60} "
            f"{module['imprecise_percent']:5.1f}% imprecise "
            f"({module['total_loc']:4} LOC)"
        )
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check type coverage using mypy"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--json",
        type=str,
        help="Output JSON report to file"
    )
    parser.add_argument(
        "--badge-only",
        action="store_true",
        help="Only print badge URL"
    )
    parser.add_argument(
        "--package",
        type=str,
        default="py3plex",
        help="Package to analyze (default: py3plex)"
    )
    
    args = parser.parse_args()
    
    # Find package path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    package_path = repo_root / args.package
    
    if not package_path.exists():
        print(f"Error: Package not found: {package_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run mypy with coverage
    if not args.badge_only:
        print(f"Running mypy type coverage analysis on {package_path}...", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        report_path, exit_code = run_mypy_coverage(package_path, temp_path)
        
        # Parse results
        metrics = parse_linecount_report(report_path)
    
    # Generate badge
    badge_url = generate_badge_url(metrics["precise_percent"])
    
    if args.badge_only:
        print(badge_url)
        return
    
    # Prepare output
    output = {
        "total_loc": metrics["total_loc"],
        "precise_loc": metrics["precise_loc"],
        "imprecise_loc": metrics["imprecise_loc"],
        "precise_percent": round(metrics["precise_percent"], 2),
        "imprecise_percent": round(metrics["imprecise_percent"], 2),
        "badge_url": badge_url,
        "modules": metrics["modules"]
    }
    
    # Save JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"JSON report saved to: {args.json}", file=sys.stderr)
    
    # Display summary
    print("\n" + "=" * 80)
    print("TYPE COVERAGE REPORT")
    print("=" * 80)
    print(f"\nTotal Lines of Code:      {metrics['total_loc']:,}")
    print(f"Precisely Typed:          {metrics['precise_loc']:,} ({metrics['precise_percent']:.2f}%)")
    print(f"Imprecisely Typed:        {metrics['imprecise_loc']:,} ({metrics['imprecise_percent']:.2f}%)")
    print(f"\nType Coverage:            {metrics['precise_percent']:.2f}%")
    print(f"\nBadge: {badge_url}")
    
    if args.verbose:
        print(format_top_imprecise_modules(metrics["modules"], 20))
        print("\n" + "=" * 80)
    
    # Exit with appropriate code
    # Success if coverage is reasonable (>50%) or improving
    if metrics["precise_percent"] >= 50:
        sys.exit(0)
    else:
        print(f"\nWarning: Type coverage is below 50%", file=sys.stderr)
        sys.exit(0)  # Don't fail CI, just warn


if __name__ == "__main__":
    main()
