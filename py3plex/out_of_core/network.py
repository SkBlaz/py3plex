"""OutOfCoreNetwork descriptor and constructors."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import OutOfCoreIOError, SchemaError
from .schema import SUPPORTED_EDGE_FORMATS


class OutOfCoreNetwork:
    """Descriptor for a multilayer network stored on disk.

    An ``OutOfCoreNetwork`` does not load any data into memory at
    construction time.  It records the location and format of the on-disk
    edge (and optional node) table so that the executor can scan them in
    chunks when a query is executed.

    Args:
        edges_path: Path to the edge table file (or directory for Parquet).
        edges_format: One of ``"csv"``, ``"parquet"``, ``"arrow"``,
                      ``"jsonl"``.
        nodes_path: Optional path to the node table.
        nodes_format: Format of the node table (same options as edges).
        directed: Whether the network is directed (default ``False``).
        partitioning: Optional metadata dict describing how the data is
                      physically partitioned (e.g. by ``source_layer``).
        fingerprint: Optional pre-computed counts dict, e.g.
                     ``{"node_count": 1000, "edge_count": 5000}``.
        workdir: Working directory for spill files during query execution.
                 Defaults to the system temp directory.
    """

    is_out_of_core: bool = True

    def __init__(
        self,
        edges_path: str,
        edges_format: str = "csv",
        nodes_path: Optional[str] = None,
        nodes_format: Optional[str] = None,
        directed: bool = False,
        partitioning: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
        workdir: Optional[str] = None,
    ) -> None:
        fmt = edges_format.lower()
        if fmt not in SUPPORTED_EDGE_FORMATS:
            raise OutOfCoreIOError(
                f"Unsupported edge format {edges_format!r}. "
                f"Supported: {SUPPORTED_EDGE_FORMATS}"
            )
        self.edges_path = str(edges_path)
        self.edges_format = fmt
        self.nodes_path = str(nodes_path) if nodes_path else None
        self.nodes_format = nodes_format.lower() if nodes_format else None
        self.directed = directed
        self.partitioning = partitioning or {}
        self.fingerprint: Dict[str, Any] = fingerprint or {}
        self.workdir = workdir
        # Mark fingerprint as estimated when counts are not provided
        if "node_count" not in self.fingerprint and "edge_count" not in self.fingerprint:
            self.fingerprint["estimated"] = True

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_edges_csv(
        cls,
        path: str,
        directed: bool = False,
        workdir: Optional[str] = None,
    ) -> "OutOfCoreNetwork":
        """Create an OutOfCoreNetwork backed by a CSV edge list.

        The CSV must have a header row with at least the columns:
        ``source``, ``target``, ``source_layer``, ``target_layer``.

        Args:
            path: Path to the CSV file.
            directed: Whether edges are directed.
            workdir: Spill workdir.

        Returns:
            OutOfCoreNetwork instance.
        """
        if not os.path.isfile(path):
            raise OutOfCoreIOError(f"CSV file not found: {path!r}")
        return cls(
            edges_path=path,
            edges_format="csv",
            directed=directed,
            workdir=workdir,
        )

    @classmethod
    def from_edges_parquet(
        cls,
        path: str,
        directed: bool = False,
        workdir: Optional[str] = None,
    ) -> "OutOfCoreNetwork":
        """Create an OutOfCoreNetwork backed by a Parquet edge table.

        Requires ``pyarrow`` to be installed.

        Args:
            path: Path to a Parquet file or directory.
            directed: Whether edges are directed.
            workdir: Spill workdir.

        Returns:
            OutOfCoreNetwork instance.
        """
        if not os.path.exists(path):
            raise OutOfCoreIOError(f"Parquet path not found: {path!r}")
        return cls(
            edges_path=path,
            edges_format="parquet",
            directed=directed,
            workdir=workdir,
        )

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        """Return a summary dict of the network descriptor.

        Returns:
            Dict with keys: edges_path, edges_format, directed,
            nodes_path, nodes_format, fingerprint, partitioning.
        """
        return {
            "edges_path": self.edges_path,
            "edges_format": self.edges_format,
            "directed": self.directed,
            "nodes_path": self.nodes_path,
            "nodes_format": self.nodes_format,
            "fingerprint": dict(self.fingerprint),
            "partitioning": dict(self.partitioning),
            "workdir": self.workdir,
        }

    def __repr__(self) -> str:
        return (
            f"OutOfCoreNetwork("
            f"edges={self.edges_path!r}, "
            f"format={self.edges_format!r}, "
            f"directed={self.directed})"
        )
