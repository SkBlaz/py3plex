"""Experiment dataclass and deterministic ID computation.

An ``Experiment`` captures everything required to reproduce a DSL v2 query
execution: the query, its provenance metadata, environment, and the paths to
serialised result artifacts.

Design notes
------------
* The dataclass is intentionally *not* frozen – we need to be able to stamp
  the ``id`` field after construction.
* ``compute_id()`` is deterministic: identical inputs always produce the same
  24-character hex ID (SHA-256 over canonical JSON of the key fields).
* Volatile fields (timestamps, timings, absolute paths) are **excluded** from
  the hash so that re-running the same experiment on the same data always
  produces the same ID.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .utils import canonical_json, stable_hash


@dataclasses.dataclass
class Experiment:
    """Immutable record of a single experiment execution.

    Fields
    ------
    id : str
        24-hex-char prefix of the full SHA-256 hash (``id_full``).
    id_full : str
        Full 64-char SHA-256 hash used as the canonical experiment identifier.
    created_utc : str
        ISO-8601 UTC timestamp of when the experiment was created.
    py3plex_version : str
        py3plex version string at the time of execution.
    engine : str
        Execution engine used (e.g. ``"dsl_v2_executor"``).
    query : dict
        Sub-fields: ``original`` (str|None), ``ast_hash`` (str),
        ``ast_summary`` (str), ``normalized`` (dict), ``params`` (dict).
    randomness : dict
        Sub-fields: ``seed`` (int|None), ``n_samples`` (int|None),
        ``method`` (str|None), ``uq`` (dict|None).
    backend : dict
        Sub-fields: ``graph_backend`` (str), ``algo_backends`` (list[str]),
        ``fast_path`` (bool).
    network_fingerprint : dict
        Sub-fields: ``node_count``, ``edge_count``, ``layer_count``,
        ``layers`` (list[str]), ``fingerprint_hash`` (str).
    environment : dict
        Sub-fields from :func:`py3plex.experiments.env.get_environment_fingerprint`.
    performance : dict
        Sub-fields: ``stage_ms`` (dict[str,float]), ``total_ms`` (float).
    artifacts : dict
        Sub-fields: ``result_table`` (dict), ``result_object`` (dict|None),
        ``logs`` (dict|None).
    notes : str | None
        Free-text annotation.
    tags : list[str]
        Arbitrary tags for filtering / search.
    """

    # --- identity ---
    id: str = ""
    id_full: str = ""
    created_utc: str = ""

    # --- provenance ---
    py3plex_version: str = ""
    engine: str = ""

    # --- query ---
    query: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- randomness ---
    randomness: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- backend ---
    backend: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- network ---
    network_fingerprint: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- environment ---
    environment: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- performance ---
    performance: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- artifacts ---
    artifacts: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # --- metadata ---
    notes: Optional[str] = None
    tags: List[str] = dataclasses.field(default_factory=list)

    # ------------------------------------------------------------------
    # ID computation
    # ------------------------------------------------------------------

    def compute_id(self) -> str:
        """Compute the deterministic experiment ID from stable fields.

        Hashed fields (volatile fields such as timestamps / timings are **excluded**):

        * ``py3plex_version``
        * ``engine``
        * ``query.ast_hash``, ``query.normalized``, ``query.params``
        * ``randomness`` (seed, n_samples, method, uq)
        * ``backend`` (graph_backend, algo_backends, fast_path)
        * ``network_fingerprint`` (node_count, edge_count, layer_count, layers, fingerprint_hash)
        * ``environment.env_hash``

        Returns:
            24-character hex string (prefix of full SHA-256).
        """
        payload = {
            "py3plex_version": self.py3plex_version,
            "engine": self.engine,
            "query": {
                "ast_hash": self.query.get("ast_hash", ""),
                "normalized": self.query.get("normalized", {}),
                "params": self.query.get("params", {}),
            },
            "randomness": {
                "seed": self.randomness.get("seed"),
                "n_samples": self.randomness.get("n_samples"),
                "method": self.randomness.get("method"),
                "uq": self.randomness.get("uq"),
            },
            "backend": {
                "graph_backend": self.backend.get("graph_backend", ""),
                "algo_backends": sorted(self.backend.get("algo_backends", [])),
                "fast_path": self.backend.get("fast_path", False),
            },
            "network_fingerprint": {
                "node_count": self.network_fingerprint.get("node_count", 0),
                "edge_count": self.network_fingerprint.get("edge_count", 0),
                "layer_count": self.network_fingerprint.get("layer_count", 0),
                "layers": sorted(self.network_fingerprint.get("layers", [])),
                "fingerprint_hash": self.network_fingerprint.get("fingerprint_hash", ""),
            },
            "env_hash": self.environment.get("env_hash", ""),
        }
        full = stable_hash(payload, length=64)
        self.id_full = full
        self.id = full[:24]
        return self.id

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dictionary representation."""
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        """Reconstruct an Experiment from a dictionary (e.g. loaded from JSON).

        Unknown keys are silently ignored so that forward-compatible loading
        works when new fields are added in later versions.

        Args:
            data: Dictionary previously produced by :meth:`to_dict`.

        Returns:
            Experiment instance.
        """
        known = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_query(provenance: Dict[str, Any]) -> Dict[str, Any]:
        """Build the ``query.normalized`` dict from a provenance record.

        Strips volatile fields (timestamps, absolute paths, timing) and returns
        a stable, canonical representation suitable for hashing.

        Args:
            provenance: ``result.meta["provenance"]`` dict.

        Returns:
            Normalized query dict.
        """
        q = provenance.get("query", {})
        return {
            "target": q.get("target", ""),
            "ast_hash": q.get("ast_hash", ""),
            "ast_summary": q.get("ast_summary", ""),
            "params": q.get("params", {}),
        }

    @classmethod
    def from_provenance(
        cls,
        provenance: Dict[str, Any],
        *,
        artifacts: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> "Experiment":
        """Build an Experiment from a DSL v2 provenance dict.

        This is the primary integration point with QueryResult:
        ``result.meta["provenance"]`` is passed here.

        Args:
            provenance: Provenance dict from ``QueryResult.meta["provenance"]``.
            artifacts: Optional artifact metadata dict.
            notes: Optional free-text notes.
            tags: Optional list of tags.

        Returns:
            Experiment with ``id`` already computed.
        """
        from .env import get_environment_fingerprint

        q = provenance.get("query", {})
        net = provenance.get("network_fingerprint", {})
        rnd = provenance.get("randomness", {})
        back = provenance.get("backend", {})
        perf = provenance.get("performance", {})
        py3ver = provenance.get("py3plex_version", "")
        engine = provenance.get("engine", "")

        # Build network fingerprint hash (node_count + edge_count + sorted layers)
        layers = sorted(net.get("layers", []))
        fp_hash = stable_hash(
            {
                "node_count": net.get("node_count", 0),
                "edge_count": net.get("edge_count", 0),
                "layer_count": net.get("layer_count", 0),
                "layers": layers,
            },
            length=16,
        )

        network_fingerprint = {
            "node_count": net.get("node_count", 0),
            "edge_count": net.get("edge_count", 0),
            "layer_count": net.get("layer_count", 0),
            "layers": layers,
            "fingerprint_hash": net.get("fingerprint_hash", fp_hash),
        }

        query_dict = {
            "original": q.get("original"),
            "ast_hash": q.get("ast_hash", ""),
            "ast_summary": q.get("ast_summary", ""),
            "normalized": cls._normalize_query(provenance),
            "params": q.get("params", {}),
        }

        randomness_dict = {
            "seed": rnd.get("seed"),
            "n_samples": rnd.get("n_samples"),
            "method": rnd.get("method"),
            "uq": rnd.get("uq"),
        }

        backend_dict = {
            "graph_backend": back.get("graph_backend", "networkx"),
            "algo_backends": back.get("algo_backends", []),
            "fast_path": back.get("fast_path", False),
        }

        performance_dict = {
            "stage_ms": perf.get("stage_ms", {}),
            "total_ms": perf.get("total_ms", 0.0),
        }

        env = get_environment_fingerprint()

        exp = cls(
            created_utc=provenance.get(
                "timestamp_utc",
                datetime.now(timezone.utc).isoformat(),
            ),
            py3plex_version=py3ver,
            engine=engine,
            query=query_dict,
            randomness=randomness_dict,
            backend=backend_dict,
            network_fingerprint=network_fingerprint,
            environment=env,
            performance=performance_dict,
            artifacts=artifacts or {},
            notes=notes,
            tags=tags or [],
        )
        exp.compute_id()
        return exp
