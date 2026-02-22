"""
Tests for link checker script.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_link_checker_exists():
    """Test that link checker script exists and is executable."""
    script_path = Path(__file__).parent.parent / "scripts" / "check_links.py"
    assert script_path.exists(), f"Link checker script not found at {script_path}"
    assert script_path.stat().st_mode & 0o111, "Link checker script is not executable"


def test_link_checker_runs_successfully():
    """Test that link checker runs without errors."""
    script_path = Path(__file__).parent.parent / "scripts" / "check_links.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent,
        timeout=60
    )
    
    # Should exit with 0 if all links are valid
    assert result.returncode == 0, f"Link checker failed:\n{result.stdout}\n{result.stderr}"
    
    # Should report success
    assert "All links validated successfully" in result.stdout or "Link validation" in result.stdout


def test_no_new_markdown_files():
    """Test that no unexpected markdown files have been added."""
    repo_root = Path(__file__).parent.parent
    
    # Get all markdown files (exclude cache/build directories)
    md_files = sorted([
        str(p.relative_to(repo_root))
        for p in repo_root.rglob("*.md")
        if ".pytest_cache" not in str(p) and "node_modules" not in str(p)
    ])
    
    # Expected markdown files (based on repository audit)
    expected_md_files = [
        ".github/copilot-instructions.md",
        "AGENTS.md",
        "README.md",
        "benchmarks/README.md",
        "docs/flaky_tests_guide.md",
        "example_images/README.md",
        "examples/README.md",
        "examples/advanced/README.md",
        "examples/cli/README.md",
        "examples/dsl_zoo/README.md",
        "examples/getting_started/README.md",
        "examples/io_and_data/README.md",
        "examples/network_analysis/README.md",
        "examples/pipelines/README.md",
        "fuzzing/README.md",
        "gui/README.md",
        "gui/ci/api-tests/README.md",
        "notebooks/README.md",
        "py3plex/stats/README.md",
        "py3plex/uncertainty/README.md",
        "scripts/README.md",
    ]
    
    # Verify count matches
    assert len(md_files) == len(expected_md_files), (
        f"Expected {len(expected_md_files)} markdown files, found {len(md_files)}. "
        f"New files: {set(md_files) - set(expected_md_files)}"
    )
    
    # Verify all expected files exist
    missing_files = set(expected_md_files) - set(md_files)
    assert not missing_files, f"Missing expected markdown files: {missing_files}"
    
    # Verify no unexpected files exist
    unexpected_files = set(md_files) - set(expected_md_files)
    assert not unexpected_files, f"Unexpected markdown files found: {unexpected_files}"


def test_link_statistics():
    """Test that link checker reports expected statistics."""
    script_path = Path(__file__).parent.parent / "scripts" / "check_links.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent,
        timeout=60
    )
    
    # Should include statistics
    assert "Link Statistics:" in result.stdout
    assert "GitHub links:" in result.stdout
    assert "Total:" in result.stdout
    
    # Parse total links
    for line in result.stdout.split('\n'):
        if 'Total:' in line:
            total = int(line.split(':')[1].strip())
            # Should find at least 100 links across all documentation
            assert total >= 100, f"Expected at least 100 links, found {total}"
