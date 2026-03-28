#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guardrails for AGENTS.md claim language.

These tests ensure AGENTS.md keeps conservative wording around validation
coverage and warning behavior so documentation does not over-claim support.
"""

from pathlib import Path


def _read_agents_md() -> str:
    repo_root = Path(__file__).parent.parent
    return (repo_root / "AGENTS.md").read_text(encoding="utf-8")


def test_quickstart_validation_status_is_explicit():
    """Golden Paths section should clearly state tested vs advanced paths."""
    text = _read_agents_md()

    assert "**Validation status**:" in text
    assert "Path 1 and Path 2 are exercised in `tests/test_agents_golden_paths.py`" in text
    assert (
        "Path 3, Path 4, and Path 5 are advanced workflows and may require optional modules or setup in the current environment"
        in text
    )


def test_warning_behavior_claims_are_conservative():
    """Ergonomics warning docs should avoid implying stable warning text contracts."""
    text = _read_agents_md()

    assert (
        "Warning suppression behavior (`suppress_warnings`) is tested in `tests/test_agents_ergonomics_features.py`"
        in text
    )
    assert (
        "Warning triggering thresholds and exact warning text are implementation details and may vary across releases"
        in text
    )

