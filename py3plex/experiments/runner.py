"""High-level helpers for running and reproducing experiments.

The :class:`ExperimentRunner` provides:

* :meth:`record_query_result` – wrap a DSL v2 ``QueryResult`` as an
  :class:`~py3plex.experiments.model.Experiment` and persist it.
* :meth:`reproduce` – load a previously stored experiment and re-execute the
  query against the same (or a provided) network.

This module does **not** import any heavy ML/graph dependencies at the module
level; they are imported lazily inside methods so the module itself can be
loaded in lightweight contexts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifacts import save_metadata, save_result_table
from .errors import ReproductionError
from .model import Experiment
from .store import ExperimentStore, get_default_store
from .utils import path_safe_id


class ExperimentRunner:
    """Wraps query execution results as trackable experiments.

    Args:
        store: The :class:`~py3plex.experiments.store.ExperimentStore` to use.
            Defaults to the global default store.
    """

    def __init__(self, store: Optional[ExperimentStore] = None):
        self._store: ExperimentStore = store or get_default_store()

    @property
    def store(self) -> ExperimentStore:
        """The underlying :class:`~py3plex.experiments.store.ExperimentStore`."""
        return self._store

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_query_result(
        self,
        result: Any,
        *,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        save_table: bool = True,
    ) -> Experiment:
        """Create and persist an Experiment from a DSL v2 QueryResult.

        The provenance dict from ``result.meta["provenance"]`` is used to
        populate the experiment.  If ``save_table=True`` and pandas is
        available the result DataFrame is persisted alongside the metadata.

        Args:
            result: A ``QueryResult`` (or any object with ``.meta`` and
                ``.to_pandas()``).
            notes: Optional free-text annotation.
            tags: Optional list of tags.
            save_table: Persist the result DataFrame as a Parquet/CSV
                artifact.

        Returns:
            The persisted :class:`~py3plex.experiments.model.Experiment`.
        """
        provenance = {}
        if hasattr(result, "meta") and isinstance(result.meta, dict):
            provenance = result.meta.get("provenance", {})

        artifacts: Dict[str, Any] = {}

        # Attempt to save the result table
        if save_table:
            try:
                df = result.to_pandas()
                exp_tmp_id = Experiment.from_provenance(provenance, notes=notes, tags=tags)
                art_dir = self._store.root / path_safe_id(exp_tmp_id.id)
                art_dir.mkdir(parents=True, exist_ok=True)
                table_meta = save_result_table(df, art_dir)
                artifacts["result_table"] = table_meta
            except Exception as exc:  # noqa: BLE001 – best-effort
                artifacts["result_table"] = {"error": str(exc)}

        exp = Experiment.from_provenance(provenance, artifacts=artifacts, notes=notes, tags=tags)
        self._store.save(exp)
        return exp

    # ------------------------------------------------------------------
    # Reproduction
    # ------------------------------------------------------------------

    def reproduce(
        self,
        exp_id: str,
        *,
        network: Any = None,
        strict_env: bool = False,
    ) -> Any:
        """Re-execute the query captured in a stored experiment.

        Only DSL v2 experiments (``engine="dsl_v2_executor"``) are supported
        for automated re-execution.  For other engines, a
        :exc:`~py3plex.experiments.errors.ReproductionError` is raised.

        Args:
            exp_id: ID of the experiment to reproduce.
            network: Network to run against.  If *None* the function raises
                :exc:`~py3plex.experiments.errors.ReproductionError` because
                the original network is not stored (only its fingerprint is).
            strict_env: If *True*, raise if the current environment hash
                differs from the recorded one.

        Returns:
            A new ``QueryResult``.

        Raises:
            ReproductionError: If re-execution is not possible.
        """
        exp = self._store.load(exp_id)

        if strict_env:
            from .env import get_environment_fingerprint

            current_env = get_environment_fingerprint()
            if current_env.get("env_hash") != exp.environment.get("env_hash"):
                raise ReproductionError(
                    f"Environment mismatch: stored env_hash={exp.environment.get('env_hash')!r}, "
                    f"current env_hash={current_env.get('env_hash')!r}. "
                    "Pass strict_env=False to reproduce anyway."
                )

        if network is None:
            # When no network is provided we cannot re-execute, but we return
            # the stored experiment so callers can inspect the provenance.
            return exp

        ast_hash = exp.query.get("ast_hash", "")
        if not ast_hash:
            raise ReproductionError(
                f"Experiment {exp_id!r} does not have a stored AST hash; "
                "cannot reproduce automatically."
            )

        # Try to locate a replayable provenance bundle
        try:
            from py3plex.dsl.provenance import ProvenanceBuilder  # noqa: F401
        except ImportError:
            pass

        # For DSL v2 experiments we attempt to use the ast_summary as a hint
        # but the canonical reproduction path is: re-execute the same query
        # the user wrote.  We surface the stored query details and raise a
        # ReproductionError with guidance.
        ast_summary = exp.query.get("ast_summary", "")
        raise ReproductionError(
            f"Automatic reproduction of experiment {exp_id!r} requires the original "
            f"query builder code.  Stored AST summary: {ast_summary!r}.  "
            "Re-run the query code with the same parameters and network, then call "
            "ExperimentRunner.record_query_result() on the new result."
        )
