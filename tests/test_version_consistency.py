from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _project_version() -> str:
    pyproject = _read("pyproject.toml")
    project_block = pyproject.split("[project]", 1)[1].split("\n[", 1)[0]
    return _extract(r'^version\s*=\s*"([^"]+)"', project_block, "pyproject.toml::project.version")


def _project_optional_deps() -> dict:
    pyproject = _read("pyproject.toml")
    block = pyproject.split("[project.optional-dependencies]", 1)[1].split("\n[", 1)[0]
    optional: dict[str, list[str]] = {}
    for key, values_block in re.findall(r"^([A-Za-z0-9_-]+)\s*=\s*\[(.*?)\]", block, re.MULTILINE | re.DOTALL):
        optional[key] = re.findall(r'"([^"]+)"', values_block)
    return optional


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
    for extra_name in ("algos", "viz", "workflows", "arrow", "infomap", "examples"):
        for dep in optional[extra_name]:
            assert dep in optional_deps
            expected.add(dep)

    for dep in optional["mcp"]:
        assert dep in optional_deps
        expected.add(dep)

    assert optional_deps == expected


def test_release_metadata_alignment_in_docs_and_readme():
    version = _project_version()

    agents = _read("AGENTS.md")
    readme = _read("README.md")
    front_matter = _read("book/front_matter.rst")
    bibliography = _read("book/bibliography.rst")
    reproducibility_chapter = _read("book/part5_systems/chapter16_reproducible_environments.rst")
    docker_appendix = _read("book/appendices/appendix_b_docker_deployment.rst")

    assert _extract(
        r"^\*\*Version\*\*:\s*py3plex\s+([0-9]+\.[0-9]+\.[0-9]+)",
        agents,
        "AGENTS.md::header_version",
    ) == version
    assert f'print(py3plex.__version__)  # "{version}"' in agents
    assert f'"py3plex": "{version}"' in agents

    assert f"py3plex {version}" in front_matter
    assert f"Version {version}" in bibliography
    assert f"py3plex_version: {version}" in reproducibility_chapter
    assert f"py3plex:{version}" in docker_appendix

    assert "img.shields.io/badge/lines-213.5K-blue" in readme
    assert "img.shields.io/badge/tests-9.7K-blue" in readme
