"""
Additional tests for py3plex.utils path resolution helpers.

These tests focus on happy-path resolution when working directories change,
ensuring search logic prioritizes the caller's location and packaged data.
"""

import os
from pathlib import Path

from py3plex.utils import (
    MAX_UPWARD_SEARCH_LEVELS,
    _search_upward_from_script,
    get_background_knowledge_dir,
    get_background_knowledge_path,
    get_data_path,
)


def test_get_data_path_uses_calling_script_location_when_cwd_changes(tmp_path):
    """
    Ensure get_data_path can resolve datasets using caller path even if cwd is different.
    """
    target = Path(__file__).resolve().parents[1] / "datasets" / "community.dat"
    assert target.exists(), "Expected fixture dataset missing"

    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        resolved = Path(get_data_path("datasets/community.dat"))
    finally:
        os.chdir(original_cwd)

    assert resolved == target


def test_background_knowledge_helpers_resolve_existing_paths(tmp_path):
    """Verify background knowledge helpers return real, reachable paths from any cwd."""
    expected_dir = Path(__file__).resolve().parents[1] / "background_knowledge"
    expected_file = expected_dir / "bk.n3"
    assert expected_file.exists(), "Expected background knowledge fixture missing"

    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        dir_path = Path(get_background_knowledge_dir())
        file_path = Path(get_background_knowledge_path("bk.n3"))
    finally:
        os.chdir(original_cwd)

    assert dir_path == expected_dir
    assert dir_path.is_dir()
    assert file_path == expected_file
    assert file_path.is_file()


def test_search_upward_respects_max_levels(tmp_path):
    """Ensure _search_upward_from_script returns expected number and ordering of candidates."""
    script_dir = tmp_path / "a" / "b"
    script_dir.mkdir(parents=True)

    relative = "data/example.txt"
    candidates = _search_upward_from_script(script_dir, relative)

    expected = []
    potential_root = script_dir
    for _ in range(MAX_UPWARD_SEARCH_LEVELS):
        expected.append(potential_root / relative)
        potential_root = potential_root.parent

    assert candidates == expected
