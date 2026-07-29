import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _pyproject_data() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _dependency_names(specs: list[str]) -> set[str]:
    names = set()
    for spec in specs:
        name = spec.split(";", 1)[0].strip()
        for marker in ("<=", ">=", "==", "~=", "!=", "<", ">"):
            if marker in name:
                name = name.split(marker, 1)[0].strip()
                break
        names.add(name)
    return names


def test_gensim_and_rdflib_are_not_core_dependencies():
    data = _pyproject_data()
    core_deps = _dependency_names(data["project"]["dependencies"])

    assert "gensim" not in core_deps
    assert "rdflib" not in core_deps


def test_gensim_and_rdflib_live_in_algos_extra():
    data = _pyproject_data()
    optional = data["project"]["optional-dependencies"]
    algos_deps = _dependency_names(optional["algos"])

    assert "gensim" in algos_deps
    assert "rdflib" in algos_deps
