"""
Tests for capability discovery with optional dependencies monkeypatched as missing.

Verifies that ``capabilities()`` and ``capabilities_flat()`` remain stable and
never raise when optional packages are not importable.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest

from py3plex.runtime.capabilities import capabilities, capabilities_flat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _ImportBlocker:
    """Finder/loader that raises ImportError for a set of module names.

    Implements both the legacy ``find_module`` / ``load_module`` protocol and
    the modern ``find_spec`` protocol (Python 3.4+) so it works on all
    supported CPython versions including 3.12.
    """

    def __init__(self, blocked: set[str]) -> None:
        self._blocked = blocked

    def _is_blocked(self, fullname: str) -> bool:
        return fullname in self._blocked or any(
            fullname.startswith(b + ".") for b in self._blocked
        )

    # ---- modern protocol (Python 3.4+) ----

    def find_spec(self, fullname: str, path, target=None):  # type: ignore[override]
        if self._is_blocked(fullname):
            import importlib.machinery  # stdlib – always available

            spec = importlib.machinery.ModuleSpec(fullname, self)
            return spec
        return None

    def create_module(self, spec):  # type: ignore[override]
        return None

    def exec_module(self, module):  # type: ignore[override]
        raise ImportError(f"Blocked for testing: {module.__name__}")

    # ---- legacy protocol (kept for safety) ----

    def find_module(self, fullname: str, path=None):  # type: ignore[override]
        if self._is_blocked(fullname):
            return self
        return None

    def load_module(self, fullname: str):  # type: ignore[override]
        raise ImportError(f"Blocked for testing: {fullname}")


def _block_packages(*names: str):
    """Context manager that makes *names* unimportable for the duration."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        # Remove any cached module entries so safe_import actually calls find_module.
        removed = {}
        for name in names:
            if name in sys.modules:
                removed[name] = sys.modules.pop(name)
            # Also remove sub-modules that start with name + "."
            sub_keys = [k for k in list(sys.modules) if k.startswith(name + ".")]
            for k in sub_keys:
                removed[k] = sys.modules.pop(k)

        blocker = _ImportBlocker(set(names))
        sys.meta_path.insert(0, blocker)
        try:
            yield
        finally:
            sys.meta_path.remove(blocker)
            # Restore previously cached entries.
            sys.modules.update(removed)

    return _ctx()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMissingIgraph:
    """igraph is optional; its absence should not crash capabilities()."""

    def test_capabilities_does_not_raise(self):
        with _block_packages("igraph"):
            caps = capabilities()  # must not raise
        assert caps["backends"]["igraph"]["available"] is False

    def test_igraph_available_is_false(self):
        with _block_packages("igraph"):
            caps = capabilities()
        assert caps["backends"]["igraph"]["available"] is False

    def test_igraph_no_version_key(self):
        with _block_packages("igraph"):
            caps = capabilities()
        igraph_info = caps["backends"]["igraph"]
        # When unavailable, no "version" key should be present (or it is None/absent)
        assert "version" not in igraph_info or igraph_info.get("version") is None

    def test_flat_backend_igraph_false(self):
        with _block_packages("igraph"):
            flat = capabilities_flat()
        assert flat["backend_igraph"] is False


class TestMissingLeidenalg:
    """leidenalg is optional; its absence should report leiden as unavailable."""

    def test_capabilities_does_not_raise(self):
        with _block_packages("leidenalg"):
            caps = capabilities()
        assert caps["community_algorithms"]["leiden"]["available"] is False

    def test_leiden_notes_present(self):
        with _block_packages("leidenalg"):
            caps = capabilities()
        notes = caps["community_algorithms"]["leiden"].get("notes", "")
        assert "leidenalg" in notes.lower() or "igraph" in notes.lower()

    def test_flat_leiden_false(self):
        with _block_packages("leidenalg"):
            flat = capabilities_flat()
        assert flat["leiden"] is False


class TestMissingPythonLouvain:
    """python-louvain (community module) is optional."""

    def test_capabilities_does_not_raise(self):
        with _block_packages("community"):
            caps = capabilities()
        # Should not raise regardless of louvain availability
        assert isinstance(caps, dict)

    def test_community_algorithms_schema_stable(self):
        with _block_packages("community"):
            caps = capabilities()
        assert "louvain" in caps["community_algorithms"]
        assert "available" in caps["community_algorithms"]["louvain"]


class TestMissingScipy:
    """scipy is optional for UQ."""

    def test_capabilities_does_not_raise(self):
        with _block_packages("scipy"):
            caps = capabilities()
        assert isinstance(caps, dict)

    def test_scipy_available_false(self):
        with _block_packages("scipy"):
            caps = capabilities()
        assert caps["uncertainty_quantification"]["scipy_available"] is False

    def test_bootstrap_still_true(self):
        """bootstrap should remain available even without scipy."""
        with _block_packages("scipy"):
            caps = capabilities()
        assert caps["uncertainty_quantification"]["bootstrap"] is True

    def test_deterministic_seed_still_true(self):
        with _block_packages("scipy"):
            caps = capabilities()
        assert caps["uncertainty_quantification"]["deterministic_seed_context"] is True


class TestMissingInfomap:
    """infomap is optional."""

    def test_capabilities_does_not_raise(self):
        with _block_packages("infomap"):
            caps = capabilities()
        assert isinstance(caps, dict)

    def test_infomap_available_false(self):
        with _block_packages("infomap"):
            caps = capabilities()
        assert caps["community_algorithms"]["infomap"]["available"] is False


class TestAllOptionalsBlocked:
    """Block all optional backends simultaneously."""

    OPTIONALS = ("igraph", "graph_tool", "leidenalg", "community", "infomap", "scipy")

    def test_capabilities_does_not_raise(self):
        with _block_packages(*self.OPTIONALS):
            caps = capabilities()
        assert isinstance(caps, dict)

    def test_required_keys_still_present(self):
        required = {
            "backends",
            "community_algorithms",
            "core",
            "limits",
            "mcp",
            "pattern_matching",
            "performance",
            "plugins",
            "uncertainty_quantification",
        }
        with _block_packages(*self.OPTIONALS):
            caps = capabilities()
        assert required.issubset(set(caps.keys()))

    def test_networkx_still_available(self):
        """networkx is required; blocking other optionals shouldn't affect it."""
        with _block_packages(*self.OPTIONALS):
            caps = capabilities()
        assert caps["backends"]["networkx"]["available"] is True

    def test_label_propagation_still_available(self):
        """label_propagation uses only networkx which is always present."""
        with _block_packages(*self.OPTIONALS):
            caps = capabilities()
        assert caps["community_algorithms"]["label_propagation"]["available"] is True

    def test_flat_backend_networkx_still_true(self):
        with _block_packages(*self.OPTIONALS):
            flat = capabilities_flat()
        assert flat["backend_networkx"] is True

    def test_all_optional_backends_false(self):
        with _block_packages(*self.OPTIONALS):
            flat = capabilities_flat()
        assert flat["backend_igraph"] is False
        assert flat["backend_graph_tool"] is False

    def test_output_json_serialisable(self):
        import json

        with _block_packages(*self.OPTIONALS):
            caps = capabilities()
        serialised = json.dumps(caps)
        assert isinstance(serialised, str)
