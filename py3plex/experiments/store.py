"""Filesystem-based experiment registry store.

Layout under the registry root:

    experiments/
        index.json          # lightweight append-friendly index
        <exp_id>/
            metadata.json   # full Experiment.to_dict()
            result_table.parquet  (or .csv)

Default registry root selection (in order):

1. ``PY3PLEX_EXPERIMENTS_DIR`` environment variable.
2. ``~/.cache/py3plex/experiments`` on Linux / macOS.
3. ``%LOCALAPPDATA%/py3plex/experiments`` on Windows.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .artifacts import load_metadata, save_metadata
from .errors import ExperimentNotFound
from .model import Experiment
from .utils import path_safe_id


def _default_registry_path() -> Path:
    """Return the platform-appropriate default registry directory."""
    env = os.environ.get("PY3PLEX_EXPERIMENTS_DIR")
    if env:
        return Path(env)
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        return Path(local_appdata) / "py3plex" / "experiments"
    return Path.home() / ".cache" / "py3plex" / "experiments"


# Module-level singleton (overridable by register_default_store)
_default_store: Optional["ExperimentStore"] = None


def register_default_store(path: Optional[str] = None) -> "ExperimentStore":
    """Register (and return) the default global experiment store.

    Args:
        path: Optional filesystem path for the registry root.  If *None* the
            platform default is used.

    Returns:
        The newly registered :class:`ExperimentStore`.
    """
    global _default_store
    _default_store = ExperimentStore(path=path)
    return _default_store


def get_default_store() -> "ExperimentStore":
    """Return the default global store, creating it if necessary."""
    global _default_store
    if _default_store is None:
        _default_store = ExperimentStore()
    return _default_store


class ExperimentStore:
    """Filesystem-backed experiment registry.

    Args:
        path: Root directory for the registry.  Defaults to the platform
            default (see module docstring).
    """

    def __init__(self, path: Optional[str] = None):
        self.root = Path(path) if path else _default_registry_path()
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "index.json"
        if not self._index_path.exists():
            self._write_index([])

    # ------------------------------------------------------------------
    # Index helpers
    # ------------------------------------------------------------------

    def _read_index(self) -> List[Dict[str, Any]]:
        try:
            with self._index_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write_index(self, entries: List[Dict[str, Any]]) -> None:
        with self._index_path.open("w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, sort_keys=True, default=str)

    def _append_index(self, entry: Dict[str, Any]) -> None:
        entries = self._read_index()
        # Replace if already present (idempotent saves)
        entries = [e for e in entries if e.get("id") != entry["id"]]
        entries.append(entry)
        self._write_index(entries)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, experiment: Experiment) -> Path:
        """Persist an experiment to the registry.

        Creates ``<root>/<exp_id>/metadata.json`` and updates the index.

        Args:
            experiment: :class:`Experiment` to persist (must have ``id`` set).

        Returns:
            Path to the experiment directory.
        """
        safe = path_safe_id(experiment.id)
        exp_dir = self.root / safe
        exp_dir.mkdir(parents=True, exist_ok=True)

        meta_path = exp_dir / "metadata.json"
        save_metadata(experiment.to_dict(), meta_path)

        # Lightweight index entry (only stable / searchable fields)
        index_entry = {
            "id": experiment.id,
            "id_full": experiment.id_full,
            "created_utc": experiment.created_utc,
            "engine": experiment.engine,
            "py3plex_version": experiment.py3plex_version,
            "tags": experiment.tags,
            "notes": experiment.notes,
        }
        self._append_index(index_entry)
        return exp_dir

    def load(self, exp_id: str) -> Experiment:
        """Load an experiment from the registry.

        Args:
            exp_id: Experiment ID (may be the short 24-char prefix or full
                64-char hash; partial prefix matching is attempted).

        Returns:
            :class:`Experiment` instance.

        Raises:
            ExperimentNotFound: If no matching experiment exists.
        """
        exp_dir = self._resolve_dir(exp_id)
        meta_path = exp_dir / "metadata.json"
        data = load_metadata(meta_path)
        return Experiment.from_dict(data)

    def delete(self, exp_id: str) -> None:
        """Remove an experiment from the registry.

        Args:
            exp_id: Experiment ID.

        Raises:
            ExperimentNotFound: If no matching experiment exists.
        """
        import shutil

        exp_dir = self._resolve_dir(exp_id)
        shutil.rmtree(exp_dir, ignore_errors=True)
        # Remove from index
        entries = [e for e in self._read_index() if not e["id"].startswith(exp_id)]
        self._write_index(entries)

    def list(
        self,
        *,
        tags: Optional[List[str]] = None,
        engine: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return lightweight index entries matching the given filters.

        Args:
            tags: If given, only return experiments that have *all* of these tags.
            engine: If given, filter by engine name.
            limit: Maximum number of entries to return (most-recent first).

        Returns:
            List of index-entry dicts (not full Experiment objects).
        """
        entries = list(reversed(self._read_index()))  # newest first
        if tags:
            tag_set = set(tags)
            entries = [e for e in entries if tag_set.issubset(set(e.get("tags", [])))]
        if engine:
            entries = [e for e in entries if e.get("engine") == engine]
        if limit is not None:
            entries = entries[:limit]
        return entries

    def artifact_dir(self, exp_id: str) -> Path:
        """Return (and create if needed) the artifact directory for an experiment.

        Args:
            exp_id: Experiment ID.

        Returns:
            :class:`Path` to the artifact directory (``<root>/<exp_id>/``).
        """
        exp_dir = self._resolve_dir(exp_id)
        return exp_dir

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_dir(self, exp_id: str) -> Path:
        """Resolve *exp_id* to a directory path, supporting prefix matching."""
        safe = path_safe_id(exp_id)
        candidate = self.root / safe
        if candidate.exists():
            return candidate
        # Try prefix matching among existing subdirectories
        for d in self.root.iterdir():
            if d.is_dir() and d.name.startswith(safe):
                return d
        raise ExperimentNotFound(exp_id)
