"""Network Experiment Registry for py3plex.

Provides a first-class experiment tracking system that captures everything
needed to reproduce and compare results across runs.

Public API
----------
Experiment
    Immutable dataclass capturing a single experiment execution.
ExperimentStore
    Filesystem-backed registry for persisting and querying experiments.
ExperimentRunner
    High-level helper for recording query results and reproducing experiments.
load_experiment(id)
    Load a single experiment from the default store.
list_experiments(...)
    List experiments from the default store with optional filters.
reproduce_experiment(id, ...)
    Reproduce a stored experiment using the default runner.
register_default_store(path=...)
    Register a custom default store path.

Examples
--------
Record a DSL v2 query result::

    from py3plex.experiments import ExperimentRunner
    runner = ExperimentRunner()
    exp = runner.record_query_result(result, tags=["demo"])
    print(exp.id)

List stored experiments::

    from py3plex.experiments import list_experiments
    for entry in list_experiments():
        print(entry["id"], entry["created_utc"])
"""

from .errors import ArtifactError, ExperimentError, ExperimentNotFound, SchemaMismatch, ReproductionError
from .model import Experiment
from .runner import ExperimentRunner
from .store import ExperimentStore, get_default_store, register_default_store


def load_experiment(exp_id: str, *, store: "ExperimentStore | None" = None) -> "Experiment":
    """Load a single experiment from the default (or provided) store.

    Args:
        exp_id: Experiment ID (full or prefix).
        store: Optional :class:`ExperimentStore`.  Defaults to the global store.

    Returns:
        :class:`Experiment` instance.

    Raises:
        ExperimentNotFound: If no matching experiment exists.
    """
    return (store or get_default_store()).load(exp_id)


def list_experiments(
    *,
    tags=None,
    engine=None,
    limit=None,
    store: "ExperimentStore | None" = None,
):
    """List experiments from the default (or provided) store.

    Args:
        tags: Filter by tags (experiment must have *all* listed tags).
        engine: Filter by engine name.
        limit: Maximum number of entries to return.
        store: Optional :class:`ExperimentStore`.  Defaults to the global store.

    Returns:
        List of lightweight index-entry dicts.
    """
    return (store or get_default_store()).list(tags=tags, engine=engine, limit=limit)


def reproduce_experiment(exp_id: str, *, network=None, strict_env: bool = False,
                         store: "ExperimentStore | None" = None):
    """Reproduce a stored experiment using the default (or provided) runner.

    Args:
        exp_id: Experiment ID.
        network: Network to run against (required for re-execution).
        strict_env: Raise if environment hash differs from stored value.
        store: Optional :class:`ExperimentStore`.  Defaults to the global store.

    Returns:
        Stored or re-executed experiment / query result.

    Raises:
        ReproductionError: If reproduction is not possible.
    """
    runner = ExperimentRunner(store=store)
    return runner.reproduce(exp_id, network=network, strict_env=strict_env)


__all__ = [
    "Experiment",
    "ExperimentStore",
    "ExperimentRunner",
    "ExperimentError",
    "ExperimentNotFound",
    "ArtifactError",
    "SchemaMismatch",
    "ReproductionError",
    "load_experiment",
    "list_experiments",
    "reproduce_experiment",
    "register_default_store",
]
