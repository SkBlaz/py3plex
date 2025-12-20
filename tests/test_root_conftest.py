import importlib.util
import glob
import os
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def root_conftest_module():
    spec = importlib.util.spec_from_file_location("root_conftest", REPO_ROOT / "conftest.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_collect_ignore_glob_matches_infomap_tree(root_conftest_module):
    pattern = root_conftest_module.collect_ignore_glob
    assert pattern == ["py3plex/algorithms/community_detection/infomap/**/*.py"]

    matches = glob.glob(str(REPO_ROOT / pattern[0]), recursive=True)
    assert matches, "glob pattern should match infomap files"
    assert any(Path(path).name == "infomap.py" for path in matches)


def test_collect_ignore_targets_optional_infomap_dependency(root_conftest_module):
    expected = [
        "py3plex/algorithms/community_detection/infomap",
        "py3plex/algorithms/community_detection/infomap/infomap.py",
    ]
    assert root_conftest_module.collect_ignore == expected

    for rel_path in expected:
        assert (REPO_ROOT / rel_path).exists()


def test_collect_ignore_glob_covers_all_python_files(root_conftest_module):
    """Glob should ignore every Python file under the infomap tree."""
    pattern = root_conftest_module.collect_ignore_glob[0]
    matched = {Path(path).resolve() for path in glob.glob(str(REPO_ROOT / pattern), recursive=True)}

    infomap_dir = REPO_ROOT / "py3plex/algorithms/community_detection/infomap"
    python_files = set(infomap_dir.rglob("*.py"))

    # No Python file in the ignored tree should escape the glob ignore list.
    assert python_files, "expected Python files within infomap tree"
    assert python_files.issubset(matched)


def test_collect_ignore_entries_are_relative_posix(root_conftest_module):
    """Ensure ignore paths stay relative/portable rather than absolute."""
    all_paths = root_conftest_module.collect_ignore + root_conftest_module.collect_ignore_glob
    for path_str in all_paths:
        assert not os.path.isabs(path_str), "ignore entries should be relative"
        assert path_str == Path(path_str).as_posix(), "paths should use forward slashes for stability"
