"""
Sanity checks ensuring referenced datasets and assets exist.

These tests guard against accidental removal or renaming of files
used in documentation, examples, and tests.
"""

from pathlib import Path

import pytest


@pytest.mark.unit
@pytest.mark.parametrize(
    "relative_path",
    [
        "datasets/community.dat",
        "datasets/cora.mat",
        "multilayer_datasets/aarhusCS/CS-Aarhus_multiplex.edges",
        "multilayer_datasets/MLKing/MLKing2013_multiplex.edges",
        "background_knowledge/bk.n3",
        "example_images/communities.png",
    ],
)
def test_fixtures_exist(relative_path):
    root = Path(__file__).resolve().parents[1]
    target = root / relative_path
    assert target.exists(), f"Expected fixture missing: {relative_path}"
