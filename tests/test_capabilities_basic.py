"""
Tests for the runtime capability discovery system.

Tests schema stability, key presence, and basic value correctness for
``py3plex.capabilities()``, ``py3plex.capabilities_flat()``, and
``py3plex.capabilities_fingerprint()``.
"""

from __future__ import annotations

import json
import re

import pytest

import py3plex
from py3plex.runtime.capabilities import (
    capabilities,
    capabilities_fingerprint,
    capabilities_flat,
)


# ---------------------------------------------------------------------------
# Top-level schema
# ---------------------------------------------------------------------------


class TestCapabilitiesSchema:
    """Assert top-level keys are always present."""

    REQUIRED_KEYS = {
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

    def test_returns_dict(self):
        caps = capabilities()
        assert isinstance(caps, dict)

    def test_top_level_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps.keys()))

    def test_top_level_keys_sorted(self):
        caps = capabilities()
        keys = list(caps.keys())
        assert keys == sorted(keys)

    def test_json_serialisable(self):
        caps = capabilities()
        serialised = json.dumps(caps)
        assert isinstance(serialised, str)
        roundtrip = json.loads(serialised)
        assert roundtrip == caps


# ---------------------------------------------------------------------------
# core section
# ---------------------------------------------------------------------------


class TestCoreSection:
    REQUIRED_KEYS = {"dsl_version", "platform", "python_version", "version"}

    def test_core_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps["core"].keys()))

    def test_core_keys_sorted(self):
        caps = capabilities()
        keys = list(caps["core"].keys())
        assert keys == sorted(keys)

    def test_dsl_version_string(self):
        caps = capabilities()
        dsl_ver = caps["core"]["dsl_version"]
        assert isinstance(dsl_ver, str)
        assert len(dsl_ver) > 0

    def test_version_matches_package(self):
        caps = capabilities()
        pkg_version = getattr(py3plex, "__version__", None)
        if pkg_version is not None:
            assert caps["core"]["version"] == pkg_version

    def test_python_version_format(self):
        caps = capabilities()
        py_ver = caps["core"]["python_version"]
        # Should look like "3.11.6"
        assert re.match(r"^\d+\.\d+\.\d+$", py_ver)

    def test_platform_non_empty(self):
        caps = capabilities()
        assert isinstance(caps["core"]["platform"], str)
        assert len(caps["core"]["platform"]) > 0


# ---------------------------------------------------------------------------
# backends section
# ---------------------------------------------------------------------------


class TestBackendsSection:
    EXPECTED_BACKENDS = {"networkx", "igraph", "graph_tool"}

    def test_expected_backends_present(self):
        caps = capabilities()
        assert self.EXPECTED_BACKENDS.issubset(set(caps["backends"].keys()))

    def test_each_backend_has_available_key(self):
        caps = capabilities()
        for name, info in caps["backends"].items():
            assert "available" in info, f"Backend {name!r} missing 'available' key"

    def test_available_is_bool(self):
        caps = capabilities()
        for name, info in caps["backends"].items():
            assert isinstance(info["available"], bool), (
                f"Backend {name!r} 'available' should be bool"
            )

    def test_networkx_available(self):
        # networkx is a required dependency of py3plex
        caps = capabilities()
        assert caps["backends"]["networkx"]["available"] is True

    def test_networkx_has_version_when_available(self):
        caps = capabilities()
        nx_info = caps["backends"]["networkx"]
        if nx_info["available"]:
            assert "version" in nx_info
            assert isinstance(nx_info["version"], str)

    def test_unavailable_backends_no_version(self):
        caps = capabilities()
        for name, info in caps["backends"].items():
            if not info["available"]:
                assert "version" not in info or info.get("version") is None


# ---------------------------------------------------------------------------
# community_algorithms section
# ---------------------------------------------------------------------------


class TestCommunityAlgorithmsSection:
    EXPECTED_ALGORITHMS = {"louvain", "leiden", "label_propagation", "infomap"}

    def test_expected_algorithms_present(self):
        caps = capabilities()
        assert self.EXPECTED_ALGORITHMS.issubset(
            set(caps["community_algorithms"].keys())
        )

    def test_each_algorithm_has_available_key(self):
        caps = capabilities()
        for name, info in caps["community_algorithms"].items():
            assert "available" in info, f"Algorithm {name!r} missing 'available' key"

    def test_available_is_bool(self):
        caps = capabilities()
        for name, info in caps["community_algorithms"].items():
            assert isinstance(info["available"], bool)

    def test_label_propagation_available(self):
        # label_propagation uses networkx which is always present
        caps = capabilities()
        assert caps["community_algorithms"]["label_propagation"]["available"] is True


# ---------------------------------------------------------------------------
# uncertainty_quantification section
# ---------------------------------------------------------------------------


class TestUQSection:
    REQUIRED_KEYS = {"bootstrap", "deterministic_seed_context", "scipy_available"}

    def test_uq_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps["uncertainty_quantification"].keys()))

    def test_bootstrap_is_true(self):
        caps = capabilities()
        assert caps["uncertainty_quantification"]["bootstrap"] is True

    def test_deterministic_seed_context_is_true(self):
        caps = capabilities()
        assert caps["uncertainty_quantification"]["deterministic_seed_context"] is True


# ---------------------------------------------------------------------------
# pattern_matching section
# ---------------------------------------------------------------------------


class TestPatternMatchingSection:
    def test_keys_present(self):
        caps = capabilities()
        pm = caps["pattern_matching"]
        assert "available" in pm
        assert "engine" in pm

    def test_available_when_networkx_present(self):
        caps = capabilities()
        if caps["backends"]["networkx"]["available"]:
            assert caps["pattern_matching"]["available"] is True


# ---------------------------------------------------------------------------
# plugins section
# ---------------------------------------------------------------------------


class TestPluginsSection:
    def test_keys_present(self):
        caps = capabilities()
        plugins = caps["plugins"]
        assert "entrypoint_group" in plugins
        assert "installed" in plugins

    def test_installed_is_list(self):
        caps = capabilities()
        assert isinstance(caps["plugins"]["installed"], list)

    def test_entrypoint_group_string(self):
        caps = capabilities()
        assert caps["plugins"]["entrypoint_group"] == "py3plex.plugins"


# ---------------------------------------------------------------------------
# mcp section
# ---------------------------------------------------------------------------


class TestMCPSection:
    REQUIRED_KEYS = {"enabled", "max_handles", "security_profile"}

    def test_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps["mcp"].keys()))

    def test_max_handles_positive_int(self):
        caps = capabilities()
        assert isinstance(caps["mcp"]["max_handles"], int)
        assert caps["mcp"]["max_handles"] > 0

    def test_security_profile_non_empty_string(self):
        caps = capabilities()
        assert isinstance(caps["mcp"]["security_profile"], str)
        assert len(caps["mcp"]["security_profile"]) > 0


# ---------------------------------------------------------------------------
# limits section
# ---------------------------------------------------------------------------


class TestLimitsSection:
    REQUIRED_KEYS = {"default_truncation", "max_nodes_warning_threshold"}

    def test_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps["limits"].keys()))

    def test_default_truncation_positive_int(self):
        caps = capabilities()
        assert isinstance(caps["limits"]["default_truncation"], int)
        assert caps["limits"]["default_truncation"] > 0

    def test_max_nodes_positive_int(self):
        caps = capabilities()
        assert isinstance(caps["limits"]["max_nodes_warning_threshold"], int)
        assert caps["limits"]["max_nodes_warning_threshold"] > 0


# ---------------------------------------------------------------------------
# performance section
# ---------------------------------------------------------------------------


class TestPerformanceSection:
    REQUIRED_KEYS = {
        "auto_backend_selection",
        "default_backend",
        "deterministic_seed_default",
        "dsl_fast_path_enabled",
        "numpy_available",
        "parallelism_enabled",
    }

    def test_keys_present(self):
        caps = capabilities()
        assert self.REQUIRED_KEYS.issubset(set(caps["performance"].keys()))

    def test_default_backend_non_empty(self):
        caps = capabilities()
        assert isinstance(caps["performance"]["default_backend"], str)
        assert len(caps["performance"]["default_backend"]) > 0


# ---------------------------------------------------------------------------
# capabilities_flat
# ---------------------------------------------------------------------------


class TestCapabilitiesFlat:
    def test_returns_dict(self):
        flat = capabilities_flat()
        assert isinstance(flat, dict)

    def test_all_values_bool(self):
        flat = capabilities_flat()
        for k, v in flat.items():
            assert isinstance(v, bool), f"Key {k!r} value should be bool, got {type(v)}"

    def test_keys_sorted(self):
        flat = capabilities_flat()
        keys = list(flat.keys())
        assert keys == sorted(keys)

    def test_expected_keys_present(self):
        flat = capabilities_flat()
        expected = {
            "backend_networkx",
            "label_propagation",
            "pattern_matching",
            "mcp_enabled",
            "uq_bootstrap",
        }
        assert expected.issubset(set(flat.keys()))

    def test_backend_networkx_true(self):
        flat = capabilities_flat()
        assert flat["backend_networkx"] is True

    def test_uq_bootstrap_true(self):
        flat = capabilities_flat()
        assert flat["uq_bootstrap"] is True

    def test_json_serialisable(self):
        flat = capabilities_flat()
        serialised = json.dumps(flat)
        assert isinstance(serialised, str)


# ---------------------------------------------------------------------------
# capabilities_fingerprint
# ---------------------------------------------------------------------------


class TestCapabilitiesFingerprint:
    def test_returns_string(self):
        fp = capabilities_fingerprint()
        assert isinstance(fp, str)

    def test_length_is_64(self):
        fp = capabilities_fingerprint()
        assert len(fp) == 64

    def test_hex_characters_only(self):
        fp = capabilities_fingerprint()
        assert re.match(r"^[0-9a-f]{64}$", fp)

    def test_deterministic(self):
        fp1 = capabilities_fingerprint()
        fp2 = capabilities_fingerprint()
        assert fp1 == fp2

    def test_exposed_from_package(self):
        fp = py3plex.capabilities_fingerprint()
        assert isinstance(fp, str)


# ---------------------------------------------------------------------------
# Public API exposure on py3plex package
# ---------------------------------------------------------------------------


class TestPublicAPI:
    def test_capabilities_callable_from_package(self):
        caps = py3plex.capabilities()
        assert isinstance(caps, dict)

    def test_capabilities_flat_callable_from_package(self):
        flat = py3plex.capabilities_flat()
        assert isinstance(flat, dict)

    def test_capabilities_fingerprint_callable_from_package(self):
        fp = py3plex.capabilities_fingerprint()
        assert isinstance(fp, str)


# ---------------------------------------------------------------------------
# Stability across calls
# ---------------------------------------------------------------------------


class TestStability:
    def test_identical_across_two_calls(self):
        caps1 = capabilities()
        caps2 = capabilities()
        assert caps1 == caps2

    def test_flat_identical_across_two_calls(self):
        flat1 = capabilities_flat()
        flat2 = capabilities_flat()
        assert flat1 == flat2
