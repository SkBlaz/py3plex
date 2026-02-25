"""Out-of-core streaming query execution for py3plex.

This package enables running DSL v2 queries over multilayer graphs stored on
disk (CSV edge lists, Apache Arrow / Parquet) without loading the full
adjacency structure into RAM.

Supported query patterns (MVP)
--------------------------------
* ``Q.edges().from_layers(...).where(...).limit(...).order_by(...)``
* ``Q.nodes().from_layers(...).where(degree__gt=N)``
* ``Q.nodes()`` / ``Q.edges()`` with ``per_layer()`` aggregations
* ``coverage(mode="at_least", k=N)`` for edges across layer pairs

Unsupported operations raise :class:`~py3plex.out_of_core.errors.UnsupportedOutOfCoreOperation`
with guidance on how to proceed.

Quick start
-----------
::

    from py3plex.out_of_core import OutOfCoreNetwork

    net = OutOfCoreNetwork.from_edges_csv("edges.csv")
    from py3plex.out_of_core.executor import OutOfCoreBackend

    backend = OutOfCoreBackend(net)
    result = backend.execute({
        "target": "edges",
        "layer_names": ["social"],
        "conditions": [{"field": "weight", "op": "gt", "value": 0.5}],
        "limit_n": 100,
    })
    df = result.to_pandas()
"""

from .errors import (
    OutOfCoreError,
    OutOfCoreIOError,
    SchemaError,
    UnsupportedOutOfCoreOperation,
)
from .network import OutOfCoreNetwork

__all__ = [
    "OutOfCoreNetwork",
    "OutOfCoreError",
    "OutOfCoreIOError",
    "SchemaError",
    "UnsupportedOutOfCoreOperation",
]
