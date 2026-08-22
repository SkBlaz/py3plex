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
    get_data_path,
    get_dataset_path,
    get_example_image_path,
    get_layer_names,
    get_multilayer_dataset_path,
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


def test_dataset_and_image_path_helpers_normalize_prefix(monkeypatch):
    """Convenience helpers should pass expected prefixed paths to get_data_path."""
    captured = []

    def fake_get_data_path(path):
        captured.append(path)
        return f"/abs/{path}"

    monkeypatch.setattr("py3plex.utils.get_data_path", fake_get_data_path)

    assert get_dataset_path("demo.csv") == "/abs/datasets/demo.csv"
    assert get_dataset_path("datasets/demo.csv") == "/abs/datasets/demo.csv"
    assert get_example_image_path("plot.png") == "/abs/example_images/plot.png"
    assert (
        get_example_image_path("example_images/plot.png")
        == "/abs/example_images/plot.png"
    )

    assert captured == [
        "datasets/demo.csv",
        "datasets/demo.csv",
        "example_images/plot.png",
        "example_images/plot.png",
    ]


def test_multilayer_dataset_helper_normalize_prefix(monkeypatch):
    """Multilayer helper should prepend folder only when missing."""
    captured = []

    def fake_get_data_path(path):
        captured.append(path)
        return f"/abs/{path}"

    monkeypatch.setattr("py3plex.utils.get_data_path", fake_get_data_path)

    assert (
        get_multilayer_dataset_path("MLKing/sample.edges")
        == "/abs/multilayer_datasets/MLKing/sample.edges"
    )
    assert (
        get_multilayer_dataset_path("multilayer_datasets/MLKing/sample.edges")
        == "/abs/multilayer_datasets/MLKing/sample.edges"
    )
    assert captured == [
        "multilayer_datasets/MLKing/sample.edges",
        "multilayer_datasets/MLKing/sample.edges",
    ]


def test_get_layer_names_ignores_non_tuple_and_sorts():
    """Layer extraction should ignore malformed nodes and sort unique layers."""

    class DummyCoreNetwork:
        def nodes(self):
            return [
                ("A", "work"),
                ("B", "social"),
                ("C", "work"),  # duplicate layer
                "not-a-tuple",
                ("missing_layer_only",),
            ]

    class DummyNet:
        core_network = DummyCoreNetwork()

    assert get_layer_names(DummyNet()) == ["social", "work"]


def test_get_layer_names_returns_empty_on_core_network_errors():
    """Layer extraction should be defensive when core network access fails."""

    class BrokenCoreNetwork:
        def nodes(self):
            raise RuntimeError("boom")

    class DummyNet:
        core_network = BrokenCoreNetwork()

    assert get_layer_names(DummyNet()) == []
