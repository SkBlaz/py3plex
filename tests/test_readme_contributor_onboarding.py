"""Tests for contributor onboarding guidance in README."""

from pathlib import Path

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


def test_readme_lists_supported_load_network_input_types(readme_content: str):
    """README TL;DR should list canonical supported load_network input types."""
    required_input_types = [
        "edgelist",
        "multiedgelist",
        "multiplex_edges",
        "multiplex_folder",
        "gml",
        "graphml",
        "gpickle",
        "gpickle_biomine",
        "nx",
        "sparse",
    ]

    assert "TL;DR: Public API and supported load formats" in readme_content
    assert "multi_layer_network.load_network" in readme_content
    missing = [item for item in required_input_types if f"`{item}`" not in readme_content]
    assert not missing, f"README is missing supported input_type values: {missing}"
