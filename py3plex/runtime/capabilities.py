"""
Runtime capability discovery for py3plex.

This module provides a deterministic, machine-consumable description of every
feature available in the current Python environment.  It is the single source
of truth for capability queries originating from:

- Python API  : ``import py3plex; py3plex.capabilities()``
- CLI         : ``py3plex capabilities [--json | --pretty]``
- MCP tool    : ``capabilities`` (no arguments required)

Design goals
------------
* **Deterministic** – identical output for the same environment; keys are
  sorted alphabetically inside every nested dict.
* **Non-crashing** – optional dependencies that fail to import are reported as
  ``{"available": false}``; the function never raises.
* **Fast** – all checks use lightweight ``importlib.import_module`` calls;
  no heavy computation takes place.
* **Complete** – every documented field is always present in the output, even
  when its value is ``false`` / ``None``.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import platform
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["capabilities", "capabilities_flat", "capabilities_fingerprint"]

# Canonical DSL version string exposed to consumers.
_DSL_VERSION = "2.1"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_import(pkg: str) -> Tuple[bool, Optional[str]]:
    """Attempt to import *pkg* and return ``(available, version_or_None)``.

    Uses ``importlib.import_module`` so the package is never executed as a
    script.  Any exception is silently caught.
    """
    try:
        mod = importlib.import_module(pkg)
        version = getattr(mod, "__version__", None)
        return True, version
    except Exception:  # noqa: BLE001
        return False, None


def _sorted_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return *d* with keys sorted recursively (alphabetical)."""
    out: Dict[str, Any] = {}
    for k in sorted(d):
        v = d[k]
        if isinstance(v, dict):
            out[k] = _sorted_dict(v)
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _core_section() -> Dict[str, Any]:
    """Return the ``core`` section of the capability report."""
    import py3plex  # local import – avoid circular dependency at module load

    return {
        "dsl_version": _DSL_VERSION,
        "platform": platform.system().lower() + "-" + platform.machine(),
        "python_version": "{}.{}.{}".format(*sys.version_info[:3]),
        "version": getattr(py3plex, "__version__", "unknown"),
    }


def _backends_section() -> Dict[str, Any]:
    """Detect installed graph backends."""
    backends: Dict[str, Any] = {}

    # NetworkX (always expected)
    nx_avail, nx_ver = _safe_import("networkx")
    if nx_avail and nx_ver:
        backends["networkx"] = {"available": True, "version": nx_ver}
    else:
        backends["networkx"] = {"available": nx_avail}

    # python-igraph
    ig_avail, ig_ver = _safe_import("igraph")
    if ig_avail and ig_ver:
        backends["igraph"] = {"available": True, "version": ig_ver}
    else:
        backends["igraph"] = {"available": False}

    # graph-tool (hard to import – only available on Linux/macOS with special build)
    gt_avail, gt_ver = _safe_import("graph_tool")
    if gt_avail and gt_ver:
        backends["graph_tool"] = {"available": True, "version": gt_ver}
    else:
        backends["graph_tool"] = {"available": False}

    return backends


def _community_algorithms_section() -> Dict[str, Any]:
    """Check availability of community detection algorithms."""

    def _check_louvain() -> Dict[str, Any]:
        # python-louvain exposes the ``community`` module
        avail, _ = _safe_import("community")
        if not avail:
            avail, _ = _safe_import("community.community_louvain")
        if avail:
            return {"available": True, "backend": "networkx", "notes": "python-louvain"}
        return {"available": False, "notes": "requires python-louvain"}

    def _check_leiden() -> Dict[str, Any]:
        avail, _ = _safe_import("leidenalg")
        if avail:
            return {"available": True, "backend": "igraph", "notes": "leidenalg"}
        return {"available": False, "notes": "requires leidenalg and python-igraph"}

    def _check_label_propagation() -> Dict[str, Any]:
        # Always available via networkx
        nx_avail, _ = _safe_import("networkx")
        if nx_avail:
            return {"available": True, "backend": "networkx"}
        return {"available": False, "notes": "requires networkx"}

    def _check_infomap() -> Dict[str, Any]:
        avail, _ = _safe_import("infomap")
        if avail:
            return {"available": True, "backend": "infomap"}
        return {"available": False, "notes": "requires infomap"}

    return {
        "infomap": _check_infomap(),
        "label_propagation": _check_label_propagation(),
        "leiden": _check_leiden(),
        "louvain": _check_louvain(),
    }


def _uq_section() -> Dict[str, Any]:
    """Report uncertainty-quantification capabilities."""
    scipy_avail, _ = _safe_import("scipy")
    return {
        "bootstrap": True,  # always available (pure Python / numpy)
        "deterministic_seed_context": True,
        "scipy_available": scipy_avail,
    }


def _pattern_matching_section() -> Dict[str, Any]:
    """Detect pattern-matching engine availability."""
    nx_avail, _ = _safe_import("networkx")
    if nx_avail:
        # NetworkX ships VF2 for subgraph isomorphism
        return {"available": True, "engine": "vf2"}
    return {"available": False, "engine": None}


def _plugins_section() -> Dict[str, Any]:
    """Discover installed py3plex plugins."""
    installed: List[str] = []
    entrypoint_group = "py3plex.plugins"
    try:
        # importlib.metadata is stdlib ≥ 3.9
        from importlib.metadata import entry_points  # type: ignore[attr-defined]

        eps = entry_points(group=entrypoint_group)
        for ep in eps:
            installed.append(ep.name)
    except Exception:  # noqa: BLE001
        pass

    return {
        "entrypoint_group": entrypoint_group,
        "installed": sorted(installed),
    }


def _mcp_section() -> Dict[str, Any]:
    """Report MCP server configuration."""
    mcp_avail, _ = _safe_import("mcp")
    return {
        "enabled": mcp_avail,
        "max_handles": 32,
        "security_profile": "strict",
    }


def _limits_section() -> Dict[str, Any]:
    """Expose operational limits."""
    return {
        "default_truncation": 200,
        "max_nodes_warning_threshold": 10000,
    }


def _performance_section() -> Dict[str, Any]:
    """Report performance-related flags."""
    # Read DSL fast-path flag if config is importable
    fast_path = True
    try:
        from py3plex import config as _cfg  # type: ignore[attr-defined]

        fast_path = getattr(_cfg, "DSL_FAST_PATH_ENABLED", True)
    except Exception:  # noqa: BLE001
        pass

    numpy_avail, _ = _safe_import("numpy")

    return {
        "auto_backend_selection": True,
        "default_backend": "networkx",
        "deterministic_seed_default": True,
        "dsl_fast_path_enabled": fast_path,
        "numpy_available": numpy_avail,
        "parallelism_enabled": False,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def capabilities() -> Dict[str, Any]:
    """Return a deterministic, JSON-serialisable capability report.

    The report covers:

    * ``core``                   – library version information
    * ``backends``               – installed graph backends
    * ``community_algorithms``   – which community detection algorithms are usable
    * ``uncertainty_quantification`` – UQ support flags
    * ``pattern_matching``       – subgraph / motif engine
    * ``plugins``                – installed entry-point plugins
    * ``mcp``                    – MCP server configuration
    * ``limits``                 – default operational limits
    * ``performance``            – performance-related flags

    All nested dicts have their keys sorted alphabetically so the output is
    stable across Python versions.

    Returns
    -------
    dict
        JSON-serialisable capability report.

    Example
    -------
    >>> import py3plex
    >>> caps = py3plex.capabilities()
    >>> caps["core"]["version"]
    '1.1.4'
    >>> caps["backends"]["networkx"]["available"]
    True
    """
    report: Dict[str, Any] = {
        "backends": _backends_section(),
        "community_algorithms": _community_algorithms_section(),
        "core": _core_section(),
        "limits": _limits_section(),
        "mcp": _mcp_section(),
        "pattern_matching": _pattern_matching_section(),
        "performance": _performance_section(),
        "plugins": _plugins_section(),
        "uncertainty_quantification": _uq_section(),
    }
    return _sorted_dict(report)


def capabilities_flat() -> Dict[str, bool]:
    """Return a simplified, flat capability map optimised for LLM routing.

    Every key maps to a single boolean.  The map is sorted alphabetically.

    Example
    -------
    >>> import py3plex
    >>> flat = py3plex.capabilities_flat()
    >>> flat["backend_networkx"]
    True
    >>> flat["leiden"]
    False  # if leidenalg is not installed
    """
    caps = capabilities()
    flat: Dict[str, bool] = {}

    # backends
    for name, info in caps["backends"].items():
        flat[f"backend_{name}"] = bool(info.get("available", False))

    # community algorithms
    for name, info in caps["community_algorithms"].items():
        flat[name] = bool(info.get("available", False))

    # UQ
    for key, val in caps["uncertainty_quantification"].items():
        flat[f"uq_{key}"] = bool(val)

    # pattern matching
    flat["pattern_matching"] = bool(
        caps["pattern_matching"].get("available", False)
    )

    # mcp
    flat["mcp_enabled"] = bool(caps["mcp"].get("enabled", False))

    return dict(sorted(flat.items()))


def capabilities_fingerprint() -> str:
    """Return a SHA-256 hex digest of the normalised capability JSON.

    The fingerprint is deterministic for the same environment.  It can be
    stored alongside analysis results to document the exact capability set
    used during a run.

    Example
    -------
    >>> import py3plex
    >>> fp = py3plex.capabilities_fingerprint()
    >>> len(fp)
    64
    """
    caps_json = json.dumps(capabilities(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(caps_json.encode()).hexdigest()
