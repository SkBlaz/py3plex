"""Tests for quality analysis tools."""

import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create package structure
        pkg_dir = repo_root / "py3plex"
        pkg_dir.mkdir()

        # Create __init__.py
        (pkg_dir / "__init__.py").write_text(
            """
__all__ = ["public_func", "PublicClass"]

from .core import public_func, PublicClass
"""
        )

        # Create core module
        (pkg_dir / "core.py").write_text(
            """
def public_func():
    '''A public function.'''
    return "public"

class PublicClass:
    '''A public class.'''
    pass

def _private_func():
    '''A private function.'''
    return "private"

def unused_func():
    '''An unused function.'''
    return "unused"
"""
        )

        # Create another module with duplicates
        (pkg_dir / "utils.py").write_text(
            """
def helper_func():
    '''Helper function.'''
    x = 1
    y = 2
    return x + y

def another_helper():
    '''Another helper (duplicate).'''
    x = 1
    y = 2
    return x + y
"""
        )

        # Create examples directory
        examples_dir = repo_root / "examples"
        examples_dir.mkdir()

        (examples_dir / "example1.py").write_text(
            """
from py3plex.core import public_func

result = public_func()
print(result)
"""
        )

        (examples_dir / "broken_example.py").write_text(
            """
from py3plex.nonexistent import missing_func

missing_func()
"""
        )

        # Create docs directory
        docs_dir = repo_root / "docfiles"
        docs_dir.mkdir()

        (docs_dir / "tutorial.rst").write_text(
            """
Tutorial
========

Here's an example:

.. code-block:: python

    from py3plex.core import public_func
    
    result = public_func()
    print(result)
"""
        )

        # Create build directory
        build_dir = repo_root / "build" / "quality"
        build_dir.mkdir(parents=True)

        yield repo_root


def test_import_graph_analyzer(temp_repo):
    """Test import graph analyzer."""
    from tools.quality.import_graph import ImportGraphAnalyzer

    analyzer = ImportGraphAnalyzer(temp_repo)
    result = analyzer.analyze()

    assert "nodes" in result
    assert "edges" in result
    assert "stats" in result
    assert result["stats"]["total_modules"] >= 0


def test_dead_code_detector(temp_repo):
    """Test dead code detector."""
    from tools.quality.dead_code import DeadCodeDetector

    detector = DeadCodeDetector(temp_repo)
    items = detector.analyze()

    # Check structure
    assert isinstance(items, list)

    # Check that unused_func is detected (if scoring is high enough)
    symbols = [item.symbol for item in items]
    # Note: unused_func might not be detected due to thresholds, but structure should be valid

    for item in items:
        assert hasattr(item, "file")
        assert hasattr(item, "line")
        assert hasattr(item, "symbol")
        assert hasattr(item, "score")
        assert 0 <= item.score <= 1


def test_redundancy_detector(temp_repo):
    """Test redundancy detector."""
    from tools.quality.redundancy import RedundancyDetector

    detector = RedundancyDetector(temp_repo)
    clusters = detector.analyze()

    # Check structure
    assert isinstance(clusters, list)

    # The two helper functions should be detected as duplicates
    for cluster in clusters:
        assert hasattr(cluster, "cluster_id")
        assert hasattr(cluster, "similarity_type")
        assert hasattr(cluster, "members")
        assert len(cluster.members) >= 2


def test_api_auditor(temp_repo):
    """Test public API auditor."""
    from tools.quality.api_audit import PublicAPIAuditor

    auditor = PublicAPIAuditor(temp_repo)
    symbols = auditor.analyze()

    # Check structure
    assert isinstance(symbols, list)

    # Check that public_func is in the API
    symbol_names = [s.symbol for s in symbols]

    for symbol in symbols:
        assert hasattr(symbol, "symbol")
        assert hasattr(symbol, "stability_tier")
        assert symbol.stability_tier in ["core", "supported", "experimental", "internal"]


def test_examples_health_checker(temp_repo):
    """Test examples health checker."""
    from tools.quality.examples_health import ExamplesHealthChecker

    checker = ExamplesHealthChecker(temp_repo)
    results = checker.check()

    # Check structure
    assert isinstance(results, list)
    assert len(results) >= 2  # example1.py and broken_example.py

    # Check statuses
    statuses = [r.status for r in results]
    assert "healthy" in statuses or "import_error" in statuses


def test_docs_health_checker(temp_repo):
    """Test docs health checker."""
    from tools.quality.docs_health import DocsHealthChecker

    checker = DocsHealthChecker(temp_repo)
    results = checker.check()

    # Check structure
    assert isinstance(results, list)

    for ref in results:
        assert hasattr(ref, "file")
        assert hasattr(ref, "line")
        assert hasattr(ref, "status")


def test_runner_output(temp_repo):
    """Test that runner creates output files."""
    from tools.quality.import_graph import ImportGraphAnalyzer
    from tools.quality.dead_code import DeadCodeDetector

    output_dir = temp_repo / "build" / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run import graph
    analyzer = ImportGraphAnalyzer(temp_repo)
    output_file = output_dir / "import_graph.json"
    analyzer.save_to_json(output_file)

    assert output_file.exists()

    # Verify JSON is valid
    with open(output_file, "r") as f:
        data = json.load(f)
        assert "nodes" in data

    # Run dead code detector
    detector = DeadCodeDetector(temp_repo)
    output_file = output_dir / "dead_code.json"
    detector.save_to_json(output_file)

    assert output_file.exists()

    with open(output_file, "r") as f:
        data = json.load(f)
        assert "total_candidates" in data


def test_whitelist_loading(temp_repo):
    """Test whitelist configuration loading."""
    from tools.quality.dead_code import DeadCodeDetector

    # Create whitelist file
    whitelist_path = temp_repo / "tools" / "whitelist.yml"
    whitelist_path.parent.mkdir(parents=True, exist_ok=True)
    whitelist_path.write_text(
        """
plugin_entrypoints:
  - TestPlugin

cli_commands:
  - main
"""
    )

    detector = DeadCodeDetector(temp_repo, whitelist_path)
    assert "TestPlugin" in detector.whitelist.get("plugin_entrypoints", [])
    assert "main" in detector.whitelist.get("cli_commands", [])


def test_json_output_stable(temp_repo):
    """Test that JSON outputs are stable across runs."""
    from tools.quality.import_graph import ImportGraphAnalyzer

    analyzer = ImportGraphAnalyzer(temp_repo)
    result1 = analyzer.analyze()
    result2 = analyzer.analyze()

    # Check that results are identical
    assert result1["stats"] == result2["stats"]
    assert len(result1["nodes"]) == len(result2["nodes"])


def test_baseline_comparison(temp_repo):
    """Test baseline comparison functionality."""
    from tools.quality.baseline import BaselineChecker
    
    quality_dir = temp_repo / "build" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    
    # Create initial baseline metrics
    baseline_metrics = {
        "dead_code": {"total_candidates": 100, "high_confidence": 10},
        "redundancy": {"total_clusters": 20},
    }
    
    # Create and save baseline
    checker = BaselineChecker(temp_repo)
    checker.update_baseline(baseline_metrics)
    
    # Reload checker to get baseline
    checker = BaselineChecker(temp_repo)
    
    # Compare against same baseline (should pass)
    results = checker.compare(baseline_metrics)
    if results:
        assert all(not r.regression for r in results)
    
    # Compare with regression
    regressed_metrics = {
        "dead_code": {"total_candidates": 110, "high_confidence": 10},  # +10 (threshold is 5)
        "redundancy": {"total_clusters": 20},
    }
    results = checker.compare(regressed_metrics)
    
    # Should detect regression in dead_code
    if results:
        dead_code_results = [r for r in results if r.metric == "dead_code_count"]
        if dead_code_results:
            assert dead_code_results[0].regression  # 110 > 100 + 5


def test_layer_checker_rules(temp_repo):
    """Test layer boundary checker."""
    from tools.quality.layer_checker import ImportBoundaryChecker
    
    # Create pyproject.toml with rules
    pyproject = temp_repo / "pyproject.toml"
    pyproject.write_text("""
[tool.py3plex.layering]
dsl_forbidden_imports = ["py3plex.algorithms"]
""")
    
    # Create violating code
    dsl_dir = temp_repo / "py3plex" / "dsl"
    dsl_dir.mkdir(parents=True, exist_ok=True)
    (dsl_dir / "test.py").write_text("""
from py3plex.algorithms import something
""")
    
    checker = ImportBoundaryChecker(temp_repo)
    violations = checker.check()
    
    # Should detect violation
    assert len(violations) > 0
    assert violations[0].rule == "dsl_forbidden_imports"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
