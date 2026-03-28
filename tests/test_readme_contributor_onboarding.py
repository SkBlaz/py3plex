"""Tests for contributor onboarding guidance in README."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_first_pr_quick_path_section():
    """README should include an explicit first-contribution quick path."""
    content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Contributing (First PR Quick Path)" in content
    assert "make setup" in content
    assert "make dev-install" in content
    assert "make format" in content
    assert "make lint" in content
    assert "make test" in content


def test_readme_mentions_contributor_safety_policy():
    """README should surface key contributor safety constraints."""
    content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Do not add new markdown files unless explicitly requested" in content
    assert "make ci" in content
