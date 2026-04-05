from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def _project_optional_deps() -> dict:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["optional-dependencies"]


def _extract(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    assert match, f"Missing version pattern for {label}"
    return match.group(1)


def test_version_is_consistent_across_release_files():
    version = _project_version()

    py3plex_init = _read("py3plex/__init__.py")
    py3plex_config = _read("py3plex/config.py")
    mcp_init = _read("py3plex_mcp/__init__.py")
    doc_conf = _read("docfiles/conf.py")
    book_conf = _read("book/conf.py")
    citation = _read("CITATION.cff")

    assert _extract(r'^__version__\s*=\s*"([^"]+)"', py3plex_init, "py3plex.__version__") == version
    assert _extract(r'^__api_version__\s*=\s*"([^"]+)"', py3plex_init, "py3plex.__api_version__") == version
    assert _extract(r'^__version__\s*=\s*"([^"]+)"', py3plex_config, "config.__version__") == version
    assert _extract(r'^__api_version__\s*=\s*"([^"]+)"', py3plex_config, "config.__api_version__") == version
    assert _extract(r'^__version__\s*=\s*"([^"]+)"', mcp_init, "py3plex_mcp.__version__") == version
    assert _extract(r"^version\s*=\s*'([^']+)'", doc_conf, "docfiles/conf.py::version") == version
    assert _extract(r"^release\s*=\s*'([^']+)'", doc_conf, "docfiles/conf.py::release") == version
    assert _extract(r"^version\s*=\s*'([^']+)'", book_conf, "book/conf.py::version") == version
    assert _extract(r"^release\s*=\s*'([^']+)'", book_conf, "book/conf.py::release") == version
    assert _extract(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)", citation, "CITATION.cff::version") == version


def test_optional_extra_contains_common_feature_extras():
    optional = _project_optional_deps()
    assert "optional" in optional

    optional_deps = set(optional["optional"])
    expected = set()
    for extra_name in ("algos", "viz", "workflows", "arrow", "infomap"):
        for dep in optional[extra_name]:
            assert dep in optional_deps
            expected.add(dep)

    for dep in optional["mcp"]:
        assert dep in optional_deps
        expected.add(dep)

    assert optional_deps == expected
