"""Main runner for all quality analysis tools.

This script runs all quality analysis tools and generates reports.
Usage: python -m tools.quality.runner [repo_root]
"""

import sys
from pathlib import Path
import argparse


def main():
    """Run all quality analysis tools."""
    parser = argparse.ArgumentParser(description="Run py3plex quality analysis tools")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the repository",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=["import", "dead", "redundancy", "api", "examples", "docs", "all"],
        default=["all"],
        help="Tools to run",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for reports (default: repo_root/build/quality)",
    )

    args = parser.parse_args()

    repo_root = args.repo_root
    output_dir = args.output_dir or (repo_root / "build" / "quality")
    output_dir.mkdir(parents=True, exist_ok=True)

    tools_to_run = args.tools
    if "all" in tools_to_run:
        tools_to_run = ["import", "dead", "redundancy", "api", "examples", "docs"]

    print("=" * 70)
    print("Py3plex Quality Analysis Runner")
    print("=" * 70)
    print(f"Repository: {repo_root}")
    print(f"Output directory: {output_dir}")
    print(f"Tools: {', '.join(tools_to_run)}")
    print("=" * 70)
    print()

    # Import graph
    if "import" in tools_to_run:
        print("Running import graph analysis...")
        from .import_graph import ImportGraphAnalyzer

        analyzer = ImportGraphAnalyzer(repo_root)
        analyzer.save_to_json(output_dir / "import_graph.json")
        print()

    # Dead code detection
    if "dead" in tools_to_run:
        print("Running dead code detection...")
        from .dead_code import DeadCodeDetector

        detector = DeadCodeDetector(repo_root)
        detector.save_to_json(output_dir / "dead_code.json")
        print()

    # Redundancy detection
    if "redundancy" in tools_to_run:
        print("Running redundancy detection...")
        from .redundancy import RedundancyDetector

        detector = RedundancyDetector(repo_root)
        detector.save_to_json(output_dir / "redundancy.json")
        print()

    # API audit
    if "api" in tools_to_run:
        print("Running public API audit...")
        from .api_audit import PublicAPIAuditor

        auditor = PublicAPIAuditor(repo_root)
        auditor.save_to_json(output_dir / "public_api.json")
        print()

    # Examples health
    if "examples" in tools_to_run:
        print("Running examples health check...")
        from .examples_health import ExamplesHealthChecker

        checker = ExamplesHealthChecker(repo_root)
        checker.save_to_json(output_dir / "examples_health.json")
        print()

    # Docs health
    if "docs" in tools_to_run:
        print("Running docs health check...")
        from .docs_health import DocsHealthChecker

        checker = DocsHealthChecker(repo_root)
        checker.save_to_json(output_dir / "docs_health.json")
        print()

    print("=" * 70)
    print("Quality analysis complete!")
    print(f"Reports saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
