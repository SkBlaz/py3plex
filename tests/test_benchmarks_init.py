import importlib


def test_benchmarks_metadata_docstring_and_all():
    module = importlib.reload(importlib.import_module("benchmarks"))
    assert module.__doc__.lstrip().startswith("Benchmark suite for py3plex performance testing.")
    assert module.__all__ == []


def test_wildcard_import_exports_nothing(monkeypatch):
    namespace = {"__builtins__": __builtins__}
    exec("from benchmarks import *", namespace)
    exported = {name for name in namespace if not name.startswith("__")}
    assert exported == set()


def test_reload_restores_metadata_and_leaves_other_state_intact():
    module = importlib.import_module("benchmarks")
    module.__all__.append("leaked_name")
    module.__doc__ = "mutated doc"
    module.transient_attr = 123

    reloaded = importlib.reload(module)

    assert reloaded.__doc__.lstrip().startswith("Benchmark suite for py3plex performance testing.")
    assert reloaded.__all__ == []
    assert reloaded.transient_attr == 123
