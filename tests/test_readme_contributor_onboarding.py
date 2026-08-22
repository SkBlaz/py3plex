"""Tests for contributor onboarding guidance in README."""

from pathlib import Path
import re

import pytest

repo_root: Path = Path(__file__).resolve().parents[1]


@pytest.fixture
def readme_content() -> str:
    """Return repository README text for onboarding assertions."""
    return (repo_root / "README.md").read_text(encoding="utf-8")


def test_readme_has_first_pr_quick_path_section(readme_content: str):
    """README should include an explicit first-contribution quick path."""
    assert "### Contributing (First PR Quick Path)" in readme_content
    assert "### MCP Integration (AI Agents)" in readme_content
    quick_path_split = readme_content.split(
        "### Contributing (First PR Quick Path)", maxsplit=1
    )
    assert len(quick_path_split) == 2
    mcp_split = quick_path_split[1].split("### MCP Integration (AI Agents)", maxsplit=1)
    assert len(mcp_split) == 2
    section = mcp_split[0]
    required_commands = [
        "make setup",
        "make dev-install",
        "make format",
        "make lint",
        "make test",
    ]
    missing = [command for command in required_commands if command not in section]
    assert not missing, f"README contributor quick path is missing commands: {missing}"


def test_readme_mentions_contributor_safety_policy(readme_content: str):
    """README should surface key contributor safety constraints."""
    assert "Do not add new markdown files unless explicitly requested" in readme_content
    assert "make ci" in readme_content


def test_readme_uses_test_coverage_badge_label(readme_content: str):
    """README should use the exact test coverage badge label casing."""
    assert "[![Test coverage]" in readme_content


def test_readme_coverage_badges_use_percentage_badge_urls(readme_content: str):
    """README coverage badges should use shields percentage badge endpoints."""
    assert (
        "https://img.shields.io/badge/test_coverage-"
        in readme_content
    )
    assert (
        "https://img.shields.io/badge/type_coverage-"
        in readme_content
    )


def test_readme_test_coverage_badge_threshold_at_least_40(readme_content: str):
    """README test coverage badge should display at least 40%."""
    match = re.search(
        r"https://img\.shields\.io/badge/test_coverage-([0-9]+(?:\.[0-9]+)?)%25",
        readme_content,
    )
    assert match is not None, "Missing test_coverage shields badge in README"
    assert float(match.group(1)) >= 40.0
