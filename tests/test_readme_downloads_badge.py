from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_download_badge_uses_live_monthly_count():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    badge = next(line for line in readme.splitlines() if "img.shields.io/pypi/dm/py3plex" in line)

    assert "PyPI downloads (last month)" in badge
    assert "cacheSeconds=3600" in badge
    assert "(https://pypistats.org/packages/py3plex)" in badge
